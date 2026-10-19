"""
Kylmämuovattu RHS/SHS-sauva — EN 1993-1-1 + SFS-NA  (eurocode-fi -moduuli)
==========================================================================

Putkiristikon paarteen tai uumasauvan tarkastus normaalivoimalle ja
taivutukselle:
  - poikkileikkaussuureet geometriasta (pyöristetyt nurkat, EN 10219-2:n
    nurkkasäteet parametritiedostosta)
  - poikkileikkausluokka (Table 5.2, sisäosa puristettuna)
  - N_c,Rd (§6.2.4), M_c,Rd (§6.2.5), M_N,y,Rd (§6.2.9.1)
  - taivutusnurjahdus molempien akselien suhteen (§6.3.1), L_cr = kerroin · L
    (Annex BB.1.3, kerroin parametritiedostosta)
  - yhteisvaikutus tason sisällä (§6.3.3, kaava 6.61, Annex B); C_my syötetään
    itse taulukosta B.3 (ks. eurocode-fi -skill: rivin valinta)

KAIKKI normikohtaiset arvot luetaan tiedostosta params/na_steel.yaml (ei
kovakoodattuja normiarvoja — ks. docs/11 ja tekijänoikeusperiaate).

Riippumaton ristiintarkistus (verifiointitaso 2): A, I ja W_pl lasketaan
uudelleen numeerisesti integroimalla poikkileikkauksen leveysfunktiota
(eri reitti kuin suljetut kaavat). Jos ero > toleranssi, paluukoodi 2.

Aja:  python rhs_member_ec3.py [polku/na_steel.yaml]
Vaatii: pyyaml, numpy  (pip install -r requirements.txt)
"""

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
sys.path.insert(0, HERE)
from glulam_beam_ec5 import is_dummy, pct, util_label, util_verdict, UTIL_MAX  # noqa: E402
from steel_beam_ec3 import load_params, req  # noqa: E402

DEFAULT_PARAMS = os.path.join(REPO_ROOT, "params", "na_steel.yaml")

# --- Lähtötiedot (muokkaa nämä) — yleinen esimerkki, ei mikään todellinen kohde --
INPUTS = {
    "b": 150.0, "h": 150.0, "t": 6.0,  # mm, SHS 150x150x6 (h = sauvan tason suuntainen)
    "L": 3000.0,                        # mm, systeemipituus (solmuväli)
    "role": "chord",                    # "chord" (paarre) tai "brace" (uumasauva), Annex BB.1.3
    "N_Ed": 400.0,                      # kN, puristus positiivinen
    "M_Ed": 8.0,                        # kNm, suurin itseisarvo tason sisällä
    "C_my": 0.9,                        # -, EN 1993-1-1 Annex B Table B.3 (valitse itse, ks. skill)
}
SECTION_TOL = 1e-3   # suljettu kaava vs. numeerinen integrointi


# --- Poikkileikkaus -----------------------------------------------------------
def corner_radii(t, params):
    """Ulko- ja sisäsäde. r_o/t-taulukko parametritiedostosta (EN 10219-2)."""
    table = req(params, "cold_formed_rhs.r_o_over_t", "EN 10219-2 Annex A (nurkkasäde)")
    for t_max, factor in sorted(table):
        if t <= t_max:
            r_o = factor * t
            return r_o, r_o - t
    raise SystemExit(f"Seinämänpaksuudelle t = {t} mm ei ole r_o/t-arvoa "
                     "(cold_formed_rhs.r_o_over_t).")


def _spandrel(r):
    """Nurkkapala (neliö r×r − neljännesympyrä): ala, keskiön etäisyys reunasta, I omasta keskiöstä."""
    a = (1 - math.pi / 4) * r**2
    yc = r * (10 - 3 * math.pi) / (12 - 3 * math.pi) if r > 0 else 0.0
    i_own = (1 / 3 - math.pi / 16 - 1 / (9 * (4 - math.pi))) * r**4
    return a, yc, i_own


def _rounded_rect(b, h, r):
    """Täysi pyöristetty suorakaide: A, I (h-suunnassa), puolikkaan staattinen momentti."""
    a, yc, i_own = _spandrel(r)
    d = h / 2 - yc
    A = b * h - 4 * a
    I = b * h**3 / 12 - 4 * (i_own + a * d**2)
    S_half = b * h**2 / 8 - 2 * a * d
    return A, I, S_half


def rhs_properties(b, h, t, r_o, r_i):
    """Suljetut kaavat. y = vahva akseli (taivutus h-suunnassa), z = heikko."""
    Ao, Iyo, Syo = _rounded_rect(b, h, r_o)
    Ai, Iyi, Syi = _rounded_rect(b - 2 * t, h - 2 * t, r_i)
    _, Izo, Szo = _rounded_rect(h, b, r_o)
    _, Izi, Szi = _rounded_rect(h - 2 * t, b - 2 * t, r_i)
    A, Iy, Iz = Ao - Ai, Iyo - Iyi, Izo - Izi
    return {
        "A": A, "Iy": Iy, "Iz": Iz,
        "Wpl_y": 2 * (Syo - Syi), "Wpl_z": 2 * (Szo - Szi),
        "Wel_y": 2 * Iy / h, "Wel_z": 2 * Iz / b,
        "i_y": math.sqrt(Iy / A), "i_z": math.sqrt(Iz / A),
        "c_flange": b - 2 * r_o, "c_web": h - 2 * r_o,   # suorat osat (Table 5.2)
    }


