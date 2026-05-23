"""
services/export.py  ─  CSV and PDF export generators
"""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import TYPE_CHECKING

import pytz
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)

from config.settings import TIMEZONE

if TYPE_CHECKING:
    from services.sheets import SheetsService

# ─── colour palette ───────────────────────────────────────────────────────────
BRAND_DARK = colors.HexColor("#1a1a2e")
BRAND_MID = colors.HexColor("#16213e")
BRAND_ACCENT = colors.HexColor("#0f3460")
BRAND_TEAL = colors.HexColor("#533483")
POSITIVE = colors.HexColor("#27ae60")
NEGATIVE = colors.HexColor("#e74c3c")
HEADER_TXT = colors.white
ROW_ALT = colors.HexColor("#f0f4ff")


def _now_str() -> str:
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")


# ─────────────────────────── CSV exports ──────────────────────────────────────

def export_products_csv(sheets: "SheetsService") -> io.BytesIO:
    products = sheets.get_all_products()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["ID", "Product Name", "Price", "Cost", "Quantity",
                "Stock Value", "Est. Profit", "Date Added"])
    for p in products:
        w.writerow([
            p["id"], p["name"],
            f"{p['price']:.2f}", f"{p['cost']:.2f}", p["quantity"],
            f"{p['quantity'] * p['price']:.2f}",
            f"{p['quantity'] * (p['price'] - p['cost']):.2f}",
            p["added"],
        ])
    return io.BytesIO(buf.getvalue().encode("utf-8-sig"))


def export_transactions_csv(sheets: "SheetsService") -> io.BytesIO:
    raw = sheets.get_all_transactions_raw()
    buf = io.StringIO()
    w = csv.writer(buf)
    for row in raw:
        w.writerow(row)
    return io.BytesIO(buf.getvalue().encode("utf-8-sig"))


# ─────────────────────────── PDF helpers ──────────────────────────────────────

def _make_styles():
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "ReportTitle",
        parent=base["Title"],
        fontSize=20,
        textColor=BRAND_DARK,
        spaceAfter=6,
    )
    sub = ParagraphStyle(
        "SubTitle",
        parent=base["Normal"],
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=14,
    )
    section = ParagraphStyle(
        "Section",
        parent=base["Heading2"],
        fontSize=12,
        textColor=BRAND_ACCENT,
        spaceBefore=12,
        spaceAfter=4,
    )
    normal = ParagraphStyle(
        "Body",
        parent=base["Normal"],
        fontSize=9,
    )
    return title, sub, section, normal


