# Track 5 — AI Agent Architecture: Notes (partial, software-analog only)

**Status:** Not directly researched for this project. Logging one adjacent finding from the prior pass as a reference point, since it's the closest existing precedent to "vision-based AI agent driving a phone."

**Source:** `../sources/android_control_research.md` §1.12.

---

## droidrun / mobilerun (closest existing software analog)

Open-source framework (2024–2026 era) wrapping Accessibility Service + ADB with an LLM-agent control loop. Installs an on-device "Portal" app running an accessibility service that exposes: (1) the UI accessibility tree, (2) screenshots, to a host-side agent. The agent reasons over this observed state (vision + structured tree) and issues taps/swipes/text-input/app-launch actions.

This is architecturally a **perception → planning → action loop** already implemented in software-only form — worth studying as a reference design for this project's Track 5 loop, even though this project's actuation layer is physical/mechanical rather than software-injected. The perception and planning halves (VLM/tree-grounding + action planning) are largely reusable regardless of whether the action layer is `dispatchGesture` or a physical stylus moving to XY coordinates.

Requirements: ADB + Developer Options for initial install, manual accessibility-service enable (subject to Android 15 Restricted Settings friction if sideloaded). No root.

https://github.com/droidrun/mobilerun · https://pypi.org/project/droidrun/

Related tools noted but not investigated: AppAgent, Mobile-Agent, and various "Android MCP server" wrappers — these appeared in search results as thin orchestration wrappers around ADB/UIAutomator2, not independent agent architectures. Flagged as unresearched.

## Gap

This track needs its own dedicated pass — the prior research was scoped to Android control mechanisms, not VLM/GUI-grounding model literature, prompting-vs-fine-tuning tradeoffs, or verification-loop design. Seed terms from the pipeline doc ("mobile GUI agent," "vision language mobile agent," "embodied mobile agent," "physical computer-use agent") were not searched.
