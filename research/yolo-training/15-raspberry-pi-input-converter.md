---
tags: [raspberry-pi, HID, hardware, control, ESP32, bluetooth, iOS]
status: answered
date: 2026-10-05
related:
  - "[[13-exposing-device-controls]]"
  - "[[../ios-control/01-faceid-autofill-accessibility]]"
  - "[[03-hardware]]"
---

# 15 — Raspberry Pi "input converter" between host and device

## Question

Should a Raspberry Pi (or cheaper MCU) sit between the model/host and the robot/phone —
as a **network→serial bridge** to the GRBL Arduino, or as a **USB/Bluetooth HID gadget**
driving the stock iPhone directly (AssistiveTouch pointer + hardware keyboard)? What does
iOS actually accept, and what's the minimal BOM + software stack?

Builds on `specs/02-firmware-and-software.md` §4.1 (dumb controller, smart host) and
`07-ios-control-constraints.md` (which flagged AssistiveTouch as "not useful" *for the
stylus approach* — this note reframes it as the entire mechanism *if* we add HID input).

Tags: `[Documented]` docs/vendor · `[Benchmark]` measured · `[Community]` forum/anecdote.

## TL;DR recommendation (lazy senior-dev)

- **Keep the gantry for taps.** Add a **HID keyboard** as a near-free upgrade for the
  `type` command — the gantry's weakest skill. iOS accepts hardware keyboards natively (full
  charset, no AssistiveTouch, no on-screen keyboard, no camera-captured keystrokes — a
  security plus for passwords). Cheapest: an **ESP32-S3** (~$6) serial→USB/BLE HID bridge.
- **Network→serial bridge:** only worth a Pi if the robot must be physically separated
  from the host (see `[[13-exposing-device-controls]]`). Otherwise the Mac's existing USB
  link to GRBL is already the bridge — don't add a box. If remote: **`ser2net` on a Pi
  Zero 2 W**, ~10 lines of config.
- **HID *mouse* as a full gantry alternative** is real (production precedent: VK DeviceHub)
  but **relative-pointer only** on iOS → dead-reckoning + visual servo, no true multitouch,
  and it abandons the physical premise. Flag as a research branch, not the default.

## The decisive constraint: iOS pointers are RELATIVE only `[Documented]`

- iOS 13+ exposes **AssistiveTouch pointer** support for a mouse/trackpad; keyboard works
  natively. Apple docs: Settings → Accessibility → Touch → AssistiveTouch. `[Documented]`
- **No absolute digitizer/touchscreen HID.** VK **DeviceHub** (a production device farm that
  drives real iPhones via an ESP32) states it plainly: *"Because the mouse is a relative
  pointing device… we convert the absolute target into relative deltas… set the highest
  sensitivity and keep track of the current (guessed) cursor position."* Apple Dev Forums
  agree (*"only relative mouse positions"*): an absolute/tablet descriptor (PiKVM's absolute
  mode) is **consumed as relative** by iOS AssistiveTouch. `[Documented]/[Community]`
- **Keyboard is the happy path.** iPhone accepts USB-C and BLE **HID keyboards** fully
  (any focused text field; even `Cmd+Space` → Spotlight via the HID report path). No
  cursor bookkeeping — a key is a key. `[Documented]`

## Option 1 — Pi as network→serial bridge to GRBL

Relocates the `pyserial` G-code streamer behind the network so the model/host (even the
CPU-only training box or a Windows machine) can reach the robot. Architecture unchanged.

- **`ser2net`** (cminyard, maintained → v4.6.7, Feb 2026): raw **TCP↔/dev/ttyUSB0**, config
  is a few lines. The host opens a socket instead of a local serial port. `[Documented]`
- **WebSocket** flavor if the controller is a browser/JS app: `SerialWebsocketJS`,
  or a ~30-line FastAPI `/move`/`/tap` daemon wrapping the §4.1 contract. `[Community]`
- Or **run the whole action executor on the Pi** (Pi 4 is plenty) — host sends intents,
  Pi owns the serial link. Best if you want the robot self-contained.
- **Verdict:** low-risk, boring, correct. But a Pi here is optional plumbing — only add it
  for physical/network separation, which is the subject of `[[13-exposing-device-controls]]`.

## Option 2 — Pi / ESP32 as USB HID gadget to the iPhone

Pi emulates keyboard + mouse via **`configfs` + `libcomposite`** on the **`dwc2`** UDC.
Which boards can be a USB *device* (not just host):

