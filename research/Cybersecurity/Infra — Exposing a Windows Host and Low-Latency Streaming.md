---
type: research
status: answered
author: marc
date: 2026-10-05
tags: [cybersecurity, robotics, networking, security, windows, streaming, infrastructure, yolo]
---

# 14 — Exposing a Windows robot host + low-latency streaming

## Question

How does an off-LAN machine (the CPU-only trainer from `03`, a remote agent, or an
operator) exchange a constant, low-latency stream — camera frames one way, tap/move
commands the other — with the **Windows** robot host, safely and with minimal setup?
Extends the host/agent/motion split in `specs/02-firmware-and-software.md` §4/§7/§9.

Tags: `[Documented]` official docs · `[Benchmark]` measured · `[Community]` forum/anecdotal.

## TL;DR — you probably don't need a public port

Both endpoints are **yours**, so the lazy-correct answer is a private mesh, not an
open port. Put **Tailscale** on the robot host and the trainer/agent box: you get a
WireGuard-encrypted, NAT-traversed, peer-to-peer link with **zero port-forwards, zero
firewall rules, zero TLS certs, and no CDN/ToS limits** — at full LAN-ish bandwidth
for the camera stream. A truly *public* port is only needed if an **un-trusted,
non-Tailscale client** must connect (e.g. sharing to someone who can't install
anything). `ponytail:` ceiling = everyone who needs in can run Tailscale; upgrade
path is Funnel/Cloudflare below. The iPhone flash app (`02`) is served on the **LAN**
and never needs public exposure.

## Option comparison

| Option | Opens a port? | Auth | Good for a video stream? | Effort / risk |
|---|---|---|---|---|
| **Tailscale tailnet** ⭐ | No | Device auth + ACLs (default-deny) | **Yes** — direct P2P WireGuard, full BW `[Community]` | Lowest; installs as a Win service |
| Tailscale **Funnel** | No (relayed) | Public ingress; auth is on *you* | Weakly — relayed via DERP, **ports 443/8443/10000 only**, fair-use BW `[Documented]/[Community]` | Low; for public web entry only |
| **Cloudflare Tunnel** (`cloudflared`) | No (outbound) | **Cloudflare Access** (SSO, service token, mTLS) `[Documented]` | **ToS risk** — serving video/large files over the CDN is restricted off Enterprise `[Documented]` | Low–med; WS fully supported `[Documented]` |
| **WireGuard** (raw) | UDP port-forward (or cloud relay) | Static keys | Yes, if you solve NAT yourself | Med; Tailscale *is* this, automated |
| **ngrok** | No (agent) | Token / OAuth add-on | **No** — free = **1 GB/mo** out, kills a constant stream `[Documented]` | Low but capped; interstitial on free |
| Router **port-forward** + Caddy + `New-NetFirewallRule` | **Yes (inbound)** | Whatever you build (TLS + token/mTLS) | Yes | **Highest attack surface**; you own patching/DDoS |

Notes: ngrok free is **1 GB/month out, 20k HTTP req/mo, 3 endpoints, random dev URL,
no session timeout** — a ~1 Mbps camera feed (~450 MB/hr) exhausts it in ~2 h.
`[Documented]` Cloudflare Tunnel **"has full support for Websockets"** `[Documented]`,
but Cloudflare still reserves the right to throttle/redirect **video or a
disproportionate amount of non-HTML content** served over its CDN on Free/Pro/Business
(the old "Section 2.8" rule survived the 2026 ToS rewrite). `[Documented]` Tailscale
**Funnel listens only on 443/8443/10000** and relays through DERP — fine for a control
UI, not for heavy sustained video. `[Documented]/[Community]`

## Never expose these (fail-closed)

- **Raw GRBL / USB serial** — it is a local USB device; it must **never** be a network
 socket. The agent talks serial locally; only the agent's high-level API crosses the
 wire (`specs/02` §4 contract: `move/tap/swipe/type`). `[Documented]`
- **Flask dev server** — Flask's own docs: not for production/exposure. Run behind
 **waitress** (pure-Python, Windows-friendly WSGI) and bind to `127.0.0.1`/`tailscale0`
 only; let the VPN/tunnel be the sole ingress. `[Documented]`
- Bind every service to loopback or the tailnet interface, not `0.0.0.0`.
- Credential vault (`specs/02` §9) stays host-side; never reachable over the stream API.

## Streaming transport

