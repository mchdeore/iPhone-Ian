---
tags: [control, agent, GRBL, iOS, action-space, MCP, accessibility, AssistiveTouch, homography]
status: answered
date: 2026-10-05
related:
  - "[[== ML CENTRAL ==]]"
---

# 13 — Exposing device controls to the model/agent

## Question

How do we expose the iPhone's controls to the agent as a clean action space, map those
actions through screen → camera → gantry → GRBL, wrap them as tool/function calls
safely, and — crucially — can stock-iOS accessibility (mouse pointer, hardware keyboard,
Switch/Voice Control) drive the phone *without the gantry at all*?

Builds on the agent loop (``), VLM action-space
survey (``), iOS constraints (``),
GRBL mechanics (``), firmware contract (`specs/02` §4–§8).

## Key findings

### 1. The field has converged on a tiny action vocabulary

| Agent | Coordinate style | Primitives | Source |
|---|---|---|---|
| **UI-TARS** mobile | raw pixels `point='x y'` | `click`, `long_press`, `type`, `scroll`, `drag`, `open_app`, `press_home`, `press_back`, `finished` | `[Documented]` prompt.py |
| **UI-TARS** desktop | raw pixels | adds `left_double`, `right_single`, `hotkey`, **`wait()`** | `[Documented]` |
| **AppAgent** | **element index** (set-of-marks numbers overlaid) | `Tap`, `Long_Press`, `Swipe(elem,dir,dist)`, `Text` | `[Documented]` 2312.13771 §3.1 |
| **OS-Atlas / UGround** | normalized grounding → pixel | grounding emits the point; action layer is thin | `[Benchmark]` (see ``) |
| **Anthropic / OpenAI computer-use** | pixels | `screenshot`, `click`, `type`, `key`, `scroll`, `wait` + "hybrid GUI+API" | `[Community]` emergentmind |

Takeaway: **6–9 primitives cover every GUI agent.** AppAgent's element-index style
needs an accessibility tree we don't have → we use **pixel/point actions** like UI-TARS,
whose `wait()` *is* the did-screen-change check (§6).

### 2. Proposed action API (backend-agnostic — this is the deliverable)

Observation = camera frame rectified to a flat **screen image** via the fiducial
homography (``). **Every coordinate the agent emits
is a SCREEN coordinate (CSS px or normalized 0–1);** the backend hides camera pixels
and gantry mm — the model never sees them.

```
tap(x, y)           # down → dwell ≥100 ms → up (iOS touch latency 40–75 ms, note 07)
long_press(x, y, ms=600)    # context menus, app wiggle
swipe(x1,y1, x2,y2, ms=300)  # single contact; also expresses scroll + edge gestures
type(text)           # per-key taps on iOS keyboard (software path: HID keystrokes)
press_home()          # Face-ID models have NO home button → swipe-up from bottom edge
press_back()          # tap top-left chevron OR left-edge swipe-in (app-dependent)
wait(ms=1000)         # dwell, then re-observe
done(summary) / fail(reason)  # terminal
```

iPhone system gestures expand to single-point edge swipes (safe; multi-touch is
not — note 07): Home = swipe-up, App Switcher = swipe-up-and-hold, Control Center =
swipe-down-top-right, Back = left-edge swipe-in. No `hotkey`/`open_app` on the gantry
(no keyboard, no launcher API); `open_app` = `press_home()` + `tap(icon)`.

### 3. Coordinate pipeline — two independent homographies

```
PERCEPTION: camera px --H_cam→screen (fiducials, per-frame)--> screen px --> VLM
ACTION:   VLM tap(sx,sy) --H_screen→gantry (session, calibrated)--> (X,Y) mm --> GRBL
```

- `H_cam→screen` is re-solved **every frame** from the 4 flash-app fiducials — a
 drifting mount silently corrupts it (``). DPR cancels in CSS px.
- `H_screen→gantry` is fit by **closed-loop calibration**, not vision: flash a target
 at known screen px → command gantry XY → measure the landed tap via `touchstart` →
 solve affine/homography (`specs/02` §5.1). Converges in dozens of samples; the only
 transform the actuator uses. `[Documented]`

### 4. GRBL motion backend over serial `[Documented]`

