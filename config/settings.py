"""
config/settings.py  ─  Centralised configuration loader
"""
import os
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
GOOGLE_CREDENTIALS_PATH: str = os.getenv(
    "GOOGLE_CREDENTIALS_PATH", "credentials.json")

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
