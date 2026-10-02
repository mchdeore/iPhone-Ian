"""v2 LAYOUT (concept, view-only): CoreXY gantry over a row of 4 iPhones.

See docs/hardware-concept-v2.md. Real envelope dimensions, placeholder shapes, colors = real materials.

How it moves (CoreXY): both motors are FIXED at the +X end. Two belts (A low, B high) each run
toolhead -> bridge end idler -> along a side -> around their motor pulley -> back along the outside
-> across the -X end -> along the other side -> other bridge end idler -> back to the toolhead.
  motor A and B turn the SAME way      -> bridge moves along X (across the phones)
  motor A and B turn OPPOSITE ways     -> toolhead moves along Y on the bridge rail (down each phone)
Each pulley is wrapped 180 deg (motors) or 90 deg (idlers): the two strands leaving a pulley are
one pitch-diameter apart.

Frame: X = long axis (row of phones), Y = front/back, Z = up. Origin = base center.
Run:  ../.venv/Scripts/python.exe v2_0_layout.py   -> v2_0_layout.step / .stl
"""
from build123d import *

# ---------------- envelope (mm) ----------------
BASE_Y, BASE_T = 320, 3                   # base: 3 mm aluminium plate, laser-cut at JLCCNC (slotted holes); X derived below
FEET = 3
PITCH, N_PHONES = 95, 2                   # phones in the row: change this and the frame resizes
PHONE = (77.6, 163.0, 8.25)               # iPhone Pro Max body (worst case)
TRAY_T = 2
RAIL_Y = 105                              # long rails at y = +/- this
RISER = (20, 10)                          # aluminium flat bar 20 wide x 10 tall under each long rail
BRIDGE_RAIL_L, BRIDGE_L = 230, 240
STOCK_RAILS = (200, 215, 230, 250, 260, 280, 300, 320, 330, 350, 360, 380, 400, 420, 440, 450, 470, 490, 500)
MGN9_RAIL_W, MGN9_RAIL_H = 9, 6.5
MGN9H_L, MGN9H_W, MGN9H_TOP = 39.9, 20, 10   # carriage length, width, top above rail base
BRIDGE_W = BRIDGE_H = 20                  # 2020 extrusion
MOTOR = (42.3, 42.3, 23)                  # NEMA 17 pancake
MOTOR_B_RISE = 8                          # motor B sits on a spacer so its pulley lines up with belt B
GT2_PD = 12.73                            # 20T GT2 pitch diameter
R = GT2_PD / 2
FLANGE_R, PULLEY_H = 8, 8                 # pulley/idler flange radius, toothed-section height
BELT_W, BELT_T = 6, 1.5
LIFT = 3                                  # stylus tip clearance above glass when up
CAP_T = 3                                 # top plates that clamp idler bolts from above (double support)

glass_z = BASE_T + TRAY_T + PHONE[2]
rail_base_z = BASE_T + RISER[1]
bridge_z0 = rail_base_z + MGN9H_TOP
bridge_z1 = bridge_z0 + BRIDGE_H
ZA, ZB = bridge_z0 + 8, bridge_z0 + 16    # belt plane centers (A low, B high), both inside bridge height

# CoreXY belt geometry
YI = 125.0                                # inner strand: bridge-end idler -> its motor
YO = YI + GT2_PD                          # outer strand: motor -> far corner (one pitch diameter out)
YC = (YI + YO) / 2                        # motor pulley / corner idler centers
# frame sized from the phone count: stylus reach -> long-rail length (stock size, +10 mm margin) -> motors -> base
REACH = (N_PHONES - 1) / 2 * PITCH + PHONE[0] / 2          # stylus half-travel along X
LONG_RAIL_L = min(L for L in STOCK_RAILS if L >= 2 * (REACH + MGN9H_L / 2) + 10)
XM = LONG_RAIL_L / 2 + 9 + MOTOR[0] / 2   # motor pulleys at +XM (motors clear the rail risers), corner idlers at -XM
BASE_X = 2 * (XM + MOTOR[0] / 2 + 4)
X_BACK = 19.0                             # belts run along the BACK of the bridge at x = bridge + X_BACK
CLAMP_HALF = 15                           # toolhead belt clamp half-length (belts end on its faces)

STYLUS_DX = -(BRIDGE_W / 2 + MGN9_RAIL_H + 21)   # stylus tip vs bridge centerline (toolhead hangs in front)
xs = [(i - (N_PHONES - 1) / 2) * PITCH + STYLUS_DX for i in range(N_PHONES)]  # row shifted -> travel centered

