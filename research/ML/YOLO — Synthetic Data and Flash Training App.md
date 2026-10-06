---
tags: [YOLO, synthetic-data, flash-app, homography, ML, computer-vision]
status: answered
date: 2026-10-04
related:
  - "[[== ML Central ==]]"
---

# 02 — Synthetic data and the "flash training app"

Goal: auto-label YOLO training captures by flashing targets at known CSS coordinates
in mobile Safari, mapping them into the camera frame via a homography, and
optionally scoring tap accuracy. Extends `specs/02-firmware-and-software.md` §5.1.

Tags: `[Documented]` · `[Benchmark]` · `[Community]`.

## Part 1 — Synthetic data for detection

### Q: Does synthetic/randomized data transfer to the real world?

Yes. **Tobin et al. 2017 (Domain Randomization)** trained a real-world detector to
**1.5 cm accuracy using only simulated images** with non-realistic random textures,
robust to distractors and occlusion. `[Documented]` Randomize so aggressively that
reality looks like "just another variation." For us, the flashed rectangle *is* the
rendered target; the physical screen + camera is the reality gap.

### Q: What's the cheapest way to generate synthetic detection data?

2D compositing, not 3D rendering. **Dwibedi et al. 2017 (Cut, Paste and Learn)**:
paste object crops on random backgrounds with mixed blending so the detector ignores
paste artifacts. **+21% relative** when combined with real data; **synthetic + 10%
real beat all-real**. `[Benchmark]` The flash app is the physical version of this:
the "paste" happens on a real screen photographed by a real camera, so lighting and
edge artifacts are realistic for free.

### Q: How much real data must be mixed in?

| Study | Finding |
|---|---|
| Burdorf et al. 2022 (Cityscapes/Synscapes) | Real-data need reduced **up to 70%**; **5–20% real** is the efficient mix `[Benchmark]` |
| YOLO11 rural driving (2026) | **1 real : 0.5 synth** best (mAP50 0.758); **1:1 caused domain shift** that erased gains `[Benchmark]` |
| SIP15-OD manufacturing | YOLOv8 **synthetic-only** hit mAP50 94–99.5% with strong randomization + distractors `[Benchmark]` |

Plan: mostly auto-labeled flash data **plus a small (~5–20%) hand-checked set of
real iOS screens photographed in the rig**, used for fine-tune and validation.

### Q: What tooling exists for richer synthesis?

BlenderProc, Unity Perception, NVIDIA Omniverse Replicator / Isaac Sim — all
**overkill** for flat GUI targets. Rendering in the real browser on the real device
is a *better* domain match than any renderer. `ponytail:` the browser is the
synthesizer.

### Q: Is there precedent for GUI-specific datasets?

- **Rico** — >9.3k Android apps, >66k screens; usable as realistic backgrounds and element priors. `[Documented]`
- **ScreenSpot** (SeeClick) — >1,200 instructions across iOS/Android/macOS/Windows/Web, tagged **Text** vs **Icon/Widget**. `[Documented]`
- **ScreenSpot-Pro** — best model only **18.9%**; GUI grounding is far from solved. `[Benchmark]`
- Lesson: Text vs Icon/Widget is a sensible minimal class taxonomy to flash.

## Part 2 — Designing the flash app

### Architecture

```
Host (Mac now / HomeLab later): Flask + OpenCV  (Flask already in .venv)
 ├─ GET /flash → fullscreen page in iPhone Safari (CSS px)
 │   · 4 ArUco/AprilTag fiducials at FIXED CSS positions
 │   · N targets (text|icon) at RANDOMIZED CSS x,y,w,h,color,label
 │   · visible frame_id patch (number / small QR)
 │   · touchstart → POST /tap {frame_id, clientX, clientY}
 ├─ camera thread: cv2.VideoCapture (locked focus/exposure)
 └─ labeler: detect fiducials → findHomography(CSS→cam px)
       → perspectiveTransform(target corners) → YOLO txt
```

### Capture loop (pseudocode)

```python
FIDUCIALS_CSS = ...             # 4 fixed CSS corner points
for frame_id in range(N):
  targets = randomize(pos, size, color, text, bg, brightness)
  push_to_browser(targets, frame_id)    # websocket/SSE
  sleep(0.4)                # hold: let photons settle
  img = camera.read()
  if read_frame_id(img) != frame_id: continue   # latency guard
  cam_pts = detect_fiducials(img)         # cv2.aruco
  if len(cam_pts) < 4: continue          # fail closed, no bad labels
  H, _ = cv2.findHomography(FIDUCIALS_CSS, cam_pts)
  for t in targets:
    box = cv2.perspectiveTransform(t.corners_css(), H)
    write_yolo_line(t.cls, *normalize(box, img.shape)) # cls cx cy w h
  # optional: await /tap, score = 1 - |tap - center| / radius
```

