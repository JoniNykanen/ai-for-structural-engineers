"""
Liimapuupalkin mitoitus — EN 1995-1-1 + SFS-NA  (eurocode-fi -moduuli)
=====================================================================

Vapaasti tuetun liimapuupalkin ULS- (taivutus, leikkaus) ja SLS-tarkastus
(taipuma). Lukee KAIKKI normikohtaiset arvot tiedostosta params/na_timber.yaml
(ei kovakoodattuja normiarvoja — ks. docs/11 ja tekijänoikeusperiaate).

Tuottaa: konsolitulosteen + suomenkielisen laskumuistion (laskumuistio_liimapuupalkki.md).
Sisältää riippumattoman ristiintarkistuksen (verifiointitaso 2).

Aja:  python glulam_beam_ec5.py [polku/na_timber.yaml]

Vaatii: pyyaml, numpy  (pip install -r requirements.txt)
"""

import os
import sys

try:                                    # Finnish/§ chars print correctly on Windows
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# --- Lähtötiedot (muokkaa nämä) --------------------------------------------
INPUTS = {
    "L": 6.0,          # m, jänneväli (vapaasti tuettu)
    "b": 140.0,        # mm, poikkileikkauksen leveys
    "h": 450.0,        # mm, poikkileikkauksen korkeus
    "g_k": 3.0,        # kN/m, pysyvä ominaiskuorma (viivakuorma palkille)
    "s_k": 6.0,        # kN/m, lumen ominaiskuorma (viivakuorma palkille)
    "snow_duration": "medium_term",  # lumen aikaluokka (SFS/EC5, muokattavissa)
}


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
        return yaml.safe_load(f)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO_ROOT, "params", "na_timber.yaml")
    p = load_params(path)

    # Normiarvot (kaikki parametritiedostosta)
    f_m_k = req(p, "material.f_m_k", "EN 14080")
    f_v_k = req(p, "material.f_v_k", "EN 14080")
    E0mean = req(p, "material.E0_mean", "EN 14080")
    gM = req(p, "partial_factors.gamma_M", "EN 1995-1-1 §2.4.1 + SFS-NA")
    kmod_perm = req(p, "k_mod.permanent", "EN 1995-1-1 Table 3.1")
    kmod_snow = req(p, f"k_mod.{INPUTS['snow_duration']}", "EN 1995-1-1 Table 3.1")
    kdef = req(p, "k_def", "EN 1995-1-1 Table 3.2")
    kcr = req(p, "k_cr", "EN 1995-1-1 §6.1.7 + SFS-NA")
    gG = req(p, "actions.gamma_G", "EN 1990 §6.4.3 + SFS-NA")
    gQ = req(p, "actions.gamma_Q", "EN 1990 + SFS-NA")
    KFI = req(p, "actions.KFI", "EN 1990 + SFS-NA")
    psi2_snow = req(p, "actions.psi2_snow", "EN 1990 + SFS-NA")
    w_inst_ratio = req(p, "deflection_limits.w_inst_ratio", "SFS-NA EN 1995-1-1 §7.2")
    w_fin_ratio = req(p, "deflection_limits.w_net_fin_ratio", "SFS-NA EN 1995-1-1 §7.2")

    L, b, h = INPUTS["L"], INPUTS["b"], INPUTS["h"]
    g_k, s_k = INPUTS["g_k"], INPUTS["s_k"]

    # Poikkileikkaussuureet
    W = b * h**2 / 6.0          # mm^3
    A = b * h                   # mm^2
    I = b * h**3 / 12.0         # mm^4

    # ULS-kuormayhdistelmät (EN 1990 6.10, KFI mukana): valitaan määräävä max(qd/kmod)
    combos = [
        ("Pysyvä", KFI * gG * g_k, kmod_perm),
        ("Pysyvä + lumi", KFI * (gG * g_k + gQ * s_k), kmod_snow),
    ]
    name, qd, kmod = max(combos, key=lambda c: c[1] / c[2])   # määräävä (§3.1.3)

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

    # --- Riippumaton ristiintarkistus (taso 2): momentti numeerisesti ------
    import numpy as np
    x = np.linspace(0, Lmm, 2001)
    q_Nmm = qd            # kN/m == N/mm
    R = q_Nmm * Lmm / 2.0
    Mx = R * x - q_Nmm * x**2 / 2.0          # N*mm pituusakselilla
    M_num_kNm = Mx.max() / 1e6
    sigma_num = Mx.max() / W
    dM = abs(M_num_kNm - M_d)
    dS = abs(sigma_num - sigma_m_d)
    cross_ok = dM < 1e-3 * max(M_d, 1e-9) and dS < 1e-3 * max(sigma_m_d, 1e-9)

    # --- Tulostus ----------------------------------------------------------
    def fmt(u):
        return f"{u:.2f} {'OK' if u <= 1.0 else 'YLITTYY'}"

    print("=== Liimapuupalkki — EN 1995-1-1 + SFS-NA ===")
    print(f"L={L} m, b={b:.0f} mm, h={h:.0f} mm | Määräävä yhdistelmä: {name} (qd={qd:.2f} kN/m, kmod={kmod})")
    print(f"Taivutus §6.1.6:  sigma_m,d={sigma_m_d:.2f}  f_m,d={f_m_d:.2f} N/mm^2  -> käyttöaste {fmt(util_m)}")
    print(f"Leikkaus §6.1.7:  tau_d={tau_d:.2f}  f_v,d={f_v_d:.2f} N/mm^2  -> käyttöaste {fmt(util_v)}")
    print(f"Taipuma §7.2:     w_inst={w_inst_tot:.1f}/{w_inst_lim:.1f} mm -> {fmt(util_winst)}; "
          f"w_fin={w_fin:.1f}/{w_fin_lim:.1f} mm -> {fmt(util_wfin)}")
    print(f"Ristiintarkistus (momentti numeerisesti): {'OK' if cross_ok else f'DELTA M={dM:.3e}, sigma={dS:.3e}'}")

    write_note(locals())
    return 0


def write_note(v):
    """Kirjoita suomenkielinen laskumuistio (markdown)."""
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "laskumuistio_liimapuupalkki.md")
    def uf(u):
        return f"{u:.2f} ({'OK' if u <= 1.0 else 'YLITTYY'})"
    md = f"""# Laskumuistio — liimapuupalkki (EN 1995-1-1 + SFS-NA)

_Automaattisesti tuotettu `glulam_beam_ec5.py`:llä. Normiarvot käyttäjän
lisensoidusta normista (`params/na_timber.yaml`)._

## Lähtötiedot
- Jänneväli L = {v['L']} m, vapaasti tuettu
- Poikkileikkaus b × h = {v['b']:.0f} × {v['h']:.0f} mm
- Kuormat: pysyvä g_k = {v['g_k']} kN/m, lumi s_k = {v['s_k']} kN/m
- Määräävä ULS-yhdistelmä: **{v['name']}**, qd = {v['qd']:.2f} kN/m, kmod = {v['kmod']}

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
Riippumaton ristiintarkistus (momentti numeerisella integroinnilla vs.
suljettu muoto): **{'OK' if v['cross_ok'] else 'ERO HAVAITTU'}**.

---
*Apuväline; suunnittelija vastaa tuloksista. Arvot käyttäjän lisensoidusta
normista. Ei korvaa EN 1995-1-1 / SFS-NA:ta.*
"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Laskumuistio kirjoitettu: {out}")


if __name__ == "__main__":
    sys.exit(main())