Glass-to-glass latency context: HLS 20–30 s, LL-HLS 2–5 s, **WebRTC 200–500 ms**
(public) / **sub-200 ms** on a good link; most of the budget is the **camera + USB
bus (~100 ms)**, not the protocol. `[Benchmark]/[Documented]`

| Transport | G2G (LAN/good link) | Verdict for this rig |
|---|---|---|
| **WebRTC** (`aiortc`, Python) ⭐ | ~100–200 ms `[Benchmark]` | Best video path: UDP, adaptive bitrate, **congestion control = built-in backpressure**, DTLS-SRTP encryption, P2P (bypasses any CDN). Dominant Py lib = aiortc. |
| **MJPEG over HTTP** | ~60–120 ms LAN `[Benchmark]` | Dead-simple, OpenCV-native. But intra-frame only → **bitrate scales linearly with fps**, bandwidth-heavy; over TCP it **falls behind then jumps** under congestion. `[Community]` |
| **JPEG over WebSocket** | ≈ MJPEG | Same cost as MJPEG, but you control framing, can **drop old frames**, and carry commands on the *same* socket. Lazy robust default. |
| **gRPC** (HTTP/2 stream) | low | Great for the **command/telemetry** channel (typed, binary, multiplexed); not a media-optimized path. |
| **ZeroMQ** (PUB/SUB, PUSH/PULL) | lowest on LAN | Minimal overhead; `ZMQ_CONFLATE` **drops stale frames natively**. No TLS/auth by default, not browser-friendly → keep it *inside* the tunnel only. |

JPEG quality/resolution: crop to the screen region first (same win as `02`/`03`),
send **grayscale or Q≈60–75 JPEG at the detector's `imgsz` (640)** — the YOLO model
doesn't need 1080p, so encode at inference resolution and cut bandwidth 5–10×.

### Backpressure (drop old frames)

The agent wants the **newest** frame, never a backlog. Enforce a **queue of depth 1,
drop-oldest** on the sender. WebRTC/`aiortc` does congestion control for you (but can
still accumulate delay if you push frames faster than it encodes — see aiortc disc.
#1238). ZeroMQ: `ZMQ_CONFLATE=1`. MJPEG/WebSocket: explicitly discard the previous
frame if the send buffer isn't drained. `[Community]`

## Running it 24/7 on Windows

- **As a service:** wrap the Python app with **NSSM** — `nssm install robotstream
 python app.py`, then `AppExit Default Restart`, `AppThrottle`, `AppStdout/AppStderr`
 logs. `[Community]` Caddy/`cloudflared`/Tailscale can run the same way; `cloudflared`
 and Tailscale ship **native service installers** (`cloudflared service install`,
 Tailscale auto-registers `tailscaled`). `sc.exe failure` sets restart actions if you
 skip NSSM. `[Documented]`
- **Watchdog:** a scheduled task every N min that hits a `/health` endpoint and
 `Restart-Service` on failure — covers hangs NSSM won't catch.
- **Keep it awake:** `powercfg /change standby-timeout-ac 0`, `hibernate-timeout-ac 0`,
 `monitor-timeout-ac 0`; **disable USB selective suspend** (else the webcam / GRBL
 serial drop out). A service process can also hold `SetThreadExecutionState`. `[Documented]`
- **Windows Update reboots:** set **Active Hours** + enable **"No auto-restart with
 logged on users for scheduled automatic updates installations"** (gpedit → Windows
 Update, or `HKLM\...\WindowsUpdate\AU\NoAutoRebootWithLoggedOnUsers=1`). Active Hours
 caps at 18 h; for 24/7 use the **rolling-active-hours scheduled task** that rewrites
 `ActiveHoursStart/End` hourly. `[Documented]/[Community]` Expect occasional forced
 reboots anyway → set all services **Automatic (Delayed Start)** so the rig self-heals.

## Default architecture — exact steps

1. **Install Tailscale** on robot host + trainer/agent; sign both into one tailnet
  (auto-starts as a Windows service).
2. **Lock the ACL:** default-deny; allow only `trainer → robot:<stream port>`. Turn on
  device approval; disable key-expiry for these two nodes (or script re-auth).
3. **Bind to loopback/tailnet only:** Flask-under-waitress for the flash app (LAN);
  stream server on the tailscale interface. GRBL stays on USB serial.
4. **Video:** `aiortc` WebRTC track for frames; **commands over a WebRTC datachannel**
  (or a parallel WebSocket) — both over the tailnet, so no public exposure. Depth-1
  drop-old-frames queue; encode cropped Q≈70 JPEG/VP8 at `imgsz` 640.
