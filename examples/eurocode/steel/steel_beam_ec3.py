"""
Teräspalkin mitoitus — EN 1993-1-1 + SFS-NA  (eurocode-fi -moduuli)
==================================================================

Vapaasti tuetun valssatun I-palkin ULS- (taivutus, leikkaus, kiepahdus) ja
SLS-tarkastus (taipuma). Palkin pituus, profiili ja materiaali luetaan Teklasta
viedystä JSON-tiedostosta (export_tekla_beam.py). KAIKKI normikohtaiset arvot
luetaan tiedostosta params/na_steel.yaml (ei kovakoodattuja normiarvoja —
ks. docs/11 ja tekijänoikeusperiaate).

Tuottaa: konsolitulosteen + suomenkielisen laskumuistion (laskumuistio_teraspalkki.md).
Riippumattomat ristiintarkistukset (verifiointitaso 2):
  1. poikkileikkaussuureet geometriasta vs. Teklan profiilikirjasto
  2. M, V ja taipuma numeerisesti integroimalla (ei suljettuja kaavoja)
  3. kiepahduksen M_cr Rayleigh–Ritz-energiamenetelmällä (ei C1/C2-kertoimia)
Jos ristiintarkistus ei täsmää, skripti päättyy nollasta poikkeavalla paluukoodilla.

Aja:  python steel_beam_ec3.py [polku/na_steel.yaml] [polku/tekla_beam.json]

Vaatii: pyyaml, numpy, scipy  (pip install -r requirements.txt)
"""

import json
import math
import os
import sys

for _stream in (sys.stdout, sys.stderr):  # Finnish/§ chars print correctly on Windows
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "timber"))
from glulam_beam_ec5 import (beam_numeric, is_dummy, pct, util_label,  # noqa: E402
                             util_verdict, UTIL_MAX, UTIL_TARGET)

DEFAULT_PARAMS = os.path.join(REPO_ROOT, "params", "na_steel.yaml")
DEFAULT_BEAM = os.path.join(HERE, "tekla_beam_IPE300.json")

# --- Lähtötiedot (muokkaa nämä) --------------------------------------------
INPUTS = {
    "q_k": 5.0,        # kN/m, muuttuva ominaiskuorma (tasainen viivakuorma)
    "g_k_add": 0.0,    # kN/m, lisäpysyvä kuorma omapainon lisäksi
    "lateral": "free", # "free" = ylälaippa tukematon tukien välillä,
                       # "restrained" = puristettu laippa sivusuunnassa tuettu (ei kiepahdusta)
    "load_level": "top",  # kuorman vaikutuskohta: "top" (ylälaippa), "sc" (vääntökeskiö)
    # Kriittisen momentin C1/C2: tasainen kuorma, haarukkatuet (k = k_w = 1).
    # Lähde: NCCI SN003 (kirjallisuus, EI EN 1993-1-1:n arvo — standardi ei anna M_cr-kaavaa).
    "C1": 1.127,
    "C2": 0.454,
}
GRAVITY = 9.81          # m/s^2
CROSS_TOL = 1e-3        # M, V, w: suhteellinen toleranssi
SECTION_TOL = 0.01      # geometria vs. kirjasto (kirjaston arvot on pyöristetty)
MCR_TOL = 0.02          # C1/C2-kaava vs. Ritz (C1/C2 ovat itsekin approksimaatioita)


def req(params, dotted, clause):
    """Hae sisäkkäinen avain; pysähdy selkeästi jos arvo puuttuu/tyhjä."""
    node = params
    for key in dotted.split("."):
        if not isinstance(node, dict) or key not in node or node[key] is None:
            raise SystemExit(
                f"Puuttuva arvo: '{dotted}'. Täytä params/na_steel.yaml "
                f"(lähde: {clause}). Moduuli ei arvaa normiarvoja."
            )
        node = node[key]
    return node


