"""Y-carriage bracket (real part) — the keystone of the gantry.

One of two. Each bracket:
  - rides a Y rod via a pressed-in bronze bushing (Y bore = BUSHING_OD press fit, near top),
  - holds BOTH X rod ends (X bores, near bottom) and CLAMPS them with grub screws,
    so the two rods + two brackets form one rigid ladder (stiff, no rattle),
  - carries two M3 heat-set inserts on top (belt clamp / X-motor mount attach),
  - is a SOLID block (100% infill) with filleted outer edges for stiffness + longevity.

Print: PETG, 100% infill, Y-bore axis vertical on the bed so layers run across the load.

Run:  123_part 3      (export)      123_show 3   (view)

ponytail: the block is convex+solid so it carries load without internal gussets; fillets
          just soften the outer edges. Grub clamp tuned by GRUB_TAP; bushing by BUSHING_OD.
"""
from build123d import *
from params import *

# ---- geometry (local frame: origin on the Y-rod axis) ----
dz       = 12.0                       # Y rod sits this far above the X rods
half_x   = ROD_SPACING / 2            # the two X rods, +/- this in Y
y_bore_r = BUSHING_OD / 2 - BUSHING_PRESS / 2   # press fit for the bronze bushing (Y rod)
x_bore_r = ROD_D / 2 + 0.25           # slip fit for the X rods (then grub-clamped)

body_x = 24.0                         # depth along the X-rod axis (full-depth rod engagement)
z_top  = dz + y_bore_r + WALL
z_bot  = -(x_bore_r + WALL)
body_z = z_top - z_bot
body_y = 2 * (half_x + x_bore_r + WALL)
cz     = (z_top + z_bot) / 2
x_ins  = y_bore_r + HEATSET_D / 2 + 0.6   # insert x, clear of the Y bore

# ---- fail-fast sanity checks ----
assert half_x + x_bore_r + WALL <= body_y / 2 + 1e-6, "body too narrow for the X-rod bores"
assert z_top > 0 and dz > y_bore_r, "Y bore and X bores overlap — increase dz"
assert x_ins - HEATSET_D / 2 > y_bore_r, "insert clips the Y bore"
assert x_ins + HEATSET_D / 2 < body_x / 2, "insert falls off the side"

with BuildPart() as bracket:
    with Locations((0, 0, cz)):
        Box(body_x, body_y, body_z)
    fillet(bracket.edges().filter_by(Axis.Z), radius=FILLET)
    # Y bushing bore (rod runs along Y), near the top
    with Locations((0, 0, dz)):
        Cylinder(radius=y_bore_r, height=body_y + 2, rotation=(90, 0, 0), mode=Mode.SUBTRACT)
    # the two X-rod bores (rods run along X), near the bottom
    with Locations((0, half_x, 0), (0, -half_x, 0)):
        Cylinder(radius=x_bore_r, height=body_x + 2, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
    # grub-screw holes from the top down into each X bore (clamp the rods)
    with Locations((0, half_x, z_top / 2), (0, -half_x, z_top / 2)):
        Cylinder(radius=GRUB_TAP / 2, height=z_top + 2, mode=Mode.SUBTRACT)
    # two M3 heat-set inserts on the top face (belt clamp / accessory mount)
    with Locations((x_ins, 0, z_top - 3), (-x_ins, 0, z_top - 3)):
        Cylinder(radius=HEATSET_D / 2, height=6, mode=Mode.SUBTRACT)

if __name__ == "__main__":
    export_stl(bracket.part, "3_y_carriage_bracket.stl")
    export_step(bracket.part, "3_y_carriage_bracket.step")
    print("Exported STL + STEP. Part volume (mm^3):", round(bracket.part.volume, 1))
    import os
    if os.environ.get("SHOW"):
        from ocp_vscode import show, set_port
        set_port(int(os.environ.get("OCP_PORT", "3939")))
        show(bracket.part)
