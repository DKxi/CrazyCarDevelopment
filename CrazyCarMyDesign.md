# CrazyCar — implemented design

This document supersedes the original proposed three-level design. Executable source is authoritative. The original proposal named different cars, suggested collision masks and described automatic transitions and lobby audio; those were not the actual baseline implementation.

## Preserved architecture and behavior

Python/Streamlit owns the lobby, credits, selections and session. Browser JavaScript owns Canvas, Web Audio and requestAnimationFrame. The original three cars and five sponsors, original three point layouts, dark lime/orange visual identity, acceleration/reverse model, speed-dependent steering and nearest-centerline collision are retained. Frame-rate-independent coasting replaces a per-frame multiplier with the equivalent 60 Hz baseline.

## Configuration and progression

`game_config.py` supplies exactly 23 explicit open routes in Rookie (1–4), Amateur (5–9), Pro (10–14), Elite (15–19) and Master (20–23) bands. Each track has metadata, world dimensions, width, timer, modifiers and points. Original route coordinates are preserved but roads are widened to match Rookie progression. Later tracks lengthen and gain corners; time limits reflect distance, corners and band. Index comparisons use configuration length.

Seven cars have declarative unlock requirements; the first three remain available, then Road Reaper at 6, BeastHunter at 12, Night Fang at 18 and Apex Titan at 23. Existing speed/handling labels remain cosmetic and all cars can complete every circuit. `highest_level_unlocked` grows monotonically after completion and never resets on retry or exit. The lobby permits starting at any unlocked level. No accounts, databases or durable save files are introduced.

## Component boundary

The large RACE_HTML literal is extracted into `game/index.html`, `race.js`, and `race.css`, served by `components.declare_component` using an absolute path relative to app.py. A small vanilla-JS V1 message bridge handles ready, render, value and frame-height messages. Only completion and lobby exit trigger Streamlit reruns; a stable unique race key preserves the running iframe. Incoming render messages are source-checked and initialization happens once. Python checks race IDs, event IDs and valid progression. This is a modest component refactor, with no Node build or framework dependency.

## Input, state and safety

Keyboard and a pointer-captured joystick map into one analog accelerate/brake/steer state. The joystick clamps radial movement and applies a 0.12 per-axis dead zone. Pointer release/cancel/capture loss and window blur clear input; hidden tabs and resizing also pause. Keyboard repeat cannot repeatedly trigger retry. Space retries only a failed race. The same restart function handles buttons, R and Space.

States are ready, racing, paused, failed, complete and exiting. Pause preserves timer, position, orientation, speed and current level. Restart resets only the current run. NEXT LEVEL is explicit. Championship completion depends on the final configured track. Modal buttons support focus and Tab navigation. Return to Lobby sends a real Streamlit event from every menu.

## Rendering and mobile

The fixed per-track world is projected through a following camera. Resizing changes the view, never physics coordinates. Roads are open non-intersecting polylines with ordered checkpoints and a visible finish marker. The car sprite retains its original rotation convention. The sponsor path is drawn on a dark roof panel within that transform; lobby SVGs use the same geometry.

The Streamlit host sizes the iframe using dynamic viewport height with a legacy fallback. The component reads only its own viewport. HUD and controls use separate layout regions in portrait; landscape uses a compact joystick overlay. Identity, track, progress and timer stay visible. Pointer gesture suppression is scoped to the game. Optional audio has one context/interval, starts or resumes from a gesture, stops on exit, and cannot crash gameplay.

## Verification and limits

See README for the exact level/car/sponsor tables, commands and browser coverage. Lightweight configuration and Streamlit tests plus real Chrome/Edge integration cover all progression and unlock milestones. A deterministic driver validates all routes through the actual physics. Physical iOS Safari/Chrome and Android Chrome remain intended, unverified device targets; human handling and sustained mobile frame rate still benefit from real-device playtesting.

## Diagrams

- [Architecture](md/architecture.md)
- [Flow](md/graph.md)
- [Data model](md/class.md)
- [Sequence](md/sequence.md)
- [State machine](md/state.md)
