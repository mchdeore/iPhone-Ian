---
tags: [ios, face-id, passcode, autofill, accessibility, voiceover, 2fa, passkey]
status: answered
date: 2026-10-05
related:
  - "[[== SOFTWARE CENTRAL ==]]"
---

# iOS control constraints — Face ID, autofill, accessibility

## Question

What iOS-specific behaviors affect a robot physically tapping a stock iPhone? Face ID lockout, autofill prompts, accessibility features, stylus vs finger behavior, and the current state of app login flows.

## Key findings

### Face ID / biometrics: robot never triggers them

- **5 failed Face ID attempts → passcode required.** iOS locks Face ID. `[Documented]` https://support.apple.com/en-us/102381
- Touch ID: same 5-attempt rule.
- Device passcode has escalating timeouts: 1 min → 5 min → 15 min → 60 min → disabled (requires restore). This is triggered by wrong passcode entries, NOT biometric failures.
- **Robot path:** never triggers Face ID. Always uses passcode fallback. "Enter Passcode" button is always available on the lock screen. Passcode entry is a standard number pad — robot taps digits directly.

### Autofill: can help or hinder

- **Triggered by tapping a username/email field.** iOS shows saved credentials in the QuickType bar (above the keyboard) or as a "Passwords" button. `[Documented]`
- AutoFill requires Face ID/Touch ID/passcode authentication to release credentials. This is a separate prompt from app login.
- Credential fill happens via tapping the suggestion — NOT automatic.
- Third-party managers (1Password, Bitwarden) register as AutoFill providers. Same mechanism.
- **Two flows for robot:**
 - Flow A (credentials saved in iCloud Keychain): tap username field → tap autofill suggestion → authenticate → done.
 - Flow B (credentials not saved): tap username field → dismiss/ignore autofill bar → manually type username, tap password field, type password.
- The QuickType bar above the keyboard is an extra UI element the robot's CV must recognize and either use or skip.

### Accessibility features: mostly a risk

- **VoiceOver** — screen reader. Gestures completely change (single tap = select, double tap = activate). If accidentally enabled (triple-click side button), robot taps behave differently → major risk. Disable the Accessibility Shortcut or set it to something harmless.
- **Switch Control** — allows external switches (Bluetooth, USB). Requires prior setup on phone. Not useful for us. Physical tapping still works alongside it.
- **AssistiveTouch** — on-screen overlay. Designed for human accessibility, adds overlay robot must work around. Not useful.
- **Full Keyboard Access** — requires connected keyboard. Not relevant.
- **Recommendation:** disable triple-click Accessibility Shortcut. Stick with pure capacitive tapping. No accessibility features needed.

Sources: https://support.apple.com/guide/iphone/use-switch-control-iph2c3a5acfc/ios · https://support.apple.com/guide/iphone/use-assistivetouch-iph96b21954/27.0/ios/27.0

### Stylus vs finger: identical to the touchscreen

- **Passive capacitive stylus = same as finger.** Both distort the capacitive field. The screen cannot distinguish them at the hardware level. `[Documented]`
- **Grounded stylus works better.** Connection to ground provides stronger, more consistent signal than floating metal.
- **Touch latency:** iPhone touch latency ~40–75ms. Robot tap-and-release should be ≥100ms to reliably register. Very fast taps (<50ms) may be missed.
- **Palm rejection:** iPad has it for Apple Pencil. iPhone has no stylus-specific palm rejection (Apple Pencil doesn't work on iPhone). Single-point tapping is safe. Multi-touch gestures (pinch, edge swipe) can be accidentally triggered if two contact points — avoid.
- **Edge rejection** on newer iPhones (thin bezels) only affects holding grip, not tapping.

### App login landscape (2025-2026)

- **Passkey adoption growing (~5 billion globally, mid-2026) but password fallback remains universal.** No major app has gone passkey-only. `[Community]`
- Banking: most major banks offer passkey as option alongside password. Password + 2FA still common.
- Social media: still username/email + password. "Sign in with Apple/Google" buttons common — these trigger Face ID and are dead ends for robot.
- Email: Gmail/Outlook use password + 2FA. IMAP/SMTP always username + password (protocol limitation).
- **"Sign in with Apple" buttons are dead ends.** Robot should tap "Other options" or go directly to password field.
- **2FA is the hardest problem:**
 - SMS-based: robot needs phone number access or SIM swap. Hardest case.
 - TOTP-based: can be computed offline from shared secret. Preferred.
 - Email-based: robot needs email access. Medium difficulty.
 - **Prefer accounts without 2FA, or with TOTP 2FA** (can be pre-provisioned).

Sources: https://digitaldigest.com/passkey-adoption-reality-check-financial-services-2 · https://www.wultra.com/blog/passwordless-authentication-in-banking-a-guide-to-fido2-passkeys

## Open questions / follow-ups

- Which specific iOS apps are our first targets? Their login flow specifics matter.
- How to handle 2FA codes practically — TOTP vault integration on HomeLab host?
- Does the robot need to simulate a "human typing speed" to avoid bot detection on certain apps?