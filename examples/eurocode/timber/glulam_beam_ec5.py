"""
Liimapuupalkin mitoitus — EN 1995-1-1 + SFS-NA  (eurocode-fi -moduuli)
=====================================================================

Vapaasti tuetun liimapuupalkin ULS- (taivutus, leikkaus) ja SLS-tarkastus
(taipuma). Lukee KAIKKI normikohtaiset arvot tiedostosta params/na_timber.yaml
(ei kovakoodattuja normiarvoja — ks. docs/11 ja tekijänoikeusperiaate).

Tuottaa: konsolitulosteen + suomenkielisen laskumuistion (laskumuistio_liimapuupalkki.md).
Sisältää riippumattoman ristiintarkistuksen (verifiointitaso 2): rasitukset ja
taipuma integroidaan numeerisesti kuormasta tasapainoehdoilla, ei suljetulla
kaavalla. Jos ristiintarkistus ei täsmää, skripti päättyy nollasta poikkeavalla
paluukoodilla.

Aja:  python glulam_beam_ec5.py [polku/na_timber.yaml]

Vaatii: pyyaml, numpy  (pip install -r requirements.txt)
"""

import os
import re
import sys

for _stream in (sys.stdout, sys.stderr):  # Finnish/§ chars print correctly on Windows
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_PARAMS = os.path.join(REPO_ROOT, "params", "na_timber.yaml")

# --- Lähtötiedot (muokkaa nämä) --------------------------------------------
# Lumen aikaluokka EI ole tässä: se on normivalinta (EN 1995-1-1 Table 2.2 +
# SFS-NA) ja luetaan parametritiedostosta (actions.snow_duration).
INPUTS = {
    "L": 6.0,          # m, jänneväli (vapaasti tuettu)
    "b": 140.0,        # mm, poikkileikkauksen leveys
    "h": 450.0,        # mm, poikkileikkauksen korkeus
    "g_k": 3.0,        # kN/m, pysyvä ominaiskuorma (viivakuorma palkille)
    "s_k": 6.0,        # kN/m, lumen ominaiskuorma (viivakuorma palkille)
}

SNOW_DURATIONS = ("long_term", "medium_term")   # sallitut actions.snow_duration
CROSS_TOL = 1e-3                                 # suhteellinen toleranssi
_MARKER = re.compile(r"\b(DUMMY|TEST)\b")        # merkintä parametritiedoston kommenteissa


def req(params, dotted, clause):
    """Hae sisäkkäinen avain; pysähdy selkeästi jos arvo puuttuu/tyhjä."""
    node = params
    for key in dotted.split("."):
        if not isinstance(node, dict) or key not in node or node[key] is None:
            raise SystemExit(
                f"Puuttuva arvo: '{dotted}'. Täytä params/na_timber.yaml "
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
            "Kopioi params/na_timber.example.yaml -> params/na_timber.yaml ja "
            "täytä arvot lisensoidusta normistasi."
        )
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return yaml.safe_load(text) or {}, text


def is_dummy(text):
    """True, jos parametritiedoston kommentit merkitsevät sen DUMMY/TEST-arvoiksi."""
    for line in text.splitlines():
        if "#" in line and _MARKER.search(line[line.index("#"):]):
            return True
    return False


# --- Riippumaton ristiintarkistus (taso 2) ---------------------------------
def _cumtrapz(y, x):
    """Kumulatiivinen trapetsi-integraali, alkaa nollasta."""
    import numpy as np
    out = np.zeros_like(y)
    out[1:] = np.cumsum(0.5 * (y[1:] + y[:-1]) * np.diff(x))
    return out


def beam_numeric(q_Nmm, Lmm, EI=None, n=4001):
    """Vapaasti tuettu palkki numeerisesti kuormasta q(x) (N/mm, tasainen).

    Ei käytä suljettuja muotoja qL²/8, qL/2 tai 5qL⁴/384EI:
      R_A   tukimomenttiehdosta B:n suhteen:  R_A·L = ∫ q(x)(L−x) dx
      V(x)  = R_A − ∫ q dx
      M(x)  = ∫ V dx                    (tarkistus: M(L) ≈ 0)
      EI w'' = −M  → integroidaan kahdesti, reunaehdot w(0)=w(L)=0.
    Palauttaa dict: x, V, M, (w), R_A, R_B.
    """
    import numpy as np
    x = np.linspace(0.0, Lmm, n)
    q = np.full_like(x, float(q_Nmm))
    Q = _cumtrapz(q, x)                                  # ∫ q dx
    R_A = _cumtrapz(q * (Lmm - x), x)[-1] / Lmm
    R_B = Q[-1] - R_A                                    # pystytasapaino
    V = R_A - Q
    M = _cumtrapz(V, x)
    out = {"x": x, "V": V, "M": M, "R_A": R_A, "R_B": R_B}
    if EI is not None:
        theta0 = _cumtrapz(-M / EI, x)                   # w' ilman vakiota
        w0 = _cumtrapz(theta0, x)                        # w ilman C1·x
        C1 = -w0[-1] / Lmm                               # w(L) = 0
        out["w"] = w0 + C1 * x                           # alaspäin positiivinen
    return out


