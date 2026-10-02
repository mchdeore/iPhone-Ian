"""X-motor bracket (real part) — the +X Y-carriage bracket with an integrated NEMA-17 mount.

Same keystone bracket as part 3, plus a solid top plate carrying the X stepper (shaft
down, drive pulley below the plate at the belt line). One machine uses ONE of these
(the +X side) and one plain bracket (part 3) on the -X side.

NEMA-17: 31 mm bolt square (M3), 22 mm boss clearance bore. Solid, fused to the bracket.

Run:  123_part 4      (export)      123_show 4   (view)

ponytail: exact pulley height / belt-line offset is finalized with the pulley+belt task;
          here the plate is centered on the bracket (pulley over the rail end, which is
          where the X belt terminates).
"""
import importlib.util, os, sys
from build123d import *
from params import *

# --- reuse the finalized bracket (part 3) as the base solid ---
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
_spec = importlib.util.spec_from_file_location("p3", os.path.join(_here, "3_y_carriage_bracket.py"))
p3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p3)
base  = p3.bracket.part
z_top = p3.z_top

# This variant mounts the motor to the plate, so the plain bracket's top heat-set
# inserts are unused here -> fill them, or they'd become enclosed voids under the plate.
for _sx in (1, -1):
    base += Pos(_sx * p3.x_ins, 0, z_top - 3) * Cylinder(radius=HEATSET_D / 2, height=6)

# --- NEMA-17 mount plate on top ---
NEMA_BOLT = 31.0          # bolt-hole square spacing
NEMA_BOSS = 22.0          # raised-boss clearance diameter
plate_t   = 10.0
pcz = z_top + 2           # plate center: laps ~3 mm into the bracket so it fuses to one solid

plate = Pos(0, 0, pcz) * Box(46, 46, plate_t)
plate -= Pos(0, 0, pcz) * Cylinder(radius=NEMA_BOSS / 2, height=plate_t + 4)
for hx in (-NEMA_BOLT / 2, NEMA_BOLT / 2):
    for hy in (-NEMA_BOLT / 2, NEMA_BOLT / 2):
        plate -= Pos(hx, hy, pcz) * Cylinder(radius=M3_FREE / 2, height=plate_t + 4)

part = base + plate

# --- verify at import/run time that it's one fused solid ---
assert len(part.solids()) == 1, f"expected 1 solid, got {len(part.solids())}"

if __name__ == "__main__":
    export_stl(part, "4_x_motor_bracket.stl")
    export_step(part, "4_x_motor_bracket.step")
    bb = part.bounding_box()
    print("Exported STL + STEP. volume:", round(part.volume, 1),
          "size:", round(bb.size.X, 1), round(bb.size.Y, 1), round(bb.size.Z, 1))
    if os.environ.get("SHOW"):
        from ocp_vscode import show, set_port
        set_port(int(os.environ.get("OCP_PORT", "3939")))
        show(part)
