# Force rebuild

from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import whisper
import tempfile
import os

app = FastAPI(title="Whisper STT Service")

# Load the Whisper model
model = whisper.load_model("base")

class Response(BaseModel):
    text: str

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok"}

@app.post("/transcribe", response_model=Response)
async def transcribe(audio_file: UploadFile = File(...)):
    """
    Transcribe audio using Whisper model
    """
    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file.flush()

            # Transcribe using Whisper
            result = model.transcribe(temp_file.name)

            # Clean up the temporary file
            os.unlink(temp_file.name)

            return Response(text=result["text"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007) 