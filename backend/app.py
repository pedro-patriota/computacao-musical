import streamlit as st
import json
import os
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

def find_latest_json_files(output_dir):
    """Find the latest generated JSON files in the output directory."""
    lyrics_file = None
    chords_file = None
    
    if os.path.exists(output_dir):
        files = os.listdir(output_dir)
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(output_dir, file)
                if "lyrics" in file.lower():
                    lyrics_file = file_path
                elif "piano" in file.lower() or "chord" in file.lower():
                    chords_file = file_path
    
    print(f"Found lyrics file: {lyrics_file}")
    print(f"Found chords file: {chords_file}")
    return lyrics_file, chords_file

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
        
        # Always show audio player when file is uploaded
        st.audio(uploaded_file, format="audio/mp3")
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
    st.header("🎵 Play Along")
    
    results_folder = st.session_state.results_folder
    
    # Gather all stems and chord files from the selected folder
    if os.path.exists(results_folder):
        files = os.listdir(results_folder)
        chords_files = [os.path.join(results_folder, f) for f in files if f.endswith("_chords.json")]
        stem_files = [os.path.join(results_folder, f) for f in files if f.endswith(".wav")]
        lyrics_file = os.path.join(results_folder, "lyrics.json")
        
        # Load all available instruments and their files
        instruments = get_instruments(chords_files=chords_files, stem_files=stem_files)
        
        instrument_options = list(instruments.keys())
        if not instrument_options:
            st.error(f"No instruments found in {results_folder} folder.")
        else:
            # Instrument selection
            current_muted = st.selectbox(
                "Select the instrument you want to play along with (muted):",
                instrument_options,
                index=0,
                key="mute_select"
            )
            
            # Check if instrument changed to recalculate chords
            if "current_muted" not in st.session_state or st.session_state.current_muted != current_muted or "current_folder" not in st.session_state or st.session_state.current_folder != results_folder:
                st.session_state.current_muted = current_muted
                st.session_state.current_folder = results_folder
                
                # Load lyrics and chords for the muted instrument
                with open(lyrics_file, 'r') as f:
                    lyrics_data = json.load(f)
                chords_filepath = instruments[current_muted]['chords']
                with open(chords_filepath, 'r') as f:
                    chords_data = json.load(f)
                
                # Sync lyrics and chords
                st.session_state.synced_data = sync_lyrics_with_chords(lyrics_data, chords_data, verbose=False)
                st.session_state.chords_filepath = chords_filepath
                st.session_state.stem_filepath = instruments[current_muted]['audio']
            
            # Get active tracks (all except muted)
            active_tracks = []
            active_track_names = []
            for inst, files in instruments.items():
                if inst != current_muted and files['audio']:
                    active_tracks.append(files['audio'])
                    active_track_names.append(inst.title())
            
            # === AUDIO EFFECTS CONTROLS ===
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                tempo = st.slider("Tempo", 0.5, 2.0, 1.0, 0.1, label_visibility="collapsed", key="tempo_slider")
                st.caption("🎚️ Tempo")
            
            with col2:
                reverb = st.slider("Reverb", 0.0, 1.0, 0.0, 0.1, label_visibility="collapsed", key="reverb_slider")
                st.caption("🔊 Reverb")
            
            with col3:
                st.write("")  # spacing
            
            if active_tracks:
                st.write(f"**Playing:** {' + '.join(active_track_names)}")
                st.write(f"**Muted for play-along:** {current_muted.title()}")
                
                # Use a single reusable mixed file (overwrite each time)
                mixed_file_path = os.path.join(results_folder, "mixed_playback.wav")
                
                # Always regenerate the mixed file for the current selection
                with st.spinner("Mixing audio tracks..."):
                    try:
                        mixed_path = mix_audio_files(active_tracks, mixed_file_path)
                        if mixed_path and os.path.exists(mixed_path):
                            # Apply effects if not at default values
                            if tempo != 1.0 or reverb != 0.0:
                                from audio_processor import AudioProcessor
                                processor = AudioProcessor(mixed_path)
                                processed_audio = processor.process(tempo=tempo, reverb=reverb)
                                st.audio(processed_audio, sample_rate=processor.sr, format="audio/wav")
                            else:
                                st.audio(mixed_path, format="audio/wav")
                        else:
                            st.error("Failed to mix audio tracks")
                    except Exception as e:
                        st.error(f"Error mixing audio: {e}")
            
            # Show chords for the muted instrument
            if "synced_data" in st.session_state:
                st.subheader(f"🎼 Chord Guide")
                stem_filepath = st.session_state.stem_filepath
                chords_filepath = st.session_state.chords_filepath
                synced_data = st.session_state.synced_data
                
                sliced_chords, sr = extract_chord_segments(stem_filepath, chords_filepath) if stem_filepath else (None, None)
                display_synced_lyrics(synced_data, sliced_chords, sr)
    else:
        st.error(f"Results folder {results_folder} not found.")
