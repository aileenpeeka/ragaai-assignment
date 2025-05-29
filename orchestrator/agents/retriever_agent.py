# Force rebuild

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="Retriever Agent")

class Request(BaseModel):
    query: str

class Response(BaseModel):
    results: list

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok"}

@app.post("/search", response_model=Response)
async def search(request: Request):
    """
    Simulate document retrieval
    """
    try:
        # Placeholder: In reality, this would call the actual retriever service
        return Response(results=[{"id": "doc1", "content": f"Retrieved document for query: {request.query}"}])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 