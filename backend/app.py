import streamlit as st
import json
import os
import plotly.graph_objects as go
import librosa
import numpy as np
from main import process_audio_with_music_ai
from chordsSync import sync_lyrics_with_chords, load_json_files
from display import display_synced_lyrics
from slice_audio import extract_chord_segments
from utils import get_instruments, mix_audio_files
from constants import *

# Set page config
st.set_page_config(
    page_title="Play Along",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🎵 Play Along Generator")


def render_waveform(audio_path, color, inst_name):
    """Render compact waveform visualization using librosa and plotly."""
    if audio_path and os.path.exists(audio_path):
        try:
            y, sr = librosa.load(audio_path, sr=None, mono=True)
            downsample = max(1, len(y) // 2000)
            y_vis = y[::downsample]
            time_axis = np.arange(len(y_vis)) * downsample / sr

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=time_axis, y=y_vis,
                fill='tozeroy',
                line=dict(color=color, width=1),
                hovertemplate='<b>%{x:.2f}s</b><extra></extra>'
            ))
            fig.update_layout(
                xaxis_title="",
                yaxis_title="",
                height=50,
                margin=dict(l=0, r=0, t=0, b=0),
                hovermode='x unified',
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False, showticklabels=False),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        except Exception as e:
            st.caption(f"🎵 {os.path.basename(audio_path)}")
    else:
        st.caption("⚠️ No audio")


def create_stacked_multitrack_player(instruments, current_muted):
    """Compact stacked multi-track player with librosa/plotly waveforms."""
    
    # Initialize session state for mute tracking
    if 'muted_instruments' not in st.session_state:
        st.session_state.muted_instruments = set()
    
    # Top controls: just the Instrument selector
    instrument_options = list(instruments.keys()) + ["Custom"]
    
    # Determine selectbox index based on muted instruments
    if len(st.session_state.muted_instruments) == 1:
        muted_inst = list(st.session_state.muted_instruments)[0]
        if muted_inst in instrument_options:
            default_index = instrument_options.index(muted_inst)
        else:
            default_index = len(instrument_options) - 1
    else:
        default_index = len(instrument_options) - 1  # "Custom"
    
    selected_instrument = st.selectbox(
        "🎸 Play Along (mute):", 
        instrument_options, 
        index=default_index,
        key="play_along_instrument"
    )
    
    # Update muted_instruments based on selectbox selection
    if selected_instrument != "Custom":
        st.session_state.muted_instruments = {selected_instrument}

    track_colors = {
        'drums': '#ff4444',
        'bass': '#4444ff',
        'guitar': '#44ff44',
        'vocals': '#ff44ff',
        'piano': '#ffff44',
        'other': '#888888'
    }

    track_states = {}

    # Compact track rows
    for inst_name, files in instruments.items():
        color = track_colors.get(inst_name, track_colors['other'])
        
        is_muted_now = inst_name in st.session_state.muted_instruments
        highlight = "🎯 " if is_muted_now else ""
        
        # Compact row: Name | Mute | Volume | Waveform
        c1, c2, c3, c4 = st.columns([1, 0.5, 1.5, 7])

        with c1:
            st.markdown(f"**{highlight}{inst_name.upper()}**")

        with c2:
            def update_mute(inst=inst_name):
                is_checked = st.session_state.get(f"mute_{inst}", False)
                if is_checked:
                    st.session_state.muted_instruments.add(inst)
                else:
                    st.session_state.muted_instruments.discard(inst)
            
            st.checkbox("M", value=is_muted_now, 
                       key=f"mute_{inst_name}", help="Mute",
                       on_change=update_mute, args=(inst_name,))

        with c3:
            vol = st.slider("", 0, 100, 100, key=f"vol_{inst_name}", 
                           label_visibility="collapsed")
            per_track_volume = vol / 100.0

        with c4:
            render_waveform(files['audio'], color, inst_name)

        track_states[inst_name] = {
            'muted': is_muted_now,
            'volume': per_track_volume
        }

    return track_states


# Main Single Page Layout
st.header("📤 Upload Audio File")

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a"])
    
    if uploaded_file is not None:
        current_file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        previous_file_id = st.session_state.get("current_file_id", None)
        
        if current_file_id != previous_file_id:
            st.success("✅ File uploaded successfully!")
            st.session_state.audio_data = uploaded_file
            st.session_state.current_file_id = current_file_id
            
            if "process_completed" in st.session_state:
                del st.session_state.process_completed
            if "results_folder" in st.session_state:
                del st.session_state.results_folder
        
        st.info(f"📁 {uploaded_file.name} ({uploaded_file.size / 1024 / 1024:.2f} MB)")
        st.audio(uploaded_file)
    else:
        if "audio_data" in st.session_state:
            del st.session_state.audio_data
        if "current_file_id" in st.session_state:
            del st.session_state.current_file_id

st.divider()
st.header("⚙️ Process Audio")

col1, col2 = st.columns(2)