# ---------------- colors = real materials ----------------
C = dict(
    plate=Color(0.70, 0.71, 0.74), rubber=Color(0.07, 0.07, 0.07), cf=Color(0.22, 0.22, 0.24),
    tpu=Color(0.12, 0.12, 0.13), alu=Color(0.83, 0.84, 0.87), steel=Color(0.60, 0.61, 0.64),
    stator=Color(0.10, 0.10, 0.11), phone=Color(0.30, 0.30, 0.33), glass=Color(0.04, 0.05, 0.09),
    servo=Color(0.08, 0.08, 0.09), brass=Color(0.80, 0.62, 0.25), belt=Color(0.03, 0.03, 0.03))

static, phones = [], []
def add(lst, shape, color, label):
    shape.color, shape.label = C[color], label
    lst.append(shape)
    return shape

def box(x, y, z, sx, sy, sz):                    # centered box
    return Pos(x, y, z) * Box(sx, sy, sz)

def cyl(x, y, z0, z1, r):                        # vertical cylinder from z0 to z1
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(radius=r, height=z1 - z0)

def belt_x(lst, y, x0, x1, z):                   # belt strand running along X
    if x1 - x0 > 0.5:
        add(lst, box((x0 + x1) / 2, y, z, x1 - x0, BELT_T, BELT_W), "belt", "GT2 belt")

def belt_y(lst, x, y0, y1, z):                   # belt strand running along Y
    if y1 - y0 > 0.5:
        add(lst, box(x, (y0 + y1) / 2, z, BELT_T, y1 - y0, BELT_W), "belt", "GT2 belt")

def pulley(lst, x, y, z, label, color="alu"):     # 20T pulley/idler: toothed body + two flanges
    add(lst, cyl(x, y, z - PULLEY_H / 2, z + PULLEY_H / 2, R), color, label)
    for s in (-1, 1):
        add(lst, cyl(x, y, z + s * (PULLEY_H / 2) - 0.5, z + s * (PULLEY_H / 2) + 0.5, FLANGE_R), color, label + " flange")

# ---------------- static: base, slots, rails ----------------
add(static, box(0, 0, BASE_T / 2, BASE_X, BASE_Y, BASE_T), "plate", "base plate (3 mm aluminium, JLCCNC)")
for sx in (-1, 0, 1):                              # 6 feet: middle pair stops the thin plate sagging
    for sy in (-1, 1):
        add(static, cyl(sx * (BASE_X / 2 - 20), sy * (BASE_Y / 2 - 20), -FEET, 0, 10), "rubber", "foot (black TPU)")

for i, x in enumerate(xs):
    add(static, box(x, 0, BASE_T + TRAY_T / 2, PITCH - 5, PHONE[1] + 12, TRAY_T), "cf", f"slot {i+1} tray (CF-PETG)")
    for sx in (-1, 1):
        for sy in (-1, 1):
            add(static, box(x + sx * (PHONE[0] / 2 + 2.5), sy * (PHONE[1] / 2 + 2.5), BASE_T + TRAY_T + 3, 5, 5, 6),
                "tpu", f"slot {i+1} corner pad (TPU)")
    z0 = BASE_T + TRAY_T
    add(phones, box(x, 0, z0 + (PHONE[2] - 0.3) / 2, PHONE[0], PHONE[1], PHONE[2] - 0.3), "phone", f"iPhone {i+1}")
    add(phones, box(x, 0, glass_z - 0.15, PHONE[0] - 2, PHONE[1] - 2, 0.3), "glass", f"iPhone {i+1} screen")

for sy in (-1, 1):
    y = sy * RAIL_Y
    add(static, box(0, y, BASE_T + RISER[1] / 2, LONG_RAIL_L + 10, RISER[0], RISER[1]), "alu", "rail riser (alu flat bar 20x10)")
    add(static, box(0, y, rail_base_z + MGN9_RAIL_H / 2, LONG_RAIL_L, MGN9_RAIL_W, MGN9_RAIL_H), "steel", f"MGN9 rail {LONG_RAIL_L}")

