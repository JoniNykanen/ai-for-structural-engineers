"""
Two-span continuous beam — finite element analysis with PyNite
==============================================================

A beam over three supports (A, B, C), two equal spans L, uniform line load q
on both spans. This:
  1. builds the model in PyNite (free, MIT-licensed 3D frame FEA library),
  2. solves it (linear static),
  3. reports support reactions, the support moment over B, the maximum span
     moment and the maximum deflection,
  4. checks every one of those against the closed-form textbook solution,
  5. plots the bending moment and shear force diagrams.

This is structural *analysis* only (internal forces). Member design (EC3 / EC5
resistance checks) is a separate step.

Run:  python continuous_beam_pynite.py

No MATLAB or Robot license required. Same model can be run in Robot for a
third opinion — see README.md in this folder.
"""

# ---------------------------------------------------------------------------
# How to verify the AI's answer
# ---------------------------------------------------------------------------
# A two-span continuous beam with equal spans and equal UDL is a classic
# statically indeterminate case with a known exact solution. By symmetry the
# slope over B is zero, so each span behaves as a propped cantilever:
#   * end reactions       R_A = R_C = 3qL/8
#   * middle reaction     R_B       = 10qL/8 = 5qL/4
#   * support moment      M_B       = -qL^2/8        (hogging)
#   * max span moment     M_span    = 9qL^2/128      at x = 3L/8 from A
#   * max deflection      delta_max = 0.005416 qL^4/EI at x = 0.4215 L from A
#   * equilibrium         R_A + R_B + R_C = 2qL
# Note M_B and the reactions do not depend on EI (equal spans, constant EI).
# self_check() compares PyNite to all of these. If the FE model gets a known
# case wrong, do not trust it on your real problem.
# ---------------------------------------------------------------------------

import math
import os
import sys

from Pynite import FEModel3D

for _stream in (sys.stdout, sys.stderr):  # Unicode chars print correctly on Windows
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))

# --- Given (edit these) ------------------------------------------------------
# Units: kN and m throughout (PyNite has no units; it only needs consistency).
INPUTS = {
    "L": 6.0,          # m, length of each span
    "q": 10.0,         # kN/m, uniform line load (downward), both spans
    "E": 210e6,        # kN/m^2, Young's modulus (steel, 210 GPa)
    "G": 81e6,         # kN/m^2, shear modulus (steel)
    "I": 8356e-8,      # m^4, second moment of area about the bending axis (≈ IPE 300)
    "Iz": 604e-8,      # m^4, weak-axis second moment of area (≈ IPE 300)
    "J": 20.1e-8,      # m^4, torsion constant (≈ IPE 300)
    "A": 53.8e-4,      # m^2, cross-section area (≈ IPE 300)
}

REL_TOL = 5e-3        # 0.5 % — FE vs closed form
COMBO = "ULS"         # single load combination, factor 1.0 (analysis only)


def build_model(L, q, E, G, I, Iz, J, A):
    """Two members A-B and B-C along global X, loaded in -Y."""
    model = FEModel3D()
    model.add_node("A", 0.0, 0.0, 0.0)
    model.add_node("B", L, 0.0, 0.0)
    model.add_node("C", 2 * L, 0.0, 0.0)

    model.add_material("Steel", E=E, G=G, nu=0.3, rho=0.0)
    # PyNite's Iy/Iz are about the member's local y/z axes. A horizontal
    # member loaded in global Y bends about local z, so Iz carries I here.
    model.add_section("Sec", A=A, Iy=Iz, Iz=I, J=J)

    model.add_member("AB", "A", "B", "Steel", "Sec")
    model.add_member("BC", "B", "C", "Steel", "Sec")

    # A: pin. B, C: rollers (free in X). Out-of-plane DOFs (Z, RX, RY) held at
    # every node so the 3D model behaves as a 2D in-plane beam.
    model.def_support("A", True, True, True, True, True, False)
    model.def_support("B", False, True, True, True, True, False)
    model.def_support("C", False, True, True, True, True, False)

    for member in ("AB", "BC"):
        model.add_member_dist_load(member, "FY", -q, -q, case="Q")
    model.add_load_combo(COMBO, {"Q": 1.0})
    return model


def solve(L, q, E, G, I, Iz, J, A, n_points=201):
    """Run the FE analysis and return results in kN, kN·m, m (sagging M > 0)."""
    model = build_model(L, q, E, G, I, Iz, J, A)
    model.analyze_linear(check_statics=False)

    # Sample both members into one diagram along the beam (x from A).
    xs, M, V, dy = [], [], [], []
    for member, x0 in (("AB", 0.0), ("BC", L)):
        m = model.members[member]
        for k in range(n_points):
            x = L * k / (n_points - 1)
            xs.append(x0 + x)
            # PyNite's Mz is negative for sagging on this layout; flip so the
            # diagram reads sagging-positive (the usual engineering convention).
            M.append(-m.moment("Mz", x, COMBO))
            V.append(m.shear("Fy", x, COMBO))
            dy.append(m.deflection("dy", x, COMBO))

    nodes = model.nodes
    return {
        "x": xs,
        "M": M,
        "V": V,
        "dy": dy,
        "R_A": nodes["A"].RxnFY[COMBO],
        "R_B": nodes["B"].RxnFY[COMBO],
        "R_C": nodes["C"].RxnFY[COMBO],
        "M_B": -model.members["AB"].moment("Mz", L, COMBO),
        "M_span": max(M),
        "delta_max": -min(dy),
    }


