"""Schematic ASSEMBLY PREVIEW v5 — FLAT: near-coplanar rods, side-mounted servo (view-only).

Design (per owner):
  - Flattest possible: X rods sit just UNDER the Y rods (near-coplanar), not stacked tall.
  - Bar order / stylus mounting are free -> chosen for minimum height.
  - Servo mounts on the SIDE of the carriage (no room beneath when this flat); short stylus.
  - X rods span between two Y-carriage brackets = the cross-members (no beam).
  - Y motor stands upright at the frame end; X motor rides the bracket. Clean straight belts.
  - Gantry parks aside so a top camera sees the surface; calibration/RL gives pointing accuracy.

Colors: grey=rod/pulley  yellow=printed  dark=motor/servo  black=belt  red=stylus
        translucent blue = context (surface/base), NOT apparatus.

Run:  123_show 0
"""
import os
from build123d import *
from params import *

STEEL, PRINTED, MOTOR = Color(0.72, 0.72, 0.75), Color(0.95, 0.74, 0.15), Color(0.18, 0.18, 0.20)
BELT, STYLUS, PULLEY  = Color(0.08, 0.08, 0.08), Color(0.85, 0.25, 0.15), Color(0.55, 0.55, 0.58)
CONTEXT = Color(0.30, 0.65, 1.00, 0.30)

parts = []
def add(s, c, l): s.color = c; s.label = l; parts.append(s)

# --- heights: kept as flat as possible ---
base_t, surf_th = 3, 4
surf_top = base_t + surf_th
Zx, Zy = 16, 28            # X rods just under Y rods (near-coplanar)
rail_x = Y_RAIL_X          # 100
half_x = ROD_SPACING / 2
Y_len  = WORK_Y + 70
X_len  = 2 * rail_x + 10
dz     = (Zy - Zx) / 2

# --- context ---
add(Pos(0, 0, base_t / 2) * Box(2 * rail_x + 30, Y_len + 10, base_t), CONTEXT, "baseplate (context)")
add(Pos(0, 0, base_t + surf_th / 2) * Box(WORK_X, WORK_Y, surf_th), CONTEXT, "work area: 2 iPhones (context)")

# --- frame posts + raised Y rods ---
for sx in (-1, 1):
    for sy in (-1, 1):
        add(Pos(sx * rail_x, sy * (Y_len / 2 - 8), Zy / 2) * Box(12, 12, Zy), PRINTED, "frame post")
for sx in (-1, 1):
    add(Pos(sx * rail_x, 0, Zy) * Rot(90, 0, 0) * Cylinder(radius=ROD_D / 2, height=Y_len), STEEL, "Y rail")

# --- short Y-carriage brackets: Y bushing on top, hold the two X rods just below ---
def bracket():
    b = Box(16, ROD_SPACING + 18, Zy - Zx + 12)
    b -= Pos(0, 0, dz) * (Rot(90, 0, 0) * Cylinder(radius=ROD_D / 2 + 0.5, height=ROD_SPACING + 24))
    for sy in (-1, 1):
        b -= Pos(0, sy * half_x, -dz) * (Rot(0, 90, 0) * Cylinder(radius=ROD_D / 2 + 0.5, height=22))
    return b
for sx in (-1, 1):
    add(Pos(sx * rail_x, 0, (Zx + Zy) / 2) * bracket(), PRINTED, "Y-carriage bracket")

# --- two X rods span the brackets = cross-members ---
for sy in (-1, 1):
    add(Pos(0, sy * half_x, Zx) * Rot(0, 90, 0) * Cylinder(radius=ROD_D / 2, height=X_len), STEEL, "X rail")

# --- compact hollow X-carriage ---
def carriage():
    c = Box(30, ROD_SPACING + 18, 12)
    for sy in (-1, 1):
        c -= Pos(0, sy * half_x, 0) * (Rot(0, 90, 0) * Cylinder(radius=ROD_D / 2 + 0.5, height=34))
    c -= Box(16, ROD_SPACING - 6, 14)
    return c
add(Pos(0, 0, Zx) * carriage(), PRINTED, "X-carriage (compact, hollow)")

# --- servo on the SIDE + short stylus ---
add(Pos(0, 26, Zx) * Box(14, 14, 12), MOTOR, "servo (tap / Z), side-mounted")
add(Pos(0, 26, (surf_top + 13) / 2) * Cylinder(radius=1.5, height=13 - surf_top), STYLUS, "stylus")

# --- X drivetrain: motor rides the +x bracket, straight belt along the X rods ---
add(Pos(rail_x + 13, 0, Zx) * Box(22, 18, 22), MOTOR, "X motor (rides gantry)")
add(Pos(rail_x - 2, 0, Zx) * Cylinder(radius=5, height=10), PULLEY, "X pulley")
add(Pos(-rail_x + 2, 0, Zx) * Cylinder(radius=5, height=10), PULLEY, "X idler")
for s in (-1, 1):
    add(Pos(0, -16 + s * 3, Zx) * Box(2 * rail_x, 1.5, 7), BELT, "belt")
add(Pos(0, -16, Zx) * Box(8, 10, 10), PRINTED, "belt clamp")

# --- Y drivetrain: motor stands upright at the frame end (shaft up), belt down the Y rail ---
add(Pos(rail_x, Y_len / 2 + 20, base_t + 20) * Box(42, 42, 40), MOTOR, "Y motor (upright)")
add(Pos(rail_x, Y_len / 2, Zy) * Cylinder(radius=5, height=10), PULLEY, "Y pulley")
add(Pos(rail_x, -Y_len / 2, Zy) * Cylinder(radius=5, height=10), PULLEY, "Y idler")
for s in (-1, 1):
    add(Pos(rail_x + 11 + s * 3, 0, Zy) * Box(1.5, Y_len, 7), BELT, "belt")
add(Pos(rail_x + 11, 0, Zy) * Box(10, 8, 10), PRINTED, "belt clamp")

if __name__ == "__main__":
    print(f"Assembly preview built: {len(parts)} components")
    if os.environ.get("SHOW"):
        from ocp_vscode import show, set_port
        set_port(int(os.environ.get("OCP_PORT", "3939")))
        show(*parts)