def load_params(path):
    try:
        import yaml
    except ModuleNotFoundError:
        raise SystemExit("pyyaml puuttuu. Aja:  pip install -r requirements.txt")
    if not os.path.exists(path):
        raise SystemExit(
            f"Parametritiedostoa ei löydy: {path}\n"
            "Kopioi params/na_steel.example.yaml -> params/na_steel.yaml ja "
            "täytä arvot lisensoidusta normistasi."
        )
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return yaml.safe_load(text) or {}, text


# --- Poikkileikkaussuureet (valssattu I, juuripyöristys r) ------------------
def section_properties(h, b, tw, tf, r):
    """Suljetut kaavat; pyöristykset ('spandrel', neliö r×r − neljännesympyrä) mukana.

    Pyöristyksen ala a = (1 − π/4)r², staattinen momentti suoran reunansa
    suhteen S = (5/6 − π/4)r³ ja hitausmomentti saman reunan suhteen
    I_e = (1 − 5π/16)r⁴.
    """
    a = (1 - math.pi / 4) * r**2
    S = (5 / 6 - math.pi / 4) * r**3
    Ie = (1 - 5 * math.pi / 16) * r**4
    hw = h - 2 * tf
    df = h / 2 - tf                                     # laipan sisäpinta NA:sta
    A = 2 * b * tf + hw * tw + 4 * a
    Iy = (b * h**3 - (b - tw) * hw**3) / 12 + 4 * (df**2 * a - 2 * df * S + Ie)
    Iz = (2 * tf * b**3 + hw * tw**3) / 12 + 4 * ((tw / 2)**2 * a + tw * S + Ie)
    Wpl = b * tf * (h - tf) + tw * hw**2 / 4 + 4 * (df * a - S)
    Wel = 2 * Iy / h
    # Vääntöjäyhyys: El Darwish & Johnston (pyöristys mukana)
    alpha = (-0.042 + 0.2204 * tw / tf + 0.1355 * r / tf
             - 0.0865 * r * tw / tf**2 - 0.0725 * tw**2 / tf**2)
    D = ((tf + r)**2 + tw * (r + tw / 4)) / (2 * r + tf)
    It = 2 / 3 * b * tf**3 + hw * tw**3 / 3 + 2 * alpha * D**4 - 0.420 * tf**4
    Iw = Iz * (h - tf)**2 / 4                           # kaksoissymmetrinen I
    return {"A": A, "Iy": Iy, "Iz": Iz, "Wpl": Wpl, "Wel": Wel, "It": It, "Iw": Iw}


def check_section_vs_catalog(sec, cat):
    """Ristiintarkistus 1: geometriasta lasketut vs. Teklan kirjasto."""
    pairs = {"A": "CROSS_SECTION_AREA", "Iy": "MOMENT_OF_INERTIA_X",
             "Iz": "MOMENT_OF_INERTIA_Y", "Wel": "SECTION_MODULUS_X"}
    deltas = {k: abs(sec[k] - cat[c]) / cat[c] for k, c in pairs.items() if c in cat}
    return {"ok": bool(deltas) and all(d < SECTION_TOL for d in deltas.values()),
            "deltas": deltas, "catalog": {k: cat[c] for k, c in pairs.items() if c in cat}}


# --- Kiepahdus --------------------------------------------------------------
def mcr_closed(E, G, sec, L, zg, C1, C2):
    """M_cr (N·mm), C1/C2-kaava; zg > 0 = kuorma vääntökeskiön yläpuolella."""
    Iz, It, Iw = sec["Iz"], sec["It"], sec["Iw"]
    base = C1 * math.pi**2 * E * Iz / L**2
    return base * (math.sqrt(Iw / Iz + L**2 * G * It / (math.pi**2 * E * Iz)
                             + (C2 * zg)**2) - C2 * zg)


