# 15 — How to check an AI calculation

*Claude runs real code, but the code can still be wrong. Here are six quick
checks that catch most mistakes, plus a real bug from this repo that a
one-line check caught.*

## The six checks

1. **Predict first.** Before you ask, write down a rough guess: the sign, the
   order of magnitude, and roughly where it should land. If you expect "about
   200 MPa" and get 2 MPa or 20 000 MPa, something is wrong. That could be your
   guess or the answer. Either way you've learned something.
2. **Try a limit case.** Put in a special case where you already know the
   answer. Example: von Mises in **pure shear** (σx = σy = 0, τxy = τ) must give
   **σ_vm = √3·τ**, so τ = 100 MPa → 173.2 MPa. Other good ones are zero load
   giving zero stress, a symmetric case giving symmetric results, and one
   parameter going to 0 or ∞.
3. **Check units and dimensions.** Every term in a sum must have the same units.
   The result must have the units you asked for. Watch for kN vs N and MPa vs
   Pa: a silent ×1000 is the most common error (see the warning in
   [docs/14](14-robot-mcp.md)).
4. **Use a second, independent method.** Get the same number a different way,
   for example principal stresses vs the component formula, SymPy (symbolic)
   vs NumPy (numeric), or a hand calc such as `M_max = wL²/8` vs software. Two
   routes that agree are much stronger evidence than one route twice.
5. **Compare with a textbook or reference tool.** Use a solved textbook example
   with the same inputs. For Finnish timber design, the free **Puuinfo** Excel
   tools are good references (e.g. the straight glulam beam tool vs
   `glulam_beam_ec5.py`), see [docs/12](12-suomalaiset-referenssityokalut.md).
6. **Check sanity ranges.** Does it look like the real world? Structural steel
   has E ≈ 200–210 GPa and a yield strength of a few hundred MPa. Elastic
   strains are around 0.001. A factor of safety below 1 means failure, and a
   strain above 1 is almost never right in this kind of work.

You don't need all six every time. **One limit case plus a units check** takes
a minute and catches a lot. The kit's `CLAUDE.md` tells Claude to include at
least one check in every calculation answer. Read it, and run your own too.

## Real example: the Ramberg–Osgood bug

An AI-written example in this repo
([`stress_strain_ramberg_osgood.py`](../examples/plasticity/stress_strain_ramberg_osgood.py))
used this form of the Ramberg–Osgood curve:

```
ε = σ/E + α · (σ/σy)^n · (σy/E)        with α = 0.002
```

The code ran without errors and produced a nice smooth plot. It was still
wrong.

**The limit check.** In this model, σy is the 0.2 % proof stress. So at
σ = σy the *plastic* strain must be **0.002**, by definition. Put σ = σy in the
plastic term:

```
α · (σy/σy)^n · (σy/E) = α · σy/E = 0.002 × 250 / 200 000 = 2.5e-6
```

That is 2.5 × 10⁻⁶ instead of 2 × 10⁻³, about **800 times too small**. The
curve was practically linear-elastic all the way past yield. The `α = 0.002`
belongs to the form `ε = σ/E + 0.002·(σ/σy)^n`. In the `σy/E` form, the
matching value is α = 0.002·E/σy = 1.6. The value was copied from one form into
the other.

**What this teaches:**
- **A units check would *not* have caught it.** Both forms are
  dimensionless, so the units were fine. Only the limit case exposed it.
- **A good-looking plot proves nothing.** It just showed the wrong curve
  neatly.
- **Know what each parameter means physically.** "At σ = σy the plastic strain
  is 0.2 %" is a one-line test that anyone can run.

The example has since been fixed and now checks itself.

## Ask Claude to help you check

```
Before you give the final answer: test it with a limit case where the answer is
known, check the units of every term, and recompute it by a second independent
method. Tell me which checks passed.
```

Related: [docs/07 — how to prompt](07-how-to-prompt-claude.md) ·
[docs/16 — using AI honestly in coursework](16-academic-integrity.md)
