"""Tests for examples/eurocode/steel/rhs_member_ec3.py.

Section properties are checked against limit cases with exact closed forms
(sharp corners, r = 0) and against the independent numerical integration;
the buckling curve against a hand-computed point. Code values come from the
TEST-ONLY fixture tests/fixtures/na_steel.test.yaml (artificial numbers).

Run:  .venv\\Scripts\\python.exe -m pytest tests/test_rhs_member_ec3.py
"""

import importlib.util
import math
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SCRIPT = os.path.join(REPO, "examples", "eurocode", "steel", "rhs_member_ec3.py")
FIXTURE = os.path.join(HERE, "fixtures", "na_steel.test.yaml")

_spec = importlib.util.spec_from_file_location("rhs_member_ec3", SCRIPT)
rm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rm)


def test_sharp_corner_limit_matches_box_formulas():
    # r_o = r_i = 0: hollow rectangle, exact textbook formulas.
    b, h, t = 100.0, 200.0, 10.0
    s = rm.rhs_properties(b, h, t, 0.0, 0.0)
    bi, hi = b - 2 * t, h - 2 * t
    assert s["A"] == pytest.approx(b * h - bi * hi)
    assert s["Iy"] == pytest.approx((b * h**3 - bi * hi**3) / 12)
    assert s["Iz"] == pytest.approx((h * b**3 - hi * bi**3) / 12)
    assert s["Wpl_y"] == pytest.approx((b * h**2 - bi * hi**2) / 4)
    assert s["Wpl_z"] == pytest.approx((h * b**2 - hi * bi**2) / 4)


@pytest.mark.parametrize("b,h,t,ro", [(150, 150, 6, 12), (200, 100, 8, 20), (70, 50, 3, 6)])
def test_closed_form_matches_numeric_integration(b, h, t, ro):
    ri = ro - t
    s = rm.rhs_properties(b, h, t, ro, ri)
    n = rm.rhs_properties_numeric(b, h, t, ro, ri)
    for k in n:
        assert s[k] == pytest.approx(n[k], rel=1e-4), k


def test_square_section_is_symmetric():
    s = rm.rhs_properties(120, 120, 5, 10, 5)
    assert s["Iy"] == pytest.approx(s["Iz"])
    assert s["Wpl_y"] == pytest.approx(s["Wpl_z"])


def test_rounded_corners_reduce_area():
    sharp = rm.rhs_properties(150, 150, 6, 0, 0)
    round_ = rm.rhs_properties(150, 150, 6, 12, 6)
    # Each corner loses (4 - π)/4 · (r_o² − r_i²) of material.
    assert sharp["A"] - round_["A"] == pytest.approx((4 - math.pi) * (12**2 - 6**2))


def test_buckling_curve_hand_value():
    # Choose N_cr = A·f_y → λ̄ = 1.0; α = 0.49:
    #   Φ = 0.5·(1 + 0.49·0.8 + 1) = 1.196, χ = 1/(1.196 + √(1.196² − 1)) = 0.5399
    A, fy, E, L = 1000.0, 300.0, 200000.0, 1000.0
    I = A * fy * L**2 / (math.pi**2 * E)
    r = rm.flexural_buckling(A, I, fy, E, L, 0.49, 1.0)
    assert r["lam"] == pytest.approx(1.0)
    assert r["phi"] == pytest.approx(1.196)
    assert r["chi"] == pytest.approx(0.5399, abs=1e-4)


def test_stocky_member_has_no_reduction():
    r = rm.flexural_buckling(1000.0, 1e9, 300.0, 200000.0, 100.0, 0.49, 1.0)
    assert r["lam"] <= 0.2 and r["chi"] == 1.0


def test_calculate_with_test_fixture():
    v = rm.calculate(FIXTURE)
    assert v["dummy"] and v["cross_ok"]
    assert (v["r_o"], v["r_i"]) == (9.0, 3.0)          # 1.5·6 from the fixture
    assert v["cls"] in (1, 2)
    # Hand check of N_c,Rd and the 6.61 interaction from the module's own pieces.
    assert v["N_cRd"] == pytest.approx(v["sec"]["A"] * 300.0)
    ny = 400e3 / v["by"]["N_bRd"]
    assert v["utils"]["yhteisvaikutus (6.61)"] == pytest.approx(
        ny + v["k_yy"] * 8e6 / v["M_cRd"])
    assert v["k_yy"] <= 0.9 * (1 + 0.8 * ny) + 1e-12


def test_missing_value_stops(tmp_path):
    bad = tmp_path / "na_steel.yaml"
    bad.write_text(open(FIXTURE, encoding="utf-8").read().replace(
        "alpha_cold_formed_hollow: 0.5", "alpha_cold_formed_hollow:"), encoding="utf-8")
    with pytest.raises(SystemExit, match="alpha_cold_formed_hollow"):
        rm.calculate(str(bad))


def test_main_exits_zero_with_fixture():
    assert rm.main([FIXTURE]) == 0
