"""Tests for examples/revit/check_revit_beam.py.

Uses the values read from the Revit 2027 sample model (Snowdon Towers
Structural, element 608386). That type is named W18x55 but carries W12X26
stiffness data, so the script must flag it. A corrected copy (Ix from the
plate geometry, matching name key) must pass.

Run:  .venv\\Scripts\\python.exe -m pytest tests/test_check_revit_beam.py
"""

import importlib.util
import json
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SCRIPT = os.path.join(REPO, "examples", "revit", "check_revit_beam.py")
SAMPLE = os.path.join(REPO, "examples", "revit", "snowdon_W18x55_608386.json")

_spec = importlib.util.spec_from_file_location("check_revit_beam", SCRIPT)
crb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(crb)

IN = 0.0254


def test_unit_conversion():
    b = crb.load_beam(SAMPLE)
    assert b["L"] == pytest.approx(17.33333333333 * 0.3048)    # 17'-4" = 5.283 m
    assert b["d"] == pytest.approx(18.100 * IN)
    assert b["Ix"] == pytest.approx(204.0 * IN**4, rel=1e-6)   # Revit shows 204 in^4
    assert b["A"] == pytest.approx(16.20 * IN**2, rel=1e-6)


def test_plate_ix_close_to_catalogue_w18x55():
    # AISC W18x55: Ix = 890 in^4. Plates without fillets give a little less.
    b = crb.load_beam(SAMPLE)
    _, Ix = crb.plate_properties(**b)
    assert Ix / IN**4 == pytest.approx(890, rel=0.02)


def test_sample_model_is_flagged():
    rows = {r[0]: r for r in crb.section_checks(crb.load_beam(SAMPLE))}
    assert rows["A"][4] is True
    assert rows["Ix"][4] is False          # 204 vs ~879 in^4
    assert rows["name"][4] is False        # W18x55 vs W12X26
    assert crb.main(SAMPLE, 10.0) == 2


def test_fe_matches_closed_form():
    b = crb.load_beam(SAMPLE)
    q = 10.0
    M, delta = crb.analyse(b["L"], q, b["A"], b["Ix"], b["Iy"], b["J"])
    M_cf, d_cf = crb.closed_form(b["L"], q, b["Ix"])
    assert M == pytest.approx(M_cf, rel=crb.FE_TOL)
    assert delta == pytest.approx(d_cf, rel=crb.FE_TOL)
    assert M_cf == pytest.approx(10 * 5.2832**2 / 8, rel=1e-3)  # 34.89 kN*m


def test_consistent_beam_passes(tmp_path):
    with open(SAMPLE, encoding="utf-8") as f:
        raw = json.load(f)
    b = crb.load_beam(SAMPLE)
    _, Ix = crb.plate_properties(**b)
    raw["Ix_strong_ft4"] = Ix / 0.3048**4
    raw["section_name_key"] = "W18X55"
    path = tmp_path / "fixed.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    assert crb.main(str(path), 10.0) == 0
