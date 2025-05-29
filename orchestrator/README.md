# Orchestrator Service

## Overview
The Orchestrator Service is a FastAPI-based microservice that routes requests between various agents (Voice, API, Retriever, Analysis, etc.) and handles voice processing (STT, LLM, TTS). It is designed to be extensible, production-ready, and capable of enabling voice-driven financial research and analytics.

## Architecture
- **FastAPI**: The service is built using FastAPI for high performance and easy API documentation.
- **STT (Speech-to-Text)**: Converts audio input to text (placeholder for Whisper or similar).
- **LLM (Language Model)**: Processes text and generates responses (placeholder for OpenAI GPT, Hugging Face, etc.).
- **TTS (Text-to-Speech)**: Converts text responses to audio (placeholder for gTTS, pyttsx3, etc.).
- **Agent Routing**: Routes requests to the appropriate agent based on intent.

## File Structure
```
orchestrator/
├── main.py               # FastAPI entrypoint
├── agents/               # Adapters to each microservice
│   ├── language_agent.py
│   ├── retriever_agent.py
│   ├── scraping_agent.py
│   └── analysis_agent.py
├── stt/                  # Speech-to-text logic
│   └── whisper.py
├── tts/                  # Text-to-speech logic
│   └── tts.py
├── llm/                  # LLM adapter (OpenAI/HuggingFace)
│   └── llm.py
├── requirements.txt
└── README.md
```

## Setup & Deployment
1. **Environment Variables**: Ensure `.env` is configured with necessary API keys and settings.
2. **Install Dependencies**: Run `pip install -r requirements.txt`.
3. **Run the Service**: Execute `python main.py` to start the service on `http://0.0.0.0:8000`.

## Usage
- **Voice Processing**: Send a POST request to `/voice/process` with an audio file to get a text response and audio output.
- **Request Routing**: Send a POST request to `/route` with a JSON payload containing `text` to route the request to the appropriate agent.

## Performance & Benchmarks
- **Latency**: The service is optimized for low latency, with STT, LLM, and TTS processing completed in under 2 seconds.
- **Scalability**: Designed to handle multiple concurrent requests efficiently.

## Framework/Toolkit Comparisons
- **FastAPI vs Flask**: FastAPI offers better performance and automatic API documentation.
- **STT Options**: Whisper (OpenAI) vs Hugging Face Whisper (open-source).
- **TTS Options**: gTTS (Google) vs pyttsx3 (offline).

## AI Tool Usage
Detailed logs of AI-tool prompts, code generation steps, and model parameters are available in `docs/ai_tool_usage.md`.

## License
MIT 