def closed_form(L, q, E, I, **_):
    """Exact two-span continuous beam (equal spans, UDL, constant EI)."""
    xi = (1 + math.sqrt(33)) / 16                 # location of max deflection / L
    k_delta = xi * (1 - 3 * xi**2 + 2 * xi**3) / 48  # = 0.005416
    return {
        "R_A": 3 * q * L / 8,
        "R_B": 10 * q * L / 8,
        "R_C": 3 * q * L / 8,
        "M_B": -q * L**2 / 8,
        "M_span": 9 * q * L**2 / 128,
        "delta_max": k_delta * q * L**4 / (E * I),
    }


def self_check(fe, exact, q, L):
    """Compare FE to closed form. Returns list of (name, fe, exact, rel_err, ok)."""
    rows = []
    for key in ("R_A", "R_B", "R_C", "M_B", "M_span", "delta_max"):
        err = abs(fe[key] - exact[key]) / abs(exact[key])
        rows.append((key, fe[key], exact[key], err, err <= REL_TOL))
    total = fe["R_A"] + fe["R_B"] + fe["R_C"]
    err = abs(total - 2 * q * L) / (2 * q * L)
    rows.append(("ΣR = 2qL", total, 2 * q * L, err, err <= REL_TOL))
    return rows


def plot(fe, L, path):
    import matplotlib.pyplot as plt

    fig, (ax_m, ax_v) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax_m.plot(fe["x"], fe["M"], color="tab:blue")
    ax_m.fill_between(fe["x"], fe["M"], alpha=0.2, color="tab:blue")
    ax_m.axhline(0, color="k", lw=0.8)
    ax_m.invert_yaxis()  # structural convention: sagging plotted below the axis
    ax_m.set_ylabel("M [kN·m]  (sagging +, drawn down)")
    ax_m.set_title("Two-span continuous beam — PyNite")
    ax_m.annotate(f"M_B = {fe['M_B']:.1f}", (L, fe["M_B"]), ha="left",
                  va="top", textcoords="offset points", xytext=(8, 0))

    ax_v.plot(fe["x"], fe["V"], color="tab:red")
    ax_v.fill_between(fe["x"], fe["V"], alpha=0.2, color="tab:red")
    ax_v.axhline(0, color="k", lw=0.8)
    ax_v.set_ylabel("V [kN]")
    ax_v.set_xlabel("x from support A [m]")
    for s in (0, L, 2 * L):
        for ax in (ax_m, ax_v):
            ax.axvline(s, color="grey", ls=":", lw=0.8)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def main():
    p = INPUTS
    fe = solve(**p)
    exact = closed_form(**p)

    print("Given")
    print(f"  Two equal spans L = {p['L']} m, UDL q = {p['q']} kN/m on both spans")
    print(f"  E = {p['E'] / 1e6:.0f} GPa, I = {p['I'] * 1e8:.0f} cm^4  (EI = {p['E'] * p['I']:.0f} kN·m²)")
    print()
    print(f"{'Quantity':<12}{'PyNite':>12}{'Closed form':>14}{'Error':>10}  Check")
    rows = self_check(fe, exact, p["q"], p["L"])
    units = {"R_A": "kN", "R_B": "kN", "R_C": "kN", "M_B": "kN·m",
             "M_span": "kN·m", "delta_max": "mm"}
    for name, v_fe, v_ex, err, ok in rows:
        scale = 1000.0 if name == "delta_max" else 1.0
        unit = units.get(name, "kN")
        print(f"{name:<12}{v_fe * scale:>10.3f} {unit:<4}{v_ex * scale:>9.3f} {unit:<4}"
              f"{err * 100:>6.3f} %  {'PASS' if ok else 'FAIL'}")

    png = os.path.join(HERE, "continuous_beam_pynite.png")
    plot(fe, p["L"], png)
    print(f"\nDiagrams saved: {png}")
    print(f"Deflection ratio: L/δ = {p['L'] / fe['delta_max']:.0f}")

    if not all(ok for *_, ok in rows):
        print("\nSELF-CHECK FAILED — do not trust these results.")
        return 1
    print("\nSelf-check passed: FE matches the closed-form solution within "
          f"{REL_TOL * 100:.1f} %.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
