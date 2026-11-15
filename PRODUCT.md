# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Emergency dispatcher (operator console, `/console?mode=operator`).** A 112 / SAMU call-taker at a desk, often wearing a headset, receiving an alert raised by a bystander wearing Meta AI glasses. Job: understand the scene in seconds, take over from the automated guide, talk the bystander through CPR, confirm help is on the way, then close the call with a handover report.
- **Bystander (glasses wearer, iOS CameraAccess app).** An untrained witness kneeling next to an unresponsive person, hands busy, stressed.
- **Projection viewer (`/console?mode=viewer`, `/caller`).** Jury or audience watching the demo.

## Product Purpose

FirstFive covers the first five minutes of a cardiac arrest before professionals arrive. The glasses stream the witness's first-person view; a fixed-script guide asks responsiveness and breathing questions and starts CPR with a metronome; a dispatcher can take over by voice and sees what the witness sees. Success: the dispatcher acts faster with better information, and the call ends with a usable report.

## Positioning

The dispatcher sees the scene from the witness's own eyes, hands-free, while guidance keeps running. A phone video call cannot do this: the witness's hands must stay on the chest.

## Operating Context

- Hackathon demo (Junction 2026, Meta "AI Glasses for Everyone, Everyday" challenge). Recorded on a MacBook screen (~1440×900, Chrome full screen), shown side by side with the iPhone view.
- Simulation only: no real emergency service is contacted. This must stay visible.
- Server: FastAPI on the Mac; console is plain static HTML/CSS/JS in `web/`, no build step. Voice through LiveKit Cloud.
- Interface language: English (international jury).

## Capabilities and Constraints

- Phases: `idle` (waiting), `ai_guide` (incoming emergency, automated guide running), `connected` (dispatcher on the call), `ended`.
- Live JPEG frames from the glasses, device status badge, briefing card (situation, location, scene, facts), timeline, live voice status, end call → report (fallback report when no LLM is configured), rehearsal controls (keys 1 2 3 4 0).
- JS hooks are element IDs in `web/app.js`; any redesign must keep them.
- Guide answers are a fixed script, not a free conversation with a model. Location and battery are not implemented yet.

## Brand Commitments

Name: FirstFive. No logo, palette or typeface imposed (confirmed by the user).

## Evidence on Hand

No real users, partners, metrics or testimonials. Do not invent survival statistics on screen.

## Product Principles

1. In an emergency the screen answers one question first: what is happening and what do I do now.
2. Trust over show: the simulation status, consent and data scope stay visible and honest.
3. Hands-free for the witness, glanceable for the dispatcher.
4. Never hide a failure: if voice or video drops, say so plainly with the fallback.

## Accessibility & Inclusion

High contrast, state never conveyed by colour alone, keyboard operable (rehearsal shortcuts), readable from a recorded screen.
