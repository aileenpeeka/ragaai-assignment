from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
import os
from dotenv import load_dotenv
from .voice_service import VoiceService, VoiceResponse, VoiceQuery

# Load environment variables
load_dotenv()

app = FastAPI(title="Voice Agent")
voice_service = VoiceService()

# Mount the audio files directory
audio_dir = os.getenv("AUDIO_DIR", "audio_files")
os.makedirs(audio_dir, exist_ok=True)
app.mount("/audio", StaticFiles(directory=audio_dir), name="audio")

class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy")

@app.post("/speech-to-text")
async def speech_to_text(audio_file: UploadFile = File(...)):
    """Convert speech to text"""
    text = await voice_service.speech_to_text(audio_file)
    return {"text": text}

@app.post("/text-to-speech", response_model=VoiceResponse)
async def text_to_speech(query: VoiceQuery):
    """Convert text to speech"""
    return await voice_service.text_to_speech(query.text, query.language)

@app.post("/market-query", response_model=VoiceResponse)
async def market_query(query: VoiceQuery):
    """Process a market data query and return a voice response"""
    return await voice_service.process_market_query(query.text)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8005))
    uvicorn.run(app, host="0.0.0.0", port=port) 