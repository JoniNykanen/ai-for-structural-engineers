"""
Mathcad worksheet (.mcdx) → independent Python re-check
=======================================================

Reads a PTC Mathcad Prime worksheet straight from the file — no Mathcad, no
licence, works with the free Mathcad Express — and:
  1. lists every definition (name, formula, value, unit) in worksheet order,
  2. re-evaluates each formula in Python with its own unit handling,
  3. compares the Python value with the result Mathcad saved in the file,
  4. reports Mathcad's own errors (e.g. "This variable is undefined").

A .mcdx file is a zip. `mathcad/worksheet.xml` holds the math regions as an
expression tree; `mathcad/result.xml` holds the results of the last
calculation, linked by `resultRef`. A result is a bare number in the region's
display unit when the region has a unit override (e.g. `= 6.2 kN/m`), otherwise
a value with SI base units (meter, newton, …).

Limits — reported as NOT CHECKED, never guessed:
  * user-defined functions f(x) := …, programs, if/for, integrals, sums,
    solve blocks and any operator not listed in `OPS` / `FUNCS`,
  * vector × vector (Mathcad means a dot product there).
When a formula can't be evaluated, later formulas keep going with the value
Mathcad saved, and the row says so.

Run:  python check_mcdx.py worksheet.mcdx [--all]
      (default prints only rows that need attention; --all prints every row)

Exit codes: 0 = every re-checked result matches and Mathcad reports no errors,
            1 = at least one MISMATCH or MATHCAD ERROR.
"""

# ---------------------------------------------------------------------------
# How to verify the AI's answer
# ---------------------------------------------------------------------------
# This IS the verification step for a Mathcad worksheet: an independent
# second evaluation of every formula. A row is OK only when the Python value
# and Mathcad's saved value agree to REL_TOL and have the same dimensions.
# It does not prove the formulas are the right ones for the design code —
# that is still the engineer's job — but it catches stale results, unit slips,
# undefined variables and results that changed after an input was edited.
# ---------------------------------------------------------------------------

import math
import sys
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from fractions import Fraction

import numpy as np

for _stream in (sys.stdout, sys.stderr):  # Unicode names print on Windows
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

REL_TOL = 1e-6   # Mathcad saves full doubles, so agreement should be near-exact

NS_WS = "{http://schemas.mathsoft.com/worksheet50}"
NS_ML = "{http://schemas.mathsoft.com/math50}"
NS_RES = "{http://schemas.mathsoft.com/result10}"
NS_U = "{http://schemas.mathsoft.com/units10}"


# ---------------------------------------------------------------------------
# Units: value in SI + dimension exponents (mass, length, time)
# ---------------------------------------------------------------------------

class Unsupported(Exception):
    """The formula uses something this checker does not evaluate."""


class UnitError(Exception):
    """Inconsistent units, e.g. adding metres to newtons."""


DIMLESS = (Fraction(0), Fraction(0), Fraction(0))


def _d(m, l, t):
    return (Fraction(m), Fraction(l), Fraction(t))


@dataclass
class Q:
    """A quantity: SI value (float or numpy array) and (M, L, T) exponents."""
    v: object
    dims: tuple = DIMLESS

    def __add__(self, o):
        _same(self, o, "+")
        return Q(self.v + o.v, self.dims)

    def __sub__(self, o):
        _same(self, o, "−")
        return Q(self.v - o.v, self.dims)

    def __mul__(self, o):
        if _is_vec(self.v) and _is_vec(o.v):
            raise Unsupported("vector × vector (Mathcad dot product)")
        return Q(self.v * o.v, tuple(a + b for a, b in zip(self.dims, o.dims)))

    def __truediv__(self, o):
        if _is_vec(o.v):
            raise Unsupported("division by a vector")
        return Q(self.v / o.v, tuple(a - b for a, b in zip(self.dims, o.dims)))

    def __neg__(self):
        return Q(-self.v, self.dims)

    def pow(self, o):
        if o.dims != DIMLESS or _is_vec(o.v):
            raise UnitError("exponent must be a dimensionless scalar")
        p = Fraction(float(o.v)).limit_denominator(12)
        return Q(np.power(self.v, float(o.v)), tuple(a * p for a in self.dims))


def _is_vec(v):
    return isinstance(v, np.ndarray) and v.size > 1


def _same(a, b, op):
    if a.dims != b.dims:
        raise UnitError(f"units differ across '{op}': "
                        f"{unit_label(a.dims)} vs {unit_label(b.dims)}")


