"""
Symbolic derivation of the von Mises yield function  (SymPy)
============================================================

Shows the *algebra*, done exactly (no rounding):
  1. split the stress tensor into hydrostatic + deviatoric parts,
  2. form the second deviatoric invariant J2,
  3. write the von Mises equivalent stress sigma_vm = sqrt(3*J2),
  4. differentiate the yield function f = sigma_vm - sigma_y to get the
     associated-flow direction dEps^p ~ df/dsigma.

Run:  python symbolic_yield_derivation.py
No MATLAB license required.
"""

import sympy as sp


def main():
    # Symbolic stress components.
    sx, sy, sz, txy, tyz, tzx, sig_y = sp.symbols(
        "sigma_x sigma_y sigma_z tau_xy tau_yz tau_zx sigma_Y", real=True)

    sigma = sp.Matrix([[sx,  txy, tzx],
                       [txy, sy,  tyz],
                       [tzx, tyz, sz]])

    # Hydrostatic (mean) stress and deviatoric stress tensor.
    p = sigma.trace() / 3
    s = sigma - p * sp.eye(3)

    # Second deviatoric invariant J2 = 1/2 s:s.
    J2 = sp.Rational(1, 2) * sum((s[i, j])**2 for i in range(3) for j in range(3))
    J2 = sp.simplify(J2)

    # von Mises equivalent stress.
    sigma_vm = sp.sqrt(3 * J2)

    print("Deviatoric stress tensor s =")
    sp.pprint(s)
    print("\nJ2 (second deviatoric invariant) =")
    sp.pprint(sp.expand(J2))
    print("\nvon Mises equivalent stress sigma_vm = sqrt(3*J2) =")
    sp.pprint(sp.simplify(sigma_vm))

    # Associated flow rule: dEps^p is proportional to df/dsigma, f = sigma_vm - sigma_Y.
    f = sigma_vm - sig_y
    print("\nAssociated flow directions df/dsigma_ij (plastic strain increment ~ these):")
    for name, var in [("sigma_x", sx), ("sigma_y", sy), ("sigma_z", sz),
                      ("tau_xy", txy), ("tau_yz", tyz), ("tau_zx", tzx)]:
        d = sp.simplify(sp.diff(f, var))
        print(f"  df/d{name} =")
        sp.pprint(d)


if __name__ == "__main__":
    main()
