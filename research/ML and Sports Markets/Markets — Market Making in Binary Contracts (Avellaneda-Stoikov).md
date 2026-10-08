---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [machine-learning, ml-and-sports-markets, market-making, avellaneda-stoikov, inventory-risk, polymarket]
---

# Markets — Market Making in Binary Contracts (Avellaneda-Stoikov)

**TL;DR**
- Being the maker avoids fees and earns rebates ([[Markets — Polymarket Order Book, Fees and Execution]]). It also needs an inventory model, or "market making" quietly becomes a directional bet.
- **Avellaneda–Stoikov (AS)** gives a reservation price and spread that skew quotes against your inventory.
- For binary contracts it needs changes: prices bounded in [0, 1], **Bernoulli variance** instead of volatility, and a **terminal penalty** because inventory settles at exactly 0 or 1. A Polymarket thesis that did this reported ~155 USDC per market on its test set.

## Classical AS in one paragraph

A market maker quotes around a **reservation price** r = mid − q·γ·σ²·(T − t), where q is inventory, γ risk aversion, σ volatility and T − t time left. It quotes a spread that widens with γ, σ and order-arrival intensity. Long inventory → lower quotes to sell it off [1][2].

## Why binary contracts break it

- Prices live in [0, 1] and **snap to 0 or 1 at settlement**. As resolution nears, the market goes one-sided, so inventory has to be managed more aggressively than in classical markets [3].
- Feil & Nendel model the price as a conditional probability driven by a latent belief diffusion. The maker maximises terminal wealth while controlling **both mark-to-market and settlement risk**: "fundamentally different" from classical settings [4].

## The Polymarket adaptation (Comillas thesis)

- Prices bounded to [0, 1]; **Bernoulli variance p(1 − p)** replaces historical volatility; **normalised inventory**; **terminal risk penalty** for settlement [5].
- Goal: earn the spread "without becoming a hidden directional bet", not forecast outcomes [5].
- Result: ~**155 USDC per market** on the test set; CVaR showed sensitivity to tail events and the small sample [5].

## For in-play tennis

- **Variance isn't smooth.** p jumps on every point, and jumps are largest on high-importance points ([[Markets — Point Importance and Leverage in Tennis]]). Scale the spread with **point importance**, not a constant σ.
- **Adverse selection:** pull or widen quotes the instant a point ends, until the feed confirms the new score. Faster participants pick off stale quotes.
- **Combine with the fade:** skew the reservation price toward the *model's* fair value instead of the mid. That's market making with a view, which is the natural form for an edge-holder.
- **RL extension:** a 2026 paper keeps AS's HJB structure but lets the market state pick the AS parameters [6]. That's a sensible small RL problem for a simulator ([[Markets — In-Play Entry, Exit and Sequential Decisions]]).

## Pitch in

- [ ] ML: implement binary-AS on recorded tennis books (paper trading); measure spread capture vs adverse selection by point type.

## Sources

1. [Hummingbot — AS strategy deep dive](https://hummingbot.org/blog/technical-deep-dive-into-the-avellaneda--stoikov-strategy/) `[Community]`
2. [RL to improve AS market making (PMC9767337)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9767337/) · [Guéant et al. — inventory risk (arXiv 1105.3115)](https://arxiv.org/pdf/1105.3115) `[Benchmark]`
3. [Prediction market making guide](https://newyorkcityservers.com/blog/prediction-market-making-guide) `[Community]`
4. [Feil & Nendel — Optimal market making in prediction markets (arXiv 2607.17991)](https://arxiv.org/pdf/2607.17991) `[Benchmark]`
5. [Comillas thesis — AS on Polymarket](https://repositorio.comillas.edu/jspui/handle/11531/109133) `[Benchmark]`
6. [Zero-shot adaptation to order book dynamics (arXiv 2605.21707)](https://arxiv.org/pdf/2605.21707) `[Benchmark]`

## Related

- **Summary:** [[State of — Machine Learning]] · [[State of — ML and Sports Markets]]
