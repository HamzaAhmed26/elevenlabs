import streamlit as st
import requests
import json
import time
import base64
from io import BytesIO
import os

# Set page configuration
st.set_page_config(
    page_title="Voice Lab",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a cleaner look
st.markdown("""
<style>
    .main {
        background-color: #f8fafc;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .css-18e3th9 {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3, h4 {
        color: #1e293b;
    }
    .stButton>button {
        background-color: #2563eb;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #1e40af;
    }
    .voice-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    .voice-card:hover {
        border-color: #2563eb;
    }
    .selected-card {
        border-color: #2563eb;
        background-color: rgba(37, 99, 235, 0.05);
    }
    .history-item {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    .audio-player {
        width: 100%;
        margin-top: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        color: #1e293b;
        padding: 10px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: transparent;
        border-bottom: 2px solid #2563eb;
        color: #2563eb;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'voices' not in st.session_state:
    st.session_state.voices = []
if 'selected_voice' not in st.session_state:
    st.session_state.selected_voice = None
if 'history' not in st.session_state:
    st.session_state.history = []
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False
if 'generated_audio' not in st.session_state:
    st.session_state.generated_audio = None

# Function to connect to ElevenLabs API
def connect_to_api(api_key):
    try:
        response = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": api_key}
        )
        
        if response.status_code == 200:
            voices_data = response.json()
            st.session_state.voices = voices_data.get("voices", [])
            st.session_state.api_connected = True
            return True
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return False

# Function to generate speech
def generate_speech(voice_id, text, stability, similarity, style):
    try:
        response = requests.post(
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
        
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error generating speech: {str(e)}")
        return None

# Function to get voice preview
def get_voice_preview(preview_url):
    try:
        response = requests.get(preview_url)
        if response.status_code == 200:
            return response.content
        else:
            return None
    except:
        return None

# Function to get audio player HTML
def get_audio_player(audio_bytes):
    audio_base64 = base64.b64encode(audio_bytes).decode()
    audio_player = f"""
        <audio controls class="audio-player">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
    """
    return audio_player

# Function to add to history
def add_to_history(text, voice_data, audio_bytes):
    voice_name = voice_data.get("name", "Unknown")
    voice_id = voice_data.get("voice_id", "")
    
    history_item = {
        "id": str(time.time()),
        "text": text,
        "voice": voice_name,
        "voice_id": voice_id,
        "audio": audio_bytes,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    st.session_state.history.insert(0, history_item)
    
    # Limit history to 20 items
    if len(st.session_state.history) > 20:
        st.session_state.history = st.session_state.history[:20]

# Function to download audio
def get_audio_download_link(audio_bytes, filename="audio.mp3"):
    b64 = base64.b64encode(audio_bytes).decode()
    href = f'<a href="data:audio/mp3;base64,{b64}" download="{filename}">Download Audio</a>'
    return href

# ---- UI LAYOUT ----
# Header
st.title("Voice Lab")
st.markdown("*A minimalist interface for ElevenLabs text-to-speech*")

# API Key Input
if not st.session_state.api_connected:
    with st.container():
        st.subheader("Connect to ElevenLabs API")
        api_key = st.text_input("Enter your ElevenLabs API Key", type="password")
        if st.button("Connect"):
            if api_key:
                st.session_state.api_key = api_key
                with st.spinner("Connecting to ElevenLabs API..."):
                    if connect_to_api(api_key):
                        st.success("Connected successfully!")
                    else:
                        st.error("Failed to connect. Please check your API key and try again.")
            else:
                st.warning("Please enter an API key")

# Main Content
if st.session_state.api_connected:
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Text to Speech", "Voices", "History"])
    
    # Text to Speech Tab
    with tab1:
        st.subheader("Text to Speech")
        
        # Voice selection
        voice_options = {voice["name"]: voice["voice_id"] for voice in st.session_state.voices}
        selected_voice_name = st.selectbox(
            "Select Voice",
            options=list(voice_options.keys()),
            index=0 if voice_options else None
        )
        
        if selected_voice_name:
            selected_voice_id = voice_options[selected_voice_name]
            st.session_state.selected_voice = next(
                (voice for voice in st.session_state.voices if voice["voice_id"] == selected_voice_id),
                None
            )
        
        # Text input
        text_input = st.text_area("Enter text to convert to speech", height=150)
        
        # Voice settings
        with st.expander("Voice Settings", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                stability = st.slider(
                    "Stability",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.01,
                    help="Higher values make voice more consistent but may sound flatter"
                )
                
                similarity = st.slider(
                    "Clarity/Similarity",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.75,
                    step=0.01,
                    help="Higher values make voice more similar to original but may reduce clarity"
                )
            
            with col2:
                style = st.slider(
                    "Style",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0,
                    step=0.01,
                    help="Higher values enhance speaking style but may affect consistency"
                )
        
        # Generate button
        if st.button("Generate Speech"):
            if not text_input.strip():
                st.warning("Please enter some text")
            elif not st.session_state.selected_voice:
                st.warning("Please select a voice")
            else:
                with st.spinner("Generating speech..."):
                    audio_bytes = generate_speech(
                        selected_voice_id,
                        text_input,
                        stability,
                        similarity,
                        style
                    )
                    
                    if audio_bytes:
                        st.session_state.generated_audio = audio_bytes
                        add_to_history(text_input, st.session_state.selected_voice, audio_bytes)
                        st.success("Speech generated successfully!")
        
        # Display audio player if available
        if st.session_state.generated_audio:
            st.subheader("Generated Audio")
            st.markdown(get_audio_player(st.session_state.generated_audio), unsafe_allow_html=True)
            st.markdown(
                get_audio_download_link(
                    st.session_state.generated_audio, 
                    f"voice_{selected_voice_name}_{int(time.time())}.mp3"
                ),
                unsafe_allow_html=True
            )
    
    # Voices Tab
    with tab2:
        st.subheader("Available Voices")
        
        # Search box
        search_term = st.text_input("Search voices", "")
        
        # Filter voices based on search
        filtered_voices = st.session_state.voices
        if search_term:
            search_term = search_term.lower()
            filtered_voices = [
                voice for voice in st.session_state.voices
                if search_term in voice.get("name", "").lower() or 
                   search_term in voice.get("description", "").lower()
            ]
        
        # Display voices in a grid
        if filtered_voices:
            # Create columns for grid layout
            cols = st.columns(2)
            
            for i, voice in enumerate(filtered_voices):
                col_idx = i % 2
                
                with cols[col_idx]:
                    is_selected = st.session_state.selected_voice and st.session_state.selected_voice.get("voice_id") == voice.get("voice_id")
                    card_class = "voice-card selected-card" if is_selected else "voice-card"
                    
                    with st.container():
                        st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
                        
                        st.markdown(f"### {voice.get('name', 'Unnamed Voice')}")
                        st.write(voice.get("description", "No description available"))
                        
                        # Preview button if preview URL exists
                        preview_url = voice.get("preview_url")
                        if preview_url:
                            preview_bytes = get_voice_preview(preview_url)
                            if preview_bytes:
                                st.markdown(get_audio_player(preview_bytes), unsafe_allow_html=True)
                        
                        # Use voice button
                        if st.button("Use This Voice", key=f"use_voice_{voice.get('voice_id')}"):
                            st.session_state.selected_voice = voice
                            # Switch to Text to Speech tab programmatically not possible in Streamlit
                            # So we'll just notify the user
                            st.success(f"Selected voice: {voice.get('name')}. Please go to the Text to Speech tab to use it.")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No voices found matching your search criteria")
    
    # History Tab
    with tab3:
        st.subheader("Your Voice History")
        
        if not st.session_state.history:
            st.info("No history items yet. Generate some speech to see it here.")
        else:
            for item in st.session_state.history:
                with st.container():
                    st.markdown('<div class="history-item">', unsafe_allow_html=True)
                    
                    # Truncate text if it's too long
                    display_text = item["text"] if len(item["text"]) <= 100 else item["text"][:100] + "..."
                    st.write(display_text)
                    
                    # Voice info and timestamp
                    st.caption(f"**Voice:** {item['voice']} • **Date:** {item['timestamp']}")
                    
                    # Audio player
                    st.markdown(get_audio_player(item["audio"]), unsafe_allow_html=True)
                    
                    # Action buttons
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Use This Voice", key=f"history_use_voice_{item['id']}"):
                            voice_id = item["voice_id"]
                            # Find the voice in the voices list
                            selected_voice = next(
                                (voice for voice in st.session_state.voices if voice["voice_id"] == voice_id),
                                None
                            )
                            if selected_voice:
                                st.session_state.selected_voice = selected_voice
                                st.success(f"Selected voice: {item['voice']}. Please go to the Text to Speech tab to use it.")
                    
                    with col2:
                        st.markdown(
                            get_audio_download_link(
                                item["audio"], 
                                f"voice_{item['voice']}_{item['id']}.mp3"
                            ),
                            unsafe_allow_html=True
                        )
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.write(f"Using API Key: {api_key[:4]}... (truncated for security)")

# Footer
st.markdown("---")
st.caption("Voice Lab - Powered by ElevenLabs API")
