import streamlit as st
import requests
import json
import time
import base64
from io import BytesIO

# --- CONFIGURATION ---
st.set_page_config(page_title="Voice Lab", page_icon="🎙️", layout="wide")

# --- SESSION STATE ---
for key in ["api_key", "voices", "selected_voice", "history", "api_connected", "generated_audio"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "voices" or key == "history" else None if key == "selected_voice" or key == "generated_audio" else False if key == "api_connected" else ""

# --- FUNCTIONS ---
def connect_to_api(api_key):
    try:
        res = requests.get("https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": api_key})
        if res.status_code == 200:
            st.session_state.voices = res.json().get("voices", [])
            st.session_state.api_connected = True
            return True
        else:
            st.error(f"API Error: {res.status_code} - {res.text}")
    except Exception as e:
        st.error(f"Connection error: {e}")
    return False

def generate_speech(voice_id, text, stability, similarity, style):
    try:
        res = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": st.session_state.api_key,
                "Content-Type": "application/json"
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity,
                    "style": style,
                    "use_speaker_boost": True
                }
            }
        )
        return res.content if res.status_code == 200 else st.error(f"Generation failed: {res.status_code} - {res.text}")
    except Exception as e:
        st.error(f"Speech generation error: {e}")


def get_audio_player(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    return f"""
    <audio controls style='width:100%'>
        <source src='data:audio/mp3;base64,{b64}' type='audio/mp3'>
    </audio>
    """

def get_voice_preview(url):
    try:
        res = requests.get(url)
        return res.content if res.status_code == 200 else None
    except:
        return None

def add_to_history(text, voice, audio):
    st.session_state.history.insert(0, {
        "id": str(time.time()),
        "text": text,
        "voice": voice.get("name", "Unknown"),
        "voice_id": voice.get("voice_id", ""),
        "audio": audio,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    st.session_state.history = st.session_state.history[:20]

def download_link(audio_bytes, filename):
    b64 = base64.b64encode(audio_bytes).decode()
    return f'<a href="data:audio/mp3;base64,{b64}" download="{filename}">Download Audio</a>'

# --- UI ---
st.title("Voice Lab 🎙️")
st.markdown("A minimalist ElevenLabs TTS interface")

# API Key Section
if not st.session_state.api_connected:
    st.subheader("Connect to ElevenLabs")
    key_input = st.text_input("API Key", type="password")
    if st.button("Connect"):
        if key_input:
            st.session_state.api_key = key_input
            with st.spinner("Connecting..."):
                connect_to_api(key_input)
        else:
            st.warning("Please enter an API key.")

# Main Interface
if st.session_state.api_connected:
    tab1, tab2, tab3 = st.tabs(["Text to Speech", "Voices", "History"])

    with tab1:
        st.subheader("Text to Speech")
        voice_names = {v["name"]: v["voice_id"] for v in st.session_state.voices}
        selected_name = st.selectbox("Choose Voice", list(voice_names.keys()))
        st.session_state.selected_voice = next((v for v in st.session_state.voices if v["name"] == selected_name), None)

        text_input = st.text_area("Text", height=150)
        with st.expander("Voice Settings"):
            col1, col2 = st.columns(2)
            with col1:
                stability = st.slider("Stability", 0.0, 1.0, 0.5, 0.01)
                similarity = st.slider("Similarity", 0.0, 1.0, 0.75, 0.01)
            with col2:
                style = st.slider("Style", 0.0, 1.0, 0.0, 0.01)

        if st.button("Generate"):
            if not text_input.strip():
                st.warning("Enter some text.")
            else:
                with st.spinner("Generating audio..."):
                    audio = generate_speech(voice_names[selected_name], text_input, stability, similarity, style)
                    if audio:
                        st.session_state.generated_audio = audio
                        add_to_history(text_input, st.session_state.selected_voice, audio)
                        st.success("Done!")

        if st.session_state.generated_audio:
            st.markdown(get_audio_player(st.session_state.generated_audio), unsafe_allow_html=True)
            st.markdown(download_link(st.session_state.generated_audio, f"tts_{int(time.time())}.mp3"), unsafe_allow_html=True)

    with tab2:
        st.subheader("Voices")
        search = st.text_input("Search Voices")
        filtered = [v for v in st.session_state.voices if search.lower() in v.get("name", "").lower()] if search else st.session_state.voices

        cols = st.columns(2)
        for i, v in enumerate(filtered):
            try:
                with cols[i % 2]:
                    st.markdown(f"#### {v.get('name', 'Unnamed')}")
                    st.caption(v.get("description", "No description"))
                    preview = get_voice_preview(v.get("preview_url")) if v.get("preview_url") else None
                    if preview:
                        st.markdown(get_audio_player(preview), unsafe_allow_html=True)
                    if st.button("Use Voice", key=f"use_{v.get('voice_id')}"):
                        st.session_state.selected_voice = v
                        st.success(f"Selected: {v.get('name')}")
            except Exception as e:
                st.warning(f"Could not load voice: {e}")

    with tab3:
        st.subheader("History")
        if not st.session_state.history:
            st.info("No history yet.")
        for item in st.session_state.history:
            st.write(item["text"][:100] + ("..." if len(item["text"]) > 100 else ""))
            st.caption(f"Voice: {item['voice']} | {item['timestamp']}")
            st.markdown(get_audio_player(item["audio"]), unsafe_allow_html=True)
            st.markdown(download_link(item["audio"], f"voice_{item['id']}.mp3"), unsafe_allow_html=True)
