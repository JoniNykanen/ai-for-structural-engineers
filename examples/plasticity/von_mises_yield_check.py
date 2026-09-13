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

import numpy as np


def yield_check(sigma, sigma_y):
    """sigma: 3x3 stress tensor (MPa). sigma_y: yield strength (MPa)."""
    sigma = np.asarray(sigma, dtype=float)

    # Principal stresses = eigenvalues of the (symmetric) stress tensor.
    principal = np.sort(np.linalg.eigvalsh(sigma))[::-1]  # s1 >= s2 >= s3
    s1, s2, s3 = principal

    # von Mises equivalent stress (from principal stresses).
    von_mises = np.sqrt(0.5 * ((s1 - s2) ** 2 + (s2 - s3) ** 2 + (s3 - s1) ** 2))

    # Tresca equivalent stress = max shear diameter = s1 - s3.
    tresca = s1 - s3

    return {
        "principal": principal,
        "von_mises": von_mises,
        "tresca": tresca,
        "n_vm": sigma_y / von_mises,
        "n_tresca": sigma_y / tresca,
    }


def main():
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
