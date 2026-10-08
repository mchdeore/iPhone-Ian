# marc/ — software (Marc)

Software lead: OCR / vision, training + reinforcement loop, agent, host control, credentials. Hardware lives in
[`../aria/`](../aria/).

| Path | What |
|---|---|
| [`DEVLOG.md`](DEVLOG.md) | Marc's dev log (v1 hardware snapshot, 2026-09-13) |
| [`parts-v1/`](parts-v1/) | v1 rod/oilite gantry CAD (build123d). **Retired** by the v2 CoreXY proposal — see `../aria/hardware-concept-v2.md` §4 |

Moved here from the repo root on 2026-10-02 (Aria) when we split the repo by owner. Note: `parts-v1/aliases.zsh` and its
README hard-code the old `parts/` path; update the `source` line in `~/.zshrc` to `marc/parts-v1/aliases.zsh` (and the
paths inside it) if you still use them.

Open items from the 2026-10-02 call: OCR + movement training code, exposed-parameter overview, functional diagram,
research organization, work/home inventory, nuke the database.
