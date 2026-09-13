# MATLAB Engine API example

Proves the **Method 2** connection (docs/03): Python starts MATLAB, runs code,
and reads results back.

| File | What it does | Needs MATLAB? |
|---|---|---|
| `call_matlab_from_python.py` | Boots MATLAB via `matlab.engine`, runs a von Mises calc in MATLAB, prints results in Python | ✅ |

## Run it

First install the engine (see `docs/03-connect-matlab-engine-api.md`), then:

```bash
python call_matlab_from_python.py
```

If MATLAB isn't installed, the script prints a friendly message and points you to
the free Python path (`docs/05`) — it won't crash.
