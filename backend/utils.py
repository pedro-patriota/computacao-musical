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

    # 1. Find all valid chords files (vocals always included, others need > 1 event OR are the only instrument)
    for file_path in chords_files:
        if not os.path.exists(file_path):
            continue
        try:
            with open(file_path, 'r') as f:
                chords_data = json.load(f)
                if isinstance(chords_data, list):
                    filename_lower = file_path.lower()
                    is_vocals = "vocals" in filename_lower
                    
                    # Include vocals regardless of chord count, others need > 1 event
                    if is_vocals or len(chords_data) > 1:
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

    # If no instruments found with > 1 event, accept any instrument with at least 1 event
    if not instruments:
        for file_path in chords_files:
            if not os.path.exists(file_path):
                continue
            try:
                with open(file_path, 'r') as f:
                    chords_data = json.load(f)
                    if isinstance(chords_data, list) and len(chords_data) > 0:
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
                            inst = os.path.splitext(os.path.basename(file_path))[0]
                        instruments[inst] = {'chords': file_path, 'audio': None}
            except (json.JSONDecodeError, IOError):
                continue

    if not instruments:
        print("Warning: No valid chord files found.")
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

def mix_audio_files(audio_files, output_path):
    """
    Mix multiple audio files into a single output file.
    """
    import soundfile as sf
    import numpy as np
    
    if not audio_files:
        return None
    
    # Load first audio file to get properties
    mixed_audio, sample_rate = sf.read(audio_files[0])
    
    # Mix in other audio files
    for audio_file in audio_files[1:]:
        try:
            audio_data, sr = sf.read(audio_file)
            if sr != sample_rate:
                print(f"Warning: Sample rate mismatch in {audio_file}")
                continue
            
            # Handle different lengths by padding with zeros
            if len(audio_data) > len(mixed_audio):
                # Pad mixed_audio to match longer file
                if mixed_audio.ndim == 1:
                    mixed_audio = np.pad(mixed_audio, (0, len(audio_data) - len(mixed_audio)))
                else:
                    mixed_audio = np.pad(mixed_audio, ((0, len(audio_data) - len(mixed_audio)), (0, 0)))
            elif len(audio_data) < len(mixed_audio):
                # Pad audio_data to match mixed_audio
                if audio_data.ndim == 1:
                    audio_data = np.pad(audio_data, (0, len(mixed_audio) - len(audio_data)))
                else:
                    audio_data = np.pad(audio_data, ((0, len(mixed_audio) - len(audio_data)), (0, 0)))
            
            # Add audio data to mix
            mixed_audio = mixed_audio + audio_data
        except Exception as e:
            print(f"Error processing {audio_file}: {e}")
            continue
    
    # Normalize to prevent clipping
    if mixed_audio.max() > 1.0 or mixed_audio.min() < -1.0:
        mixed_audio = mixed_audio / np.max(np.abs(mixed_audio))
    
    # Save mixed audio
    sf.write(output_path, mixed_audio, sample_rate)
    return output_path