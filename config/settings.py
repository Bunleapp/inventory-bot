"""
config/settings.py  ─  Centralised configuration loader
"""
import os
import json
import tempfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ──────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

_raw_ids = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS: set[int] = {
    int(uid.strip()) for uid in _raw_ids.split(",") if uid.strip().isdigit()
}

# ── Google Sheets ─────────────────────────────────────────────────────────────
GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "")

# Handle credentials for Railway deployment
# Railway stores credentials as JSON string in environment variable
_creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if _creds_json:
    # Running on Railway - create temp file from env variable
    try:
        # Parse JSON to validate it
        creds_data = json.loads(_creds_json)
        
        # Create temp file
        _temp_creds = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(creds_data, _temp_creds)
        _temp_creds.close()
        GOOGLE_CREDENTIALS_PATH = _temp_creds.name
        print(f"✓ Using Railway credentials from environment variable")
    except json.JSONDecodeError as e:
        print(f"✗ Failed to parse GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")
        raise
else:
    # Running locally - use file path
    GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    if Path(GOOGLE_CREDENTIALS_PATH).exists():
        print(f"✓ Using local credentials file: {GOOGLE_CREDENTIALS_PATH}")
    else:
        print(f"✗ Credentials file not found: {GOOGLE_CREDENTIALS_PATH}")

# Sheet tab names  (change only if you rename the tabs in Google Sheets)
SHEET_PRODUCTS = "Products"
SHEET_TRANSACTIONS = "Transactions"
SHEET_SETTINGS = "Settings"

# ── Inventory ─────────────────────────────────────────────────────────────────
LOW_STOCK_THRESHOLD: int = int(os.getenv("LOW_STOCK_THRESHOLD", "10"))
LOW_STOCK_CHECK_INTERVAL: int = int(
    os.getenv("LOW_STOCK_CHECK_INTERVAL", "60"))  # minutes

# ── Timezone ──────────────────────────────────────────────────────────────────
TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Phnom_Penh")

# ── Validation ────────────────────────────────────────────────────────────────


def validate() -> None:
    missing = []
    if not BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not GOOGLE_SHEET_ID:
        missing.append("GOOGLE_SHEET_ID")
    if not ALLOWED_USER_IDS:
        missing.append("ALLOWED_USER_IDS")
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Copy .env.example → .env and fill in the values."
        )
