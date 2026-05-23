"""
utils/formatters.py  ─  Message formatting helpers
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

TYPE_EMOJI = {
    "STOCK_IN":       "📥",
    "STOCK_OUT":      "📤",
    "SALE":           "🛒",
    "ADD_PRODUCT":    "➕",
    "DELETE_PRODUCT": "🗑️",
}


def fmt_product(p: dict, show_value: bool = False) -> str:
    qty_icon = "⚠️" if p["quantity"] <= 10 else "✅"
    margin = ((p["price"] - p["cost"]) / p["price"] * 100) if p["price"] else 0
    lines = [
        f"*{p['name']}*  `[{p['id']}]`",
        f"  💰 Price: `${p['price']:.2f}`  |  Cost: `${p['cost']:.2f}`  |  Margin: `{margin:.1f}%`",
        f"  {qty_icon} Qty in Stock: `{p['quantity']}`",
    ]
    if show_value:
        lines.append(f"  📦 Stock Value: `${p['quantity'] * p['price']:.2f}`")
    if p.get("added"):
        lines.append(f"  🗓 Added: `{p['added']}`")
    return "\n".join(lines)


def fmt_product_list(products: list[dict]) -> str:
    if not products:
        return "No products found."
    chunks = []
    for p in products:
        qty_icon = "⚠️" if p["quantity"] <= 10 else "✅"
        chunks.append(
            f"{qty_icon} `{p['id']}` *{p['name']}*\n"
            f"   Price: `${p['price']:.2f}` | Qty: `{p['quantity']}`"
        )
    return "\n\n".join(chunks)


def fmt_transaction(t: dict) -> str:
    emoji = TYPE_EMOJI.get(t["type"], "📌")
    price = f"${float(t['price']):.2f}" if t["price"] else "—"
    return (
        f"{emoji} `{t['id']}` · *{t['type']}*\n"
        f"   {t['date']}\n"
        f"   {t['product']} `[{t['prod_id']}]`\n"
        f"   Qty: `{t['qty']}` | Price: `{price}`\n"
        f"   Note: {t['note']}"
    )


def fmt_summary(s: dict) -> str:
    low_count = len(s["low_stock"])
    low_icon = "⚠️" if low_count else "✅"
    return (
        "📊 *Inventory Dashboard*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Total Products:   `{s['total_products']}`\n"
        f"🔢 Total Units:      `{s['total_qty']:,}`\n"
        f"💵 Stock Value:      `${s['total_value']:,.2f}`\n"
        f"🧾 Cost Value:       `${s['total_cost']:,.2f}`\n"
        f"📈 Est. Profit:      `${s['gross_profit']:,.2f}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📥 Recent Stock-In:  `{s['recent_in']} units`\n"
        f"📤 Recent Stock-Out: `{s['recent_out']} units`\n"
        f"🛒 Recent Sales:     `${s['recent_sales']:,.2f}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{low_icon} Low Stock Items:  `{low_count}`"
    )


def fmt_low_stock(products: list[dict]) -> str:
    if not products:
        return "✅ *All products are sufficiently stocked!*"
    lines = ["⚠️ *Low Stock Alert*\n━━━━━━━━━━━━━━━━━━━━"]
    for p in products:
        lines.append(
            f"• `{p['id']}` *{p['name']}*  —  only `{p['quantity']}` left!"
        )
    return "\n".join(lines)
