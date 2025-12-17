import io
import base64
import soundfile as sf
import json
import html as html_lib
import streamlit.components.v1 as components

def display_synced_lyrics(synced_data, sliced_chords, samplerate, show_chords=True):
    """
    Displays lyrics with interactive chord buttons that play real audio segments.
    
    Args:
        synced_data (list): The list of word objects with chords.
        sliced_chords (dict): The dictionary from extract_chord_segments.
        samplerate (int): The sample rate of the audio.
        show_chords (bool): Whether to show chord buttons (default: True).
    """
    if not synced_data:
        return

    container_id = "lyrics_container"
    overlay_id = "chord_overlay"

    flowing_html = []
    chord_buttons = []
    
    # We need to track chord instances to match the keys in sliced_chords (e.g., C_0, C_1)
    chord_counter = {}

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
            raw_chord_text = word[chord_start+1:chord_end] # e.g., "C:maj"
            word_text = word[:chord_start] + word[chord_end+1:]

            # --- AUDIO PROCESSING START ---
            
            # 1. Reconstruct the key used in extract_chord_segments
            sanitized_name = raw_chord_text.replace(":", "").replace("#", "sharp")
            
            # Get current count for this specific chord name
            count = chord_counter.get(sanitized_name, 0)
            unique_key = f"{sanitized_name}_{count}"
            
            # Increment for next time
            chord_counter[sanitized_name] = count + 1
            
            b64_audio = None
            
            # 2. Fetch the audio segment and convert to Base64
            if unique_key in sliced_chords:
                segment = sliced_chords[unique_key]
                
                # Create an in-memory buffer
                buffer = io.BytesIO()
                # Write the numpy array to the buffer as a WAV
                sf.write(buffer, segment, samplerate, format='WAV')
                # Encode to base64
                b64_audio = base64.b64encode(buffer.getvalue()).decode()
            
            # --- AUDIO PROCESSING END ---

            flowing_html.append(
                f'<span id="word-{i}" style="white-space: pre-wrap;">{html_lib.escape(word_text)}</span>'
            )

            if show_chords:
                chord_buttons.append({
                    "index": i,
                    "chord": raw_chord_text, # Display name
                    "duration": duration,
                    "audioData": b64_audio # The actual sound
                })
        else:
            flowing_html.append(
                f'<span style="white-space: pre-wrap;">{html_lib.escape(word)}</span>'
            )

    flowing_html_str = " ".join(flowing_html)

    html = f"""
    <div id="{container_id}" style="
        position: relative;
        background-color: #1e1e1e;
        color: #e0e0e0;
        padding: 28px;
        border-radius: 10px;
        font-family: 'Courier New', monospace;
        font-size: 20px;
        line-height: 3;
        overflow: auto;
        max-height: 420px;
        border: 1px solid #333;
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

        // --- 1. AUDIO PLAYER ---
        // We no longer need the complex Oscillator logic. 
        // We simply play the Base64 string.
        
        let currentAudio = null;

        function playChord(b64Data) {{
            if (!b64Data) return;

            // Stop previous if playing (optional, keeps it clean)
            if (currentAudio) {{
                currentAudio.pause();
                currentAudio.currentTime = 0;
            }}

            // Create audio object from Base64 string
            const audioSource = "data:audio/wav;base64," + b64Data;
            currentAudio = new Audio(audioSource);
            
            // Optional: Fade out logic could be added here, but native play is snappy
            currentAudio.play().catch(e => console.error("Playback failed:", e));
        }}

        // --- 2. BUTTON CREATION ---
        chordSpecs.forEach(spec => {{
            const btn = document.createElement("button");
            btn.className = "chord-btn";
            btn.dataset.index = spec.index;
            btn.innerText = spec.chord;
            
            // Store the audio data directly on the element for easy access
            // (Note: For very large files, this might use memory, but for short chords it's fine)
            if (spec.audioData) {{
                btn.dataset.audio = spec.audioData;
            }}

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
                boxShadow: "0 2px 6px rgba(0,0,0,0.4)",
                transition: "transform 0.1s, filter 0.1s"
            }});
            
            // Hover effect
            btn.onmouseover = () => btn.style.filter = "brightness(1.1)";
            btn.onmouseout = () => btn.style.filter = "brightness(1.0)";
            btn.onmousedown = () => btn.style.transform = "translateX(-50%) scale(0.95)";
            btn.onmouseup = () => btn.style.transform = "translateX(-50%) scale(1)";

            overlay.appendChild(btn);
        }});

        // --- 3. EVENT LISTENER ---
        overlay.addEventListener("click", ev => {{
            const el = ev.target;
            if (el && el.classList.contains("chord-btn")) {{
                // Play the audio stored in the dataset
                if (el.dataset.audio) {{
                    playChord(el.dataset.audio);
                }} else {{
                    console.warn("No audio data found for this chord.");
                }}
            }}
        }});

        // --- 4. POSITIONING LOGIC (Unchanged) ---
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