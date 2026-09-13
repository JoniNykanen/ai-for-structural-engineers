# Eurocode timber examples (EN 1995-1-1 + SFS-NA)

Code-grounded timber design, driven by the **`eurocode-fi` skill** and the
**`params/na_timber.yaml`** parameter file. No copyrighted standard values live
in the code — you supply them from your licensed National Annex.

| File | What it does | Needs MATLAB? |
|---|---|---|
| `glulam_beam_ec5.py` | Simply-supported glulam beam: ULS bending (§6.1.6) + shear (§6.1.7) and SLS deflection (§7.2), with clause citations, utilisations, and an independent cross-check. Writes a Finnish calc note. | ❌ (Python) |

## Setup (once)

```bash
pip install -r requirements.txt          # includes pyyaml
cp params/na_timber.example.yaml params/na_timber.yaml   # then FILL from your licensed NA
```
The `.yaml` you fill is gitignored (your licensed values stay local). The blank
template with clause references is committed.

## Run

```bash
python examples/eurocode/timber/glulam_beam_ec5.py
```
Edit the `INPUTS` block (span, section, loads) at the top of the script. It
prints the checks and writes `laskumuistio_liimapuupalkki.md` (Finnish calc note).

If a required value is missing, it **stops and tells you which field + clause to
fill** — it never guesses a code value.

> Full explanation, copyright stance, and verification model: [docs/11](../../../docs/11-eurocode-fi.md).
> This is a design aid — the engineer remains responsible. Not a substitute for
> EN 1995-1-1 / SFS-NA.