# ---------------- static: motors (+X end) and corner idlers (-X end) ----------------
for name, sy, zp, rise in (("A", 1, ZA, 0), ("B", -1, ZB, MOTOR_B_RISE)):
    my = sy * YC
    z_bot = BASE_T + rise
    if rise:
        add(static, box(XM, my, BASE_T + rise / 2, MOTOR[0], MOTOR[1], rise), "cf", f"motor {name} spacer (CF-PETG)")
    add(static, box(XM, my, z_bot + (MOTOR[2] - 3) / 2, MOTOR[0], MOTOR[1], MOTOR[2] - 3), "stator", f"NEMA17 pancake {name}")
    add(static, box(XM, my, z_bot + MOTOR[2] - 1.5, MOTOR[0], MOTOR[1], 3), "alu", f"NEMA17 {name} end cap")
    add(static, cyl(XM, my, z_bot + MOTOR[2], zp - PULLEY_H / 2, 6.5), "alu", f"pulley {name} hub")
    # motor clamp: two bars over the face-hole pairs (belts + pulley pass between them), legs to the base
    top = z_bot + MOTOR[2]
    for side in (-1, 1):
        by = my + side * 15.5
        add(static, box(XM + 2, by, top + 1.5, 46, 8, 3), "cf", f"motor {name} clamp bar (CF-PETG)")
        add(static, box(XM + 23, by, BASE_T + (top + 3 - BASE_T) / 2, 4, 8, top + 3 - BASE_T), "cf",
            f"motor {name} clamp leg (CF-PETG)")
    pulley(static, XM, my, zp, f"GT2 20T pulley {name} (motor)")

for sy in (-1, 1):
    cy = sy * YC
    add(static, box(-XM, cy, BASE_T + (ZA - PULLEY_H / 2 - 1 - BASE_T) / 2, 16, 16, ZA - PULLEY_H / 2 - 1 - BASE_T),
        "cf", "corner idler post (CF-PETG)")
    cap_z0 = ZB + PULLEY_H / 2 + 1
    add(static, cyl(-XM, cy, BASE_T, cap_z0 + CAP_T, 1.5), "steel", "M3 idler bolt (clamped both ends)")
    add(static, box(-XM - 4, cy, cap_z0 + CAP_T / 2, 24, 20, CAP_T), "cf", "corner idler top plate (CF-PETG)")
    add(static, box(-XM - 14.5, cy, BASE_T + (cap_z0 + CAP_T - BASE_T) / 2, 3, 20, cap_z0 + CAP_T - BASE_T), "cf",
        "corner idler side wall (CF-PETG, outside the belt)")
    pulley(static, -XM, cy, ZA, "idler A (corner)")
    pulley(static, -XM, cy, ZB, "idler B (corner)")

# ---------------- moving: bridge, toolhead, bridge-end idlers, belts ----------------
def gantry(bx, ty):
    """bx = bridge centerline X, ty = toolhead (= stylus) Y."""
    p = []
    x0 = bx + X_BACK                                   # belt line behind the bridge
    # long-rail carriages + bridge + its rail
    for sy in (-1, 1):
        add(p, box(bx, sy * RAIL_Y, rail_base_z + 1.5 + (MGN9H_TOP - 1.5) / 2, MGN9H_L, MGN9H_W, MGN9H_TOP - 1.5),
            "steel", "MGN9H carriage")
    add(p, box(bx, 0, (bridge_z0 + bridge_z1) / 2, BRIDGE_W, BRIDGE_L, BRIDGE_H), "alu", "bridge (2020 extrusion)")
    rail_x = bx - BRIDGE_W / 2 - MGN9_RAIL_H / 2
    add(p, box(rail_x, 0, (bridge_z0 + bridge_z1) / 2, MGN9_RAIL_H, BRIDGE_RAIL_L, MGN9_RAIL_W), "steel",
        f"MGN9 rail {BRIDGE_RAIL_L} (bridge)")
    # bridge end blocks carry the 4 bridge-end idlers (one per belt per end)
    for sy in (-1, 1):
        add(p, box(bx + 6.5, sy * 124.5, bridge_z0 + 1.5, 53, 33, 3), "cf", "bridge end block (CF-PETG)")
        cz0 = ZB + PULLEY_H / 2 + 1                    # top plate rests on the bridge via a 1 mm spacer
        add(p, box(bx + 12, sy * 125, cz0 + CAP_T / 2, 44, 32, CAP_T), "cf", "bridge end top plate (CF-PETG)")
        add(p, box(bx, sy * 115, (bridge_z1 + cz0) / 2, BRIDGE_W, 10, cz0 - bridge_z1), "cf", "top plate spacer")
    for x, y, z, lab in ((x0 + R, YI - R, ZA, "A+"), (x0 - R, YO - R, ZB, "B+"),
                         (x0 - R, -(YO - R), ZA, "A-"), (x0 + R, -(YI - R), ZB, "B-")):
        add(p, cyl(x, y, bridge_z0 + 3, ZB + PULLEY_H / 2 + 1 + CAP_T, 1.5), "steel", "M3 idler bolt (clamped both ends)")
        pulley(p, x, y, z, f"idler {lab} (bridge end)")
    # toolhead: carriage on the bridge rail, plate, servo, lever, sprung stylus, belt clamp
    fx = bx - BRIDGE_W / 2 - MGN9_RAIL_H               # front face of the bridge rail
    add(p, box(fx - 5, ty, (bridge_z0 + bridge_z1) / 2, 10, MGN9H_L, MGN9H_W), "steel", "MGN9H carriage (toolhead)")
    plate_z0 = glass_z + 7
    add(p, box(fx - 12.5, ty, (plate_z0 + bridge_z1) / 2, 5, 40, bridge_z1 - plate_z0), "cf", "toolhead plate (CF-PETG)")
    add(p, box(fx - 26, ty + 17.5, bridge_z1 - 6, 22, 23, 12), "servo", "MG90S servo (lying flat)")
    sx_, top = fx - 21, plate_z0 + 14
    add(p, box(sx_, ty + 4, top + 2, 10, 26, 4), "cf", "tap lever (CF-PETG)")
    add(p, cyl(sx_, ty, top - 8, top, 5), "cf", "stylus sleeve, spring inside (CF-PETG)")
    tip_z = glass_z + LIFT
    add(p, cyl(sx_, ty, tip_z + 3, top - 8, 2.5), "brass", "stylus barrel (brass tube, grounded)")
    add(p, cyl(sx_, ty, tip_z, tip_z + 3, 3), "rubber", "conductive stylus tip")
    add(p, box((fx - 15 + x0 + 7) / 2, ty, plate_z0 + 1.5, x0 + 7 - (fx - 15), 2 * CLAMP_HALF, 3), "cf",
        "toolhead under-bridge bracket (CF-PETG)")
    add(p, box(x0 + 2, ty, (plate_z0 + bridge_z1) / 2, 6, 2 * CLAMP_HALF, bridge_z1 - plate_z0), "cf",
        "belt clamp block (CF-PETG)")
    # belt A (low plane): toolhead -> A+ -> motor A -> outside -> -X end -> -Y side -> A- -> toolhead
    belt_y(p, x0, ty + CLAMP_HALF, YI - R, ZA)
    belt_x(p, YI, x0 + R, XM, ZA)
    belt_x(p, YO, -XM, XM, ZA)
    belt_y(p, -XM - R, -YC, YC, ZA)
    belt_x(p, -YO, -XM, x0 - R, ZA)
    belt_y(p, x0, -(YO - R), ty - CLAMP_HALF, ZA)
    # belt B (high plane): mirror image in Y
    belt_y(p, x0, -(YI - R), ty - CLAMP_HALF, ZB)
    belt_x(p, -YI, x0 + R, XM, ZB)
    belt_x(p, -YO, -XM, XM, ZB)
    belt_y(p, -XM - R, -YC, YC, ZB)
    belt_x(p, YO, -XM, x0 - R, ZB)
    belt_y(p, x0, ty + CLAMP_HALF, YO - R, ZB)
    return p