N_ = _d(1, 1, -2)
PA = _d(1, -1, -2)
UNITS = {   # Mathcad unit label → (SI factor, dims)
    "m": (1.0, _d(0, 1, 0)), "mm": (1e-3, _d(0, 1, 0)), "cm": (1e-2, _d(0, 1, 0)),
    "km": (1e3, _d(0, 1, 0)),
    "kg": (1.0, _d(1, 0, 0)), "g": (1e-3, _d(1, 0, 0)), "tonne": (1e3, _d(1, 0, 0)),
    "s": (1.0, _d(0, 0, 1)), "min": (60.0, _d(0, 0, 1)), "hr": (3600.0, _d(0, 0, 1)),
    "N": (1.0, N_), "kN": (1e3, N_), "MN": (1e6, N_),
    "Pa": (1.0, PA), "kPa": (1e3, PA), "MPa": (1e6, PA), "GPa": (1e9, PA),
    "°": (math.pi / 180, DIMLESS), "deg": (math.pi / 180, DIMLESS),
    "rad": (1.0, DIMLESS), "%": (0.01, DIMLESS),
}
SI_BASE = {  # unit names used in result.xml (SI base / derived)
    "meter": _d(0, 1, 0), "kilogram": _d(1, 0, 0), "second": _d(0, 0, 1),
    "newton": N_, "pascal": PA, "joule": _d(1, 2, -2), "radian": DIMLESS,
}
CONSTANTS = {"π": math.pi, "e": math.e}

_NAMED = {N_: "N", PA: "Pa", _d(1, 2, -2): "N·m", _d(1, 0, -2): "N/m"}


def unit_lookup(label):
    """'kN', 'N·m', … → Q with the unit's SI factor."""
    q = Q(1.0)
    for part in label.split("·"):
        if part not in UNITS:
            raise Unsupported(f"unit '{part}'")
        f, dims = UNITS[part]
        q = q * Q(f, dims)
    return q


def unit_label(dims):
    """Readable SI label for a dimension tuple, e.g. N, Pa, m^2, kg·m/s^2."""
    if dims == DIMLESS:
        return ""
    if dims in _NAMED:
        return _NAMED[dims]
    num, den = [], []
    for sym, p in zip(("kg", "m", "s"), dims):
        if p == 0:
            continue
        s = sym if abs(p) == 1 else f"{sym}^{abs(p)}"
        (num if p > 0 else den).append(s)
    out = "·".join(num) or "1"
    return out + ("/" + "·".join(den) if den else "")


# ---------------------------------------------------------------------------
# Reading the file
# ---------------------------------------------------------------------------

def name_of(id_el):
    """Mathcad label → text: g<Subscript>k.katto</Subscript> → 'g_k.katto'."""
    span = next(iter(id_el), None)
    if span is None:
        return (id_el.text or "").strip()
    out = span.text or ""
    for child in span:
        if child.tag.endswith("Subscript"):
            out += "_" + (child.text or "")
        else:
            out += child.text or ""
        out += child.tail or ""
    return out.strip()


@dataclass
class Region:
    order: int
    kind: str                  # 'define' | 'eval' | 'function'
    name: str                  # variable name, or the expression text for 'eval'
    expr: object               # ml element to evaluate (None for 'function')
    override: object = None    # ml unit expression from unitOverride, or None
    result: object = None      # resultData element, or None
    errors: list = field(default_factory=list)
    warnings: int = 0
    shows_result: bool = False  # region ends in '= …' (only then is a result displayed)


