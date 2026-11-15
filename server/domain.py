"""Deterministic demo state. All event times are server times, never LLM output."""

import time
import uuid
from dataclasses import asdict, dataclass, field

PROMPTS = {
    "responsive": "Is he responding? Shake his shoulders.",
    "breathing": "Is he breathing normally? Look at his chest.",
    "cpr": "Put your hands in the center of his chest. Push hard and fast, follow the beat.",
    "stay": "A dispatcher is taking your call now.",
}


@dataclass
class Session:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    phase: str = "ai_guide"
    started_at: float = field(default_factory=time.time)
    ended_at: float | None = None
    picked_up_at: float | None = None
    cpr_at: float | None = None
    step: str = "responsive"
    location: dict = field(default_factory=dict)
    answers: dict = field(default_factory=dict)
    timeline: list = field(default_factory=list)
    frames: list = field(default_factory=list)
    subtitles: list = field(default_factory=list)
    dialogue: list = field(default_factory=list)
    audio: dict = field(default_factory=dict)
    scene: str = ""
    report: dict | None = None
    report_status: str = "pending"
    warnings: list = field(default_factory=list)
    device: dict = field(default_factory=dict)

    def elapsed(self, now=None):
        return round(max(0, (now if now is not None else time.time()) - self.started_at), 3)

    def event(self, kind, label, now=None):
        e = {"t": self.elapsed(now), "kind": kind, "label": label}
        self.timeline.append(e)
        return e

    def answer(self, step, value):
        if self.phase != "ai_guide" or step != self.step or step not in ("responsive", "breathing"):
            raise ValueError("Answer does not match the active guide step")
        if value not in ("yes", "no"):
            raise ValueError("Answer must be yes or no")
        self.answers[step] = value
        labels = {
            ("responsive", "no"): "Not responding (reported)",
            ("responsive", "yes"): "Responding (reported)",
            ("breathing", "no"): "Not breathing normally (reported)",
            ("breathing", "yes"): "Breathing normally (reported)",
        }
        self.event("answer", labels[step, value])
        self.step = "stay" if value == "yes" else ("breathing" if step == "responsive" else "cpr")
        if self.step == "cpr":
            self.cpr_at = time.time()
            self.event(
                "cpr_guided",
                "CPR guidance started — compressions not independently verified",
            )

    def card(self):
        suspected = self.answers.get("responsive") == "no" and self.answers.get("breathing") == "no"
        return {
            "location": self.location,
            "situation": "Suspected cardiac arrest — CPR guided"
            if suspected
            else "Assessment in progress",
            "facts": [
                {"t": e["t"], "text": e["label"]}
                for e in self.timeline
                if e["kind"] in ("answer", "cpr_guided", "pickup")
            ],
            "scene": self.scene,
        }

    def metrics(self):
        end = self.ended_at or time.time()
        return {
            "total_seconds": self.elapsed(end),
            "alert_to_cpr_guidance_seconds": self.elapsed(self.cpr_at) if self.cpr_at else None,
            "alert_to_pickup_seconds": self.elapsed(self.picked_up_at)
            if self.picked_up_at
            else None,
            "cpr_guidance_window_seconds": round(end - self.cpr_at, 3) if self.cpr_at else None,
        }

    def state(self):
        return {
            "type": "state",
            "phase": self.phase,
            "session_id": self.id,
            "started_at": self.started_at * 1000,
            "server_now": time.time() * 1000,
            "ended_at": self.ended_at * 1000 if self.ended_at else None,
            "step": self.step,
            "timeline": self.timeline,
            "card": self.card(),
            "device": self.device,
            "subtitles": self.subtitles[-1:],
            "report_status": self.report_status,
        }

    def json(self):
        return asdict(self)
