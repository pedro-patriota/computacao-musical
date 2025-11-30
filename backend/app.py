import streamlit as st
import json
import os
from main import process_audio_with_music_ai
from chrodsSync import sync_lyrics_with_chords, load_json_files
from display import display_synced_lyrics
from slice_audio import extract_chord_segments
from utils import select_guitar_or_piano
from constants import *

# Set page config
st.set_page_config(
    page_title="Lyrics & Chords Sync",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🎵 Lyrics & Chords Synchronizer")

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
    uploaded_file = st.file_uploader("Choose an MP3 file", type=["mp3", "wav", "m4a"])
    
    if uploaded_file is not None:
        st.success("✅ File uploaded successfully!")
        st.audio(uploaded_file, format="audio/mp3")
        
        # Save to session state
        if "audio_data" not in st.session_state:
            st.session_state.audio_data = uploaded_file
        
        # Show file info
        st.info(f"File size: {uploaded_file.size / 1024 / 1024:.2f} MB")

st.divider()
st.header("⚙️ Process Audio with Music.AI")

# Check for pre-existing JSON files from results folder
lyrics_file, chords_file = find_latest_json_files(DEMO_DIR)
pre_existing_files = lyrics_file and chords_file

if pre_existing_files and "synced_data" not in st.session_state:
    st.info("📁 Found pre-existing JSON files in the results folder. Loading...")
    with st.spinner("Loading pre-existing data..."):
        lyrics_data, chords_data = load_json_files(lyrics_file, chords_file)
        if lyrics_data and chords_data:
            # Automatically sync
            with st.spinner("Synchronizing lyrics with chords..."):
                synced_result = sync_lyrics_with_chords(lyrics_data, chords_data, verbose=False)
                if synced_result:
                    st.session_state.synced_data = synced_result
                    st.success(f"✅ Loaded and synchronized data from:\n- {os.path.basename(lyrics_file)}\n- {os.path.basename(chords_file)}")

if "audio_data" in st.session_state and st.session_state.audio_data:
    if st.button("🚀 Process with Music.AI", key="process_music_ai"):
        try:
            # Save uploaded file temporarily
            temp_file_path = "temp_upload.mp3"
            with open(temp_file_path, "wb") as f:
                f.write(st.session_state.audio_data.getbuffer())
            print(f"Saved uploaded file to {temp_file_path}")
            
            # Use imported function from main.py
            with st.spinner("Processing audio with Music.AI..."):
                result = process_audio_with_music_ai(
                    api_key=API_KEY,
                    workflow_name=WORKFLOW_NAME,
                    mp3_file_path=temp_file_path,
                    output_dir=OUTPUT_DIR,
                    verbose=True
                )
                print(f"Music.AI processing result: {result}")
            
            if result["success"]:
                st.success("✅ Job completed successfully!")
                    
                # Load the generated JSON files
                lyrics_file = result.get("lyrics_file")
                chords_files = result.get("chords_files")
                stem_files = result.get("stem_files", [])
                stem_file = None
                chords_file = None
                file_type = None

                chords_file, stem_file = select_guitar_or_piano(chords_files, stem_files)
                print(f"Selected chords file: {chords_file}")
                print(f"Selected stem file: {stem_file}")

                if lyrics_file and chords_file:
                    with open(lyrics_file, 'r') as f:
                        lyrics_data = json.load(f)
                    with open(chords_file, 'r') as f:
                        chords_data = json.load(f)
                    
                    # Automatically run chords sync
                    with st.spinner("Synchronizing lyrics with chords..."):
                        synced_result = sync_lyrics_with_chords(lyrics_data, chords_data, verbose=False)
                        if synced_result:
                            st.session_state.chords_filepath = chords_file
                            st.session_state.stem_filepath = stem_file
                            st.session_state.synced_data = synced_result
                            st.success("✅ Synchronization completed!")

                # Clean up
                os.remove(temp_file_path)
            else:
                st.error(f"Job failed: {result.get('message', 'Unknown error')}")
                st.session_state.show_backup_upload = True
        
        except Exception as e:
            st.error(f"Error processing with Music.AI: {str(e)}")
            st.session_state.show_backup_upload = True
else:
    if not pre_existing_files:
        st.info("👈 Please upload an audio file first")

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

# Display synced lyrics if available
if "synced_data" in st.session_state:
    st.divider()
    st.header("🎼 Synchronized Lyrics with Chords")

    demo_chords_file_path, demo_stem_file_path = select_guitar_or_piano(
        chords_files=[DEMO_DIR + "/guitar_chords_file.json", DEMO_DIR + "/piano_chords_file.json"],
        stem_files=[DEMO_DIR + "/guitar_stem.wav", DEMO_DIR + "/piano_stem.wav"]
    )
    
    synced_data = st.session_state.synced_data
    stem_filepath = st.session_state.get("stem_filepath", demo_stem_file_path)
    chords_filepath = st.session_state.get("chords_filepath", demo_chords_file_path)

    print(f"Using stem file: {stem_filepath}")
    print(f"Using chords file: {chords_filepath}")

    sliced_chords, sr = extract_chord_segments(stem_filepath, chords_filepath)
    display_synced_lyrics(synced_data, sliced_chords, sr)
    
    # Download section
    st.divider()
    st.subheader("📥 Download Results")
    
    # Create text output
    text_output = ' '.join([item['word'] for item in synced_data])
    
    # Create JSON output
    json_output = json.dumps(synced_data, indent=2)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📄 Download as Text",
            data=text_output,
            file_name="lyrics_with_chords.txt",
            mime="text/plain"
        )
    
    with col2:
        st.download_button(
            label="📊 Download as JSON",
            data=json_output,
            file_name="synced_lyrics.json",
            mime="application/json"
        )
