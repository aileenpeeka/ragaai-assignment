from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uvicorn
import os
from dotenv import load_dotenv
import spacy
from textblob import TextBlob
import logging
from datetime import datetime
import langdetect
from langdetect import LangDetectException
import re
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("Successfully loaded spaCy model")
except OSError:
    logger.warning("Downloading spaCy model...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")
    logger.info("Successfully downloaded and loaded spaCy model")

# Initialize Hugging Face summarizer
try:
    # Using BART-large-CNN for high-quality summarization
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    logger.info("Successfully initialized Hugging Face summarizer")
except Exception as e:
    logger.error(f"Error initializing Hugging Face summarizer: {str(e)}")
    summarizer = None

app = FastAPI(
    title="Language Agent",
    description="API for natural language processing tasks using Hugging Face and spaCy",
    version="1.0.0"
)

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.now)
    spacy_status: str = "initialized"
    huggingface_status: str = "initialized" if summarizer else "not_initialized"

class TextRequest(BaseModel):
    text: str = Field(..., description="Text to analyze", min_length=1)
    language: Optional[str] = Field(None, description="Language code (e.g., 'en', 'es')")

class Entity(BaseModel):
    text: str
    label: str
    start: int
    end: int
    confidence: Optional[float] = None

class SentimentAnalysis(BaseModel):
    polarity: float = Field(..., description="Sentiment polarity (-1.0 to 1.0)")
    subjectivity: float = Field(..., description="Subjectivity score (0.0 to 1.0)")
    assessment: str = Field(..., description="Sentiment assessment (positive, negative, neutral)")
    confidence: Optional[float] = None

class TextAnalysis(BaseModel):
    entities: List[Entity]
    sentiment: SentimentAnalysis
    language: str
    language_confidence: Optional[float] = None
    word_count: int
    sentence_count: int
    keywords: List[str]
    summary: Optional[str] = None
    processing_time: float

class APIInfo(BaseModel):
    name: str = "Language Agent API"
    version: str = "1.0.0"
    description: str = "Natural Language Processing API for text analysis using Hugging Face and spaCy"
    endpoints: Dict[str, str] = {
        "/": "API information (this endpoint)",
        "/health": "Health check endpoint",
        "/analyze": "Analyze text for entities, sentiment, and other features",
        "/sentiment": "Analyze text sentiment",
        "/entities": "Extract named entities from text",
        "/keywords": "Extract keywords from text",
        "/summarize": "Generate a summary of the text using Hugging Face"
    }

def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """Extract keywords from text using spaCy"""
    doc = nlp(text)
    
    # Get noun chunks and named entities
    keywords = []
    for chunk in doc.noun_chunks:
        if not any(token.is_stop for token in chunk):
            keywords.append(chunk.text.lower())
    
    for ent in doc.ents:
        if ent.label_ in ['ORG', 'PRODUCT', 'PERSON', 'GPE']:
            keywords.append(ent.text.lower())
    
    # Remove duplicates and sort by frequency
    keyword_freq = {}
    for keyword in keywords:
        keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
    
    # Sort by frequency and get top keywords
    sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
    return [k for k, v in sorted_keywords[:max_keywords]]

@app.get("/", response_model=APIInfo)
async def root():
    """Root endpoint providing API information"""
    return APIInfo()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        spacy_status="initialized",
        huggingface_status="initialized" if summarizer else "not_initialized"
    )