def rhs_properties_numeric(b, h, t, r_o, r_i, n=200001):
    """Ristiintarkistus: integroi leveysfunktio w(y) numeerisesti (ei suljettuja kaavoja)."""
    import numpy as np

    def width(y, bb, hh, r):
        y = np.abs(y)
        inside = y <= hh / 2
        d = np.clip(y - (hh / 2 - r), 0.0, None)
        w = bb - 2 * r + 2 * np.sqrt(np.clip(r**2 - d**2, 0.0, None))
        return np.where(inside, w, 0.0)

    def integrate(bb, hh, tt, ro, ri):
        y = np.linspace(0.0, hh / 2, n)
        w = width(y, bb, hh, ro) - width(y, bb - 2 * tt, hh - 2 * tt, ri)
        A = 2 * np.trapezoid(w, y)
        I = 2 * np.trapezoid(w * y**2, y)
        Wpl = 2 * np.trapezoid(w * y, y)
        return A, I, Wpl

    A, Iy, Wpl_y = integrate(b, h, t, r_o, r_i)
    _, Iz, Wpl_z = integrate(h, b, t, r_o, r_i)
    return {"A": A, "Iy": Iy, "Iz": Iz, "Wpl_y": Wpl_y, "Wpl_z": Wpl_z}


# --- Nurjahdus ----------------------------------------------------------------
def flexural_buckling(A, I, fy, E, L_cr, alpha, gamma_M1):
    """§6.3.1.2: N_cr, λ̄, Φ, χ ja N_b,Rd (N, mm)."""
    N_cr = math.pi**2 * E * I / L_cr**2
    lam = math.sqrt(A * fy / N_cr)
    phi = 0.5 * (1 + alpha * (lam - 0.2) + lam**2)
    chi = 1.0 if lam <= 0.2 else min(1.0, 1 / (phi + math.sqrt(phi**2 - lam**2)))
    return {"L_cr": L_cr, "N_cr": N_cr, "lam": lam, "phi": phi, "chi": chi,
            "N_bRd": chi * A * fy / gamma_M1}


