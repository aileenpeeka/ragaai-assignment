import streamlit as st
import requests
import os
import httpx # Import httpx for making HTTP requests
import base64 # Import base64 for decoding audio
import asyncio

# Function to check service health
async def check_service_health(url, service_name):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/health", timeout=2)
            response.raise_for_status()
            return service_name, "✅ Running"
    except httpx.RequestError as e:
        return service_name, f"❌ {service_name} (Connection refused)"
    except Exception as e:
        return service_name, f"❌ {service_name} (Error: {str(e)[:50]}...)"

# Function to display service status
async def display_service_status():
    st.sidebar.title("Services Status (Direct Connect)")
    services = {
        "Orchestrator": ORCHESTRATOR_URL,
        "Language Agent": "http://localhost:8004",
        "Retriever Agent": "http://localhost:8002",
        "Scraping Agent": "http://localhost:8001",
        "Analysis Agent": "http://localhost:8003",
        "TTS Service": "http://localhost:8008",
        "LLM Service": "http://localhost:8009",
    }
    tasks = [check_service_health(url, name) for name, url in services.items()]
    results = await asyncio.gather(*tasks)
    for name, status in results:
        if "✅" in status:
            st.sidebar.success(f"{name}: {status}")
        else:
            st.sidebar.error(f"{name}: {status}")

# Define async function for processing query with Orchestrator
async def process_user_query_async(query):
    try:
        st.write("Processing query directly via LLM and TTS...") # Update message

        # Call LLM service directly
        async with httpx.AsyncClient() as client:
            llm_response = await client.post(f"http://localhost:8009/process", json={"text": query})
            llm_response.raise_for_status()
            llm_result = llm_response.json()
            llm_text = llm_result.get("response", "")

        st.write("LLM Response:")
        st.write(llm_text)

        st.write("TTS Audio:")

        # Call TTS service directly
        async with httpx.AsyncClient() as client:
            tts_response = await client.post(f"http://localhost:8008/synthesize", json={"text": llm_text})
            tts_response.raise_for_status()
            tts_result = tts_response.json()
            tts_audio_base64 = tts_result.get("audio_base64", "")

        if tts_audio_base64:
            # Decode base64 and play audio
            audio_bytes = base64.b64decode(tts_audio_base64)
            st.audio(audio_bytes, format='audio/mpeg') # Assuming MP3 from gTTS
        else:
            st.warning("No audio data received from TTS service.")

    except httpx.HTTPStatusError as e:
        st.error(f"HTTP error during processing: {e}. Response: {e.response.text}")
    except httpx.RequestError as e:
        st.error(f"Error connecting to service: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")

# Configure the page
st.set_page_config(
    page_title="RagaAI Assignment",
    page_icon="🎵",
    layout="wide"
)

# URLs for other services - connecting directly to Docker services from local Streamlit
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8009") # Use localhost as port is published
TTS_SERVICE_URL = os.getenv("TTS_SERVICE_URL", "http://localhost:8008") # Use localhost as port is published

# Define the Orchestrator URL
ORCHESTRATOR_URL = "http://localhost:8000"

# Title
st.title("RagaAI Assignment")

# Main content
st.write("Welcome to the RagaAI Assignment application!")

# Add a text input for user queries
user_query = st.text_input("Enter your query:", "give me the market brief")

# Add a submit button
if st.button("Submit"):
    if user_query:
        # Set session state to trigger async processing
        st.session_state.process_query = True

# --- Async Processing Logic ---# This block runs on each script re-run
if st.session_state.get('process_query', False):
    st.session_state.process_query = False # Reset the flag
    st.write("Processing query via Orchestrator...")
    # Call the async processing function
    asyncio.run(process_user_query_async(user_query))

# --- Service Status Display ---# This block also runs on each script re-run
# Initial call to display service status
asyncio.run(display_service_status()) 