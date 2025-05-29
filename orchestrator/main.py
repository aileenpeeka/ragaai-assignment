# Force rebuild

print("DEBUG: Starting orchestrator main.py")
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
import json
import logging
from typing import Dict, Any
import httpx # Import httpx to make requests to other services
import base64

# DEBUG: Imports finished
print("DEBUG: Imports finished")

# Load environment variables
load_dotenv()

# DEBUG: Env loaded
print("DEBUG: Env loaded")

# DEBUG: Before logging config
print("DEBUG: Before logging config")
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# DEBUG: After logging config
print("DEBUG: After logging config")

app = FastAPI(title="Orchestrator Service", description="Routes requests between agents and handles voice processing")

# DEBUG: After FastAPI init
print("DEBUG: After FastAPI init")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# URLs for other services - using service names from docker-compose
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm_service:8009")
TTS_SERVICE_URL = os.getenv("TTS_SERVICE_URL", "http://tts_service:8008")

# Placeholder/Mock classes (will be replaced by actual calls)
# class STT:
#     def process(self, audio_file: UploadFile) -> str:
#         # Placeholder: In reality, use Whisper or another STT model
#         return "Transcribed text from audio"

# class LLM:
#     def process(self, text: str) -> str:
#         # Placeholder: In reality, use OpenAI GPT, Hugging Face, etc.
#         return "LLM response for: " + text

# class TTS:
#     def process(self, text: str) -> bytes:
#         # Placeholder: In reality, use gTTS, pyttsx3, etc.
#         return b"TTS audio data for: " + text.encode()

# Initialize services - not needed with microservices architecture
# stt_service = STT()
# llm_service = LLM()
# tts_service = TTS()

@app.post("/voice/process")
async def process_voice(request: Dict[str, Any]): # Accept JSON with text
    """
    Process voice input (simulated via text): STT(simulated) -> LLM -> TTS
    """
    try:
        # STT (simulated): Get text directly from request
        text = request.get("text")
        if not text:
            raise HTTPException(status_code=400, detail="No text provided")
            
        logger.info(f"Received text for voice processing: {text}")

        # LLM: Send text to LLM service
        async with httpx.AsyncClient() as client:
            llm_response = await client.post(f"{LLM_SERVICE_URL}/process", json={"text": text})
            llm_response.raise_for_status() # Raise an exception for bad status codes
            llm_result = llm_response.json()
            llm_text = llm_result.get("response", "") # Assuming LLM returns {"response": "..."}
            
        logger.info(f"Received LLM response: {llm_text}")

        # TTS: Send LLM response text to TTS service
        async with httpx.AsyncClient() as client:
            tts_response = await client.post(f"{TTS_SERVICE_URL}/synthesize", json={"text": llm_text})
            tts_response.raise_for_status() # Raise an exception for bad status codes
            # Assuming TTS returns binary audio data or base64 encoded string
            # Let's assume it returns base64 encoded string as per Streamlit update
            tts_audio_base64 = tts_response.json().get("audio_base64", "") # Assuming TTS returns {"audio_base64": "..."}
            
        logger.info("Received TTS response")

        return {"text": llm_text, "audio": tts_audio_base64} # Return both text and audio
        
    except Exception as e:
        logger.error(f"Error processing voice request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/route")
async def route_request(request: Dict[str, Any]):
    """
    Route text requests to the appropriate agent (or voice pipeline)
    """
    try:
        text = request.get("text", "")
        if not text:
             raise HTTPException(status_code=400, detail="No text provided")
             
        logger.info(f"Received text for routing: {text}")

        # --- Simplified Routing Logic ---
        # For this simplified demo, we will just pass text queries to the voice processing pipeline
        # A real implementation would analyze the query and route to RAG, Analysis, etc.
        
        # Call the voice processing endpoint internally
        # Note: Internal calls within FastAPI app should ideally use the actual function, not HTTP client
        # But for simplicity and demonstrating the flow, we'll reuse the logic. 
        # A better approach for internal calls would be direct Python function calls.
        
        # Since the /voice/process expects text now, we can call it directly (conceptually) or via HTTP client
        # Given the time constraint and existing structure, let's reuse the HTTP client approach for simplicity
        # assuming /voice/process is designed to be called either via actual audio upload or text payload.
        # *** Correction: The /voice/process is designed for audio upload. We modified Streamlit to send TEXT to it.
        # So the logic below is correct for the Streamlit -> Orchestrator -> LLM -> TTS flow.
        # The original /route endpoint was for text routing to other agents. Let's keep /route simple or repurpose.
        # Given the focus is VOICE pipeline, let's make /route also call /voice/process for this demo.

        # Repurposing /route to call /voice/process for demo purposes
        voice_processing_response = await process_voice(request={"text": text}) # Call the voice processing logic
        
        # Return the result from voice processing
        return voice_processing_response
        
    except Exception as e:
        logger.error(f"Error routing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok"}

# Remove the direct uvicorn run here if using docker-compose
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000) 