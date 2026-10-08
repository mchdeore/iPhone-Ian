"""iPhone-Ian shared machine parameters (mm). Import with `from params import *`.

Coordinate frame (looking down at the work surface):
  X = SHORT axis   Y = LONG axis   Z = tap (toward glass)
"""

# --- Work envelope: sized to fit TWO regular iPhones side by side; frame kept tight ---
WORK_X = 150    # short-axis working width  (~2 phones wide)
WORK_Y = 160    # long-axis working length

# --- Linear motion: steel rod + pressed-in bronze OILITE bushing (print only the housing) ---
ROD_D         = 8.0
BUSHING_OD    = 12.0
BUSHING_LEN   = 12.0
BUSHING_PRESS = 0.15
ROD_SPACING   = 24.0            # TIGHT spacing of the two X rods (the stylus carriage)
Y_RAIL_X      = WORK_X / 2 + 25 # half-distance between the two Y rods (clears the X-carriage travel)

# --- Device / tap geometry ---
DEVICE_H   = 8.0    # surface-top to glass; CALIBRATED per setup (bare iPhone ~8, iPad ~7, cased ~12)
TAP_STROKE = 6.0    # vertical tip travel for a tap (also how far it lifts to clear the glass while moving)
STYLUS_ADJ = 16.0   # vertical adjustment range of the stylus mount, to cover different device thicknesses
SPRING_TRAVEL = 4.0 # sprung-tip over-travel: absorbs height error + sets a gentle, consistent contact force

# --- Fasteners ---
M3_FREE   = 3.4
HEATSET_D = 4.2

# --- Reinforcement / print standard (quality build = solid parts) ---
# Print standard: PETG, 4-5 perimeters, 100% infill (parts are small), orient for load.
WALL     = 3.0    # minimum solid material around any bore
FILLET   = 2.0    # internal-corner radius to relieve stress
GRUB_TAP = 2.6    # M3 grub-screw tap hole (clamps the X rods into the brackets)
