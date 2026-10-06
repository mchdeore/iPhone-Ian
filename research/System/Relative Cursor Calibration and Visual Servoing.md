---
tags: [control, iOS, AssistiveTouch, HID, relative-pointer, visual-servoing, calibration, dead-reckoning, PID, latency]
status: answered
date: 2026-10-05
related:
 - ""
---

# 03 — Closed-loop cursor control with a RELATIVE-only iOS pointer

## Question

iOS AssistiveTouch accepts **only relative** pointer deltas `(dX,dY)` — there is no absolute
digitizer HID (``). Given a known screen
target `(sx,sy)`, how do we land the cursor there and click, using (a) corner/edge reset,
(b) linearizing the iOS acceleration curve, and (c) camera visual-servoing — and how does
per-tap accuracy/latency compare to the gantry?

## Key findings

### 1. The core problem: relative pointer + hidden, accelerated mapping

- **Relative only, position unknown to the device.** VK **DeviceHub** (production iOS farm, ESP32-BLE):
 *"the mouse is a relative pointing device… we convert the absolute target… into mouse events with
 relative deltas… setting the highest possible sensitivity… and keep track of the current (guessed)
 position of the iOS cursor."* So you must *estimate* the cursor (dead-reckon) or *see* it (camera); an
 absolute HID descriptor is consumed as relative anyway (``). `[Documented]`
- **The mapping is nonlinear & unobservable.** iOS applies a pointer-accel (gain) curve: pointer
 velocity = f(input velocity), input velocity = `delta × report_rate`. The same displacement sent as
 **one big delta** lands farther (high-gain) than **many small deltas** (near-linear) — the Arduino
 relative-mouse note: *"position did not reflect… expected… due to 'mouse acceleration'. The
 workaround… only move small distances at a time."* `[Community]`

### 2. iOS tuning: flatten, don't disable (you cannot fully disable it)

| Setting | Path | Effect |
|---|---|---|
| **AssistiveTouch ON** | Settings → Accessibility → Touch → AssistiveTouch | enables pointer `[Documented]` |
| **Tracking Sensitivity → max** | …→ AssistiveTouch | largest px per unit (DeviceHub recipe) `[Documented]` |
| **Tracking Speed → max** | Settings → General → Trackpad & Mouse | flattens high end of curve `[Documented]` |
| **Trackpad Inertia → OFF** | Settings → Accessibility → Pointer Control | kills coast/glide after a move `[Documented]` |

- **No iOS switch disables pointer acceleration** (unlike macOS Mouse → Advanced, or `defaults write
 .GlobalPreferences com.apple.mouse.scaling -1`): you can only **flatten** (max speed) + **remove
 inertia**; the curve persists → closed-loop or careful dead-reckoning is mandatory. `[Documented]`
- **HID delta caps the "slam":** boot-protocol reports signed **8-bit** X/Y (−127..+127/report) →
 crossing a ~1200 px screen needs *many* reports (16-bit descriptors exist but assume 8-bit, loop). `[Documented]`

### 3. Method A — Corner/edge reset (homing a relative pointer) `[Community]`

The one trick that gives an **absolute** origin from a relative device: drive hard into a corner; the
OS **clamps** the cursor at the physical edge, so position becomes known (0,0) regardless of prior
drift. Canonical statement: *"move the pointer enough in each direction that it is certain it is now
located at one of the corners… a reference point from which to base all relative movements."* It is the
HID analogue of GRBL `$H` homing (``). The `per1234/MouseTo` Arduino library
packages exactly this: home-to-corner + incremental move + position tracking.

- **Slam** = burst of max reports (e.g. 15–25× `(−127,−127)`) until two frames show no motion → pinned
 at (0,0). **Re-zero policy** (Arduino thread): *home once then dead-reckon* (fast, slip corrupts all
 later moves) vs *home every move* (robust, costs a slam). We **home once/session + on drift**, camera as detector (§5).

### 4. Method B — Linearize the acceleration curve (calibrate px-per-unit) `[Benchmark]`-plan

Gain depends on `delta × rate`: fix a **small per-report delta** in the near-linear band and modulate
distance by **report count** at **fixed rate** → `px ≈ k·n`, a clean invertible model. Measure `k` per Tracking-Speed setting:

