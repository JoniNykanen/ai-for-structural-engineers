"""Tests for examples/mathcad/check_mcdx.py.

No Mathcad needed: each test writes a small .mcdx (a zip with
mathcad/worksheet.xml + mathcad/result.xml) in the same XML layout Mathcad
Prime 12 saves, then checks what the reader makes of it. The sample is a
simply supported glulam beam; its expected values are worked out by hand
here, independently of the checker.

Run:  .venv\\Scripts\\python.exe -m pytest tests/test_check_mcdx.py
"""

import importlib.util
import math
import os
import zipfile

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SCRIPT = os.path.join(REPO, "examples", "mathcad", "check_mcdx.py")

_spec = importlib.util.spec_from_file_location("check_mcdx", SCRIPT)
cm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cm)


# ---------------------------------------------------------------------------
# Tiny .mcdx writer (layout as saved by Mathcad Prime 12)
# ---------------------------------------------------------------------------

SPAN = ('<Span xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" '
        'xmlns:pw="clr-namespace:Ptc.Wpf;assembly=Ptc.Core">{}<pw:Subscript>{}'
        '</pw:Subscript></Span>')


def var(name, sub=None):
    label = SPAN.format(name, sub) if sub else name
    return f'<ml:id labels="VARIABLE" xml:space="preserve">{label}</ml:id>'


def unit(u):
    return f'<ml:id labels="UNIT" xml:space="preserve">{u}</ml:id>'


def real(x):
    return f"<ml:real>{x}</ml:real>"


def ap(op, *args):
    return f"<ml:apply><ml:{op} />{''.join(args)}</ml:apply>"


def fn(name, *args):
    head = f'<ml:id labels="FUNCTION" xml:space="preserve">{name}</ml:id>'
    body = args[0] if len(args) == 1 else f"<ml:sequence>{''.join(args)}</ml:sequence>"
    return f"<ml:apply>{head}{body}</ml:apply>"


def qty(x, u):  # 2.5 kN/m² etc.
    return ap("scale", real(x), u)


def define(target, expr):
    return f"<ml:define>{target}{expr}</ml:define>"


def define_eval(target, expr, override=None):
    return f"<ml:define>{target}{evaluation(expr, override)}</ml:define>"


def evaluation(expr, override=None):
    o = override if override else "<ml:placeholder />"
    return f"<ml:eval>{expr}<ml:unitOverride>{o}</ml:unitOverride></ml:eval>"


def res_real(x):
    return f"<ml:result><ml:real>{x!r}</ml:real></ml:result>"


def res_si(x, **powers):  # res_si(4.47e-4, meter=4)
    refs = "".join(f'<u:unitReference unit="{u}" power-numerator="{p}" '
                   f'power-denominator="1" />' for u, p in powers.items())
    return (f"<ml:result><ml:unitedValue><ml:real>{x!r}</ml:real>"
            f"<u:unitMonomial>{refs}</u:unitMonomial></ml:unitedValue></ml:result>")


def res_error(msg):
    return ("<engineErrors><engineError error-id=\"0\"><errorCode>bad</errorCode>"
            f"<resource-string>{msg}</resource-string></engineError></engineErrors>")


class Sheet:
    """Collects regions top-to-bottom and writes them as a .mcdx file."""

    def __init__(self):
        self.items = []   # (math_xml, result_xml, nested_in_text)

    def add(self, math_xml, result_xml="", inline=False):
        self.items.append((math_xml, result_xml, inline))
        return self

    def write(self, path):
        regions, results = [], []
        for i, (m, r, inline) in enumerate(self.items):
            math = f'<math resultRef="{i}">{m}</math>'
            top = 40.0 * (i + 1)
            if inline:   # math written inside a text paragraph
                regions.append(f'<region region-id="{100 + i}" top="{top}" left="0">'
                               f'<text><regions><region region-id="{i}">{math}'
                               f'</region></regions></text></region>')
            else:
                regions.append(f'<region region-id="{i}" top="{top}" left="0">{math}</region>')
            results.append(f'<resultData result-id="{i}" '
                           f'calculation-status="Synchronized">{r}</resultData>')
        ws = ('<?xml version="1.0" encoding="utf-8"?>'
              '<worksheet xmlns="http://schemas.mathsoft.com/worksheet50" '
              'xmlns:ml="http://schemas.mathsoft.com/math50"><regions>'
              + "".join(regions) + "</regions></worksheet>")
        rs = ('<?xml version="1.0" encoding="utf-8"?>'
              '<resultsList xmlns="http://schemas.mathsoft.com/result10" '
              'xmlns:ml="http://schemas.mathsoft.com/math50" '
              'xmlns:u="http://schemas.mathsoft.com/units10">'
              + "".join(results) + "</resultsList>")
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("mathcad/worksheet.xml", ws)
            z.writestr("mathcad/result.xml", rs)
        return str(path)


