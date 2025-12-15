import streamlit as st
import json
import os
from streamlit_advanced_audio import audix, WaveSurferOptions
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

def create_waveform_player_from_path(audio_path):
    """Create an interactive waveform player from a file path."""
    try:
        if not os.path.exists(audio_path):
            st.error(f"Audio file not found: {audio_path}")
            return
        
        # Get file info
        file_size = os.path.getsize(audio_path)
        file_name = os.path.basename(audio_path)
        
        st.info(f"📁 {file_name} ({file_size / 1024 / 1024:.2f} MB)")
        
        # Configure WaveSurfer options with custom styling
        options = WaveSurferOptions(
            wave_color="#1DB954",
            progress_color="#1ed760",
            cursor_color="#1DB954",
            height=120,
            bar_height=2,
            bar_width=2,
            bar_radius=2,
            normalize=True
        )
        
        # Create the interactive player
        audix(audio_path, wavesurfer_options=options)
            
    except Exception as e:
        print(f"Error in create_waveform_player_from_path: {str(e)}")
        st.warning(f"⚠️ Could not create waveform player: {str(e)}")
        st.audio(audio_path)

def create_waveform_player(audio_file):
    """Create an interactive waveform player using streamlit_advanced_audio."""
    try:
        # Check if audio_file is a file path (string) or uploaded file object
        if isinstance(audio_file, str):
            # It's already a file path
            create_waveform_player_from_path(audio_file)
            return
        
        # It's an uploaded file object
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        file_ext = audio_file.name.split('.')[-1].lower()
        temp_audio_path = os.path.join(temp_dir, f"preview_audio.{file_ext}")
        
        with open(temp_audio_path, "wb") as f:
            f.write(audio_file.getbuffer())
        
        st.info(f"📁 {audio_file.name} ({audio_file.size / 1024 / 1024:.2f} MB)")
        
        options = WaveSurferOptions(
            wave_color="#1DB954",
            progress_color="#1ed760",
            cursor_color="#1DB954",
            height=120,
            bar_height=2,
            bar_width=2,
            bar_radius=2,
            normalize=True
        )
        
        audix(temp_audio_path, wavesurfer_options=options)
            
    except Exception as e:
        print(f"Error in create_waveform_player: {str(e)}")
        st.warning(f"⚠️ Could not create waveform player: {str(e)}")
        if hasattr(audio_file, 'name'):
            file_ext = audio_file.name.split('.')[-1] if '.' in audio_file.name else 'mp3'
            st.audio(audio_file, format=f"audio/{file_ext}")

def create_stacked_multitrack_player(instruments, current_muted):
    """Create a stacked multi-track player with waveforms like a DAW."""
    st.subheader("🎚️ Multi-Track Studio")
    
    # Color mapping for instruments
    track_colors = {
        'drums': ('#ff4444', '#ff6666'),      # Red
        'bass': ('#4444ff', '#6666ff'),       # Blue
        'guitar': ('#44ff44', '#66ff66'),     # Green
        'vocals': ('#ff44ff', '#ff66ff'),     # Purple
        'piano': ('#ffff44', '#ffff66'),      # Yellow
        'other': ('#888888', '#aaaaaa')       # Gray
    }
    
    track_states = {}
    
    # Playback controls at the top - simplified
    control_col1, control_col2 = st.columns([1, 3])
    
    with control_col1:
        play_pause = st.button("▶️ Play / ⏸️ Pause", key="master_play_pause", use_container_width=True)
        if play_pause:
            st.session_state.is_playing = not st.session_state.get('is_playing', False)
    
    with control_col2:
        master_volume = st.slider("🔊 Master Volume", 0, 100, 100, key="master_volume")
    
    st.markdown("---")
    
    # Individual tracks stacked vertically
    for inst_name, files in instruments.items():
        # Get colors for this instrument
        wave_color, progress_color = track_colors.get(inst_name, track_colors['other'])
        
        # Track container with custom styling
        with st.container():
            # Track header with controls - simplified
            header_col1, header_col2, header_col3, header_col4 = st.columns([2, 0.5, 0.5, 2])
            
            with header_col1:
                st.markdown(f"### {inst_name.upper()}")
            
            with header_col2:
                is_muted = st.checkbox("M", value=(inst_name == current_muted), 
                                      key=f"mute_{inst_name}", help="Mute")
            
            with header_col3:
                is_solo = st.checkbox("S", value=False, 
                                     key=f"solo_{inst_name}", help="Solo")
            
            with header_col4:
                volume = st.slider(f"Vol", 0, 100, 100, 
                                 key=f"vol_{inst_name}",
                                 label_visibility="collapsed")
            
            # Waveform display for this track
            if files['audio'] and os.path.exists(files['audio']):
                options = WaveSurferOptions(
                    wave_color=wave_color,
                    progress_color=progress_color,
                    cursor_color=progress_color,
                    height=80,
                    bar_height=1,
                    bar_width=2,
                    bar_radius=2,
                    normalize=True
                )
                
                try:
                    audix(files['audio'], wavesurfer_options=options, key=f"wave_{inst_name}")
                except Exception as e:
                    st.caption(f"🎵 {os.path.basename(files['audio'])}")
            else:
                st.caption("⚠️ No audio file")
            
            track_states[inst_name] = {
                'muted': is_muted,
                'solo': is_solo,
                'volume': (volume / 100.0) * (master_volume / 100.0)
            }
            
            st.markdown("---")
    
    return track_states

