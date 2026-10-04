"""
Symbolic derivation of the von Mises yield function  (SymPy)
============================================================

Shows the *algebra*, done exactly (no rounding):
  1. split the stress tensor into hydrostatic + deviatoric parts,
  2. form the second deviatoric invariant J2,
  3. write the von Mises equivalent stress sigma_vm = sqrt(3*J2),
  4. differentiate the yield function f = sigma_vm - sigma_Y to get the
     associated-flow direction dEps^p ~ df/dsigma.

Notation: sigma_y here is the normal stress in the y direction; the yield
strength is the symbol sigma_Y (capital Y).

Note on shear terms: df/dtau_xy = 3*tau_xy/sigma_vm. Because tau_xy appears
twice in the symmetric tensor (xy and yx), this derivative gives the
ENGINEERING plastic shear strain increment dgamma^p_xy = 2*dEps^p_xy.

Run:  python symbolic_yield_derivation.py
No MATLAB license required.
"""

# ---------------------------------------------------------------------------
# How to verify the AI's answer
# ---------------------------------------------------------------------------
# A symbolic result can look impressive and still be wrong. Test it by
# substituting cases whose answer you know. self_check() below checks:
#   * uniaxial stress sigma  -> sigma_vm = sigma
#   * pure shear tau         -> sigma_vm = sqrt(3)*tau
#   * hydrostatic pressure   -> sigma_vm = 0 (pressure does not cause yielding)
#   * units: doubling every stress doubles sigma_vm (it is a stress, too)
#   * plastic flow keeps volume constant: df/dsx + df/dsy + df/dsz = 0
#   * uniaxial flow ratio dEps_y/dEps_x = -1/2 (plastic "Poisson ratio" 0.5)
# ---------------------------------------------------------------------------

import sympy as sp

# Symbolic stress components.
sx, sy, sz, txy, tyz, tzx, sig_Y = sp.symbols(
    "sigma_x sigma_y sigma_z tau_xy tau_yz tau_zx sigma_Y", real=True)
COMPONENTS = [("sigma_x", sx), ("sigma_y", sy), ("sigma_z", sz),
              ("tau_xy", txy), ("tau_yz", tyz), ("tau_zx", tzx)]


def derive():
    """Return (deviatoric tensor s, J2, sigma_vm, {name: df/dvar})."""
    sigma = sp.Matrix([[sx,  txy, tzx],
                       [txy, sy,  tyz],
                       [tzx, tyz, sz]])

    # Hydrostatic (mean) stress and deviatoric stress tensor.
    p = sigma.trace() / 3
    s = sigma - p * sp.eye(3)

    # Second deviatoric invariant J2 = 1/2 s:s (sums all 9 terms, so each
    # shear term is counted twice, as it should be).
    J2 = sp.Rational(1, 2) * sum((s[i, j])**2 for i in range(3) for j in range(3))
    J2 = sp.simplify(J2)

    # von Mises equivalent stress.
    sigma_vm = sp.sqrt(3 * J2)

    # Associated flow rule: dEps^p is proportional to df/dsigma, f = sigma_vm - sigma_Y.
    f = sigma_vm - sig_Y
    flow = {name: sp.simplify(sp.diff(f, var)) for name, var in COMPONENTS}
    return s, J2, sigma_vm, flow


def _at(expr, **values):
    """Substitute stress values; components not given are set to zero."""
    subs = {var: values.get(name, 0) for name, var in COMPONENTS}
    return sp.simplify(expr.subs(subs))


def self_check():
    """Physics checks on the symbolic result. Raises AssertionError on failure."""
    s, J2, sigma_vm, flow = derive()
    S, tau, p, k = sp.symbols("S tau p k", positive=True)

    # 1) Uniaxial stress: sigma_vm = sigma.
    assert sp.simplify(_at(sigma_vm, sigma_x=S) - S) == 0, "uniaxial: sigma_vm should equal sigma"

    # 2) Pure shear: sigma_vm = sqrt(3)*tau.
    assert sp.simplify(_at(sigma_vm, tau_xy=tau) - sp.sqrt(3) * tau) == 0, (
        "pure shear: sigma_vm should equal sqrt(3)*tau")

    # 3) Hydrostatic pressure: no deviatoric stress, so sigma_vm = 0.
    assert _at(sigma_vm, sigma_x=-p, sigma_y=-p, sigma_z=-p) == 0, (
        "hydrostatic stress must give sigma_vm = 0")
    assert sp.simplify(s.trace()) == 0, "deviatoric tensor must have zero trace"

    # 4) J2 matches the textbook principal-stress form when there is no shear.
    J2_textbook = sp.Rational(1, 6) * ((sx - sy)**2 + (sy - sz)**2 + (sz - sx)**2)
    assert sp.simplify(_at(J2, sigma_x=sx, sigma_y=sy, sigma_z=sz) - J2_textbook) == 0, (
        "J2 should equal 1/6[(s1-s2)^2 + (s2-s3)^2 + (s3-s1)^2]")

    # 5) Units / dimensions: sigma_vm is a stress, so scaling all stresses by k scales it by k.
    scaled = sigma_vm.subs({var: k * var for _, var in COMPONENTS}, simultaneous=True)
    assert sp.simplify(scaled - k * sigma_vm) == 0, "sigma_vm must scale linearly with stress"

    # 6) Plastic incompressibility: the normal flow components sum to zero.
    vol = flow["sigma_x"] + flow["sigma_y"] + flow["sigma_z"]
    assert sp.simplify(vol) == 0, "plastic flow must be volume-preserving (trace of df/dsigma = 0)"

    # 7) Uniaxial flow: dEps_x : dEps_y : dEps_z = 1 : -1/2 : -1/2.
    fx = _at(flow["sigma_x"], sigma_x=S)
    fy = _at(flow["sigma_y"], sigma_x=S)
    assert fx == 1 and fy == sp.Rational(-1, 2), (
        f"uniaxial flow direction should be (1, -1/2, -1/2), got ({fx}, {fy}, ...)")


def main():
    self_check()

    s, J2, sigma_vm, flow = derive()
    print("Deviatoric stress tensor s =")
    sp.pprint(s)
    print("\nJ2 (second deviatoric invariant) =")
    sp.pprint(sp.expand(J2))
    print("\nvon Mises equivalent stress sigma_vm = sqrt(3*J2) =")
    sp.pprint(sp.simplify(sigma_vm))

    print("\nAssociated flow directions df/dsigma_ij (plastic strain increment ~ these;")
    print(" shear entries give engineering shear strain increments dgamma^p):")
    for name, d in flow.items():
        print(f"  df/d{name} =")
        sp.pprint(d)


if __name__ == "__main__":
    main()
