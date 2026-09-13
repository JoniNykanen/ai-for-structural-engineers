"""
Ramberg-Osgood stress-strain curve  (Python / NumPy / Matplotlib)
=================================================================

The Ramberg-Osgood model describes an elastic-plastic uniaxial stress-strain
curve with smooth yielding:

    epsilon = sigma/E + alpha * (sigma/sigma_y)^n * (sigma_y/E)

Run:  python stress_strain_ramberg_osgood.py
Saves 'ramberg_osgood.png' next to this script. No MATLAB license required.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")  # save to file instead of opening a window (more reliable)
import matplotlib.pyplot as plt


def ramberg_osgood(sigma, E, sigma_y, alpha, n):
    """Total strain for a given stress array (consistent units)."""
    return sigma / E + alpha * (sigma / sigma_y) ** n * (sigma_y / E)


def main():
    # --- Inputs (edit these) ---
    E = 200e3        # Young's modulus, MPa (200 GPa)
    sigma_y = 250.0  # nominal yield strength, MPa
    alpha = 0.002    # yield offset parameter
    n = 10           # hardening exponent

    sigma = np.linspace(0, 1.6 * sigma_y, 400)  # MPa
    eps = ramberg_osgood(sigma, E, sigma_y, alpha, n)

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(eps, sigma, lw=2, label="Ramberg–Osgood")
    ax.axhline(sigma_y, ls="--", color="grey", lw=1)
    ax.text(eps[-1], sigma_y, "  σy", va="bottom", ha="right", color="grey")
    ax.set_xlabel("Strain  ε  [-]")
    ax.set_ylabel("Stress  σ  [MPa]")
    ax.set_title(f"Ramberg–Osgood  (E={E/1e3:.0f} GPa, σy={sigma_y:.0f} MPa, n={n})")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "ramberg_osgood.png")
    fig.savefig(out, dpi=130)
    print(f"Saved figure to: {out}")
    print(f"At sigma = sigma_y = {sigma_y:.0f} MPa, total strain = "
          f"{ramberg_osgood(sigma_y, E, sigma_y, alpha, n):.5f}")


if __name__ == "__main__":
    main()
