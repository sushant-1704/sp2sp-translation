import streamlit as st
import requests
import base64
import io
from pydub import AudioSegment
import sounddevice as sd

API_URL = "https://cb94oiimtk.execute-api.us-east-1.amazonaws.com/translate"

st.title("🎙️ Hindi → English Speech Translation")

# Initialize session state for audio bytes
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

mode = st.radio("Choose input mode:", options=["🎤 Record Audio", "📁 Upload Audio"])

# ---------- RECORD MODE ----------
if mode == "🎤 Record Audio":
    duration = st.slider("Recording duration (seconds)", 3, 30, 6)
    fs = 16000  # Sample rate

    if st.button("Start Recording 🎙️"):
        st.info("Recording... Speak now!")
        audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="int16")
        sd.wait()
        st.success("Recording finished ✅")

        # Convert to wav bytes
        buf = io.BytesIO()
        sound = AudioSegment(audio_data.tobytes(), frame_rate=fs, sample_width=2, channels=1)
        sound.export(buf, format="wav")
        audio_bytes = buf.getvalue()

        # Save to session state
        st.session_state.audio_bytes = audio_bytes

        # Play recorded audio
        st.audio(audio_bytes, format="audio/wav")

# ---------- UPLOAD MODE ----------
elif mode == "📁 Upload Audio":
    uploaded_file = st.file_uploader("Upload Hindi audio file", type=["wav", "mp3", "m4a"])
    if uploaded_file:
        st.audio(uploaded_file)
        audio = AudioSegment.from_file(uploaded_file)
        fixed_audio = audio.set_frame_rate(16000).set_channels(1)
        buf = io.BytesIO()
        fixed_audio.export(buf, format="wav")
        audio_bytes = buf.getvalue()

        st.session_state.audio_bytes = audio_bytes
        st.info("🔄 Audio auto-converted to 16kHz WAV for backend.")

# ---------- TRANSLATE BUTTON ----------
if st.button("Translate ▶️"):
    if st.session_state.audio_bytes:
        with st.spinner("Processing and translating..."):
            headers = {"Content-Type": "audio/wav"}
            resp = requests.post(API_URL, data=st.session_state.audio_bytes, headers=headers)

            if resp.status_code != 200:
                st.error(f"❌ Error: {resp.status_code}\n{resp.text}")
            else:
                result = resp.json()
                if "output_audio" in result:
                    audio_b64 = result["output_audio"]
                    translated_audio = base64.b64decode(audio_b64)
                    st.success("✅ Translation complete!")
                    st.audio(translated_audio, format="audio/wav")
                elif "s3_url" in result:
                    st.success("✅ Translation complete! Download below 👇")
                    st.audio(result["s3_url"])
                else:
                    st.write("Response JSON:", result)
    else:
        st.warning("⚠️ Please record or upload an audio file first!")