# 00 — What is this? (read me first)

*Written for someone who has never used an AI coding tool. 5-minute read.*

## The problem

Engineering courses are full of calculations that are conceptually simple but
tedious and error-prone: tensor stress transforms, yield checks, solving
nonlinear equations, integrating a stress–strain law, sweeping a parameter to
make a plot. Doing them by hand is slow and easy to get wrong. Doing them in
MATLAB works, but only if you already know the syntax.

## The idea

**Claude Code** is an AI assistant that lives in your terminal (the black
text window on your computer). Unlike a chatbot in a browser, Claude Code can:

- read and write files on your computer,
- **run code** (Python or MATLAB) and read back the real results,
- draw plots and save them.

So instead of *"how do I write the MATLAB for a von Mises check?"* you just say
*"is this stress state yielding?"* and it writes the code, runs it, and explains
the answer.

## The three pieces

```
   You  ──(plain English)──►  Claude Code  ──(writes + runs code)──►  MATLAB or Python
                                    │
                                    └──(shows working + result + plot)──►  You
```

1. **Claude Code** — the assistant. You install it once. ([docs/01](01-install-claude-code.md))
2. **A calculation engine** — either **Python** (free, no license, works
   instantly — [docs/02](02-python-setup.md)) or **MATLAB** (if your university
   gives you a license — [docs/03](03-connect-matlab-engine-api.md)).
3. **This repo** — the guides + example problems that tie it together.

## Do I need MATLAB?

**No, not to start.** Python with the SymPy and NumPy libraries can do
essentially all the undergraduate-level symbolic and numeric work — for free.
Use MATLAB when your course *requires* MATLAB output, or when you're checking
homework that must be done in MATLAB. This repo teaches both, plus a way to have
Claude drive MATLAB for you.

## What this is NOT

- It is **not** a way to avoid learning. It's a way to check your work, see
  worked steps, and iterate faster. You still need to understand the physics.
- It is **not** always right. AI can be confidently wrong. That's exactly why
  this repo insists Claude *runs* the numbers and *shows* the steps — so you can
  verify them against your textbook.

## Next step

→ [docs/01 — Install Claude Code](01-install-claude-code.md)
