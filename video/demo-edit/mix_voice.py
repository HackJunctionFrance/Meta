import numpy as np
import soundfile as sf

v, sr = sf.read("v48.wav")
a, _ = sf.read("a48.wav")
N = len(v)
voice = np.zeros(N)
TTS = [(11.1, 15.7), (19.0, 21.5), (25.6, 30.2), (35.6, 38.7)]
# (source start, source end, destination start, kind)
P = [
    (2.60, 3.40, 0.40, "line"),  # Hey
    (4.00, 4.90, 1.35, "line"),  # hey man
    (6.10, 7.25, 2.60, "line"),  # Are you okay?
    (8.70, 9.80, 4.40, "line"),  # Are you okay?
    (11.65, 13.35, 6.15, "line"),  # Man / okay
    (14.45, 15.70, 8.55, "line"),  # Emergency
    (17.40, 19.15, 15.85, "line"),  # There's a man laying on the floor
    (19.70, 21.20, 17.45, "line"),  # He's not responding
    (23.50, 24.40, 21.85, "line"),  # Let me check
    (25.45, 26.95, 23.70, "line"),  # No, he's not breathing
    (30.90, 36.00, 30.50, "breath"),  # effort while compressing
    (36.60, 43.20, 38.90, "breath"),
]


def rms(x):
    return np.sqrt(np.mean(x**2) + 1e-12)


target_line = 10 ** (-17 / 20)
target_breath = 10 ** (-31 / 20)
log = []
for s, e, d, k in P:
    seg = a[int(s * sr) : int(e * sr)].copy()
    # gain from the speech part only (ignore padding)
    core = seg[np.abs(seg) > 0.02] if k == "line" else seg
    g = (target_line if k == "line" else target_breath) / rms(core if len(core) else seg)
    if k == "line":
        g = min(g, 0.95 / np.abs(seg).max())
    seg *= g
    f = int(0.015 * sr)
    ramp = np.linspace(0, 1, f)
    seg[:f] *= ramp
    seg[-f:] *= ramp[::-1]
    i = int(d * sr)
    voice[i : i + len(seg)] += seg[: N - i]
    log.append((s, e, d, round(d + e - s, 2), k, round(20 * np.log10(g), 1)))
# overlap check: voice energy inside TTS windows
for s, e in TTS:
    w = voice[int(s * sr) : int(e * sr)]
    print(f"TTS {s}-{e}: voice peak inside {np.abs(w).max():.3f}")
vv = v + voice[:, None]
peak = np.abs(vv).max()
print("mix peak", round(peak, 3))
if peak > 0.98:
    vv *= 0.98 / peak
sf.write("mix48.wav", vv.astype(np.float32), sr)
for row in log:
    print(row)