# Main Single Page Layout
st.header("📤 Upload Audio File")

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav", "m4a"])
    
    # Check if a new file was uploaded by comparing file names and sizes
    if uploaded_file is not None:
        current_file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        previous_file_id = st.session_state.get("current_file_id", None)
        
        # If this is a new file (different name or size), update everything
        if current_file_id != previous_file_id:
            st.success("✅ File uploaded successfully!")
            st.session_state.audio_data = uploaded_file
            st.session_state.current_file_id = current_file_id
            
            # Clear previous processing state when new file is uploaded
            if "process_completed" in st.session_state:
                del st.session_state.process_completed
            if "results_folder" in st.session_state:
                del st.session_state.results_folder
        
        # Show interactive waveform player when file is uploaded
        create_waveform_player(uploaded_file)
        #st.info(f"📁 {uploaded_file.name} ({uploaded_file.size / 1024 / 1024:.2f} MB)")
    else:
        # Clear session state when no file is uploaded
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
                # Create temp directory if it doesn't exist
                os.makedirs("temp", exist_ok=True)
                
                # Save uploaded file temporarily with proper extension
                uploaded_file = st.session_state.audio_data
                file_extension = uploaded_file.name.split('.')[-1].lower() if uploaded_file.name else 'mp3'
                temp_file_path = f"temp/temp_upload.{file_extension}"
                # Remove previous temp file if it exists to avoid conflicts
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Verify file was created and has content
                if not os.path.exists(temp_file_path) or os.path.getsize(temp_file_path) == 0:
                    st.error("Failed to save uploaded file properly")
                else:
                    print(f"Saved uploaded file to {temp_file_path} ({os.path.getsize(temp_file_path)} bytes)")
                    
                    # Use imported function from main.py
                    with st.spinner("Processing audio with Music.AI..."):
                        result = process_audio_with_music_ai(
                            api_key=API_KEY,
                            workflow_name=WORKFLOW_NAME,
                            mp3_file_path=temp_file_path,
                            output_dir="results/api",  # API results go to results/api
                            verbose=True
                        )
                        print(f"Music.AI processing result: {result}")
                    
                    if result["success"]:
                        st.success("✅ Job completed successfully!")
                        # Set the results folder for the unified workflow
                        st.session_state.results_folder = "results/api"
                        st.session_state.process_completed = True

                        # Clean up temp file
                        if os.path.exists(temp_file_path):
                            os.remove(temp_file_path)
                            print(f"Cleaned up temp file: {temp_file_path}")
                    else:
                        st.error(f"Job failed: {result.get('message', 'Unknown error')}")
                        st.session_state.show_backup_upload = True
            
            except Exception as e:
                st.error(f"Error processing with Music.AI: {str(e)}")
                # Clean up temp file in case of error
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
            # Set the results folder for the unified workflow
            st.session_state.results_folder = "results/demo"
            st.session_state.process_completed = True
            st.success("✅ Demo loaded successfully!")
    
    with col2_2:
        if st.button("📂 Load API Results", key="load_api_results"):
            # Check if API results exist
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
    
    # If both backup files are loaded, automatically sync
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
        
        instruments = get_instruments(chords_files=chords_files, stem_files=stem_files)
        
        if instruments:
            # Stacked multi-track mixer UI
            track_states = create_stacked_multitrack_player(
                instruments, 
                st.session_state.get("current_muted", list(instruments.keys())[0])
            )
            
            # Determine which tracks to play based on mute/solo states
            has_solo = any(state['solo'] for state in track_states.values())
            active_tracks = []
            
            for inst_name, state in track_states.items():
                audio_file = instruments[inst_name]['audio']
                if audio_file and os.path.exists(audio_file):
                    if has_solo:
                        if state['solo']:
                            active_tracks.append((audio_file, state['volume']))
                    else:
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
            st.warning("No instruments found with valid chord data.")
    else:
        st.error(f"Results folder not found: {results_folder}")
