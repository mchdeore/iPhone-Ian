"""Base plate for JLCCNC: 3 mm aluminium, laser-cut. Holes are slotted wherever CAD error could matter.

Every position comes from v2_0_layout.py (single source of dimensions). Run from this folder:
    ../../.venv/Scripts/python.exe base_plate.py
Outputs: base_plate.step (quote / CAD check), base_plate.dxf (laser profile),
         base_plate_drawing.pdf (2D drawing for the JLCCNC upload; needs pymupdf in the venv),
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


def write_drawing(path):
    """A3 2D drawing for the JLCCNC upload: outline, numbered holes, hole table, notes. Geometry lives in the STEP."""
    import pymupdf
    W, H = pymupdf.paper_size("a3-l")
    doc = pymupdf.open()
    page = doc.new_page(width=W, height=H)
    S, OX, OY = 1.6, 70, 70                              # pt per mm; plate's top-left corner on the page
    px = lambda x: OX + (x + L.BASE_X / 2) * S
    py = lambda y: OY + (L.BASE_Y / 2 - y) * S
    black, blue = (0, 0, 0), (0.15, 0.4, 0.8)

    def text(x, y, s, size=7, color=black, rotate=0):
        page.insert_text((x, y), s, fontsize=size, fontname="helv", color=color, rotate=rotate)

    def arrow(tip, dx, dy):                              # filled arrowhead pointing along (dx, dy)
        bx, by = tip[0] - 6 * dx, tip[1] - 6 * dy
        page.draw_polyline([tip, (bx - 2 * dy, by + 2 * dx), (bx + 2 * dy, by - 2 * dx), tip],
                           color=black, fill=black, width=0.3)

    # cut profile, straight from the same sketch as the DXF
    shape = page.new_shape()
    for e in profile.edges():
        n = 2 if e.geom_type == GeomType.LINE else 25
        shape.draw_polyline([(px(p.X), py(p.Y)) for p in (e.position_at(i / (n - 1)) for i in range(n))])
    shape.finish(color=black, width=0.8)
    shape.commit()

    for i, (_, x, y, kind, angle) in enumerate(holes, 1):
        dx = 4.5 if kind == "slot" and angle == 0 else 2.5
        text(px(x) + dx * S, py(y) - 2.5 * S, f"H{i}", 6, blue)

    # overall dimensions + datum
    x0, x1, y0, y1 = px(-L.BASE_X / 2), px(L.BASE_X / 2), py(L.BASE_Y / 2), py(-L.BASE_Y / 2)
    yd, xd = y1 + 28, x0 - 28
    page.draw_line((x0, y1 + 4), (x0, yd + 4), color=black, width=0.3)
    page.draw_line((x1, y1 + 4), (x1, yd + 4), color=black, width=0.3)
    page.draw_line((x0, yd), (x1, yd), color=black, width=0.4)
    arrow((x0, yd), -1, 0); arrow((x1, yd), 1, 0)
    text((x0 + x1) / 2 - 12, yd - 4, f"{L.BASE_X:.1f}", 9)
    page.draw_line((x0 - 4, y0), (xd - 4, y0), color=black, width=0.3)
    page.draw_line((x0 - 4, y1), (xd - 4, y1), color=black, width=0.3)
    page.draw_line((xd, y0), (xd, y1), color=black, width=0.4)
    arrow((xd, y0), 0, -1); arrow((xd, y1), 0, 1)
    text(xd - 4, (y0 + y1) / 2 + 8, f"{L.BASE_Y:.0f}", 9, rotate=90)
    text(x1 - 60, y0 - 6, f"R{CORNER_R} typ. (4 corners)", 7)
    text(x0 + 4, y1 + 14, "DATUM (0, 0) = bottom-left corner", 7)
    page.draw_line((x0, y1), (x0 + 18, y1), color=black, width=1.2)
    page.draw_line((x0, y1), (x0, y1 - 18), color=black, width=1.2)

    # hole table
    tx, ty, row = 650, 72, 10.6
    cols = (0, 26, 112, 150, 188)
    for c, head in zip(cols, ("ID", "Type", "X", "Y", "Feature")):
        text(tx + c, ty, head, 7.5)
    page.draw_line((tx, ty + 3), (tx + 330, ty + 3), color=black, width=0.4)
    for i, (lab, x, y, kind, angle) in enumerate(holes, 1):
        kind_s = "Ø3.4 thru" if kind == "round" else f"slot 3.4×7.4, along {'X' if angle == 0 else 'Y'}"
        r = ty + 3 + i * row
        for c, s in zip(cols, (f"H{i}", kind_s, f"{x + L.BASE_X / 2:.1f}", f"{y + L.BASE_Y / 2:.1f}", lab)):
            text(tx + c, r, s, 7)

    notes = [
        "NOTES",
        f"1. Material: aluminium 5052-H32 (6061-T6 acceptable), {T:.1f} mm sheet. Qty 1.",
        "2. Laser cut. No bends, no threads, no countersinks.",
        f"3. All holes Ø{HOLE} through. Slots {HOLE} wide × {HOLE + TRAVEL:.1f} overall ({TRAVEL:.1f} between arc centres).",
        "4. Table gives hole / slot centres from the datum, in mm.",
        "5. General tolerance ISO 2768-m. Deburr all edges. Finish: none (raw).",
        "6. Geometry is defined by the STEP file. Drawing not to scale.",
    ]
    ny = ty + 3 + (len(holes) + 2) * row
    for j, s in enumerate(notes):
        text(tx, ny + j * 11, s, 8 if j == 0 else 7)

    tb = pymupdf.Rect(tx, H - 110, W - 30, H - 30)       # title block
    page.draw_rect(tb, color=black, width=0.8)
    text(tb.x0 + 10, tb.y0 + 24, "iPhone-Ian: BASE PLATE", 16)
    text(tb.x0 + 10, tb.y0 + 44, f"{L.BASE_X:.1f} × {L.BASE_Y:.0f} × {T:.1f} mm aluminium, {len(holes)} holes", 9)
    text(tb.x0 + 10, tb.y0 + 60, "Rev A  |  2026-10-10  |  units mm  |  source: aria/cad/base_plate.py", 8)
    doc.save(path)

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
    write_drawing("base_plate_drawing.pdf")
    print("exported base_plate.step / .dxf / _preview.svg / _drawing.pdf")