def cross_check(r):
    """Vertaa suljetun muodon tuloksia numeeriseen integrointiin. Palauttaa dict."""
    import numpy as np
    Lmm = r["L"] * 1000.0
    EI = r["E0mean"] * r["I"]
    uls = beam_numeric(r["qd"], Lmm)
    sls = beam_numeric(r["g_k"] + r["s_k"], Lmm, EI=EI)

    M_num = uls["M"].max() / 1e6                         # kN·m
    V_num = np.abs(uls["V"]).max() / 1e3                 # kN
    sigma_num = uls["M"].max() / r["W"]
    tau_num = 1.5 * np.abs(uls["V"]).max() / (r["kcr"] * r["b"] * r["h"])
    w_num = np.interp(Lmm / 2.0, sls["x"], sls["w"])     # mm, keskellä
    closure = abs(uls["M"][-1]) / max(uls["M"].max(), 1e-12)   # M(L) ≈ 0

    def rel(a, b):
        return abs(a - b) / max(abs(b), 1e-12)

    deltas = {
        "M": rel(M_num, r["M_d"]),
        "V": rel(V_num, r["V_d"]),
        "sigma": rel(sigma_num, r["sigma_m_d"]),
        "tau": rel(tau_num, r["tau_d"]),
        "w_inst": rel(w_num, r["w_inst_tot"]),
        "M(L)": closure,
    }
    return {
        "ok": all(d < CROSS_TOL for d in deltas.values()),
        "deltas": deltas,
        "M_num": M_num, "V_num": V_num, "w_num": w_num,
    }


# --- Laskenta ---------------------------------------------------------------
def calculate(params_path=DEFAULT_PARAMS, inputs=None):
    """Lue parametrit, laske ULS/SLS + ristiintarkistus. Palauttaa tulos-dictin.

    Pysähtyy (SystemExit) jos normiarvo puuttuu tai on virheellinen.
    """
    inp = dict(INPUTS if inputs is None else inputs)
    p, text = load_params(params_path)

    # Normiarvot (kaikki parametritiedostosta)
    f_m_k = req(p, "material.f_m_k", "EN 14080")
    f_v_k = req(p, "material.f_v_k", "EN 14080")
    E0mean = req(p, "material.E0_mean", "EN 14080")
    gM = req(p, "partial_factors.gamma_M", "EN 1995-1-1 §2.4.1 + SFS-NA")
    snow_duration = req(p, "actions.snow_duration", "EN 1995-1-1 Table 2.2 + SFS-NA")
    if snow_duration not in SNOW_DURATIONS:
        raise SystemExit(
            f"Virheellinen arvo: 'actions.snow_duration' = {snow_duration!r}. "
            f"Sallitut: {', '.join(SNOW_DURATIONS)} "
            "(lähde: EN 1995-1-1 Table 2.2 + SFS-NA)."
        )
    kmod_perm = req(p, "k_mod.permanent", "EN 1995-1-1 Table 3.1")
    kmod_snow = req(p, f"k_mod.{snow_duration}", "EN 1995-1-1 Table 3.1")
    kdef = req(p, "k_def", "EN 1995-1-1 Table 3.2")
    kcr = req(p, "k_cr", "EN 1995-1-1 §6.1.7 + SFS-NA")
    gG_a = req(p, "actions.gamma_G_610a", "EN 1990 §6.4.3.2 kaava 6.10a + SFS-NA")
    gG_b = req(p, "actions.gamma_G_610b", "EN 1990 §6.4.3.2 kaava 6.10b + SFS-NA")
    gQ = req(p, "actions.gamma_Q", "EN 1990 + SFS-NA")
    KFI = req(p, "actions.KFI", "EN 1990 + SFS-NA")
    psi2_snow = req(p, "actions.psi2_snow", "EN 1990 + SFS-NA")
    w_inst_ratio = req(p, "deflection_limits.w_inst_ratio", "SFS-NA EN 1995-1-1 §7.2")
    w_fin_ratio = req(p, "deflection_limits.w_net_fin_ratio", "SFS-NA EN 1995-1-1 §7.2")

    L, b, h = inp["L"], inp["b"], inp["h"]
    g_k, s_k = inp["g_k"], inp["s_k"]

    # Poikkileikkaussuureet
    W = b * h**2 / 6.0          # mm^3
    I = b * h**3 / 12.0         # mm^4

    # ULS-kuormayhdistelmät (EN 1990 6.10a/6.10b, KFI mukana).
    # Määräävä = max(qd/kmod), koska lyhin aikaluokka määrää kmod:n (§3.1.3).
    combos = [
        ("6.10a: pysyvä", KFI * gG_a * g_k, kmod_perm),
        ("6.10b: pysyvä + lumi", KFI * (gG_b * g_k + gQ * s_k), kmod_snow),
    ]
    name, qd, kmod = max(combos, key=lambda c: c[1] / c[2])

    # Taivutus (§6.1.6)
    M_d = qd * L**2 / 8.0                    # kN*m
    sigma_m_d = M_d * 1e6 / W                # N/mm^2
    f_m_d = kmod * f_m_k / gM                # N/mm^2
    util_m = sigma_m_d / f_m_d

    # Leikkaus (§6.1.7)
    V_d = qd * L / 2.0                       # kN
    tau_d = 1.5 * V_d * 1e3 / (kcr * b * h)  # N/mm^2
    f_v_d = kmod * f_v_k / gM
    util_v = tau_d / f_v_d

    # Taipuma (SLS, ominaisyhdistelmä; §2.2.3, §7.2)
    Lmm = L * 1000.0
    def w_inst(q_knm):                       # q kN/m == N/mm numeerisesti
        return 5.0 * q_knm * Lmm**4 / (384.0 * E0mean * I)
    w_g, w_s = w_inst(g_k), w_inst(s_k)
    w_inst_tot = w_g + w_s
    w_fin = w_g * (1 + kdef) + w_s * (1 + psi2_snow * kdef)
    w_inst_lim = Lmm / w_inst_ratio
    w_fin_lim = Lmm / w_fin_ratio
    util_winst = w_inst_tot / w_inst_lim
    util_wfin = w_fin / w_fin_lim

    r = {
        "params_path": params_path, "dummy": is_dummy(text),
        "L": L, "b": b, "h": h, "g_k": g_k, "s_k": s_k,
        "W": W, "I": I, "E0mean": E0mean, "kcr": kcr,
        "snow_duration": snow_duration, "combos": combos,
        "name": name, "qd": qd, "kmod": kmod,
        "M_d": M_d, "sigma_m_d": sigma_m_d, "f_m_d": f_m_d, "util_m": util_m,
        "V_d": V_d, "tau_d": tau_d, "f_v_d": f_v_d, "util_v": util_v,
        "w_g": w_g, "w_s": w_s, "w_inst_tot": w_inst_tot, "w_fin": w_fin,
        "w_inst_lim": w_inst_lim, "w_fin_lim": w_fin_lim,
        "util_winst": util_winst, "util_wfin": util_wfin,
    }
    cc = cross_check(r)
    r["cross"] = cc
    r["cross_ok"] = cc["ok"]
    return r


