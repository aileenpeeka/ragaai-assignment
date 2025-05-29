# Create data directory if it doesn't exist
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Initialize SEC downloader
sec_downloader = Downloader(DATA_DIR / "sec_filings", email_address=os.getenv("SEC_EMAIL_ADDRESS", "test@example.com")) 

