"""
Ramberg-Osgood stress-strain curve  (Python / NumPy / Matplotlib)
=================================================================

The Ramberg-Osgood model describes an elastic-plastic uniaxial stress-strain
curve with smooth yielding. This script uses the "0.2 % offset" form:

    epsilon = sigma/E  +  0.002 * (sigma/sigma_y)^n
              -------     -------------------------
              elastic     plastic

Why this form? sigma_y is defined as the 0.2 % proof stress: the stress at
which the permanent (plastic) strain is 0.002. Put sigma = sigma_y into the
plastic term and you get exactly 0.002, so the formula matches the definition.

Beware: textbooks also write the SAME model as

    epsilon = sigma/E + alpha * (sigma/sigma_y)^n * (sigma_y/E)

and there alpha is NOT 0.002. Matching the two forms gives
alpha = 0.002 * E / sigma_y  (= 1.6 for E = 200 GPa, sigma_y = 250 MPa).
Plugging alpha = 0.002 into this second form is a common mistake: the plastic
strain at sigma_y becomes 2.5e-6 instead of 0.002 and the curve stays almost
straight. So: alpha depends on which form you use. Always check which one!

Run:  python stress_strain_ramberg_osgood.py
Saves 'ramberg_osgood.png' next to this script. No MATLAB license required.
"""

# ---------------------------------------------------------------------------
# How to verify the AI's answer
# ---------------------------------------------------------------------------
# Code that runs is not the same as code that is right. self_check() below
# tests the PHYSICS, not just the code:
#   * definition check: plastic strain at sigma = sigma_y must be 0.002,
#   * limit cases: zero stress -> zero strain; low stress -> pure Hooke's law,
#   * both textbook forms (offset form and alpha form) give the same curve,
#   * units: strain is dimensionless, so MPa and Pa inputs give equal strain,
#   * physics sense: more stress always means more strain.
# If any of these fail, the formula or the parameters are wrong.
# ---------------------------------------------------------------------------

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")  # save to file instead of opening a window (more reliable)
import matplotlib.pyplot as plt

PROOF_STRAIN = 0.002  # 0.2 % offset that defines sigma_y


def ramberg_osgood(sigma, E, sigma_y, n, offset=PROOF_STRAIN):
    """Total strain for a given stress (consistent units, e.g. MPa).

    0.2 %-offset form: eps = sigma/E + offset * (sigma/sigma_y)^n
    """
    return sigma / E + offset * (sigma / sigma_y) ** n


def plastic_strain(sigma, E, sigma_y, n, offset=PROOF_STRAIN):
    """Permanent strain = total strain minus the elastic part sigma/E."""
    return ramberg_osgood(sigma, E, sigma_y, n, offset) - sigma / E


def self_check():
    """Physics checks. Raises AssertionError if the model is wrong."""
    E, sigma_y, n = 200e3, 250.0, 10  # MPa, MPa, -

    # 1) Definition: plastic strain at sigma_y is the 0.2 % offset.
    ep = plastic_strain(sigma_y, E, sigma_y, n)
    assert abs(ep - 0.002) < 1e-9, (
        f"plastic strain at sigma_y should be 0.002, got {ep:.3e}")

    # 2) Limit case: no stress, no strain.
    assert ramberg_osgood(0.0, E, sigma_y, n) == 0.0, "zero stress must give zero strain"

    # 3) Limit case: well below yield the material is (almost) linear elastic.
    s_low = 0.1 * sigma_y
    eps_low = ramberg_osgood(s_low, E, sigma_y, n)
    assert abs(eps_low - s_low / E) / (s_low / E) < 1e-6, (
        "at 10 % of sigma_y the strain should be ~ Hooke's law sigma/E")

    # 4) Equivalent textbook form: alpha * (s/sy)^n * (sy/E), alpha = 0.002*E/sy.
    alpha = 0.002 * E / sigma_y
    assert abs(alpha - 1.6) < 1e-12, f"alpha should be 1.6 here, got {alpha}"
    s = np.linspace(0, 1.5 * sigma_y, 50)
    eps_alpha_form = s / E + alpha * (s / sigma_y) ** n * (sigma_y / E)
    assert np.allclose(ramberg_osgood(s, E, sigma_y, n), eps_alpha_form,
                       rtol=1e-12, atol=0), "offset form and alpha form disagree"

    # 5) Units: strain is dimensionless -> same answer in MPa and in Pa.
    eps_mpa = ramberg_osgood(300.0, E, sigma_y, n)
    eps_pa = ramberg_osgood(300.0e6, E * 1e6, sigma_y * 1e6, n)
    assert abs(eps_mpa - eps_pa) < 1e-12, "strain changed when units changed"

    # 6) Physical sense: strain grows monotonically with stress.
    assert np.all(np.diff(ramberg_osgood(s, E, sigma_y, n)) > 0), (
        "strain must increase with stress")


def main():
    self_check()

    # --- Inputs (edit these) ---
    E = 200e3        # Young's modulus, MPa (200 GPa)
    sigma_y = 250.0  # 0.2 % proof (yield) strength, MPa
    n = 10           # hardening exponent

    # Up to 1.3*sigma_y: plastic strain there is 0.002*1.3^10 ~ 0.028.
    sigma = np.linspace(0, 1.3 * sigma_y, 400)  # MPa
    eps = ramberg_osgood(sigma, E, sigma_y, n)

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(eps, sigma, lw=2, label="Ramberg–Osgood")
    ax.axhline(sigma_y, ls="--", color="grey", lw=1)
    ax.text(eps[-1], sigma_y, "  σy", va="bottom", ha="right", color="grey")
    # 0.2 % offset line: slope E, starting at strain 0.002. It meets the curve at sigma_y.
    s_off = np.linspace(0, 1.1 * sigma_y, 50)
    ax.plot(PROOF_STRAIN + s_off / E, s_off, ls=":", color="tab:red", lw=1,
            label="0.2 % offset line")
    ax.set_xlabel("Strain  ε  [-]")
    ax.set_ylabel("Stress  σ  [MPa]")
    ax.set_title(f"Ramberg–Osgood  (E={E/1e3:.0f} GPa, σy={sigma_y:.0f} MPa, n={n})")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "ramberg_osgood.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"Saved figure to: {out}")
    print(f"At sigma = sigma_y = {sigma_y:.0f} MPa:")
    print(f"  total strain   = {ramberg_osgood(sigma_y, E, sigma_y, n):.5f}")
    print(f"  plastic strain = {plastic_strain(sigma_y, E, sigma_y, n):.5f}"
          "  (should be 0.00200 = the 0.2 % offset)")


if __name__ == "__main__":
    main()