def read_mcdx(path):
    """Parse a .mcdx file into Regions, in Mathcad's calculation order."""
    with zipfile.ZipFile(path) as z:
        ws = ET.fromstring(z.read("mathcad/worksheet.xml"))
        rs = ET.fromstring(z.read("mathcad/result.xml"))
    results = {rd.get("result-id"): rd for rd in rs}

    # Math can sit inline inside a text region; such nested regions have no
    # top/left of their own and take the position of the region holding them.
    parent = {c: p for p in ws.iter() for c in p}

    def position(region):
        r = region
        while r is not None and r.get("top") is None:
            r = parent.get(r)
            while r is not None and r.tag != NS_WS + "region":
                r = parent.get(r)
        if r is None:
            return (0.0, 0.0)
        return (float(r.get("top")), float(r.get("left", 0)))

    placed = []
    for seq, region in enumerate(ws.iter(NS_WS + "region")):
        math_el = region.find(NS_WS + "math")
        if math_el is None:
            continue
        placed.append((position(region) + (seq,), math_el))
    placed.sort(key=lambda p: p[0])   # Mathcad: top-to-bottom, then left-to-right

    regions = []
    for i, (_, m) in enumerate(placed):
        top = next((c for c in m if c.tag.startswith(NS_ML)), None)
        if top is None:
            continue
        rd = results.get(m.get("resultRef"))
        tag = top.tag[len(NS_ML):]
        if tag == "define":
            target, body = top[0], top[1]
            if target.tag == NS_ML + "function":
                r = Region(i, "function", name_of(target[0]), None)
            else:
                r = Region(i, "define", name_of(target), body)
        elif tag == "eval":
            r = Region(i, "eval", "", top)
            r.name = render(top[0])
        else:
            continue   # text-like math: labels, bare comparisons, 'ok' …
        r.shows_result = r.expr is not None and r.expr.tag == NS_ML + "eval"
        if r.shows_result:
            uo = r.expr.find(NS_ML + "unitOverride")
            if uo is not None and len(uo) and uo[0].tag != NS_ML + "placeholder":
                r.override = uo[0]
            r.expr = r.expr[0]
        if rd is not None:
            r.result = rd.find(NS_ML + "result")
            r.errors = [e.findtext(NS_RES + "resource-string", "").strip()
                        for e in rd.iter(NS_RES + "engineError")]
            r.warnings = len(list(rd.iter(NS_RES + "Warning")))
        regions.append(r)
    return regions


def saved_value(region):
    """Mathcad's saved result as Q (SI), or None if the region shows none."""
    res = region.result
    if not region.shows_result or res is None or len(res) == 0:
        return None
    saved = _parse_number(res[0])
    if region.override is not None:
        # Number is in the override unit; any SI units left over (when the
        # override doesn't cover all dimensions) are attached to it.
        unit = evaluate(region.override, {})
        return Q(saved.v * unit.v,
                 tuple(a + b for a, b in zip(unit.dims, saved.dims)))
    return saved


def _parse_number(el):
    tag = el.tag[len(NS_ML):]
    if tag == "real":
        return Q(float(el.text))
    if tag == "unitedValue":
        q = _parse_number(el[0])
        dims = DIMLESS
        for ref in el.iter(NS_U + "unitReference"):
            unit = ref.get("unit")
            if unit not in SI_BASE:
                raise Unsupported(f"result unit '{unit}'")
            p = Fraction(int(ref.get("power-numerator", 1)),
                         int(ref.get("power-denominator", 1)))
            dims = tuple(a + b * p for a, b in zip(dims, SI_BASE[unit]))
        return Q(q.v, dims)
    if tag == "matrix":
        rows, cols = int(el.get("rows")), int(el.get("cols"))
        items = [_parse_number(c) for c in el]
        if len({q.dims for q in items}) > 1:
            raise Unsupported("matrix with mixed units")
        # Mathcad stores matrices column by column
        arr = np.array([q.v for q in items], dtype=float).reshape(cols, rows).T
        return Q(arr, items[0].dims)
    raise Unsupported(f"saved result type '{tag}'")


# ---------------------------------------------------------------------------
# Evaluating the expression tree
# ---------------------------------------------------------------------------

def _cmp(fn):
    def op(a, b):
        _same(a, b, "comparison")
        return Q(np.where(fn(a.v, b.v), 1.0, 0.0) if _is_vec(a.v) or _is_vec(b.v)
                 else float(fn(a.v, b.v)))
    return op


OPS = {
    "plus": lambda a, b: a + b,
    "minus": lambda a, b: a - b,
    "mult": lambda a, b: a * b,
    "scale": lambda a, b: a * b,     # number × unit, e.g. 2.5 kN/m²
    "div": lambda a, b: a / b,
    "pow": lambda a, b: a.pow(b),
    "lessOrEqual": _cmp(lambda x, y: x <= y),
    "lessThan": _cmp(lambda x, y: x < y),
    "greaterOrEqual": _cmp(lambda x, y: x >= y),
    "greaterThan": _cmp(lambda x, y: x > y),
}


def _dimless(fn, name):
    def f(*args):
        if len(args) != 1 or args[0].dims != DIMLESS:
            raise UnitError(f"{name}() needs one dimensionless argument")
        return Q(fn(args[0].v))
    return f


def _extreme(fn):
    def f(*args):
        for a in args[1:]:
            _same(args[0], a, "max/min")
        vals = np.concatenate([np.ravel(a.v) for a in args])
        return Q(float(fn(vals)), args[0].dims)
    return f


