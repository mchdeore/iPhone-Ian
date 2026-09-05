# Controlling a Modern Android Phone from a Computer: A Technical Survey

*Research scope: Android 12–16, covering software/USB control mechanisms, observability/detectability characteristics, and physical touchscreen-actuator hardware. Compiled September 2026.*

**Citation key:** [Verified/documented] = official docs or source code · [Developer/researcher report] = blog/GitHub issue by someone who built it · [Anecdotal] = forum/Reddit report · [Inference] = author's own reasoning, explicitly labeled as such.

---

## Table of Contents

1. [Part 1 — Software/USB Control Mechanisms](#part-1)
2. [Part 2 — Observability & Detectability (Defensive)](#part-2)
3. [Part 3 — Physical Touchscreen Actuator Hardware](#part-3)
4. [Part 4 — Comparison Table & Rankings](#part-4)
5. [Sources](#sources)

---

<a id="part-1"></a>
## Part 1 — Software/USB Control Mechanisms

### 1.1 Background: how Android dispatches input, and why Android 13 changed things

All Android touch/key events ultimately pass through the system `InputDispatcher` in `frameworks/native`, which routes `MotionEvent`/`KeyEvent` objects to the window currently eligible to receive them. Any process that wants to *inject* rather than *originate* an event must hold the `android.permission.INJECT_EVENTS` signature-level permission — normally granted only to the `system` and `shell` UIDs [Verified/documented] ([source.android.com input docs](https://source.android.com/docs/core/interaction/input/getevent); [CircleCI/Robotium injection permission thread](https://discuss.circleci.com/t/injecting-to-another-application-requires-inject-events-permission/19970)). This is why `adb shell input …` works out of the box (it runs as the `shell` UID, which is pre-granted `INJECT_EVENTS`), while a third-party app calling `InputManager.injectInputEvent()` via reflection is rejected with a `SecurityException` unless it has been elevated (root, signature permission, or shell UID via `adb shell run-as`/instrumentation).

**Android 13 tightened UID-target validation**, not the `INJECT_EVENTS` permission itself. A well-documented example is [Genymobile/scrcpy issue #3186](https://github.com/Genymobile/scrcpy/issues/3186) [Developer/researcher report]: on the Android 13 preview, scrcpy's SDK-level input injection began failing with `InputDispatcher` logging `"Injected event targeted at uid 0 would be dispatched to window ... owned by uid <other>"`. In other words, Android 13 added a check that an injected event's *claimed source UID* must match the UID that actually owns the destination window, closing a spoofing vector that previously let a `uid 0` (root/shell)-origin injected event silently reach arbitrary app windows. This did **not** remove `adb shell input`'s ability to control the foreground app — `adb`/`shell`-origin taps continue to work on stock Android 13–16 devices as of this writing — but it broke some non-standard injection paths (e.g., apps trying to inject into a specific window they don't legitimately own) and pushed several remote-control tools (scrcpy included) toward alternative mechanisms (UHID, AOA) that don't rely on framework-level event injection at all [Developer/researcher report].

Separately, **Android 15 introduced "Restricted Settings"** for sideloaded (non-Play-Store-installed, unverified) APKs: such an app cannot have its Accessibility Service or Device Admin toggled on directly from Settings — the toggle is greyed out until the user manually visits *App info → More (⋮) → Allow restricted settings* [Verified/documented] ([Google Support: Learn about restricted settings](https://support.google.com/android/answer/12623953?hl=en); [Android Authority coverage](https://www.androidauthority.com/android-15-restricted-settings-sideloading-3481098/); [9to5Google](https://9to5google.com/2024/09/12/android-15-sideloaded-apps-restrictions/)). This affects any accessibility-service-based control tool (see §1.4) when the controlling app is sideloaded rather than installed via `adb install` in a Developer-Options-unlocked state or via a store — the extra tap is a **usability friction**, not a hard technical block, and does not apply to apps installed via `adb install` with `INSTALL_REASON` normal in most testing configurations [Developer/researcher report variance noted in threads].

### 1.2 ADB (`adb shell input`)

**Mechanism:** The `adb shell input <command>` CLI (backed by `com.android.commands.input.Input`, part of AOSP `frameworks/base/cmds/input`) calls into `InputManager`/`WindowManager` as the `shell` UID to inject `MotionEvent`/`KeyEvent` objects. Sub-commands include `tap x y`, `swipe x1 y1 x2 y2 [duration]`, `text <string>`, `keyevent <code>`, `press`, `roll`, `draganddrop` (device-dependent) [Verified/documented] ([Zebra Developer Portal ADB intro](https://developer.zebra.com/community/home/blog/2015/03/09/introduction-to-adb-shell-commands); [Gesture Testing ADB notes](https://www.shariqsp.com/mobileTesting/Gesture.html)).

- **Taps/swipes/long-press:** Yes — `tap`, `swipe` (a long swipe duration approximates long-press; some builds also expose `input swipe x y x y 1000+`ms for press-and-hold).
- **Typing:** `input text "…"` injects a text string (limited to characters representable in the current IME's `KeyEvent` mapping; no native Unicode/emoji support without a helper IME).
- **Multi-touch:** **Not supported** — `input tap`/`swipe` are strictly single-pointer. There is no `input pinch` or `input multi-tap` in stock AOSP [Developer/researcher report] ([multi-touch gesture research doc](https://glama.ai/mcp/servers/@AlexGladkov/claude-in-mobile/blob/c99a81727a745eb84df3fc4f22374faff15174b4/docs/multi-touch-research.md)). Pinch/zoom, two-finger rotate, and other multi-finger gestures require a different mechanism (§1.9, or UIAutomator2/Appium wrappers that synthesize them via lower-level APIs).
- **Arbitrary-app interaction:** Yes, coordinate-based taps land on whatever is frontmost; no app-specific integration needed.
- **USB requirement:** Not strictly required — ADB works over Wi-Fi (`adb tcpip`/`adb pair`) after the initial USB or wireless-debugging pairing.
- **Developer Options / USB debugging:** **Required.** The device must have Developer Options → USB debugging enabled, and the host computer's RSA key must be authorized via the on-device fingerprint dialog the first time it connects [Verified/documented] ([Nikolay Elenkov: Secure USB debugging in Android 4.2.2](https://nelenkov.blogspot.com/2013/02/secure-usb-debugging-in-android-422.html); [getandora ADB unauthorized guide](https://getandora.in/blog/adb-unauthorized)).
- **Root:** Not required for `input tap`/`swipe`/`text`/`keyevent` — these run fine as `shell` UID.
- **Accessibility permission:** Not required.
- **Android 12–16 support:** Works on all of them for the basic `input` subcommands; see §1.1 for the Android 13 UID-targeting nuance (does not affect normal `shell`-UID usage).
- **Coordinate precision:** Pixel-exact, using the device's actual display coordinate space (post-density-scaling); as precise as the framework's own event pipeline.
- **Reliability for continuous/long-running use:** Each `adb shell input …` invocation spawns a new shell process, so there's non-trivial per-call latency (measured around **300–400 ms per invocation** in one developer's benchmark versus raw `/dev/input` `sendevent` injection) [Developer/researcher report] ([xarantolus: How to tap the Android screen from the underlying Linux system](https://blog.010.one/how-to-tap-the-android-screen-from-the-underlying-linux-system)). Fine for scripted test sequences; not ideal for frame-accurate, low-latency continuous control (e.g., games) without batching or switching to `sendevent`/UIAutomator2.
- **Screen visibility to computer:** No — `adb shell input` is control-only. Screen visibility requires a separate mechanism (`adb exec-out screencap`, `scrcpy` for streaming, etc.).
- **Works while locked:** Taps/swipes are dispatched into whatever `Window` currently has focus, including the keyguard — so `adb shell input swipe` **can** perform the "swipe up to unlock" gesture and `adb shell input text`/`keyevent` can enter a PIN, **if** ADB is already authorized (which itself normally requires the device to have been unlocked once to accept the authorization dialog, and on many OEM skins, USB debugging authorization can be revoked while locked) [Anecdotal/Developer report] ([XDA: CLI lock screen settings](https://xdaforums.com/t/guide-how-to-get-or-set-the-lock-screen-settings-via-cli-command.4647038/); [Repeato: lock/unlock via ADB](https://www.repeato.app/how-to-lock-and-unlock-the-android-screen-via-adb/); [scrcpy issue #733 on unlock scripting](https://github.com/Genymobile/scrcpy/issues/733)).

### 1.3 Android `InputManager` / `injectInputEvent` (direct API)

**Mechanism:** `android.hardware.input.InputManager` exposes a (partly hidden/restricted) `injectInputEvent(InputEvent, int mode)` method. It is the same underlying call `adb shell input` uses internally. Direct use from a third-party app requires either the `INJECT_EVENTS` **signature** permission (unattainable by ordinary apps without root/system privilege) or invoking it through reflection while running with `shell`/`system` UID privileges (e.g., via `adb shell app_process`, an instrumentation context, or root) [Verified/documented — AOSP `InputManager` source]; [Developer/researcher report] ([android-inputinjector library](https://github.com/arnebp/android-inputinjector); [Genymobile scrcpy #4785 discussion](https://github.com/Genymobile/scrcpy/issues/4785)).

- **Requirements:** Root, or a shell-elevated process (adb-launched), or a system-signed app. Not usable by a normal installed app without one of those.
- **Capabilities:** Full parity with whatever `MotionEvent`/`KeyEvent` construction the caller performs — arbitrary multi-pointer `MotionEvent`s (including proper `PointerProperties`/`PointerCoords` arrays for real multi-touch, pressure, tool type, etc.) are possible here, unlike the `input` CLI, because the caller builds the raw event object.
- **Android 13+ nuance:** Subject to the UID-target-window check described in §1.1 — an injected event whose reported UID doesn't own the destination window can be silently dropped by `InputDispatcher` on some configurations [Developer/researcher report].
- **Reliability:** In-process calls (no per-call process spawn) make this far faster than shelling out to `adb shell input` repeatedly — this is the basis of tools like minitouch/UIAutomator2 servers that stay resident on-device (§1.7).

### 1.4 Android Accessibility Services (`dispatchGesture`)

**Mechanism:** An `AccessibilityService` with `canPerformGestures="true"` (via its `accessibilityfeedbacktype`/`accessibility-service` XML config) can call `dispatchGesture(GestureDescription, callback, handler)`. A `GestureDescription` is built from one or more `GestureDescription.StrokeDescription` objects, each defined by a `Path`, start time, and duration — enabling taps, long-presses, swipes, and (since API 26) **multi-stroke concurrent gestures**, i.e., real multi-touch (pinch, two-finger scroll) by supplying multiple simultaneous `StrokeDescription`s [Verified/documented] ([Android Developers: Create an accessibility service](https://developer.android.com/guide/topics/ui/accessibility/service); [Microsoft Learn: AccessibilityService.DispatchGesture](https://learn.microsoft.com/en-us/dotnet/api/android.accessibilityservices.accessibilityservice.dispatchgesture?view=net-android-35.0)).

- **Taps/swipes/long-press:** Yes, natively.
- **Multi-touch:** Yes — multiple concurrent `StrokeDescription`s in one `GestureDescription`, a genuine advantage over `adb shell input`.
- **Typing:** Indirectly — an accessibility service can use `performAction(ACTION_SET_TEXT)` on an editable `AccessibilityNodeInfo` (more reliable than simulating individual keystrokes) or dispatch gesture-based taps onto an on-screen keyboard.
- **Arbitrary-app interaction:** Yes, this is the mechanism's core design purpose (and the same one abused by banking trojans — see Part 2).
- **USB requirement:** None — the service runs entirely on-device, once installed by any means (sideload, Play Store, ADB install).
- **Developer Options / USB debugging:** Not required for operation (only potentially for *installing* the APK via `adb install`, though sideloading via a file manager works too).
- **Root:** Not required.
- **Accessibility permission:** **Required** — the user must manually enable the service in Settings → Accessibility, a conspicuous, user-visible toggle (see Part 2 for observability). On Android 15+, if the hosting APK is sideloaded, the "Restricted Settings" gate (§1.1) requires an extra explicit unlock step before the toggle is even available [Verified/documented].
- **Android 12–16 support:** Fully supported; `dispatchGesture` has existed since API 24 (Android 7.0) and multi-stroke since API 26. There is an open Google Issue Tracker feature request ([issue #350653948](https://issuetracker.google.com/issues/350653948)) asking for *more* flexibility in `dispatchGesture` (e.g., continuous/streaming gesture updates rather than fixed pre-planned paths), indicating known limitations around highly dynamic/continuous interaction [Developer/researcher report].
- **Coordinate precision:** Pixel-precise (`Path` uses float coordinates in screen pixels).
- **Continuous/long-running reliability:** Reasonably good for discrete gesture sequences; less suited to frame-by-frame continuous control since each `GestureDescription` is a pre-planned, fire-and-forget stroke with a fixed duration rather than a live streamable pointer — some apps report gestures dispatched this way are not always recognized by target apps that do custom touch handling (e.g. certain games/canvases) [Anecdotal] ([XDA: "some apps didn't respond to dispatchGesture"](https://xdaforums.com/t/some-apps-didnt-response-dispatchgesture-sent-by-android-accessibilityservice.4608747/)).
- **Screen visibility to computer:** Not inherently — the accessibility service sees the **accessibility node tree** (UI hierarchy/text/content descriptions), not pixels, unless separately combined with `MediaProjection`/screenshot APIs.
- **Works while locked:** Generally **no** for `dispatchGesture` targeting apps — gestures dispatched by an accessibility service are subject to the same window-focus rules as other injected input, and most accessibility services are not permitted to interact with content behind the secure lockscreen (`FLAG_SECURE` / keyguard windows are protected) [Inference based on documented AccessibilityService window-visibility restrictions].

### 1.5 UIAutomator / UIAutomator2

**Mechanism:** Google's `androidx.test.uiautomator` library, built on top of the accessibility API and instrumentation, lets on-device (or host-driven, via `openatx/uiautomator2`) test code query the UI hierarchy across app boundaries and perform gestures (click, swipe, drag, pinch) using coordinate or `UiObject`/`UiObject2` selectors [Verified/documented] ([Android Developers: UI Automator](https://developer.android.com/training/testing/other-components/ui-automator)).

- Cross-app capability is a defining feature: UIAutomator can test system UI (notification shade, home screen, other apps' windows) because it's not confined to a single app's Instrumentation context, unlike Espresso.
- **openatx/uiautomator2** wraps this in an always-resident HTTP server APK on-device, communicating with a Python client over HTTP, avoiding the per-call `adb shell` spawn overhead and enabling richer gestures (double-tap, pinch in/out, multi-point swipe sequences, drag) [Developer/researcher report] ([openatx/uiautomator2 README](https://github.com/openatx/uiautomator2)).
- **Requirements:** ADB + Developer Options/USB debugging to install/launch the automation server initially; **root not required**; Android 4.4+ supported by the library.
- **Multi-touch:** Yes, via `UiDevice`/gesture APIs exposing pinch and multi-point paths.
- **Reliability:** Because the server is resident, this is markedly more efficient for continuous/scripted long-running use than shelling `adb shell input` repeatedly.
- **Locked-screen / screen visibility:** Same general constraints as Accessibility (§1.4) since it's built on the same substrate — not a screen-mirroring solution by itself.

### 1.6 Appium (UiAutomator2 / Espresso drivers)

**Mechanism:** Appium is a cross-platform test-automation server; for Android it drives either the **UiAutomator2 driver** (installs `appium-uiautomator2-server` APK, which is itself an Instrumentation-based service wrapping UIAutomator + accessibility) or the **Espresso driver** (drives Espresso's `Instrumentation`-based synchronous UI actions, but confined to a single target app under test) [Verified/documented] ([appium-uiautomator2-driver README](https://github.com/appium/appium-uiautomator2-driver); [Appium docs: UiAutomator2 driver](https://appium.io/docs/en/2.1/quickstart/uiauto2-driver/)).

- **Taps/swipes/multi-touch/typing:** Full support via `W3C Actions API` (`TouchAction`/multi-pointer `PointerInput` sequences) — this is one of the most capable software-only interfaces for arbitrary gesture composition, including pinch, multi-finger swipe, and precise timed sequences.
- **Arbitrary-app interaction:** Yes with the UiAutomator2 driver (cross-app); Espresso driver is intentionally scoped to one app's process for white-box testing speed/determinism.
- **Requirements:** ADB, Developer Options/USB debugging for setup; installs a server APK and an instrumentation runner on-device (`io.appium.uiautomator2.server` + test package), which must be installed/granted permissions — Appium/UiAutomator2-server users commonly hit `INSTRUMENTATION_FAILED`/permission-denial errors tied to Android's Instrumentation-signing and permission-grant model on newer Android versions, often requiring `adb shell pm grant`, disabling Play Protect scanning of the test APK, or manually re-granting permissions after each app reset [Developer/researcher report] ([appium-uiautomator2-server issue #243](https://github.com/appium/appium-uiautomator2-server/issues/243); [appium issue #12246](https://github.com/appium/appium/issues/12246); [appium issue #17679](https://github.com/appium/appium/issues/17679)).
- **Root:** Not required for the standard UiAutomator2 flow (root helps with some edge cases, e.g., bypassing certain permission dialogs, but is not mandatory).
- **Reliability:** Good for long automated test suites; this is Appium's core use case, with retry/wait/synchronization primitives built in.
- **Screen visibility:** Appium separately supports screenshot capture (`adb exec-out screencap` under the hood) but is not itself a live mirroring tool.

### 1.7 minicap / minitouch (OpenSTF-era tools)

**Mechanism:** Two small C/NDK-built binaries originally from the OpenSTF project. **minitouch** exposes a Unix-socket, LF-terminated line protocol (`d` down, `m` move, `u` up, `c` commit, `w` wait) to inject multi-touch events directly, bypassing both `adb shell input`'s single-touch limit and the overhead of spawning shell processes per event [Verified/documented] ([openstf/minitouch README](https://github.com/openstf/minitouch/blob/master/README.md)). **minicap** streams raw framebuffer frames over a socket for low-latency screen mirroring, often paired with minitouch to build remote-control web UIs.

- **Requirements:** Push the prebuilt binary via `adb push` and run via `adb shell`; **generally does not require root** if launched via `adb shell` on SDK 25+ (older/Wear SDK 20 needed root).
- **Multi-touch:** Yes — this was minitouch's whole purpose, and it remains one of the few free/open tools offering true low-level multi-touch injection without needing to hand-roll `/dev/input` `sendevent` sequences (§1.9).
- **Current status: largely unmaintained.** The OpenSTF org states the projects are "provided as-is... without active development," with further work continuing (if at all) under the DeviceFarmer fork; **minitouch does not work out-of-the-box on Android 10+** due to new security policy changes and requires routing commands through `STFService` instead [Developer/researcher report] ([openstf/minitouch issue #49: Android 10 support](https://github.com/openstf/minitouch/issues/49); [DeviceLab: OpenSTF & DeviceFarmer alternatives in 2026](https://devicelab.dev/blog/openstf-devicefarmer-alternative)). Given this staleness, minitouch/minicap should be considered **legacy/unreliable for Android 12+** without significant patching; modern equivalents (scrcpy, UIAutomator2) have largely superseded them.

### 1.8 scrcpy (control protocol, not just mirroring)

scrcpy is the most actively maintained, most capable open-source tool in this space, and it supports **three distinct input-control architectures** — a critical, often-overlooked distinction:

**(a) SDK-injection mode (default, requires ADB).** The on-device `scrcpy-server` (pushed and run via `adb`) receives control messages over the same ADB socket used for mirroring and calls Android's own input-injection APIs (functionally the same path as `adb shell input`/`InputManager.injectInputEvent`). Its control protocol (documented in [`doc/control.md`](https://raw.githubusercontent.com/Genymobile/scrcpy/master/doc/control.md)) supports: keyboard key events, text injection, mouse click/move, scroll, and — notably — a **"virtual finger" mechanism for simulating a second touch point** from mouse+modifier-key combinations (Ctrl+drag = pinch-zoom from screen center, Shift+drag = vertical tilt, Ctrl+Shift+drag = horizontal tilt), plus file drag-and-drop (push file/APK-install by dropping onto the window) [Verified/documented] ([scrcpy control.md](https://raw.githubusercontent.com/Genymobile/scrcpy/master/doc/control.md)). Full multi-touch beyond this two-point virtual-finger trick is not exposed. This mode requires USB debugging/ADB authorization exactly like §1.2, and is subject to the same Android 13 UID-window-targeting behavior noted in §1.1.

**(b) UHID mode.** Introduced to let scrcpy simulate a **real HID keyboard/mouse device** over the existing ADB (USB or TCP/IP) connection, using the kernel's `uhid` facility on-device, without needing an AOA-capable cable setup. As of scrcpy 3.x this extends to virtual-display / secondary-display control scenarios too [Verified/documented] ([UbuntuHandbook: scrcpy 3.3 adds UHID mouse to virtual display](https://ubuntuhandbook.org/index.php/2025/06/scrcpy-3-3-added-uhid-mouse-to-android-virtual-display/); [scrcpy GitHub issue #4034 discussing HID simulation approaches](https://github.com/Genymobile/scrcpy/issues/4034)). Because it emulates an actual kernel-level HID device rather than calling the app-level injection API, the device treats the input as if a physical keyboard/mouse were plugged in — this can also work **wirelessly** over the ADB TCP/IP connection since only the *control channel* uses ADB, while the resulting input event genuinely enters the kernel input subsystem as an external HID device.

**(c) OTG/AOA mode (`scrcpy --otg`), no ADB at all.** This mode uses `libusb` to speak the **Android Open Accessory (AOA) 2.0 protocol** directly to the phone over USB, sending raw USB HID reports for keyboard/mouse/gamepad, entirely bypassing ADB/USB-debugging [Verified/documented] ([scrcpy doc/otg.md](https://github.com/Genymobile/scrcpy/blob/master/doc/otg.md); [DeepWiki: OTG Mode and USB Input](https://deepwiki.com/Genymobile/scrcpy/5.1-otg-mode-and-usb-input); [XDA: scrcpy to make any Android phone a USB keyboard/mouse](https://xdaforums.com/t/scrcpy-to-make-any-android-phone-a-usb-keyboard-mouse.4656868/)). Since the device receives genuine USB HID reports, from the Android input framework's perspective this input **is indistinguishable in origin from a physically-plugged-in USB keyboard/mouse** (`InputDevice.isVirtual()` returns `false` for it — see Part 2). Limitations: USB connection mandatory (no wireless), no screen mirroring/audio in this mode (input-only), and historically flaky on Windows [Developer/researcher report].

- **Android version support:** Actively maintained; supports Android 5.0+ for mirroring, with UHID/OTG features tracking the newest scrcpy releases (3.x, 2025–2026) that specifically target Android 12–16 compatibility.
- **Works while locked:** Mirroring works with screen off (`--turn-screen-off`, `--stay-awake`) since ADB access itself doesn't require an unlocked screen once authorized; injected input can perform an unlock swipe/PIN entry, same caveats as §1.2.

### 1.9 USB HID gadget mode — companion device (Raspberry Pi/microcontroller) as USB host emulating keyboard/mouse

**Mechanism:** A Linux single-board computer with USB OTG/gadget-capable silicon (Raspberry Pi Zero/4/5, or a dedicated microcontroller like a Teensy/Arduino Leonardo/Pico with native USB) can configure its USB controller in **device mode** presenting a standard HID keyboard/mouse descriptor via the Linux `configfs`/`libcomposite` gadget framework (`/sys/kernel/config/usb_gadget/...`) [Verified/documented] ([Raspberry Pi Forums: Pi Zero as USB keyboard HID gadget](https://forums.raspberrypi.com/viewtopic.php?t=151940); [Raspberry Pi 5 USB Gadget Mode thread](https://forums.raspberrypi.com/viewtopic.php?t=377420)). The Pi's USB port is plugged into the Android phone's USB-C port (with the phone acting as **USB host**, and the SBC as the **USB device/peripheral**, opposite of the usual Pi-as-peripheral-to-a-PC setup) or, more commonly for phone control, a Pi/microcontroller acts as USB host issuing AOA commands to the phone (functionally the same role scrcpy's OTG mode plays, §1.8c).

- Python libraries such as `zero-hid` wrap the gadget-mode `/dev/hidg0` character device to send keyboard/mouse HID reports programmatically from Python running on the Pi [Developer/researcher report] ([zero-hid GitHub](https://github.com/thewh1teagle/zero-hid); [PyPI zero-hid](https://pypi.org/project/zero-hid/1.0.0)).
- **Requirements:** A USB-OTG-capable SBC (not all Pi models — Pi 4/5 need specific port/driver configuration; Pi Zero/Zero 2 W is the most common due to its single USB-C/micro-USB data port); the phone's USB port must support **USB host / OTG mode**, which almost all modern Android phones do (USB-C phones typically support this natively; the phone does not need Developer Options or USB debugging enabled, because from the phone's perspective this is just a standard external HID accessory, exactly like a wired mouse).
- **No ADB/root/Developer Options/accessibility permission needed** on the phone side for basic keyboard/mouse HID input — this is the same class of mechanism as scrcpy's OTG mode (§1.8c) but with a general-purpose SBC instead of a purpose-built libusb tool, useful for building custom control logic, macros, or bridging other input sources (e.g., a script-driven macro pad).
- **Touch/gesture fidelity:** HID mouse reports are relative/absolute pointer + button events, translated by Android's `InputDevice` subsystem into `SOURCE_MOUSE` events — apps see cursor movement and clicks, not true multi-touch `MotionEvent`s, unless the phone's Android build maps an absolute-position HID device into a pointer overlay (Android does support an on-screen mouse cursor since Android 4.0 for external mice). This is functionally more like "plug in a USB mouse" than "simulate a finger" — most apps handle it fine for clicking, but touch-specific gesture recognizers (multi-finger swipe-optimized UI) may not respond identically to a `SOURCE_MOUSE` click as they would to a `SOURCE_TOUCHSCREEN` tap [Inference, consistent with documented `InputDevice` source constants].

### 1.10 Bluetooth HID

**Mechanism:** Android has supported acting as a **Bluetooth HID *host*** (i.e., connecting to external Bluetooth keyboards/mice) since inception, and since **Android 9 (Pie)** gained native support for the phone to act as a **Bluetooth HID *device*** (i.e., the phone can present itself as a keyboard/mouse to another host) via the `BluetoothHidDevice` API [Verified/documented] ([XDA: Android P adds Bluetooth Keyboard/Mouse HID device support](https://www.xda-developers.com/android-p-bluetooth-keyboard-mouse/)). For *controlling* a phone from a computer, the relevant direction is a computer/microcontroller acting as a **BLE/Bluetooth Classic HID device** paired to the phone, exactly analogous to §1.9 but wireless instead of wired USB.

- Sample Android-side implementations exist for the reverse direction (phone-as-HID-device controlling a PC) — e.g. [Kontroller](https://github.com/raghavk92/Kontroller) — but the pattern generalizes: any BLE HID peripheral (ESP32 with `esp_hidh`, a dedicated BLE HID dev board) can pair with the phone and inject keyboard/mouse events with **no ADB, root, Developer Options, or accessibility permission** required — pairing/bonding is the only user action needed, identical in spirit to plugging in a Bluetooth mouse [Verified/documented — ESP-IDF `esp_hidh` docs referenced].
- **Limitations:** Same as wired HID (§1.9) — mouse/keyboard semantics, not native multi-touch; Bluetooth pairing UX (discoverable/bonding) is an extra step versus USB plug-and-play; latency is higher than wired; reliability can suffer from Bluetooth interference/reconnection issues in continuous-use scenarios.

### 1.11 Android Instrumentation & Espresso

**Mechanism:** `Instrumentation` is the base Android testing framework class that allows a specially-signed test APK, launched via `am instrument`, to drive `KeyEvent`/`MotionEvent` injection (`Instrumentation.sendKeyDownUpSync`, `sendPointerSync`) and lifecycle control of a **specific target app process** it's bound to. **Espresso** builds a synchronous, deterministic UI-testing DSL (`onView(...).perform(click())`) on top of Instrumentation [Verified/documented] ([Android Developers: Build instrumented tests](https://developer.android.com/training/testing/instrumented-tests); [AOSP: Instrumentation tests](https://source.android.com/docs/core/tests/development/instrumentation)).

- **Scope limitation:** Both are fundamentally **single-app-scoped** — the test APK must be signed with (historically) the same signing certificate as, and specify `android:targetPackage` for, the app under test (`instr-app-e2e` requires this relationship; a "self-instrumenting" test bundles its own target) [Verified/documented] ([AOSP: Target an app example](https://source.android.com/docs/core/tests/development/instr-app-e2e); [AOSP: Self-instrumenting tests example](https://source.android.com/docs/core/tests/development/instr-self-e2e)). This makes Instrumentation/Espresso **unsuitable for controlling arbitrary third-party apps you don't own/build** — it's a white-box, same-app testing tool, not a general remote-control mechanism. (UIAutomator, by contrast, is explicitly designed for cross-app/black-box control — §1.5.)
- **Requirements:** ADB install of both target APK and test APK; Developer Options/USB debugging for the install/launch step; no root; runs via `adb shell am instrument`.
- **Reliability:** Excellent for its narrow purpose (deterministic, synchronized with the app's UI thread — Espresso explicitly blocks until the app is idle before each action, eliminating flaky timing), but not applicable as a general "control any app" tool.

### 1.12 droidrun / mobilerun and other LLM-agent-driven automation frameworks

A newer category (2024–2026) of open-source tools wraps the above primitives (mainly Accessibility Service + ADB) with an LLM-agent control loop for natural-language-driven automation. **droidrun** (recently rebranded/forked as **mobilerun**) installs a **"Portal" app** on-device that runs an accessibility service exposing the UI tree + screenshots to a host-side agent, which issues taps/swipes/text-input actions and app-launch commands based on LLM reasoning over the observed UI state [Developer/researcher report] ([droidrun/mobilerun README](https://github.com/droidrun/mobilerun/blob/main/README.md); [PyPI: droidrun](https://pypi.org/project/droidrun/)).

- **Requirements:** ADB + Developer Options/USB debugging for initial Portal-app install; the Portal app's accessibility service must be manually enabled in Settings (same user-visible toggle as §1.4, subject to the same Android 15 Restricted Settings gate if sideloaded); no root.
- **Capabilities:** Effectively inherits Accessibility Service capabilities (§1.4) — taps, swipes, text entry, multi-touch via gesture dispatch, cross-app — plus the framework's own planning/vision layer on top. This is a control-*orchestration* layer, not a new low-level injection primitive.
- Related tools in the same space: **AppAgent**, **Mobile-Agent**, and various "Android MCP server" wrappers (surfaced in the search results as `android-mcp-server`, `android-mcp-toolkit`, `android-puppeteer-mcp`) that expose `adb shell input`/UIAutomator2 actions as MCP tool calls for LLM agents — architecturally these are thin wrappers around §1.2/§1.5/§1.6, not independent mechanisms.

### 1.13 Maestro

**Mechanism:** Maestro is a YAML-flow-based mobile UI testing framework. For Android it also installs and drives via `UIAutomator`/`Instrumentation`-adjacent mechanisms under the hood (a device-resident driver comparable in spirit to Appium's UiAutomator2 server), exposing a simplified declarative flow syntax (`tapOn`, `swipe`, `inputText`, etc.) [Developer/researcher report] ([BrowserStack: What is Maestro Testing](https://www.browserstack.com/guide/maestro-testing); [Maestro docs: supported platforms](https://docs.maestro.dev/get-started/supported-platform)). Requirements and capability profile are essentially the same class as UIAutomator2/Appium (§1.5/§1.6): ADB + Developer Options for setup, no root, cross-app capable, no native low-level multi-touch beyond what the underlying gesture APIs expose.

### 1.14 Raw `/dev/input` injection via `sendevent` (root)

**Mechanism:** Below all of the above, the Linux kernel input subsystem exposes each touchscreen (and other input hardware) as a character device at `/dev/input/eventN`. A process with sufficient privilege (this **requires root**, as write access to `/dev/input/*` is not granted to the `shell` UID on production builds) can write raw `input_event` structs (`type`, `code`, `value`) directly to the device node, following the **Multi-touch Protocol B** convention (`ABS_MT_TRACKING_ID`, `ABS_MT_POSITION_X/Y`, `ABS_MT_SLOT`, terminated by `SYN_REPORT`) to synthesize arbitrary multi-touch sequences that the kernel driver — and everything above it, including the Android input framework — treats identically to genuine hardware touch events [Verified/documented] ([AOSP `getevent` tool docs](https://source.android.com/docs/core/interaction/input/getevent); [newandroidbook.com: The Android Input Architecture](https://newandroidbook.com/Book/Input.html)); [Developer/researcher report, benchmarked and implemented as a Magisk module] ([xarantolus: How to tap the Android screen from the underlying Linux system](https://blog.010.one/how-to-tap-the-android-screen-from-the-underlying-linux-system)).

- **Advantages:** True multi-touch (arbitrary number of simultaneous slots, subject to the touch controller's reported `ABS_MT_SLOT` maximum), lowest latency of any software method (no per-call shell spawn, no framework-level Java object marshaling — the developer report above found this dramatically faster than `adb shell input`), and — because it enters the pipeline at the same point as genuine hardware — is the **software method architecturally closest to physical touch** in terms of the event's path through the OS.
- **Drawbacks:** Requires root; **highly device-specific** — the `/dev/input/eventN` numbering, coordinate ranges (some report 0–4096, others native pixel 0–1080/1440, others 0–32767), and whether pressure/touch-major fields are mandatory all vary by touch-controller firmware, so scripts are rarely portable across device models without calibration [Developer/researcher report] ([multi-touch gesture research doc](https://glama.ai/mcp/servers/@AlexGladkov/claude-in-mobile/blob/c99a81727a745eb84df3fc4f22374faff15174b4/docs/multi-touch-research.md)).
- **Works while locked:** Yes, identically to §1.2/§1.9 — it's below the window-focus layer, so it can drive keyguard unlock gestures if root/ADB access exists.

---

<a id="part-2"></a>
## Part 2 — Observability & Detectability (Defensive)

This section describes **what an app or the Android framework can technically observe** about the origin and character of input events. It is written for defensive/technical understanding (accessibility-tooling authors, QA engineers building realistic test harnesses, and app developers implementing anti-abuse logic) and deliberately stops at *what is observable*, not *how to defeat it*.

### 2.1 Event-source metadata: `MotionEvent`, `InputDevice`, tool type

Every `MotionEvent` an app's `onTouchEvent`/`dispatchTouchEvent` receives carries provenance metadata the app can inspect [Verified/documented] ([Android Developers: MotionEvent reference](https://stuff.mit.edu/afs/sipb/project/android/docs/reference/android/view/MotionEvent.html); [Android Developers: Advanced stylus features](https://developer.android.com/develop/ui/views/touch-and-input/stylus-input/advanced-stylus-features)):

- **`MotionEvent.getSource()`** — a bitmask identifying the originating input class: `SOURCE_TOUCHSCREEN`, `SOURCE_MOUSE`, `SOURCE_STYLUS`, `SOURCE_TOUCHPAD`, etc. A HID mouse (§1.9/§1.10/§1.8b) generates `SOURCE_MOUSE` events, which many gesture recognizers treat differently from `SOURCE_TOUCHSCREEN` — this is directly observable and is a structural (not just statistical) difference between HID-mouse-based control and true touch/gesture-injection methods (§1.2–§1.7, §1.14), which all report as `SOURCE_TOUCHSCREEN`.
- **`MotionEvent.getToolType(int pointerIndex)`** — reports `TOOL_TYPE_FINGER`, `TOOL_TYPE_STYLUS`, `TOOL_TYPE_MOUSE`, `TOOL_TYPE_ERASER`, or `TOOL_TYPE_UNKNOWN`. Software-injected events via the standard `input`/`InputManager` path are typically stamped `TOOL_TYPE_FINGER` (mimicking the most common case), but the field is inspectable and its consistency with other signals (e.g., pressure/size data expected of a real finger) can be cross-checked by a sufficiently motivated app.
- **`InputDevice.getSources()` / `InputManager.getInputDeviceIds()` + `getInputDevice(id)`** — any app can enumerate currently-connected input devices and their declared source capabilities [Verified/documented] ([`InputDevice` reference](https://developer.android.com/reference/android/view/InputDevice)). A genuine USB/Bluetooth HID keyboard-mouse (§1.9/§1.10) shows up here as a **distinct enumerated `InputDevice`** with a real vendor/product descriptor, separate from the built-in touchscreen's `InputDevice` entry.
- **`InputDevice.isVirtual()`** — returns `true` for devices the framework itself synthesizes (no physical hardware backing), `false` for anything backed by a real kernel input device node, including a USB/BT HID gadget device plugged in via OTG/AOA (§1.8c, §1.9, §1.10) — because from the kernel's perspective those *are* physical `/dev/input` devices. This is a meaningful, checkable distinction: **AOA/HID-gadget/Bluetooth-HID control methods report as non-virtual, physically-present hardware**, whereas software-level injection through the app-facing `InputManager.injectInputEvent`/`adb shell input` path does not create a new enumerable `InputDevice` at all — the event appears to originate from the existing touchscreen `InputDevice` entry (or, on some Android versions/injection paths, a distinguishable synthetic device ID), which is itself a detectable structural signature for apps that check `InputDevice` provenance consistency [Verified/documented API surface; Inference for the comparative significance].

### 2.2 `isUserAMonkey()` / `isUserAGoat()`

- **`ActivityManager.isUserAMonkey()`** is a genuine, documented public API (since Android 1.6/API 4) that returns `true` when the current session is being driven by the **Monkey** or **monkeyrunner** UI/exerciser testing tools specifically — it does **not** detect ADB `input` commands, Accessibility Service gestures, UIAutomator, Appium, or HID input generally; it is a narrow flag tied specifically to Monkey/monkeyrunner's own instrumentation of the framework [Verified/documented] ([Microsoft Learn: ActivityManager.IsUserAMonkey](https://learn.microsoft.com/en-us/dotnet/api/android.app.activitymanager.isuseramonkey?view=net-android-35.0); [Hacker News discussion of the API](https://news.ycombinator.com/item?id=26931720)).
- **`isUserAGoat()`** is confirmed by community investigation to be an **Easter egg** with no functional detection purpose — it does not correspond to any real automation-detection mechanism; a dedicated app ("isUserAMonkey & isUserAGoat") exists purely to demonstrate/joke about these two oddly-named APIs [Developer/researcher report] ([TrianguloY/isUserAMonkey GitHub](https://github.com/TrianguloY/isUserAMonkey); [F-Droid listing](https://f-droid.org/en/packages/com.trianguloy.isUserAMonkey/)).
- **Practical takeaway:** neither API is a general-purpose "is this being remote-controlled" detector; they cover one specific legacy tool (Monkey) and a joke, respectively.

### 2.3 `AccessibilityManager` — observability of accessibility-based control

An app **can** enumerate currently-enabled accessibility services via `AccessibilityManager.getEnabledAccessibilityServiceList(int feedbackTypeFlags)`, available since API 14 [Verified/documented] ([DevSec Blog: Detecting Banker Malware via Accessibility](https://devsec-blog.com/2024/03/detecting-banker-malware-installed-on-android-devices/)). This is exactly how banking-anti-fraud SDKs and malware-scanning tools flag suspicious accessibility usage:

```java
AccessibilityManager am = (AccessibilityManager) context.getSystemService(Context.ACCESSIBILITY_SERVICE);
List<AccessibilityServiceInfo> services = am.getEnabledAccessibilityServiceList(
    AccessibilityServiceInfo.FEEDBACK_GENERIC | AccessibilityServiceInfo.FEEDBACK_VISUAL | AccessibilityServiceInfo.FEEDBACK_HAPTIC);
```

- Detection heuristics reported in defensive-security literature include: filtering out pre-installed system services (via `ApplicationInfo.FLAG_SYSTEM`/`FLAG_UPDATED_SYSTEM_APP`) to isolate user-installed ones, and specifically checking for the `CAPABILITY_CAN_RETRIEVE_WINDOW_CONTENT` capability flag, which is required for any service that reads/interacts with screen content (a strong signal for remote-control-capable services, benign or malicious) [Verified/documented API + Developer/researcher-reported heuristic] ([DevSec Blog](https://devsec-blog.com/2024/03/detecting-banker-malware-installed-on-android-devices/)).
- **`AccessibilityManager.isEnabled()`** reports whether *any* accessibility service is active system-wide; **`isTouchExplorationEnabled()`** reports specifically whether TalkBack-style touch-exploration mode is on — both are legitimate, documented, publicly-callable APIs any app can query without special permission.
- **User-visible footprint:** Regardless of code-level detection, an enabled accessibility service is **always visible to the user** in Settings → Accessibility → [service name] as an explicit ON toggle with (since Android 15, for sideloaded apps) an additional "Restricted settings" unlock step required before it can even be turned on (§1.1) [Verified/documented].
- Security researchers and malware analyses of Android banking trojans (Vultur, OverlayPhantom, and others) consistently identify heavy accessibility-service reliance as the primary observable mechanism by which such malware achieves remote screen-reading and input-injection, and correspondingly the primary signal used by security tooling and increasingly by the OS itself (Android 14+ narrows what "restricted" accessibility services backed by sideloaded/rarely-used apps can do; coverage indicates continued platform tightening through Android 16/17-era proposals) [Developer/researcher report / security-vendor analysis] ([SecurityWeek: Vultur](https://www.securityweek.com/android-banking-trojan-vultur-abusing-accessibility-services/); [CyberSecurityNews: OverlayPhantom](https://cybersecuritynews.com/android-banking-trojan-overlayphantom/); [Appdome: Prevent Accessibility Service Malware](https://www.appdome.com/how-to/account-takeover-prevention/android-and-ios-trojans/detect-accessibility-service-malware-on-android-apps/); [chocapikk: Android's AccessibilityService — A Single Toggle to Total Device Control](https://chocapikk.com/posts/2026/android-a11y-god-mode/); [gBlock: Android 17 blocks the permission 90% of malware exploits](https://www.gblock.app/articles/android-17-accessibility-api-malware-block)).

### 2.4 USB debugging authorization as an observable/auditable footprint

- The ADB RSA-key authorization dialog and the resulting `adbkey`/authorized-key list represent a **persistent, user-visible artifact**: Developer Options must be manually enabled (multiple taps on Build Number, a documented, deliberately-friction-y gesture) and USB debugging explicitly toggled on, and the first connection from any new host key requires an on-screen confirmation dialog naming the host's RSA key fingerprint [Verified/documented] ([Nelenkov: Secure USB debugging in Android 4.2.2](https://nelenkov.blogspot.com/2013/02/secure-usb-debugging-in-android-422.html)).
- These authorized keys are visible/revocable in Settings → Developer Options → "Revoke USB debugging authorizations." A forensic or MDM inspection of a device can trivially determine whether Developer Options/USB debugging is currently enabled (`Settings.Global.ADB_ENABLED`) — this is queryable by any app holding `WRITE_SECURE_SETTINGS` (privileged) or observable by the user directly in Settings; ordinary third-party apps without that permission cannot read the raw setting but can infer ADB-adjacent conditions indirectly (e.g., certain build/device state checks).

### 2.5 Certificate/signing differences for instrumented/test builds

- Instrumented (Espresso/Instrumentation) test APKs and their target-under-test have historically required matching signing certificates, and the `am instrument` invocation itself leaves OS-level traces (the test package and instrumentation component are registered in `PackageManager` and visible via `adb shell pm list instrumentation` or to any app with `QUERY_ALL_PACKAGES`) [Verified/documented] ([AOSP: Target an app example — signing requirement](https://source.android.com/docs/core/tests/development/instr-app-e2e); [OWASP MASTG 0x05i: Testing Code Quality and Build Settings](https://github.com/OWASP/owasp-mastg/blob/v1.5.0/Document/0x05i-Testing-Code-Quality-and-Build-Settings.md)).
- More broadly, **debuggable builds** (`android:debuggable="true"` in the manifest, standard for `debug` build variants) are a distinct, checkable flag (`ApplicationInfo.FLAG_DEBUGGABLE`) any app can read about *itself* or (with `QUERY_ALL_PACKAGES`) about other installed packages — a debuggable target app combined with an active JDWP/instrumentation session is a detectable configuration mismatch versus a normal production/release install.

### 2.6 Timing/jitter characteristics — human vs. synthetic input

While this report does not provide evasion guidance, the underlying technical facts about *why* timing signals exist are documented in touch-hardware and Android-framework literature and are worth summarizing at a defensive/mechanistic level:

- **Hardware scan-rate quantization:** A touch controller samples at a fixed rate (commonly 60–240Hz on modern flagships; higher on gaming phones). Every genuine `MotionEvent.getEventTime()`/`getDownTime()` timestamp is therefore quantized to multiples of the scan interval (e.g., ~8.3ms steps at 120Hz, ~16.7ms at 60Hz) — a naive software injector that doesn't replicate this quantization (e.g., emitting events at arbitrary/non-quantized intervals, or with suspiciously perfect/constant deltas) produces a statistically distinguishable timing signature from genuine hardware input [Developer/researcher-report-style technical analysis] ([Sendwin: Touch Event Fingerprinting Mobile guide](https://blog.send.win/touch-event-fingerprinting-mobile-complete-guide-2026/)).
- **Contact geometry and pressure quantization:** Real capacitive touch hardware reports a `size`/`pressure`/`touchMajor`/`touchMinor` contact ellipse with device-specific analog-to-digital resolution (documented as roughly 8–10 bit ADC quantization in industry technical writeups); values that are exactly zero, exactly constant, or outside plausible ranges for the claimed device model are structurally different from genuine capacitive contact data. `MotionEvent.getPressure()`/`getSize()`/`getTouchMajor()` are inspectable per-event.
- **Movement kinematics:** Genuine human swipes/drags exhibit natural acceleration/deceleration curves and micro-jitter (small path deviations from a perfectly straight line or a perfectly smooth Bezier), whereas naive programmatic swipes (e.g., `adb shell input swipe x1 y1 x2 y2 duration` internally interpolates linearly) tend toward constant velocity and a perfectly straight path — again, this is a description of an observable *statistical* difference rooted in how each method generates the intermediate points, not an evasion technique. `android.view.VelocityTracker` and raw historical-point access (`MotionEvent.getHistoricalX/Y`) expose this path data to any view/app that wants to analyze it [Verified/documented API + Developer/researcher-report analysis] ([Android Developers: Track touch and pointer movements](https://developer.android.com/develop/ui/views/touch-and-input/gestures/movement)).
- **Multi-touch pointer coalescing:** `MotionEvent.getCoalescedEvents()` (Pointer Events context) exposes how many sub-events the compositor batched between dispatch frames — a signal tied to the underlying hardware's true sampling rate, again potentially inconsistent for naively-generated synthetic sequences [Developer/researcher-report].

**Important caveat:** the physical-actuator methods in Part 3, and HID-based methods (§1.8b/c, §1.9, §1.10) that inject at or below the kernel input layer, do **not** share the "obviously synthetic" timing signature of naive high-level software injection, because a real touch controller (physical finger/stylus/actuator case) or a real HID device (mouse case) genuinely produces hardware-quantized, physically-jittery data — the observability discussion here is about *what categories of signal exist to be observed*, and different control methods land very differently against each signal depending on how close to "real hardware" they are architecturally, which is exactly why Part 1 and Part 3 both emphasize each method's position in the input pipeline.

### 2.7 Summary table of observability by method

| Method | `getSource()` | `getToolType()` | New `InputDevice` enumerated? | `isVirtual()` | Accessibility service visible in Settings? | USB-debug artifact? | Timing/jitter matches real hardware? |
|---|---|---|---|---|---|---|---|
| Physical finger | `SOURCE_TOUCHSCREEN` | `TOOL_TYPE_FINGER` | No (existing touchscreen device) | N/A (not applicable, genuine) | No | No | Yes (genuine) |
| Capacitive stylus (passive) | `SOURCE_TOUCHSCREEN` | `TOOL_TYPE_FINGER` or `TOOL_TYPE_STYLUS`* | No | N/A | No | No | Yes (genuine, hardware-quantized) |
| Mechanical/hardware touch actuator (Part 3) | `SOURCE_TOUCHSCREEN` | Usually `TOOL_TYPE_FINGER` | No | N/A | No | No | Yes — physically real contact, hardware-quantized like genuine touch |
| ADB `input`/`InputManager` injection | `SOURCE_TOUCHSCREEN` | `TOOL_TYPE_FINGER` (synthesized) | No | N/A (app-level injection, not device-level) | No | **Yes** (ADB auth) | Often not — depends on injector's interpolation |
| Accessibility `dispatchGesture` | `SOURCE_TOUCHSCREEN` | `TOOL_TYPE_FINGER` (synthesized) | No | N/A | **Yes** — visible toggle | No (unless installed via ADB) | Depends on stroke-path construction |
| UIAutomator/Appium/Maestro | `SOURCE_TOUCHSCREEN` | `TOOL_TYPE_FINGER` (synthesized) | No | N/A | Sometimes (if accessibility-based) | Yes (setup) | Depends |
| `sendevent` raw `/dev/input` | `SOURCE_TOUCHSCREEN` | Depends on injected fields | No (writes to existing device node) | N/A | No | No (root-based, no ADB needed if pre-rooted) | Can closely mimic real hardware if fields are crafted carefully |
| HID gadget/AOA (USB or BT) | `SOURCE_MOUSE` (or gamepad/keyboard sources) | `TOOL_TYPE_MOUSE` | **Yes** — real external `InputDevice` | **`false`** (physically present) | No | No | N/A (real HID device, genuinely jittery per its own hardware) |

*\*Stylus tool-type detection depends on whether the touchscreen controller supports active-stylus discrimination (see Part 3.1); many passive capacitive styluses are indistinguishable from a finger at the `MotionEvent` level.*

---

<a id="part-3"></a>
## Part 3 — Physical Touchscreen Actuator Hardware

### 3.1 How capacitive touchscreens actually detect touch

Modern smartphones use **projected capacitive (PCAP) touch**, specifically **mutual-capacitance** sensing in a grid of transparent electrodes (usually ITO — indium tin oxide) etched in rows and columns beneath the cover glass, separated by an insulating layer [Verified/documented] ([Densitron: Projected Capacitive Touch Sensor](https://www.densitron.com/company/news/projected-capacitive-touch-sensor); [TI CapTIvate Technology Guide: Capacitive Sensing Basics](https://software-dl.ti.com/msp430/msp430_public_sw/mcu/msp430/CapTIvate_Design_Center/1_83_00_08/exports/docs/users_guide/html/CapTIvate_Technology_Guide_html/markdown/ch_basics.html); [Canvys: Projected Capacitive Touch](https://www.canvys.com/custom-touch-screen-monitors/touch-screen-pcap-touch/)):

- Each row/column intersection forms a small capacitor with a baseline capacitance value the controller continuously measures.
- A grounded conductive object (a human finger, or any sufficiently conductive body) placed near an intersection **draws away some of the local electric field**, measurably *reducing* the mutual capacitance at that intersection — the controller detects this dip and computes a touch coordinate (often with sub-electrode interpolation for higher effective resolution than the raw electrode pitch).
- **Grounding matters:** a human finger works because the human body is a large, earth-referenced (or at least self-capacitive, charge-storing) conductor connected to the touching finger — this is why a truly floating, ungrounded, small conductive object often registers weakly or not at all, and why some capacitive-stylus and actuator designs specifically add a **ground wire/strap** back to a chassis or earth reference to reliably register [Developer/researcher report, directly built and tested] ([TestDevLab: How We Built a Robot for Automated Manual Mobile Testing](https://www.testdevlab.com/blog/how-we-built-a-robot-for-automated-manual-mobile-testing) — "added a ground cable running from Arduino to stylus pen so that the mobile device screen registers touches properly").
- Because detection is based on **capacitive coupling, not pressure**, any sufficiently conductive material with adequate contact area and proper grounding can register a touch — mechanical pressure/force is irrelevant to *detection* (though a physical actuator still needs enough travel/consistency to make reliable, repeatable contact).

### 3.2 DIY/hobbyist actuator approaches

**(a) Capacitive stylus tip on a servo/solenoid ("tapper") rig.** The simplest class of build: a passive capacitive-stylus-like tip (commercially available conductive-rubber stylus tips, or homemade conductive foam/aluminum-foil-wrapped tips) mounted on a servo arm or solenoid plunger that swings/presses down onto a fixed screen location, then retracts. This is adequate for **single-point repeated tapping** (e.g., automated "click this button 10,000 times" endurance/reliability testing) but not for swipes without additional axes of motion [Developer/researcher report] ([Hackaday: Reaching Out To A Touch Screen With A Microcontroller](https://hackaday.com/2012/05/04/reaching-out-to-a-touch-screen-with-a-microcontroller/); [Instructables: Screen Tapping Robot](https://www.instructables.com/Screen-Tapping-Robot/)).

**(b) XY gantry/plotter rigs.** For arbitrary-coordinate tap/swipe capability, hobbyists adapt CNC/3D-printer-style XY gantries (belt- or leadscrew-driven, stepper-motor-controlled, Arduino/Raspberry-Pi-driven via GRBL or similar firmware) with a capacitive-stylus end effector mounted on a Z-axis that lowers to make contact, then moves along X/Y while in contact to perform a swipe, then lifts. This is the most flexible and most commonly documented approach for reproducing **both taps and swipes/drags** at arbitrary, precisely repeatable coordinates.

**(c) Delta-robot rigs.** TestDevLab's **"Tappy"** project ([full write-up](https://www.testdevlab.com/blog/how-we-built-a-robot-for-automated-manual-mobile-testing)) [Developer/researcher report] built a 3-arm delta-robot (Hitec HS-311 hobby servos) with a spring-loaded pen-style capacitive stylus end effector (the spring absorbs over-travel so the tip doesn't crack the screen if positioning is imperfect):
  - **Cost:** approximately **€70 (~US $80)** in parts, explicitly noted as roughly 10x cheaper than a pre-built commercial rig.
  - **Precision/calibration:** required a two-stage calibration — kinematic calibration of the delta-arm geometry itself, and a **browser-based screen-calibration step** (open a calibration webpage on the device, so the rig learns the screen's physical coordinate mapping without needing a custom app installed on the device under test).
  - **Mechanical iteration:** early prototypes had reliability problems (heavy moving platform detaching from ball-joint linkages); switching from metal bearing balls to neodymium magnets and from metal to plastic linkage rods improved reliability.
  - **Swipe support:** confirmed working after the mechanical redesign ("tap and swipe").
  - **Grounding fix:** as noted in §3.1, they had to add a dedicated ground wire from the Arduino to the stylus pen for the phone to reliably register contact — a concrete, hands-on confirmation of the physics in §3.1.
  - **Multi-touch:** not mentioned/implemented in this specific build (single end-effector).

**(d) Commercial multi-finger robots.** **MATT (Adapta Robotics)** is a commercial touchscreen-test robot using **1, 2, or 3 independently-moving capacitive stylus "nibs"** as interchangeable end effectors, explicitly supporting **tap, swipe, pinch, and rotate** gestures (i.e., genuine multi-touch via multiple independently-actuated physical contact points) and designed to work with curved and irregularly-shaped device screens without device modification [Developer/researcher report / vendor technical description] ([MATT — Adapta Robotics](https://www.mattrobot.ai/)). This demonstrates that **true physical multi-touch is achievable** but requires multiple independently-controllable end effectors (i.e., multiple small XY/Z mechanisms, not just one stylus), which is mechanically and cost-wise a significant step up from a single-tip rig.

**(e) Academic/patented approaches.** A published patent application, [WO2017051263A2 "Robot arm for testing of touchscreen applications"](https://patents.google.com/patent/WO2017051263A2/en), documents a robot-arm approach to touchscreen test automation at a more industrial/IP-protected level, consistent with the general architecture above (arm + conductive/capacitive effector + coordinate calibration) [Verified/documented — patent text].

### 3.3 Multi-touch feasibility for DIY builds

- **Single end-effector rigs** (the overwhelming majority of hobbyist builds found) are inherently limited to one contact point at a time — they can still simulate a *sequence* of single touches, and some can simulate two-point gestures like pinch/zoom only if they have **two independently movable effectors** (like the delta-robot "virtual finger" concept scrcpy uses in software, §1.8a, but reproduced mechanically).
- **True simultaneous multi-touch** (as MATT achieves) requires multiple independently-actuated tips converging on the screen at the same time with independent XY(Z) control per tip — a meaningfully harder and more expensive mechanical design than a single-axis tapper or single-effector gantry, explaining why most budget/DIY builds documented online stick to one effector and single/sequential touch.

### 3.4 Coordinate accuracy achievable

- Gantry/plotter-based rigs using stepper motors and standard CNC-style leadscrews/belts can typically achieve **sub-millimeter mechanical positioning accuracy**, which is more than sufficient given that modern phone screens have physical pixel pitches on the order of tens of micrometers but UI touch targets are conventionally sized (Android's own accessibility guidelines recommend touch targets of at least 48dp, several millimeters) — mechanical precision is rarely the limiting factor; **calibration accuracy** (correctly mapping the rig's coordinate frame to the screen's coordinate frame) is the more common practical error source, which is exactly why TestDevLab built a dedicated calibration step [Developer/researcher report + Inference from documented touch-target sizing standards].
- Servo-arm/delta-robot designs are somewhat less precise than a true Cartesian gantry due to the kinematic transforms and mechanical slop in ball/socket linkages (as evidenced by TestDevLab's iteration to reduce play), but with correction (magnet joints, plastic linkages, calibration) can still reliably hit standard UI touch targets.

### 3.5 Do screen protectors interfere?

- Because capacitive sensing works through a thin insulating layer by design (the cover glass itself already sits between the finger and the actual sensing electrodes), a **thin, properly-applied screen protector (tempered glass or film) generally does not meaningfully block capacitive touch detection** — this is consistent across general consumer-technology explainers on the topic [Anecdotal/general-knowledge consensus] ([Nelson Miller: How Do Touchscreens Work With a Screen Protector?](https://nelson-miller.com/how-do-touchscreens-work-with-a-screen-protector/); [SuperGuardZ: Does a Screen Protector Affect Touch Sensitivity?](https://superguardz.com/does-a-screen-protector-affect-touch-sensitivity/)). However:
  - A **thick** or air-gapped protector, or a poorly-conductive/very-hard stylus tip that already sits at the margin of reliable detection, can push a marginal actuator design over into unreliable territory — thickness/gap adds capacitive attenuation.
  - **[Inference]:** For a physical actuator rig specifically (as opposed to a human finger), because such rigs often already operate near the minimum threshold for reliable capacitive coupling (especially if grounding is imperfect, per §3.1/§3.2c), an added screen protector is more likely to matter for a marginal DIY rig than for a human finger, which has ample and consistent conductivity/contact area. Removing the screen protector from the device under test is a common practical workaround reported by hobbyists building these rigs, though this was not found as an explicit universal recommendation in the sources reviewed and is offered here as inference from the underlying physics plus TestDevLab's grounding struggles.

### 3.6 Do modern phone characteristics (thinner glass, edge-to-edge, curved screens) make this harder?

- **Thinner glass** generally **helps** capacitive coupling (less insulating-layer attenuation between the actuator tip and the sensing electrode grid), so thinner modern cover glass is not a barrier and if anything is more forgiving than older, thicker glass.
- **Edge-to-edge and curved-edge ("waterfall") screens** pose a *mechanical/geometric* challenge more than an electrical one: a rigid, fixed-angle stylus tip calibrated for a flat central area may not make reliable, consistent contact near curved edges where the surface normal changes — commercial rigs like MATT specifically market their "advanced embedded software safely interacts with curved screens and all device shapes" as a differentiator, implying this is a genuinely nontrivial problem that simpler DIY rigs may not handle well [Developer/researcher report / vendor claim] ([MATT — Adapta Robotics](https://www.mattrobot.ai/)). Note that the broader industry trend as of 2025–2026 has actually been *away* from curved/edge displays back toward flat panels for durability and readability reasons [Developer/researcher-report trend coverage] ([Android Police: Samsung ditches curved displays](https://www.androidpolice.com/samsung-ditches-curved-displays/)), which somewhat reduces this concern's practical relevance for the newest flagship generation but remains relevant for the many still-curved devices in active use.
- No source reviewed indicated that modern capacitive sensitivity/electrode density changes have made mechanical actuation fundamentally harder — if anything, higher-resolution/higher-sensitivity modern controllers (partly driven by demand for reliable glove-touch and stylus support) are, if anything, easier to trigger reliably than older, less sensitive panels [Inference from general PCAP technology trend].

### 3.7 Phone modification needed?

**None of the DIY/commercial physical-actuator approaches surveyed require any modification to the phone itself** — this is their entire value proposition relative to software methods: no Developer Options, no USB debugging, no accessibility service installation, no root, nothing installed on the device. The phone is treated as a completely opaque black box interacted with purely through its touchscreen surface, exactly as a human user would. The one common exception/caveat is the browser-based calibration step some rigs use (opening a calibration webpage), which requires no persistent install and leaves no lasting footprint.

### 3.8 Realistic DIY cost (tens to few hundred dollars)

Based on the projects reviewed:

| Build class | Approx. cost | Source |
|---|---|---|
| Single solenoid/servo tapper (single point) | **$10–40** (microcontroller + solenoid/servo + basic frame) | [Instructables: Screen Tapping Robot](https://www.instructables.com/Screen-Tapping-Robot/); [Hackaday microcontroller touch article](https://hackaday.com/2012/05/04/reaching-out-to-a-touch-screen-with-a-microcontroller/) |
| Delta-robot with spring-loaded capacitive stylus, tap+swipe | **~€70 / ~US $80** (Hitec servos + Arduino + printed/fabricated frame) | [TestDevLab "Tappy"](https://www.testdevlab.com/blog/how-we-built-a-robot-for-automated-manual-mobile-testing) |
| XY CNC-style gantry rig (stepper motors, GRBL, capacitive stylus Z-axis) | **~$100–300** (reusing common 3D-printer/CNC hobby parts: NEMA17 steppers, belts/rails, Arduino/RAMPS or similar controller) | [Inference from typical CNC/3D-printer hobby-part pricing, consistent with the general architecture described in Hackaday/patent sources] |
| Commercial multi-finger robot (MATT-class) | Not disclosed publicly; multi-effector, curved-screen-capable rigs are understood to be priced well above hobbyist DIY builds (four-figure-plus territory is typical for this class of commercial test-automation hardware) | [Inference, MATT pricing not published in reviewed source] |

---

<a id="part-4"></a>
## Part 4 — Comparison Table & Rankings

### 4.1 Comparison table

| Method | Software/Hardware | USB | Root | Permissions | Tap | Swipe | Multi-touch | Arbitrary apps | Modern Android (12–16) support | Physical-looking input | Reliability | Approx. cost |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Physical finger** | Hardware (human) | No | No | None | Yes | Yes | Yes (up to ~10 fingers) | Yes | Full | N/A — is the baseline | Perfect (but not automatable) | $0 |
| **Physical actuator rig** (servo/gantry/delta, DIY) | Hardware | No | No | None | Yes | Yes (gantry/delta) | Only with multiple effectors | Yes | Full (device-agnostic — treats phone as black box) | Genuinely physical contact; structurally indistinguishable from touch at the OS level | Good once calibrated; mechanical wear/drift over time | $10–300 DIY; $$$$ commercial |
| **ADB `input tap/swipe`** | Software | Optional (Wi-Fi ADB works too) | No | USB debugging auth | Yes | Yes | **No** | Yes | Full (Android 13 UID-window nuance, doesn't block normal use) | No — synthetic, often linear-interpolated | High for scripted use; ~300-400ms/call latency | $0 |
| **`InputManager.injectInputEvent` (direct)** | Software | Depends on access method | Usually yes (or shell-elevated) | `INJECT_EVENTS` (signature) | Yes | Yes | Yes (full `MotionEvent` control) | Yes | Full, subject to Android 13 UID checks | No | High (in-process, low latency) | $0 |
| **Accessibility `dispatchGesture`** | Software | No | No | Accessibility service (user-enabled) | Yes | Yes | **Yes** (multi-stroke) | Yes | Full | No | Good for discrete gestures; less suited to continuous/streamed control | $0 |
| **UIAutomator / UIAutomator2** | Software | Setup only | No | USB debugging (setup) | Yes | Yes | Yes | Yes (cross-app by design) | Full | No | Good; resident server reduces overhead | $0 |
| **Appium (UiAutomator2 driver)** | Software | Setup only | No | USB debugging (setup) | Yes | Yes | Yes (W3C Actions) | Yes | Full | No | High — built for long test suites | $0 (OSS) |
| **Appium (Espresso driver)** | Software | Setup only | No | USB debugging (setup), matching signing cert historically | Yes | Yes | Limited | **No — single app only** | Full | No | Very high (synchronized w/ UI thread) | $0 |
| **minicap/minitouch** | Software | Setup only | Sometimes | USB debugging (setup) | Yes | Yes | Yes | Yes | **Poor — largely unmaintained, broken on Android 10+ without patching** | No | Low (unmaintained) on modern Android | $0 |
| **scrcpy — SDK mode** | Software | Optional (Wi-Fi works) | No | USB debugging auth | Yes | Limited (virtual-finger trick for 2-pt) | Partial (2-point via modifier keys) | Yes | Full | No | High | $0 |
| **scrcpy — UHID mode** | Software (emulates HID) | Optional (works over Wi-Fi ADB) | No | USB debugging auth (for the ADB control channel) | Yes (mouse-based) | Yes | No (mouse semantics) | Yes | Full, actively developed | Partially — real kernel HID device, but `SOURCE_MOUSE` not `SOURCE_TOUCHSCREEN` | High | $0 |
| **scrcpy — OTG/AOA mode** | Hardware protocol (software-driven) | **Required** | No | **None — no ADB/Developer Options needed** | Yes (mouse-based) | Yes | No (mouse semantics) | Yes | Full | Yes — genuine external USB HID device (`isVirtual()==false`) | High | $0 (uses existing USB cable) |
| **USB HID gadget (Pi/microcontroller)** | Hardware | **Required** | No (device side) | **None on phone side** | Yes (mouse-based) | Yes | No (mouse semantics) | Yes | Full — treated as plug-in mouse/keyboard | Yes — real external HID device | High once built | $10–35 (Pi Zero/microcontroller) |
| **Bluetooth HID (peripheral device)** | Hardware | No | No | **None on phone side** (pairing only) | Yes (mouse-based) | Yes | No (mouse semantics) | Yes | Full | Yes — real external HID device | Medium (BT reliability/latency) | $10–30 (BLE dev board) |
| **Instrumentation/Espresso (general)** | Software | Setup only | No | USB debugging + signing-cert match | Yes | Yes | Limited | **No — single target app** | Full | No | Very high (deterministic) | $0 |
| **`sendevent` raw `/dev/input`** | Software (kernel-level) | Setup only (or none if pre-rooted) | **Yes** | **Root** | Yes | Yes | **Yes** (full Protocol B) | Yes | Full — most device-specific to calibrate, but works at the lowest OS layer | Closest software method to physical (enters pipeline at hardware layer) | High once calibrated per-device | $0 |
| **droidrun/mobilerun (LLM agent)** | Software (orchestration over Accessibility) | Setup only | No | Accessibility service (user-enabled) | Yes | Yes | Yes (inherits dispatchGesture) | Yes | Full | No | Good (adds retry/reasoning layer) | $0 (OSS) + LLM API cost |
| **Maestro** | Software | Setup only | No | USB debugging (setup) | Yes | Yes | Yes | Yes | Full | No | High (built for CI/test reliability) | $0 (OSS) |

### 4.2 Rankings

- **Cheapest:** **ADB `input tap/swipe`** (and equally, Accessibility `dispatchGesture`, UIAutomator, Appium, Maestro, `sendevent`) — all are $0, requiring only a USB cable you likely already own and free open-source tooling. Among physical methods, the **single solenoid/servo tapper** ($10–40) is cheapest.

- **Simplest:** **`adb shell input tap x y`** — a single command-line invocation, no app install, no service to enable, works the moment USB debugging is authorized. Nothing else in this survey has a lower time-to-first-successful-tap.

- **Most capable software solution:** **Appium with the UiAutomator2 driver** — combines cross-app reach, full W3C Actions multi-touch gesture composition, robust element-selection APIs, built-in retry/synchronization, and mature tooling/ecosystem for long-running automated suites. Accessibility `dispatchGesture` is close behind and is the only mechanism that works with *zero* setup on the computer side (no ADB link needed once the service is installed), but Appium's gesture-composition flexibility and cross-platform test ecosystem make it the more complete solution.

- **Most reliable:** **Espresso (Instrumentation-based)** for its narrow scope — its defining design goal is eliminating flaky timing by synchronizing every action with the app's UI thread idle state, making it the most deterministic method surveyed. For general-purpose (not single-app) reliability, **Appium/UIAutomator2** is the most reliable broadly-applicable choice, given its purpose-built retry/wait primitives and wide production use in CI pipelines.

- **Most precise:** **`sendevent` raw `/dev/input` injection** — because it writes directly into the same kernel input-event pipeline genuine hardware uses, it offers full, uncompromised control over every `MotionEvent` field (pointer count, pressure, tool type, exact per-pointer coordinates) with no framework-level abstraction loss, at the lowest achievable latency of any software method. (Runner-up: `InputManager.injectInputEvent` directly, which offers the same fidelity from a higher-privilege in-process context.)

- **Best for continuous interaction:** **A resident on-device server (UIAutomator2/minitouch-style architecture) or scrcpy's UHID mode** — both avoid the ~300–400ms per-call process-spawn overhead that plagues repeated `adb shell input` invocations, sustaining low-latency, high-frequency interaction. Among physically-installed mechanisms, **scrcpy's UHID or OTG/AOA HID modes** are particularly well suited to continuous interaction because they behave like a persistently-connected physical mouse rather than issuing discrete, connection-per-call commands.

- **Best purely physical:** **MATT-class multi-effector commercial robot** — the only physical approach demonstrated to achieve genuine simultaneous multi-touch (tap, swipe, pinch, rotate) across curved and irregular screen shapes without any device modification, at production-grade reliability.

- **Best DIY hardware:** **TestDevLab's "Tappy" delta-robot design** (or an equivalent XY-gantry build) — documented, reproducible, ~$80 in parts, achieves both tap and swipe with a calibration workflow, and its publicly-documented grounding/mechanical lessons (magnet joints, plastic linkages, ground wire to the stylus) make it the most practical, well-evidenced starting point for a hobbyist build in the tens-to-hundreds-of-dollars range.

- **Best for reproducing ordinary touchscreen interaction (i.e., closest to "just a normal user tapping the screen"):** **A physical actuator (finger-equivalent stylus rig)**, because it is the only category that produces genuine capacitive-coupling contact events indistinguishable at the hardware/OS level from a real finger — no `SOURCE_MOUSE` mismatch, no missing `InputDevice` enumeration quirks, no framework-level injection artifacts. Among software methods, **Accessibility `dispatchGesture`** and **`sendevent`** come closest, since both produce genuine `SOURCE_TOUCHSCREEN` `MotionEvent`s through the same window-dispatch path real touches use — but true physical actuation is the only method with zero abstraction gap.

- **Best overall:** **Appium (UiAutomator2 driver) for general-purpose software automation; scrcpy for interactive human-in-the-loop remote control; a physical actuator rig for pure black-box interaction with zero on-device footprint.** No single method dominates every axis — the right choice depends heavily on whether the goal is scripted test automation (Appium/UIAutomator2), live interactive control with screen visibility (scrcpy, which uniquely also solves the "can the computer see the phone's screen" requirement none of the pure-input methods address), or interaction that must leave literally no software trace on the device (physical actuator hardware). If forced to name one, **scrcpy** earns the broadest "best overall" nod: it is free, actively maintained, offers three selectable input architectures (SDK/UHID/OTG) trading off setup requirements against physical realism, natively solves screen visibility (which most competitors don't attempt), and works across the full Android 12–16 range.

---

<a id="sources"></a>
## Sources

### Official/AOSP documentation
- [Android Open Accessory 2.0 — source.android.com](https://source.android.com/docs/core/interaction/accessories/aoa2)
- [Custom accessories — source.android.com](https://source.android.com/docs/core/interaction/accessories/custom)
- [getevent tool — source.android.com](https://source.android.com/docs/core/interaction/input/getevent)
- [Instrumentation tests — source.android.com](https://source.android.com/docs/core/tests/development/instrumentation)
- [Self-instrumenting tests example — source.android.com](https://source.android.com/docs/core/tests/development/instr-self-e2e)
- [Target an app example — source.android.com](https://source.android.com/docs/core/tests/development/instr-app-e2e)
- [Create an accessibility service — developer.android.com](https://developer.android.com/guide/topics/ui/accessibility/service)
- [Build instrumented tests — developer.android.com](https://developer.android.com/training/testing/instrumented-tests)
- [UI Automator — developer.android.com](https://developer.android.com/training/testing/other-components/ui-automator)
- [Track touch and pointer movements — developer.android.com](https://developer.android.com/develop/ui/views/touch-and-input/gestures/movement)
- [Advanced stylus features (Views) — developer.android.com](https://developer.android.com/develop/ui/views/touch-and-input/stylus-input/advanced-stylus-features)
- [InputDevice reference — developer.android.com](https://developer.android.com/reference/android/view/InputDevice)
- [MotionEvent reference (archival mirror) — stuff.mit.edu](https://stuff.mit.edu/afs/sipb/project/android/docs/reference/android/view/MotionEvent.html)
- [Learn about restricted settings — support.google.com](https://support.google.com/android/answer/12623953?hl=en)

### scrcpy (Genymobile)
- [scrcpy GitHub repository](https://github.com/Genymobile/scrcpy)
- [scrcpy control.md protocol doc](https://raw.githubusercontent.com/Genymobile/scrcpy/master/doc/control.md)
- [scrcpy otg.md](https://github.com/Genymobile/scrcpy/blob/master/doc/otg.md)
- [scrcpy issue #3186 — Android 13 input injection breakage](https://github.com/Genymobile/scrcpy/issues/3186)
- [scrcpy issue #4785 — InjectInputEvent help](https://github.com/Genymobile/scrcpy/issues/4785)
- [scrcpy issue #4034 — better HID simulation method](https://github.com/Genymobile/scrcpy/issues/4034)
- [scrcpy issue #733 — unlock scripting](https://github.com/Genymobile/scrcpy/issues/733)
- [DeepWiki: OTG Mode and USB Input](https://deepwiki.com/Genymobile/scrcpy/5.1-otg-mode-and-usb-input)
- [DeepWiki: Advanced Topics](https://deepwiki.com/Genymobile/scrcpy/5-advanced-topics)
- [UbuntuHandbook: scrcpy 3.3 adds UHID mouse to virtual display](https://ubuntuhandbook.org/index.php/2025/06/scrcpy-3-3-added-uhid-mouse-to-android-virtual-display/)
- [XDA: scrcpy to make any Android phone a USB keyboard/mouse](https://xdaforums.com/t/scrcpy-to-make-any-android-phone-a-usb-keyboard-mouse.4656868/)
- [XDA: scrcpy update brings keyboard/mouse passthrough without USB debugging](https://www.xda-developers.com/scrcpy-update-keyboard-mouse-passthrough/)

### UI automation frameworks
- [appium-uiautomator2-driver README](https://github.com/appium/appium-uiautomator2-driver/blob/master/README.md)
- [Appium docs: UiAutomator2 driver quickstart](https://appium.io/docs/en/2.1/quickstart/uiauto2-driver/)
- [appium-uiautomator2-server issue #243](https://github.com/appium/appium-uiautomator2-server/issues/243)
- [appium issue #12246 — permission denial starting instrumentation](https://github.com/appium/appium/issues/12246)
- [appium issue #17679 — permission related app op changed](https://github.com/appium/appium/issues/17679)
- [openatx/uiautomator2 GitHub](https://github.com/openatx/uiautomator2)
- [BrowserStack: What is Maestro Testing](https://www.browserstack.com/guide/maestro-testing)
- [Maestro docs: supported platforms](https://docs.maestro.dev/get-started/supported-platform)
- [OWASP MASTG 0x05i: Testing Code Quality and Build Settings](https://github.com/OWASP/owasp-mastg/blob/v1.5.0/Document/0x05i-Testing-Code-Quality-and-Build-Settings.md)

### minicap/minitouch and OpenSTF
- [openstf/minitouch README](https://github.com/openstf/minitouch/blob/master/README.md)
- [openstf/minitouch issue #49 — Android 10 support](https://github.com/openstf/minitouch/issues/49)
- [openstf/minicap GitHub](https://github.com/openstf/minicap)
- [DeviceLab: OpenSTF & DeviceFarmer alternatives in 2026](https://devicelab.dev/blog/openstf-devicefarmer-alternative)

### LLM-agent Android automation
- [droidrun/mobilerun README](https://github.com/droidrun/mobilerun/blob/main/README.md)
- [PyPI: droidrun](https://pypi.org/project/droidrun/)
- [Multi-touch gestures research doc (glama.ai mirror)](https://glama.ai/mcp/servers/@AlexGladkov/claude-in-mobile/blob/c99a81727a745eb84df3fc4f22374faff15174b4/docs/multi-touch-research.md)

### ADB / input injection internals
- [CircleCI/Robotium discuss: INJECT_EVENTS permission](https://discuss.circleci.com/t/injecting-to-another-application-requires-inject-events-permission/19970)
- [Gesture Testing Using ADB Commands — shariqsp.com](https://www.shariqsp.com/mobileTesting/Gesture.html)
- [Zebra Developer Portal: Introduction to ADB Shell Commands](https://developer.zebra.com/community/home/blog/2015/03/09/introduction-to-adb-shell-commands)
- [android-inputinjector library](https://github.com/arnebp/android-inputinjector)
- [xarantolus: How to tap the Android screen from the underlying Linux system](https://blog.010.one/how-to-tap-the-android-screen-from-the-underlying-linux-system)
- [newandroidbook.com: The Android Input Architecture (Chapter 12)](https://newandroidbook.com/Book/Input.html)
- [XDA: CLI lock screen settings guide](https://xdaforums.com/t/guide-how-to-get-or-set-the-lock-screen-settings-via-cli-command.4647038/)
- [Repeato: How to Lock/Unlock Android Screen via ADB](https://www.repeato.app/how-to-lock-and-unlock-the-android-screen-via-adb/)
- [Nelenkov: Secure USB debugging in Android 4.2.2](https://nelenkov.blogspot.com/2013/02/secure-usb-debugging-in-android-422.html)
- [getandora: adb devices unauthorized fix guide](https://getandora.in/blog/adb-unauthorized)

### USB/Bluetooth HID
- [Raspberry Pi Forums: Pi Zero as a USB keyboard HID gadget](https://forums.raspberrypi.com/viewtopic.php?t=151940)
- [Raspberry Pi Forums: Raspberry Pi 5 USB Gadget Mode](https://forums.raspberrypi.com/viewtopic.php?t=377420)
- [zero-hid GitHub](https://github.com/thewh1teagle/zero-hid)
- [PyPI: zero-hid](https://pypi.org/project/zero-hid/1.0.0)
- [XDA: Android P adds Bluetooth Keyboard/Mouse HID device support](https://www.xda-developers.com/android-p-bluetooth-keyboard-mouse/)
- [Kontroller GitHub (Android BluetoothHidDevice sample)](https://github.com/raghavk92/Kontroller)

### Detectability / anti-automation (defensive)
- [TrianguloY/isUserAMonkey GitHub](https://github.com/TrianguloY/isUserAMonkey)
- [F-Droid: isUserAMonkey & isUserAGoat](https://f-droid.org/en/packages/com.trianguloy.isUserAMonkey/)
- [Hacker News: ActivityManager#isUserAMonkey() discussion](https://news.ycombinator.com/item?id=26931720)
- [Microsoft Learn: ActivityManager.IsUserAMonkey](https://learn.microsoft.com/en-us/dotnet/api/android.app.activitymanager.isuseramonkey?view=net-android-35.0)
- [DevSec Blog: Detecting Banker Malware via Accessibility](https://devsec-blog.com/2024/03/detecting-banker-malware-installed-on-android-devices/)
- [Appdome: Prevent Accessibility Service Malware](https://www.appdome.com/how-to/account-takeover-prevention/android-and-ios-trojans/detect-accessibility-service-malware-on-android-apps/)
- [SecurityWeek: Vultur banking trojan](https://www.securityweek.com/android-banking-trojan-vultur-abusing-accessibility-services/)
- [CyberSecurityNews: OverlayPhantom banking trojan](https://cybersecuritynews.com/android-banking-trojan-overlayphantom/)
- [chocapikk: Android's AccessibilityService — A Single Toggle to Total Device Control](https://chocapikk.com/posts/2026/android-a11y-god-mode/)
- [gBlock: Android 17 blocks the permission 90% of malware exploits](https://www.gblock.app/articles/android-17-accessibility-api-malware-block)
- [Sendwin: Touch Event Fingerprinting Mobile — Complete Guide 2026](https://blog.send.win/touch-event-fingerprinting-mobile-complete-guide-2026/)
- [Android Authority: Android 15 restricted settings sideloading](https://www.androidauthority.com/android-15-restricted-settings-sideloading-3481098/)
- [9to5Google: Android 15 sideloaded apps restrictions](https://9to5google.com/2024/09/12/android-15-sideloaded-apps-restrictions/)

### Touchscreen physics
- [Densitron: Projected Capacitive Touch Sensor](https://www.densitron.com/company/news/projected-capacitive-touch-sensor)
- [TI CapTIvate Technology Guide: Capacitive Sensing Basics](https://software-dl.ti.com/msp430/msp430_public_sw/mcu/msp430/CapTIvate_Design_Center/1_83_00_08/exports/docs/users_guide/html/CapTIvate_Technology_Guide_html/markdown/ch_basics.html)
- [Canvys: Projected Capacitive Touch](https://www.canvys.com/custom-touch-screen-monitors/touch-screen-pcap-touch/)
- [Nelson Miller: How Do Touchscreens Work With a Screen Protector?](https://nelson-miller.com/how-do-touchscreens-work-with-a-screen-protector/)
- [SuperGuardZ: Does a Screen Protector Affect Touch Sensitivity?](https://superguardz.com/does-a-screen-protector-affect-touch-sensitivity/)

### Physical actuator / DIY hardware projects
- [Hackaday: Reaching Out To A Touch Screen With A Microcontroller](https://hackaday.com/2012/05/04/reaching-out-to-a-touch-screen-with-a-microcontroller/)
- [Instructables: Screen Tapping Robot](https://www.instructables.com/Screen-Tapping-Robot/)
- [TestDevLab: How We Built a Robot for Automated Manual Mobile Testing ("Tappy")](https://www.testdevlab.com/blog/how-we-built-a-robot-for-automated-manual-mobile-testing)
- [MATT — Adapta Robotics](https://www.mattrobot.ai/)
- [Google Patents: WO2017051263A2 — Robot arm for testing of touchscreen applications](https://patents.google.com/patent/WO2017051263A2/en)
- [PhoneArena: Automated touchscreen test device shows off smartphone accuracy](https://phonearena.com/news/Automated-touchscreen-test-device-shows-off-the-accuracy-of-smartphones_id10418)
- [Android Police: Samsung ditches curved displays](https://www.androidpolice.com/samsung-ditches-curved-displays/)
