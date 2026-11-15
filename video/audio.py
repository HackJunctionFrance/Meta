import json

import numpy as np
import soundfile as sf

SR = 48000
tl = json.load(open("timeline.json"))
ecg = json.load(open("ecg.json"))
T = tl["_total"]
N = int(T * SR) + SR
t = np.arange(N) / SR
voice = np.zeros(N, np.float32)
for k, v in tl.items():
    if k.startswith("_"):
        continue
    s, _ = sf.read(f"r48_vo_{k}.wav", dtype="float32")
    s = s / (np.abs(s).max() + 1e-9) * 0.89
    i = int(v["start"] * SR)
    voice[i : i + len(s)] += s[: N - i]


def env(a, b, fade_in, fade_out):
    e = np.clip((t - a) / max(fade_in, 1e-3), 0, 1) * np.clip((b - t) / max(fade_out, 1e-3), 0, 1)
    return e


reveal = tl["reveal"]["start"]
end = T
fx = np.zeros(N, np.float32)
bed = np.zeros(N, np.float32)
# Dark drone until the reveal
lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.11 * t)
drone = (
    np.sin(2 * np.pi * 55 * t) * 0.5
    + np.sin(2 * np.pi * 110 * t) * 0.35
    + np.sin(2 * np.pi * 164.81 * t) * 0.18
) * lfo
bed += drone * env(0, reveal + 0.8, 2.5, 1.2)
# Warm major pad after the reveal
pad = sum(
    a * np.sin(2 * np.pi * f * t + p)
    for f, a, p in [
        (130.81, 0.45, 0),
        (196.0, 0.35, 1),
        (261.63, 0.25, 2),
        (329.63, 0.2, 0.5),
        (392.0, 0.12, 1.7),
    ]
)
pad *= 0.8 + 0.2 * np.sin(2 * np.pi * 0.07 * t)
bed += pad * env(reveal + 0.3, end, 2.0, 2.5)
bed *= 0.05
# Duck the bed under the voice
venv = np.convolve(np.abs(voice), np.ones(4800) / 4800, mode="same")
duck = 1 - 0.55 * np.clip(venv / 0.05, 0, 1)
bed *= duck


def tone(at, dur, freqs, amp, decay=None, attack=0.004):
    i = int(at * SR)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    w = sum(np.sin(2 * np.pi * f * tt) for f in freqs) / len(freqs)
    e = np.clip(tt / attack, 0, 1) * (
        np.exp(-tt / decay) if decay else np.clip((dur - tt) / 0.02, 0, 1)
    )
    seg = (w * e * amp).astype(np.float32)
    fx[i : i + n] += seg[: max(0, min(n, N - i))]


for b in ecg["beats"]:
    tone(b, 0.13, [1000], 0.18)
flat_dur = 2.6
tone(ecg["flat"], flat_dur, [1000], 0.12)
fx[int(ecg["flat"] * SR) : int((ecg["flat"] + flat_dur) * SR)] *= np.linspace(
    1, 0, int(flat_dur * SR)
)[: len(fx[int(ecg["flat"] * SR) : int((ecg["flat"] + flat_dur) * SR)])]
tone(reveal + 0.35, 3.0, [523.25, 784.0, 1046.5], 0.16, decay=0.9, attack=0.01)
tone(tl["alert"]["start"] + 0.9, 0.06, [2200], 0.10, decay=0.015)
g = tl["guide"]["start"] + 3.3
stop = tl["takeover"]["start"] - 0.2
k = g
while k < stop:
    tone(k, 0.05, [1500], 0.10, decay=0.012)
    k += 60 / 110
tone(tl["end"]["start"] - 0.05, 3.5, [392.0, 587.33, 783.99], 0.13, decay=1.1, attack=0.01)

mix = voice + bed + fx
fade = np.clip((T + 0.5 - t) / 1.5, 0, 1)
mix *= fade
mix = mix[: int((T + 0.4) * SR)]
mix /= max(1.0, np.abs(mix).max() / 0.95)
sf.write("mix.wav", mix.astype(np.float32), SR)
print("audio s", len(mix) / SR)
