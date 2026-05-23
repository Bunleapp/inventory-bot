"""
utils/keyboards.py  ─  All InlineKeyboardMarkup builders
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# ─────────────────────── main menu ────────────────────────────────────────────

def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📦 Products",     callback_data="menu_products"),
            InlineKeyboardButton(
                "📊 Dashboard",    callback_data="menu_dashboard"),
        ],
        [
            InlineKeyboardButton(
                "📥 Stock In",     callback_data="menu_stock_in"),
            InlineKeyboardButton(
                "📤 Stock Out",    callback_data="menu_stock_out"),
        ],
        [
            InlineKeyboardButton("🛒 Record Sale",  callback_data="menu_sale"),
            InlineKeyboardButton(
                "📋 History",      callback_data="menu_history"),
        ],
        [
            InlineKeyboardButton(
                "⚠️  Low Stock",   callback_data="menu_low_stock"),
            InlineKeyboardButton(
                "📂 Export",       callback_data="menu_export"),
        ],
    ])


# ─────────────────────── sub-menus ────────────────────────────────────────────

def products_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add Product",    callback_data="prod_add"),
            InlineKeyboardButton("🗑️ Delete Product",
                                 callback_data="prod_delete"),
        ],
        [
            InlineKeyboardButton(
                "📃 View All",       callback_data="prod_view"),
            InlineKeyboardButton(
                "🔍 Search",         callback_data="prod_search"),
        ],
        [InlineKeyboardButton(
            "🔙 Back",              callback_data="back_main")],
    ])


def export_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📄 Products CSV",
                                 callback_data="export_prod_csv"),
            InlineKeyboardButton("📄 Products PDF",
                                 callback_data="export_prod_pdf"),
        ],
        [
            InlineKeyboardButton("📑 Transactions CSV",
                                 callback_data="export_txn_csv"),
            InlineKeyboardButton("📑 Transactions PDF",
                                 callback_data="export_txn_pdf"),
        ],
        [InlineKeyboardButton(
            "🔙 Back",                 callback_data="back_main")],
    ])


def back_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Main Menu",
                              callback_data="back_main")]
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ])


def confirm_kb(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Confirm", callback_data=f"confirm_{action}"),
            InlineKeyboardButton("❌ Cancel",  callback_data="cancel"),
        ]
    ])
