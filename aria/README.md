# aria/ — hardware (Aria)

Hardware lead: CAD, parts, sourcing, assembly. Software lives in [`../marc/`](../marc/).

| File | What |
|---|---|
| [`hardware-concept-v2.md`](hardware-concept-v2.md) | Requirements, design, CAD review, **parts list with links + sourcing columns**, open questions |
| [`LOG.md`](LOG.md) | Dated log of decisions and to-dos |
| [`cad/v2_0_layout.py`](cad/v2_0_layout.py) | Layout model (build123d). `N_PHONES` near the top resizes the frame. Checks reach + collisions, exports STEP/STL |

Run the model (outputs are git-ignored):

```
cd aria/cad
../../.venv/Scripts/python.exe v2_0_layout.py     # Windows
../../.venv/bin/python v2_0_layout.py             # macOS/Linux
```

One-time setup at the repo root: `python -m venv .venv` then `pip install build123d` into it.