```
calibrate_scale():           # run once per device/settings profile
  assert AssistiveTouch on; sensitivity+speed maxed; inertia off  # manual, §2
  corner_reset()            # known origin (0,0)
  d, rate = 20, 100          # small delta (units/report), reports/sec
  samples = []
  for n in [5,10,20,40,80]:
    corner_reset()
    send_n_reports(dx=d, dy=0, n=n, rate=rate); sleep(SETTLE)
    px = detect_cursor().x      # camera-measured displacement from origin
    samples.append((n*d, px))
  k = slope(linregress(samples))    # px per mouse-unit (near-linear region)
  # control check: ONE delta of 400 units lands FARther than k*400 (accel) ->
  # proves "many small" beats "one big"; keep per-report delta <= ~110 units.
  return k               # dead-reckoning gain; servo gain Kp ~ 1/k
```

Lower Tracking Speed → smaller `k` (finer, more reports/screen); store `k` with the settings profile, re-run if a slider changes.

### 5. Method C — Camera visual-servoing (the robust path) `[Community]`

Dead-reckoning alone drifts (accel residual + packet loss); the **camera already sees the screen**, so
close the loop on the **cursor** itself. Detect the AssistiveTouch pointer (a ~size-adjustable grey
circle) as a dedicated **YOLO class** or by **template match** on the rectified screen image
(``), then proportional/PID-correct until within `TOL` px.
This **removes the gantry's `H_screen→gantry` calibration and mount-drift problem** entirely
(``): screen px map straight to pointer deltas.

```
servo_to(target_sx, target_sy):     # closed-loop; returns on success/giveup
  TOL, Kp, MAX_IT, CAP = 8, 0.9/k, 8, 110    # px, units/px, iters, per-report cap
  integ = (0,0)
  for i in range(MAX_IT):
    frame = camera.grab()           # 33 ms @30fps (16 @60)
    screen = rectify(frame, H_cam2screen)    # per-frame fiducial homography
    cur  = detect_cursor(screen)       # YOLO 'cursor' class / template match
    if cur is None:               # off-screen or occluded
      corner_reset(); continue
    ex, ey = target_sx-cur.x, target_sy-cur.y
    if hypot(ex,ey) <= TOL: break        # converged
    integ = clamp(integ + (ex,ey)*Ki)      # small Ki only if steady-state bias
    dux  = clamp(Kp*ex + integ.x, -CAP, CAP)  # P(+I); D rarely needed, 1 contact
    duy  = clamp(Kp*ey + integ.y, -CAP, CAP)
    send_relative(dux, duy, rate=100)      # 1+ reports, fixed rate (near-linear)
    sleep(SETTLE)                # ~1 frame + iOS render (40-75 ms, note 07)
  click()                     # HID button down -> >=50-100 ms -> up
```

- **Convergence** ~**3–6 iters** to `TOL≤8 px` with `Kp≈0.9/k` (`<1` avoids overshoot into the
 high-gain band); D unneeded (single contact, inertia off), tiny I only for constant bias. **Accuracy
 floor** = cursor centroid (~1–3 px) + homography (few px) → **a few px regardless of the accel
 curve**, enough for keyboard/passcode keys that dead-reckoning alone misses (`` open Q). `[Community]`

### 6. Prior art & KVM-over-IP relative-mode lessons

- **DeviceHub:** relative→delta + max sensitivity + guessed-position tracking over **BLE** (ESP32-C6
 best, C3 close); paired with WebDriverAgent **screencapture**, not a camera. `[Documented]`
- **PiKVM:** relative mode "exclusively captures" the cursor and *"generates a huge number of events…
 optimized using a vector sum"* (**"Squash mouse moves"**, toggle off if accel misbehaves) — prior art
 for taming relative streams; rel unsupported on mobile browsers/VNC. **TinyPilot** added rel only in **v3.1 (Jul 2026)**. `[Documented]`
- **Gotchas:** GL.iNet's relative mode **broke tap-to-click on touchscreens** (we click via a separate
 HID **button**, so unaffected). **Mouse-jiggler** (PiKVM: 1 px nudge/~60 s) is the trivial relative
 baseline + our anti-sleep keep-alive — proves iOS accepts tiny deltas reliably. `[Community]/[Documented]`

### 7. Latency & accuracy per tap vs the gantry `[Benchmark]`-estimate (not yet benched on our rig)

Component budget: HID report **USB 1–8 ms / BLE 15–30 ms**; camera obs **33 ms @30fps**; detector
**~3–30 ms** (nano YOLO/template, note 08); iOS touch settle **40–75 ms** (note 07).

