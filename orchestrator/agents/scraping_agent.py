# Force rebuild

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="Scraping Agent")

class Request(BaseModel):
    url: str

class Response(BaseModel):
    data: str

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok"}

@app.post("/scrape", response_model=Response)
async def scrape(request: Request):
    """
    Simulate web scraping
    """
    try:
        # Placeholder: In reality, this would call an actual scraping service
        return Response(data=f"Scraped data from: {request.url}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 