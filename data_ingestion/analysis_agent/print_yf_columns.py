import yfinance as yf

symbols = ["AAPL", "MSFT", "TSM", "005930.KS", "SPY"]
start_date = "2024-05-01"
end_date = "2024-05-24"

data = yf.download(symbols, start=start_date, end=end_date, progress=False)
print("Columns:", data.columns)
print("Data head:")
print(data.head()) 