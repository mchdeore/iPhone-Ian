"""Base plate for JLCCNC: 3 mm aluminium, laser-cut. Holes are slotted wherever CAD error could matter.

Every position comes from v2_0_layout.py (single source of dimensions). Run from this folder:
    ../../.venv/Scripts/python.exe base_plate.py
Outputs: base_plate.step (quote / CAD check), base_plate.dxf (laser profile),
         base_plate_preview.svg (plate + footprints of everything that sits on it).

Frame: X = long axis (row of phones), Y = front/back (+Y = back), origin = plate center.
All holes are M3 clearance; screws come up from below into heat-set inserts (printed parts) or tapped holes (risers).
Heads under the plate must be button heads (1.65 mm) to clear the 3 mm feet.
"""
from build123d import *
import v2_0_layout as L

T = L.BASE_T                 # 3 mm
HOLE = 3.4                   # M3 clearance
TRAVEL = 4.0                 # slot travel = +/-2 mm of adjustment
CORNER_R = 5
EDGE_MIN = 3.0               # min metal between a hole and the edge or another hole (>= thickness for laser cut)

holes = []                   # (label, x, y, kind, angle)   angle 0 = slot runs along X
def slot(label, x, y, along):
    holes.append((label, x, y, "slot", 0 if along == "x" else 90))
def rnd(label, x, y):
    holes.append((label, x, y, "round", 0))

# rail risers: 4 per riser, slots along Y so the two rails can be set parallel at the right spacing.
# x = +/-40, +/-100 sits midway between the MGN9 rail's own holes (20 mm pitch, 5 mm end distance on a 230 rail),
# so the tapped holes from above and below don't meet inside the 10 mm bar.
for sy in (-1, 1):
    for x in (-100, -40, 40, 100):
        slot("rail riser", x, sy * L.RAIL_Y, "y")

# motor cradles (+X end): 2 holes on the -X side + 2 on the inner side of each motor (the outer side and +X side
# are too close to the plate edge). Slots along X = belt-tension adjustment.
for sy in (-1, 1):
    my = sy * L.YC
    for dy in (-10, 10):
        slot("motor cradle", L.XM - 26, my + dy, "x")
    for dx in (-10, 10):
        slot("motor cradle", L.XM + dx, my - sy * 26, "x")

# corner idlers (-X end): idler bolt (slot along X, doubles as tensioner) + 2 anchors either side of the post,
# also slotted along X so the whole printed bracket slides with the bolt
for sy in (-1, 1):
    cy = sy * L.YC
    slot("corner idler bolt", -L.XM, cy, "x")
    for dy in (-14, 14):
        slot("corner bracket", -L.XM, cy + dy, "x")

# phone trays: 4 per tray, slots along X to center each tray under the stylus travel
for x in L.xs:
    for dx in (-38, 38):
        for dy in (-78, 78):
            slot("phone tray", x + dx, dy, "x")

# feet: screwed from the top, so only where nothing sits on the plate above them
FX, FY = L.BASE_X / 2 - 12, L.BASE_Y / 2 - 12
for x, y in ((FX, 0), (-FX, 0), (60, FY), (-60, FY), (60, -FY), (-60, -FY)):
    rnd("foot", x, y)

# reserved: camera mast base at the back edge, unused until the camera decision
for x in (-25, 25):
    for y in (L.BASE_Y / 2 - 10, L.BASE_Y / 2 - 24):
        rnd("camera mast (reserved)", x, y)


def cutter(x, y, kind, angle):
    if kind == "round":
        return Pos(x, y) * Circle(HOLE / 2)
    return Pos(x, y) * SlotCenterToCenter(TRAVEL, HOLE, rotation=angle)

profile = RectangleRounded(L.BASE_X, L.BASE_Y, CORNER_R)
for _, x, y, kind, angle in holes:
    profile -= cutter(x, y, kind, angle)
plate = extrude(profile, T)
plate.label = "base plate (3 mm aluminium, JLCCNC)"

# footprints of everything resting on the plate (2D, for clash checks and the preview)
def rect(x, y, sx, sy):
    return Pos(x, y) * Rectangle(sx, sy)

footprints = {}
for sy in (-1, 1):
    footprints[f"riser {sy:+d}"] = rect(0, sy * L.RAIL_Y, L.LONG_RAIL_L + 10, L.RISER[0])
    footprints[f"motor {sy:+d}"] = rect(L.XM, sy * L.YC, L.MOTOR[0], L.MOTOR[1])
    footprints[f"corner post {sy:+d}"] = rect(-L.XM, sy * L.YC, 16, 16)
    footprints[f"corner wall {sy:+d}"] = rect(-L.XM - 14.5, sy * L.YC, 3, 20)
for i, x in enumerate(L.xs):
    footprints[f"tray {i+1}"] = rect(x, 0, L.PITCH - 5, L.PHONE[1] + 12)

# what each hole is allowed to sit under (anything else is a clash)
ALLOWED = {"rail riser": "riser", "phone tray": "tray", "corner idler bolt": "corner post"}

if __name__ == "__main__":
    shapes = [(lab, cutter(x, y, k, a)) for lab, x, y, k, a in holes]
    problems = []
    for lab, s in shapes:
        bb = s.bounding_box()
        margin = min(L.BASE_X / 2 - max(abs(bb.min.X), abs(bb.max.X)),
                     L.BASE_Y / 2 - max(abs(bb.min.Y), abs(bb.max.Y)))
        if margin < EDGE_MIN:
            problems.append(f"{lab} at ({bb.center().X:.1f}, {bb.center().Y:.1f}): {margin:.1f} mm to edge")
        for name, fp in footprints.items():
            if (s & fp).area > 1e-3 and not name.startswith(ALLOWED.get(lab, "-")):
                problems.append(f"{lab} at ({bb.center().X:.1f}, {bb.center().Y:.1f}) sits under {name}")
    gaps = [shapes[i][1].distance_to(shapes[j][1]) for i in range(len(shapes)) for j in range(i + 1, len(shapes))]

    counts = {}
    for lab, *_ in holes:
        counts[lab] = counts.get(lab, 0) + 1
    print(f"plate {L.BASE_X:.1f} x {L.BASE_Y} x {T} mm, corner R{CORNER_R}, {len(holes)} holes (M3, slots +/-{TRAVEL/2:.0f} mm)")
    for lab, n in counts.items():
        print(f"  {n:2d}  {lab}")
    print(f"closest hole-to-hole metal: {min(gaps):.1f} mm (min {EDGE_MIN})")
    print("problems:", "none" if not problems else "")
    for p in problems:
        print("  -", p)

    export_step(plate, "base_plate.step")
    dxf = ExportDXF(unit=Unit.MM)
    dxf.add_layer("CUT")
    dxf.add_shape(profile, layer="CUT")
    dxf.write("base_plate.dxf")
    svg = ExportSVG(unit=Unit.MM, margin=5)
    svg.add_layer("parts", line_color=(40, 110, 220), line_weight=0.3)
    svg.add_layer("plate", line_color=(0, 0, 0), line_weight=0.5)
    for fp in footprints.values():
        svg.add_shape(fp, layer="parts")
    svg.add_shape(profile, layer="plate")
    svg.write("base_plate_preview.svg")
    print("exported base_plate.step / .dxf / _preview.svg")
