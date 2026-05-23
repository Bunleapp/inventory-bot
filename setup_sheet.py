"""
setup_sheet.py  ─  One-time Google Sheet initialiser
Run once: python setup_sheet.py

Creates the two tabs with headers and sample formatting.
"""
import sys
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from config.settings import GOOGLE_CREDENTIALS_PATH, GOOGLE_SHEET_ID, validate

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

HEADER_BG = {"red": 0.063, "green": 0.204, "blue": 0.376}  # #103468
HEADER_FG = {"red": 1, "green": 1, "blue": 1}


def hex_to_rgb(hex_str: str) -> dict:
    h = hex_str.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return {"red": r/255, "green": g/255, "blue": b/255}


def ensure_tab(svc, name: str, existing: list[str]) -> int:
    """Create tab if missing; return its sheetId."""
    for s in svc.spreadsheets().get(
        spreadsheetId=GOOGLE_SHEET_ID
    ).execute()["sheets"]:
        if s["properties"]["title"] == name:
            return s["properties"]["sheetId"]

    resp = svc.spreadsheets().batchUpdate(
        spreadsheetId=GOOGLE_SHEET_ID,
        body={"requests": [{"addSheet": {"properties": {"title": name}}}]},
    ).execute()
    return resp["replies"][0]["addSheet"]["properties"]["sheetId"]


def write_headers(svc, tab: str, headers: list[str]) -> None:
    svc.spreadsheets().values().update(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=f"{tab}!A1",
        valueInputOption="USER_ENTERED",
        body={"values": [headers]},
    ).execute()


def style_header_row(svc, sheet_id: int, n_cols: int) -> None:
    svc.spreadsheets().batchUpdate(
        spreadsheetId=GOOGLE_SHEET_ID,
        body={"requests": [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": n_cols,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": HEADER_BG,
                            "textFormat": {
                                "foregroundColor": HEADER_FG,
                                "bold": True,
                                "fontSize": 10,
                            },
                            "horizontalAlignment": "CENTER",
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
                }
            },
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "gridProperties": {"frozenRowCount": 1},
                    },
                    "fields": "gridProperties.frozenRowCount",
                }
            },
        ]},
    ).execute()


def main() -> None:
    try:
        validate()
    except EnvironmentError as e:
        print(f"Config error: {e}")
        sys.exit(1)

    creds = Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_PATH, scopes=SCOPES)
    svc = build("sheets", "v4", credentials=creds, cache_discovery=False)

    print("Setting up Products sheet…")
    prod_id = ensure_tab(svc, "Products", [])
    write_headers(svc, "Products", [
                  "ID", "Product Name", "Price", "Cost", "Quantity", "Date Added"])
    style_header_row(svc, prod_id, 6)

    print("Setting up Transactions sheet…")
    txn_id = ensure_tab(svc, "Transactions", [])
    write_headers(svc, "Transactions", [
        "Txn ID", "Date/Time", "Type", "Product ID",
        "Product Name", "Quantity", "Unit Price", "Note", "User ID"
    ])
    style_header_row(svc, txn_id, 9)

    print("✅ Google Sheet is ready!")
    print(
        f"   Sheet URL: https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/edit")


if __name__ == "__main__":
    main()