- **pyserial** 115200 8-N-1; stream a line, wait for `ok` (buffer-aware streamer,
 `specs/02` §4). States via real-time `?` → `<Idle|MPos:0.000,0.000,0.000|FS:0,0>`
 (poll **≤5 Hz**); states: Idle/Run/Jog/Hold/Alarm/Home/Door.
- **Move:** `G90 G0 X.. Y..` (rapid) **or** prefer `$J=X.. Y.. F..` **jog** — cancellable
 (`0x85`), purges the queue, and with soft-limits on **errors instead of alarming** on
 out-of-range → ideal for agent moves. `F` is mm/min (G94); jog never changes modal state.
- **Tap (servo-Z):** laser mode `$32=1`; `M3 S<down>` → `G4 P0.12` dwell → `M5`/`S0`
 up (``).
- **Homing:** `$H` (needs limit switches, `$22=1`); set phone-corner origin with `G10 L20`.

### 5. Tool-calling / MCP exposure

Two ways to let the model act, both over the SAME API §2:
- **(a) Text DSL** emitted by a native GUI model and parsed host-side (UI-TARS:
 `click(point='x y')`). Zero schema overhead; best with a fine-tuned model.
- **(b) MCP tools** with JSON-schema args (`tap`,`swipe`,`type`,`screenshot`,`wait`) —
 many mobile-automation MCP servers already expose this exact set (`mobile-next/mobile-mcp`, `open-mobile-mcp`). `[Community]`

MCP is the better fit: identical tool signatures over a **swappable backend** —
GRBL-gantry **or** Pi-HID (§7) **or** a simulator — and a `screenshot` tool that
returns the rectified frame. Per MCP best-practice, annotate each tool
(`readOnlyHint:false`, `destructiveHint` per-action, `idempotentHint:false`,
`openWorldHint:true`). Keep high-level intents (`login`,`open`, `specs/02` §8) as
*separate* tools layered on the primitives = the "hybrid GUI+API" pattern. `[Community]`

### 6. Safety

- **Workspace limits** = the phone's bounding box → GRBL soft limits (`$20=1`) **and**
 host-side rejection of off-screen `(x,y)` (flash-app scores "missed the phone" ≪ 0, §5.1).
- **E-stop:** real-time soft-reset `Ctrl-X` (`0x18`) + hardware button; feed hold `!`,
 resume `~`, jog-cancel `0x85`.
- **Rate limiting:** host min interval between actions (≥ tap dwell + settle), `?` poll
 ≤5 Hz; never fire a move before `Idle`.
- **Confirm-before-destructive:** agent gates irreversible UI (send/delete/pay/logout/
 erase) behind a confirmation step (`destructiveHint:true`); secrets typed only from
 the vault at point of use, never logged (`specs/02` §9).

### 7. Feedback / verification

- After **every** action: capture the next frame → **did-screen-change** (frame diff /
 perceptual hash over the screen ROI) → if the expected change is absent, retry
 (re-perceive, nudge offset) then escalate/abort (loop in `specs/02` §7, note 05).
- UI-TARS formalizes this: `wait()` = "sleep 5 s, screenshot, check for changes." `[Documented]`
- Calibration-time verification = the flash-app **tap score** (1 − error/radius).

### 8. Software-side alternative — drive a STOCK iPhone with NO gantry

This re-opens what `` dismissed *for a tapping
robot*: used as the **actuator itself**, stock-iOS accessibility is powerful.

- **Pointer + AssistiveTouch** (iOS 13+): a plain **USB or Bluetooth mouse acts as a
 finger** — clicks tap what you'd tap; the AssistiveTouch menu reaches Home, App
 Switcher, Control Center, Siri, and **recorded custom gestures** (incl. multi-touch).
 `[Documented]` Apple 111775 / iph96b21954.
- **Full Keyboard Access** (hardware keyboard, iOS 13.4+): Tab/arrows move a focus
 ring, Space/Return activate; whole UI drivable from keys, no pointer. `[Documented]` ipha4375873f.
- **Switch Control → Point Mode:** a scanning crosshair (stop X, then Y) hits
 **arbitrary coordinates with no vision and no menu** — exact but slow; USB/BLE switches. `[Documented]`
- **Voice Control:** numbered / named / grid overlay ("Tap 23"), "Swipe down", "Long
 press <app>", custom commands, + iOS 27 Apple-Intelligence natural-language element
 reference; drivable by synthesized speech but brittle/slow. `[Documented]`
