RagaAI Assignment

A modular AI-powered system for data ingestion, analysis and voice interaction.

## Project Structure

```
ragaai_assignment/
├── data_ingestion/     # Data collection and processing
├── agents/            # AI agents for different tasks
├── orchestrator/      # Service orchestration
├── streamlit_app/     # Web interface
└── docs/             # Documentation
```

## Components

### Data Ingestion
- **API Agent**: Handles data collection from various APIs
- **Scraping Agent**: Web scraping and data extraction

### AI Agents
- **Retriever Agent**: Handles embeddings and information retrieval
- **Analysis Agent**: Performs data analysis and insights generation
- **Language Agent**: Generates natural language narratives
- **Voice Agent**: Speech-to-text and text-to-speech capabilities

### Orchestrator
- Manages microservices communication
- Routes requests between components

### Streamlit App
- Interactive web interface
- Data visualization
- User interaction

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run with Docker:
   ```bash
   docker-compose up
   ```

## Development

- Each component has its own test suite
- Follow the architecture guidelines in `docs/`
- Use the provided Docker configuration for consistent environments

## Documentation

- `docs/ai_tool_usage.md`: Guide for AI tool integration
- `docs/MCP_setup_guide.md`: Microservices setup instructions
- `docs/architecture_diagram.png`: System architecture visualization

## License

[Add your license information here] 