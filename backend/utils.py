import json
import os

def get_instruments(chords_files, stem_files):
    """
    Scans a list of chord files and audio stems, and returns a dictionary mapping
    instrument types (e.g., 'guitar', 'piano', 'voice') to their chord and audio files.

    Args:
        chords_files (list): List of file paths to JSON chord files.
        stem_files (list): List of file paths to audio stem files.

    Returns:
        dict: {instrument_type: {'chords': chord_file, 'audio': audio_file}}
    """
    instruments = {}

    # 1. Find all valid chords files (must have > 1 chord event)
    for file_path in chords_files:
        if not os.path.exists(file_path):
            continue
        try:
            with open(file_path, 'r') as f:
                chords_data = json.load(f)
                if isinstance(chords_data, list) and len(chords_data) > 1:
                    filename_lower = file_path.lower()
                    if "guitar" in filename_lower:
                        inst = "guitar"
                    elif "piano" in filename_lower:
                        inst = "piano"
                    elif "vocals" in filename_lower:
                        inst = "vocals"
                    elif "bass" in filename_lower:
                        inst = "bass"
                    elif "drums" in filename_lower:
                        inst = "drums"
                    else:
                        # Try to extract instrument from filename
                        inst = os.path.splitext(os.path.basename(file_path))[0]
                    instruments[inst] = {'chords': file_path, 'audio': None}
        except (json.JSONDecodeError, IOError):
            continue

    if not instruments:
        print("Warning: No valid chord files found (with > 1 event).")
        return {}

    # 2. Find the matching audio stem for each instrument
    for inst in instruments:
        for stem in stem_files:
            if inst in stem.lower():
                instruments[inst]['audio'] = stem
                break
        if not instruments[inst]['audio']:
            print(f"Warning: Found {inst} chords, but no matching audio stem.")

    return instruments

def mix_audio_files(audio_files, output_file, volumes=None):
    """
    Mix multiple audio files into one, with optional volume control for each track.
    
    Args:
        audio_files: List of audio file paths to mix
        output_file: Path to save the mixed audio
        volumes: Optional list of volume multipliers (0.0-1.0) for each track
    """
    from pydub import AudioSegment
    
    if not audio_files:
        return None
    
    # If volumes not provided, use full volume for all tracks
    if volumes is None:
        volumes = [1.0] * len(audio_files)
    
    # Load first audio file as base
    mixed = AudioSegment.from_file(audio_files[0])
    
    # Apply volume to first track
    if volumes[0] != 1.0:
        mixed = mixed + (20 * (volumes[0] - 1.0))  # Convert 0-1 to dB
    
    # Overlay remaining tracks
    for i, audio_file in enumerate(audio_files[1:], start=1):
        audio = AudioSegment.from_file(audio_file)
        
        # Apply volume adjustment (convert 0-1 range to dB)
        if volumes[i] != 1.0:
            # -20dB to +20dB range based on 0-1 input
            db_change = 20 * (volumes[i] - 1.0)
            audio = audio + db_change
        
        mixed = mixed.overlay(audio)
    
    # Export mixed audio
    mixed.export(output_file, format="wav")
    return output_file