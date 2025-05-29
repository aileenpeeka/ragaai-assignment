# Force rebuild

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="Analysis Agent")

class Request(BaseModel):
    data: str

class Response(BaseModel):
    result: str

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok"}

@app.post("/analyze", response_model=Response)
async def analyze(request: Request):
    """
    Simulate data analysis
    """
    try:
        # Placeholder: In reality, this would call an actual analysis service
        return Response(result=f"Analysis result for: {request.data}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 