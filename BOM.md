# Bill of Materials — iPhone-Ian v2

**Design:** CoreXY gantry, 2 phones, MKS DLC32 + FluidNC, spring-loaded grounded stylus. Full design: `aria/hardware-concept-v2.md`.

**Ordered 2026-10-08.** What was actually bought differs from this list in places (belt → PU steel-core, idlers → Mellow bearing type, heat-set inserts + screws reused from Olyntia). See `aria/LOG.md` for the as-ordered list. #23–25 bought (Amazon 2026-10-11, JLCCNC 2026-10-10); M3 tap bought 2026-10-16. Wiring and tools (#26–31) come from Aria's work where possible. Actual costs: **Spend log** at the bottom.

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
| 24 | 6061 rail risers, 10×10 mm | MECCANIXITY 10×10×305 mm, 2-pack (B0DFLS311P). Delivers ~Oct 13–14 (swapped from the slow COYOUCO 10×20). Cut each to 240 mm; drill 2.5 mm and tap M3, 6 rail holes on top and 4 plate holes underneath, spotted through the plate slots. 10 mm wide is fine because the rail is 9 mm and the plate holes sit on the riser centreline. | 1 | 13.99 | check at checkout | ☐ | ☐ |

## 3. JLCCNC — ordered 2026-10-10

| # | Part | Pick | Qty | C$ | Aria (work) | Marc (work) |
|---|---|---|---|---|---|---|
| 25 | Base plate, 3 mm aluminium, 340.6×320 mm, 40 M3 holes (mostly **slotted**) | 5052, raw finish, no threads; uploaded the STEP from `aria/cad/base_plate.py`. 20.60 + 31.13 shipping (Global Standard Direct Line); HST may apply at import | 1 | 51.73 | ☐ | ☐ |

## 3b. Wiring and tools — Aria sourcing from work; Amazon for anything work doesn't have

| # | Part | Why | Qty | Aria (work) | Marc (work) |
|---|---|---|---|---|---|
| 26 | Stepper cable, 4-pin XH2.54 ↔ 6-pin PH2.0, 1 m | Board motor sockets are XH2.54. Skip if the motors arrive with an XH plug already | 2 | ☐ | ☐ |
| 27 | Crimper + XH2.54/Dupont connector kit | Terminate the 26 AWG (servo signal, 5 V buck, stylus ground) onto board headers | 1 | ☐ | ☐ |
| 28 | Heat-shrink assortment | Solder joints, stylus ground | 1 | ☐ | ☐ |
| 29 | USB cable, board ↔ PC | FluidNC over USB (no radio) | 1 | ☐ | ☐ |
| 30 | M3 tap + handle, 2.5 mm drill bit, cutting oil | Tap the riser bars (#24) | 1 | ☐ | ☐ |
| 31 | Hacksaw + file | Cut risers to 240 mm, deburr | 1 | ☐ | ☐ |

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

## Spend log (actuals, C$)

Everything actually paid for iPhone-Ian hardware and tools. Split 50/50 with Marc.

| Date | Vendor | What | Before tax | Tax / shipping | Total | Paid by |
|---|---|---|---|---|---|---|
| 2026-10-08 | AliExpress | 21 lines: controller, 4 drivers, 2 motors, 2 servos, PSU, 5 V buck, endstops, 3× MGN9H, 2020, belt, pulleys, 12 idlers, nyloc nuts, shims, brass tube, springs, wire, servo ext, DC jacks, T-nuts | — | HST included | ~381 | Aria |
| 2026-10-10 | JLCCNC | Base plate, 5052, 3 mm | 20.60 | 31.13 shipping (+ import HST if billed on delivery) | 51.73 | Aria |
| 2026-10-11 | Amazon | MECCANIXITY 6061 10×10 bars ×2 (13.99) + PATIKIL 6 mm stylus tips (8.49) | 22.48 | 2.92 HST, free ship | 25.40 | Aria |
| 2026-10-16 | Amazon | uxcell M3 × 0.5 tap, 2-pack | 13.99 | 1.82 HST | 15.81 | Aria |
| | | **Total so far** | | | **≈ 473.94** | **≈ 237 each** |

**C$0 (already owned or borrowed):** M3 heat-set inserts + M2/M3/M4 screw kit (Olyntia's Amazon set); wiring, crimper, heat shrink, drill, hacksaw (Aria's work).

**Next to buy (Amazon, not yet ordered):** M3 × 30/35/40/45/50 **button**-head kit, 304 SS, 20 each (B0BJQ3BTV1, 16.39) for the idler axles (heads sit under the plate); M3 × 8 button head, 304 SS, 120 pcs (B0DNMZXHK2, 10.39) for the ~28 screws under the plate. ≈ 30.26 with HST. The Olyntia kit (LUKAISEN 820 pcs) is all socket head, M3 4–20 mm, so it covers everything on top of the plate.

**Why not cent-exact on AliExpress:** the listings render in CAD and ship free to Canada (HST added at checkout), but each item's displayed price depends on the variant selected and on account-specific coupons / new-shopper promos — e.g. the controller listing currently flashes a C$1.74 "new shopper" price on a *shell* variant, not the C$26.85 board. Your real cart total is whatever your own account shows at checkout, and it will likely be **lower** than this baseline once coupons apply, not higher. Recheck in your cart before paying.

## Before you place the order
- [ ] Recheck every AliExpress price and that each listing is still live.
- [ ] Marc ticks his work-sourcing column; Aria ticks his. Remove what's covered.
- [ ] Decide who places each order and the ship-to address.
- [ ] Order #23 (stylus tips) regardless — cheap and on the critical path.
- [ ] Hold #25 (plate) until its drawing is done.
