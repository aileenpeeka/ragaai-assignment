# Force rebuild

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64 # Import base64
from typing import Dict, Any
import io # Import io for handling audio data in memory
from gtts import gTTS # Import gTTS

app = FastAPI(title="TTS Service")

class Request(BaseModel):
    text: str

class Response(BaseModel):
    audio_base64: str

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok"}

@app.post("/synthesize", response_model=Response)
async def synthesize(request: Request):
    """
    Synthesize text-to-speech and return base64 encoded audio
    """
    try:
        # Log received text
        print(f"DEBUG TTS: Received text for synthesis: {request.text[:100]}...")
        
        # Use gTTS to synthesize speech
        tts = gTTS(text=request.text, lang='en', slow=False)
        
        # Save the audio to a bytes buffer in memory
        audio_bytes_io = io.BytesIO()
        tts.write_to_fp(audio_bytes_io)
        audio_bytes_io.seek(0) # Rewind the buffer
        
        # Read the bytes and base64 encode them
        audio_bytes = audio_bytes_io.read()
        # Log size of audio bytes
        print(f"DEBUG TTS: Audio bytes size: {len(audio_bytes)}")
        
        audio_base64_string = base64.b64encode(audio_bytes).decode('utf-8')
        # Log base64 string length and snippet
        print(f"DEBUG TTS: Base64 string length: {len(audio_base64_string)}")
        print(f"DEBUG TTS: Base64 snippet: {audio_base64_string[:50]}...{audio_base64_string[-50:]}")
        
        # Prepend data URI scheme for base64 encoded audio
        audio_base64_with_uri = f"data:audio/mpeg;base64,{audio_base64_string}"

        return Response(audio_base64=audio_base64_with_uri)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008) 