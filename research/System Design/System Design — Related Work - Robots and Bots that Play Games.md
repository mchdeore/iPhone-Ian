---
type: research
status: answered
author: marc
date: 2026-10-07
tags: [system-design, robotics, cybersecurity, prior-art, game-bots, poker]
---

# System Design — Related Work: Robots and Bots that Play Games

**TL;DR**
- Three neighbouring fields: **(1) physical device-testing robots** (Tapster), **(2) software screen-reading game bots** (emulator + OpenCV), and **(3) physical robots playing board games**.
- Almost nobody combines a physical robot with a vision agent on a phone. That's our niche ([[Prior Art — Touchscreen Robots and Software Agents]]).
- Real-money online poker is the one area to avoid: operators ban real-time assistance and bots outright, confiscate funds, and run dedicated detection teams.

## 1. Physical device-testing robots

- **TapsterBot** (Jason Huggins, creator of Selenium): open-source BSD delta robot for mobile testing; Arduino + 3 servos + printed parts, ~€250; driven by a Node.js server, with Appium integration and Robot Framework keywords (taps, swipes, stress gestures) [1][2][3]. It grew out of an earlier **belt-driven Cartesian** design (BitBeam Bot); the delta was chosen for speed and simplicity, but deltas are harder to make precise [1][3]. Tapster 2 is retired from sale; the designs stay open [3].
- **TestDevLab** built its own robot for automated "manual" mobile testing [4].
- **Lesson:** the testing world solved tap and swipe actuation a decade ago. What's new for us is the **vision agent and game brain** on top.

## 2. Software game bots (no robot)

- Commercial bot services run games in **Android emulators** with **OpenCV image recognition + scripted decisions** [5]. That's the same perception → decision loop, minus the physical layer.
- A pending patent, CA3167360A1 "Mobile gaming bot and system", mentions a robot, user actions and optical sensors (only metadata seen) [6].
- **Our previously cited "BrainyBot/TappingBot"** (CV robot tapping phone games, in [[Agents — VLM GUI Agents and Vision Grounding Survey]]) **could not be re-verified** in this search. Treat it as unconfirmed until someone checks the repo.

## 3. Physical robots playing board games

- Student and academic projects combine CV + AI + a robot arm for board games (e.g. an HKU Chinese Checkers robot arm) [7]. The same architecture applies, but they manipulate physical pieces rather than a screen.

## 4. Where not to go: real-money online card rooms

- **PokerStars:** zero tolerance for real-time assistance (RTA), permanent bans; detection uses behavioural indicators, including "perfect GTO" play or solver use only at critical moments, across billions of hands [8][9].
- **GGPoker:** bans any external tool that gives an edge or influences decisions in real time, *including charts*; penalties include permanent bans and **confiscation of funds**. 31 accounts were blocked in Feb 2025 with GTO Wizard's Fair Play Check, and 40+ high-stakes accounts banned with $1.2M+ confiscated in 2020 [10][11][12].
- **Why it's out of scope:** in multiplayer real-money games a bot takes money from other people. It's cheating, not research. Our card work targets single-player, offline and play-money games, plus our own apps.

## Pitch in

- [ ] Anyone: check the DeMaCS-UNICAL/TappingBot repo; update the VLM survey note if it's real, or remove the claim.
- [ ] Robotics: read the TapsterBot calibration code; borrow anything useful for our calibration.

## Sources

1. [QCon NY 2013 — Tapster talk](https://qconnewyork.com/ny2013/node/333.html) `[Documented]`
2. [TapsterBot wiki — Robot Framework keywords](https://github.com/pylapp/tapsterbot/wiki/07-%5C--Drive-the-robot:-Robot-Framework-keywords) `[Documented]`
3. [Tapster — Robot as a Service](https://write.as/pylapp/tag:tests) · [Tindie — Tapster](https://blog.tindie.com/2016/09/tapster-manipulates-phone-automatically) · [SlideShare deck](https://www.slideshare.net/slideshow/dont-fear-our-new-robot-overlords-a-new-way-to-test-on-mobile/37275458) `[Community]`
4. [TestDevLab — testing robot](https://www.testdevlab.com/blog/how-we-built-a-robot-for-automated-manual-mobile-testing) `[Community]`
5. [AI-powered bots in casual mobile gaming (press release)](https://business.minstercommunitypost.com/minstercommunitypost/article/abnewswire-2025-12-1-how-ai-powered-bots-are-quietly-reshaping-even-casual-mobile-gaming) `[Community]`
6. [CA3167360A1 — Mobile gaming bot (Google Patents)](https://patents.google.com/patent/CA3167360A1/en) `[Documented]`
7. [HKU FYP — Chinese Checkers robot](https://wp2024.cs.hku.hk/fyp24057/wp-content/uploads/sites/58/2025/05/Fyp_Final_Report_2.pdf) `[Community]`
8. [PokerNews — PokerStars vs RTA](https://www.pokernews.com/news/2023/10/pokerstars-battle-against-real-time-assistance-44628.htm) `[Documented]`
9. [Pokerfuse — inside PokerStars' RTA arsenal](https://pokerfuse.com/news/poker-room-news/219952-inside-pokerstars-arsenal-how-it-combats-rta/) · [PokerNews — how PokerStars deals with bots](https://www.pokernews.com/news/2020/04/how-does-pokerstars-deal-with-bots-37068.htm) `[Documented]`
10. [PokerNews — GGPoker × GTO Wizard](https://www.pokernews.com/news/2025/03/ggpoker-and-gto-wizard-team-up-to-keep-poker-fair-48110.htm) `[Documented]`
11. [Pokerfuse — GGPoker reimburses 4,000+ players](https://pokerfuse.com/news/poker-room-news/211765-ggpoker-reimburses-over-4000-players-following-recent-rta/) `[Documented]`
12. [PokerNews — Fedor Holz on WSOP bans](https://www.pokernews.com/news/2025/03/fedor-holz-hints-at-wsop-bans-for-ggpoker-rule-breakers-48061.htm) `[Documented]`

## Related

- **Summary:** [[State of — System Design]] · [[State of — Robotics]] · [[State of — Cybersecurity]]
- **See also:** [[Betting Apps — Behavioral and Automation Detection]] · [[Game Theory — Poker AI Milestones (Cepheus to Pluribus)]]
