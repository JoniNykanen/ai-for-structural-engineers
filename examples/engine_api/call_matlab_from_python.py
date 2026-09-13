"""
Calling MATLAB from Python via the MATLAB Engine API
====================================================

Proves the Method 2 connection works: starts MATLAB, runs a few commands,
reads the results back into Python.

Requires: a MATLAB license + the matlabengine package installed in this
environment (see docs/03-connect-matlab-engine-api.md).

Run:  python call_matlab_from_python.py
"""

import sys


def main():
    try:
        import matlab.engine
    except ModuleNotFoundError:
        print("The 'matlab' module is not installed in this environment.")
        print("This example needs a MATLAB license + the Engine API.")
        print("See docs/03-connect-matlab-engine-api.md.  (No MATLAB? Use the")
        print("free Python path in docs/05-python-sympy-fallback.md instead.)")
        sys.exit(1)

    print("Starting MATLAB engine (first launch takes a few seconds)...")
    eng = matlab.engine.start_matlab()
    try:
        # 1) Call a MATLAB built-in directly.
        print("MATLAB sqrt(2.0) =", eng.sqrt(2.0))

        # 2) Run MATLAB code and read a variable out of the workspace.
        eng.eval("A = [180 40 0; 40 60 0; 0 0 0];", nargout=0)  # stress tensor
        eng.eval("p = sort(eig(A), 'descend');", nargout=0)      # principal stresses
        principal = eng.workspace["p"]
        print("Principal stresses from MATLAB (MPa):", list(principal))

        # 3) A full von Mises calc in MATLAB, result back in Python.
        eng.eval(
            "vm = sqrt(0.5*((p(1)-p(2))^2 + (p(2)-p(3))^2 + (p(3)-p(1))^2));",
            nargout=0,
        )
        print("von Mises stress from MATLAB (MPa):", eng.workspace["vm"])
    finally:
        eng.quit()
        print("MATLAB engine closed.")


if __name__ == "__main__":
    main()