### Q: CSS px vs physical px (devicePixelRatio)?

Modern iPhones report **DPR 3** (iPhone 15: ~393 CSS px wide ≈ 1179 physical).
`[Documented]` **Do everything in CSS px and DPR cancels out**: fiducials, targets,
and `touchstart clientX/clientY` all share CSS px, so the homography maps CSS →
camera directly, and tap scoring is apples-to-apples. DPR only matters for
gantry↔screen physical calibration.

### Q: Safari viewport / safe-area pitfalls?

- `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">` and read `env(safe-area-inset-*)` to know where the Dynamic Island / home indicator sit. `[Documented]`
- The collapsing URL bar changes viewport height. Use **Add to Home Screen (standalone PWA)** for a stable, chrome-free viewport; otherwise `dvh` / `visualViewport`.

### Q: How to sync displayed frame and camera capture?

`requestAnimationFrame` runs before the next vsync (~16 ms @60 Hz), but photons reach
the glass **~16–50 ms** later (compositor + panel). `[Documented]/[Community]`
Capturing in that window labels a target that isn't shown yet. Fixes:

1. **Flash → hold 300–500 ms → capture.** Simple, race-free; ~2–3 samples/s is plenty. `ponytail:` ceiling is throughput; upgrade path is (2).
2. **Visible frame_id handshake** — read the id back from the camera image and only label on match.

### Q: What should be randomized?

- Software (per frame, free): position, size, aspect, color/contrast, label text, class, background (solid → gradient → Rico/real screenshot), distractors, target count, brightness.
- Physical (per session): room light, camera exposure/WB, slight camera distance/angle (fiducials re-detected per frame), True Tone/Night Shift on/off.

### Q: How to handle glare and moiré?

- Camera further back + zoom in (optical low-pass) — most effective.
- Shutter at an integer multiple of the refresh period (e.g. 1/60 s) to kill rolling bands.
- Disable auto-brightness.
- Diffuse lighting, slight off-axis angle against specular hotspots.
- Some residual moiré/glare is useful randomization — don't over-engineer it away. `[Community]`

## Part 3 — Pitfalls

- **Stale homography → label drift.** Detect fiducials **in every labeled frame**; rigid mounts; skip frames with <4 fiducials; never let the stylus occlude a fiducial; drop high reprojection-error frames.
- **Overfitting to synthetic style.** Model learns "flat rectangle on plain bg" instead of iOS controls. Use realistic mock UI, real screenshots as backgrounds, heavy randomization, and **validate only on real iOS captures**.
- **Secrets in captures.** Captures are photos of the screen. The flash app renders only synthetic content; never run the camera while real login/vault content is on glass; scrub/segregate datasets (charter security rules).

## Key takeaways

- Domain randomization + distractors is the biggest lever; synthetic-only can reach cm-level real accuracy.
- The flash app is physical cut-and-paste with free realistic artifacts.
- Keep a **5–20% real** set; avoid ≥1:1 synth:real.
- Work in **CSS px**; DPR cancels.
- Standalone PWA + `viewport-fit=cover` for a stable viewport.
- **Flash → hold → capture**, frame-ID check, **per-frame homography**, fail closed.

## Sources

- https://arxiv.org/abs/1703.06907 — Tobin et al., Domain Randomization
- https://arxiv.org/abs/1708.01642 — Dwibedi et al., Cut, Paste and Learn
- https://arxiv.org/html/2202.00632v1 — Burdorf et al., reducing real data with synthetic
- https://arxiv.org/html/2607.27058 — real/synthetic mixing, YOLO11
- https://arxiv.org/pdf/2506.07539v1 — SIP15-OD, synthetic-only YOLOv8
- https://arxiv.org/pdf/2509.15045 — sim-to-real with YOLOv11 + domain randomization
- https://developer.nvidia.com/blog/bootstrapping-object-detection-model-training-with-3d-synthetic-data/
- https://interactionmining.org/rico
- https://arxiv.org/abs/2401.10935 — SeeClick / ScreenSpot
- https://arxiv.org/html/2504.07981v1 — ScreenSpot-Pro
- https://docs.opencv.org/3.4/d9/dab/tutorial_homography.html
- https://docs.opencv.org/3.4/d5/dae/tutorial_aruco_detection.html
- https://www.lambdatest.com/web-technologies/devicepixelratio-safari
- https://sizzy.co/blog/safe-area-insets
- https://web.dev/articles/speed-rendering
- https://www.royal-display.com/moire-pattern-screen/
