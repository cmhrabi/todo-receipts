from dotenv import load_dotenv
import os

load_dotenv()

NOTION_API_KEY: str = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID: str = os.getenv("NOTION_DATABASE_ID", "")
PRINTER_TYPE: str = os.getenv("PRINTER_TYPE", "console")
POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "10"))
SETTLE_DELAY_SECONDS: int = int(os.getenv("SETTLE_DELAY_SECONDS", "10"))

if not NOTION_API_KEY or not NOTION_DATABASE_ID:
    raise SystemExit("Error: NOTION_API_KEY and NOTION_DATABASE_ID must be set in .env")