5. **Service-ify** the Python app with NSSM (restart-on-exit + logs). Add the `/health`
  watchdog task.
6. **powercfg** timeouts → 0 on AC; USB selective suspend off.
7. **Windows Update:** Active Hours + no-auto-restart policy (or rolling task); services
  Automatic.
8. **Only if a non-Tailscale public client is required:** add **Cloudflare Tunnel +
  Access** (service token / mTLS) for the control UI — but **keep video on WebRTC P2P**
  and route only signaling/commands through the tunnel, dodging the CDN video ToS.
  Tailscale **Funnel** is the simpler alternative for a quick public 443 web entry.

## Key takeaways

- Default = **Tailscale private mesh**, no public port, full bandwidth, WireGuard+ACL. ⭐
- Public ingress only for un-trusted clients → **Cloudflare Tunnel + Access**; never
 stream heavy video *through the CDN* (ToS) — keep media on **WebRTC P2P**.
- **ngrok free (1 GB/mo)** and **Tailscale Funnel (443/8443/10000, relayed)** can't carry
 a constant camera feed; port-forward + Caddy is the highest-risk last resort.
- Transport: **WebRTC** for sub-200 ms adaptive video (backpressure built-in); JPEG/WS
 or ZeroMQ-CONFLATE as the lazy drop-old-frames path; gRPC/WS for commands.
- Never expose raw GRBL serial or the Flask dev server; bind to loopback/tailnet.
- On Windows: NSSM service + watchdog, `powercfg` no-sleep + USB-suspend off, and tame
 Windows Update reboots (Active Hours + no-auto-restart; Automatic services self-heal).

## Sources

- https://tailscale.com/kb/1223/funnel/ — Funnel overview `[Documented]`
- https://www.ssdnodes.com/learn/tailscale-funnel-limits-and-ports — Funnel ports/limits/bandwidth `[Community]`
- https://developers.cloudflare.com/cloudflare-one/faq/cloudflare-tunnels-faq/ — "full support for Websockets" `[Documented]`
- https://blog.cloudflare.com/updated-tos — 2026 ToS rewrite (video-over-CDN restriction persists) `[Documented]`
- https://support.cloudflare.com/hc/en-us/articles/360057976851-Delivering-Videos-with-Cloudflare/ — video/large-file redirect on Free/Pro/Business `[Documented]`
- https://ngrok.com/docs/pricing-limits/free-plan-limits — 1 GB/mo out, 20k req, 3 endpoints, no timeout `[Documented]`
- https://fictionlab.pl/blog/webrtc-on-robots-how-to-stream-live-video-from-your-rover-to-any-browser/ — sub-200 ms g2g on robots `[Benchmark]`
- https://discourse.openrobotics.org/t/where-does-latency-in-webrtc-video-streaming-come-from-an-analysis/54566 — latency is mostly camera+USB `[Benchmark]`
- https://github.com/aiortc/aiortc — Python WebRTC; disc. #1238 delay build-up `[Community]`
- https://github.com/kig/raspivid_mjpeg_server — MJPEG ~120 ms g2g over WiFi `[Benchmark]`
- https://www.forasoft.com/learn/video-streaming/articles-streaming/latency-glass-to-glass-explained — HLS/LL-HLS/WebRTC latency bands `[Documented]`
- https://caddy.community/t/caddy-as-an-nssm-service/11758 — Caddy via NSSM on Windows `[Community]`
- https://caddyserver.com/docs/automatic-https — Caddy automatic TLS `[Documented]`
- https://learn.microsoft.com/en-us/windows/deployment/update/waas-restart — manage update restarts `[Documented]`
- https://techcommunity.microsoft.com/discussions/windows11/how-to-prevent-all-windows-11-auto-reboots-and-auto-shutdowns/4194463 — rolling Active Hours task `[Community]`

## Open questions / follow-ups

- Measure real g2g latency on *this* rig (WebRTC vs JPEG/WS) with the camera-sees-its-own-timestamp method before committing a transport.
- Does the trainer actually need live frames, or just a batched upload of captured datasets? If batch-only, drop streaming entirely → a `tailscale`-scoped `rsync`/HTTP pull. (Flag in `questions.md`.)
- Confirm Tailscale **direct** (not DERP-relayed) path holds through the home router (`tailscale ping`); if it falls back to DERP, video bandwidth suffers.
- If a public operator UI is ever needed, decide Cloudflare Access (SSO/mTLS) vs Tailscale Funnel + app-level token.