KN_M = ap("div", unit("kN"), unit("m"))
KNM = unit("kN·m")
MPA = unit("MPa")

# Hand-worked values for the sample beam (GL30c-like, 115 × 360, L = 6 m)
Q_D, L_ = 10.0, 6.0                      # kN/m, m
B, H = 0.115, 0.360                      # m
M_HAND = Q_D * L_**2 / 8                 # 45 kN·m
W_HAND = B * H**2 / 6                    # 2.484e-3 m³
I_HAND = B * H**3 / 12                   # 4.4712e-4 m⁴
SIGMA_HAND = M_HAND * 1e3 / W_HAND / 1e6 # 18.116 MPa
E_MEAN = 13000.0                         # MPa
DEFL_HAND = 5 * Q_D * 1e3 * L_**4 / (384 * E_MEAN * 1e6 * I_HAND) * 1e3  # mm


def beam_sheet():
    """A clean worksheet: inputs, formulas, displayed results, one check."""
    return (Sheet()
            .add(define(var("q", "d"), qty(10, KN_M)))
            .add(define(var("L"), qty(6, unit("m"))))
            .add(define(var("b"), qty(115, unit("mm"))))
            .add(define(var("h"), qty(360, unit("mm"))))
            .add(define(var("E", "0.mean"), qty(13000, MPA)))
            .add(define(var("f", "m.d"), qty(19.2, MPA)))
            .add(define_eval(var("M", "d"),
                             ap("div", ap("mult", var("q", "d"), ap("pow", var("L"), real(2))), real(8)),
                             KNM), res_real(M_HAND))
            .add(define_eval(var("W", "y"),
                             ap("div", ap("mult", var("b"), ap("pow", var("h"), real(2))), real(6))),
                 res_si(W_HAND, meter=3))
            .add(define_eval(var("σ", "m.d"), ap("div", var("M", "d"), var("W", "y")), MPA),
                 res_real(SIGMA_HAND))
            .add(evaluation(ap("lessOrEqual", var("σ", "m.d"), var("f", "m.d"))), res_real(1.0))
            .add(define_eval(var("I", "y"),
                             ap("div", ap("mult", var("b"), ap("pow", var("h"), real(3))), real(12))),
                 res_si(I_HAND, meter=4))
            .add(define_eval(var("w", "inst"),
                             ap("div",
                                ap("mult", ap("mult", real(5), var("q", "d")), ap("pow", var("L"), real(4))),
                                ap("mult", ap("mult", real(384), var("E", "0.mean")), var("I", "y"))),
                             unit("mm")), res_real(DEFL_HAND)))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_hand_values_are_sane():
    # The fixture's own numbers, checked against textbook results first.
    assert M_HAND == pytest.approx(45.0)
    assert SIGMA_HAND == pytest.approx(18.116, rel=1e-4)
    assert DEFL_HAND == pytest.approx(29.03, rel=1e-3)


def test_clean_sheet_passes(tmp_path):
    path = beam_sheet().write(tmp_path / "beam.mcdx")
    rows = cm.check(cm.read_mcdx(path))
    status = {r.name: r.status for r in rows}
    assert status["q_d"] == "INPUT"
    assert status["M_d"] == "OK"
    assert status["W_y"] == "OK"        # saved with SI units (m³), no override
    assert status["σ_m.d"] == "OK"
    assert status["w_inst"] == "OK"
    assert status["σ_m.d≤f_m.d"] == "OK"
    assert cm.main(path) == 0


def test_values_are_si(tmp_path):
    v = cm.values(beam_sheet().write(tmp_path / "beam.mcdx"))
    assert v["M_d"].v == pytest.approx(45e3)              # N·m
    assert v["M_d"].dims == cm._d(1, 2, -2)                # kg·m²/s² = N·m
    assert v["w_inst"].v == pytest.approx(DEFL_HAND / 1e3)  # m
    assert v["E_0.mean"].v == pytest.approx(13e9)         # Pa


def test_stale_result_is_flagged(tmp_path):
    # Input edited after the last calculation: saved M no longer matches.
    sheet = beam_sheet()
    m, _, inline = sheet.items[6]
    sheet.items[6] = (m, res_real(40.5), inline)
    path = sheet.write(tmp_path / "stale.mcdx")
    rows = {r.name: r for r in cm.check(cm.read_mcdx(path))}
    assert rows["M_d"].status == "MISMATCH"
    assert cm.main(path) == 1


def test_mathcad_error_is_reported(tmp_path):
    path = (Sheet()
            .add(define_eval(var("x"), ap("mult", real(2), var("y"))),
                 res_error("This variable is undefined."))
            .write(tmp_path / "err.mcdx"))
    rows = cm.check(cm.read_mcdx(path))
    assert rows[0].status == "MATHCAD ERROR"
    assert "undefined" in rows[0].note
    assert cm.main(path) == 1


