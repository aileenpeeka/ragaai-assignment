from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="LLM Service")

class Request(BaseModel):
    text: str

class Response(BaseModel):
    response: str

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/process", response_model=Response)
async def process(request: Request):
    try:
        user_text = request.text.lower()
        if "market brief" in user_text:
            # --- Simple yfinance fetch ---
            try:
                import yfinance as yf
                stock = yf.Ticker("AAPL")
                data = stock.history(period="1d")
                price = data['Close'].iloc[0]
                brief = f"Apple's latest closing price is ${price:.2f}."
                response_text = f"Here is your market brief: {brief}"
            except Exception as ex:
                response_text = f"Market brief not available due to error: {ex}"
            return Response(response=response_text)
        # fallback: echo/placeholder
        return Response(response=f"LLM response for: {request.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
