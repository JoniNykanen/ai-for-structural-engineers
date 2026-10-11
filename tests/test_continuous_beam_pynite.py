"""Tests for examples/frame/continuous_beam_pynite.py.

PyNite's results are compared to the exact two-span continuous beam solution
(equal spans L, UDL q, constant EI):
  R_A = R_C = 3qL/8, R_B = 10qL/8, M_B = -qL^2/8, M_span = 9qL^2/128,
  delta_max = 0.005416 qL^4/EI.

Run:  .venv\\Scripts\\python.exe -m pytest tests/test_continuous_beam_pynite.py
"""

import importlib.util
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SCRIPT = os.path.join(REPO, "examples", "frame", "continuous_beam_pynite.py")

_spec = importlib.util.spec_from_file_location("continuous_beam_pynite", SCRIPT)
cb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cb)

REL = 5e-3


@pytest.fixture(scope="module")
def default_run():
    return cb.solve(**cb.INPUTS)


def test_hand_calc_values(default_run):
    # L = 6 m, q = 10 kN/m:
    #   R_A = 3*10*6/8 = 22.5 kN, R_B = 10*10*6/8 = 75 kN
    #   M_B = -10*36/8 = -45 kN*m, M_span = 9*10*36/128 = 25.3125 kN*m
    fe = default_run
    assert fe["R_A"] == pytest.approx(22.5, rel=REL)
    assert fe["R_B"] == pytest.approx(75.0, rel=REL)
    assert fe["R_C"] == pytest.approx(22.5, rel=REL)
    assert fe["M_B"] == pytest.approx(-45.0, rel=REL)
    assert fe["M_span"] == pytest.approx(25.3125, rel=REL)


def test_deflection_matches_closed_form(default_run):
    exact = cb.closed_form(**cb.INPUTS)
    assert exact["delta_max"] == pytest.approx(
        0.005416 * 10 * 6**4 / (210e6 * 8356e-8), rel=1e-3)
    assert default_run["delta_max"] == pytest.approx(exact["delta_max"], rel=REL)


def test_equilibrium(default_run):
    total = default_run["R_A"] + default_run["R_B"] + default_run["R_C"]
    assert total == pytest.approx(2 * 10.0 * 6.0, rel=1e-9)


def test_moments_independent_of_EI():
    # Equal spans + constant EI: reactions and M_B must not change with EI.
    stiff = dict(cb.INPUTS, I=cb.INPUTS["I"] * 10)
    fe = cb.solve(**stiff, n_points=21)
    assert fe["M_B"] == pytest.approx(-45.0, rel=REL)
    assert fe["R_B"] == pytest.approx(75.0, rel=REL)


@pytest.mark.parametrize("L,q", [(4.0, 5.0), (8.0, 25.0)])
def test_self_check_passes_for_other_inputs(L, q):
    p = dict(cb.INPUTS, L=L, q=q)
    rows = cb.self_check(cb.solve(**p, n_points=101), cb.closed_form(**p), q, L)
    assert all(ok for *_, ok in rows), rows


def test_main_writes_plot_and_exits_zero(tmp_path, monkeypatch):
    monkeypatch.setattr(cb, "HERE", str(tmp_path))
    assert cb.main() == 0
    assert (tmp_path / "continuous_beam_pynite.png").exists()
