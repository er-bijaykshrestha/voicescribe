"""Turn segments into text, subtitle, or JSON output."""
import json
from typing import List

from .engine import Segment


def format_timestamp(seconds: float, srt: bool = False) -> str:
    """Seconds -> HH:MM:SS (or HH:MM:SS,mmm for SRT)."""
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}" if srt else f"{h:02}:{m:02}:{s:02}"


def to_txt(segments: List[Segment], timestamps: bool = False) -> str:
    if timestamps:
        return "\n".join(f"[{format_timestamp(s.start)}] {s.text}" for s in segments)
    return " ".join(s.text for s in segments)


def to_srt(segments: List[Segment]) -> str:
    blocks = []
    for i, s in enumerate(segments, 1):
        blocks.append(f"{i}\n{format_timestamp(s.start, True)} --> {format_timestamp(s.end, True)}\n{s.text}\n")
    return "\n".join(blocks)


def to_json(segments: List[Segment]) -> str:
    return json.dumps(
        {
            "word_count": sum(len(s.text.split()) for s in segments),
            "segments": [{"start": s.start, "end": s.end, "text": s.text} for s in segments],
        },
        indent=2,
        ensure_ascii=False,
    )
