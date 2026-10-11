"""
Revit beam → section check → PyNite analysis
============================================

Takes the values Claude read from a Revit model with the Revit MCP
(`get_element_data` on a Structural Framing instance and on its type) and:
  1. converts Revit's internal units (feet) to SI,
  2. checks the section data for consistency — type name vs Section Name Key,
     and area / second moment of area vs the plate geometry of the I-section,
  3. analyses the member in PyNite as a simply supported beam under a UDL,
  4. checks the FE result against qL²/8 and 5qL⁴/384EI.

The Revit model has no loads, so the line load q is an INPUT you choose — it is
not read from the model. Support conditions (simply supported) are an
assumption too; state both when you report the result.

Run:  python check_revit_beam.py [beam.json] [q_kN_per_m]
      (defaults: snowdon_W18x55_608386.json, q = 10 kN/m)

Exit codes: 0 = section data consistent and FE check passed,
            1 = FE result does not match the closed form,
            2 = section data in the Revit type is inconsistent (results are
                printed for both stiffness values; do not trust the Revit one).
"""

# ---------------------------------------------------------------------------
# How to verify the AI's answer
# ---------------------------------------------------------------------------
# BIM data is an input, not a truth. Two independent checks run here:
#   * Section: Ix of an I-section from its plates,
#       Ix = [bf·d³ − (bf − tw)·(d − 2tf)³] / 12,
#     must agree with the Revit "Moment of Inertia strong axis" to within
#     SECTION_TOL (root fillets add ~1–2 %, so a few % is normal; a factor of
#     4 is not). Area is checked the same way.
#   * Analysis: PyNite midspan moment and deflection must match qL²/8 and
#     5qL⁴/(384·EI) to within FE_TOL.
# ---------------------------------------------------------------------------

import json
import os
import re
import sys

from Pynite import FEModel3D

for _stream in (sys.stdout, sys.stderr):  # Unicode chars print correctly on Windows
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON = os.path.join(HERE, "snowdon_W18x55_608386.json")

FT = 0.3048           # m per ft (Revit internal length unit)
E = 210e6             # kN/m², steel
G = 81e6              # kN/m², steel
SECTION_TOL = 0.05    # 5 % — plate model vs Revit section property
FE_TOL = 5e-3         # 0.5 % — FE vs closed form


def load_beam(path):
    """Read the JSON written from Revit MCP output and convert to SI (m)."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return {
        "raw": raw,
        "L": raw["system_length_ft"] * FT,
        "d": raw["height_ft"] * FT,
        "bf": raw["width_ft"] * FT,
        "tf": raw["flange_thickness_ft"] * FT,
        "tw": raw["web_thickness_ft"] * FT,
        "A": raw["section_area_ft2"] * FT**2,
        "Ix": raw["Ix_strong_ft4"] * FT**4,
        "Iy": raw["Iy_weak_ft4"] * FT**4,
        "J": raw["J_ft4"] * FT**4,
    }


def plate_properties(d, bf, tf, tw, **_):
    """Area and strong-axis Ix of a doubly symmetric I-section (no fillets)."""
    hw = d - 2 * tf
    A = 2 * bf * tf + hw * tw
    Ix = (bf * d**3 - (bf - tw) * hw**3) / 12
    return A, Ix


def _norm(name):
    return re.sub(r"[^a-z0-9.]", "", name.lower())


def section_checks(b):
    """Return list of (name, revit, independent, rel_diff, ok)."""
    A_p, Ix_p = plate_properties(**b)
    rows = []
    for name, rv, ind in (("A", b["A"], A_p), ("Ix", b["Ix"], Ix_p)):
        diff = (rv - ind) / ind
        rows.append((name, rv, ind, diff, abs(diff) <= SECTION_TOL))
    raw = b["raw"]
    same = _norm(raw["type_name"]) == _norm(raw.get("section_name_key", raw["type_name"]))
    rows.append(("name", raw["type_name"], raw.get("section_name_key", "—"), 0.0, same))
    return rows


def analyse(L, q, A, Ix, Iy, J):
    """Simply supported beam, UDL q (kN/m). Returns M_mid (kN·m), delta (m)."""
    m = FEModel3D()
    m.add_node("A", 0.0, 0.0, 0.0)
    m.add_node("B", L, 0.0, 0.0)
    m.add_material("Steel", E=E, G=G, nu=0.3, rho=0.0)
    # Horizontal member loaded in global Y bends about local z → Iz = Ix.
    m.add_section("Sec", A=A, Iy=Iy, Iz=Ix, J=J)
    m.add_member("AB", "A", "B", "Steel", "Sec")
    m.def_support("A", True, True, True, True, False, False)   # pin (+ torsion)
    m.def_support("B", False, True, True, False, False, False)  # roller
    m.add_member_dist_load("AB", "FY", -q, -q, case="Q")
    m.add_load_combo("C", {"Q": 1.0})
    m.analyze_linear(check_statics=False)
    beam = m.members["AB"]
    return abs(beam.moment("Mz", L / 2, "C")), -beam.min_deflection("dy", "C")


def closed_form(L, q, Ix):
    return q * L**2 / 8, 5 * q * L**4 / (384 * E * Ix)


def main(path=DEFAULT_JSON, q=10.0):
    b = load_beam(path)
    raw = b["raw"]
    print(f"Revit element {raw['element_id']}  type '{raw['type_name']}'  ({raw['source']})")
    print(f"Given: L = {b['L']:.3f} m (System Length), q = {q} kN/m (ASSUMED, not in model),"
          " simply supported (ASSUMED)\n")

    print("Section data check (Revit type vs independent plate model)")
    sec = section_checks(b)
    for name, rv, ind, diff, ok in sec:
        if name == "name":
            print(f"  type name '{rv}' vs Section Name Key '{ind}': {'OK' if ok else 'MISMATCH'}")
        else:
            unit, scale = ("cm²", 1e4) if name == "A" else ("cm⁴", 1e8)
            print(f"  {name:<3} Revit {rv * scale:>9.0f} {unit} | plates {ind * scale:>9.0f} {unit}"
                  f" | {diff * 100:+6.1f} %  {'OK' if ok else 'MISMATCH'}")
    section_ok = all(ok for *_, ok in sec)

    _, Ix_plate = plate_properties(**b)
    cases = [("Revit Ix", b["Ix"])]
    if not section_ok:
        cases.append(("plate Ix", Ix_plate))

    print("\nPyNite analysis vs closed form")
    fe_ok = True
    for label, Ix in cases:
        M, delta = analyse(b["L"], q, b["A"], Ix, b["Iy"], b["J"])
        M_cf, d_cf = closed_form(b["L"], q, Ix)
        ok = abs(M - M_cf) / M_cf <= FE_TOL and abs(delta - d_cf) / d_cf <= FE_TOL
        fe_ok &= ok
        print(f"  {label}: M_mid = {M:.2f} kN·m (qL²/8 = {M_cf:.2f}),"
              f" δ = {delta * 1000:.2f} mm (5qL⁴/384EI = {d_cf * 1000:.2f}),"
              f" L/δ = {b['L'] / delta:.0f}  {'PASS' if ok else 'FAIL'}")

    if not fe_ok:
        print("\nFE CHECK FAILED — do not trust these results.")
        return 1
    if not section_ok:
        print("\nSECTION DATA INCONSISTENT — the Revit type's properties do not match its"
              " geometry. Fix the type (or use catalogue values) before any design check.")
        return 2
    print("\nSection data consistent and FE check passed.")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    sys.exit(main(args[0] if args else DEFAULT_JSON, float(args[1]) if len(args) > 1 else 10.0))
