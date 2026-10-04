# 07 — How to prompt Claude for engineering calculations

*The setup is done. This is the skill that actually makes it useful.*

A vague question gets a vague, possibly-wrong answer. A precise question gets a
reproducible, verifiable one. Here's how engineering students should ask.

## The five things to always include

1. **All inputs, with units.** `σy = 250 MPa`, not "the yield strength."
2. **What you want computed.** "Factor of safety," "collapse load," "plastic
   strain at σ = 300 MPa."
3. **The assumptions / context.** Plane stress vs plane strain; von Mises vs
   Tresca; associated flow; small strain.
4. **The tool, if it matters.** "in MATLAB," "in Python," "symbolically."
5. **Ask to see the working and a check.** "Show each step and sanity-check the
   result."

## Templates you can copy

**Yield / safety check**
```
Stress state: σx=__, σy=__, σz=__, τxy=__, τyz=__, τzx=__ (MPa). Yield strength
σy=__ MPa. Assume plane stress / 3D [pick one]. Compute principal stresses, the
von Mises and Tresca equivalent stresses, and the factor of safety for each.
Show the working and tell me which criterion is more conservative here.
```

**Symbolic derivation**
```
Derive, symbolically, the plastic strain increment direction for a von Mises
material using the associated flow rule (dε^p = dλ ∂f/∂σ). Show ∂f/∂σ for each
stress component. Use SymPy and print the result in a readable form.
```

**Parametric plot**
```
Plot the Ramberg–Osgood stress–strain curve ε = σ/E + 0.002·(σ/σy)^n for
E=200 GPa, σy=250 MPa, n=10, for strain 0 to 0.02. Check that the plastic
strain at σ = σy is 0.002. Label axes with units and mark the yield point.
Save the figure.
```

**Check my homework** *(use only after you've solved it yourself, and only if
your course allows AI for this; see [docs/16](16-academic-integrity.md))*
```
I have already solved this myself. Here is my full hand solution [paste].
Don't rewrite it for me. Redo the calculation independently in [MATLAB/Python],
compare to my numbers step by step, and tell me where (if anywhere) we differ
and why. Where I went wrong, explain the concept so I can fix it myself. Also
run one limit-case or units check on your own answer.
```

## Good habits

- **One problem per conversation.** Use `/clear` between unrelated problems so
  Claude stays focused (and fast).
- **Ask "why," not just "what."** "Why is Tresca more conservative here?" turns a
  calculator into a tutor.
- **Verify.** Reproducible working beats a confident number. Spot-check against
  your textbook — especially for anything you'll submit or build. How:
  [docs/15 — how to check an AI calculation](15-verify-ai-results.md).
- **Stay honest.** Try it yourself first, disclose AI use, and be able to
  explain every line you hand in: [docs/16](16-academic-integrity.md).
- **Iterate.** "Now sweep n from 5 to 20 and show how the curve changes" builds
  on the previous answer instantly.

## Red flags — when to be extra careful

- The answer has **no units** or the units don't cancel → ask it to redo with units.
- A **factor of safety < 1** presented as fine, or **strain > 1**, or negative
  areas/lengths → physically suspicious, question it.
- Claude **won't run the code** and just asserts a number → tell it to execute
  and show the output.

## The one-line rule

> **Reproducible beats plausible.** If you can re-run it and get the same number,
> you can trust it. If you can't, don't.
