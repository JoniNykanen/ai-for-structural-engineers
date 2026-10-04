"""Tests for examples/eurocode/timber/glulam_beam_ec5.py.

All parameter values come from tests/fixtures/na_timber.test.yaml, which holds
artificial round numbers (TEST-ONLY, NOT standard values). Expected results are
hand-computed below from those numbers.

Run:  .venv\\Scripts\\python.exe -m pytest tests/test_glulam_ec5.py
"""

import importlib.util
import os

import pytest
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FIXTURE = os.path.join(HERE, "fixtures", "na_timber.test.yaml")
SCRIPT = os.path.join(REPO, "examples", "eurocode", "timber", "glulam_beam_ec5.py")

_spec = importlib.util.spec_from_file_location("glulam_beam_ec5", SCRIPT)
ec5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ec5)

# Fixture values used in the hand calcs:
#   f_m_k=20, f_v_k=2, E0_mean=10000 N/mm^2, gamma_M=1.0
#   kmod: permanent=0.4, long_term=0.5, medium_term=0.6
#   k_def=1.0, k_cr=1.0
#   gamma_G_610a=2.0, gamma_G_610b=1.0, gamma_Q=2.0, KFI=1.0, psi2_snow=0.5
#   snow_duration=medium_term, w_inst_ratio=200, w_net_fin_ratio=100
#
# Section for all cases: b=100 mm, h=400 mm, L=4 m
#   W = 100*400^2/6  = 2 666 666.67 mm^3
#   I = 100*400^3/12 = 533 333 333.3 mm^4
#   E*I = 1e4 * 5.3333e8 = 5.3333e12 N*mm^2
SECTION = {"L": 4.0, "b": 100.0, "h": 400.0}


def write_params(tmp_path, mutate):
    """Copy the fixture to tmp_path after applying mutate(dict)."""
    with open(FIXTURE, encoding="utf-8") as f:
        p = yaml.safe_load(f)
    mutate(p)
    out = tmp_path / "params.yaml"
    out.write_text("# TEST-ONLY — NOT standard values.\n" + yaml.safe_dump(p), encoding="utf-8")
    return str(out)


def test_610b_governs():
    # g_k=1, s_k=4 kN/m
    # 6.10a: qd = 1.0*2.0*1                 = 2.0 kN/m, kmod 0.4 -> qd/kmod = 5.0
    # 6.10b: qd = 1.0*(1.0*1 + 2.0*4)       = 9.0 kN/m, kmod 0.6 -> qd/kmod = 15.0  <- governs
    # M_d = 9*4^2/8 = 18 kN*m ; sigma = 18e6/2 666 666.67 = 6.75 N/mm^2
    # f_m_d = 0.6*20/1.0 = 12 ; util_m = 6.75/12 = 0.5625
    # V_d = 9*4/2 = 18 kN ; tau = 1.5*18000/(1.0*100*400) = 0.675 ; f_v_d = 0.6*2 = 1.2
    # util_v = 0.5625
    # w_g = 5*1*4000^4/(384*5.3333e12) = 1.28e15/2.048e15 = 0.625 mm ; w_s = 4*0.625 = 2.5 mm
    # w_inst = 3.125 mm ; w_fin = 0.625*(1+1) + 2.5*(1+0.5*1) = 1.25 + 3.75 = 5.0 mm
    # limits: 4000/200 = 20 mm, 4000/100 = 40 mm
    r = ec5.calculate(FIXTURE, {**SECTION, "g_k": 1.0, "s_k": 4.0})
    assert r["name"].startswith("6.10b")
    assert r["snow_duration"] == "medium_term"
    assert r["qd"] == pytest.approx(9.0)
    assert r["kmod"] == pytest.approx(0.6)
    assert r["M_d"] == pytest.approx(18.0)
    assert r["sigma_m_d"] == pytest.approx(6.75)
    assert r["util_m"] == pytest.approx(0.5625)
    assert r["V_d"] == pytest.approx(18.0)
    assert r["tau_d"] == pytest.approx(0.675)
    assert r["util_v"] == pytest.approx(0.5625)
    assert r["w_inst_tot"] == pytest.approx(3.125)
    assert r["w_fin"] == pytest.approx(5.0)
    assert r["w_inst_lim"] == pytest.approx(20.0)
    assert r["w_fin_lim"] == pytest.approx(40.0)


