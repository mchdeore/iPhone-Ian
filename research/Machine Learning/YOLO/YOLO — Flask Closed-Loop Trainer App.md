---
type: research
status: answered
author: marc
date: 2026-10-05
tags: [machine-learning, yolo, robotics, flask, flash-app, trainer, active-learning, computer-vision]
---

# 06 — Flask trainer app: the closed-loop flash app

Extends the passive labeler in into a **trainer** that also
*requests an action* ("tap the blue button", "swipe left"), *observes* it, *scores* it, and *logs
labeled samples*. Builds on `specs/02-firmware-and-software.md` §5.1 (scoring + RL honesty); 02 owns
CSS px/DPR, fiducials, homography, flash→hold→capture. Core framing: **two observations/episode** —
pointer events are the *precise* touch truth (iPhone reports contact in CSS px), the camera frame is
the detector input + physical proof. `[Documented]`·`[Benchmark]`·`[Community]`.

## Q: Flask vs Flask-SocketIO vs plain WebSocket/SSE?

Data shape decides: a **server monologue** (host pushes "flash + act"), client replies
with one ordinary POST — not a bidirectional sub-100 ms conversation. That is SSE's shape.

| Option | Fit | Cost |
|---|---|---|
| **SSE (`EventSource`)** ⭐ | server→client push over plain HTTP; auto-reconnect in-spec; stock Flask `Response(gen, mimetype="text/event-stream")` | ~0 deps `[Documented]` |
| Plain WebSocket | full-duplex; only worth it for bidirectional, high-freq, <100 ms round-trips (games/collab) — not us | own protocol, sticky sessions, DIY reconnect `[Community]` |
| Flask-SocketIO | Socket.IO on WSGI needs **eventlet/gevent greenlets** monkey-patched onto sync Flask | most parts, least benefit `[Community]` |

Verdict: **SSE + `POST /touch`.** Flash→hold→capture already costs ~300–500 ms/episode (02), so
WebSocket latency buys nothing. `ponytail:` upgrade to WS only if swipe navigation later needs a tight bidirectional stream.

## Q: Capturing touch in mobile Safari (+ hiding chrome)?

- **Pointer Events, not Touch Events:** `pointerdown/move/up` unify finger+stylus, give
 `clientX/clientY` in CSS px (same frame as targets/fiducials → DPR cancels, 02), plus
 `pressure`, `pointerId`, `timeStamp`. `[Documented]`
- **Swipes = trajectories:** on `pointermove` call **`getCoalescedEvents()`** for merged sub-frame
 samples. Caveat: UAs may cap it (Chromium stylus 1/frame); `pointerrawupdate` is higher-rate but secure-context-only, thin on Safari. `[Documented]`/`[Community]`
- **Claim the gesture:** `touch-action:none` + `-webkit-user-select/callout:none` + `preventDefault()`
 on `touchmove`/`gesturestart` (`{passive:false}`). **`user-scalable=no` is ignored** by iOS Safari — don't rely on it. `[Community]`
- **No iPhone Fullscreen API** (status bar always shows) → hide chrome via **standalone PWA**
 (Add-to-Home-Screen + manifest `"display":"standalone"`): bar-free *and* kills pinch/double-tap
 zoom; detect `navigator.standalone===true`. Install is manual; EU iOS 17.4+ falls back to a Safari tab. `[Documented]`

## Q: Flash-to-capture timing for an *action*?

02's recipe stands (`requestAnimationFrame`→paint, **hold 300–500 ms**, grab, verify visible
`frame_id`, per-frame homography). Trainer adds only **timestamp alignment**: `pointerdown.timeStamp`
vs grab time confirms the tap hit the shown frame; for swipes the coalesced path is the temporal truth, the hold-time frame is the training image. `[Documented]`

## Q: Episode schema (JSONL) + YOLO labels?

**JSONL, append-only** — one episode/line: crash-safe, streamable, read with a 3-line loop on the
CPU box. `images/`+`labels/` stay **pure Ultralytics** (`yolo train` ingests untouched, 02); trainer extras live in the sidecar only.

