"""Physics self-checks for the plasticity and SymPy examples."""
import importlib

import pytest

EXAMPLES = [
    "stress_strain_ramberg_osgood",   # examples/plasticity
    "von_mises_yield_check",          # examples/plasticity
    "symbolic_yield_derivation",      # examples/sympy
]


@pytest.mark.parametrize("module_name", EXAMPLES)
def test_example_self_check(module_name):
    module = importlib.import_module(module_name)
    module.self_check()


def test_ramberg_osgood_plastic_strain_at_yield_is_0_2_percent():
    """Regression: the alpha=0.002 mix-up gave 2.5e-6 here instead of 0.002."""
    ro = importlib.import_module("stress_strain_ramberg_osgood")
    E, sigma_y, n = 200e3, 250.0, 10
    total = ro.ramberg_osgood(sigma_y, E, sigma_y, n)
    plastic = total - sigma_y / E
    assert plastic == pytest.approx(0.002, abs=1e-9)
