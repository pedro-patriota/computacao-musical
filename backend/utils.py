import json
import os

def select_guitar_or_piano(chords_files, stem_files):
    """
    Scans a list of chord files for a valid JSON (len > 1), determines
    if it is guitar/piano, and finds the corresponding audio stem.

    Args:
        chords_files (list): List of file paths to JSON chord files.
        stem_files (list): List of file paths to audio stem files.

    Returns:
        tuple: (chords_file, stem_file, file_type) or (None, None, None) if failed.
    """
    selected_chords_file = None
    selected_stem_file = None
    file_type = None

    # 1. Find the first valid chords file (must have > 1 chord event)
    for file_path in chords_files:
        if not os.path.exists(file_path):
            continue
            
        try:
            with open(file_path, 'r') as f:
                chords_data = json.load(f)
                # Ensure it's a list and has content
                if isinstance(chords_data, list) and len(chords_data) > 1:
                    selected_chords_file = file_path
                    break
        except (json.JSONDecodeError, IOError):
            continue # Skip corrupted or unreadable files

    # If no valid chords file was found, return early
    if not selected_chords_file:
        print("Warning: No valid chord file found (with > 1 event).")
        return None, None

    # 2. Determine the instrument type
    filename_lower = selected_chords_file.lower()
    if "guitar" in filename_lower:
        file_type = "guitar"
    elif "piano" in filename_lower:
        file_type = "piano"
    else:
        # You can choose to raise an error or return None here
        raise ValueError(f"Unknown instrument type in filename: {selected_chords_file}")

    # 3. Find the matching audio stem
    for stem in stem_files:
        if file_type in stem.lower():
            selected_stem_file = stem
            break
            
    if not selected_stem_file:
        print(f"Warning: Found {file_type} chords, but no matching audio stem.")
        return None, None

    return selected_chords_file, selected_stem_file