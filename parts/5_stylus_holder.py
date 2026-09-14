"""Stylus / servo holder (real part) — bolts under the X-carriage and does the tap (Z).

- Top flange bolts up into the carriage BOTTOM inserts (M3 at x = +/-5).
- Pocket for an MG90S micro servo (the tap actuator); its horn lifts/drops the stylus.
- A vertical guide bore holds a SPRING-LOADED stylus plunger: the spring gives a gentle,
  consistent contact force AND absorbs device-thickness variation (bare phone ~8, iPad ~7,
  cased ~12) over SPRING_TRAVEL, so one servo setting works across devices (the
  "calibration/adjustable height" done in software + spring, no fiddly mechanics).
- SOLID (100% infill), filleted.

FIRST PASS: servo pocket + plunger/spring dims are approximate — fit them to the real
MG90S, spring, and capacitive stylus you buy (say the word and I'll dial them in).

Run:  123_part 5      (export)      123_show 5   (view)

ponytail: exact horn->plunger actuation geometry is left simple here; refine once the real
          servo horn + stylus are in hand.
"""
from build123d import *
from params import *

# --- first-pass dims (mm) ---
FL_T   = 4.0                     # flange thickness (bolts to carriage bottom)
ARM_W  = 26.0                    # wide enough for the ~23 mm MG90S body
ARM_D  = 22.0                    # deep enough to separate servo (back) from stylus (front)
ARM_H  = 34.0                    # hangs down toward the surface
PLUNGER_D = 6.0                  # sprung-stylus shaft bore
SPRING_D  = 9.0                  # spring seat counterbore
SERVO_L, SERVO_W, SERVO_H = 23.0, 12.5, 23.0   # MG90S body pocket
SERVO_SCREW = 28.0               # MG90S mounting-hole spacing
gy = -ARM_D / 2 + 5              # stylus plunger sits toward the FRONT (-Y)

assert PLUNGER_D < SPRING_D < ARM_W, "spring seat won't fit"
assert SERVO_L < ARM_W and SERVO_W < ARM_D, "servo pocket won't fit the arm"

with BuildPart() as holder:
    # top flange + arm (same footprint -> one clean prism)
    with Locations((0, 0, -FL_T / 2)):
        Box(ARM_W, ARM_D, FL_T)
    with Locations((0, 0, -FL_T - ARM_H / 2)):
        Box(ARM_W, ARM_D, ARM_H)
    fillet(holder.edges().filter_by(Axis.Z), radius=FILLET)
    # bolt holes up into the carriage bottom inserts
    with Locations((5, 0, -FL_T / 2), (-5, 0, -FL_T / 2)):
        Cylinder(radius=M3_FREE / 2, height=FL_T + 2, mode=Mode.SUBTRACT)
    # MG90S pocket, opening on the BACK (+Y) face, upper part of the arm
    with Locations((0, ARM_D / 2 - SERVO_W / 2, -FL_T - 1 - SERVO_H / 2)):
        Box(SERVO_L, SERVO_W + 0.02, SERVO_H, mode=Mode.SUBTRACT)
    # servo mounting screw holes (through the arm, vertical pair)
    with Locations((0, 0, -FL_T - 5), (0, 0, -FL_T - 5 - SERVO_SCREW)):
        Cylinder(radius=1.1, height=ARM_D + 2, rotation=(90, 0, 0), mode=Mode.SUBTRACT)
    # sprung stylus guide bore (vertical, front) + spring seat counterbore near the top
    with Locations((0, gy, -FL_T - ARM_H / 2)):
        Cylinder(radius=PLUNGER_D / 2, height=ARM_H + FL_T + 2, mode=Mode.SUBTRACT)
    with Locations((0, gy, -FL_T - 6)):
        Cylinder(radius=SPRING_D / 2, height=SPRING_TRAVEL + 4, mode=Mode.SUBTRACT)

if __name__ == "__main__":
    export_stl(holder.part, "5_stylus_holder.stl")
    export_step(holder.part, "5_stylus_holder.step")
    bb = holder.part.bounding_box()
    print("Exported STL + STEP. volume:", round(holder.part.volume, 1),
          "size:", round(bb.size.X, 1), round(bb.size.Y, 1), round(bb.size.Z, 1),
          "solids:", len(holder.part.solids()), "shells:", len(holder.part.shells()))
    import os
    if os.environ.get("SHOW"):
        from ocp_vscode import show, set_port
        set_port(int(os.environ.get("OCP_PORT", "3939")))
        show(holder.part)
