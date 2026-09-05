# 02 — Training & Control Spec

Covers decision **D4** (an ML training rig / app is a first-class deliverable) and
**D5** (command-driven, credential-aware control).

The agent's job: **command + camera image of the iPhone screen → a sequence of
physical taps/swipes/keystrokes** that accomplishes the command.

---

## 1. Control loop (perception → planning → action)

Because the phone is a black box, the agent's only input is a **camera image** of
the screen (no accessibility tree). The loop:

```
        ┌─────────────────────────────────────────────┐
        │  command (e.g. "login to Bank")             │
        └───────────────┬─────────────────────────────┘
                        ▼
  [camera] → [perception: OCR + VLM grounding] → screen state + element boxes
                        ▼
              [planner: intent → next action]
                        ▼
     [calibration transform: screen px → gantry XY]
                        ▼
        [robot: move + tap / swipe / type key]
                        ▼
              [verify from next camera frame] ──┐
                        ▲                        │
                        └──── loop until done ───┘
```

This mirrors the software agent design in
`research/05-ai-agent-architecture-notes.md`; only the **action layer** changes
(physical stylus moving to XY instead of software input injection). Perception and
planning are reusable.

## 2. Calibration (the actual hard problem)

- We must map **camera pixels → iPhone screen coordinates → gantry XY**.
- Approach: a **homography** from a one-time calibration routine — display known
  targets (a calibration webpage or a grid image on the phone), have the robot or
  operator register correspondences, solve the transform. (Tappy used a
  browser-based calibration page for exactly this.)
- Re-calibration triggers: phone remounted, camera moved, different iPhone model.
- **This is where reliability is won or lost** — budget the most effort here.

## 3. The ML training rig / app (D4)

Goal: make the agent *perform well*, not just run. Two layers, build the cheap one
first.

### Layer A — zero-training baseline (Phase 2, lazy path)
- Off-the-shelf **VLM** (e.g. a vision model) + **OCR** for grounding, plus the
  homography for coordinates. No training at all.
- Establishes a working loop and, crucially, **generates labeled data** as it
  runs.

### Layer B — trained grounding (Phase 3)
- **Data-collection app** records, per step, a tuple:
  `(screen_image, command, chosen_action, target_coord, outcome)`.
  - `outcome` = did the next frame show the expected state change? (self-labeling).
- Uses of the data:
  - **Fine-tune** a UI-grounding model on iPhone screens for faster/cheaper/more
    reliable element localization than a general VLM.
  - **Imitation learning** from operator demonstrations (human drives, robot
    records).
  - **Evaluation set**: a fixed battery of (command → expected outcome) cases to
    measure success rate as we iterate (see §5).
- **Privacy:** any frame containing a visible secret (password field mid-type)
  must be dropped or masked before it enters the dataset (see charter §6).

## 4. Command vocabulary (D5)

Commands are **high-level intents** the planner expands into action sequences.
Initial set (extend later):

| Command | Meaning | Example expansion |
|---|---|---|
| `exit` | Leave current screen / app | tap system back / close, or swipe-up to home |
| `enter` | Confirm / submit current field or dialog | tap primary button (Continue/Submit/OK) |
| `login <target>` | Authenticate to a named app/site | focus username → type user → focus password → type secret (from vault) → `enter` |
| `open <app>` | Launch an app | go home → locate icon → tap |
| `type <text>` | Type arbitrary text on the on-screen keyboard | per-key tap sequence |
| `tap <label>` | Tap a described element | ground `<label>` in the current frame → tap |

- Intents are **verified**: after acting, the agent checks the next frame to
  confirm the expected state change and retries/aborts on mismatch.
- `login` is the flagship command and the reason credential retrieval exists.

## 5. Success metrics

- **Task success rate** on the fixed evaluation battery (§3 Layer B).
- **Taps-to-completion** vs. an ideal path (efficiency).
- **Calibration drift**: positional error over a session.
- **Zero secret leaks** in logs/screenshots/datasets (hard gate, not a metric to
  optimize — it must always hold).

## 6. Credential handling (summary — full rules in charter §6)

- Secrets live in a **host-side vault** on HomeLab (macOS Keychain / 1Password CLI
  / `sops`+`age`). Never in this repo.
- `login <target>` → agent requests the specific secret for that target → robot
  **types** it → secret is never logged or stored in training data.
- iOS reality: biometric/passkey-only logins can't be satisfied by a robot; scope
  `login` to credential-typeable flows.