def mcr_ritz(E, G, sec, L, zg, n_terms=7, n=2001):
    """Ristiintarkistus 3: M_cr energiamenetelmällä (Rayleigh–Ritz).

    v = Σ A_i sin(iπx/L), φ = Σ B_i sin(iπx/L). Toinen variaatio:
      ½∫(EIz v''² + GIt φ'² + EIw φ''²) + λ[∫M₀ φ v'' − ½∫q₀ zg φ²] = 0
    pienin positiivinen λ → M_cr = λ·q₀L²/8. Ei käytä C1/C2-kertoimia.
    """
    import numpy as np
    from scipy.linalg import eig
    x = np.linspace(0.0, L, n)
    q0 = 1.0
    M0 = q0 * x * (L - x) / 2
    k = np.arange(1, n_terms + 1)[:, None] * math.pi / L
    s, ds, dds = np.sin(k * x), k * np.cos(k * x), -k**2 * np.sin(k * x)
    integ = lambda f: np.trapezoid(f, x)  # noqa: E731
    Kvv = E * sec["Iz"] * integ(dds[:, None] * dds[None])
    Kpp = G * sec["It"] * integ(ds[:, None] * ds[None]) + E * sec["Iw"] * integ(dds[:, None] * dds[None])
    C = integ(M0 * dds[:, None] * s[None])
    P = q0 * zg * integ(s[:, None] * s[None])
    Z = np.zeros_like(Kvv)
    K = np.block([[Kvv, Z], [Z, Kpp]])
    Gm = np.block([[Z, C], [C.T, -P]])
    lam = eig(K, -Gm, right=False)
    lam = lam[np.isfinite(lam)].real
    return lam[lam > 0].min() * q0 * L**2 / 8


def chi_lt(lam, alpha, lam0, beta, method):
    """Kiepahduksen pienennystekijä (EN 1993-1-1 §6.3.2.2 / §6.3.2.3)."""
    if lam <= lam0:
        return 1.0, None
    phi = 0.5 * (1 + alpha * (lam - lam0) + beta * lam**2)
    chi = min(1.0, 1 / (phi + math.sqrt(phi**2 - beta * lam**2)))
    if method == "rolled":
        chi = min(chi, 1 / lam**2)
    return chi, phi