with col1:
    if "audio_data" in st.session_state and st.session_state.audio_data:
        if st.button("🚀 Process with Music.AI", key="process_music_ai"):
            try:
                os.makedirs("temp", exist_ok=True)
                
                uploaded_file = st.session_state.audio_data
                file_extension = uploaded_file.name.split('.')[-1].lower() if uploaded_file.name else 'mp3'
                temp_file_path = f"temp/temp_upload.{file_extension}"
                
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                if not os.path.exists(temp_file_path) or os.path.getsize(temp_file_path) == 0:
                    st.error("Failed to save uploaded file properly")
                else:
                    with st.spinner("Processing audio with Music.AI..."):
                        result = process_audio_with_music_ai(
                            api_key=API_KEY,
                            workflow_name=WORKFLOW_NAME,
                            mp3_file_path=temp_file_path,
                            output_dir="results/api",
                            verbose=True
                        )
                    
                    if result["success"]:
                        st.success("✅ Job completed successfully!")
                        st.session_state.results_folder = "results/api"
                        st.session_state.process_completed = True

                        if os.path.exists(temp_file_path):
                            os.remove(temp_file_path)
                    else:
                        st.error(f"Job failed: {result.get('message', 'Unknown error')}")
                        st.session_state.show_backup_upload = True
            
            except Exception as e:
                st.error(f"Error processing with Music.AI: {str(e)}")
                temp_file_path = f"temp/temp_upload.{st.session_state.audio_data.name.split('.')[-1] if st.session_state.audio_data.name else 'mp3'}"
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                st.session_state.show_backup_upload = True
    else:
        st.info("👈 Please upload an audio file first")

with col2:
    col2_1, col2_2 = st.columns(2)
    
    with col2_1:
        if st.button("🧪 Load Demo", key="load_demo"):
            st.session_state.results_folder = "results/demo"
            st.session_state.process_completed = True
            st.success("✅ Demo loaded successfully!")
    
    with col2_2:
        if st.button("📂 Load API Results", key="load_api_results"):
            if os.path.exists("results/api") and os.path.exists("results/api/lyrics.json"):
                st.session_state.results_folder = "results/api"
                st.session_state.process_completed = True
                st.success("✅ API results loaded successfully!")
            else:
                st.error("No API results found. Process a file first or check results/api folder.")

# Show backup file upload only if processing failed
if st.session_state.get("show_backup_upload", False):
    st.divider()
    st.header("📁 Backup: Upload JSON Files")
    st.warning("If Music.AI processing failed, you can upload pre-existing lyrics and chords JSON files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        lyrics_json = st.file_uploader("Upload Lyrics JSON", type=["json"], key="lyrics")
        if lyrics_json:
            st.session_state.lyrics_data = json.load(lyrics_json)
            st.success("✅ Lyrics file loaded!")
    
    with col2:
        chords_json = st.file_uploader("Upload Chords JSON", type=["json"], key="chords")
        if chords_json:
            st.session_state.chords_data = json.load(chords_json)
            st.success("✅ Chords file loaded!")
    
    if "lyrics_data" in st.session_state and "chords_data" in st.session_state and "synced_data" not in st.session_state:
        with st.spinner("Synchronizing lyrics with chords..."):
            synced_result = sync_lyrics_with_chords(st.session_state.lyrics_data, st.session_state.chords_data, verbose=False)
            if synced_result:
                st.session_state.synced_data = synced_result
                st.success("✅ Synchronization completed!")


# --- UNIFIED PLAY-ALONG WORKFLOW ---
if st.session_state.get("process_completed", False):
    st.divider()
    st.header("🎵 Play Along Studio")
    
    results_folder = st.session_state.results_folder
    
    if os.path.exists(results_folder):
        files = os.listdir(results_folder)
        chords_files = [os.path.join(results_folder, f) for f in files if f.endswith("_chords.json")]
        stem_files = [os.path.join(results_folder, f) for f in files if f.endswith(".wav")]
        
        # Load lyrics and chords if not already loaded
        if "synced_data" not in st.session_state:
            lyrics_path = os.path.join(results_folder, "lyrics.json")
            chords_path = os.path.join(results_folder, "chords.json")
            
            if os.path.exists(lyrics_path) and os.path.exists(chords_path):
                try:
                    lyrics_data, chords_data = load_json_files(lyrics_path, chords_path)
                    synced_result = sync_lyrics_with_chords(lyrics_data, chords_data, verbose=False)
                    if synced_result:
                        st.session_state.synced_data = synced_result
                except Exception as e:
                    st.warning(f"Could not load lyrics/chords: {e}")
        
        instruments = get_instruments(chords_files=chords_files, stem_files=stem_files)
        
        if instruments:
            # Display Lyrics and Chords FIRST
            st.subheader("📝 Lyrics & Chords")
            if st.session_state.get("synced_data"):
                display_synced_lyrics(st.session_state.synced_data)
            else:
                st.info("No synced lyrics and chords available.")
            
            st.divider()
            
            # Stacked multi-track mixer UI
            st.subheader("🎚️ Multi-Track Mixer")
            track_states = create_stacked_multitrack_player(
                instruments, 
                st.session_state.get("current_muted", list(instruments.keys())[0])
            )
            
            # Determine which tracks to play
            active_tracks = []
            
            for inst_name, state in track_states.items():
                audio_file = instruments[inst_name]['audio']
                if audio_file and os.path.exists(audio_file):
                    if not state['muted']:
                        active_tracks.append((audio_file, state['volume']))
            
            # Mix and play
            if active_tracks:
                mixed_file_path = os.path.join(results_folder, "studio_mix.wav")
                
                with st.spinner("🎛️ Mixing tracks..."):
                    try:
                        audio_files = [track[0] for track in active_tracks]
                        volumes = [track[1] for track in active_tracks]
                        
                        mixed_path = mix_audio_files(audio_files, mixed_file_path, volumes=volumes)
                        
                        if mixed_path and os.path.exists(mixed_path):
                            st.success("✅ Mix ready!")
                            st.audio(mixed_path)
                    except Exception as e:
                        st.error(f"❌ Error mixing audio: {e}")
            else:
                st.warning("⚠️ Select at least one track to play")
        else:
            st.warning("No instruments found with valid chord data.")
    else:
        st.error(f"Results folder not found: {results_folder}")