def main(argv=None, note_path=None):
    argv = sys.argv[1:] if argv is None else argv
    path = argv[0] if argv else DEFAULT_PARAMS
    v = calculate(path)

    def fmt(u):
        return f"{u:.2f} {'OK' if u <= 1.0 else 'YLITTYY'}"

    cc = v["cross"]
    print("=== Liimapuupalkki — EN 1995-1-1 + SFS-NA ===")
    if v["dummy"]:
        print(f"HUOM: parametritiedosto on merkitty DUMMY/TEST-arvoiksi ({path}) — EI normiarvoja.")
    print(f"L={v['L']} m, b={v['b']:.0f} mm, h={v['h']:.0f} mm | "
          f"Lumen aikaluokka: {v['snow_duration']}")
    for cname, cqd, ck in v["combos"]:
        print(f"  {cname:<22} qd={cqd:.2f} kN/m, kmod={ck}, qd/kmod={cqd / ck:.2f}")
    print(f"Määräävä yhdistelmä: {v['name']} (qd={v['qd']:.2f} kN/m, kmod={v['kmod']})")
    print(f"Taivutus §6.1.6:  sigma_m,d={v['sigma_m_d']:.2f}  f_m,d={v['f_m_d']:.2f} N/mm^2  -> käyttöaste {fmt(v['util_m'])}")
    print(f"Leikkaus §6.1.7:  tau_d={v['tau_d']:.2f}  f_v,d={v['f_v_d']:.2f} N/mm^2  -> käyttöaste {fmt(v['util_v'])}")
    print(f"Taipuma §7.2:     w_inst={v['w_inst_tot']:.1f}/{v['w_inst_lim']:.1f} mm -> {fmt(v['util_winst'])}; "
          f"w_fin={v['w_fin']:.1f}/{v['w_fin_lim']:.1f} mm -> {fmt(v['util_wfin'])}")
    worst = max(cc["deltas"].items(), key=lambda kv: kv[1])
    print(f"Ristiintarkistus (numeerinen integrointi: M, V, w): "
          f"{'OK' if cc['ok'] else 'EPÄONNISTUI'} (suurin suht. ero {worst[0]}: {worst[1]:.1e})")

    write_note(v, note_path)
    if not cc["ok"]:
        print("VIRHE: ristiintarkistus ei täsmää — tuloksia ei voi käyttää.", file=sys.stderr)
        return 2
    return 0


