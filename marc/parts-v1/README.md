# parts — how we design the mechanism together

Parts are defined in Python (**build123d**) and live here as `N_name.py`, numbered in
build order. Running a part exports an STL (to slice) and a STEP (editable later).
Because it's code, the assistant edits the files and you just run them.

## Commands (aliases — work from any directory)

Add this line once to `~/.zshrc`, then open a new terminal:
```
source /Users/cheddar/Documents/CODE/iPhone-Ian/parts/aliases.zsh
```

| Command | Does |
|---|---|
| `123_part 1`  (or `123_part1`) | render part `1_*.py`, export STL + STEP |
| `123_viewer` | open the 3D viewer in your browser (leave it running) |
| `123_show 1`  (or `123_show1`) | render part 1 and push it to the viewer |

The aliases call the venv's Python by absolute path, so you never `cd` or activate
anything — that's what broke a raw `source .venv/bin/activate` (it only works from the
repo root).

## Naming convention

`N_name.py` — N is build order. `params.py` (no number) holds machine-wide dimensions;
every part does `from params import *`, so one edit updates all parts. Each part carries
`assert(...)` checks that fail fast if a dimension is impossible.

## One-time environment (already set up on this machine)

A Python 3.12 venv at the repo root holds build123d:
```
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install build123d ocp_vscode
```
(`brew install python@3.12` if needed — the system Python 3.9 is too old.)

## Self-lubricating without niche filament: bronze oilite bushings

Print everything in **common PETG**. For the sliding surface, press a cheap **bronze
oilite bushing** (~$2, 8 ID x 12 OD) into the printed housing — oil-impregnated sintered
bronze is **self-lubricating**, no special filament. So: steel rod (precision) + printed
PETG housing + bronze bushing. `BUSHING_PRESS` in `params.py` tunes the press fit.

## Files

- `params.py` — shared machine dimensions (edit first).
- `1_x_carriage_bushing_block.py` — printed PETG bushing-carriage housing.
- `aliases.zsh` — the `123_*` shell helpers.
