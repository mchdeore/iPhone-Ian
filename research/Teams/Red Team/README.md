# Red Team research

Red builds the pixel observer: detector, OCR, typed extraction and validated coordinates. Start with the existing scripted/native-inference baseline. Future training, fine-tuning and RL remain held. Gantry actuation requires measured calibration and an independently reviewed hardware gate.

These are additive links to existing notes. Their contents and original locations are preserved.

[Team hub](../README.md)

## Future training and optimization — held

- [Training — QLoRA Fine-Tuning a Small VLM on 12 GB](<../../Machine Learning/Training — QLoRA Fine-Tuning a Small VLM on 12 GB.md>)
- [YOLO — Detection Grouping and Class Taxonomy](<../../Machine Learning/YOLO/YOLO — Detection Grouping and Class Taxonomy.md>)
- [YOLO — Efficient Dataset Recipe](<../../Machine Learning/YOLO/YOLO — Efficient Dataset Recipe.md>)
- [YOLO — Efficient Training Strategy](<../../Machine Learning/YOLO/YOLO — Efficient Training Strategy.md>)
- [YOLO — Flask Closed-Loop Trainer App](<../../Machine Learning/YOLO/YOLO — Flask Closed-Loop Trainer App.md>)
- [YOLO — Knowledge Distillation](<../../Machine Learning/YOLO/YOLO — Knowledge Distillation.md>)
- [YOLO — Other Optimization Techniques](<../../Machine Learning/YOLO/YOLO — Other Optimization Techniques.md>)
- [YOLO — Pruning](<../../Machine Learning/YOLO/YOLO — Pruning.md>)
- [YOLO — Quantization by Hardware](<../../Machine Learning/YOLO/YOLO — Quantization by Hardware.md>)
- [YOLO — Quantization](<../../Machine Learning/YOLO/YOLO — Quantization.md>)
- [YOLO — Synthetic Data and Flash Training App](<../../Machine Learning/YOLO/YOLO — Synthetic Data and Flash Training App.md>)
- [YOLO — Training Hardware and Capture Rig](<../../Machine Learning/YOLO/YOLO — Training Hardware and Capture Rig.md>)
- [YOLO — Training on Different Hardware](<../../Machine Learning/YOLO/YOLO — Training on Different Hardware.md>)

## Gantry, capture and physical input

- [Android Control Survey (Legacy)](<../../Robotics/Android Control Survey (Legacy).md>)
- [Gantry — Capacitive Touch Physics and Architecture](<../../Robotics/Gantry — Capacitive Touch Physics and Architecture.md>)
- [Gantry — FluidNC Control Interface (Jogging, Soft Limits, Realtime)](<../../Robotics/Gantry — FluidNC Control Interface (Jogging, Soft Limits, Realtime).md>)
- [Gantry — XY Builds and Microcontroller Choice](<../../Robotics/Gantry — XY Builds and Microcontroller Choice.md>)
- [Prior Art — Touchscreen Robots and Software Agents](<../../Robotics/Prior Art — Touchscreen Robots and Software Agents.md>)
- [Rig — Camera-to-Screen Calibration with ChArUco](<../../Robotics/Rig — Camera-to-Screen Calibration with ChArUco.md>)
- [Rig — iPhone Screen Capture Paths (USB, AirPlay, Multi-Phone)](<../../Robotics/Rig — iPhone Screen Capture Paths (USB, AirPlay, Multi-Phone).md>)
- [State of — Robotics](<../../Robotics/State of — Robotics.md>)
- [Touch Telemetry — Measuring What the Rig Emits](<../../Robotics/Touch Telemetry — Measuring What the Rig Emits.md>)
- [iOS Control — Alternative Accessibility Input Paths](<../../Robotics/iOS Control — Alternative Accessibility Input Paths.md>)
- [iOS Control — AssistiveTouch Pointer Mechanics](<../../Robotics/iOS Control — AssistiveTouch Pointer Mechanics.md>)
- [iOS Control — Exposing Device Controls to the Agent](<../../Robotics/iOS Control — Exposing Device Controls to the Agent.md>)
- [iOS Control — Raspberry Pi HID Input Converter](<../../Robotics/iOS Control — Raspberry Pi HID Input Converter.md>)
- [iOS Control — Relative Cursor Calibration and Visual Servoing](<../../Robotics/iOS Control — Relative Cursor Calibration and Visual Servoing.md>)

