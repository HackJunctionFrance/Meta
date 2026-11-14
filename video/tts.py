import json, soundfile as sf, numpy as np
from kokoro_onnx import Kokoro
k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
out = {}
for key, text in json.load(open("lines.json")):
    s, sr = k.create(text, voice="af_heart", speed=0.94, lang="en-us")
    s = np.asarray(s, dtype=np.float32)
    # trim leading/trailing silence
    idx = np.where(np.abs(s) > 0.01)[0]
    s = s[max(0, idx[0] - int(0.03 * sr)): idx[-1] + int(0.08 * sr)]
    sf.write(f"vo_{key}.wav", s, sr)
    out[key] = {"text": text, "dur": round(len(s) / sr, 3), "sr": sr}
    print(key, out[key]["dur"])
json.dump(out, open("vo.json", "w"), indent=1)
