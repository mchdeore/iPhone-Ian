"""Printed PETG bushing-carriage HOUSING (build123d).

Holds two pressed-in bronze oilite bushings (bought, self-lubricating); the steel rods
slide inside the bushings. This is the part the beam or the servo plate bolts onto.

Run:  python x_carriage_bushing_block.py
      -> writes x_carriage_bushing_block.stl and .step, prints volume, and (if the
         OCP CAD Viewer is running) shows the part live.

ponytail: press fit set by BUSHING_PRESS (ceiling: FDM bore accuracy ~0.1-0.2mm).
          If a bushing seats loose, add a drop of glue; if too tight, raise BUSHING_PRESS and reprint.
"""

from build123d import *
from params import *

# ---- part parameters (the knobs we'll tune together) ----
block_len = 40.0                       # length along travel (longer = less rock, more drag)
block_w   = ROD_SPACING + 30.0         # spans both rods, room for mount holes outboard
block_h   = BUSHING_OD + 8.0           # material around the bushing
bore_r    = BUSHING_OD / 2 - BUSHING_PRESS / 2   # housing bore = press fit on bushing OD
ox        = ROD_SPACING / 2 + 10       # x of the mounting holes (outboard, clear of the bores)

# ---- runnable sanity checks (fail fast if the geometry can't exist) ----
assert 0 < BUSHING_PRESS < 1, "BUSHING_PRESS must be a small positive fit (mm)"
assert block_w / 2 > ox + M3_FREE / 2 + 1, "block too narrow: mount holes fall off the edge"
assert bore_r * 2 + 3 < block_h, "block too short: not enough wall around the bushing bore"
assert ox - M3_FREE / 2 > ROD_SPACING / 2 + bore_r + 1, "mount holes clip the bushing bore"

with BuildPart() as carriage:
    Box(block_w, block_len, block_h)
    # two bushing bores running along Y (the travel direction)
    with Locations((-ROD_SPACING / 2, 0, 0), (ROD_SPACING / 2, 0, 0)):
        Cylinder(radius=bore_r, height=block_len + 2, rotation=(90, 0, 0), mode=Mode.SUBTRACT)
    # four M3 mount holes on the top face, clear of the bores
    corners = [(x, y, 0) for x in (-ox, ox) for y in (-block_len / 2 + 8, block_len / 2 - 8)]
    with Locations(*corners):
        Cylinder(radius=M3_FREE / 2, height=block_h + 2, mode=Mode.SUBTRACT)

if __name__ == "__main__":
    export_stl(carriage.part, "x_carriage_bushing_block.stl")
    export_step(carriage.part, "x_carriage_bushing_block.step")
    print("Exported STL + STEP. Part volume (mm^3):", round(carriage.part.volume, 1))
    # Live 3D view is opt-in: start the viewer first (`123_viewer`), then `123_show1`.
    import os
    if os.environ.get("SHOW"):
        from ocp_vscode import show, set_port
        set_port(int(os.environ.get("OCP_PORT", "3939")))
        show(carriage.part)
