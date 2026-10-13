"""Rail riser bars (qty 2, identical): 1:1 drilling template on US Letter landscape.

Print at 100% / "Actual size", check the 100 mm scale bar, cut out the top view, tape it to the bar, punch the crosshairs.
Rail holes come from v2_0_layout.py (MGN9 pattern), plate holes from base_plate.py, so the template can't drift
from the plate that was cut. Run from this folder (needs pymupdf in the venv):
    ../../.venv/Scripts/python.exe riser_bar.py
Output: riser_bar_drawing.pdf
"""
import pymupdf
import v2_0_layout as L
from base_plate import holes as plate_holes

LENGTH = L.LONG_RAIL_L + 10                  # 240: rail centred with 5 mm of bar at each end
RAIL_PITCH, RAIL_END = 20, 5                 # MGN9 rail hole pattern
RAIL_X0 = (LENGTH - L.LONG_RAIL_L) / 2
rail_all = [RAIL_X0 + RAIL_END + i * RAIL_PITCH for i in range((L.LONG_RAIL_L - 2 * RAIL_END) // RAIL_PITCH + 1)]
# every other rail hole, kept symmetric (centre +/-10, 50, 90) so the bar can go on either way round
rail = [h for h in rail_all if (abs(h - LENGTH / 2) - 10) % 40 == 0]
plate = sorted({LENGTH / 2 + x for lab, x, *_ in plate_holes if lab == "rail riser"})
assert min(abs(r - q) for r in rail for q in plate) >= 10, "rail and plate holes too close"

K = 72 / 25.4                                # pt per mm: the page is drawn 1:1
W, H = pymupdf.paper_size("letter-l")
X0 = (W / K - LENGTH) / 2                    # bar's left end, mm from the page edge
BLACK, GREY, BLUE, RED = (0, 0, 0), (0.55, 0.55, 0.55), (0.1, 0.35, 0.8), (0.8, 0.15, 0.1)
DASH = "[2 1.5] 0"

doc = pymupdf.open()
page = doc.new_page(width=W, height=H)

def p(x, y):                                 # mm on the page -> pt
    return pymupdf.Point(x * K, y * K)

def line(x0, y0, x1, y1, color=BLACK, width=0.4, dashes=None):
    page.draw_line(p(x0, y0), p(x1, y1), color=color, width=width, dashes=dashes)

def rect(x0, y0, x1, y1, color=BLACK, width=0.6):
    page.draw_rect(pymupdf.Rect(p(x0, y0), p(x1, y1)), color=color, width=width)

def text(x, y, s, size=8, color=BLACK, align="left"):
    w = pymupdf.get_text_length(s, fontname="helv", fontsize=size) / K
    x += {"left": 0, "center": -w / 2, "right": -w}[align]
    page.insert_text(p(x, y), s, fontsize=size, fontname="helv", color=color)

def arrow(x, y, d):                          # horizontal arrowhead, tip at (x, y), pointing along d = +/-1
    page.draw_polyline([p(x, y), p(x - 2 * d, y - 0.7), p(x - 2 * d, y + 0.7), p(x, y)],
                       color=BLACK, fill=BLACK, width=0.2)

holes = sorted([(h, "R", BLUE) for h in rail] + [(h, "P", RED) for h in plate])
X1 = X0 + LENGTH

text(X0, 12, "iPhone-Ian: RAIL RISER BAR  (qty 2, identical)", 14)
text(X0, 18, "1:1 drilling template. Print at 100% / Actual size and check the scale bar before punching.", 8.5)

# top view, 1:1
TY = 42
line(X0, TY - 1, X0, 24); line(X1, TY - 1, X1, 24)
line(X0, 26, X1, 26); arrow(X0, 26, -1); arrow(X1, 26, 1)
text((X0 + X1) / 2, 25, f"{LENGTH:.0f}", 9, align="center")
text(X0, TY - 8.5, "0", 7.5, align="center")
for h, tag, c in holes:
    line(X0 + h, TY - 1, X0 + h, TY - 7, c, 0.3)
    text(X0 + h, TY - 8.5, f"{h:.0f}", 7.5, c, "center")
    text(X0 + h, TY + 14, tag, 8, c, "center")
rect(X0, TY, X1, TY + 10)
line(X0 - 3, TY + 5, X1 + 3, TY + 5, GREY, 0.3, "[6 1.5 1 1.5] 0")
for h, _, c in holes:
    page.draw_circle(p(X0 + h, TY + 5), 1.25 * K, color=c, width=0.4)
    line(X0 + h - 3, TY + 5, X0 + h + 3, TY + 5, c, 0.3)
    line(X0 + h, TY + 2, X0 + h, TY + 8, c, 0.3)
text(X0, TY + 21, "TOP VIEW, 1:1. Cut out along the outline, tape it to the bar, centre-punch each crosshair.", 8)

# side view, 1:1: rail on top, bar, plate underneath; holes dashed (through)
SY = 78
rect(X0 + RAIL_X0, SY - 6.5, X0 + RAIL_X0 + L.LONG_RAIL_L, SY, GREY, 0.4)
text((X0 + X1) / 2, SY - 2, f"MGN9 rail, {L.LONG_RAIL_L}", 7, GREY, "center")
rect(X0, SY, X1, SY + 10)
rect(X0 - 8, SY + 10, X1 + 8, SY + 13, GREY, 0.4)
text(X1 + 8, SY + 17, "base plate, 3 mm", 7, GREY, "right")
for h, _, c in holes:
    for dx in (-1.25, 1.25):
        line(X0 + h + dx, SY, X0 + h + dx, SY + 10, c, 0.3, DASH)
text(X0, SY + 17, "SIDE VIEW, 1:1. Every hole goes straight through. R screws come down through the rail, "
     "P screws come up through the plate.", 8)

# scale check
SC = 108
line(X0, SC, X0 + 100, SC, BLACK, 0.6)
for i in range(11):
    line(X0 + 10 * i, SC - (2 if i % 5 else 3.5), X0 + 10 * i, SC)
text(X0, SC + 4, "0", 7, align="center"); text(X0 + 100, SC + 4, "100 mm", 7, align="center")
text(X0 + 106, SC + 1, "Scale check: this must measure exactly 100 mm. If not, reprint at Actual size.", 8)

fmt = lambda xs: ", ".join(f"{x:.0f}" for x in xs)
text(X0, 124, f"R   rail screws, {len(rail)} holes:  {fmt(rail)}", 9.5, BLUE)
text(X0, 130, f"P   plate screws, {len(plate)} holes:  {fmt(plate)}", 9.5, RED)
text(X0 + 150, 124, "mm from either end", 8, GREY)

notes = [
    "NOTES",
    "1. Stock: 6061 aluminium, 10 x 10 x 304.8 mm (12 in). Cut each to 240 mm, square the ends, deburr.",
    "2. All holes on the centreline, 5 mm from each side. Centre punch, drill Ø2.5 straight through, tap M3 x 0.5 all the way through.",
    "3. Cutting oil on the drill and tap. Back the tap off every half turn to break the chip.",
    "4. The pattern is symmetric: measure from either end, drill from either face. Both bars are identical.",
    f"5. Before drilling the R holes, lay the rail 5 mm in from each end and check its holes sit at {fmt(rail_all[:3])} ... (20 mm pitch).",
    "6. P holes must match the plate within 0.2 mm along the bar. Best: mark them through the plate's slots once it arrives.",
    "7. Screws: M3 x 8 in every hole (rail from above, plate button heads from below).",
]
for j, s in enumerate(notes):
    text(X0, 142 + j * 6, s, 9 if j == 0 else 8.5)

text(X0, H / K - 8, "Rev A  |  2026-10-13  |  units mm  |  source: aria/cad/riser_bar.py", 7.5, GREY)
doc.save("riser_bar_drawing.pdf")
print(f"riser {LENGTH} mm: R {fmt(rail)} | P {fmt(plate)} -> riser_bar_drawing.pdf")
