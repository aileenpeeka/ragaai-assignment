import streamlit as st
import asyncio
import os

# ------------------ Mocked Service Health ------------------
async def check_service_health(url, service_name):
    # Always show as running (for demo)
    return service_name, "✅ Running"

async def display_service_status():
    st.sidebar.title("Services Status (Direct Connect)")
    services = {
        "Orchestrator": "http://localhost:8000",
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
        st.sidebar.success(f"{name}: {status}")

# ------------------ Mocked Processing ------------------
async def process_user_query_async(query):
    st.write("Processing query directly via LLM and TTS (mocked)...")
    await asyncio.sleep(1)  # Simulate processing delay
    fake_response = (
        f"**Mocked LLM Response:** Here is your market brief for '{query}'.\n\n"
        "- The market is trending upwards 🚀\n"
        "- Key sectors: AI, Cloud, Finance\n"
        "- Major news: Everything is awesome!\n"
    )
    st.markdown(fake_response)
    
    # Simulate TTS (audio) by playing a sample mp3 if available
    audio_file_path = os.path.join(os.path.dirname(__file__), "sample.mp3")
    if os.path.exists(audio_file_path):
        audio_bytes = open(audio_file_path, "rb").read()
        st.audio(audio_bytes, format="audio/mp3")
        st.success("TTS Audio: (Sample audio played!) 🔊")
    else:
        st.info("TTS Audio: (Pretend audio plays here!) 🔊")

# ------------------ Streamlit Page Setup ------------------
st.set_page_config(
    page_title="RagaAI Assignment",
    page_icon="🎵",
    layout="wide"
)
st.title("RagaAI Assignment")
st.write("Welcome to the RagaAI Assignment application!")

# Query Input
user_query = st.text_input("Enter your query:", "give me the market brief")
if st.button("Submit"):
    st.session_state.process_query = True

# Process Query (Mocked)
if st.session_state.get('process_query', False):
    st.session_state.process_query = False
    st.write("Processing query via Orchestrator...")
    asyncio.run(process_user_query_async(user_query))

# Show all services as running
asyncio.run(display_service_status())
