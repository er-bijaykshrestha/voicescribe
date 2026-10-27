"""Audio helpers: format conversion and basic file info."""
import os
import tempfile

NATIVE_FORMATS = (".wav", ".flac", ".aiff", ".aif")
SUPPORTED_EXTENSIONS = NATIVE_FORMATS + (".mp3", ".m4a", ".ogg", ".wma", ".aac", ".webm")


def ensure_wav(path: str):
    """Return (wav_path, is_temporary).

    WAV/FLAC/AIFF are read directly by SpeechRecognition. Everything else is
    converted to WAV with pydub (which needs ffmpeg installed).
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Audio file not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    if ext in NATIVE_FORMATS:
        return path, False

    try:
        from pydub import AudioSegment
    except ImportError as e:
        raise RuntimeError("pydub is required to read this format: pip install pydub") from e

    try:
        audio = AudioSegment.from_file(path)
    except FileNotFoundError as e:
        raise RuntimeError("ffmpeg not found. Install ffmpeg to use mp3/m4a/ogg files.") from e

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    audio.set_channels(1).export(tmp.name, format="wav")
    return tmp.name, True
