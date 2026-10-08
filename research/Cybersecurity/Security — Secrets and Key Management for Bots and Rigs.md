---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [cybersecurity, robotics, ml-and-sports-markets, secrets, sops, age, push-protection, key-management]
---

# Security — Secrets and Key Management for Bots and Rigs

**TL;DR**
- We'll accumulate secrets: API keys, a Polymarket signing wallet, app test logins, host credentials, tunnel tokens.
- Layer them: **SOPS + age** for any secret that must live in the repo (encrypted values, readable structure); a **pre-commit scanner**; **GitHub push protection**; the same checks **in CI**.
- Signing keys for anything holding money stay in a **hardware wallet or vault**, never in a file on the rig host.

**Builds on:** the repo `.gitignore`, which already blocks `.env`, `*.key`, `*.sops.yaml` and `*.age` (from the original charter), and [[Markets — Polymarket Order Book, Fees and Execution]] (wallet).

## Layers

| Layer | Tool | Catches | Gap |
|---|---|---|---|
| Encrypt at rest | **SOPS + age** | Secrets committed *on purpose*: values encrypted, YAML structure readable, diffs still reviewable [1][2] | The age private key itself must never be committed. Back it up in a password manager [2] |
| Recipient control | `.sops.yaml` creation rules; `sops updatekeys` to rotate people in or out [2] | Who can decrypt | Re-encrypt when someone leaves the group |
| Pre-commit | gitleaks (or a SOPS-metadata check) | High-entropy strings and known key patterns before they're committed | Hooks can be skipped; a metadata grep only proves the file *has* SOPS headers [1] |
| Push time | **GitHub push protection** | Known token formats; on by default for public repos; bypasses create alerts and audit entries [3][4] | Known formats only, so custom secrets need custom patterns [3] |
| CI | Same scans on every PR | Machines without hooks | — |

Note that our `.gitignore` currently blocks `*.sops.yaml`. If we adopt SOPS, change that so *encrypted* files are allowed, and block only plaintext names.

## Key classes and where they live

| Secret | Storage | Why |
|---|---|---|
| Polymarket / wallet signing key | Hardware wallet or a dedicated vault; host gets **scoped API credentials** only | Money; EIP-712 orders can be signed without exporting the key |
| Exchange/data API keys | SOPS-encrypted `secrets.sops.yaml`, decrypted into env at runtime | Shared across the group, rotatable |
| Test-phone Apple ID / app logins | Password manager; **never** typed by the agent from a file | The agent could leak them through screenshots or logs |
| Rig host SSH / tunnel tokens | Per-person keys; no shared accounts | Accountability (the "repudiation" leg of STRIDE) |

## Logging hygiene

Screenshots and OCR logs can capture secrets on screen. Blur known credential fields before writing datasets, and keep `captures/` and `datasets/` out of git (already ignored).

## Pitch in

- [ ] Security: add a gitleaks pre-commit config and a CI job; enable push protection on the repo.
- [ ] Decide as a group whether any secret goes in the repo at all, or everything stays in a password manager.

## Sources

1. [OneUptime — SOPS with git on Ubuntu](https://oneuptime.com/blog/post/2026-03-02-how-to-use-sops-with-git-on-ubuntu-for-secret-management/markdown) `[Community]`
2. [GitOps secrets with SOPS + age (DEV)](https://dev.to/lyraalishaikh/gitops-secrets-on-linux-with-sops-age-encrypted-configs-clean-deploys-1nek) `[Community]`
3. [GitHub Docs — secret scanning and push protection](https://docs.github.com/en/code-security/secret-scanning/working-with-secret-scanning-and-push-protection) `[Documented]`
4. [The Hacker News — default push protection for public repos](https://thehackernews.com/2024/03/github-rolls-out-default-secret.html) `[Documented]`

## Related

- **Summary:** [[State of — Cybersecurity]] · [[State of — Robotics]] · [[State of — ML and Sports Markets]]