def _header_style(n_cols: int) -> TableStyle:
    return TableStyle([
        # header row
        ("BACKGROUND",   (0, 0), (n_cols - 1, 0), BRAND_ACCENT),
        ("TEXTCOLOR",    (0, 0), (n_cols - 1, 0), HEADER_TXT),
        ("FONTNAME",     (0, 0), (n_cols - 1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (n_cols - 1, 0), 9),
        ("ALIGN",        (0, 0), (n_cols - 1, 0), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (n_cols - 1, 0), 8),
        ("TOPPADDING",   (0, 0), (n_cols - 1, 0), 8),
        # body rows
        ("FONTSIZE",     (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ("GRID",         (0, 0), (-1, -1), 0.25, colors.HexColor("#d0d0d0")),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
    ])


# ─────────────────────────── PDF: inventory report ────────────────────────────

def export_inventory_pdf(sheets: "SheetsService") -> io.BytesIO:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    title_s, sub_s, section_s, normal_s = _make_styles()
    story = []

    # ── Header ──────────────────────────────────────────────────────────────
    story.append(Paragraph("📦  Inventory Report", title_s))
    story.append(
        Paragraph(f"Generated: {_now_str()}  ·  Timezone: {TIMEZONE}", sub_s))

    # ── Summary cards ────────────────────────────────────────────────────────
    summary = sheets.get_summary()
    cards = [
        ["Metric", "Value"],
        ["Total Products",     str(summary["total_products"])],
        ["Total Units in Stock", f"{summary['total_qty']:,}"],
        ["Total Stock Value",  f"${summary['total_value']:,.2f}"],
        ["Total Cost Value",   f"${summary['total_cost']:,.2f}"],
        ["Estimated Profit",   f"${summary['gross_profit']:,.2f}"],
        ["Low Stock Items",    str(len(summary["low_stock"]))],
    ]
    t = Table(cards, colWidths=[8 * cm, 6 * cm])
    t.setStyle(_header_style(2))
    # colour the profit row
    profit_row = 6
    color = POSITIVE if summary["gross_profit"] >= 0 else NEGATIVE
    t.setStyle(TableStyle([
        ("TEXTCOLOR", (1, profit_row), (1, profit_row), color),
        ("FONTNAME",  (1, profit_row), (1, profit_row), "Helvetica-Bold"),
    ]))
    story.append(Paragraph("Summary", section_s))
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))

    # ── All products table ────────────────────────────────────────────────────
    story.append(Paragraph("All Products", section_s))
    products = sheets.get_all_products()
    if products:
        headers = ["ID", "Name", "Price", "Cost",
                   "Qty", "Stock Value", "Margin"]
        rows = [headers]
        for p in products:
            margin = ((p["price"] - p["cost"]) / p["price"]
                      * 100) if p["price"] else 0
            rows.append([
                p["id"],
                p["name"][:30],
                f"${p['price']:.2f}",
                f"${p['cost']:.2f}",
                str(p["quantity"]),
                f"${p['quantity'] * p['price']:.2f}",
                f"{margin:.1f}%",
            ])
        col_w = [1.5*cm, 5*cm, 2*cm, 2*cm, 1.5*cm, 2.5*cm, 2*cm]
        t2 = Table(rows, colWidths=col_w, repeatRows=1)
        t2.setStyle(_header_style(len(headers)))
        # Highlight low stock
        for i, p in enumerate(products, start=1):
            if p["quantity"] <= 10:
                t2.setStyle(TableStyle([
                    ("TEXTCOLOR", (4, i), (4, i), NEGATIVE),
                    ("FONTNAME",  (4, i), (4, i), "Helvetica-Bold"),
                ]))
        story.append(t2)
    else:
        story.append(Paragraph("No products found.", normal_s))

    # ── Low stock alert ───────────────────────────────────────────────────────
    low = summary["low_stock"]
    if low:
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph("⚠️  Low Stock Alerts", section_s))
        lrows = [["ID", "Name", "Current Qty", "Price"]]
        for p in low:
            lrows.append([p["id"], p["name"], str(
                p["quantity"]), f"${p['price']:.2f}"])
        lt = Table(lrows, colWidths=[2*cm, 8*cm, 3*cm, 3*cm])
        lt.setStyle(_header_style(4))
        lt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NEGATIVE),
        ]))
        story.append(lt)

    doc.build(story)
    buf.seek(0)
    return buf


# ─────────────────────────── PDF: transactions report ─────────────────────────

def export_transactions_pdf(sheets: "SheetsService", limit: int = 100) -> io.BytesIO:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    title_s, sub_s, section_s, _ = _make_styles()
    story = []

    story.append(Paragraph("🔄  Transaction History", title_s))
    story.append(Paragraph(
        f"Generated: {_now_str()}  ·  Showing last {limit} transactions", sub_s
    ))

    txns = sheets.get_transactions(limit)
    if txns:
        headers = ["Txn ID", "Date/Time", "Type",
                   "Prod ID", "Product", "Qty", "Price", "Note"]
        rows = [headers]
        type_colors = {
            "STOCK_IN":       POSITIVE,
            "SALE":           colors.HexColor("#2980b9"),
            "STOCK_OUT":      NEGATIVE,
            "ADD_PRODUCT":    BRAND_TEAL,
            "DELETE_PRODUCT": colors.HexColor("#7f8c8d"),
        }
        for t in txns:
            rows.append([
                t["id"], t["date"], t["type"],
                t["prod_id"], t["product"][:25],
                t["qty"], f"${float(t['price']):.2f}" if t["price"] else "-",
                t["note"][:20],
            ])

        col_w = [2*cm, 4*cm, 3*cm, 2*cm, 5.5*cm, 1.5*cm, 2.2*cm, 4*cm]
        t2 = Table(rows, colWidths=col_w, repeatRows=1)
        t2.setStyle(_header_style(len(headers)))
        for i, txn in enumerate(txns, start=1):
            c = type_colors.get(txn["type"], colors.black)
            t2.setStyle(TableStyle([("TEXTCOLOR", (2, i), (2, i), c)]))
        story.append(t2)
    else:
        story.append(Paragraph("No transactions found.",
                     getSampleStyleSheet()["Normal"]))

    doc.build(story)
    buf.seek(0)
    return buf