def gantry_at(x, y):                                   # place everything so the STYLUS TIP is over (x, y)
    return gantry(x - STYLUS_DX, y)

def travel_ok(x, y):
    bx = x - STYLUS_DX
    return abs(bx) + MGN9H_L / 2 <= LONG_RAIL_L / 2 and abs(y) + MGN9H_L / 2 <= BRIDGE_RAIL_L / 2

def clash(a_list, b_list):
    hits = []
    for a in a_list:
        for b in b_list:
            intended = (("MGN9H" in a.label and "rail" in b.label)          # carriage rides its rail
                        or ("belt" in a.label and ("pulley" in b.label or "idler" in b.label)))
            if not intended and (a & b).volume > 1e-3:
                hits.append((a.label, b.label))
    return hits

moving = gantry_at(xs[1], 20)                          # preview: stylus over phone 2

if __name__ == "__main__":
    corners = [(x + dx, dy) for x in xs for dx in (-PHONE[0] / 2, PHONE[0] / 2) for dy in (-PHONE[1] / 2, PHONE[1] / 2)]
    off_rail = [c for c in corners if not travel_ok(*c)]
    bad = []
    for c in corners:
        bad += clash(gantry_at(*c), phones + static)
    all_parts = static + moving + phones
    top = max(p.bounding_box().max.Z for p in all_parts)
    print(f"glass z {glass_z:.1f} | bridge underside {bridge_z0:.1f} | belt planes A {ZA} B {ZB} | top {top:.1f}")
    print(f"overall height incl. feet {top + FEET:.1f} mm | footprint {BASE_X} x {BASE_Y} mm")
    print("corners the carriages can't reach:", off_rail or "none")
    print(f"clashes with stylus at all {len(corners)} screen corners:", sorted(set(bad)) or "none")
    asm = Compound(children=all_parts, label="iPhone-Ian v2 layout")
    export_step(asm, "v2_0_layout.step")
    export_stl(asm, "v2_0_layout.stl")
    print("exported v2_0_layout.step / .stl with", len(all_parts), "components")