| Path | Per-tap time | Accuracy | Notes |
|---|---|---|---|
| Dead-reckon only (session reset) | ~0.15–0.3 s | poor on small targets (drift) | fine for big buttons |
| **Relative + camera servo** (3–6 iters) | **~0.3–0.6 s** | **~few px** | recommended default |
| Relative + corner-reset **every** move | ~0.5–1.0 s | few px | most robust, slowest |
| **Gantry** tap (traverse+Z dwell) | ~0.5–2 s | sub-mm mech. + homography | note 15 "100s of ms"; README "seconds" |

**Verdict:** both paths share the **same camera observation floor**, so HID is *comparable*, not
dramatically faster. HID's real wins: the **click is electronic/instant** vs the gantry's Z-lower +
≥100 ms capacitive dwell; no mechanical traverse; and it **deletes `H_screen→gantry` calibration and
mount-drift** — at the cost of cursor-estimation and a one-time accessibility toggle (``). Keep the camera loop either way; the phone is a black box.

## Sources

- [VKCOM/devicehub esp32.md](https://github.com/VKCOM/devicehub/blob/master/doc/ios-docs/esp32.md) — relative→delta, max sensitivity, guessed-cursor tracking; ESP32-C6/C3 BLE `[Documented]`
- [Arduino forum: BLE HID absolute positioning](https://forum.arduino.cc/t/ble-hid-mouse-with-cursor-absolute-positioning/1216238) — corner-reset "homing", accel workaround "many small moves" `[Community]`; [per1234/MouseTo](https://github.com/per1234/MouseTo) — home+increment+track library `[Community]`
- [PiKVM mouse.md](https://github.com/pikvm/pikvm/blob/master/docs/mouse.md) — abs vs rel, "Squash mouse moves" vector-sum, rel not on mobile browsers `[Documented]`; [PiKVM jiggler](https://docs.pikvm.org/mouse_jiggler/) + [1px gist](https://gist.github.com/Overemployed/ccf6f48c68af2b874b573d10ba445618) `[Documented]/[Community]`; [TinyPilot rel v3.1 Jul 2026](https://tinypilotkvm.com/blogs/news/whats-new-in-tinypilot-3-1-0-relative-mouse) `[Documented]`
- Apple: [pointer + AssistiveTouch](https://support.apple.com/en-gb/HT210546) (Tracking Speed) · [AssistiveTouch](https://support.apple.com/en-ca/111794) · [Trackpad Inertia off](https://discussions.apple.com/thread/253160979) · [macOS pointer-accel OFF (contrast)](https://support.apple.com/en-my/guide/mac-help/mchlp1138/mac) `[Documented]`
- [espressif/arduino-esp32 #9232](https://github.com/espressif/arduino-esp32/issues/9232) — 8-bit vs 16-bit relative delta range `[Documented]`
- [GL.iNet: relative mode breaks tap-to-click](https://forum.gl-inet.com/t/relative-mode-does-not-support-tapping-to-click-on-touchscreen-devices-fw-1-7-0/66256) `[Community]`; [HijelHID_BLEMouse](https://github.com/HijelHub/HijelHID_BLEMouse) — current ESP32 BLE HID mouse, iOS-tested `[Community]`

## Open questions / follow-ups

- **Bench the estimates in §7** on the actual ESP32-BLE + camera rig (per-tap time, iters-to-converge,
 landed px error) → promote `[Benchmark]`-plan to measured; resolves the `hid-vs-gantry` open row and
 note-15's "corner-reset dead-reckoning vs camera-servo for passcode-pad accuracy" in `questions.md`.
- Is the AssistiveTouch pointer **reliably detectable** through the camera (grey circle, user-set size,
 low contrast on light UIs)? Needs a dedicated YOLO `cursor` class + synthetic data (``).
- Does the HID **click** register as a tap without a dwell, or does iOS require a minimum touch
 duration like the capacitive stylus (≥100 ms, note 07)? → bench.
- Multi-touch (pinch/rotate) is **out of reach** for a single relative pointer — needs AssistiveTouch
 custom-gesture recording or Switch Control; track separately.
- Does enabling AssistiveTouch + max sensitivity violate the charter's "stock, untouched phone"
 premise? → `specs/00-charter.md` (ties to `hid-vs-gantry`).
