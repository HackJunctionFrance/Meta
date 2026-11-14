"""Generate a clearly labelled synthetic MP4 for simulator and Meta Mock Device Kit."""

from pathlib import Path

import cv2
import numpy as np

output = Path("data/sample.mp4")
output.parent.mkdir(exist_ok=True)
writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"mp4v"), 3, (960, 540))
if not writer.isOpened():
    raise SystemExit("MP4 encoder unavailable")
try:
    for i in range(90):
        frame = np.full((540, 960, 3), (45, 32, 20), dtype=np.uint8)
        cv2.putText(
            frame,
            "FIRSTFIVE / SYNTHETIC REHEARSAL",
            (35, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (190, 240, 160),
            2,
        )
        cv2.putText(
            frame,
            f"{i / 3:.1f}s - No patient footage",
            (35, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (200, 200, 200),
            2,
        )
        cv2.circle(frame, (250, 300), 35, (180, 180, 180), 8)
        cv2.line(frame, (290, 300), (550, 300), (180, 180, 180), 12)
        cv2.line(frame, (550, 300), (680, 380), (180, 180, 180), 12)
        cv2.circle(frame, (410, 290), 15 + i % 3 * 3, (130, 220, 160), -1)
        writer.write(frame)
finally:
    writer.release()
print(output)
