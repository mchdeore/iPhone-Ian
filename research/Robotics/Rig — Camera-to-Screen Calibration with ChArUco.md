---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, robotics, calibration, charuco, opencv, homography, computer-vision]
---

# Rig — Camera-to-Screen Calibration with ChArUco

**TL;DR**
- If the rig uses a camera, pixel → mm accuracy decides tap accuracy.
- Use a **ChArUco** board: chessboard corners with ArUco IDs, so it tolerates occlusion and gives sub-pixel corners.
- **Calibrate the lens first**, then get the screen-plane pose. A raw homography is only accurate when distortion is already removed.
- Close the loop by **displaying a ChArUco on the phone screen itself**, so the calibration target *is* the tap plane.

**Builds on:** [[iOS Control — Relative Cursor Calibration and Visual Servoing]] and [[YOLO — Synthetic Data and Flash Training App]] (homography).

## Why ChArUco

- Plain ArUco marker corners aren't very accurate "even after applying subpixel refinement". ChArUco interpolates **chessboard** corners, which are accurate at sub-pixel level [1].
- Community estimate: inner-corner sub-pixel quality up to ~10× better (forum claim, unmeasured) [2].
- Handles **partial views and occlusion**, e.g. the toolhead covering part of the screen [1].

## Procedure

1. **Intrinsics:** print a ChArUco board, capture 20–40 images at varied angles and positions, run `calibrateCamera`. Record the reprojection error.
2. **Screen-plane pose:** show a ChArUco image **on the phone** (the Flask app can render it at a known pixel pitch). Detect it, then `solvePnP` with intrinsics to get the camera → screen transform.
3. **Screen → gantry:** jog the stylus to 4–9 known screen points (the app shows touch coordinates), then fit gantry mm ↔ screen px (affine or homography).
4. **Chain:** camera px → screen px → gantry mm. Re-run step 2 whenever the phone is re-seated.

## Pitfalls (from OpenCV docs and an independent evaluation)

- Without intrinsics, ChArUco interpolation uses local homographies and is **more sensitive to distortion** [1].
- **Disable marker corner refinement** when detecting for ChArUco. Nearby squares make subpixel refinement drift, and the error spreads to the interpolated corners [1].
- Direct OpenCV ChArUco detection is limited by blur and compression and degrades with strong radial distortion; OpenCV may report corners **shifted by 0.5 px** by convention [3].
- Newer OpenCV uses `cv2.aruco.CharucoDetector`; older tutorials use a different API [1].
- Phone-screen glare and moiré: lower the camera exposure, tilt slightly off-axis, and use a matte screen protector if needed.

## Accuracy budget

Target ≤ 0.5 mm landing error (iOS minimum tap targets are ~44 pt ≈ 7 mm). Measure it with [[Touch Telemetry — Measuring What the Rig Emits]] landing scatter.

## Pitch in

- [ ] Robotics: add a `/calib` page to the Flask app that renders a ChArUco at native resolution.
- [ ] Post reprojection error and end-to-end landing error after the first calibration.

## Sources

1. [OpenCV — ChArUco detection tutorial](https://docs.opencv.org/4.5.5/df/d4a/tutorial_charuco_detection.html) `[Documented]`
2. [OpenCV forum — non-planar calibration thread](https://forum.opencv.org/t/non-planar-camera-calibration-returns-system-error/1323/19) `[Community]`
3. [StereoComplex — ChArUco identification baseline](https://stereocomplex.readthedocs.io/en/latest/CHARUCO_IDENTIFICATION.html) `[Benchmark]`

## Related

- **Summary:** [[State of — Machine Learning]] · [[State of — Robotics]]
