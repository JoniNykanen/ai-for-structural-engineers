"""
von Mises & Tresca yield check  (Python / NumPy)
================================================

Given a 3x3 Cauchy stress tensor and a yield strength, this:
  1. finds the principal stresses (eigenvalues of the stress tensor),
  2. computes the von Mises equivalent stress,
  3. computes the Tresca equivalent stress,
  4. reports the factor of safety for each criterion.

Run:  python von_mises_yield_check.py

No MATLAB license required.
"""

# ---------------------------------------------------------------------------
# How to verify the AI's answer
# ---------------------------------------------------------------------------
# Feed the code stress states whose answer you already know from the textbook.
# self_check() below does exactly that:
#   * uniaxial tension sigma      -> von Mises = sigma,       Tresca = sigma
#   * pure shear tau              -> von Mises = sqrt(3)*tau, Tresca = 2*tau
#   * hydrostatic pressure p      -> von Mises = 0, Tresca = 0 (no yielding)
#   * any state: von Mises <= Tresca <= (2/sqrt(3)) * von Mises
#   * units: factor of safety is dimensionless -> same in MPa and in Pa.
# If the code gets a known case wrong, do not trust it on your real problem.
# ---------------------------------------------------------------------------

import numpy as np


def yield_check(sigma, sigma_y):
    """sigma: 3x3 stress tensor (MPa). sigma_y: yield strength (MPa)."""
    sigma = np.asarray(sigma, dtype=float)

    # Principal stresses = eigenvalues of the (symmetric) stress tensor.
    principal = np.sort(np.linalg.eigvalsh(sigma))[::-1]  # s1 >= s2 >= s3
    s1, s2, s3 = principal

    # von Mises equivalent stress (from principal stresses).
    von_mises = np.sqrt(0.5 * ((s1 - s2) ** 2 + (s2 - s3) ** 2 + (s3 - s1) ** 2))

    # Tresca equivalent stress = diameter of the largest Mohr circle = s1 - s3
    # (= 2 * maximum shear stress).
    tresca = s1 - s3

    # Pure hydrostatic stress gives zero equivalent stress -> infinite safety.
    return {
        "principal": principal,
        "von_mises": von_mises,
        "tresca": tresca,
        "n_vm": sigma_y / von_mises if von_mises > 0 else np.inf,
        "n_tresca": sigma_y / tresca if tresca > 0 else np.inf,
    }


def self_check():
    """Physics checks against textbook cases. Raises AssertionError on failure."""
    sy = 250.0  # MPa
    tol = 1e-9

    # 1) Uniaxial tension: both criteria reduce to the applied stress.
    s = 100.0
    r = yield_check([[s, 0, 0], [0, 0, 0], [0, 0, 0]], sy)
    assert abs(r["von_mises"] - s) < tol, f"uniaxial: von Mises should be {s}, got {r['von_mises']}"
    assert abs(r["tresca"] - s) < tol, f"uniaxial: Tresca should be {s}, got {r['tresca']}"

    # 2) Pure shear: von Mises = sqrt(3)*tau, Tresca = 2*tau.
    tau = 50.0
    r = yield_check([[0, tau, 0], [tau, 0, 0], [0, 0, 0]], sy)
    assert abs(r["von_mises"] - np.sqrt(3) * tau) < tol, (
        f"pure shear: von Mises should be sqrt(3)*tau = {np.sqrt(3) * tau:.4f}, got {r['von_mises']:.4f}")
    assert abs(r["tresca"] - 2 * tau) < tol, (
        f"pure shear: Tresca should be 2*tau = {2 * tau}, got {r['tresca']}")
    # Principal stresses of pure shear are +tau, 0, -tau.
    assert np.allclose(r["principal"], [tau, 0, -tau], atol=tol), "pure shear principals should be +tau, 0, -tau"

    # 3) Hydrostatic pressure never causes yielding (metals are pressure-insensitive).
    r = yield_check(-80.0 * np.eye(3), sy)
    assert abs(r["von_mises"]) < tol and abs(r["tresca"]) < tol, "hydrostatic stress must give zero equivalent stress"
    assert r["n_vm"] == np.inf, "hydrostatic stress: factor of safety should be infinite"

    # 4) General bound: von Mises <= Tresca <= 2/sqrt(3) * von Mises.
    general = [[180.0, 40.0, -20.0], [40.0, 60.0, 15.0], [-20.0, 15.0, -30.0]]
    r = yield_check(general, sy)
    assert r["von_mises"] <= r["tresca"] + tol, "Tresca equivalent stress must be >= von Mises"
    assert r["tresca"] <= 2 / np.sqrt(3) * r["von_mises"] + tol, "Tresca must be <= 1.155 * von Mises"

    # 5) Units: scaling all stresses (MPa -> Pa) must not change the factor of safety.
    r_pa = yield_check(np.asarray(general) * 1e6, sy * 1e6)
    assert abs(r_pa["n_vm"] - r["n_vm"]) < 1e-12, "factor of safety must be dimensionless"


def main():
    self_check()

    # --- Inputs (edit these) ---
    sigma = [[180.0, 40.0, 0.0],
             [ 40.0, 60.0, 0.0],
             [  0.0,  0.0, 0.0]]   # MPa
    sigma_y = 250.0                # MPa

    r = yield_check(sigma, sigma_y)
    s1, s2, s3 = r["principal"]

    print("=== von Mises / Tresca yield check ===")
    print(f"Principal stresses:  s1={s1:8.2f}  s2={s2:8.2f}  s3={s3:8.2f}  MPa")
    print(f"von Mises stress:    {r['von_mises']:8.2f} MPa")
    print(f"Tresca stress:       {r['tresca']:8.2f} MPa")
    print(f"Yield strength:      {sigma_y:8.2f} MPa")
    print("-" * 40)
    print(f"Factor of safety (von Mises): {r['n_vm']:.3f}")
    print(f"Factor of safety (Tresca):    {r['n_tresca']:.3f}")
    print("-" * 40)
    yielding = r["von_mises"] >= sigma_y
    print("Result (von Mises):", "YIELDING" if yielding else "SAFE (elastic)")
    print("Note: Tresca is always the more conservative (lower FoS) criterion.")


if __name__ == "__main__":
    main()