FUNCS = {
    "sin": _dimless(np.sin, "sin"), "cos": _dimless(np.cos, "cos"),
    "tan": _dimless(np.tan, "tan"), "asin": _dimless(np.arcsin, "asin"),
    "acos": _dimless(np.arccos, "acos"), "atan": _dimless(np.arctan, "atan"),
    "ln": _dimless(np.log, "ln"), "log": _dimless(np.log10, "log"),
    "exp": _dimless(np.exp, "exp"),
    "sqrt": lambda a: a.pow(Q(0.5)),
    "abs": lambda a: Q(np.abs(a.v), a.dims),
    "max": _extreme(np.max), "min": _extreme(np.min),
}


def evaluate(el, env):
    """Evaluate a Mathcad ml expression element to Q. `env`: name → Q."""
    tag = el.tag[len(NS_ML):]
    if tag == "real":
        return Q(float(el.text))
    if tag == "parens":
        return evaluate(el[0], env)
    if tag == "id":
        name, label = name_of(el), el.get("labels")
        if label == "UNIT":
            return unit_lookup(name)
        if label == "CONSTANT" and name in CONSTANTS:
            return Q(CONSTANTS[name])
        if name in env:
            if env[name] is None:
                raise Unsupported(f"depends on '{name}', which was not checked")
            return env[name]
        if label is None and name in UNITS:
            return unit_lookup(name)
        raise Unsupported(f"'{name}' is not defined above this point")
    if tag == "matrix":
        rows, cols = int(el.get("rows")), int(el.get("cols"))
        items = [evaluate(c, env) for c in el]
        if len({q.dims for q in items}) > 1:
            raise Unsupported("matrix with mixed units")
        arr = np.array([float(q.v) for q in items]).reshape(cols, rows).T
        return Q(arr, items[0].dims)
    if tag == "apply":
        head, args = el[0], list(el)[1:]
        h = head.tag[len(NS_ML):]
        if h == "id":                                    # function call
            fname = name_of(head)
            if fname not in FUNCS:
                raise Unsupported(f"function '{fname}'")
            if args and args[0].tag == NS_ML + "sequence":
                args = list(args[0])
            return FUNCS[fname](*[evaluate(a, env) for a in args])
        if h == "neg":
            return -evaluate(args[0], env)
        if h == "nthRoot":
            index, radicand = args
            n = 2.0 if index.tag == NS_ML + "placeholder" else float(evaluate(index, env).v)
            return evaluate(radicand, env).pow(Q(1.0 / n))
        if h in OPS:
            a, b = (evaluate(x, env) for x in args)
            return OPS[h](a, b)
        raise Unsupported(f"operator '{h}'")
    raise Unsupported(f"'{tag}'")


_SYM = {"plus": "+", "minus": "−", "mult": "·", "scale": " ", "div": "/",
        "pow": "^", "lessOrEqual": "≤", "lessThan": "<", "greaterOrEqual": "≥",
        "greaterThan": ">"}


def render(el):
    """Short text form of an expression, for eval-only rows and messages."""
    tag = el.tag[len(NS_ML):]
    if tag == "real":
        return el.text
    if tag == "id":
        return name_of(el)
    if tag == "parens":
        return "(" + render(el[0]) + ")"
    if tag == "apply":
        head, args = el[0], list(el)[1:]
        h = head.tag[len(NS_ML):]
        if h == "id":
            if args and args[0].tag == NS_ML + "sequence":
                args = list(args[0])
            return name_of(head) + "(" + ", ".join(render(a) for a in args) + ")"
        if h == "neg":
            return "−" + render(args[0])
        if h == "nthRoot":
            return "√(" + render(args[1]) + ")"
        if h in _SYM and len(args) == 2:
            return render(args[0]) + _SYM[h] + render(args[1])
    return "…"


# ---------------------------------------------------------------------------
# The check
# ---------------------------------------------------------------------------

@dataclass
class Row:
    name: str
    kind: str
    status: str     # OK | MISMATCH | MATHCAD ERROR | UNIT WARNING | INPUT | DEFINED | NOT CHECKED
    mathcad: object = None   # Q or None
    python: object = None    # Q or None
    unit: str = ""           # display unit label used for printing
    note: str = ""


def _close(a, b):
    if a.dims != b.dims:
        return False
    va, vb = np.asarray(a.v, dtype=float), np.asarray(b.v, dtype=float)
    if va.shape != vb.shape and va.size != vb.size:
        return False
    return bool(np.allclose(va.ravel(), vb.ravel(), rtol=REL_TOL, atol=1e-12))