# --- Laskenta -----------------------------------------------------------------
def calculate(params_path=DEFAULT_PARAMS, inputs=None):
    inp = dict(INPUTS if inputs is None else inputs)
    p, text = load_params(params_path)
    fy = req(p, "material.f_y", "EN 1993-1-1 Table 3.1 / EN 10219-1")
    E = req(p, "material.E", "EN 1993-1-1 §3.2.6")
    gM0 = req(p, "partial_factors.gamma_M0", "EN 1993-1-1 §6.1 + SFS-NA")
    gM1 = req(p, "partial_factors.gamma_M1", "EN 1993-1-1 §6.1 + SFS-NA")
    lim = [req(p, f"classification.hollow_internal_ct_class{k}",
               "EN 1993-1-1 Table 5.2 (sisäosa, puristus)") for k in (1, 2, 3)]
    alpha = req(p, "member_buckling.alpha_cold_formed_hollow", "EN 1993-1-1 Table 6.1 + Table 6.2")
    role = inp["role"]
    if role not in ("chord", "brace"):
        raise SystemExit(f"Virheellinen role = {role!r}. Sallitut: chord, brace.")
    k_Lcr = req(p, f"member_buckling.Lcr_factor_{role}", "EN 1993-1-1 Annex BB.1.3")

    b, h, t, L = inp["b"], inp["h"], inp["t"], inp["L"]
    r_o, r_i = corner_radii(t, p)
    sec = rhs_properties(b, h, t, r_o, r_i)
    num = rhs_properties_numeric(b, h, t, r_o, r_i)
    deltas = {k: abs(sec[k] - num[k]) / num[k] for k in num}

    # Luokka (Table 5.2): määräävä suora osa = leveämpi seinämä
    eps = math.sqrt(235.0 / fy)
    ct = max(sec["c_flange"], sec["c_web"]) / t
    cls = next((k for k, l in zip((1, 2, 3), lim) if ct <= l * eps), 4)
    if cls > 2:
        raise SystemExit(f"Poikkileikkaus on luokkaa {cls} (c/t = {ct:.2f}); "
                         "moduuli tukee vain luokkia 1–2 (plastinen kestävyys).")

    N_Ed, M_Ed = inp["N_Ed"] * 1e3, inp["M_Ed"] * 1e6     # N, N·mm
    N_cRd = sec["A"] * fy / gM0
    M_cRd = sec["Wpl_y"] * fy / gM0
    n = N_Ed / N_cRd
    a_w = min((sec["A"] - 2 * b * t) / sec["A"], 0.5)     # §6.2.9.1(5)
    M_NRd = min(M_cRd * (1 - n) / (1 - 0.5 * a_w), M_cRd)

    by = flexural_buckling(sec["A"], sec["Iy"], fy, E, k_Lcr * L, alpha, gM1)
    bz = flexural_buckling(sec["A"], sec["Iz"], fy, E, k_Lcr * L, alpha, gM1)

    # §6.3.3 kaava 6.61, Annex B Table B.1 (luokat 1–2, väännölle epäherkkä putki, χ_LT = 1)
    ny = N_Ed / by["N_bRd"]
    C_my = inp["C_my"]
    k_yy = min(C_my * (1 + (by["lam"] - 0.2) * ny), C_my * (1 + 0.8 * ny))
    inter = ny + k_yy * M_Ed / (M_cRd * gM0 / gM1)

    utils = {"normaalivoima": n, "taivutus": M_Ed / M_cRd, "N+M (§6.2.9)": M_Ed / M_NRd,
             "nurjahdus y": N_Ed / by["N_bRd"], "nurjahdus z": N_Ed / bz["N_bRd"],
             "yhteisvaikutus (6.61)": inter}
    gov = max(utils, key=utils.get)
    return {
        "params_path": params_path, "dummy": is_dummy(text), "inp": inp,
        "fy": fy, "E": E, "gM0": gM0, "gM1": gM1, "alpha": alpha, "k_Lcr": k_Lcr,
        "r_o": r_o, "r_i": r_i, "sec": sec, "num": num, "deltas": deltas,
        "cross_ok": all(d < SECTION_TOL for d in deltas.values()),
        "eps": eps, "ct": ct, "lim": lim, "cls": cls,
        "N_cRd": N_cRd, "M_cRd": M_cRd, "a_w": a_w, "M_NRd": M_NRd,
        "by": by, "bz": bz, "k_yy": k_yy, "utils": utils,
        "util_governing": gov, "util_max": utils[gov],
    }


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    v = calculate(argv[0] if argv else DEFAULT_PARAMS)
    inp, s = v["inp"], v["sec"]
    print("=== Kylmämuovattu RHS/SHS-sauva — EN 1993-1-1 + SFS-NA ===")
    if v["dummy"]:
        print("HUOM: parametritiedosto on merkitty DUMMY/TEST-arvoiksi — EI normiarvoja.")
    print(f"{inp['h']:.0f}x{inp['b']:.0f}x{inp['t']} ({inp['role']}), L = {inp['L']:.0f} mm, "
          f"r_o = {v['r_o']:.1f}, r_i = {v['r_i']:.1f} mm")
    print(f"A = {s['A']:.1f} mm², I_y = {s['Iy']:.4e}, I_z = {s['Iz']:.4e} mm⁴, "
          f"W_pl,y = {s['Wpl_y']:.0f} mm³")
    print(f"Luokka (Table 5.2): ε = {v['eps']:.3f}, c/t = {v['ct']:.2f} → luokka {v['cls']}")
    print(f"§6.2.4  N_c,Rd = {v['N_cRd'] / 1e3:.1f} kN")
    print(f"§6.2.5  M_c,Rd = {v['M_cRd'] / 1e6:.2f} kNm")
    print(f"§6.2.9  a_w = {v['a_w']:.3f}, M_N,y,Rd = {v['M_NRd'] / 1e6:.2f} kNm")
    for ax in ("y", "z"):
        bk = v["b" + ax]
        print(f"§6.3.1  {ax}: L_cr = {bk['L_cr']:.0f} mm, N_cr = {bk['N_cr'] / 1e3:.1f} kN, "
              f"λ̄ = {bk['lam']:.3f}, χ = {bk['chi']:.3f}, N_b,Rd = {bk['N_bRd'] / 1e3:.1f} kN")
    print(f"§6.3.3  C_my = {inp['C_my']}, k_yy = {v['k_yy']:.3f}")
    for k, u in v["utils"].items():
        print(f"  {k:24s} {u:.3f} {util_label(u)}")
    worst = max(v["deltas"].values())
    print(f"Ristiintarkistus (numeerinen integrointi): {'OK' if v['cross_ok'] else 'EPÄONNISTUI'} "
          f"| suurin ero {worst:.1e}")
    print(f"Suurin käyttöaste: {pct(v['util_max'])} ({v['util_governing']}) → {util_verdict(v['util_max'])}")
    source = ("DUMMY/TEST-parametritiedostosta, EIVÄT lisensoidusta normista" if v["dummy"]
              else "käyttäjän lisensoidusta normista")
    print(f"Apuväline; suunnittelija vastaa tuloksista. Arvot {source}. "
          "Ei korvaa EN 1993-1-1 / SFS-NA:ta.")
    if not v["cross_ok"]:
        print("VIRHE: ristiintarkistus ei täsmää — tuloksia ei voi käyttää.", file=sys.stderr)
        return 2
    if v["util_max"] >= UTIL_MAX:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
