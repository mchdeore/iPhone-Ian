---
tags: [ios, accessibility, full-keyboard-access, switch-control, voice-control, back-tap, guided-access, hid, uiaccessibility, decision]
status: answered
date: 2026-10-05
related:
 - ""
---

# 04 — Alternative accessibility input paths & the actuator decision

## Question

Beyond pointer+AssistiveTouch (`` §8), which
*other* stock-iOS input surfaces could drive an unmodified iPhone — Full Keyboard Access,
Switch Control, Voice Control, Shortcuts/Back Tap, Guided Access — and, weighing reach /
reliability / setup / app-detectability / VoiceOver-conflict (note 07), what's the verdict:
**pure gantry vs AssistiveTouch+HID vs hybrid**? And is a Settings toggle a "modification"?

## Key findings

### 1. Full Keyboard Access (FKA) — a hardware keyboard drives the whole UI `[Documented]`

- `Settings > Accessibility > Keyboards > Full Keyboard Access`; needs a connected USB/BT
 keyboard — a Pi-HID keyboard (``) qualifies.
- **Tab / Shift-Tab** move a visible **focus ring** between elements; **arrows** move within
 a group; **Space/Return** activate. WWDC21: tab = significant areas, arrows = within area. `[Documented]`
- A **customizable Commands list** (Navigation / Interaction / Device categories) reaches
 Home Screen, App Switcher, Control/Notification Center, etc. → no pointer needed.
- **Navigate without vision?** *Partly.* Tab-order is deterministic, so a KNOWN screen can be
 traversed blind by counting tabs. But iOS exposes no focus position to the host (black box,
 charter §5) → for dynamic/unknown screens the camera must still read the focus ring. Net
 win: collapses the action space to ~4 keys and **removes coordinate grounding** for text/nav.
- **Not app-detectable** — no `UIAccessibility` flag exists for FKA (see §7).

### 2. Switch Control — scanning selection from one or more switches `[Documented]`

- `Settings > Accessibility > Switch Control`. Switch **sources: External (Bluetooth/MFi),
 Screen, Camera (head)**; Back Tap & Sound also selectable (iOS 14+).
- **External captures a raw HID keypress**: AAC switch interfaces present as BT keyboards
 emitting Space/Enter, so a **Pi-HID key registers as a switch** — the "external switch via
 HID keyboard" path. `[Community]`
- **Item scanning** (default): sequentially highlights items/groups → select → action menu.
 **Point scanning / Point Mode**: vertical-then-horizontal crosshairs land an **arbitrary
 coordinate with no element tree and no on-device vision** — exact but slow and timing-critical.
- Scanner **Device menu** mimics Home, App Switcher, Control/Notification Center, Siri,
 screenshot, volume, lock → reaches system functions a tap can't. **Recipes** temporarily bind
 a switch to one gesture (page-turn/tap) for repetitive tasks.
- **App-detectable**: `isSwitchControlRunning == true`. Reliability: point-scan brittle (timing);
 item-scan reliable but slow and order-dependent.

### 3. Voice Control — spoken commands + an on-screen number/grid overlay `[Documented]`

- `Settings > Accessibility > Voice Control`; on-device speech. "Show names" / **"Show numbers"**
 / **"Show grid"** overlay items; "Tap `<n>`", "Tap `<name>`", drag/swipe by cell. Grid rows ×
 cols adjustable ("Show grid with 5 rows"). iOS 26/27 adds natural-language element reference.
- **The overlay is the prize, not the audio.** The numbered/grid overlay is an on-screen
 **set-of-marks** our camera + YOLO can read directly → a *free grounding aid* that converts
 "where is the button" into "read the number," independent of whether we ever speak. `[Documented]`
- Driving *by audio* (speaker → mic) is **brittle**: latency, ambient noise, English parsing,
 no success signal. Treat as perception support, not a primary actuator.
- **Not app-detectable** — Apple exposes no Voice Control flag (dev-forum confirmed, §7).

### 4. AssistiveTouch pointer (recap of 13 §8, for the matrix) `[Documented]`

