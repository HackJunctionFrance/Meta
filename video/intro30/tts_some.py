import json, sys, soundfile as sf, numpy as np
from kokoro_onnx import Kokoro
k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
vo = json.load(open("i30/vo.json")); lines = dict(json.load(open("i30/lines.json")))
for key in sys.argv[1:]:
    s, sr = k.create(lines[key], voice="af_heart", speed=0.97, lang="en-us"); s = np.asarray(s, np.float32)
    idx = np.where(np.abs(s) > 0.01)[0]; s = s[max(0, idx[0]-int(0.03*sr)): idx[-1]+int(0.08*sr)]
    sf.write(f"i30/vo_{key}.wav", s, sr); vo[key] = {"text": lines[key], "dur": round(len(s)/sr, 3)}; print(key, vo[key]["dur"])
json.dump(vo, open("i30/vo.json", "w"), indent=1)
