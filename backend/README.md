# 🎵 Lyrics & Chords Synchronizer

A Streamlit web application that synchronizes lyrics with chord changes in music. Upload your audio file along with lyrics and chord data, and visualize them together with interactive chord buttons. Currently only works for guitar or piano.

## Features

✨ **Key Features:**
- 📤 Upload MP3, WAV, or M4A audio files
- 🎼 Upload lyrics and chord timing data (JSON format)
- 🔄 Automatic synchronization of lyrics with chords
- 🎨 Interactive display with chord buttons positioned above lyrics
- 📊 Detailed timeline view
- 📥 Download synchronized results as text or JSON

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup

1. **Clone or download this project** to your local machine

2. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a dot env file and add your music.ai API KEY**
   ```bash
    API_KEY=your-api-key
   ```

4. **Run the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

The app will open in your default web browser at `http://localhost:8501`

## Usage

### Step 1: Upload Audio File
- Navigate to the "📤 Upload" tab
- Click the file uploader and select an MP3, WAV, or M4A file
- The audio player will appear so you can preview the file

### Step 2: Process Audio Data
- Go to the "🔍 Process" tab
- Upload two JSON files:
  - **Lyrics JSON**: Contains words with timing information (start/end times)
  - **Chords JSON**: Contains chord information with timing

### Example JSON Formats

**Lyrics JSON Format:**
```json
[
  {
    "start": 3.52,
    "end": 9.4,
    "text": "What you see, what you feel, all I give to you is real",
    "language": "english",
    "words": [
      {
        "word": "What",
        "start": 3.52,
        "end": 3.83,
        "score": 0.84
      },
      {
        "word": "you",
        "start": 3.83,
        "end": 3.97,
        "score": 0.97
      }
    ]
  }
]
```

**Chords JSON Format:**
```json
[
  {
    "start": 0.76,
    "end": 7.09,
    "chord_majmin": "D#:maj"
  },
  {
    "start": 7.09,
    "end": 18.11,
    "chord_majmin": "N"
  }
]
```

### Step 4: Download Results
- Use the download buttons at the bottom to save:
  - **Text format**: Simple text with chords embedded in curly braces
  - **JSON format**: Full timing data for further processing

## How It Works

1. **Timeline Alignment**: The app calculates when each chord starts relative to each word
2. **Position Calculation**: For each chord, it determines the character position within the word based on the time offset proportional to the word duration
3. **Chord Insertion**: Chords are inserted into words at the calculated positions
4. **Visual Display**: Chord buttons are positioned above lyrics, appearing exactly when they start

### Algorithm Example

For the phrase: "I love sushi forever" with chords C, A, B:
- If C starts at 0.76s (during "I")
- If A starts at 2.5s (mid-way through "love")  
- If B starts at 4.0s (at end of word before "forever")

Result: `{C}I lo{A}ve sushi fore{B}ver`

## Related Scripts

### `chrodsSync.py`
The core synchronization engine. This script:
- Loads lyrics and chords JSON files
- Extracts timing information for each word and chord
- Calculates proper insertion positions
- Outputs synchronized lyrics with embedded chords

**Usage:**
```bash
python chrodsSync.py
```

Outputs: `lyrics_with_chords.txt`

## File Structure

```
.
├── app.py                      # Main Streamlit application
├── chrodsSync.py              # Core synchronization engine
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── demo--lyricsOutput.json    # Example lyrics data
└── demo--guitarOutput.json    # Example chords data
```

## Requirements

- **streamlit**: Web application framework
- **librosa**: Audio processing (optional, for future audio analysis)
- **numpy**: Numerical computing (optional, for future audio analysis)

## Tips & Tricks

💡 **Best Practices:**

1. **Accurate Timing**: Ensure your JSON files have accurate start/end times for best results
2. **JSON Format**: Double-check that JSON files are properly formatted (valid JSON syntax)
3. **Chord Naming**: Use standard chord notation (e.g., "C:maj", "G:min", "D#:maj")
4. **Audio Quality**: Higher quality audio files may provide better results if using automatic extraction

## Troubleshooting

**Issue**: "Error loading files: ..."
- **Solution**: Verify your JSON files are valid and properly formatted

**Issue**: Chords not appearing in display
- **Solution**: Check that your chord data has `chord_majmin` field and it's not "N" (no chord)

**Issue**: Streamlit app won't start
- **Solution**: Make sure all dependencies are installed: `pip install -r requirements.txt`

## Future Enhancements

🚀 **Planned Features:**
- Automatic chord detection from audio using machine learning
- Real-time lyrics extraction using Whisper API
- Synchronized playback with visual highlighting
- Support for multiple languages
- Export to various formats (PDF, LRC, etc.)
- Plugin system for custom chord detection models

## License

Open source - Feel free to use and modify for your needs!

## Author

Created for the Criatividade Computacional project

---

**Questions?** Check the app's built-in help or review the example JSON files included in the project.