- A BT/USB mouse via Pi-HID acts as a finger; the overlay menu reaches Home/App Switcher/
 Control Center/Siri and **recorded multi-touch gestures** (true pinch). iOS synthesizes **real
 touch events** → event-level indistinguishable from a finger, **but** `isAssistiveTouchRunning`
 is queryable (setting state is detectable even though the events aren't).

### 5. Shortcuts app + Back Tap — narrow, not a general surface `[Documented]`

- **Shortcuts** runs only **app-exposed actions/intents**, never arbitrary UI (charter §4) → good
 for deterministic jumps (open app, set clipboard, run an automation) but **cannot fill arbitrary
 login fields**. Not a control channel for our agent.
- **Back Tap** (iOS 14+): double/triple-tap the **back glass** fires **one** assigned action —
 screenshot, Control Center, scroll, toggle an accessibility feature, or run a Shortcut. The
 gantry/finger could physically trigger it, but it's a single bound action, not a stream. Also
 usable as a Switch Control source and an Accessibility-Shortcut target.

### 6. Guided Access — containment, not input `[Documented]`

- Triple-click side button → **locks to one app**; circle screen regions to disable touch, turn
 **Touch off** entirely, disable hardware buttons, set a time limit. `isGuidedAccessEnabled` queryable.
- **Not an actuator** — it's a **safety rail**: pins the agent inside the target app and blocks
 accidental system gestures / app exits. Complements *any* actuator; recommend ON in all modes.

### 7. Detection surface — what an app can see `[Documented]`

- **Queryable** (`UIAccessibility`): `isVoiceOverRunning`, `isSwitchControlRunning`,
 `isAssistiveTouchRunning`, `isGuidedAccessEnabled` (+ boldText, reduceMotion, …).
- **NOT queryable**: **Voice Control** and **Full Keyboard Access** — no public API (Apple
 dev-forum thread 835302). These are the only truly invisible-by-API paths.
- **Practical risk ≈ 0**: consumer apps almost never branch on these flags (gating function on
 assistive state is an accessibility anti-pattern / App Review risk), and touch/pointer/HID
 events are indistinguishable from human at the `UIEvent` level. Detection is theoretical.

### 8. VoiceOver conflict (note 07) — the one hard incompatibility `[Documented]`

- VoiceOver **inverts touch semantics** (single-tap = speak, double-tap = activate, swipe =
 navigate) → **fatal to a glass-tapping gantry**. VoiceOver must be **OFF** for the gantry.
- All HID paths (pointer / keyboard / switch) and Voice Control **coexist** with each other and
 with physical tapping; **none coexist with VoiceOver's gesture model**.
- Mitigation (per 07): set the triple-click Accessibility Shortcut to a single harmless feature or
 disable it, so a stray triple-click (gantry near the button, or Back Tap) can't flip VO on.

### 9. Is a Settings toggle a "modification"? (charter premise)

- Charter D2: *no jailbreak, no MDM, no dev provisioning, nothing installed, "black box"*; §4:
 must be *"arbitrary, zero-install, on any phone I set it in front of."*
- A toggle **installs nothing, no jailbreak, fully reversible, stock iOS only** → satisfies the
 **letter** of D2 (software black-box). But it **pre-configures that specific phone** → breaks the
 **spirit** of "any untouched phone I set it in front of."
- **Verdict:** a toggle is *configuration, not modification* — fine for a phone **you own and
 provision once**; **disqualifying** for the hero demo of black-box control of an *arbitrary*
 phone. The gantry on an untouched phone is the only path that satisfies §4 literally.

### 10. Decision matrix & recommendation

| Path | Reaches | Reliability | Setup cost | App-detectable | VoiceOver |
|---|---|---|---|---|---|
| **Pure gantry** (tap glass) | all a finger can | High (post-calib) | **High** (build + `H_screen→gantry`) | No (real touch) | must be OFF |
| **AssistiveTouch + mouse (HID)** | all + menu/pinch | High | **Low** (toggle + Pi) | yes (`…AssistiveTouchRunning`) | coexists |
| **Full Keyboard Access (HID kbd)** | whole UI via focus ring + Commands | Med-High (dynamic weaker) | Low (toggle + Pi) | **No API** | coexists |
| **Switch Control (HID key)** | all (point=any coord; item=elems; Device menu) | Low (point) / Med (item) | Med (toggle + switches/recipes) | yes (`…SwitchControlRunning`) | coexists |
| **Voice Control (audio+grid)** | all named/numbered/grid | Low (audio brittle) | Med (toggle + spkr/mic) | **No API** (overlay only) | coexists |
| **Shortcuts + Back Tap** | app-exposed actions only / 1 bound tap | Low coverage | Low | partial | n/a |
| **Guided Access** | — (containment) | n/a | Low | yes (`…GuidedAccessEnabled`) | complementary |

**Recommendation (`ponytail:` build the hero, but bring up on the cheap one) — HYBRID behind the
single MCP action API (`` §2/§5):**

1. **Gantry = the deliverable / hero path.** D2/D3 already commit to the 3D-printed build; it is
  the only actuator that honors §4's *untouched arbitrary phone* premise. Ship it.
2. **Pi-HID + AssistiveTouch pointer = primary bring-up backend.** ~10× less effort and **deletes
  `H_screen→gantry` calibration** (screen coords → pointer directly), so perception + agent +
  credential loop mature while the gantry is printed/tuned. Also the fallback for owned phones.
3. **Full Keyboard Access = optional deterministic layer.** Collapses typing + focus traversal to
  key events (fast, API-invisible) — ideal for passcode/credential entry.
4. **Voice Control grid = perception aid only.** Optionally flash "Show grid" for a free numbered
  set-of-marks during grounding eval; do **not** rely on audio control.
5. **Switch Control / Shortcuts+Back Tap = not primary** (slow / app-limited). Keep Switch Control
  Point Mode in back pocket as a vision-free coordinate channel if ever needed.
6. **Guided Access = ON in every mode** as a safety rail. Keep **VoiceOver OFF** and neutralize the
  Accessibility Shortcut on all paths.

Net: validate the entire stack on HID first; the gantry remains the demonstrable black-box answer.

## Sources

- [Control iPhone with an external keyboard (FKA)](https://support.apple.com/en-am/guide/iphone/ipha4375873f/ios) · [WWDC21 Focus on iPad keyboard navigation](https://developer.apple.com/videos/play/wwdc2021/10260/) — Tab/arrow/Return focus-ring model, Commands list `[Documented]`
- [Use Switch Control (AU)](https://support.apple.com/en-au/119835) · [Switch Control on iPhone (iOS 26)](https://support.apple.com/en-me/guide/iphone/iph8de250c54/26/ios/26) — sources (External/Screen/Camera), item vs point mode, Device menu, recipes `[Documented]`
- [Use Voice Control to interact with iPhone](https://support.apple.com/guide/iphone/iph2c21a3c88/ios) · [a11ysupport Voice Control (iOS)](https://a11ysupport.io/learn/at/vc_ios) — Show numbers/names/grid overlay, "Tap n", grid rows/cols `[Documented]`/`[Community]`
- [Run shortcuts via Back Tap](https://support.apple.com/en-nz/guide/shortcuts/apd897693606/ios) · [Use Back Tap on your iPhone](https://support.apple.com/en-gw/HT211781) — double/triple-tap → one action/shortcut, iOS 14+ `[Documented]`
- [Use Guided Access on iPhone or iPad](https://support.apple.com/en-nz/111795) — single-app lock, disable touch regions, turn Touch off, time limit `[Documented]`
- [Apple dev forum 835302: no Voice Control API](https://developer.apple.com/forums/thread/835302) · [UIAccessibility class](https://docs.microsoft.com/en-us/dotnet/api/uikit.uiaccessibility) — `isVoiceOverRunning`/`isSwitchControlRunning`/`isAssistiveTouchRunning` exist; VC & FKA have none `[Documented]`

## Open questions / follow-ups

- Resolves `hid-vs-gantry` (questions.md): recommend **hybrid** — gantry hero + HID bring-up. Confirm with owner.
- Does the External Switch Control source accept an arbitrary Pi-HID keycode, or only specific keys? Needs a bench test (ties to ``).
- Is flashing Voice Control's numbered grid as a grounding aid worth the audio stack, or does our own YOLO set-of-marks already cover it? → ``.
- Can FKA focus-ring be read reliably by the camera across apps (contrast/visibility), enabling near-vision-free navigation?
- Does enabling AssistiveTouch/Switch Control (detectable flags) risk tripping any anti-automation checks in target banking/social apps? → ties to `human-typing-speed`.
