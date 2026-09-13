"""Y-carriage bracket (real part) — the keystone of the gantry.

One of two. Each bracket:
  - rides a Y rod via a pressed-in bronze bushing (Y bore, near top),
  - holds BOTH X rod ends (X bores, near bottom) and CLAMPS them with grub screws,
    so the two rods + two brackets form one rigid ladder (stiff, no rattle),
  - is a SOLID block (100% infill) for stiffness, wear life, and quiet.

Print: PETG, 100% infill, oriented with the Y bore axis vertical on the bed so the
layer lines run across the main bending load (not peeling).

Run:  123_part 3      (export)      123_show 3   (view)

ponytail: fillets on internal corners are a later stress-relief refinement; the solid
          block already carries the load. Grub clamp tuned by GRUB_TAP.
"""
from build123d import *
from params import *

# ---- geometry (local frame: origin on the Y-rod axis) ----
dz       = 12.0                       # vertical gap: Y rod sits this far above the X rods
half_x   = ROD_SPACING / 2            # the two X rods, +/- this in Y
y_bore_r = BUSHING_OD / 2 - BUSHING_PRESS / 2   # press fit for the bronze bushing (Y rod)
x_bore_r = ROD_D / 2 + 0.25           # slip fit for the X rods (then grub-clamped)

body_x = 18.0                         # depth (along the X-rod axis)
z_top  = dz + y_bore_r + WALL         # top of the Y-bushing housing
z_bot  = -(x_bore_r + WALL)           # bottom of the X-rod housings
body_z = z_top - z_bot
body_y = 2 * (half_x + x_bore_r + WALL)   # spans both X rods + walls
cz     = (z_top + z_bot) / 2

# ---- fail-fast sanity checks ----
assert half_x + x_bore_r + WALL <= body_y / 2 + 1e-6, "body too narrow for the X-rod bores"
assert z_top > 0 and dz > y_bore_r, "Y bore and X bores overlap — increase dz"
assert body_x > 2 * (x_bore_r), "body too thin to hold the X rods"

with BuildPart() as bracket:
    with Locations((0, 0, cz)):
        Box(body_x, body_y, body_z)
    # Y bushing bore (rod runs along Y), near the top
    with Locations((0, 0, dz)):
        Cylinder(radius=y_bore_r, height=body_y + 2, rotation=(90, 0, 0), mode=Mode.SUBTRACT)
    # the two X-rod bores (rods run along X), near the bottom
    with Locations((0, half_x, 0), (0, -half_x, 0)):
        Cylinder(radius=x_bore_r, height=body_x + 2, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
    # grub-screw holes from the top down into each X bore (clamp the rods)
    with Locations((0, half_x, z_top / 2), (0, -half_x, z_top / 2)):
        Cylinder(radius=GRUB_TAP / 2, height=z_top + 2, mode=Mode.SUBTRACT)

if __name__ == "__main__":
    export_stl(bracket.part, "3_y_carriage_bracket.stl")
    export_step(bracket.part, "3_y_carriage_bracket.step")
    print("Exported STL + STEP. Part volume (mm^3):", round(bracket.part.volume, 1))
    import os
    if os.environ.get("SHOW"):
        from ocp_vscode import show, set_port
        set_port(int(os.environ.get("OCP_PORT", "3939")))
        show(bracket.part)
