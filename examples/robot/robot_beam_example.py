"""
Autodesk Robot Structural Analysis — Python/COM starter
========================================================

Proves the connection to Robot Structural Analysis Professional via its COM API
and builds a minimal simply-supported beam (2 nodes + 1 bar). This is the
Robot equivalent of the MATLAB Engine API demo.

Requires (Windows only):
  - Autodesk Robot Structural Analysis Professional installed + licensed
  - pywin32:  pip install pywin32

Run:  python robot_beam_example.py

IMPORTANT — this is a *template to verify*, not a tested-here script. Robot's
COM API is intricate and version-sensitive. Confirm object/enum names against
the Robot SDK (installed with Robot: "Install Tools & utilities" -> SDK) or via
the `autodesk-product-help` MCP server and the `robot-structural` skill in this
repo. See docs/10.
"""

import sys


def main():
    if sys.platform != "win32":
        print("Robot Structural Analysis + its COM API are Windows-only.")
        return 1
    try:
        import win32com.client as win32
    except ModuleNotFoundError:
        print("pywin32 is not installed. Run:  pip install pywin32")
        print("(No Robot? Use the free Python/SymPy path - docs/05.)")
        return 1

    try:
        # EnsureDispatch generates Python wrappers from the RobotOM type library,
        # which also exposes named enums via win32com.client.constants — so we
        # never hard-code integer enum values.
        robot = win32.gencache.EnsureDispatch("Robot.Application")
        from win32com.client import constants as c
    except Exception as e:
        print(f"Could not start Robot via COM: {e}")
        print("Is Robot Structural Analysis installed and licensed? See docs/10.")
        return 1

    try:
        robot.Visible = 1
        robot.Interactive = 1
        print("Connected to Robot. Version:", robot.Version)

        # New 2D frame project.
        proj = robot.Project
        proj.New(c.I_PT_FRAME_2D)
        structure = proj.Structure

        # Geometry: a 6 m simply-supported beam (nodes 1-2, bar 1).
        nodes = structure.Nodes
        nodes.Create(1, 0.0, 0.0, 0.0)
        nodes.Create(2, 6.0, 0.0, 0.0)
        bars = structure.Bars
        bars.Create(1, 1, 2)

        print(f"Created {nodes.Count} nodes and {bars.Count} bar(s).")
        print("Next (see the robot-structural skill / SDK): assign a section &"
              " material label, add supports + a load case, run"
              " proj.CalcEngine.Calculate(), then read Results.")
    except Exception as e:
        print(f"Robot API call failed: {e}")
        print("Verify object/enum names against the SDK or the autodesk-product-help MCP.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
