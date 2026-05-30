"""
services/sheets.py  ─  All Google Sheets read / write operations
"""
from __future__ import annotations

import threading
from datetime import datetime
from typing import Optional
import time

import pytz
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.settings import (
    GOOGLE_CREDENTIALS_PATH,
    GOOGLE_SHEET_ID,
    SHEET_PRODUCTS,
    SHEET_TRANSACTIONS,
    TIMEZONE,
)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Column indices (0-based) for the Products sheet
P_ID = 0   # Auto-generated product ID
P_NAME = 1
P_PRICE = 2   # Selling price
P_COST = 3   # Cost / purchase price
P_QTY = 4
P_ADDED = 5   # Date added

# Column indices for the Transactions sheet
T_ID = 0
T_DATE = 1
T_TYPE = 2   # STOCK_IN | STOCK_OUT | ADD_PRODUCT | DELETE_PRODUCT | SALE
T_PROD_ID = 3
T_PROD = 4
T_QTY = 5
T_PRICE = 6
T_NOTE = 7
T_USER = 8


class SheetsService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cache = {}
        self._cache_ttl = 30  # seconds — refresh every 30s

        creds = Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_PATH, scopes=SCOPES
        )
        self._svc = build("sheets", "v4", credentials=creds,
                          cache_discovery=False)
        self._sheet = self._svc.spreadsheets()
        self._ensure_headers()

    def _cache_get(self, key: str):
        entry = self._cache.get(key)
        if entry and (time.time() - entry["ts"]) < self._cache_ttl:
            return entry["data"]
        return None

    def _cache_set(self, key: str, data):
        self._cache[key] = {"data": data, "ts": time.time()}

    def _cache_clear(self):
        self._cache.clear()

    # ─────────────────────────────── helpers ──────────────────────────────────

    def _now(self) -> str:
        tz = pytz.timezone(TIMEZONE)
        return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    def _read(self, tab: str, range_: str = "") -> list[list]:
        rng = f"{tab}!{range_}" if range_ else tab
        try:
            result = self._sheet.values().get(
                spreadsheetId=GOOGLE_SHEET_ID, range=rng
            ).execute()
            return result.get("values", [])
        except HttpError as e:
            raise RuntimeError(f"Sheets read error: {e}") from e

    def _append(self, tab: str, rows: list[list]) -> None:
        self._sheet.values().append(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=tab,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": rows},
        ).execute()

    def _update_cell(self, tab: str, row: int, col: int, value) -> None:
        """row/col are 1-based for the API."""
        col_letter = chr(ord("A") + col - 1)
        rng = f"{tab}!{col_letter}{row}"
        self._sheet.values().update(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=rng,
            valueInputOption="USER_ENTERED",
            body={"values": [[value]]},
        ).execute()

    def _delete_row(self, sheet_id: int, row_index: int) -> None:
        """row_index is 0-based."""
        self._svc.spreadsheets().batchUpdate(
            spreadsheetId=GOOGLE_SHEET_ID,
            body={
                "requests": [
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "ROWS",
                                "startIndex": row_index,
                                "endIndex": row_index + 1,
                            }
                        }
                    }
                ]
            },
        ).execute()

    def _get_sheet_id(self, tab_name: str) -> int:
        meta = self._svc.spreadsheets().get(
            spreadsheetId=GOOGLE_SHEET_ID
        ).execute()
        for s in meta["sheets"]:
            if s["properties"]["title"] == tab_name:
                return s["properties"]["sheetId"]
        raise ValueError(f"Sheet tab '{tab_name}' not found")

    def _next_id(self, rows: list[list]) -> str:
        if len(rows) <= 1:
            return "P001"
        existing = [r[P_ID] for r in rows[1:] if r and len(r) > P_ID and r[P_ID] and r[P_ID].startswith("P")]
        nums = [int(x[1:]) for x in existing if len(x) > 1 and x[1:].isdigit()]
        return f"P{(max(nums) + 1):03d}" if nums else "P001"

    def _next_txn_id(self, rows: list[list]) -> str:
        if len(rows) <= 1:
            return "T0001"
        existing = [r[T_ID] for r in rows[1:] if r and len(r) > T_ID and r[T_ID] and r[T_ID].startswith("T")]
        nums = [int(x[1:]) for x in existing if len(x) > 1 and x[1:].isdigit()]
        return f"T{(max(nums) + 1):04d}" if nums else "T0001"

    # ──────────────────────────── init sheets ─────────────────────────────────

    def _ensure_headers(self) -> None:
        with self._lock:
            prod_rows = self._read(SHEET_PRODUCTS)
            if not prod_rows:
                self._append(SHEET_PRODUCTS, [[
                    "ID", "Product Name", "Price", "Cost", "Quantity", "Date Added"
                ]])
            txn_rows = self._read(SHEET_TRANSACTIONS)
            if not txn_rows:
                self._append(SHEET_TRANSACTIONS, [[
                    "Txn ID", "Date/Time", "Type", "Product ID",
                    "Product Name", "Quantity", "Unit Price", "Note", "User ID"
                ]])

    # ──────────────────────────── products ────────────────────────────────────

    def get_all_products(self) -> list[dict]:
        with self._lock:
            rows = self._read(SHEET_PRODUCTS)
        if len(rows) <= 1:
            return []
        
        products = []
        for r in rows[1:]:
            if not r or len(r) <= P_ID or not r[P_ID]:
                continue
            
            try:
                price = float(r[P_PRICE]) if len(r) > P_PRICE and r[P_PRICE] else 0.0
            except (ValueError, TypeError):
                price = 0.0
            
            try:
                cost = float(r[P_COST]) if len(r) > P_COST and r[P_COST] else 0.0
            except (ValueError, TypeError):
                cost = 0.0
            
            try:
                quantity = int(r[P_QTY]) if len(r) > P_QTY and r[P_QTY] else 0
            except (ValueError, TypeError):
                quantity = 0
            
            products.append({
                "id":       r[P_ID],
                "name":     r[P_NAME] if len(r) > P_NAME else "",
                "price":    price,
                "cost":     cost,
                "quantity": quantity,
                "added":    r[P_ADDED] if len(r) > P_ADDED else "",
            })
        
        return products

    def find_product(self, product_id: str) -> Optional[dict]:
        products = self.get_all_products()
        for p in products:
            if p["id"].upper() == product_id.upper():
                return p
        return None

    def search_products(self, query: str) -> list[dict]:
        q = query.lower()
        return [
            p for p in self.get_all_products()
            if q in p["name"].lower() or q in p["id"].lower()
        ]

    def add_product(
        self,
        name: str,
        price: float,
        cost: float,
        quantity: int,
        user_id: int,
    ) -> dict:
        with self._lock:
            rows = self._read(SHEET_PRODUCTS)
            pid = self._next_id(rows)
            now = self._now()
            # Prefix date with single quote to force text format in Google Sheets
            date_str = f"'{now}"
            self._append(SHEET_PRODUCTS, [
                         [pid, name, price, cost, quantity, date_str]])
            # log transaction
            txn_rows = self._read(SHEET_TRANSACTIONS)
            tid = self._next_txn_id(txn_rows)
            self._append(SHEET_TRANSACTIONS, [[
                tid, date_str, "ADD_PRODUCT", pid, name, quantity, cost,
                "Product added", user_id
            ]])
            self._cache_clear()  # Clear cache to force refresh
        return {"id": pid, "name": name, "price": price,
                "cost": cost, "quantity": quantity, "added": now}

    def delete_product(self, product_id: str, user_id: int) -> bool:
        with self._lock:
            rows = self._read(SHEET_PRODUCTS)
            for i, r in enumerate(rows):
                if i == 0:
                    continue
                if r and len(r) > P_ID and r[P_ID].upper() == product_id.upper():
                    sheet_id = self._get_sheet_id(SHEET_PRODUCTS)
                    self._delete_row(sheet_id, i)
                    # log
                    txn_rows = self._read(SHEET_TRANSACTIONS)
                    tid = self._next_txn_id(txn_rows)
                    now = self._now()
                    # Prefix date with single quote to force text format
                    date_str = f"'{now}"
                    name = r[P_NAME] if len(r) > P_NAME else "?"
                    self._append(SHEET_TRANSACTIONS, [[
                        tid, date_str, "DELETE_PRODUCT", product_id, name, 0, 0,
                        "Product deleted", user_id
                    ]])
                    self._cache_clear()
                    return True
        return False

    def _get_product_row_index(self, product_id: str, rows: list[list] = None) -> Optional[int]:
        """Returns 1-based row index in the sheet (header = row 1)."""
        if rows is None:
            rows = self._read(SHEET_PRODUCTS)
        for i, r in enumerate(rows):
            if i == 0:
                continue
            if r and len(r) > P_ID and r[P_ID].upper() == product_id.upper():
                return i + 1  # 1-based
        return None

    # ──────────────────────────── stock ops ───────────────────────────────────

    def stock_in(
        self,
        product_id: str,
        qty: int,
        note: str,
        user_id: int,
    ) -> dict:
        with self._lock:
            rows = self._read(SHEET_PRODUCTS)
            prod = None
            for r in rows[1:]:
                if r and len(r) > P_ID and r[P_ID].upper() == product_id.upper():
                    try:
                        price = float(r[P_PRICE]) if len(r) > P_PRICE and r[P_PRICE] else 0.0
                    except (ValueError, TypeError):
                        price = 0.0
                    
                    try:
                        cost = float(r[P_COST]) if len(r) > P_COST and r[P_COST] else 0.0
                    except (ValueError, TypeError):
                        cost = 0.0
                    
                    try:
                        quantity = int(r[P_QTY]) if len(r) > P_QTY and r[P_QTY] else 0
                    except (ValueError, TypeError):
                        quantity = 0
                    
                    prod = {
                        "id": r[P_ID],
                        "name": r[P_NAME] if len(r) > P_NAME else "",
                        "price": price,
                        "cost": cost,
                        "quantity": quantity,
                        "added": r[P_ADDED] if len(r) > P_ADDED else "",
                    }
                    break
            
            if not prod:
                raise ValueError(f"Product '{product_id}' not found.")
            
            new_qty = prod["quantity"] + qty
            row_idx = self._get_product_row_index(product_id, rows)
            self._update_cell(SHEET_PRODUCTS, row_idx, P_QTY + 1, new_qty)
            txn_rows = self._read(SHEET_TRANSACTIONS)
            tid = self._next_txn_id(txn_rows)
            now = self._now()
            # Prefix date with single quote to force text format
            date_str = f"'{now}"
            self._append(SHEET_TRANSACTIONS, [[
                tid, date_str, "STOCK_IN", product_id, prod["name"], qty,
                prod["cost"], note or "Stock in", user_id
            ]])
            self._cache_clear()
        return {**prod, "old_qty": prod["quantity"], "new_qty": new_qty, "txn_id": tid}

    def stock_out(
        self,
        product_id: str,
        qty: int,
        note: str,
        user_id: int,
        txn_type: str = "STOCK_OUT",
    ) -> dict:
        with self._lock:
            rows = self._read(SHEET_PRODUCTS)
            prod = None
            for r in rows[1:]:
                if r and len(r) > P_ID and r[P_ID].upper() == product_id.upper():
                    try:
                        price = float(r[P_PRICE]) if len(r) > P_PRICE and r[P_PRICE] else 0.0
                    except (ValueError, TypeError):
                        price = 0.0
                    
                    try:
                        cost = float(r[P_COST]) if len(r) > P_COST and r[P_COST] else 0.0
                    except (ValueError, TypeError):
                        cost = 0.0
                    
                    try:
                        quantity = int(r[P_QTY]) if len(r) > P_QTY and r[P_QTY] else 0
                    except (ValueError, TypeError):
                        quantity = 0
                    
                    prod = {
                        "id": r[P_ID],
                        "name": r[P_NAME] if len(r) > P_NAME else "",
                        "price": price,
                        "cost": cost,
                        "quantity": quantity,
                        "added": r[P_ADDED] if len(r) > P_ADDED else "",
                    }
                    break
            
            if not prod:
                raise ValueError(f"Product '{product_id}' not found.")
            if prod["quantity"] < qty:
                raise ValueError(
                    f"Insufficient stock. Available: {prod['quantity']}, Requested: {qty}"
                )
            
            new_qty = prod["quantity"] - qty
            row_idx = self._get_product_row_index(product_id, rows)
            self._update_cell(SHEET_PRODUCTS, row_idx, P_QTY + 1, new_qty)
            txn_rows = self._read(SHEET_TRANSACTIONS)
            tid = self._next_txn_id(txn_rows)
            now = self._now()
            # Prefix date with single quote to force text format
            date_str = f"'{now}"
            price = prod["price"] if txn_type == "SALE" else prod["cost"]
            self._append(SHEET_TRANSACTIONS, [[
                tid, date_str, txn_type, product_id, prod["name"], qty,
                price, note or txn_type.title(), user_id
            ]])
            self._cache_clear()
        return {**prod, "old_qty": prod["quantity"], "new_qty": new_qty,
                "txn_id": tid, "total": qty * price}

    def sale(self, product_id: str, qty: int, note: str, user_id: int) -> dict:
        return self.stock_out(product_id, qty, note, user_id, txn_type="SALE")

    # ──────────────────────────── transactions ─────────────────────────────────

    def get_transactions(self, limit: int = 20) -> list[dict]:
        with self._lock:
            rows = self._read(SHEET_TRANSACTIONS)
        data = rows[1:] if len(rows) > 1 else []
        data = data[-limit:]  # most recent N
        result = []
        for r in reversed(data):
            if not r:
                continue
            
            try:
                qty = str(r[T_QTY]) if len(r) > T_QTY else "0"
            except (ValueError, TypeError):
                qty = "0"
            
            try:
                price = str(r[T_PRICE]) if len(r) > T_PRICE else "0"
            except (ValueError, TypeError):
                price = "0"
            
            result.append({
                "id":       r[T_ID] if len(r) > T_ID else "",
                "date":     r[T_DATE] if len(r) > T_DATE else "",
                "type":     r[T_TYPE] if len(r) > T_TYPE else "",
                "prod_id":  r[T_PROD_ID] if len(r) > T_PROD_ID else "",
                "product":  r[T_PROD] if len(r) > T_PROD else "",
                "qty":      qty,
                "price":    price,
                "note":     r[T_NOTE] if len(r) > T_NOTE else "",
                "user":     r[T_USER] if len(r) > T_USER else "",
            })
        return result

    def get_all_transactions_raw(self) -> list[list]:
        with self._lock:
            return self._read(SHEET_TRANSACTIONS)

    # ──────────────────────────── summary ─────────────────────────────────────

    def get_summary(self) -> dict:
        products = self.get_all_products()
        total_products = len(products)
        total_qty = sum(p["quantity"] for p in products)
        total_value = sum(p["quantity"] * p["price"] for p in products)
        total_cost = sum(p["quantity"] * p["cost"] for p in products)
        low_stock = [p for p in products if p["quantity"] <= 10]

        txns = self.get_transactions(50)
        recent_in = 0
        recent_out = 0
        recent_sales = 0.0
        
        for t in txns:
            try:
                if t["type"] == "STOCK_IN":
                    recent_in += int(t["qty"])
                elif t["type"] in ("STOCK_OUT", "SALE"):
                    recent_out += int(t["qty"])
                
                if t["type"] == "SALE":
                    recent_sales += float(t["qty"]) * float(t["price"])
            except (ValueError, TypeError):
                continue

        return {
            "total_products": total_products,
            "total_qty":      total_qty,
            "total_value":    total_value,
            "total_cost":     total_cost,
            "gross_profit":   total_value - total_cost,
            "low_stock":      low_stock,
            "recent_in":      recent_in,
            "recent_out":     recent_out,
            "recent_sales":   recent_sales,
        }

    def get_low_stock_products(self, threshold: int = 10) -> list[dict]:
        return [p for p in self.get_all_products() if p["quantity"] <= threshold]