def write_note(v, out=None):
    """Kirjoita suomenkielinen laskumuistio (markdown)."""
    if out is None:
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "laskumuistio_liimapuupalkki.md")
    def uf(u):
        return f"{u:.2f} ({'OK' if u <= 1.0 else 'YLITTYY'})"
    try:
        shown = os.path.relpath(v["params_path"], REPO_ROOT).replace(os.sep, "/")
    except ValueError:                       # eri levyasema Windowsissa
        shown = v["params_path"]
    if v["dummy"]:
        source = (f"**HUOM: parametritiedosto `{shown}` on merkitty DUMMY/TEST-arvoiksi — "
                  "arvot EIVÄT ole normiarvoja, eikä laskua saa käyttää mitoitukseen.**")
        footer = ("Apuväline; suunnittelija vastaa tuloksista. Arvot DUMMY/TEST-"
                  "parametritiedostosta, EIVÄT lisensoidusta normista. Ei korvaa "
                  "EN 1995-1-1 / SFS-NA:ta.")
    else:
        source = f"Normiarvot käyttäjän lisensoidusta normista (`{shown}`)."
        footer = ("Apuväline; suunnittelija vastaa tuloksista. Arvot käyttäjän "
                  "lisensoidusta normista. Ei korvaa EN 1995-1-1 / SFS-NA:ta.")
    combo_rows = "\n".join(
        f"| {n} | {q:.2f} | {k} | {q / k:.2f} |" for n, q, k in v["combos"]
    )
    cc = v["cross"]
    md = f"""# Laskumuistio — liimapuupalkki (EN 1995-1-1 + SFS-NA)

_Automaattisesti tuotettu `glulam_beam_ec5.py`:llä._ {source}

## Lähtötiedot
- Jänneväli L = {v['L']} m, vapaasti tuettu
- Poikkileikkaus b × h = {v['b']:.0f} × {v['h']:.0f} mm
- Kuormat: pysyvä g_k = {v['g_k']} kN/m, lumi s_k = {v['s_k']} kN/m
- Lumen aikaluokka (EN 1995-1-1 Table 2.2 + SFS-NA, parametritiedostosta): **{v['snow_duration']}**

## Kuormayhdistelmät (EN 1990 6.10a/6.10b)
| Yhdistelmä | qd (kN/m) | kmod | qd/kmod |
|---|---|---|---|
{combo_rows}

Määräävä ULS-yhdistelmä (suurin qd/kmod, EN 1995-1-1 §3.1.3): **{v['name']}**,
qd = {v['qd']:.2f} kN/m, kmod = {v['kmod']}

## Taivutus (EN 1995-1-1 §6.1.6)
σ_m,d = M_d / W = {v['sigma_m_d']:.2f} N/mm² ; f_m,d = kmod·f_m,k/γM = {v['f_m_d']:.2f} N/mm²
→ **Käyttöaste {uf(v['util_m'])}**

## Leikkaus (EN 1995-1-1 §6.1.7)
τ_d = 1,5·V_d/(k_cr·b·h) = {v['tau_d']:.2f} N/mm² ; f_v,d = {v['f_v_d']:.2f} N/mm²
→ **Käyttöaste {uf(v['util_v'])}**

## Taipuma (EN 1995-1-1 §2.2.3, §7.2)
w_inst = {v['w_inst_tot']:.1f} mm (raja {v['w_inst_lim']:.1f} mm) → {uf(v['util_winst'])}
w_fin = {v['w_fin']:.1f} mm (raja {v['w_fin_lim']:.1f} mm) → {uf(v['util_wfin'])}

## Verifiointi (taso 2)
Riippumaton ristiintarkistus: tukireaktiot tasapainoehdoista, V(x) ja M(x)
integroimalla kuormaa numeerisesti, taipuma integroimalla EI·w'' = −M kahdesti
(reunaehdot w(0) = w(L) = 0). Verrataan suljettuihin muotoihin:
M_max {cc['M_num']:.3f} vs {v['M_d']:.3f} kN·m, V_max {cc['V_num']:.3f} vs {v['V_d']:.3f} kN,
w_inst {cc['w_num']:.3f} vs {v['w_inst_tot']:.3f} mm →
**{'OK' if v['cross_ok'] else 'ERO HAVAITTU'}** (toleranssi {CROSS_TOL:.0e} suhteellinen).

---
*{footer}*
"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Laskumuistio kirjoitettu: {out}")


if __name__ == "__main__":
    sys.exit(main())