# --- Laskenta ---------------------------------------------------------------
def calculate(params_path=DEFAULT_PARAMS, beam_path=DEFAULT_BEAM, inputs=None):
    inp = dict(INPUTS if inputs is None else inputs)
    p, text = load_params(params_path)
    with open(beam_path, encoding="utf-8") as f:
        beam = json.load(f)

    fy = req(p, "material.f_y", "EN 1993-1-1 Table 3.1 / EN 10025-2")
    E = req(p, "material.E", "EN 1993-1-1 §3.2.6")
    G = req(p, "material.G", "EN 1993-1-1 §3.2.6")
    rho = req(p, "material.rho", "EN 1991-1-1 Annex A")
    gM0 = req(p, "partial_factors.gamma_M0", "EN 1993-1-1 §6.1 + SFS-NA")
    gM1 = req(p, "partial_factors.gamma_M1", "EN 1993-1-1 §6.1 + SFS-NA")
    fl_lim = req(p, "classification.flange_ct_class1", "EN 1993-1-1 Table 5.2")
    web_lim = req(p, "classification.web_ct_class1", "EN 1993-1-1 Table 5.2")
    eta = req(p, "shear.eta", "EN 1993-1-5 §5.1 + SFS-NA")
    hwtw_lim = req(p, "shear.hw_tw_limit", "EN 1993-1-1 §6.2.6(6)")
    method = req(p, "ltb.method", "EN 1993-1-1 §6.3.2.2 / §6.3.2.3")
    if method not in ("general", "rolled"):
        raise SystemExit(f"Virheellinen 'ltb.method' = {method!r}. Sallitut: general, rolled.")
    aLT = req(p, "ltb.alpha_LT", "EN 1993-1-1 Table 6.3–6.5 + SFS-NA")
    lam0 = req(p, "ltb.lambda_LT0", "EN 1993-1-1 §6.3.2.2 / §6.3.2.3 + SFS-NA")
    bLT = req(p, "ltb.beta", "EN 1993-1-1 §6.3.2.2 / §6.3.2.3 + SFS-NA")
    gG_a = req(p, "actions.gamma_G_610a", "EN 1990 Table A1.2(B) + SFS-NA")
    gG_b = req(p, "actions.gamma_G_610b", "EN 1990 Table A1.2(B) + SFS-NA")
    gQ = req(p, "actions.gamma_Q", "EN 1990 Table A1.2(B) + SFS-NA")
    KFI = req(p, "actions.KFI", "SFS-NA EN 1990 A1.3.1")
    w_max_ratio = req(p, "deflection_limits.w_max_ratio", "SFS-NA EN 1993-1-1 / EN 1990 A1.4.3")
    w_Q_ratio = req(p, "deflection_limits.w_Q_ratio", "SFS-NA EN 1993-1-1 / EN 1990 A1.4.3")

    gmt = beam["geometry_mm"]
    h, b = gmt["HEIGHT"], gmt["WIDTH"]
    tw, tf, r = gmt["WEB_THICKNESS"], gmt["FLANGE_THICKNESS"], gmt["ROUNDING_RADIUS_1"]
    Lmm = beam["length_mm"]
    L = Lmm / 1000.0

    sec = section_properties(h, b, tw, tf, r)
    sec_cc = check_section_vs_catalog(sec, beam.get("catalog_properties", {}))

    # Poikkileikkausluokka (Table 5.2), ε = √(235/f_y)
    eps = math.sqrt(235.0 / fy)
    ct_fl = (b - tw - 2 * r) / 2 / tf
    ct_web = (h - 2 * tf - 2 * r) / tw
    if ct_fl > fl_lim * eps or ct_web > web_lim * eps:
        raise SystemExit(f"Poikkileikkaus ei ole luokkaa 1 (laippa c/t={ct_fl:.2f}, "
                         f"uuma c/t={ct_web:.2f}); moduuli tukee vain luokkaa 1.")

    # Kuormat
    g_self = rho * sec["A"] * 1e-6 * GRAVITY / 1000.0     # kN/m
    g_k = g_self + inp["g_k_add"]
    q_k = inp["q_k"]
    combos = [("6.10a", KFI * gG_a * g_k), ("6.10b", KFI * (gG_b * g_k + gQ * q_k))]
    cname, qd = max(combos, key=lambda c: c[1])

    # Rasitukset
    M_Ed = qd * L**2 / 8                                  # kN·m
    V_Ed = qd * L / 2                                     # kN

    # Taivutus §6.2.5 (luokka 1)
    M_cRd = sec["Wpl"] * fy / gM0 / 1e6                   # kN·m
    util_m = M_Ed / M_cRd

    # Leikkaus §6.2.6
    hw = h - 2 * tf
    Av = max(sec["A"] - 2 * b * tf + (tw + 2 * r) * tf, eta * hw * tw)
    V_plRd = Av * fy / (math.sqrt(3) * gM0) / 1e3         # kN
    util_v = V_Ed / V_plRd
    shear_buckling_ok = hw / tw <= hwtw_lim * eps / eta

    # Kiepahdus §6.3.2
    zg = {"top": h / 2, "sc": 0.0}[inp["load_level"]]
    Mcr = mcr_closed(E, G, sec, Lmm, zg, inp["C1"], inp["C2"]) / 1e6   # kN·m
    Mcr_ritz = mcr_ritz(E, G, sec, Lmm, zg) / 1e6
    lam_LT = math.sqrt(sec["Wpl"] * fy / (Mcr * 1e6))
    chi, phi = chi_lt(lam_LT, aLT, lam0, bLT, method)
    if inp["lateral"] == "restrained":
        chi, phi = 1.0, None
    M_bRd = chi * sec["Wpl"] * fy / gM1 / 1e6
    util_ltb = M_Ed / M_bRd

    # Taipuma (SLS, ominaisyhdistelmä)
    EI = E * sec["Iy"]
    w_tot = 5 * (g_k + q_k) * Lmm**4 / (384 * EI)        # kN/m == N/mm
    w_Q = 5 * q_k * Lmm**4 / (384 * EI)
    w_max_lim, w_Q_lim = Lmm / w_max_ratio, Lmm / w_Q_ratio
    util_w, util_wQ = w_tot / w_max_lim, w_Q / w_Q_lim

    # Ristiintarkistus 2: M, V, w numeerisesti
    uls = beam_numeric(qd, Lmm)
    sls = beam_numeric(g_k + q_k, Lmm, EI=EI)
    import numpy as np
    M_num = uls["M"].max() / 1e6
    V_num = np.abs(uls["V"]).max() / 1e3
    w_num = float(np.interp(Lmm / 2, sls["x"], sls["w"]))
    rel = lambda a, c: abs(a - c) / max(abs(c), 1e-12)  # noqa: E731
    beam_deltas = {"M": rel(M_num, M_Ed), "V": rel(V_num, V_Ed), "w": rel(w_num, w_tot)}
    mcr_delta = rel(Mcr, Mcr_ritz)

    utils = {"taivutus": util_m, "leikkaus": util_v, "kiepahdus": util_ltb,
             "taipuma (G+Q)": util_w, "taipuma (Q)": util_wQ}
    gov = max(utils, key=utils.get)
    cross_ok = (sec_cc["ok"] and all(d < CROSS_TOL for d in beam_deltas.values())
                and mcr_delta < MCR_TOL)
    return {
        "params_path": params_path, "dummy": is_dummy(text), "beam": beam, "inp": inp,
        "h": h, "b": b, "tw": tw, "tf": tf, "r": r, "L": L, "sec": sec, "sec_cc": sec_cc,
        "fy": fy, "E": E, "G": G, "gM0": gM0, "gM1": gM1, "eps": eps,
        "ct_fl": ct_fl, "ct_web": ct_web, "fl_lim": fl_lim, "web_lim": web_lim,
        "g_self": g_self, "g_k": g_k, "q_k": q_k, "combos": combos, "cname": cname, "qd": qd,
        "M_Ed": M_Ed, "V_Ed": V_Ed, "M_cRd": M_cRd, "util_m": util_m,
        "Av": Av, "V_plRd": V_plRd, "util_v": util_v, "eta": eta,
        "shear_buckling_ok": shear_buckling_ok, "hw_tw": hw / tw, "hwtw_lim": hwtw_lim,
        "zg": zg, "Mcr": Mcr, "Mcr_ritz": Mcr_ritz, "mcr_delta": mcr_delta,
        "method": method, "aLT": aLT, "lam0": lam0, "bLT": bLT,
        "lam_LT": lam_LT, "phi": phi, "chi": chi, "M_bRd": M_bRd, "util_ltb": util_ltb,
        "w_tot": w_tot, "w_Q": w_Q, "w_max_lim": w_max_lim, "w_Q_lim": w_Q_lim,
        "util_w": util_w, "util_wQ": util_wQ,
        "M_num": M_num, "V_num": V_num, "w_num": w_num, "beam_deltas": beam_deltas,
        "utils": utils, "util_governing": gov, "util_max": utils[gov],
        "util_ok": utils[gov] < UTIL_MAX and shear_buckling_ok, "cross_ok": cross_ok,
    }


