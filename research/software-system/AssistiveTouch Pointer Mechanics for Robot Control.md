---
tags: [iOS, accessibility, AssistiveTouch, pointer, mouse, HID, control, actuator, lock-screen, UIAccessibility]
status: answered
date: 2026-10-05
related:
  - "[[YOLO — Exposing Device Controls to Model]]"
  - "[[YOLO — Raspberry Pi Input Converter]]"
  - "[[iOS Control Constraints — Face ID, Autofill, Accessibility]]"
  - "[[YOLO — Synthetic Data and Flash Training App]]"
---

# 01 — AssistiveTouch pointer mechanics (iOS 13→26), in depth

## Question

Exactly how does stock iOS turn a connected USB/Bluetooth mouse into a usable
actuator for the iPhone-Ian agent — pointer behaviour, acceleration, clicking,
button→action mapping, custom multi-touch replay, reachable system gestures,
lock-screen/Face-ID behaviour, reboot persistence, and whether an app can tell?

Deepens `[[YOLO — Exposing Device Controls to Model]]` §8 (named the path) and
`[[YOLO — Raspberry Pi Input Converter]]` (relative-pointer constraint, HID
bridge). This note is the *mechanics reference* for the software-actuator branch.

## Key findings

### 1. Enablement — a one-time on-device toggle, and it persists

- iPhone has **no native pointer** (unlike iPad, which gained native trackpad/mouse +
  the adaptive morphing pointer in iPadOS 13.4). On iPhone a mouse works **only** through
  **AssistiveTouch**: Settings → Accessibility → Touch → **AssistiveTouch = On** (iOS 13+). `[Documented]`
- **Quick toggle:** set the **Accessibility Shortcut**, then **triple-click the Side button**
  (Face-ID) or Home button → flips AssistiveTouch on/off with no Settings dive. `[Documented]`
- **Pairing:** BT mouse via AssistiveTouch → **Devices → Bluetooth Devices**; wired via
  USB-C/Lightning (USB-A needs the Camera-Adapter, note 15). `[Documented]`
- **Persistence:** the toggle, Pointer Style, per-device button maps, Dwell/Hot-Corners
  and saved Custom Gestures are all Settings-backed → **survive reboot**. BT pairings
  survive too. ⚠ **BUT a cold-booted phone (Before-First-Unlock) blocks accessory
  connection until a human enters the passcode once** — "you need to first unlock… to
  connect to an accessory… after you unlock, your accessory remains connected even if
  locked again" (Apple 111806). So the robot config survives a reboot; the **input channel
  does not self-recover** without one human unlock (or the camera+pointer passcode path, §7). `[Documented]`

### 2. The pointer itself — a grey disc, and acceleration you can't kill

