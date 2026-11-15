import json, sys, soundfile as sf, numpy as np
from kokoro_onnx import Kokoro
k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
vo = json.load(open("vo.json")); lines = dict(json.load(open("lines.json")))
key = sys.argv[1]; text = lines[key]
s, sr = k.create(text, voice="af_heart", speed=0.94, lang="en-us"); s = np.asarray(s, np.float32)
idx = np.where(np.abs(s) > 0.01)[0]; s = s[max(0, idx[0]-int(0.03*sr)): idx[-1]+int(0.08*sr)]
sf.write(f"vo_{key}.wav", s, sr); vo[key] = {"text": text, "dur": round(len(s)/sr, 3), "sr": sr}
json.dump(vo, open("vo.json","w"), indent=1); print(key, vo[key]["dur"])
