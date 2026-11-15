import json

import numpy as np
import soundfile as sf

SR = 48000
tl = json.load(open("timeline.json"))
T = tl["_total"]
N = int((T + 0.5) * SR)
t = np.arange(N) / SR
voice = np.zeros(N, np.float32)
for k, v in tl.items():
    if k.startswith("_"):
        continue
    s, _ = sf.read(f"r48_vo_{k}.wav", dtype="float32")
    s = s / (np.abs(s).max() + 1e-9) * 0.89
    i = int(v["start"] * SR)
    voice[i : i + len(s)] += s[: N - i]


def env(a, b, fi, fo):
    return np.clip((t - a) / max(fi, 1e-3), 0, 1) * np.clip((b - t) / max(fo, 1e-3), 0, 1)


rv = tl["reveal"]["start"]
lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.11 * t)
drone = (
    np.sin(2 * np.pi * 55 * t) * 0.5
    + np.sin(2 * np.pi * 110 * t) * 0.35
    + np.sin(2 * np.pi * 164.81 * t) * 0.18
) * lfo
pad = sum(
    a * np.sin(2 * np.pi * f * t + p)
    for f, a, p in [
        (130.81, 0.45, 0),
        (196.0, 0.35, 1),
        (261.63, 0.25, 2),
        (329.63, 0.2, 0.5),
        (392.0, 0.12, 1.7),
    ]
) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.07 * t))
bed = (drone * env(0, rv + 0.6, 1.5, 1.0) + pad * env(rv + 0.3, T + 0.5, 1.5, 1.2)) * 0.05
venv = np.convolve(np.abs(voice), np.ones(4800) / 4800, mode="same")
bed *= 1 - 0.55 * np.clip(venv / 0.05, 0, 1)
fx = np.zeros(N, np.float32)


def tone(at, dur, freqs, amp, decay):
    i = int(at * SR)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    w = sum(np.sin(2 * np.pi * f * tt) for f in freqs) / len(freqs)
    seg = (w * np.clip(tt / 0.01, 0, 1) * np.exp(-tt / decay) * amp).astype(np.float32)
    fx[i : i + n] += seg[: max(0, min(n, N - i))]


tone(rv + 0.15, 3.0, [523.25, 784.0, 1046.5], 0.16, 0.9)
tone(tl["view"]["start"] + 0.5, 0.06, [2200], 0.10, 0.015)
tone(tl["case"]["start"] + 2.8, 3.0, [392.0, 587.33, 783.99], 0.13, 1.1)
mix = voice + bed + fx
mix *= np.clip((T + 0.4 - t) / 1.0, 0, 1)
mix /= max(1.0, np.abs(mix).max() / 0.95)
sf.write("mix.wav", mix[: int(T * SR)].astype(np.float32), SR)
print("audio", T)
