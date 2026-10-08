---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, rl-and-simple-robots, grpo, ppo, lora, trl, unsloth]
---

# RL — GRPO in Practice on Small GPUs

**TL;DR**
- GRPO is PPO **without the critic**: sample a *group* of rollouts for the same prompt and use each one's reward relative to the group mean as its advantage. Dropping the value model is what makes RL fit on consumer GPUs.
- TRL's `GRPOTrainer` takes a LoRA `peft_config`, and Unsloth advertises vision GRPO for Qwen2.5-VL-7B on a free Colab T4.
- For GUI tasks a "prompt" is a screen plus instruction, and the group is N alternative action sequences from the same start state. That needs **resettable environments**, which emulators provide.

**Builds on:** [[RL — Training GUI Agents with RL (DigiRL to MobileRL)]] (MobileRL's Difficulty-Adaptive GRPO reached 80.2% on AndroidWorld).

## How GRPO works

1. For a prompt, sample G completions (rollouts).
2. Score each with the reward function.
3. Advantage = (r_i − mean(r)) / std(r) within the group, so no learned critic is needed.
4. Run a PPO-style clipped update with a KL penalty to the reference model.

DeepSeekMath introduced it: "foregoes the critic model, instead estimating the baseline from group scores, significantly reducing training resources" [1]. TRL documents the same memory trade-off [2].

## Running it

- **TRL:** `GRPOTrainer(model, reward_funcs=[...], args=GRPOConfig(num_generations=G, max_prompt_length=..., max_completion_length=...), peft_config=LoraConfig(...))` [2][3]. The documented examples are text models; VLM image handling depends on the TRL version, so check the release notes [2].
- **Unsloth vision RL** (Aug 2025): GRPO for Qwen2.5-VL, with the 7B example on a free Colab T4, and claimed ~90% less VRAM than FlashAttention-2 setups (vendor claim) [4].
- **Memory levers, in order:** a smaller G (4–8), shorter completions (actions are short JSON, so cap at ~64 tokens), lower image resolution, 4-bit base + LoRA r=16, gradient checkpointing.

## GUI-specific design

- **Reward functions:** `app_truth` (target hit from the Flask app), format validity (parseable action), a step penalty (MobileRL's shortest-path idea).
- **Single-step vs multi-step:** start with **single-step GRPO** (one screen → one action, reward = correct element). It needs no environment resets and is just supervised data plus a reward. Go multi-step only once the emulator farm exists.
- **Difficulty filtering:** drop prompts where all G rollouts succeed or all fail, since their advantage is zero and they waste compute (the MobileRL insight).

## Pitch in

- [ ] ML: single-step GRPO on Flask-app screenshots with `app_truth` reward; compare with the SFT baseline at an equal GPU-hour budget.

## Sources

1. [DeepSeekMath — GRPO (arXiv 2402.03300)](https://arxiv.org/html/2402.03300v3) `[Benchmark]`
2. [TRL GRPO trainer docs](https://www.mintlify.com/huggingface/trl/grpo-trainer) · [TRL quickstart](https://huggingface.co/docs/trl/v1.9.0/quickstart) `[Documented]`
3. [Training with GRPOTrainer (Diehl)](https://www.stephendiehl.com/posts/grpotrainer/) · [HF LLM course — GRPO](https://huggingface.co/learn/llm-course/chapter12/3b) `[Community]`
4. [Unsloth — vision RL](https://unsloth.ai/blog/vision-rl) `[Documented]` (vendor)
5. [MobileRL (arXiv 2509.18119)](https://arxiv.org/html/2509.18119v2) `[Benchmark]`

## Related

- **Summary:** [[State of — Machine Learning]] · [[State of — RL and Simple Robots]]
