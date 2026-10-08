"""X-carriage (real part) — compact block that rides the two tight X rods.

- Two press-fit bronze bushings (bores along X, ROD_SPACING apart in Y); the X rods
  slide through the bushings -> this is what moves the stylus across the phone.
- Heat-set inserts on TOP (belt clamp -> belt tows the carriage) and on the BOTTOM
  (the adjustable stylus/servo holder bolts on, hanging toward the surface).
- SOLID block (100% infill), filleted edges. No grub screws (bushings are press-fit;
  the rods must slide). No see-through window: the tight 24 mm rod spacing leaves no
  room, and the gantry parks aside to view, so occlusion is a non-issue.

Print: PETG, 100% infill, a bore axis flat on the bed so layers don't peel under load.

Run:  123_part 1      (export)      123_show 1   (view)

ponytail: one bushing per rod (12 mm engagement); the 24 mm rod spacing resists roll/yaw.
          If pitch feels loose later, lengthen body_x for a second bushing per rod.
"""
from build123d import *
from params import *

half_x = ROD_SPACING / 2
bore_r = BUSHING_OD / 2 - BUSHING_PRESS / 2      # press fit for the bronze bushings
body_x = 18.0                                     # travel-direction length (bushing engagement)
body_y = 2 * (half_x + BUSHING_OD / 2 + WALL)     # spans both rods + walls
body_z = BUSHING_OD + 2 * WALL
ins_x  = 5.0                                      # heat-set inserts at +/- this in x, on y=0 centerline

# ---- fail-fast sanity checks ----
assert half_x + BUSHING_OD / 2 + WALL <= body_y / 2 + 1e-6, "body too narrow for the bushing bores"
assert bore_r < body_z / 2, "body too short for the bushing bores"
assert ins_x + HEATSET_D / 2 < body_x / 2, "inserts fall off the ends"

with BuildPart() as carriage:
    Box(body_x, body_y, body_z)
    fillet(carriage.edges().filter_by(Axis.Z), radius=FILLET)
    # two bushing bores along X (rods slide through the pressed-in bushings)
    with Locations((0, half_x, 0), (0, -half_x, 0)):
        Cylinder(radius=bore_r, height=body_x + 2, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
    # top inserts: belt clamp
    with Locations((ins_x, 0, body_z / 2 - 3), (-ins_x, 0, body_z / 2 - 3)):
        Cylinder(radius=HEATSET_D / 2, height=6, mode=Mode.SUBTRACT)
    # bottom inserts: adjustable stylus/servo holder
    with Locations((ins_x, 0, -body_z / 2 + 3), (-ins_x, 0, -body_z / 2 + 3)):
        Cylinder(radius=HEATSET_D / 2, height=6, mode=Mode.SUBTRACT)

if __name__ == "__main__":
    export_stl(carriage.part, "1_x_carriage.stl")
    export_step(carriage.part, "1_x_carriage.step")
    bb = carriage.part.bounding_box()
    print("Exported STL + STEP. volume:", round(carriage.part.volume, 1),
          "size:", round(bb.size.X, 1), round(bb.size.Y, 1), round(bb.size.Z, 1),
          "solids:", len(carriage.part.solids()), "shells:", len(carriage.part.shells()))
    import os
    if os.environ.get("SHOW"):
        from ocp_vscode import show, set_port
        set_port(int(os.environ.get("OCP_PORT", "3939")))
        show(carriage.part)
