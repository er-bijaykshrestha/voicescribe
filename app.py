"""Streamlit web app for VoiceScribe.  
Run:  streamlit run app.py"""

import os
import tempfile

import streamlit as st

from scribe import SUPPORTED_ENGINES, to_json, to_srt, to_txt
from scribe.audio_utils import SUPPORTED_EXTENSIONS
from scribe.engine import transcribe_file

LANGUAGES = {"English (US)": "en-US", "English (India)": "en-IN", "English (UK)": "en-GB",
             "Hindi": "hi-IN", "Kannada": "kn-IN", "Tamil": "ta-IN", "Telugu": "te-IN",
             "Spanish": "es-ES", "French": "fr-FR", "German": "de-DE"}

st.set_page_config(page_title="VoiceScribe", page_icon="🎙️", layout="centered")
st.title("🎙️ VoiceScribe")
st.caption("Upload or record audio and get a transcript in seconds.")

with st.sidebar:
    st.header("Settings")
    engine = st.selectbox("Engine", SUPPORTED_ENGINES,
                          help="google needs internet. whisper and sphinx work offline once installed.")
    language = LANGUAGES[st.selectbox("Language", list(LANGUAGES))]
    chunk = st.slider("Chunk length (seconds)", 10, 60, 30)
    timestamps = st.checkbox("Show timestamps", value=True)

tab_upload, tab_record = st.tabs(["Upload file", "Record"])
audio_bytes, suffix = None, ".wav"

with tab_upload:
    up = st.file_uploader("Audio file", type=[e.strip(".") for e in SUPPORTED_EXTENSIONS])
    if up:
        audio_bytes, suffix = up.getvalue(), os.path.splitext(up.name)[1]
        st.audio(audio_bytes)

with tab_record:
    rec = st.audio_input("Record from your microphone")
    if rec:
        audio_bytes, suffix = rec.getvalue(), ".wav"

if audio_bytes and st.button("Transcribe", type="primary"):
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        path = tmp.name
    bar = st.progress(0.0, text="Transcribing...")
    try:
        segments = transcribe_file(path, engine, language, chunk, lambda f: bar.progress(f))
        st.session_state["segments"] = segments
    except Exception as e:  # show friendly error in UI
        st.error(str(e))
    finally:
        bar.empty()
        os.remove(path)

segments = st.session_state.get("segments")
if segments:
    text = to_txt(segments, timestamps)
    words = sum(len(s.text.split()) for s in segments)
    st.success(f"Done. {words} words in {len(segments)} segments.")
    st.text_area("Transcript", text, height=300)
    c1, c2, c3 = st.columns(3)
    c1.download_button("Download .txt", to_txt(segments, timestamps), "transcript.txt")
    c2.download_button("Download .srt", to_srt(segments), "transcript.srt")
    c3.download_button("Download .json", to_json(segments), "transcript.json")
elif segments == []:
    st.warning("No speech was recognized. Try clearer audio or another language.")