| Board | Device-mode port | Notes |
|---|---|---|
| Pi Zero / Zero W / **Zero 2 W** | micro-USB (the one labelled **USB**, not PWR) | Simplest, best-trodden gadget target `[Documented]` |
| **Pi 4** | USB-C (dual-role) | Works; `dwc2` overlay; USB-A ports are host-only `[Documented]` |
| **Pi 5** | USB-C power port, **USB 2.0 only** | Officially host+device per Pi engineers, but finicky/under-documented; users still fighting the UDC in 2025–26. **Avoid for HID.** `[Documented]/[Community]` |
| **ESP32-S2/S3**, **Pico/RP2040** | native USB (TinyUSB) | Cheapest real USB HID; no Linux to maintain `[Documented]` |

- Pi OS **Trixie (2026)** ships easier gadget-mode tooling out of the box. `[Documented]`
- **ESP32-C3/C6/WROOM cannot do USB HID** (no native USB) — they do **BLE** HID only
  (that's DeviceHub's path). For *USB* HID pick **S2/S3** or **RP2040**. `[Community]`

## Option 3 — Bluetooth HID (no cable to the phone)

- Pi via **BlueZ**: advertise an HID SDP record over L2CAP; many working emulators
  (`wof2/raspicontrol` explicitly lists iPad/iOS; `scientificRat` combined kbd+mouse gist).
  **PiKVM** ships a Bluetooth-HID mode (tested on Pi 4; costs the UART). `[Documented]/[Community]`
- **ESP32 BLE** is the cheap, clean version — DeviceHub recommends **ESP32-C6** (best in
  their tests), C3 nearly as good; board talks to the host over USB-serial (CDC) and to the
  iPhone over BLE. **No USB power negotiation with the phone at all.** `[Documented]`
- iOS pairs BLE HID keyboards/mice readily; one-time pairing in Settings. `[Community]`

## Option 4 — reuse existing projects

- **P4wnP1 A.L.O.A.** (mame82) — Pi Zero W composite USB gadget: HID injection + networking,
  driven over CLI/gRPC/web. Ready-made HID stack; `k1ubi` port to Pi 4B. `[Community]`
- **PiKVM / TinyPilot** — KVM-over-IP boxes whose `libcomposite` HID configs are directly
  liftable. They bundle **HDMI capture we don't need** (iPhone-Ian already has the camera).
  PiKVM supports **absolute + relative** mouse; **TinyPilot** was absolute-only until it
  added relative in **v3.1 (July 2026)** — relevant since iOS needs relative. `[Documented]`

## Latency, power, connectors

- **Latency:** USB HID report ~1–8 ms (near-instant); BLE HID ~15–30 ms (DeviceHub calls it
  "real time" for gestures). Both dwarf a gantry move (100s of ms). Either way you still gate
  the closed loop on the camera (~33 ms @30 fps) since the phone is a black box. `[Community]`
