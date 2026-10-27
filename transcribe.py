"""Command-line interface for VoiceScribe.

Examples:
    python transcribe.py talk.mp3
    python transcribe.py talk.wav -f srt -o talk.srt
    python transcribe.py talk.wav -l hi-IN --engine whisper
    python transcribe.py --mic
"""
import argparse
import os
import sys

from scribe import SUPPORTED_ENGINES, to_json, to_srt, to_txt
from scribe.engine import transcribe_file, transcribe_microphone


def main() -> None:
    p = argparse.ArgumentParser(description="VoiceScribe: audio to text")
    p.add_argument("audio", nargs="?", help="path to audio file")
    p.add_argument("--mic", action="store_true", help="transcribe from microphone")
    p.add_argument("-e", "--engine", default="google", choices=SUPPORTED_ENGINES)
    p.add_argument("-l", "--language", default="en-US", help="e.g. en-US, en-IN, hi-IN")
    p.add_argument("-f", "--format", default="txt", choices=["txt", "srt", "json"])
    p.add_argument("-o", "--output", help="save result to this file")
    p.add_argument("--timestamps", action="store_true", help="add timestamps to txt output")
    p.add_argument("--chunk", type=int, default=30, help="chunk length in seconds")
    args = p.parse_args()

    if args.mic:
        print("Listening...")
        result = transcribe_microphone(args.engine, args.language)
    elif args.audio:
        def show(frac):
            print(f"\rProgress: {frac * 100:5.1f}%", end="", file=sys.stderr)
        try:
            segments = transcribe_file(args.audio, args.engine, args.language, args.chunk, show)
        except (FileNotFoundError, RuntimeError, ValueError) as e:
            sys.exit(f"Error: {e}")
        print(file=sys.stderr)
        result = {"txt": lambda: to_txt(segments, args.timestamps),
                  "srt": lambda: to_srt(segments),
                  "json": lambda: to_json(segments)}[args.format]()
    else:
        p.error("give an audio file or use --mic")

    if not result:
        sys.exit("No speech recognized.")

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Saved to {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