- Appearance: a **translucent grey circle** (NOT an arrow, NOT iPad's adaptive pointer —
  it does **not morph or magnetically snap** into buttons). Size/colour/**Auto-Hide delay**
  are set in **AssistiveTouch → Pointer Style** (iPhone) / **Pointer Control** (iPad).
  Idle → the disc **fades out**; it reappears on movement. `[Documented]`
- **Perception impact:** YOLO must detect a soft, size-configurable grey disc that fades
  when idle, plus the floating AssistiveTouch button (set **Idle Opacity** low / hide it
  so it doesn't occlude the ROI). Ties to `[[YOLO — Synthetic Data and Flash Training App]]`. `[Community]`
- **Tracking Speed:** one slider, **Settings → General → Trackpad & Mouse**. Scales overall
  gain only. `[Documented]`
- **Acceleration curve — the crux:** iOS applies a **non-linear acceleration (gain) curve**
  to every relative pointing device and gives **no setting (and no MDM key) to disable it
  or force a linear 1:1 map**. Users keep filing requests ("Please provide an option to
  disable mouse acceleration" — iPadOS 26 feedback, Sept 2025; same complaint 2021–23). `[Documented]`(absence)/`[Community]`
  - **Trackpad Inertia** (Pointer Control) *can* be turned off, but that is post-flick
    **momentum/coasting**, not the pointer-acceleration curve — turning it off does **not**
    linearise motion. `[Documented]`
  - **Consequence:** a fixed HID delta ≠ a fixed pixel distance. Max Tracking Speed only
    **flattens** the curve (DeviceHub's recipe) → absolute targeting still needs
    closed-loop **visual servo + corner-clamp dead-reckoning** (`[[YOLO — Raspberry Pi Input Converter]]`). `[Community]`

### 3. Clicking, dwell, drag, long-press, scroll

- **Click = tap:** a physical button-press down/up where the disc sits becomes a real touch
  down/up — a tap, or a hold if held. iOS synthesises genuine `UITouch` events (§8). `[Documented]`
- **Dwell Control** (Pointer Control / AssistiveTouch, iOS 14+): **auto-click by hovering**
  — no button needed. Tunables: **time-to-select**, **Movement Tolerance**, **Fallback
  Action**, and **Hot Corners** (dwell in a screen corner → a mapped action). When Dwell is
  on, the onscreen keyboard is forced visible. Lets a *button-less* positioner still click. `[Documented]`
- **Long-press:** hold the click (or dwell past the long-press threshold) → context menus,
  Home-screen "jiggle" mode. `[Documented]`
- **Drag:** **Drag Lock** — hold the key until the item lifts, move, click again to drop
  → dragging without holding the button down. `[Documented]`
- **Scroll:** the **wheel scrolls** the view under the disc; a trackpad uses **two-finger**
  scroll. iOS routes the wheel through its **Natural Scrolling** setting (content follows
  the wheel) — a vendor KB notes AssistiveTouch "uses Apple's 'Natural Scroll'… which
  reverses all scroll outputs"; the iPad trackpad has a toggle, iPhone effectively does not. `[Documented]`/`[Community]`
- **Mouse Keys:** a *keyboard* can even drive the disc (arrow keys; Option×5 toggles) with
  Initial-Delay / Max-Speed — a fallback if only a keyboard HID is present. `[Documented]`

### 4. Button → action mapping (the lever for the robot)

- **Per-device button maps:** AssistiveTouch → Devices → *[device]* → pick a **physical
  mouse button** → dropdown of actions. A 2–5-button mouse can fire distinct system actions
  **directly**, bypassing the floating menu entirely. `[Documented]`
- **Custom Actions on the floating button:** **Single-Tap, Double-Tap, Long Press, 3D Touch**
  (3D Touch only on supported models) each map to an action. `[Documented]`
- **Assignable action set (buttons & custom actions):** Open Menu, **Home, App Switcher
  (Multitask), Control Center, Notification Center, Siri, Spotlight**, Screenshot, Lock
  Screen, Mute, Volume ±, Reachability, Shake, **SOS**, Restart, Analytics, Accessibility
  Shortcut, Rotate, and **run a saved Custom Gesture**. → essentially the whole system-gesture
  set is reachable with **no edge-swipes and no physical buttons**. `[Documented]`

### 5. AssistiveTouch menu & reachable system gestures

- Floating button → tap → **customisable top-level menu** (grid of icons, user-arranged):
  Notification Center, Control Center, Home, Siri, **Device** (→ Lock Screen, Rotate,
  Volume, Mute, **More** → Screenshot, Multitask/App Switcher, Restart, Gestures, SOS,
  Analytics, Shake…), **Custom** (gestures), App Switcher. `[Documented]`
- **On-the-fly multi-finger gestures:** menu → Device → More → **Gestures** → pick **2–5
  digits** → that many circles appear → swipe/drag → iOS plays the **simultaneous
  multi-finger** gesture (pinch-zoom, rotate, multi-finger swipe). This is how a *single*
  pointer triggers true multitouch — the gap note 15 flagged for a plain mouse. `[Documented]`

### 6. Custom Gestures — recorded, repositionable multi-touch macros

- **Create New Gesture** (AssistiveTouch): record a touch path. **Hold still → recorded as
  a tap**; move → recorded as a **drag/swipe**. For multi-finger you **record each finger's
  movement separately and they group** into one gesture (Apple's own "two dots + half-circle"
  example). Play to preview, Save with a name; the Custom menu holds **Pinch, 3D Touch,
  Double-Tap + five custom slots**. `[Documented]`/`[Community]`
- **Replay = repositionable template:** invoking a saved gesture shows **blue circle(s)** at
  the start point(s); you **drag them onto the target, release → it plays** the recorded
  motion there. So a canned **pinch / rotate / multi-swipe** becomes a one-shot primitive the
  bridge can place anywhere — a powerful, stock-iOS multitouch replay channel. `[Documented]`/`[Community]`

### 7. Lock screen, passcode, Face ID

- AssistiveTouch and the pointer **work on the Lock Screen** — iOS offers **no option to
  restrict it to the unlock screen**, i.e. the disc is live there. The pointer can
  **click the passcode digits**; on Face-ID phones it can **click-drag up** to reveal the
  pad first. `[Community]`
- **Face ID is unchanged** by the pointer (hardware camera attention; note 07). For flows
  that demand the physical **double-click of the Side button** (Apple Pay / install confirm),
  **"Confirm with AssistiveTouch"** replaces it with an on-screen confirm — reachable by the
  pointer, which otherwise cannot press the side button. `[Documented]`
- ⚠ Reboot interplay: at **BFU** the passcode pad is up but **BT/USB accessories are blocked
  until the first unlock** (§1, Apple 111806) → the pointer can't *do* that first unlock
  from cold boot. After one unlock, locked-screen pointer control resumes. `[Documented]`

### 8. App observability — and the limit of it

- Apps can **query** `UIAccessibility.isAssistiveTouchRunning` (static `Bool`, UIKit, **iOS
  10.0+**) and **observe** `UIAccessibility.assistiveTouchStatusDidChangeNotification` →
  so an app **can tell AssistiveTouch is enabled** (and react). Reports exist of the flag
  reading `false` in some setups, so treat it as a hint, not a guarantee. `[Documented]`/`[Community]`
- **Key asymmetry:** that is the *only* signal. Because iOS feeds the pointer through the
  **real touch pipeline**, an app **cannot distinguish a mouse-driven tap from a finger**
  (no per-touch "synthetic" flag) — matches note 13 §8. A hostile anti-automation app could
  use `isAssistiveTouchRunning` as a weak tell, but not detect individual injected taps. `[Community]`

## Implications for iPhone-Ian

One-time toggle (no jailbreak/app) keeps the "stock" claim arguable; all config persists
except the cold-boot BFU unlock. **Button maps + Custom Gestures give a rich action space
for free** — mouse buttons → Home/App-Switcher/Control-Center/Notification-Center/Siri, plus
replayable recorded pinch/rotate (covers note 13 §2/§5, zero gantry calibration). **The one
hard problem is positioning:** acceleration can't be linearised, so the camera must
visually-servo the grey disc on every move (note 15) — that is the whole ballgame.

## Sources

- [Apple 111775 — pointer with AssistiveTouch](https://support.apple.com/en-gb/111775) (upd. 2026-06-12) — Pointer Style, Tracking Speed loc, Dwell, Drag Lock, Mouse Keys, button assignments `[Documented]`
- [Apple iph96b21954 — AssistiveTouch (iOS 26)](https://support.apple.com/en-in/guide/iphone/iph96b21954/26/ios/26) — Custom Actions, Create New Gesture, Idle Opacity, Confirm with AssistiveTouch, triple-click shortcut `[Documented]`
- [Apple HT202658/111794 — AssistiveTouch overview](https://support.apple.com/en-us/111794) — floating button, multi-finger gestures, Device→More menu `[Documented]`
- [Apple 111806 — allow accessories / first-unlock](https://support.apple.com/en-us/111806) — BFU accessory-connect gating, the reboot caveat `[Documented]`
- [AbilityNet — mouse/trackpad on iOS 26](https://mcmw.abilitynet.org.uk/how-to-make-it-easier-to-use-a-mouse-or-trackpad-with-your-iphone-or-ipad-in-ios-26) + [iOS 13 AssistiveTouch](https://mcmw.abilitynet.org.uk/assistivetouch-ios-13-iphone-ipad-and-ipod-touch) — Dwell/Fallback/Movement Tolerance/Hot Corners; Custom menu = Pinch/3D-Touch/Double-Tap + 5 slots `[Community]`
- [iphone.skydocu — AssistiveTouch](https://iphone.skydocu.com/en/accessibility/assistivetouch/) — Device→More→Gestures, choose 2–5 digits `[Community]`
- [Apple discussions — custom actions single/double/long](https://discussions.apple.com/thread/254328214) + [multi-finger record-and-group](https://discussions.apple.com/thread/254617156) `[Community]`
- [Apple discussions — iPadOS 26 can't disable mouse acceleration](https://discussions.apple.com/thread/256143470) (2025-09) + [only overall speed, no inertia](https://discussions.apple.com/thread/254543173) `[Community]`
- [Swiftpoint KB — scroll wheel uses Natural Scroll](https://support.swiftpoint.com/portal/en/kb/articles/ios-scroll-direction) `[Community]`
- [MS .NET mirror — UIAccessibility.IsAssistiveTouchRunning](https://learn.microsoft.com/en-us/dotnet/api/uikit.uiaccessibility.isassistivetouchrunning) + [assistiveTouchStatusDidChangeNotification](https://learn.microsoft.com/en-us/dotnet/api/uikit.uiview.assistivetouchstatusdidchangenotification) — Bool + notification, UIKit `[Documented]`
- [WWDC2020 "Build for the iPadOS pointer"](https://developer.apple.com/videos/play/wwdc2020/10093/) — the adaptive morphing pointer (contrast: iPhone's AssistiveTouch disc does NOT morph) `[Documented]`

## Open questions / follow-ups

- Can a saved **Custom Gesture** be triggered by a **mouse button** (replay a canned pinch
  with one click), or only via the floating menu? → decides how cheap multitouch is.
- Does **max Tracking Speed + corner-clamp** reach **passcode-pad pixel accuracy**, or is
  per-move visual-servo mandatory every time? (shared with note 15 → `questions.md`).
- Can a **cold-boot (BFU)** phone be driven by HID at all before a human first-unlock? If
  not, the robot **cannot self-recover a reboot** — flag as an operational constraint in `questions.md`.
- Exact iOS version each sub-feature landed (Dwell = iOS 14? Confirm-with-AssistiveTouch =
  iOS 15?) — verify only if the target build matters.
- Is the floating AssistiveTouch button fully hide-able while a pointer is active, so it
  never occludes the YOLO ROI? → ties to `[[YOLO — Synthetic Data and Flash Training App]]`.
- End-to-end latency of a pointer tap vs the gantry on current iOS — bench `[Benchmark]`.