@app.post("/analyze", response_model=TextAnalysis)
async def analyze_text(request: TextRequest):
    """Analyze text for entities, sentiment, and other features"""
    start_time = datetime.now()
    try:
        logger.info(f"Processing text analysis request")
        
        # Detect language if not provided
        if not request.language:
            try:
                detected_lang = langdetect.detect(request.text)
                language = detected_lang
                language_confidence = 1.0
            except LangDetectException:
                language = "en"
                language_confidence = 0.0
                logger.warning("Language detection failed, defaulting to English")
        else:
            language = request.language
            language_confidence = 1.0
        
        # Process text with spaCy
        doc = nlp(request.text)
        
        # Extract entities with confidence scores
        entities = [
            Entity(
                text=ent.text,
                label=ent.label_,
                start=ent.start_char,
                end=ent.end_char,
                confidence=ent._.confidence if hasattr(ent._, 'confidence') else None
            )
            for ent in doc.ents
        ]
        
        # Analyze sentiment
        blob = TextBlob(request.text)
        sentiment = SentimentAnalysis(
            polarity=blob.sentiment.polarity,
            subjectivity=blob.sentiment.subjectivity,
            assessment="positive" if blob.sentiment.polarity > 0 else "negative" if blob.sentiment.polarity < 0 else "neutral",
            confidence=abs(blob.sentiment.polarity)
        )
        
        # Count words and sentences
        word_count = len([token for token in doc if not token.is_punct])
        sentence_count = len(list(doc.sents))
        
        # Extract keywords
        keywords = extract_keywords(request.text)
        
        # Generate summary using Hugging Face if available
        summary = None
        if summarizer:
            try:
                # Split text into chunks if it's too long
                max_chunk_length = 1024
                chunks = [request.text[i:i + max_chunk_length] for i in range(0, len(request.text), max_chunk_length)]
                
                summaries = []
                for chunk in chunks:
                    result = summarizer(chunk, max_length=130, min_length=30, do_sample=False)
                    summaries.append(result[0]['summary_text'])
                
                summary = " ".join(summaries)
            except Exception as e:
                logger.warning(f"Summary generation skipped: {str(e)}")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return TextAnalysis(
            entities=entities,
            sentiment=sentiment,
            language=language,
            language_confidence=language_confidence,
            word_count=word_count,
            sentence_count=sentence_count,
            keywords=keywords,
            summary=summary,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

@app.post("/sentiment", response_model=SentimentAnalysis)
async def analyze_sentiment(request: TextRequest):
    """Analyze text sentiment"""
    try:
        logger.info(f"Processing sentiment analysis request")
        blob = TextBlob(request.text)
        
        return SentimentAnalysis(
            polarity=blob.sentiment.polarity,
            subjectivity=blob.sentiment.subjectivity,
            assessment="positive" if blob.sentiment.polarity > 0 else "negative" if blob.sentiment.polarity < 0 else "neutral",
            confidence=abs(blob.sentiment.polarity)
        )
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing sentiment: {str(e)}")

@app.post("/entities", response_model=List[Entity])
async def extract_entities(request: TextRequest):
    """Extract named entities from text"""
    try:
        logger.info(f"Processing entity extraction request")
        doc = nlp(request.text)
        
        return [
            Entity(
                text=ent.text,
                label=ent.label_,
                start=ent.start_char,
                end=ent.end_char,
                confidence=ent._.confidence if hasattr(ent._, 'confidence') else None
            )
            for ent in doc.ents
        ]
        
    except Exception as e:
        logger.error(f"Error extracting entities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting entities: {str(e)}")

@app.post("/keywords")
async def extract_keywords_endpoint(request: TextRequest):
    """Extract keywords from text"""
    try:
        logger.info(f"Processing keyword extraction request")
        keywords = extract_keywords(request.text)
        return {"keywords": keywords}
    except Exception as e:
        logger.error(f"Error extracting keywords: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting keywords: {str(e)}")

@app.post("/summarize")
async def summarize_text(request: TextRequest):
    """Generate a summary of the text using Hugging Face"""
    if not summarizer:
        raise HTTPException(
            status_code=503,
            detail="Hugging Face summarizer is not initialized."
        )
    
    try:
        logger.info(f"Processing text summarization request")
        
        # Split text into chunks if it's too long
        max_chunk_length = 1024
        chunks = [request.text[i:i + max_chunk_length] for i in range(0, len(request.text), max_chunk_length)]
        
        summaries = []
        for chunk in chunks:
            result = summarizer(chunk, max_length=130, min_length=30, do_sample=False)
            summaries.append(result[0]['summary_text'])
        
        summary = " ".join(summaries)
        return {"summary": summary}
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8004))
    uvicorn.run(app, host="127.0.0.1", port=port) 