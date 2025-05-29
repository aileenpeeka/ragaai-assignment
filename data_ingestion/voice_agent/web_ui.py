from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
import httpx
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/query")
async def query(request: Request, symbol: str = Form(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://localhost:8005/market-query", json={"text": symbol, "language": "en-US"})
            data = response.json()
        return templates.TemplateResponse("index.html", {"request": request, "response": data})
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005) 