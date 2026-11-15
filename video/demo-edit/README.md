# Demo video edit (POV + voice)

- `mix_voice.py`: places the narrator's separately recorded lines in the silences of the guide's prompts
  (prompts in the POV recording at 11.1–15.7, 19.0–21.5, 25.6–30.2, 35.6–38.7 s) and mixes them.
- POV crop of the iPhone screen recording (384×832): `crop=384:460:0:120,scale=768:920:flags=lanczos`, x264 CRF 12, 60 fps.
- Split screen: starts at 35.6 s in the POV video, when the guide says "A dispatcher is answering your call now."

## Split screen (FirstFive-demo-split.mp4)

- Console recording t = POV t - 45.13 s (console timer flips: session = t_console + 51.683; report: not responding +25.6 s = POV 19.0 s).
- Split from POV 46.53 s (after Recordly zoom on Answer call), console full screen from 81.6 s.
- Filter graph: `split_filter.txt` (inputs: POV mp4, console recording). Console audio +15 dB, delayed 45.13 s.
