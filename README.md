# 🎵 Play Along Generator

A Streamlit web application that processes audio files with Music.AI to extract instrument stems and chord progressions, enabling interactive play-along experiences with real-time chord guides.

**Links:**
- 🌐 [Live Application](https://computacao-musical.streamlit.app/)
- 🎵 [Music Folder](https://drive.google.com/drive/folders/1xgPrkg0Lqx0fshC4N3ivPULE-ZWnFOoO)

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Data Format](#data-format)
- [Troubleshooting](#troubleshooting)
- [Technical Architecture](#technical-architecture)
- [Dependencies](#dependencies)
- [Tips & Tricks](#tips--tricks)
- [License](#license)

## Features

✨ **Key Features:**
- 📤 Upload MP3, WAV, or M4A audio files
- 🤖 Automatic audio processing with Music.AI API
- 🎸 Multi-instrument support: Piano, Guitar, Bass, Drums, Vocals
<!-- - 🎼 Automatic chord extraction and synchronization with lyrics -->
- 🎶 Mix/mute individual instruments for targeted practice
- 🎨 Interactive display with chord progression guide
- ⚙️ Demo mode for testing without API processing
- 🔄 Fallback support for manual JSON file uploads
- ⚠️ Smart validation: Shows errors when audio extraction fails

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Music.AI API key (for API processing)

### Setup

1. **Clone or download this project** to your local machine
   ```bash
   git clone https://github.com/pedro-patriota/computacao-musical.git
   cd computacao-musical
   ```

2. **Install required dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Create a `.env` file and add your Music.AI API key:**
   ```bash
   echo "API_KEY=your-music-ai-api-key" > .env
   ```

4. **Run the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

The app will open in your default web browser at [`http://localhost:8501`](http://localhost:8501)

## Usage

### Workflow

#### Option 1: Process with Music.AI (Recommended)
1. **Upload Audio File**
   - Click "Choose an audio file" and select MP3, WAV, or M4A
   - Preview the audio in the player

2. **Process with Music.AI**
   - Click "🚀 Process with Music.AI"
   - The app will:
     - Upload your file to Music.AI
     - Create a processing job
     - Wait for completion
     - Download stems and chord data automatically

3. **Play Along**
   - Select which instrument to practice/mute
   - All other instruments will be mixed and played
   - Follow the chord progression guide synchronized with lyrics

#### Option 2: Load Demo
- Click "🧪 Load Demo" to load pre-processed example data
- Useful for testing without API processing

#### Option 3: Load Existing API Results
- Click "📂 Load API Results" to load previously processed audio
- Useful if you've already processed files

### Play Along Interface

Once audio is processed:

1. **Select Instrument to Practice**
   - Choose which instrument to mute (that's what you'll play)
   - All other instruments will be mixed and played back

2. **Audio Playback**
   - Real-time mixed audio with selected instrument muted

3. **Chord Guide**
   - Visual display of chord progression
   - Synchronized with audio timing

## Data Format

### Expected Directory Structure

After processing, results are organized in `results/api/` or `results/demo/`:

```
results/
├── api/                    # API processing results
│   ├── piano.wav          # Instrument stem
│   ├── guitar.wav
│   ├── bass.wav
│   ├── drums.wav
│   ├── vocals.wav
│   ├── piano_chords.json  # Chord data
│   ├── guitar_chords.json
│   ├── bass_chords.json
│   ├── drums_chords.json
│   ├── vocals_chords.json
│   ├── lyrics.json        # Lyrics with timing
│   └── workflow.result.json
└── demo/                  # Demo/example data
    ├── *.wav
    ├── *_chords.json
    └── lyrics.json
```

### JSON Formats

#### Lyrics JSON Format
```json
[
  {
    "start": 2.76,
    "end": 4.31,
    "text": "What you see, what you feel",
    "language": "english",
    "words": [
      {
        "word": "What",
        "start": 2.76,
        "end": 3.0,
        "score": 0.95
      },
      {
        "word": "you",
        "start": 3.0,
        "end": 3.2,
        "score": 0.92
      }
    ]
  }
]
```

#### Chords JSON Format
```json
[
  {
    "start": 2.76,
    "end": 4.31,
    "start_bar": 0,
    "start_beat": 4,
    "end_bar": 1,
    "end_beat": 2,
    "chord_majmin": "D#:maj",
    "chord_complex_jazz": "D#",
    "chord_simple_pop": "D#",
    "chord_basic_nashville": "1",
    "bass": null,
    "bass_nashville": null
  }
]
```

**Note:** Chords with value `"N"` indicate silence/no chord detected.


## Troubleshooting

### Problem: "Cannot extract audio: All other instruments have no valid chord data"
**Cause:** Music.AI failed to detect chords in all instruments (likely due to audio quality or processing issues)

**Solutions:**
1. Try processing a different audio file
2. Ensure audio file is clear and has well-defined instruments
3. Check Music.AI service status
4. Use demo data to verify the app is working

### Problem: Only some instruments appear in the dropdown
**Cause:** Some instruments have insufficient chord data (only "N" values)

**Solutions:**
1. Use the demo to see expected behavior
2. Check if the audio processing completed successfully
3. Try re-processing the file

### Problem: "No instruments found" error
**Cause:** No valid chord files found in the results folder

**Solutions:**
1. Ensure processing completed successfully
2. Check that `results/api/` or `results/demo/` directories exist
3. Verify JSON files are present

### Problem: Streamlit app won't start
**Solutions:**
- Install all dependencies: `pip install -r requirements.txt`
- Ensure Python 3.8+ is installed
- Check that port 8501 is available

## Technical Architecture

### Audio Processing Pipeline

```
Upload Audio
    ↓
Music.AI Processing
    ↓
Stem Extraction (Piano, Guitar, Bass, Drums, Vocals)
    ↓
Chord Detection per Instrument
    ↓
Lyrics Extraction & Synchronization
    ↓
Results Download & Storage
    ↓
Play Along Interface
    ↓
Instrument Selection → Audio Mixing → Playback
    ↓
Chord Guide Display
```

## Dependencies

- **streamlit**: Web application framework
- **musicai_sdk**: Music.AI API integration
- **soundfile**: Audio file I/O (WAV format)
- **pydub**: Audio processing and conversion
- **python-dotenv**: Environment variable management



## Tips & Tricks

💡 **Best Practices:**

1. **Test with Demo First**: Use the demo to understand the app before processing your own files
2. **Audio Quality**: Higher quality audio files (44.1 kHz or higher) produce better chord detection
3. **Clear Instruments**: Music with distinct, well-separated instruments processes better
4. **Check Results**: After processing, verify the chords were detected correctly by reviewing `results/api/` files
5. **Multiple Attempts**: If one instrument fails, try processing the file again

## License

Open source - Feel free to use and modify for your needs!


---