- **Power (USB-gadget to iPhone):** the phone is the USB *host* but caps accessory current
  → *"This Accessory Uses Too Much Power."* Fix: declare the gadget **self-powered** in the
  configfs descriptor (larsimmisch's Pi-4-for-iPad gist) **and** power the Pi externally. A
  **Lightning** iPhone (≤14) uses the **Lightning→USB-3 Camera Adapter** (pass-through port
  powers both); **USB-C** iPhones (15+) take a direct cable. **ESP32-BLE sidesteps all of
  this.** `[Documented]/[Community]` (Zero 2 W ~0.4–3 W; ESP32 ~0.3–0.7 W.)

## Calibration: dead-reckoning a relative cursor

Because iOS only takes relative deltas, you must track where the cursor *is*:

1. **Linearize the mapping:** max **Tracking Sensitivity** (Accessibility→Touch→AssistiveTouch)
   **and** max **Tracking Speed** (General→Trackpad & Mouse) so delta≈pixels with least
   acceleration curvature (DeviceHub's exact recipe). You can't fully kill iOS pointer
   acceleration — only flatten it; PiKVM's **"squash mouse moves"** (vector-sum of relative
   events) is prior art for taming it over a link. `[Documented]/[Community]`
2. **Corner reset = the hard-stop trick:** send a large delta toward a corner; the cursor
   **clamps** at the physical screen edge, giving a *known* absolute origin regardless of
   accumulated error; then move by a measured delta from there. Re-zero whenever drift
   suspected. (Standard relative-pointer dead-reckoning; the gantry analogue of homing.) `[Community]`
3. **Close the loop with the camera:** YOLO already *sees* the iOS cursor → visual-servo it
   onto the target. This **removes the gantry's mount-drift problem** (`01`§homography) and
   replaces it with cursor estimation — a genuinely attractive alternative calibration path.

## Recommended BOM + minimal software stack

**Minimal, do-this-first (keyboard upgrade): ~$6–12**
- 1× **ESP32-S3 dev board** (USB-C iPhone) *or* **ESP32-C3** (BLE, any iPhone) — serial→HID.
- USB-C cable (iPhone 15+) **or** Lightning→USB-3 Camera Adapter + cable (≤14), ~$39.
- Software: Arduino-ESP32 TinyUSB/BLE-HID sketch exposing a CDC text protocol
  (`type "foo"`, `key enter`); host sends over `/dev/tty*`. ~1 file. `[Documented]`

**If a networked robot bridge is needed: +~$15**
- 1× **Pi Zero 2 W** + micro-USB; `ser2net` TCP↔GRBL serial (or a tiny FastAPI daemon
  wrapping `move/tap/swipe/type`). Powered normally; no phone power issue.

**If pursuing the full HID-pointer alternative to the gantry:**
- **Pi Zero 2 W** (libcomposite kbd+mouse, P4wnP1 to bootstrap) **or** reuse PiKVM's HID
  configs; **self-powered** descriptor; max both iOS sensitivity sliders; dead-reckon +
  camera visual-servo + corner-reset. Multitouch/pinch remain out of reach — tap/scroll/type only.

**Avoid:** Pi 5 as a HID gadget (USB-C power port = USB 2.0, finicky); PiKVM/TinyPilot
*hardware kits* (pay for HDMI capture we don't use — lift their software only).

## Key takeaways

- iOS pointer = **relative only**; keyboard = **native/exact**. That asymmetry sets the strategy.
- Cheap win: a **HID keyboard** for `type` — ESP32-S3 (USB) or ESP32-C3 (BLE), ~$6.
- A Pi serial bridge is optional plumbing — justify it only via `[[13-exposing-device-controls]]`.
- HID mouse can replace the gantry's *pointing* (DeviceHub precedent) but needs dead-reckoning +
  camera visual-servo + self-powered USB, and gives up multitouch and the physical premise.
- **Zero 2 W** or **Pi 4** for USB-gadget; **not Pi 5**. ESP32-BLE dodges the power problem.

## Sources

- [Apple: pointer with AssistiveTouch](https://support.apple.com/en-us/111775) — iOS 13+ relative pointer + sensitivity `[Documented]`
- [Apple Dev Forums: absolute BT mouse?](https://developer.apple.com/forums/thread/652700) — "only relative positions" `[Community]`; [iPhone accepts BLE HID keyboard](https://developer.apple.com/forums/thread/835175) `[Community]`
- [VK DeviceHub — ESP32 iOS cursor](https://github.com/VKCOM/devicehub/blob/master/doc/ios-docs/esp32.md) — production relative→delta, max sensitivity, ESP32-C6/C3 BLE `[Documented]`
- [PiKVM mouse modes](https://github.com/pikvm/pikvm/blob/master/docs/mouse.md) abs/rel + squash-moves · [PiKVM Bluetooth HID](https://docs.pikvm.org/bluetooth_hid/) `[Documented]`
- [TinyPilot relative mouse v3.1, Jul 2026](https://tinypilotkvm.com/blogs/news/whats-new-in-tinypilot-3-1-0-relative-mouse) — was absolute-only `[Documented]`
- [Pi forum: Pi 5 USB-C = USB 2.0 host+device](https://raspberrypi.org/forums/viewtopic.php?t=383880) · [ohyaan dwc2 guide](https://ohyaan.github.io/tips/usb_ethernet_gadget_setup/) "no Pi 5" `[Documented]/[Community]`
- [charkster/rpi_gadget_mode](https://github.com/charkster/rpi_gadget_mode) — Pi 4 (USB-C) + Zero 2 W gadget `[Community]`
- [P4wnP1 A.L.O.A.](https://github.com/mame82/P4wnP1_aloa) · [Pi 4B port](https://github.com/k1ubi/p4wnp1e) — ready-made composite HID gadget `[Community]`
- [BRANDAY/esp32s3-usb-hid-bridge](https://github.com/BRANDAY/esp32s3-usb-hid-bridge) — S3 USB HID over CDC; why S3 not C3 `[Community]`
- [Lightning→USB-3 Camera Adapter power](https://support.apple.com/en-gb/111811) · [larsimmisch: self-powered gadget for iPad](https://gist.github.com/larsimmisch/5cc90ffe13869f63d4edb90ace35214d) fixes "too much power" `[Documented]/[Community]`
- [ser2net](https://github.com/cminyard/ser2net) — serial↔network bridge · [wof2/raspicontrol](https://github.com/wof2/raspicontrol) Pi BlueZ kbd+mouse (lists iPad) `[Documented]/[Community]`

## Open questions / follow-ups

- Lightning vs USB-C target iPhone? Decides adapter BOM → ties to open `iphone-model-target` in `questions.md`.
- Does pairing an HID accessory count as "stock/unmodified" under the charter (no jailbreak, just a toggle + paired device)? Flag for charter.
- Measured end-to-end latency of ESP32-BLE `tap` on current iOS vs the gantry — bench test `[Benchmark]`.
- Can corner-reset + max-sensitivity dead-reckoning hit passcode-pad accuracy, or is camera visual-servo needed every move? → candidate new row in `questions.md`.