def main(argv=None, note_path=None):
    argv = sys.argv[1:] if argv is None else argv
    v = calculate(argv[0] if argv else DEFAULT_PARAMS,
                  argv[1] if len(argv) > 1 else DEFAULT_BEAM)
    bm, s = v["beam"], v["sec"]

    def fmt(u):
        return f"{u:.2f} {util_label(u)}"

    print("=== Teräspalkki — EN 1993-1-1 + SFS-NA ===")
    if v["dummy"]:
        print(f"HUOM: parametritiedosto on merkitty DUMMY/TEST-arvoiksi — EI normiarvoja.")
    print(f"Teklasta: {bm['profile']} {bm['material']}, L={v['L']:.2f} m (GUID {bm['guid']})")
    print(f"Kuormat: g_k={v['g_k']:.3f} kN/m (omapaino {v['g_self']:.3f}), q_k={v['q_k']} kN/m")
    for n, q in v["combos"]:
        print(f"  {n}: qd={q:.2f} kN/m")
    print(f"Määräävä {v['cname']}: qd={v['qd']:.2f} kN/m -> M_Ed={v['M_Ed']:.2f} kNm, V_Ed={v['V_Ed']:.2f} kN")
    print(f"Taivutus §6.2.5:  M_c,Rd={v['M_cRd']:.1f} kNm -> {fmt(v['util_m'])}")
    print(f"Leikkaus §6.2.6:  V_pl,Rd={v['V_plRd']:.1f} kN -> {fmt(v['util_v'])}; "
          f"lommahdus hw/tw={v['hw_tw']:.1f} {'OK' if v['shear_buckling_ok'] else 'EI OK'}")
    print(f"Kiepahdus §6.3.2: M_cr={v['Mcr']:.1f} kNm (Ritz {v['Mcr_ritz']:.1f}), "
          f"λ_LT={v['lam_LT']:.3f}, χ_LT={v['chi']:.3f}, M_b,Rd={v['M_bRd']:.1f} kNm -> {fmt(v['util_ltb'])}")
    print(f"Taipuma:          w={v['w_tot']:.1f}/{v['w_max_lim']:.1f} mm -> {fmt(v['util_w'])}; "
          f"w_Q={v['w_Q']:.1f}/{v['w_Q_lim']:.1f} mm -> {fmt(v['util_wQ'])}")
    d = v["sec_cc"]["deltas"]
    print(f"Ristiintarkistus: {'OK' if v['cross_ok'] else 'EPÄONNISTUI'} | geometria vs Tekla max "
          f"{max(d.values()):.2%} | M,V,w max {max(v['beam_deltas'].values()):.1e} | M_cr vs Ritz {v['mcr_delta']:.2%}")
    print(f"Suurin käyttöaste: {pct(v['util_max'])} ({v['util_governing']}) → {util_verdict(v['util_max'])}")

    write_note(v, note_path)
    if not v["cross_ok"]:
        print("VIRHE: ristiintarkistus ei täsmää — tuloksia ei voi käyttää.", file=sys.stderr)
        return 2
    if not v["util_ok"]:
        print(f"VIRHE: suurin käyttöaste ≥ {pct(UTIL_MAX)} tai uuman lommahdus — ei kelpaa.", file=sys.stderr)
        return 3
    return 0


