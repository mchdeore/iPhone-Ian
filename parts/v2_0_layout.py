"""v2 LAYOUT (concept, view-only): CoreXY gantry over a row of 4 iPhones.

See docs/hardware-concept-v2.md. Real envelope dimensions, placeholder shapes.
Proves the height stack (~5 cm) and checks that nothing that moves hits a phone.

Frame: X = long axis (row of phones), Y = front/back, Z = up. Origin = base center.
Run:  ../.venv/Scripts/python.exe v2_0_layout.py   -> v2_0_layout.step / .stl
"""
from build123d import *

# ---- envelope (mm) ----
BASE_X, BASE_Y, BASE_T = 520, 320, 5
FEET = 3
PITCH, N_PHONES = 95, 4
PHONE = (77.6, 163.0, 8.25)        # iPhone Pro Max body (worst case)
TRAY_T = 2                         # slot floor (camera-bump pocket lives below the body)
RAIL_Y = 105                       # long rails at y = +/- this
RISER_H = 10                       # printed/extrusion riser under each long rail
MGN9_RAIL_H, MGN9_CAR_TOP = 6.5, 10.0   # rail height; carriage top above rail base
BRIDGE_W, BRIDGE_H = 20, 20        # 2020 extrusion
MOTOR = (42.3, 42.3, 23)           # NEMA 17 pancake
LIFT = 3                           # stylus tip clearance above glass when up

glass_z = BASE_T + TRAY_T + PHONE[2]
rail_base_z = BASE_T + RISER_H
bridge_z0 = rail_base_z + MGN9_CAR_TOP
bridge_z1 = bridge_z0 + BRIDGE_H
STYLUS_DX = -(BRIDGE_W / 2 + 6.5 + 21)   # stylus tip offset from bridge centerline (toolhead hangs in front)
STYLUS_DY = -13                           # stylus tip offset from toolhead carriage center
# phone row shifted by the stylus offset so the bridge's travel is centered on the frame
xs = [(i - (N_PHONES - 1) / 2) * PITCH + STYLUS_DX for i in range(N_PHONES)]

C = dict(base=Color(0.80, 0.68, 0.48), printed=Color(0.95, 0.74, 0.15), alu=Color(0.75, 0.76, 0.80),
         steel=Color(0.55, 0.56, 0.60), motor=Color(0.18, 0.18, 0.20), phone=Color(0.08, 0.08, 0.10),
         belt=Color(0.05, 0.05, 0.05), stylus=Color(0.85, 0.25, 0.15), tpu=Color(0.25, 0.55, 0.95))

static, moving, phones = [], [], []
def add(lst, shape, color, label):
    shape.color, shape.label = C[color], label
    lst.append(shape)
    return shape

def box(x, y, z, sx, sy, sz):          # box by min-corner-free center + size
    return Pos(x, y, z) * Box(sx, sy, sz)

# ---- base + feet ----
add(static, box(0, 0, BASE_T / 2, BASE_X, BASE_Y, BASE_T), "base", "base plate (plywood v1)")
for sx in (-1, 1):
    for sy in (-1, 1):
        add(static, Pos(sx * (BASE_X / 2 - 20), sy * (BASE_Y / 2 - 20), -FEET / 2)
            * Cylinder(radius=10, height=FEET), "tpu", "foot (TPU)")

# ---- phone slots ----
for i, x in enumerate(xs):
    add(static, box(x, 0, BASE_T + TRAY_T / 2, PITCH - 5, PHONE[1] + 12, TRAY_T), "printed", f"slot {i+1} tray")
    for sx in (-1, 1):
        for sy in (-1, 1):
            add(static, box(x + sx * (PHONE[0] / 2 + 2.5), sy * (PHONE[1] / 2 + 2.5),
                            BASE_T + TRAY_T + 3, 5, 5, 6), "tpu", f"slot {i+1} corner pad")
    add(phones, box(x, 0, BASE_T + TRAY_T + PHONE[2] / 2, *PHONE), "phone", f"iPhone {i+1}")

# ---- long rails (static) ----
RAIL_L = 450
for sy in (-1, 1):
    y = sy * RAIL_Y
    add(static, box(0, y, BASE_T + RISER_H / 2, RAIL_L + 10, 20, RISER_H), "printed", "rail riser")
    add(static, box(0, y, rail_base_z + MGN9_RAIL_H / 2, RAIL_L, 9, MGN9_RAIL_H), "steel", "MGN9 rail 450")