## Navigation, imitation and RL research — held

- [RL — Bandits and Bayesian Optimisation for Hardware Tuning](<../../RL and Simple Robots/RL — Bandits and Bayesian Optimisation for Hardware Tuning.md>)
- [RL — Emulator-First Training and Sim-to-Real for the Rig](<../../RL and Simple Robots/RL — Emulator-First Training and Sim-to-Real for the Rig.md>)
- [RL — GRPO in Practice on Small GPUs](<../../RL and Simple Robots/RL — GRPO in Practice on Small GPUs.md>)
- [RL — Imitation Learning from Logged Taps (BC, ACT, LeRobot)](<../../RL and Simple Robots/RL — Imitation Learning from Logged Taps (BC, ACT, LeRobot).md>)
- [RL — Offline RL from Logged Episodes (IQL, CQL, AWR)](<../../RL and Simple Robots/RL — Offline RL from Logged Episodes (IQL, CQL, AWR).md>)
- [RL — Real-World Training Loop on the Gantry (Resets, Safety, HIL-SERL)](<../../RL and Simple Robots/RL — Real-World Training Loop on the Gantry (Resets, Safety, HIL-SERL).md>)
- [RL — Rewards and Success Detection from the Screen](<../../RL and Simple Robots/RL — Rewards and Success Detection from the Screen.md>)
- [RL — Self-Generated Tasks and Curricula for GUI Agents](<../../RL and Simple Robots/RL — Self-Generated Tasks and Curricula for GUI Agents.md>)
- [RL — Training GUI Agents with RL (DigiRL to MobileRL)](<../../RL and Simple Robots/RL — Training GUI Agents with RL (DigiRL to MobileRL).md>)
- [RL — Where RL Helps a Gantry Robot (and Where It Doesn't)](<../../RL and Simple Robots/RL — Where RL Helps a Gantry Robot (and Where It Doesn't).md>)
- [Simple Robots — Cheap Platforms to Practise RL On](<../../RL and Simple Robots/Simple Robots — Cheap Platforms to Practise RL On.md>)
- [Simple Robots — Sim-to-Real Walking for Cheap Bipeds](<../../RL and Simple Robots/Simple Robots — Sim-to-Real Walking for Cheap Bipeds.md>)
- [State of — RL and Simple Robots](<../../RL and Simple Robots/State of — RL and Simple Robots.md>)

## Vision, OCR and workflow planning

- [Security — Prompt Injection and Pop-up Attacks on GUI Agents](<../../Cybersecurity/Security — Prompt Injection and Pop-up Attacks on GUI Agents.md>)
- [Agents — Architecture and Perception Loop](<../../Machine Learning/Agents — Architecture and Perception Loop.md>)
- [Agents — VLM GUI Agents and Vision Grounding Survey](<../../Machine Learning/Agents — VLM GUI Agents and Vision Grounding Survey.md>)
- [OCR — Engines for Phone Screens](<../../Machine Learning/OCR — Engines for Phone Screens.md>)
- [State of — System Design](<../../System Design/State of — System Design.md>)
- [System Design — Bare-Minimum iPhone Setup (MVP)](<../../System Design/System Design — Bare-Minimum iPhone Setup (MVP).md>)
- [System Design — Card-Playing Gantry Rig Architecture](<../../System Design/System Design — Card-Playing Gantry Rig Architecture.md>)
- [System Design — Drag, Tap and Verify Primitives for Card Moves](<../../System Design/System Design — Drag, Tap and Verify Primitives for Card Moves.md>)
- [System Design — Game State and Decision Engines for Card Games](<../../System Design/System Design — Game State and Decision Engines for Card Games.md>)
- [System Design — Reading Cards from the Screen](<../../System Design/System Design — Reading Cards from the Screen.md>)
- [System Design — Related Work - Robots and Bots that Play Games](<../../System Design/System Design — Related Work - Robots and Bots that Play Games.md>)
- [System Design — Reliability, Error Recovery and Testing Harness](<../../System Design/System Design — Reliability, Error Recovery and Testing Harness.md>)
