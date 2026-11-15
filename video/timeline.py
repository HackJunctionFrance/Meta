import json

vo = json.load(open("vo.json"))
order = [
    "opener",
    "collapse",
    "minutes",
    "witness",
    "blind",
    "reveal",
    "alert",
    "guide",
    "takeover",
    "scope",
    "report",
    "trust",
    "impact",
    "end",
]
gap_after = {
    "opener": 1.7,
    "collapse": 1.0,
    "minutes": 0.7,
    "witness": 0.5,
    "blind": 0.9,
    "reveal": 0.9,
    "alert": 0.6,
    "guide": 0.7,
    "takeover": 0.6,
    "scope": 0.8,
    "report": 0.6,
    "trust": 0.6,
    "impact": 0.8,
    "end": 2.6,
}
t = 0.8  # opener, then ECG beats before the collapse line
tl = {}
for k in order:
    tl[k] = {"start": round(t, 3), "dur": vo[k]["dur"], "text": vo[k]["text"]}
    t += vo[k]["dur"] + gap_after[k]
tl["_total"] = round(t, 3)
json.dump(tl, open("timeline.json", "w"), indent=1)
print(json.dumps({k: (v if k == "_total" else v["start"]) for k, v in tl.items()}))