def write_note(v, out=None):
    """Kirjoita suomenkielinen laskumuistio (markdown)."""
    if out is None:
        out = os.path.join(HERE, "laskumuistio_teraspalkki.md")
    bm, s, inp = v["beam"], v["sec"], v["inp"]

    def uf(u):
        return f"{u:.2f} ({util_label(u)})"
    try:
        shown = os.path.relpath(v["params_path"], REPO_ROOT).replace(os.sep, "/")
    except ValueError:
        shown = v["params_path"]
    if v["dummy"]:
        source = (f"**HUOM: parametritiedosto `{shown}` on merkitty DUMMY/TEST-arvoiksi — "
                  "arvot EIVÄT ole normiarvoja, eikä laskua saa käyttää mitoitukseen.**")
        footer = ("Apuväline; suunnittelija vastaa tuloksista. Arvot DUMMY/TEST-"
                  "parametritiedostosta, EIVÄT lisensoidusta normista. Ei korvaa "
                  "EN 1993-1-1 / SFS-NA:ta.")
    else:
        source = f"Normiarvot käyttäjän lisensoidusta normista (`{shown}`)."
        footer = ("Apuväline; suunnittelija vastaa tuloksista. Arvot käyttäjän "
                  "lisensoidusta normista. Ei korvaa EN 1993-1-1 / SFS-NA:ta.")
    cat = v["sec_cc"]["catalog"]
    sec_rows = "\n".join(
        f"| {k} | {s[k]:,.0f} | {cat[k]:,.0f} | {v['sec_cc']['deltas'][k]:.2%} |".replace(",", " ")
        for k in cat)
    combo_rows = "\n".join(f"| {n} | {q:.2f} |" for n, q in v["combos"])
    lat = ("ylälaippa **tukematon** tukien välillä (kiepahdus tarkastetaan)"
           if inp["lateral"] == "free" else "puristettu laippa sivusuunnassa tuettu (χ_LT = 1)")
    ltb_curve = (f"Φ_LT = {v['phi']:.3f}, χ_LT = {v['chi']:.3f}" if v["phi"] is not None
                 else f"χ_LT = {v['chi']:.3f}")
    md = f"""# Laskumuistio — teräspalkki (EN 1993-1-1 + SFS-NA)

_Automaattisesti tuotettu `steel_beam_ec3.py`:llä._ {source}

## Lähtötiedot (Tekla Structures)
- Malli `{bm['model']}`, osa {bm['name']} (GUID `{bm['guid']}`)
- Profiili **{bm['profile']}**, materiaali **{bm['material']}**, jänneväli L = {v['L']:.2f} m (vapaasti tuettu, haarukkatuet)
- h = {v['h']:.0f}, b = {v['b']:.0f}, t_w = {v['tw']}, t_f = {v['tf']}, r = {v['r']:.0f} mm
- Kuormat: omapaino {v['g_self']:.3f} kN/m + lisäpysyvä {inp['g_k_add']} kN/m → g_k = {v['g_k']:.3f} kN/m; muuttuva q_k = {v['q_k']} kN/m
- Sivutuenta: {lat}; kuorma vaikuttaa {'ylälaipassa (z_g = +h/2, epäedullinen)' if inp['load_level'] == 'top' else 'vääntökeskiössä'}

## Poikkileikkaussuureet
Laskettu geometriasta (pyöristykset mukana) ja verrattu Teklan profiilikirjastoon:

| Suure | Laskettu | Tekla | Ero |
|---|---|---|---|
{sec_rows}

W_pl,y = {s['Wpl']:,.0f} mm³, I_t = {s['It']:,.0f} mm⁴, I_w = {s['Iw']:.4e} mm⁶ (Teklan kirjastossa nämä ovat tyhjiä).

Poikkileikkausluokka (EN 1993-1-1 Table 5.2), ε = √(235/f_y) = {v['eps']:.3f}:
laippa c/t = {v['ct_fl']:.2f} ≤ {v['fl_lim']}·ε = {v['fl_lim'] * v['eps']:.2f}, uuma c/t = {v['ct_web']:.2f} ≤ {v['web_lim']}·ε = {v['web_lim'] * v['eps']:.2f} → **luokka 1**

## Kuormayhdistelmät (EN 1990 6.10a/6.10b, K_FI mukana)
| Yhdistelmä | q_d (kN/m) |
|---|---|
{combo_rows}

Määräävä: **{v['cname']}**, q_d = {v['qd']:.2f} kN/m → M_Ed = q_d L²/8 = **{v['M_Ed']:.2f} kNm**, V_Ed = q_d L/2 = **{v['V_Ed']:.2f} kN**

## Taivutus (EN 1993-1-1 §6.2.5)
M_c,Rd = W_pl·f_y/γ_M0 = {s['Wpl']:,.0f} · {v['fy']} / {v['gM0']} = {v['M_cRd']:.1f} kNm
→ **Käyttöaste {uf(v['util_m'])}**

## Leikkaus (EN 1993-1-1 §6.2.6)
A_v = A − 2bt_f + (t_w + 2r)t_f ≥ η·h_w·t_w → A_v = {v['Av']:,.0f} mm²
V_pl,Rd = A_v·(f_y/√3)/γ_M0 = {v['V_plRd']:.1f} kN → **Käyttöaste {uf(v['util_v'])}**
Uuman leikkauslommahdus §6.2.6(6): h_w/t_w = {v['hw_tw']:.1f} ≤ {v['hwtw_lim']}·ε/η = {v['hwtw_lim'] * v['eps'] / v['eta']:.1f} → {'OK' if v['shear_buckling_ok'] else '**EI OK**'}
(Vapaasti tuetulla palkilla suurin M ja suurin V eivät ole samassa kohdassa → ei M–V-yhteisvaikutusta.)

## Kiepahdus (EN 1993-1-1 §6.3.2, menetelmä: {v['method']})
M_cr = C1·π²EI_z/L²·[√(I_w/I_z + L²GI_t/(π²EI_z) + (C2·z_g)²) − C2·z_g],
C1 = {inp['C1']}, C2 = {inp['C2']} (NCCI SN003, tasainen kuorma), z_g = {v['zg']:.0f} mm
→ M_cr = **{v['Mcr']:.1f} kNm**
λ̄_LT = √(W_pl·f_y/M_cr) = {v['lam_LT']:.3f}; α_LT = {v['aLT']}, λ̄_LT,0 = {v['lam0']}, β = {v['bLT']} → {ltb_curve}
M_b,Rd = χ_LT·W_pl·f_y/γ_M1 = {v['M_bRd']:.1f} kNm → **Käyttöaste {uf(v['util_ltb'])}**

## Taipuma (SLS, ominaisyhdistelmä)
w = 5(g_k + q_k)L⁴/(384EI_y) = {v['w_tot']:.1f} mm (raja L/{int(v['L'] * 1000 / v['w_max_lim'])} = {v['w_max_lim']:.1f} mm) → {uf(v['util_w'])}
w_Q = 5q_kL⁴/(384EI_y) = {v['w_Q']:.1f} mm (raja L/{int(v['L'] * 1000 / v['w_Q_lim'])} = {v['w_Q_lim']:.1f} mm) → {uf(v['util_wQ'])}

## Käyttöasteet yhteensä
Suurin käyttöaste **{pct(v['util_max'])}** ({v['util_governing']}) → **{util_verdict(v['util_max'])}**
(käyttöastepolitiikka: ehdoton raja < {pct(UTIL_MAX)}, tavoite {pct(UTIL_TARGET[0])}–{pct(UTIL_TARGET[1])}; suunnittelijan valinta, ei normiarvo)

## Verifiointi (taso 2)
1. Poikkileikkaussuureet geometriasta vs. Teklan kirjasto: suurin ero {max(v['sec_cc']['deltas'].values()):.2%} (toleranssi {SECTION_TOL:.0%})
2. M, V, w numeerisesti integroimalla: M_max {v['M_num']:.3f} vs {v['M_Ed']:.3f} kNm, V_max {v['V_num']:.3f} vs {v['V_Ed']:.3f} kN, w {v['w_num']:.3f} vs {v['w_tot']:.3f} mm
3. M_cr Rayleigh–Ritz-energiamenetelmällä (7 siniterm. v:lle ja φ:lle, ei C1/C2): {v['Mcr_ritz']:.1f} kNm vs {v['Mcr']:.1f} kNm, ero {v['mcr_delta']:.2%} (toleranssi {MCR_TOL:.0%})

→ **{'OK' if v['cross_ok'] else 'ERO HAVAITTU'}**

---
*{footer}*
"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Laskumuistio kirjoitettu: {out}")


if __name__ == "__main__":
    sys.exit(main())