- **The bridge** (how a computer presents as HID): a **Raspberry Pi Zero / Zero 2 W in
 Linux USB-gadget mode** emulates a composite keyboard+mouse (or BLE-HID), connected
 over USB-C/Lightning (powered adapter) or Bluetooth → ``.
 Many turnkey repos exist (`bluetooth_2_usb`, `zero_hid`, `keybird`). `[Community]`

**Limits / honest caveats:**
1. HID replaces only the **actuator** — perception still needs the camera (or AirPlay/HDMI capture).
2. Requires a one-time **on-device Settings toggle** (accessibility). Arguably still
  "stock/unmodified" (no jailbreak, no app install) but **not an untouched phone**.
3. Plain mouse = single pointer; true pinch needs AssistiveTouch/Switch gestures.
4. Face ID / passcode behavior unchanged (note 07) — keyboard can type the passcode.
5. iOS synthesizes **real touch events** from the pointer, so apps can't tell it from a finger.

**Verdict (`ponytail:` the cheapest actuator has no moving parts):** if the phone can
be configured once, **Pi-HID + AssistiveTouch/Full-Keyboard-Access is ~10× less build
effort than the gantry and deletes the entire `H_screen→gantry` calibration** (screen
coords go straight to the pointer). The gantry stays justified only for a *truly
untouched* phone or to demonstrate black-box physical interaction (the charter's
premise). Expose **both** behind the one MCP action API (§2/§5); default to HID when
accessibility can be enabled.

## Sources

- [UI-TARS prompt.py](https://github.com/bytedance/UI-TARS/blob/main/codes/ui_tars/prompt.py) + [paper](https://arxiv.org/html/2501.12326) — exact mobile/desktop pixel action space incl. `wait()` as screen-change check `[Documented]`
- [AppAgent 2312.13771 §3.1](https://arxiv.org/html/2312.13771v1) — element-indexed Tap/Long_Press/Swipe/Text (set-of-marks); [Hybrid GUI+API](https://www.emergentmind.com/topics/hybrid-gui-api-action-space) — pixel primitives + high-level tools `[Documented]`/`[Community]`
- [GRBL jogging](https://github.com/gnea/grbl/blob/master/doc/markdown/jogging.md) + [commands](https://github.com/gnea/grbl/blob/master/doc/markdown/commands.md) / [real-time cmds](https://support.easel.com/hc/en-us/articles/40531445916691-Grbl-v1-1-Real-Time-Commands) — `$J`, cancel `0x85`, soft-limit-error-not-alarm, `?`/`!`/`~`/`0x18`, 5 Hz `[Documented]`
- [mobile-mcp](https://github.com/mobile-next/mobile-mcp) · [open-mobile-mcp](https://github.com/xzaleksey/open-mobile-mcp) — MCP tools: screenshot/tap/swipe/type `[Community]`
- Apple: [pointer+AssistiveTouch](https://support.apple.com/en-us/HT210546) · [AssistiveTouch](https://support.apple.com/guide/iphone/iph96b21954/ios) · [Full Keyboard Access](https://support.apple.com/en-om/guide/iphone/ipha4375873f/ios) · [Voice Control](https://support.apple.com/en-ca/guide/iphone/iph2c21a3c88/ios) + [commands](https://gist.github.com/willwade/807cd631bc494039ed58b5f8304e8883) — mouse-as-finger, keyboard/voice UI control `[Documented]`
- [bluetooth_2_usb](https://github.com/quaxalber/bluetooth_2_usb) · [zero_hid example](https://github.com/miaGauci/Transforming-My-Raspberry-Pi-into-a-Dynamic-Keyboard-and-Mouse-Emulator) — Pi USB-HID gadget bridge `[Community]`

## Open questions / follow-ups

- Does enabling AssistiveTouch / Full Keyboard Access break the charter's "stock, unmodified" premise? → `specs/00-charter.md`.
- USB-C vs Lightning power/OTG needs for the Pi-HID bridge (ties to open `iphone-model-target`).
- Is Switch Control Point Mode fast enough to be practical, or demo-only?
- Software path still needs the camera for perception — is AirPlay/HDMI capture acceptable, or camera-only?
- Which UI actions count as "destructive," and how does the agent recognize them *before* tapping (ties to `retry-error-recovery`)?
