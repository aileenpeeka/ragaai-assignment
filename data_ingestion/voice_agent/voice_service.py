from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
import httpx
import json
import logging
from datetime import datetime
from gtts import gTTS
import tempfile
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class VoiceResponse(BaseModel):
    text: str
    audio_url: Optional[str] = None
    timestamp: datetime = datetime.now()

class VoiceQuery(BaseModel):
    text: str
    language: str = "en-US"

class VoiceService:
    def __init__(self):
        self.api_base_url = os.getenv("API_AGENT_URL", "http://localhost:8000")
        self.tts_engine = os.getenv("TTS_ENGINE", "gtts")  # gtts, azure, or aws
        self.stt_engine = os.getenv("STT_ENGINE", "whisper")  # whisper, azure, or aws
        self.audio_dir = os.getenv("AUDIO_DIR", "audio_files")
        
        # Create audio directory if it doesn't exist
        os.makedirs(self.audio_dir, exist_ok=True)
        
    async def text_to_speech(self, text: str, language: str = "en-US") -> VoiceResponse:
        """Convert text to speech using the configured TTS engine"""
        try:
            if self.tts_engine == "gtts":
                return await self._gtts_convert(text, language)
            elif self.tts_engine == "azure":
                return await self._azure_tts_convert(text, language)
            elif self.tts_engine == "aws":
                return await self._aws_tts_convert(text, language)
            else:
                raise HTTPException(status_code=400, detail="Unsupported TTS engine")
        except Exception as e:
            logger.error(f"TTS conversion failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Text-to-speech conversion failed")

    async def speech_to_text(self, audio_file: UploadFile) -> str:
        """Convert speech to text using the configured STT engine"""
        try:
            if self.stt_engine == "whisper":
                return await self._whisper_convert(audio_file)
            elif self.stt_engine == "azure":
                return await self._azure_stt_convert(audio_file)
            elif self.stt_engine == "aws":
                return await self._aws_stt_convert(audio_file)
            else:
                raise HTTPException(status_code=400, detail="Unsupported STT engine")
        except Exception as e:
            logger.error(f"STT conversion failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Speech-to-text conversion failed")

    async def process_market_query(self, query: str) -> VoiceResponse:
        """Process a market data query and return a voice response"""
        try:
            async with httpx.AsyncClient() as client:
                # First, get market data from API agent
                response = await client.get(f"{self.api_base_url}/market-data/{query}")
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, 
                                     detail="Failed to fetch market data")
                
                market_data = response.json()
                
                # Format the response text
                text = self._format_market_response(market_data)
                
                # Convert to speech
                return await self.text_to_speech(text)
        except Exception as e:
            logger.error(f"Market query processing failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to process market query")

    def _format_market_response(self, market_data: Dict[str, Any]) -> str:
        """Format market data into a natural language response"""
        if isinstance(market_data, list):
            # Handle batch response
            symbols = [item["symbol"] for item in market_data]
            return f"Here are the current prices for {', '.join(symbols)}. "
        
        # Handle single symbol response
        return (
            f"The current price of {market_data['symbol']} is "
            f"${market_data['price']:.2f}, "
            f"{'up' if market_data['change'] >= 0 else 'down'} "
            f"{abs(market_data['change']):.2f} "
            f"({abs(market_data['change_percent']):.2f}%). "
            f"Trading volume is {market_data['volume']:,} shares."
        )

    # TTS engine implementations
    async def _gtts_convert(self, text: str, language: str) -> VoiceResponse:
        """Convert text to speech using Google Text-to-Speech"""
        try:
            # Generate a unique filename
            filename = f"{uuid.uuid4()}.mp3"
            filepath = os.path.join(self.audio_dir, filename)
            
            # Convert text to speech
            tts = gTTS(text=text, lang=language)
            tts.save(filepath)
            
            # Create audio URL (relative to the server)
            audio_url = f"/audio/{filename}"
            
            return VoiceResponse(
                text=text,
                audio_url=audio_url,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"gTTS conversion failed: {str(e)}")
            raise HTTPException(status_code=500, detail="gTTS conversion failed")

    async def _azure_tts_convert(self, text: str, language: str) -> VoiceResponse:
        """Convert text to speech using Azure Cognitive Services"""
        # TODO: Implement Azure TTS conversion
        return VoiceResponse(text=text)

    async def _aws_tts_convert(self, text: str, language: str) -> VoiceResponse:
        """Convert text to speech using AWS Polly"""
        # TODO: Implement AWS Polly conversion
        return VoiceResponse(text=text)

    # STT engine implementations
    async def _whisper_convert(self, audio_file: UploadFile) -> str:
        """Convert speech to text using OpenAI Whisper"""
        # TODO: Implement Whisper conversion
        return ""

    async def _azure_stt_convert(self, audio_file: UploadFile) -> str:
        """Convert speech to text using Azure Speech Services"""
        # TODO: Implement Azure STT conversion
        return ""

    async def _aws_stt_convert(self, audio_file: UploadFile) -> str:
        """Convert speech to text using AWS Transcribe"""
        # TODO: Implement AWS Transcribe conversion
        return "" 