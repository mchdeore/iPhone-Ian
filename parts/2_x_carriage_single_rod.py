"""V2 carriage — SINGLE rod + anti-rotation skid (fewer bearings than V1).

Rides ONE steel rod on a single bronze bushing (half the bushings of the twin-rod V1).
A side outrigger arm ends in a downward slot that straddles a thin printed guide bar,
stopping the carriage from rotating about the rod.

Run:  123_part 2      (export)      123_show 2   (view)

ponytail: the skid is a plastic-on-plastic anti-rotation contact (ceiling: adds a little
          friction/wear). Fine for a slow, light tapper; if it drags, widen the slot or
          face the bar with tape/PTFE. This is the tradeoff for using one fewer bushing.
"""

from build123d import *
from params import *

# ---- parameters ----
block_len = 40.0
main_w    = BUSHING_OD + 16.0          # body around the single rod (wide enough for mount holes)
block_h   = BUSHING_OD + 8.0
bore_r    = BUSHING_OD / 2 - BUSHING_PRESS / 2
arm       = 34.0                       # reach out to the anti-rotation rail
arm_h     = 8.0                        # arm thickness (sits near the top)
bar_t     = 3.4                        # slot width to clear a ~3 mm printed guide bar
slot_depth = 6.0
hole_x    = main_w / 2 - 3.5           # mount-hole x (clears the central bore)

# ---- sanity checks ----
assert 0 < BUSHING_PRESS < 1, "BUSHING_PRESS must be a small positive fit (mm)"
assert bore_r * 2 + 3 < block_h, "block too short: not enough wall around the bushing bore"
assert hole_x - M3_FREE / 2 > bore_r, "mount holes would clip the rod bore"

with BuildPart() as carriage:
    # body around the single rod, with one bushing bore along Y
    Box(main_w, block_len, block_h)
    Cylinder(radius=bore_r, height=block_len + 2, rotation=(90, 0, 0), mode=Mode.SUBTRACT)

    # outrigger arm reaching to the anti-rotation rail (near the top)
    with Locations((main_w / 2 + arm / 2, 0, block_h / 2 - arm_h / 2)):
        Box(arm, block_len, arm_h)

    # downward-opening slot at the arm tip that straddles a thin printed guide bar
    with Locations((main_w / 2 + arm - bar_t / 2, 0, block_h / 2 - arm_h + slot_depth / 2)):
        Box(bar_t, block_len + 2, slot_depth, mode=Mode.SUBTRACT)

    # two M3 mount holes on the body top (clear of the rod bore)
    with Locations((hole_x, block_len / 2 - 8, 0), (-hole_x, -block_len / 2 + 8, 0)):
        Cylinder(radius=M3_FREE / 2, height=block_h + 2, mode=Mode.SUBTRACT)

if __name__ == "__main__":
    export_stl(carriage.part, "2_x_carriage_single_rod.stl")
    export_step(carriage.part, "2_x_carriage_single_rod.step")
    print("Exported STL + STEP. Part volume (mm^3):", round(carriage.part.volume, 1))
    import os
    if os.environ.get("SHOW"):
        from ocp_vscode import show, set_port
        set_port(int(os.environ.get("OCP_PORT", "3939")))
        show(carriage.part)