def test_610a_governs_large_gk_small_sk():
    # g_k=10, s_k=1 kN/m
    # 6.10a: qd = 2.0*10          = 20 kN/m, kmod 0.4 -> qd/kmod = 50  <- governs
    # 6.10b: qd = 1.0*10 + 2.0*1  = 12 kN/m, kmod 0.6 -> qd/kmod = 20
    # M_d = 20*16/8 = 40 kN*m ; sigma = 40e6/2 666 666.67 = 15.0 ; f_m_d = 0.4*20 = 8
    # util_m = 1.875
    # V_d = 20*4/2 = 40 kN ; tau = 1.5*40000/40000 = 1.5 ; f_v_d = 0.4*2 = 0.8 ; util_v = 1.875
    r = ec5.calculate(FIXTURE, {**SECTION, "g_k": 10.0, "s_k": 1.0})
    assert r["name"].startswith("6.10a")
    assert r["qd"] == pytest.approx(20.0)
    assert r["kmod"] == pytest.approx(0.4)
    assert r["sigma_m_d"] == pytest.approx(15.0)
    assert r["f_m_d"] == pytest.approx(8.0)
    assert r["util_m"] == pytest.approx(1.875)
    assert r["tau_d"] == pytest.approx(1.5)
    assert r["util_v"] == pytest.approx(1.875)


def test_snow_duration_selects_kmod(tmp_path):
    # long_term -> kmod_snow = 0.5 ; 6.10b qd = 9.0, qd/kmod = 18 (> 5) -> governs
    # f_m_d = 0.5*20 = 10 ; util_m = 6.75/10 = 0.675
    path = write_params(tmp_path, lambda p: p["actions"].update(snow_duration="long_term"))
    r = ec5.calculate(path, {**SECTION, "g_k": 1.0, "s_k": 4.0})
    assert r["snow_duration"] == "long_term"
    assert r["kmod"] == pytest.approx(0.5)
    assert r["util_m"] == pytest.approx(0.675)


@pytest.mark.parametrize("section,key", [
    ("actions", "gamma_G_610a"),
    ("actions", "gamma_G_610b"),
    ("actions", "snow_duration"),
    ("k_mod", "permanent"),
])
def test_missing_field_stops(tmp_path, section, key):
    path = write_params(tmp_path, lambda p: p[section].pop(key))
    with pytest.raises(SystemExit) as exc:
        ec5.calculate(path, {**SECTION, "g_k": 1.0, "s_k": 4.0})
    assert f"Puuttuva arvo: '{section}.{key}'" in str(exc.value)


def test_invalid_snow_duration_stops(tmp_path):
    path = write_params(tmp_path, lambda p: p["actions"].update(snow_duration="short_term"))
    with pytest.raises(SystemExit) as exc:
        ec5.calculate(path, {**SECTION, "g_k": 1.0, "s_k": 4.0})
    assert "actions.snow_duration" in str(exc.value)


@pytest.mark.parametrize("g_k,s_k", [(1.0, 4.0), (10.0, 1.0)])
def test_cross_check_passes(g_k, s_k):
    # Numerical integration (equilibrium + trapezoid) must reproduce the closed
    # forms within 1e-3: M_max = qL^2/8, V_max = qL/2, w_mid = 5qL^4/(384EI).
    r = ec5.calculate(FIXTURE, {**SECTION, "g_k": g_k, "s_k": s_k})
    cc = r["cross"]
    assert cc["ok"], cc["deltas"]
    assert cc["M_num"] == pytest.approx(r["M_d"], rel=1e-3)
    assert cc["V_num"] == pytest.approx(r["V_d"], rel=1e-3)
    assert cc["w_num"] == pytest.approx(r["w_inst_tot"], rel=1e-3)


def test_beam_numeric_is_independent_of_closed_form():
    # q = 1 N/mm, L = 1000 mm, EI = 1e9: expected R = 500 N, M_max = 1.25e5 N*mm,
    # w_mid = 5*1*1000^4/(384*1e9) = 0.01302 mm. Computed only by integration.
    out = ec5.beam_numeric(1.0, 1000.0, EI=1e9)
    assert out["R_A"] == pytest.approx(500.0, rel=1e-6)
    assert out["R_B"] == pytest.approx(500.0, rel=1e-6)
    assert out["M"].max() == pytest.approx(1.25e5, rel=1e-4)
    assert out["w"][len(out["w"]) // 2] == pytest.approx(5e12 / 384e9, rel=1e-4)


def test_cli_exits_nonzero_when_cross_check_fails(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(ec5, "cross_check",
                        lambda r: {"ok": False, "deltas": {"M": 1.0},
                                   "M_num": 0.0, "V_num": 0.0, "w_num": 0.0})
    note = tmp_path / "note.md"
    assert ec5.main([FIXTURE], note_path=str(note)) != 0
    assert "ERO HAVAITTU" in note.read_text(encoding="utf-8")


def test_cli_ok_and_note_flags_test_params(tmp_path, capsys):
    note = tmp_path / "note.md"
    assert ec5.main([FIXTURE], note_path=str(note)) == 0
    text = note.read_text(encoding="utf-8")
    assert "DUMMY/TEST" in text
    assert "käyttäjän lisensoidusta" not in text         # no false licensed-source claim
    assert "medium_term" in text                         # snow duration class printed
    assert "Ristiintarkistus" in capsys.readouterr().out
