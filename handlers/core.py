"""
handlers/core.py  ─  /start, /help, main menu callbacks, dashboard, history
"""
from telegram import Update
from telegram.ext import ContextTypes

from services.sheets import SheetsService
from utils.auth import require_auth
from utils.keyboards import main_menu_kb, products_menu_kb, export_menu_kb, back_main_kb
from utils.formatters import fmt_summary, fmt_transaction, fmt_low_stock


async def _send_main_menu(msg, text: str) -> None:
    await msg.reply_text(text, parse_mode="Markdown", reply_markup=main_menu_kb())


# ── /start ────────────────────────────────────────────────────────────────────

@require_auth
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = (
        f"👋 Welcome back, *{user.first_name}*!\n\n"
        f"🏪 *Inventory Management Bot*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Manage your stock, track transactions,\n"
        f"and get instant alerts — all in Telegram.\n\n"
        f"Use the menu below to get started:"
    )
    await _send_main_menu(update.message, text)


# ── /help ─────────────────────────────────────────────────────────────────────

@require_auth
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📖 *Help & Commands*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "/start — Main menu\n"
        "/dashboard — Inventory overview\n"
        "/lowstock — Low stock alert list\n"
        "/history — Recent transactions\n"
        "/help — This help message\n\n"
        "You can also use the inline buttons for all operations."
    )
    await update.message.reply_text(text, parse_mode="Markdown",
                                    reply_markup=back_main_kb())


# ── /dashboard ───────────────────────────────────────────────────────────────

@require_auth
async def cmd_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("typing")
    sheets: SheetsService = context.bot_data["sheets"]
    msg = update.effective_message
    await msg.reply_text("⏳ Loading dashboard…")
    try:
        summary = sheets.get_summary()
        await msg.reply_text(
            fmt_summary(summary),
            parse_mode="Markdown",
            reply_markup=back_main_kb(),
        )
    except Exception as e:
        await msg.reply_text(f"❌ Error: {e}", reply_markup=back_main_kb())


# ── /lowstock ────────────────────────────────────────────────────────────────

@require_auth
async def cmd_low_stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sheets: SheetsService = context.bot_data["sheets"]
    msg = update.effective_message
    try:
        low = sheets.get_low_stock_products()
        await msg.reply_text(
            fmt_low_stock(low),
            parse_mode="Markdown",
            reply_markup=back_main_kb(),
        )
    except Exception as e:
        await msg.reply_text(f"❌ Error: {e}")


# ── /history ─────────────────────────────────────────────────────────────────

@require_auth
async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("typing")
    sheets: SheetsService = context.bot_data["sheets"]
    msg = update.effective_message
    try:
        txns = sheets.get_transactions(15)
        if not txns:
            await msg.reply_text("📋 No transactions yet.", reply_markup=back_main_kb())
            return
        lines = ["📋 *Recent Transactions* (last 15)\n━━━━━━━━━━━━━━━━━━━━"]
        for t in txns:
            lines.append(fmt_transaction(t))
        await msg.reply_text(
            "\n\n".join(lines),
            parse_mode="Markdown",
            reply_markup=back_main_kb(),
        )
    except Exception as e:
        await msg.reply_text(f"❌ Error: {e}")


# ── Callback: main menu routing ───────────────────────────────────────────────

async def cb_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("loading...")
    data = query.data
    sheets: SheetsService = context.bot_data["sheets"]

    async def safe_edit(text, reply_markup=None):
        try:
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=reply_markup,
            )
        except Exception:
            pass  # Ignore "message not modified" and similar errors

    if data == "back_main":
        await safe_edit(
            "🏪 *Inventory Management Bot*\nChoose an action:",
            reply_markup=main_menu_kb(),
        )

    elif data == "menu_dashboard":
        await query.answer("Loading dashboard...")
        try:
            summary = sheets.get_summary()
            await safe_edit(fmt_summary(summary), reply_markup=back_main_kb())
        except Exception as e:
            await safe_edit(f"❌ Error: {e}", reply_markup=back_main_kb())

    elif data == "menu_products":
        await safe_edit(
            "📦 *Product Management*\nWhat would you like to do?",
            reply_markup=products_menu_kb(),
        )

    elif data == "menu_history":
        try:
            txns = sheets.get_transactions(15)
            if not txns:
                text = "📋 No transactions yet."
            else:
                lines = [
                    "📋 *Recent Transactions* (last 15)\n━━━━━━━━━━━━━━━━━━━━"]
                for t in txns:
                    lines.append(fmt_transaction(t))
                text = "\n\n".join(lines)
            await safe_edit(text, reply_markup=back_main_kb())
        except Exception as e:
            await safe_edit(f"❌ {e}", reply_markup=back_main_kb())

    elif data == "menu_low_stock":
        try:
            low = sheets.get_low_stock_products()
            await safe_edit(fmt_low_stock(low), reply_markup=back_main_kb())
        except Exception as e:
            await safe_edit(f"❌ {e}", reply_markup=back_main_kb())

    elif data == "menu_export":
        await safe_edit(
            "📂 *Export Reports*\nChoose format:",
            reply_markup=export_menu_kb(),
        )
