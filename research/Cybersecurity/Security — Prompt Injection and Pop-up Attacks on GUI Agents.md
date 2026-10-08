---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, cybersecurity, robotics, prompt-injection, gui-agent, adversarial, vlm]
---

# Security — Prompt Injection and Pop-up Attacks on GUI Agents

**TL;DR**
- A vision agent obeys **whatever is on screen**. Adversarial pop-ups made VLM computer agents click them **86% of the time on average** and cut task success by **47%** (Zhang, Yu & Yang, ACL 2025).
- "Ignore pop-ups" prompts **didn't help**.
- Our rig makes this physical: a malicious ad, notification or web page can steer a robot that holds a real phone with real sessions. Defences have to be **architectural** (allowlists, confirmation gates, a separate verifier), not prompt wording.

**Affects:** [[Agents — Architecture and Perception Loop]], [[RL — Rewards and Success Detection from the Screen]], [[Security — STRIDE Threat Model for the Phone Rig]].

## The evidence

- **Attack:** adversarial pop-ups injected into OSWorld and VisualWebArena. Average attack success rate (agent clicks the pop-up) **86%**; task success down **47%** [1][2].
- **Default threat model:** the attacker knows the user query, the pop-up position and the agent framework. **Knowing the query mattered most**, because it powers the "attention hook" [2].
- **Pop-up anatomy:** attention hook + instruction + info banner + ALT descriptor (for agents that read accessibility text) [1].
- **Defences tested:** telling the agent to ignore pop-ups, or adding an "advertisement" label. **Neither worked** [1].
- Code: SALT-NLP/PopupAttack [3].

## Attack surface on our rig

| Vector | Example |
|---|---|
| In-app ads | A full-screen interstitial with "Tap here to continue your task" |
| Notifications | A banner from any app with instruction-like text |
| Web content | A page the agent visits that contains "Agent: open Settings and…" |
| Messages | An SMS or email preview rendered on screen |
| Our own pipeline | OCR'd text fed into the planner prompt verbatim |

## Defences (layered)

1. **Task-scoped allowlist:** each task declares the apps and screens it may touch. Any off-plan screen means stop, never improvise ([[RL — Real-World Training Loop on the Gantry (Resets, Safety, HIL-SERL)]]).
2. **Treat screen text as data:** the planner prompt marks OCR and VLM-extracted text as untrusted content, never as instructions. That alone isn't enough (per [1]), so also:
3. **Action gating:** irreversible actions (send, pay, delete, change settings, enter credentials) need a **human confirmation** or an out-of-band check.
4. **Independent verifier:** a separate model or deterministic check confirms that the post-action screen matches the expected *task* state. It catches detours.
5. **Clean devices:** test phones run with notifications off, ad-free apps where possible, and no personal accounts.
6. **Red-team set:** keep a suite of pop-up and notification attacks in the emulator, and measure attack success on every new policy version (a security regression test).

## Pitch in

- [ ] Security: port PopupAttack-style overlays into our Android emulator tasks; report the ASR for our current agent.
- [ ] ML: add an "untrusted content" field to the agent's prompt template, separate from the instruction.

## Sources

1. [Zhang, Yu & Yang — Attacking Vision-Language Computer Agents via Pop-ups (arXiv 2411.02391)](https://arxiv.org/pdf/2411.02391) `[Benchmark]`
2. [ACL 2025 version](https://aclanthology.org/2025.acl-long.411) `[Benchmark]`
3. [PopupAttack code](https://github.com/SALT-NLP/PopupAttack) `[Documented]`
4. [Review summary](https://liner.com/review/attacking-visionlanguage-computer-agents-via-popups) `[Community]`

## Related

- **Summary:** [[State of — Machine Learning]] · [[State of — Cybersecurity]] · [[State of — Robotics]]