def test_unit_warning_when_result_is_not_the_displayed_unit(tmp_path):
    # Line load shown "in kN" — the leftover 1/m is saved with the number.
    path = (Sheet()
            .add(define(var("q"), qty(10, KN_M)))
            .add(define_eval(var("F"), var("q"), unit("kN")), res_si(10.0, meter=-1))
            .write(tmp_path / "units.mcdx"))
    rows = cm.check(cm.read_mcdx(path))
    assert rows[1].status == "UNIT WARNING"
    assert "N/m" in rows[1].note


def test_inline_math_is_read_in_place(tmp_path):
    # 'a := 3 m' is written inside a text paragraph above its use.
    path = (Sheet()
            .add(define(var("a"), qty(3, unit("m"))), inline=True)
            .add(define_eval(var("A"), ap("pow", var("a"), real(2))), res_si(9.0, meter=2))
            .write(tmp_path / "inline.mcdx"))
    rows = cm.check(cm.read_mcdx(path))
    assert [r.name for r in rows] == ["a", "A"]
    assert rows[1].status == "OK"


def test_unsupported_is_not_guessed(tmp_path):
    # A user function can't be evaluated: the call is NOT CHECKED and later
    # rows carry on with the value Mathcad saved.
    path = (Sheet()
            .add('<ml:define><ml:function>' + var("f") + '<ml:boundVars>' + var("x")
                 + '</ml:boundVars></ml:function>' + ap("mult", real(2), var("x"))
                 + '</ml:define>')
            .add(define_eval(var("y"), fn("f", real(3))), res_real(6.0))
            .add(define_eval(var("z"), ap("plus", var("y"), real(1))), res_real(7.0))
            .write(tmp_path / "func.mcdx"))
    rows = {r.name: r for r in cm.check(cm.read_mcdx(path))}
    assert rows["f"].status == "NOT CHECKED"
    assert rows["y"].status == "NOT CHECKED"
    assert "function 'f'" in rows["y"].note
    assert rows["z"].status == "OK"
    assert cm.main(path) == 0


def test_functions_roots_and_vectors(tmp_path):
    alpha = math.radians(2.86)
    k_hand = 1 / math.sqrt(1 + (19.2 / (1.5 * 2.24) * math.tan(alpha)) ** 2)
    path = (Sheet()
            .add(define(var("α"), qty(2.86, unit("°"))))
            .add(define_eval(var("k"),
                             ap("div", real(1), ap("nthRoot", "<ml:placeholder />",
                                ap("plus", real(1), ap("pow", ap("mult", ap("div", real(19.2),
                                   ap("mult", real(1.5), real(2.24))), fn("tan", var("α"))), real(2)))))),
                 res_real(k_hand))
            .add(define(var("N"), ap("scale",
                 '<ml:matrix rows="2" cols="1">' + real(278.6) + real(222.8) + "</ml:matrix>",
                 unit("kN"))))
            .add(define_eval(var("N", "max"), fn("max", var("N"), qty(100, unit("kN"))), unit("kN")),
                 res_real(278.6))
            .write(tmp_path / "fn.mcdx"))
    rows = {r.name: r for r in cm.check(cm.read_mcdx(path))}
    # By hand: 19.2/3.36 = 5.714; tan 2.86° = 0.04996; 1/√(1 + 0.2855²) = 0.9616
    assert k_hand == pytest.approx(0.9616, abs=1e-4)
    assert rows["k"].status == "OK"
    assert rows["N_max"].status == "OK"
    assert rows["N"].python.v.shape == (2, 1)                 # a column vector
    assert np.allclose(rows["N"].python.v.ravel(), [278.6e3, 222.8e3])


def test_saved_matrix_is_column_major():
    import xml.etree.ElementTree as ET
    el = ET.fromstring('<ml:matrix xmlns:ml="http://schemas.mathsoft.com/math50" '
                       'rows="2" cols="2"><ml:real>1</ml:real><ml:real>2</ml:real>'
                       '<ml:real>3</ml:real><ml:real>4</ml:real></ml:matrix>')
    q = cm._parse_number(el)
    assert q.v.tolist() == [[1.0, 3.0], [2.0, 4.0]]


def test_unit_mismatch_in_formula(tmp_path):
    path = (Sheet()
            .add(define(var("a"), qty(1, unit("m"))))
            .add(define_eval(var("bad"), ap("plus", var("a"), qty(1, unit("kN")))), res_real(2.0))
            .write(tmp_path / "bad.mcdx"))
    rows = {r.name: r for r in cm.check(cm.read_mcdx(path))}
    assert rows["bad"].status == "MISMATCH"
    assert "units differ" in rows["bad"].note
