---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, rl-and-simple-robots, curriculum, task-generation, zerogui, gui-agent]
---

# RL — Self-Generated Tasks and Curricula for GUI Agents

**TL;DR**
- The bottleneck for online GUI RL isn't compute but **tasks and rewards**: someone has to write "do X" and check it was done.
- **ZeroGUI** removes the human: a VLM proposes tasks from the current screen, and a **majority vote** of VLM judges scores them. That gave +63% relative (Aguvis-7B) and +14% (UI-TARS-7B) on OSWorld and AndroidLab.
- For us: generate tasks in emulators, filter them by difficulty, and only promote **verified** tasks to the rig.

**Builds on:** [[RL — Rewards and Success Detection from the Screen]] (voting judges) and [[RL — GRPO in Practice on Small GPUs]] (difficulty filtering).

## ZeroGUI in brief

- **Task generation:** the VLM sees a random initial screenshot plus task exemplars and proposes diverse new tasks [1][2].
- **Reward:** majority vote over several VLM evaluations of the trajectory screenshots [2].
- **Two stages:** online RL on generated tasks, then test-time adaptation on test-set tasks [1].
- Code and checkpoints are released (e.g. ZeroGUI-AndroidLab-7B) [3][4].

## Related idea: reverse synthesis

Explore first, then write the task that matches what happened. **OS-Genesis** is described as doing this (an unverified summary; read the paper before relying on it). Every trajectory becomes a correctly labelled task by construction, so there are no unsolvable tasks.

## Curriculum design for our pipeline

1. **Seed tasks** from the apps on the test phone (Settings, Notes, Clock, our Flask app). Write ~20 by hand.
2. **Expand** with ZeroGUI-style generation in Android emulators: ~10 variants per seed.
3. **Filter by difficulty:** keep tasks where the current policy succeeds 20–80% of the time. Tasks always solved or never solved give zero GRPO advantage.
4. **Verify:** promote a task to the "rig set" only if a deterministic check exists for its end state (no judge-only tasks on hardware).
5. **Refresh** every training round as the policy improves. That's the curriculum.

## Risks

- **Generated-task drift:** the generator proposes tasks the judge can "verify" but that are meaningless. Audit a random 5% by hand each round.
- **Safety:** generated tasks must respect the app allowlist (no payments, messaging or account changes). Filter them with a keyword and app blocklist before execution.

## Pitch in

- [ ] ML: run ZeroGUI's task generator on 3 Android apps; post 50 sample tasks plus a solvable/meaningful audit.

## Sources

1. [ZeroGUI (arXiv 2505.23762)](https://arxiv.org/pdf/2505.23762) `[Benchmark]`
2. [ZeroGUI review](https://liner.com/review/zerogui-automating-online-gui-learning-at-zero-human-cost) `[Community]`
3. [ZeroGUI code](https://github.com/OpenGVLab/ZeroGUI) `[Documented]`
4. [ZeroGUI-AndroidLab-7B checkpoint](https://huggingface.co/OpenGVLab/ZeroGUI-AndroidLab-7B) `[Documented]`
