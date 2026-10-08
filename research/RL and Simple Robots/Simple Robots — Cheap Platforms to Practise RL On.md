---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, robotics, rl-and-simple-robots, simple-robots, so-101, lerobot, microduck, open-duck-mini, petoi, reachy-mini, education]
---

# Simple Robots — Cheap Platforms to Practise RL On

**TL;DR**
- There's a sub-$500 tier of robots built for learning-based control.
- For this group, the **SO-101 arm** is the best buy: printable on the printers we already own, native to LeRobot (BC, ACT, SmolVLA, HIL-SERL), and the same data pipeline as the phone rig.
- For locomotion RL, the **Open Duck Mini** (DIY, <$400 BOM) or **Microduck** ($399, pre-order) are purpose-built for it.

**Useful for:** anyone in the group wanting hands-on RL without waiting for the phone rig. It also gives a shared hardware platform for the ML and robotics people.

## Options

| Robot | Price (USD) | Learning angle | Fit for us |
|---|---|---|---|
| **SO-101 arm** (LeRobot) | ~$250 per arm; a leader + follower pair is needed for teleop; assembled pairs ~$200–400 vary by vendor | Imitation (ACT, SmolVLA), real-world RL (HIL-SERL) | ★★★ 3D-printable structure, so we only buy servos and a controller. Same LeRobot format as the rig ([[RL — Imitation Learning from Logged Taps (BC, ACT, LeRobot)]]) |
| **Open Duck Mini** | <$400 BOM, DIY | RL-trained gait (sim → real) | ★★ The best sim-to-real locomotion project to copy |
| **Microduck** (Hugging Face/Pollen) | $399, pre-order (shipping planned around Christmas 2026) | Marketed as teachable by RL; 7 behaviours trained out of the box | ★★ Easiest RL biped, if it ships on time |
| **Petoi Bittle** | ~$289–309 | Open-source quadruped; gait learning | ★ Fun, small community for RL |
| **Reachy Mini** | ~$299–499 by configuration | Interaction: voice and vision, not locomotion | ★ Good for VLM agent demos, weak for RL |
| **Duckiebot / DonkeyCar** | Price not confirmed | Classic autonomous-driving RL courses | ★ Check official stores |

Prices vary between sources; check the vendor before buying. `[Community]`

## Suggested group plan

1. **Group-print one SO-101 pair.** Split the servo cost, the same way the gantry budget is split.
2. Follow the LeRobot tutorial: teleop → 50 demos → ACT → HIL-SERL. Everyone learns the pipeline once.
3. Reuse it for the phone rig: an SO-101 holding a stylus is a *second* actuation design, useful as a comparison for [[Touch Telemetry — Measuring What the Rig Emits]].

## Pitch in

- [ ] Robotics: price the SO-101 servo BOM in CAD and add sourcing columns, like Aria's parts list.
- [ ] Anyone: pick a first task (pick-and-place, or "tap a phone button") and own its demo dataset.

## Sources

- [Microduck pricing](https://www.eesel.ai/blog/microduck-pricing) · [Microduck alternatives (2026)](https://www.eesel.ai/blog/microduck-alternatives) · [Axios — Microduck](https://axios.com/2026/08/27/hugging-face-debuts-microduck-a-399-robot) `[Community]`
- [ThinkRobotics SO-101 review](https://thinkrobotics.com/blogs/product-reviews-buying-guides/thinkrobotics-lerobot-so-101-6-axis-robotic-arm-review-ai-ready-open-source-and-built-for-learning) · [Seeed — LeRobot SO-100M](https://wiki.seeedstudio.com/lerobot_so100m_new/) · [Robotic arm builds 2026](https://dupple.com/blog/how-to-make-a-robotic-arm) `[Community]`

## Related

- **Summary:** [[State of — Machine Learning]] · [[State of — Robotics]] · [[State of — RL and Simple Robots]]
