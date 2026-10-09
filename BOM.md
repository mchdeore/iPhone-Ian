# Bill of Materials — iPhone-Ian v2

**Design:** CoreXY gantry, 2 phones, MKS DLC32 + FluidNC, spring-loaded grounded stylus. Full design: `aria/hardware-concept-v2.md`.

**Status:** prices verified 2026-10-01 (C$, before tax). **Recheck at order time** — AliExpress prices drift. Order target: weekend of 2026-10-10/11, so shipping (~2–3 weeks) overlaps printing and the plate quote.

**Split:** total ~C$325 + tax, 50/50 between Aria and Marc (≈ C$163 each before work-sourcing). Tick the **Aria (work)** / **Marc (work)** column for anything you can get free through work — it comes off the order.

---

## 1. AliExpress — electronics, motion, hardware (one order)

| # | Part | Pick | Qty | C$ | Aria (work) | Marc (work) |
|---|---|---|---|---|---|---|
| 1 | MKS DLC32 V2.1 controller | board only | 1 | 26.85 | ☐ | ☐ |
| 2 | BIGTREETECH TMC2209 drivers | 4-pack | 1 | 23.21 | ☐ | ☐ |
| 3 | STEPPERONLINE 17HE08-1004S motor | 23 mm, 1 A, 20 mm shaft | 2 | 24.16 | ☐ | ☐ |
| 4 | MG90S servo | 180° (not 360°/continuous) | 2 | 5.89 | ☐ | ☐ |
| 5 | 24 V PSU | 3 A, barrel | 1 | 10.93 | ☐ | ☐ |
| 6 | Mini560 **PRO** buck → 5 V | PRO only (6–30 V in) | 1 | 5.07 | ☐ | ☐ |
| 7 | Mechanical endstops w/ cable | 3-pack | 1 | 3.97 | ☐ | ☐ |
| 8 | MGN9H linear rail + block | 230 mm | 3 | 39.15 | ☐ | ☐ |
| 9 | 2020 V-slot extrusion (bridge) | 240 mm | 1 | 6.39 | ☐ | ☐ |
| 10 | GT2 belt, 6 mm rubber/aramid | 5 m | 1 | 6.16 | ☐ | ☐ |
| 11 | 20T motor pulley, 5 mm bore | for 6 mm belt | 2 | 6.86 | ☐ | ☐ |
| 12 | 20T idler, 3 mm bore | 6 toothed + 4 smooth | 10 | 25.62 | ☐ | ☐ |
| 13 | M3 brass heat-set inserts | — | 1 lot | 7.54 | ☐ | ☐ |
| 14 | M3 DIN912 cap screws | 8/12/16/20/25/50 mm | 1 lot | ~14 | ☐ | ☐ |
| 15 | M3 nyloc nuts | — | 1 lot | 2.83 | ☐ | ☐ |
| 16 | M3 shim washers, 0.5 mm | — | 1 lot | 2.38 | ☐ | ☐ |
| 17 | M3 T-nuts for 2020 | — | 1 lot | 2.94 | ☐ | ☐ |
| 18 | Brass tube, 5 mm OD, 0.25 wall | 4.5 ID fits stylus stem | 1 | ~7.41 | ☐ | ☐ |
| 19 | Compression springs, 0.5 mm wire | ~7 mm OD × 20 mm | 1 lot | ~5.28 | ☐ | ☐ |
| 20 | Silicone hookup wire, 26 AWG | 5 m | 1 | 3.78 | ☐ | ☐ |
| 21 | Servo extension, 1-to-1 | 50 cm | 1 | 2.29 | ☐ | ☐ |
| 22 | DC jack adapter, female 5.5×2.5 | — | 1 | 2.04 | ☐ | ☐ |
| | **AliExpress subtotal** | | | **~235** (~266 w/ HST) | | |

## 2. Amazon.ca — prices confirmed 2026-10-08, shipping to Waterloo N2J

| # | Part | Pick | Qty | C$ | Ship | Aria (work) | Marc (work) |
|---|---|---|---|---|---|---|---|
| 23 | PATIKIL stylus tips, 6 mm mesh, threaded metal stem | 5-pack, 6 mm variant (AliExpress only sells active Apple Pencil nibs — won't work). **Only ~6 in stock — buy now.** | 1 | 8.49 | free if in a $35+ Amazon order, else ~6 | ☐ | ☐ |
| 24 | 6061 rail risers, 10×20 mm | COYOUCO 10×20×500 (cut in half → 2 × ~240 mm). Separate seller (COYOUCO-CA), **slow: delivers ~Oct 30–Nov 20.** Or Metal Supermarkets Kitchener for pickup. | 1 | 26.64 | 5.54 | ☐ | ☐ |

## 3. JLCCNC — order AFTER the plate CAD exists

| # | Part | Pick | Qty | C$ | Aria (work) | Marc (work) |
|---|---|---|---|---|---|---|
| 25 | Base plate, 3 mm aluminium, ~341×320 mm, **slotted** holes | quote after CAD; slots absorb a few mm of CAD error | 1 | ~50 incl. ship | ☐ | ☐ |

## 4. Already owned — C$0

| Item | What | Role |
|---|---|---|
| Compute / host | Marc's PC: multi-year gaming CPU, 32 GB DDR4, **GTX 1080 (8 GB VRAM)**, M.2 SSD | Runs FluidNC's host driver **and** the local model (training + inference). The 8 GB VRAM is the binding constraint on model size — see `PIPELINE.md`. |
| 3D printers | Aria (Elegoo Centauri, CF filaments) + Marc's | All printed parts, free filament |
| Test phone(s) | Spare iPhone(s), test Apple ID, no personal accounts | Target device |

**Printed (CF-PETG / TPU):** corner idler posts + plates, side walls, motor clamps + legs, bridge end blocks + plates, toolhead plate + lever + stylus sleeve, belt clamp, endstop mounts, 2 phone slots, cable guides, feet, controller box.

---

## Final estimate — tax in, shipped to Waterloo, ON (HST 13%)

Checked 2026-10-08. Amazon prices are confirmed live; AliExpress prices use the 2026-10-01 browser-selected baseline (see note below).

| Order | Goods (C$) | Shipping | HST 13% | All-in (C$) |
|---|---|---|---|---|
| AliExpress (#1–22) | ~235 | free | ~30.6 | **~266** |
| Amazon.ca (#23–24) | 35.13 | 5.54 (+~6 if stylus unbundled) | ~5.3–6.1 | **~46–53** |
| JLCCNC plate (#25) | ~50 incl. ship | — | ~0–6.5 at import | **~50–57** |
| **Total** | | | | **≈ C$360–375** |

**≈ C$370 all-in. Split 50/50 ≈ C$185 each**, before anyone's work-sourcing ticks (each tick drops both shares).

**Why not cent-exact on AliExpress:** the listings render in CAD and ship free to Canada (HST added at checkout), but each item's displayed price depends on the variant selected and on account-specific coupons / new-shopper promos — e.g. the controller listing currently flashes a C$1.74 "new shopper" price on a *shell* variant, not the C$26.85 board. Your real cart total is whatever your own account shows at checkout, and it will likely be **lower** than this baseline once coupons apply, not higher. Recheck in your cart before paying.

## Before you place the order
- [ ] Recheck every AliExpress price and that each listing is still live.
- [ ] Marc ticks his work-sourcing column; Aria ticks his. Remove what's covered.
- [ ] Decide who places each order and the ship-to address.
- [ ] Order #23 (stylus tips) regardless — cheap and on the critical path.
- [ ] Hold #25 (plate) until its drawing is done.
