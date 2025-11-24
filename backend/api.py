import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
 

from chrodsSync import sync_lyrics_with_chords
from constants import DEMO_DIR

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/demo-sync")
def demo_sync():
    lyrics_path = os.path.join(BASE_DIR, DEMO_DIR, "lyrics_file.json")
    chord_candidates = [
        os.path.join(BASE_DIR, DEMO_DIR, "guitar_chords_file.json"),
        os.path.join(BASE_DIR, DEMO_DIR, "piano_chords_file.json"),
    ]
    if not os.path.exists(lyrics_path):
        raise HTTPException(status_code=404, detail="Demo lyrics file not found")

    chords_path = next((p for p in chord_candidates if os.path.exists(p)), None)
    if not chords_path:
        raise HTTPException(status_code=404, detail="Demo chords file not found")

    try:
        with open(lyrics_path, "r") as f:
            lyrics_data = json.load(f)
        with open(chords_path, "r") as f:
            chords_data = json.load(f)

        synced = sync_lyrics_with_chords(lyrics_data, chords_data, verbose=False)
        if synced is None:
            raise HTTPException(status_code=500, detail="Failed to sync demo data")
        return {"synced_data": synced}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync")
async def sync_endpoint(
    lyrics_file: UploadFile = File(...),
    chords_file: UploadFile = File(...),
):
    try:
        lyrics_bytes = await lyrics_file.read()
        chords_bytes = await chords_file.read()
        lyrics_data = json.loads(lyrics_bytes.decode("utf-8"))
        chords_data = json.loads(chords_bytes.decode("utf-8"))

        synced = sync_lyrics_with_chords(lyrics_data, chords_data, verbose=False)
        if synced is None:
            raise HTTPException(status_code=400, detail="Could not synchronize given data")
        return {"synced_data": synced}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON files")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "Backend API running. Use the separate frontend (served elsewhere) and point it to this API."}
