import soundfile as sf
import json
import os

def extract_chord_segments(audio_filename, json_filename):
    """
    Loads an audio file and a JSON chord map, slices the audio, 
    and returns a dictionary of audio segments.
    
    Returns:
        dict: A dictionary where keys are chord names (e.g., "C_0") and values are numpy arrays (audio segments).
        int: The sample rate of the audio file.
    """
    
    # 1. Load the audio file
    print(f"Loading {audio_filename}...")
    try:
        data, samplerate = sf.read(audio_filename)
    except FileNotFoundError:
        print(f"Error: Could not find '{audio_filename}'.")
        return None, None

    # 2. Load the chords JSON
    print(f"Loading {json_filename}...")
    try:
        with open(json_filename, 'r') as f:
            piano_chords = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find '{json_filename}'.")
        return None, None

    print(f"Found {len(piano_chords)} chords. Processing...")

    chord_instances = {}
    chords = {}

    # 3. Process and slice
    for chord in piano_chords:
        # Convert seconds to sample indices
        start_sample = int(chord["start"] * samplerate)
        end_sample = int(chord["end"] * samplerate)
        
        # Extract the segment (Slicing the numpy array)
        segment = data[start_sample:end_sample]
        
        # Sanitize filename
        chord_name_raw = chord.get("chord_simple_pop", "Unknown").replace(":", "").replace("#", "sharp")

        # Handle duplicates by appending a number (C_sharp_0, C_sharp_1, etc.)
        chord_number = chord_instances.get(chord_name_raw, 0)
        unique_chord_name = f"{chord_name_raw}_{chord_number}"
        
        # Increment the counter for this specific chord type
        chord_instances[chord_name_raw] = chord_number + 1
        
        # Store segment
        chords[unique_chord_name] = segment

    print(f"Successfully processed {len(chords)} segments.")
    return chords, samplerate