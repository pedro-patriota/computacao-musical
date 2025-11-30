import json

LYRICS_JSON_PATH = "results2/lyrics_file.json"
CHORDS_JSON_PATH = "results2/piano_chords.json"


def sync_lyrics_with_chords(lyrics_data, chords_data, verbose=True):
    """
    Synchronize lyrics with chord timings.
    
    Args:
        lyrics_data (list): Lyrics data from JSON
        chords_data (list): Chords data from JSON
        verbose (bool): Print progress messages
    
    Returns:
        list: Synced result with words and chord information
    """
    try:
        if verbose:
            print("=" * 60)
            print("Synchronizing Lyrics with Chords")
            print("=" * 60)
        
        # Extract all words with their timings
        words_with_times = []
        for phrase in lyrics_data:
            for word_info in phrase.get('words', []):
                words_with_times.append({
                    'word': word_info['word'],
                    'start': word_info['start'],
                    'end': word_info['end']
                })
        
        if verbose:
            print(f"✓ Extracted {len(words_with_times)} words")
        
        # Extract chords with their timings
        chords_with_times = []
        for chord_info in chords_data:
            if chord_info['chord_simple_pop'] != 'N':  # Skip "N" (no chord)
                chords_with_times.append({
                    'chord': chord_info['chord_simple_pop'],
                    'start': chord_info['start'],
                    'end': chord_info['end']
                })
        
        if verbose:
            print(f"✓ Extracted {len(chords_with_times)} chords")
        
        # Sort both by start time
        words_with_times.sort(key=lambda x: x['start'])
        chords_with_times.sort(key=lambda x: x['start'])
        
        # Track which chords have been inserted to avoid duplicates
        inserted_chords = set()
        
        # Build the synced text with better chord placement
        synced_result = []
        chord_index = 0
        
        for word_idx, word_info in enumerate(words_with_times):
            word = word_info['word']
            word_start = word_info['start']
            word_end = word_info['end']
            
            # Check if there's a chord that should be placed before this word
            chord_to_place = None
            
            # Look for the next chord that starts close to or before this word
            while chord_index < len(chords_with_times):
                chord_info = chords_with_times[chord_index]
                chord_start = chord_info['start']
                
                # If chord starts before the end of this word, place it with this word
                if chord_start <= word_end:
                    # Only place chord if it's reasonably close to word start (within 0.5 seconds)
                    if abs(chord_start - word_start) <= 0.5:
                        chord_to_place = chord_info['chord']
                    chord_index += 1
                    break
                else:
                    # Chord is too far in the future, stop looking
                    break
            
            # Create the word with chord if found
            if chord_to_place:
                modified_word = '{' + chord_to_place + '}' + word
                has_chord = True
            else:
                modified_word = word
                has_chord = False
            
            synced_result.append({
                'word': modified_word,
                'start': word_start,
                'end': word_end,
                'has_chord': has_chord
            })
        
        if verbose:
            print(f"✓ Synced {len(synced_result)} words!")
            print("=" * 60)
        
        return synced_result
    
    except Exception as e:
        if verbose:
            print(f"✗ Error syncing data: {str(e)}")
        return None


def load_json_files(lyrics_file, chords_file):
    """
    Load lyrics and chords from JSON files.
    
    Args:
        lyrics_file (str): Path to lyrics JSON file
        chords_file (str): Path to chords JSON file
    
    Returns:
        tuple: (lyrics_data, chords_data) or (None, None) if error
    """
    try:
        with open(lyrics_file, 'r') as f:
            lyrics_data = json.load(f)
        
        with open(chords_file, 'r') as f:
            chords_data = json.load(f)
        
        return lyrics_data, chords_data
    except Exception as e:
        print(f"Error loading JSON files: {str(e)}")
        return None, None


def save_synced_output(synced_result, output_file="lyrics_with_chords.txt"):
    """
    Save synced lyrics to a text file.
    
    Args:
        synced_result (list): Synced result from sync_lyrics_with_chords
        output_file (str): Output file path
    
    Returns:
        str: Path to the saved file
    """
    try:
        output_text = ' '.join([item['word'] for item in synced_result])
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_text)
        
        return output_file
    except Exception as e:
        print(f"Error saving output: {str(e)}")
        return None


if __name__ == "__main__":
    print("\n📋 Loading JSON files...")
    lyrics_data, chords_data = load_json_files(LYRICS_JSON_PATH, CHORDS_JSON_PATH)
    
    if lyrics_data and chords_data:
        print("✅ Files loaded successfully!\n")
        
        # Sync lyrics with chords
        synced_result = sync_lyrics_with_chords(lyrics_data, chords_data, verbose=True)
        
        if synced_result:
            print("\n💾 Saving output...")
            output_path = save_synced_output(synced_result)
            print(f"✅ Synced lyrics saved to '{output_path}'\n")
            
            print("synced_result", synced_result)
            print("📝 Preview:")
            print("-" * 60)
            output_text = ' '.join([item['word'] for item in synced_result])
            print(output_text[:500] + ("..." if len(output_text) > 500 else ""))
            print("-" * 60)
