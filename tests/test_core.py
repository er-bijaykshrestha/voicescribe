import wave

import pytest
import speech_recognition as sr

from scribe import Segment, to_json, to_srt, to_txt
from scribe import engine as eng
from scribe.export import format_timestamp


def make_wav(path, seconds=65, rate=16000):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * rate * seconds)


def test_format_timestamp():
    assert format_timestamp(3661.5) == "01:01:01"
    assert format_timestamp(3661.5, srt=True) == "01:01:01,500"


def test_exports():
    segs = [Segment(0, 30, "hello world"), Segment(30, 60, "second part")]
    assert to_txt(segs) == "hello world second part"
    assert to_txt(segs, timestamps=True).startswith("[00:00:00] hello")
    assert "00:00:30,000 --> 00:01:00,000" in to_srt(segs)
    assert '"word_count": 4' in to_json(segs)


def test_transcribe_chunks_with_mock(tmp_path, monkeypatch):
    wav = tmp_path / "a.wav"
    make_wav(wav, seconds=65)
    monkeypatch.setattr(eng, "recognize_chunk", lambda r, a, e, l: "chunk text")
    segs = eng.transcribe_file(str(wav), chunk_seconds=30)
    assert len(segs) == 3
    assert segs[0].start == 0 and segs[1].start == 30
    assert segs[-1].end == pytest.approx(65, abs=0.5)


def test_unintelligible_audio_is_skipped(tmp_path, monkeypatch):
    wav = tmp_path / "a.wav"
    make_wav(wav, seconds=10)

    def boom(*a, **k):
        raise sr.UnknownValueError()

    monkeypatch.setattr(eng, "recognize_chunk", boom)
    assert eng.transcribe_file(str(wav)) == []


def test_missing_file_and_bad_engine(tmp_path):
    with pytest.raises(FileNotFoundError):
        eng.transcribe_file(str(tmp_path / "nope.wav"))
    with pytest.raises(ValueError):
        eng.transcribe_file("x.wav", engine="bogus")