def check(regions):
    """Re-evaluate every region in order; return one Row per region."""
    env, rows = {}, []
    for r in regions:
        if r.kind == "function":
            env[r.name] = None
            rows.append(Row(r.name, r.kind, "MATHCAD ERROR", note="; ".join(r.errors))
                        if r.errors else
                        Row(r.name, r.kind, "NOT CHECKED",
                            note="user-defined function — not evaluated"))
            continue

        unit = render(r.override) if r.override is not None else ""
        row = Row(r.name, r.kind, "", unit=unit)
        try:
            row.mathcad = saved_value(r)
        except Unsupported as e:
            row.note = f"saved result not read: {e}"
        try:
            row.python = evaluate(r.expr, env)
        except (Unsupported, UnitError) as e:
            row.note = (row.note + "; " if row.note else "") + str(e)
            if isinstance(e, UnitError):
                row.status = "MISMATCH"

        if r.errors:
            row.status = "MATHCAD ERROR"
            row.note = "; ".join(r.errors)
        elif row.status:
            pass
        elif row.python is not None and row.mathcad is not None:
            row.status = "OK" if _close(row.python, row.mathcad) else "MISMATCH"
        elif row.python is not None:
            literal = r.expr.tag == NS_ML + "real" or (
                r.expr.tag == NS_ML + "apply" and r.expr[0].tag == NS_ML + "scale")
            row.status = "INPUT" if literal else "DEFINED"
        else:
            row.status = "NOT CHECKED"
            if row.mathcad is not None:
                row.note += " — later rows use Mathcad's saved value"
        if row.status == "OK" and r.override is not None:
            shown = evaluate(r.override, {}).dims
            if shown != row.mathcad.dims:
                row.status = "UNIT WARNING"
                row.note = (f"result is {unit_label(row.mathcad.dims)}, not "
                            f"{unit_label(shown)} — check the formula's units")
        if r.warnings and row.status in ("OK", "INPUT", "DEFINED"):
            row.note = "Mathcad warning: a name used here is redefined in the sheet"

        if r.kind == "define":
            env[r.name] = row.python if row.python is not None else row.mathcad
        rows.append(row)
    return rows


def values(path):
    """name → Q (SI) for every variable defined in the worksheet.

    Handy for handing Mathcad inputs/results to other Python code, e.g. a
    eurocode-fi check. Later definitions of the same name win, as in Mathcad.
    """
    out = {}
    for row in check(read_mcdx(path)):
        if row.kind == "define":
            q = row.python if row.python is not None else row.mathcad
            if q is not None:
                out[row.name] = q
    return out


def fmt(q, unit_el_label=""):
    """Value in the row's display unit if it has one, else SI."""
    if q is None:
        return "—"
    v, label = q.v, unit_label(q.dims)
    if unit_el_label:
        try:
            u = unit_lookup_expr(unit_el_label)
            if u.dims == q.dims:
                v, label = np.asarray(q.v) / u.v, unit_el_label
        except Unsupported:
            pass
    if isinstance(v, np.ndarray) and v.size > 1:
        s = "[" + ", ".join(f"{x:.6g}" for x in np.ravel(v)) + "]"
    else:
        s = f"{float(np.ravel(v)[0]) if isinstance(v, np.ndarray) else float(v):.6g}"
    return f"{s} {label}".strip()


def unit_lookup_expr(text):
    """Evaluate a rendered unit label such as 'kN/m' or 'N/mm^2'."""
    num, _, den = text.partition("/")
    q = Q(1.0)
    for part, sign in ((num, 1), (den, -1)):
        if not part:
            continue
        base, _, p = part.partition("^")
        u = unit_lookup(base)
        if p:
            u = u.pow(Q(float(p)))
        q = q * u if sign > 0 else q / u
    return q


def main(path, show_all=False):
    rows = check(read_mcdx(path))
    counts = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1

    print(f"Mathcad worksheet: {path}")
    print(f"{len(rows)} math regions — " +
          ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())))
    print()
    attention = ("MISMATCH", "MATHCAD ERROR", "UNIT WARNING", "NOT CHECKED")
    shown = [r for r in rows if show_all or r.status in attention]
    if shown:
        print(f"{'status':<14} {'name':<26} {'Mathcad':>22} {'Python':>22}  note")
        for r in shown:
            name = ("= " + r.name if r.kind == "eval" else r.name)[:26]
            print(f"{r.status:<14} {name:<26} {fmt(r.mathcad, r.unit):>22} "
                  f"{fmt(r.python, r.unit):>22}  {r.note}")
    bad = counts.get("MISMATCH", 0) + counts.get("MATHCAD ERROR", 0)
    print()
    print("CHECK PASSED — every re-checked value matches Mathcad."
          if not bad else f"CHECK FAILED — {bad} row(s) need attention.")
    return 1 if bad else 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(args[0], show_all="--all" in sys.argv))
