import streamlit as st
import json
import os
from pathlib import Path
from musicai_sdk import MusicAiClient
from main import process_audio_with_music_ai
from chrodsSync import sync_lyrics_with_chords, load_json_files, save_synced_output
import streamlit.components.v1 as components
import html as html_lib

# Set page config
st.set_page_config(
    page_title="Lyrics & Chords Sync",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🎵 Lyrics & Chords Synchronizer")

# Configuration
API_KEY = os.getenv("API_KEY", "")
WORKFLOW_NAME = "criatividade-comp"
OUTPUT_DIR = "results"


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
                elif "guitar" in file.lower() or "chord" in file.lower():
                    chords_file = file_path
    
    return lyrics_file, chords_file


def display_synced_lyrics(synced_data):
    import html as html_lib
    import json
    import streamlit.components.v1 as components

    if not synced_data:
        return

    container_id = "lyrics_container"
    overlay_id = "chord_overlay"

    flowing_html = []
    chord_buttons = []

    for i, item in enumerate(synced_data):
        word = item.get("word", "")
        has_chord = item.get("has_chord", False)

        # chord duration extraction
        duration = 0.4
        if "start" in item and "end" in item:
            duration = max(0.15, item["end"] - item["start"])

        if has_chord and "{" in word and "}" in word:
            chord_start = word.rfind("{")
            chord_end = word.rfind("}")
            chord = word[chord_start+1:chord_end]
            word_text = word[:chord_start] + word[chord_end+1:]

            flowing_html.append(
                f'<span id="word-{i}" style="white-space: pre-wrap;">{html_lib.escape(word_text)}</span>'
            )

            chord_buttons.append({
                "index": i,
                "chord": chord,
                "duration": duration
            })
        else:
            flowing_html.append(
                f'<span style="white-space: pre-wrap;">{html_lib.escape(word)}</span>'
            )

    flowing_html_str = " ".join(flowing_html)

    html = f"""
    <div id="{container_id}" style="
        position: relative;
        background-color: #000;
        color: #fff;
        padding: 28px;
        border-radius: 10px;
        font-family: 'Courier New', monospace;
        font-size: 20px;
        line-height: 3;
        overflow: auto;
        max-height: 420px;
    ">
        <div id="lyrics_flow" style="position: relative; z-index: 1;">
            {flowing_html_str}
        </div>

        <div id="{overlay_id}" style="
            position: absolute;
            left: 0; top: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 2;">
        </div>
    </div>

    <script>
    (function() {{
        const chordSpecs = {json.dumps(chord_buttons)};
        const container = document.getElementById("{container_id}");
        const overlay = document.getElementById("{overlay_id}");

        // Create buttons
        chordSpecs.forEach(spec => {{
            const btn = document.createElement("button");
            btn.className = "chord-btn";
            btn.dataset.index = spec.index;
            btn.dataset.chord = spec.chord;
            btn.dataset.duration = spec.duration;
            btn.innerText = spec.chord;

            Object.assign(btn.style, {{
                position: "absolute",
                pointerEvents: "auto",
                transform: "translateX(-50%)",
                padding: "6px 10px",
                borderRadius: "6px",
                border: "none",
                fontSize: "12px",
                fontWeight: "700",
                cursor: "pointer",
                background: "linear-gradient(135deg, #FFD27F 0%, #FF9D3F 100%)",
                color: "white",
                boxShadow: "0 2px 6px rgba(0,0,0,0.4)"
            }});

            overlay.appendChild(btn);
        }});

        // Audio
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        const audioCtx = new AudioCtx();

        function playChord(chordName, duration) {{

            const baseFreqs = {{
              "C": 261.63, "C#": 277.18, "Db": 277.18,
              "D": 293.66, "D#": 311.13, "Eb": 311.13,
              "E": 329.63,
              "F": 349.23, "F#": 369.99, "Gb": 369.99,
              "G": 392.00, "G#": 415.30, "Ab": 415.30,
              "A": 440.00, "A#": 466.16, "Bb": 466.16,
              "B": 493.88
            }};

            const root = chordName.split(":")[0];
            const base = baseFreqs[root] || 440;

            const isMinor = /m(?!a)/i.test(chordName);
            const third = isMinor ? base * Math.pow(2, 3/12) 
                                  : base * Math.pow(2, 4/12);
            const fifth = base * Math.pow(2, 7/12);

            const freqs = [base, third, fifth];
            const now = audioCtx.currentTime;

            // Musical ADSR with real duration
            const attack = 0.03;
            const decay = 0.12;
            const release = 0.40;

            let sustainTime = Math.max(0.01, duration - attack - decay - release);
            const sustainLevel = 0.45;

            freqs.forEach(freq => {{
                const osc1 = audioCtx.createOscillator();
                const osc2 = audioCtx.createOscillator();
                const osc3 = audioCtx.createOscillator();

                const gain = audioCtx.createGain();

                osc1.type = "sine";
                osc1.frequency.value = freq;

                osc2.type = "triangle";
                osc2.frequency.value = freq * 1.004; // unison detune

                osc3.type = "sine";
                osc3.frequency.value = freq * 2; // overtone

                gain.gain.setValueAtTime(0.0001, now);
                gain.gain.linearRampToValueAtTime(0.8, now + attack);
                gain.gain.linearRampToValueAtTime(sustainLevel, now + attack + decay);

                gain.gain.setValueAtTime(sustainLevel, now + attack + decay + sustainTime);

                gain.gain.exponentialRampToValueAtTime(
                    0.0001,
                    now + attack + decay + sustainTime + release
                );

                osc1.connect(gain);
                osc2.connect(gain);
                osc3.connect(gain);
                gain.connect(audioCtx.destination);

                const totalTime = attack + decay + sustainTime + release;
                osc1.start(now);
                osc2.start(now);
                osc3.start(now);
                osc1.stop(now + totalTime);
                osc2.stop(now + totalTime);
                osc3.stop(now + totalTime);
            }});
        }}

        overlay.addEventListener("click", ev => {{
            const el = ev.target;
            if (el && el.classList.contains("chord-btn")) {{
                if (audioCtx.state === "suspended") audioCtx.resume();
                playChord(el.dataset.chord, parseFloat(el.dataset.duration));
            }}
        }});

        function positionButtons() {{
            const containerRect = container.getBoundingClientRect();

            chordSpecs.forEach(spec => {{
                const wordSpan = document.getElementById("word-" + spec.index);
                const btn = overlay.querySelector('button[data-index="' + spec.index + '"]');

                if (!wordSpan || !btn) return;

                const spanRect = wordSpan.getBoundingClientRect();

                const centerX =
                    spanRect.left - containerRect.left +
                    (spanRect.width / 2) +
                    container.scrollLeft;

                const topY =
                    spanRect.top - containerRect.top +
                    container.scrollTop - 10;

                btn.style.left = centerX + "px";
                btn.style.top = (topY - 26) + "px";
            }});
        }}

        function safeReposition() {{
            requestAnimationFrame(() => requestAnimationFrame(positionButtons));
        }}

        window.addEventListener("load", safeReposition);
        container.addEventListener("scroll", positionButtons);
        window.addEventListener("resize", safeReposition);

        const ro = new MutationObserver(safeReposition);
        ro.observe(document.getElementById("lyrics_flow"), {{
            childList: true,
            subtree: true,
            characterData: true
        }});

        safeReposition();
    }})();
    </script>
    """

    components.html(html, height=450, scrolling=True)



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
lyrics_file, chords_file = find_latest_json_files(OUTPUT_DIR)
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
            
            # Use imported function from main.py
            with st.spinner("Processing audio with Music.AI..."):
                result = process_audio_with_music_ai(
                    api_key=API_KEY,
                    workflow_name=WORKFLOW_NAME,
                    mp3_file_path=temp_file_path,
                    output_dir=OUTPUT_DIR,
                    verbose=False
                )
            
            if result["success"]:
                st.success("✅ Job completed successfully!")
                
                # Load the generated JSON files
                lyrics_file = result.get("lyrics_file")
                chords_file = result.get("chords_file")
                
                if lyrics_file and chords_file:
                    with open(lyrics_file, 'r') as f:
                        lyrics_data = json.load(f)
                    with open(chords_file, 'r') as f:
                        chords_data = json.load(f)
                    
                    # Automatically run chords sync
                    with st.spinner("Synchronizing lyrics with chords..."):
                        synced_result = sync_lyrics_with_chords(lyrics_data, chords_data, verbose=False)
                        if synced_result:
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
    
    synced_data = st.session_state.synced_data
    display_synced_lyrics(synced_data)
    
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
