import httpx
import asyncio
import json
import time
import sys

async def test_voice_agent():
    """Test the voice agent endpoints"""
    base_url = "http://localhost:8005"
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                # Test health check
                response = await client.get(f"{base_url}/health")
                print("Health check:", response.json())
                
                # Test text to speech
                tts_response = await client.post(
                    f"{base_url}/text-to-speech",
                    json={"text": "Hello! This is a test of the voice agent.", "language": "en-US"}
                )
                print("\nText to speech response:", tts_response.json())
                
                # Test market query
                market_response = await client.post(
                    f"{base_url}/market-query",
                    json={"text": "AAPL", "language": "en-US"}
                )
                print("\nMarket query response:", market_response.json())
                
                # If you have an audio file, you can test speech to text
                # with open("test.wav", "rb") as f:
                #     files = {"audio_file": ("test.wav", f, "audio/wav")}
                #     stt_response = await client.post(f"{base_url}/speech-to-text", files=files)
                #     print("\nSpeech to text response:", stt_response.json())
                
                return  # Success, exit the function
                
        except httpx.ConnectError:
            if attempt < max_retries - 1:
                print(f"Connection failed. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(retry_delay)
            else:
                print("Error: Could not connect to the voice agent server.")
                print("Make sure the server is running with: python -m data_ingestion.voice_agent.main")
                sys.exit(1)
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    print("Testing voice agent...")
    print("Make sure the server is running in a separate terminal with: python -m data_ingestion.voice_agent.main")
    asyncio.run(test_voice_agent()) 