# ---- motors + pulleys at +X end (CoreXY: both motors fixed) ----
for sy in (-1, 1):
    mx, my = BASE_X / 2 - 26, sy * (BASE_Y / 2 - 30)
    add(static, box(mx, my, BASE_T + MOTOR[2] / 2, *MOTOR), "motor", "NEMA17 pancake")
    add(static, Pos(mx, my, BASE_T + MOTOR[2] + 7) * Cylinder(radius=6.5, height=14), "steel", "GT2 20T pulley")
    add(static, Pos(-BASE_X / 2 + 26, my, BASE_T + MOTOR[2] + 7) * Cylinder(radius=6.5, height=14), "steel", "idler")

# ---- belts along X (two layers, front + back) ----
for sy in (-1, 1):
    for lz in (rail_base_z + 14, rail_base_z + 22):
        add(static, box(0, sy * (BASE_Y / 2 - 30), lz, BASE_X - 52, 1.5, 6), "belt", "GT2 belt")

# ---- moving: bridge + toolhead at a given X / Y ----
def gantry(bx, ty):
    parts = []
    for sy in (-1, 1):
        add(parts, box(bx, sy * RAIL_Y, rail_base_z + 6, 40, 20, 8), "steel", "MGN9H carriage")
    bridge_len = 2 * (BASE_Y / 2 - 30) + 20
    add(parts, box(bx, 0, (bridge_z0 + bridge_z1) / 2, BRIDGE_W, bridge_len, BRIDGE_H), "alu", "bridge (2020)")
    add(parts, box(bx - BRIDGE_W / 2 - 3.25, 0, (bridge_z0 + bridge_z1) / 2, 6.5, 200, 9), "steel", "MGN9 rail 250 (bridge)")
    fx = bx - BRIDGE_W / 2 - 6.5          # front face of the bridge rail
    add(parts, box(fx - 5, ty, (bridge_z0 + bridge_z1) / 2, 10, 40, 20), "steel", "MGN9H carriage (toolhead)")
    plate_z0 = glass_z + 7
    add(parts, box(fx - 12.5, ty, (plate_z0 + bridge_z1) / 2, 5, 40, bridge_z1 - plate_z0), "printed", "toolhead plate")
    add(parts, box(fx - 26, ty + 4, bridge_z1 - 8, 22, 23, 12), "motor", "MG90S servo (lying flat)")
    tip_z = glass_z + LIFT
    add(parts, Pos(fx - 21, ty - 13, (tip_z + plate_z0 + 10) / 2) * Cylinder(radius=3, height=plate_z0 + 10 - tip_z),
        "stylus", "spring stylus (grounded)")
    return parts

def gantry_at(x, y):                      # place the gantry so the STYLUS TIP is over (x, y)
    return gantry(x - STYLUS_DX, y - STYLUS_DY)

# preview position: stylus over phone 2, mid-screen
moving = gantry_at(xs[1], 20)

# ---- checks ----
def clash(a_list, b_list):
    hits = []
    for a in a_list:
        for b in b_list:
            v = (a & b).volume
            intended = (('MGN9H carriage' in a.label and 'rail' in b.label) or
                        ('bridge' in a.label and 'belt' in b.label))   # rides on / belt ties to
            if v > 1e-3 and not intended:
                hits.append((a.label, b.label, round(v, 1)))
    return hits

if __name__ == "__main__":
    # put the stylus on every corner of every phone: nothing moving may hit a phone or the frame
    bad = []
    for x in xs:
        for dx in (-PHONE[0] / 2, PHONE[0] / 2):
            for dy in (-PHONE[1] / 2, PHONE[1] / 2):
                bad += clash(gantry_at(x + dx, dy), phones + static)
    all_parts = static + moving + phones
    top = max(p.bounding_box().max.Z for p in all_parts)
    print(f"glass top z = {glass_z:.1f} mm | bridge underside z = {bridge_z0:.1f} mm "
          f"(clearance {bridge_z0 - glass_z:.1f}) | toolhead plate bottom z = {glass_z + 7:.1f}")
    print(f"overall height incl. feet = {top + FEET:.1f} mm | footprint = {BASE_X} x {BASE_Y} mm")
    print("clashes with stylus at all 16 screen corners:", sorted(set(bad)) or "none")
    asm = Compound(children=all_parts, label="iPhone-Ian v2 layout")
    export_step(asm, "v2_0_layout.step")
    export_stl(asm, "v2_0_layout.stl")
    print("exported v2_0_layout.step / .stl with", len(all_parts), "components")
