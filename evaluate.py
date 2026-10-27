"""Measure accuracy (Word Error Rate) against a reference transcript.

Usage:
    python evaluate.py sample_audio/clip.wav sample_audio/clip.txt
Lower WER is better (0.0 = perfect).
"""
import re
import sys

from jiwer import wer

from scribe import to_txt
from scribe.engine import transcribe_file


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9' ]+", "", text.lower()).strip()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python evaluate.py <audio> <reference.txt>")
    hypothesis = to_txt(transcribe_file(sys.argv[1]))
    reference = open(sys.argv[2], encoding="utf-8").read()
    score = wer(normalize(reference), normalize(hypothesis))
    print(f"Reference : {reference.strip()}\nTranscript: {hypothesis}\nWER       : {score:.2%}")
