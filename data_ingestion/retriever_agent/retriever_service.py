from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging
import json
from pathlib import Path
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from sklearn.metrics.pairwise import cosine_similarity
from redis.asyncio import Redis
from sklearn.preprocessing import normalize
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Redis client
redis_client = redis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)

# Initialize sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize FAISS index
dimension = 384  # dimension of all-MiniLM-L6-v2 embeddings
faiss_index = faiss.IndexFlatIP(dimension)  # Use Inner Product for cosine similarity

app = FastAPI(
    title="Document Retriever",
    description="API service for retrieving and searching documents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize rate limiter
@app.on_event("startup")
async def startup():
    if "pytest" in sys.modules:
        return
    await FastAPILimiter.init(redis_client)

# Pydantic models
class Document(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

class SearchQuery(BaseModel):
    query: str
    limit: int = 5
    min_score: float = 0.5

class SearchResult(BaseModel):
    document: Document
    score: float

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None

# Document storage
documents: Dict[str, Document] = {}
document_ids: List[str] = []  # Keep track of document order for FAISS

def get_redis_client():
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        decode_responses=True
    )

def get_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

def get_faiss_index():
    # Use a global variable for the default, but allow override in tests
    global faiss_index
    return faiss_index

def get_document_embedding(text: str) -> List[float]:
    """Get normalized embedding for a document"""
    emb = model.encode(text)
    emb = emb / np.linalg.norm(emb)
    return emb.tolist()

def compute_similarity(query_embedding: List[float], doc_embedding: List[float]) -> float:
    """Compute cosine similarity between query and document embeddings"""
    return float(cosine_similarity(
        np.array(query_embedding).reshape(1, -1),
        np.array(doc_embedding).reshape(1, -1)
    )[0][0])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "documents_count": await redis_client.dbsize(),
            "faiss_index_size": faiss_index.ntotal if faiss_index else 0
        }
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents", response_model=Document)
async def add_document(document: Document,
                      redis_client=Depends(get_redis_client),
                      model=Depends(get_model),
                      faiss_index=Depends(get_faiss_index)):
    """
    Add a document to the index
    
    Args:
        document: Document to add
    
    Returns:
        Added document with embedding
    """
    try:
        if not document.embedding:
            embedding = model.encode(document.content)
            document.embedding = embedding.tolist()
        doc_dict = document.model_dump()
        # Serialize metadata and embedding as JSON strings
        doc_dict["metadata"] = json.dumps(doc_dict["metadata"])
        doc_dict["embedding"] = json.dumps(doc_dict["embedding"])
        await redis_client.hset(f"doc:{document.id}", mapping=doc_dict)
        embedding_array = np.array([document.embedding], dtype=np.float32)
        faiss_index.add(embedding_array)
        return document
    except Exception as e:
        logger.error(f"Error adding document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{doc_id}", response_model=Document)
async def get_document(doc_id: str,
                      redis_client=Depends(get_redis_client)):
    """
    Get a document by ID
    
    Args:
        document_id: Document ID
    
    Returns:
        Document
    """
    try:
        doc_data = await redis_client.hgetall(f"doc:{doc_id}")
        if not doc_data:
            raise HTTPException(status_code=404, detail="Document not found")
        # Deserialize metadata and embedding
        doc_data["metadata"] = json.loads(doc_data["metadata"])
        doc_data["embedding"] = json.loads(doc_data["embedding"])
        return Document(**doc_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=List[SearchResult])
async def search_documents(query: SearchQuery,
                          redis_client=Depends(get_redis_client),
                          model=Depends(get_model),
                          faiss_index=Depends(get_faiss_index)):
    """
    Search documents by query
    
    Args:
        query: Search query
    
    Returns:
        List of search results
    """
    try:
        query_embedding = model.encode(query.query)
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
        scores, indices = faiss_index.search(query_embedding, query.limit)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and score >= query.min_score:
                doc_data = redis_client.hgetall(f"doc:{idx}")
                if doc_data:
                    doc = Document(**doc_data)
                    results.append(SearchResult(document=doc, score=float(score)))
        return results
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str,
                         redis_client=Depends(get_redis_client),
                         model=Depends(get_model)):
    """
    Delete a document
    
    Args:
        document_id: Document ID
    
    Returns:
        Success message
    """
    try:
        if not redis_client.exists(f"doc:{doc_id}"):
            raise HTTPException(status_code=404, detail="Document not found")
        await redis_client.delete(f"doc:{doc_id}")
        global faiss_index
        dimension = model.get_sentence_embedding_dimension()
        new_index = faiss.IndexFlatIP(dimension)
        for key in redis_client.scan_iter("doc:*"):
            doc_data = redis_client.hgetall(key)
            if doc_data:
                doc = Document(**doc_data)
                embedding_array = np.array([doc.embedding], dtype=np.float32)
                new_index.add(embedding_array)
        faiss_index = new_index
        return {"message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 