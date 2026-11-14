# FirstFive intro video (≈ 64 s, 1080p, 30 fps)

Motion-design intro that precedes the live demo. Rendered from `intro.html` (one `render(t)` function, deterministic frames).

1. `tts.py` — voiceover with Kokoro TTS (`kokoro-onnx`, voice `af_heart`), lines in `lines.json`. Model files: kokoro-onnx GitHub release `model-files-v1.0`.
2. `timeline.py` — scene start times from the voice durations → `timeline.json`.
3. `frames.js` — Playwright renders 1920×1080 JPEG frames; also writes ECG beat times.
4. `audio.py` — voice + synthesized pad, monitor beeps, 110/min metronome; then `ffmpeg loudnorm` and H.264 encode.

Font: Geist (Google Fonts, OFL), downloaded to `fonts/` next to `intro.html`.
Facts cited on screen: survival drops up to ~10% per minute without CPR (AHA); bystander CPR can more than double survival (Harvard Health, AHA).
