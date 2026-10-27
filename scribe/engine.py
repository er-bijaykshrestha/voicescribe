"""Core transcription logic."""
import os
from dataclasses import dataclass
from typing import Callable, List, Optional

import speech_recognition as sr

from .audio_utils import ensure_wav

SUPPORTED_ENGINES = ("google", "whisper", "sphinx")


@dataclass
class Segment:
    """One transcribed chunk of audio."""
    start: float
    end: float
    text: str


def recognize_chunk(recognizer: sr.Recognizer, audio: sr.AudioData, engine: str, language: str) -> str:
    """Send one audio chunk to the chosen recognition engine."""
    if engine == "google":
        return recognizer.recognize_google(audio, language=language)
    if engine == "whisper":  # offline, needs: pip install openai-whisper
        return recognizer.recognize_whisper(audio, language=language.split("-")[0])
    if engine == "sphinx":  # offline, needs: pip install pocketsphinx
        return recognizer.recognize_sphinx(audio, language=language)
    raise ValueError(f"Unknown engine '{engine}'. Choose from {SUPPORTED_ENGINES}")


def transcribe_file(
    path: str,
    engine: str = "google",
    language: str = "en-US",
    chunk_seconds: int = 30,
    progress: Optional[Callable[[float], None]] = None,
) -> List[Segment]:
    """Transcribe an audio file into timestamped segments.

    progress: optional callback receiving a float between 0 and 1.
    Chunks that cannot be understood are skipped.
    """
    if engine not in SUPPORTED_ENGINES:
        raise ValueError(f"Unknown engine '{engine}'. Choose from {SUPPORTED_ENGINES}")

    wav_path, is_temp = ensure_wav(path)
    recognizer = sr.Recognizer()
    segments: List[Segment] = []

    try:
        with sr.AudioFile(wav_path) as source:
            total = source.DURATION or 0.0
            recognizer.adjust_for_ambient_noise(source, duration=min(0.5, total))
            position = 0.0
            while position < total:
                audio = recognizer.record(source, duration=chunk_seconds)
                if len(audio.frame_data) == 0:
                    break
                end = min(position + chunk_seconds, total)
                try:
                    text = recognize_chunk(recognizer, audio, engine, language)
                    if text.strip():
                        segments.append(Segment(round(position, 2), round(end, 2), text.strip()))
                except sr.UnknownValueError:
                    pass  # silence or unintelligible audio
                except sr.RequestError as e:
                    raise RuntimeError(f"Speech service error (check your internet): {e}") from e
                position = end
                if progress:
                    progress(min(position / total, 1.0) if total else 1.0)
    finally:
        if is_temp and os.path.exists(wav_path):
            os.remove(wav_path)

    return segments


def transcribe_microphone(engine: str = "google", language: str = "en-US") -> str:
    """Record one phrase from the microphone (needs PyAudio)."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source, timeout=10, phrase_time_limit=30)
    try:
        return recognize_chunk(recognizer, audio, engine, language)
    except sr.UnknownValueError:
        return ""
