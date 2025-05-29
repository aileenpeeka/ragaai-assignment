# Force rebuild

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="Language Agent")

class Request(BaseModel):
    text: str

class Response(BaseModel):
    response: str

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok"}

@app.post("/process", response_model=Response)
async def process(request: Request):
    """
    Simulate language processing
    """
    try:
        # Placeholder: In reality, this would call an actual language model
        return Response(response=f"Language Agent processed: {request.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004) 