```jsonl
{"episode":"1696550000123","ts":1696550000.42,
 "request":{"instruction":"tap the blue button","action":"tap",
  "targets":[{"cls":"button","x":120,"y":430,"w":120,"h":48,"color":"#2d7"}]}, // CSS px
 "frame_id":"1696550000123","image":"images/....jpg","label":"labels/....txt",
 "homography_reproj_px":0.7,"fiducials":4,"robot":{"gantry_xy":[88.1,142.6]},
 "observed":{"type":"tap","points":[{"t":0.0,"x":121,"y":452}]},"score":0.93,"split":"train"}
```

YOLO label = `labels/<frame_id>.txt`, one `cls cx cy w h` line/instance (0–1 normalized), projected
from target CSS corners through the per-frame homography (02). Human-sortable IDs (epoch-ms); keep
`reproj_px`/`fiducials` to drop bad-calibration frames; **split by session, never by frame** (01). `[Documented]`

## Q: How does the score drive mining / active learning?

Labels are free, so this is **not** classic active learning (choosing *what to label*) — it is
**hard-example mining + guided domain randomization**: bin each score/IoU by condition (region,
size, contrast, brightness, glare); a low-scoring bin **raises its sampling weight** next batch (a
weighted sampler / cheap bandit over 02's knobs) so the rig keeps flashing *where it fails*; frames
with detector `conf<τ` or tap `error>ε` form a **hard set** oversampled next retrain — 01's "tap score = built-in difficulty signal" operationalized. `[Community]`/`[Documented]`

## Q: Honest note — is any of this RL?

No. Keep three apart: **(a)** the detector trains by **supervised** box/class/DFL loss on free
homography labels — no reward gradient (01); **(b)** the score updates only the **data distribution**
(mining) and the **calibration** (affine/homography correction from tap error, §5.1) — not a learned
policy; **(c)** at most a **one-step contextual bandit** (context, action=tap XY, reward=score) — no
state transition/credit/discount, so **not** full RL. `[Community]` It becomes RL only with multi-step
episodes + a policy learned from trajectory reward (*swipe navigation across screens*) — flag and defer; tap-the-target gets ~95% from calibration (§5.1).

## Endpoint list + ~40-line Flask skeleton (stdlib SSE, no SocketIO)

| Method | Path | Role |
|---|---|---|
| `GET` | `/` | flash/trainer page (pointer capture, standalone PWA) |
| `GET` | `/manifest.webmanifest` | `display:standalone` → chrome-free Add-to-Home-Screen |
| `GET` | `/stream` | **SSE** push next episode `{episode_id, frame_id, instruction, targets}` |
| `POST` | `/touch` | browser reports observed path `{episode_id, frame_id, type, points[]}` |
| `GET` | `/healthz` | liveness + camera-thread status |

```python
import json, time, queue, random, pathlib
from flask import Flask, Response, request, send_file

app = Flask(__name__)
LOG = pathlib.Path("data/episodes.jsonl"); LOG.parent.mkdir(parents=True, exist_ok=True)
bus, pending = queue.Queue(), {}   # ponytail: single client, in-memory; upgrade = per-session queue/Redis

def new_episode():
  eid = str(int(time.time() * 1000))
  tgt = {"cls": "button", "x": random.randint(40, 320), "y": random.randint(120, 760),
      "w": 120, "h": 48, "color": "#2d7"}         # CSS px (DPR cancels, note 02)
  req = {"episode_id": eid, "frame_id": eid, "action": "tap",
      "instruction": "tap the blue button", "targets": [tgt]}
  pending[eid] = req; return req

def score_tap(t, p):          # spec §5.1 rubric, CSS px
  cx, cy, r = t["x"] + t["w"]/2, t["y"] + t["h"]/2, max(t["w"], t["h"])/2
  return max(0.0, 1.0 - ((p["x"]-cx)**2 + (p["y"]-cy)**2) ** 0.5 / r)

@app.get("/")             # pointer-capture page (touch-action:none, standalone PWA)
def index(): return send_file("static/index.html")

@app.get("/stream")          # SSE: host -> browser command channel
def stream():
  def gen():
    bus.put(new_episode())     # kick off first episode
    while True: yield f"data: {json.dumps(bus.get())}\n\n"
  return Response(gen(), mimetype="text/event-stream")

@app.post("/touch")          # browser -> host: observed touch (ground truth)
def touch():
  obs = request.get_json(force=True) # {episode_id, frame_id, type, points:[{t,x,y}]}
  req = pending.pop(obs.get("episode_id"), None)
  if req is None: return {"ok": False}, 409
  score = score_tap(req["targets"][0], obs["points"][-1])
  rec = {**req, "observed": obs, "score": score,
      "image": f"images/{req['frame_id']}.jpg",      # camera thread writes it
      "label": f"labels/{req['frame_id']}.txt"}      # homography -> YOLO txt (note 02)
  with LOG.open("a") as f: f.write(json.dumps(rec) + "\n")
  bus.put(new_episode()); return {"ok": True, "score": round(score, 3)}  # close the loop

assert score_tap({"x":0,"y":0,"w":100,"h":100}, {"x":50,"y":50}) == 1.0   # self-check: centre==1.0
if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, threaded=True)     # SECURITY: no auth; LAN only unless tunneled
```

## Constraints tie-in

- **CPU-only ≤16 GB box:** **no online learning** — the app only serves + logs; training is a
 separate periodic `yolo train` elsewhere (Colab T4 / offline, 03). "Closed loop" = collect →
 retrain offline → copy weights back → resume; a human/cron closes it.
- **Windows public port:** phone reaches the host on LAN (`http://host:5000`); if blocked, a tunnel
 (ngrok/cloudflared) exposes a public **HTTPS** port → (HTTPS = secure
 context for PWA service workers / `pointerrawupdate`). **Security: the skeleton binds `0.0.0.0` with
 no auth** — a public endpoint logging camera frames and driving a robot MUST get token/basic-auth and bind narrowly first.

## Key takeaways

- **SSE + one POST**, not SocketIO/WebSocket — right shape, near-zero overhead.
- **Pointer Events** (+ `getCoalescedEvents` for swipes); pointer path = touch truth, camera = detector input; CSS px throughout.
- **No iPhone Fullscreen API** → standalone PWA hides chrome *and* kills zoom; use `touch-action:none`, not `user-scalable=no`.
- **JSONL sidecar**; `images/`+`labels/` stay pure Ultralytics; split by session. Score → **mining + guided randomization**, not RL (one-step bandit at most); training **offline/periodic**; public port needs auth.

## Sources

- https://alexcloudstar.com/blog/server-sent-events-vs-websockets-2026/ — when SSE wins vs WS (2026)
- https://dev.to/deepak_mishra_35863517037/modern-alternatives-flask-socketio-vs-fastapi-and-quart-5gh6 — Flask-SocketIO greenlet/WSGI overhead
- https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events — SSE + EventSource
- https://developer.mozilla.org/en-US/docs/Web/API/PointerEvent — Pointer Events (pressure, pointerId, timeStamp)
- https://developer.mozilla.org/en-US/docs/Web/API/PointerEvent/getCoalescedEvents — sub-frame swipe samples
- https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action — `touch-action:none` claims gestures
- https://www.magicbell.com/blog/pwa-ios-limitations-safari-support-complete-guide — iOS PWA limits 2026 (no Fullscreen API, standalone, evictions)
- https://jsonlines.org/ — JSONL append-only log format
- https://docs.ultralytics.com/datasets/detect/ — YOLO `cls cx cy w h` label format

## Open questions / follow-ups

- Public-port auth + HTTPS for a robot-driving endpoint → own it in .
- Swipe scoring: path similarity (Fréchet/DTW) vs endpoint-only — needed before any swipe RL.
- Does Safari `getCoalescedEvents` give >1 sample/frame for *touch* (vs Chromium's stylus cap)? Measure on-device.
