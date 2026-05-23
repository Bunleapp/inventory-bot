"""
handlers/stock.py  ─  Stock-In, Stock-Out, Sale conversation handlers
"""
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters,
)

from services.sheets import SheetsService
from utils.auth import require_auth
from utils.keyboards import back_main_kb, cancel_kb
from utils.formatters import fmt_product
from handlers.states import SIN_ID, SIN_QTY, SIN_NOTE, SOUT_ID, SOUT_QTY, SOUT_NOTE, SALE_ID, SALE_QTY, SALE_NOTE

END = ConversationHandler.END


# ─── Shared cancel ────────────────────────────────────────────────────────────

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("❌ Operation cancelled.", reply_markup=back_main_kb())
    else:
        await update.message.reply_text("❌ Operation cancelled.", reply_markup=back_main_kb())
    context.user_data.clear()
    return END


# ─────────────────────────── STOCK IN ─────────────────────────────────────────

@require_auth
async def cb_stock_in(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📥 *Stock In*\n━━━━━━━━━━━━━━━━━━━━\n"
        "Enter the *Product ID* (e.g. `P001`):",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    return SIN_ID


async def sin_get_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pid = update.message.text.strip().upper()
    sheets: SheetsService = context.bot_data["sheets"]
    prod = sheets.find_product(pid)
    if not prod:
        await update.message.reply_text(
            f"❌ Product `{pid}` not found. Try again:",
            parse_mode="Markdown",
            reply_markup=cancel_kb(),
        )
        return SIN_ID
    context.user_data["sin_pid"] = pid
    await update.message.reply_text(
        f"✅ Found: *{prod['name']}*\nCurrent Qty: `{prod['quantity']}`\n\n"
        f"Enter the *quantity to add*:",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    return SIN_QTY


async def sin_get_qty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        qty = int(update.message.text.strip())
        if qty <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Please enter a positive whole number:")
        return SIN_QTY
    context.user_data["sin_qty"] = qty
    await update.message.reply_text(
        "Add an optional *note* (e.g. `Supplier delivery #123`), or type `skip`:",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    return SIN_NOTE


async def sin_get_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    note = update.message.text.strip()
    if note.lower() == "skip":
        note = "Stock In"
    pid = context.user_data.pop("sin_pid")
    qty = context.user_data.pop("sin_qty")
    sheets: SheetsService = context.bot_data["sheets"]
    user_id = update.effective_user.id
    try:
        result = sheets.stock_in(pid, qty, note, user_id)
        await update.message.reply_text(
            f"✅ *Stock In Recorded!*\n\n"
            f"🏷 Product: *{result['name']}*  `[{result['id']}]`\n"
            f"📥 Added: `+{qty} units`\n"
            f"📦 New Qty: `{result['new_qty']}`\n"
            f"🔖 Txn ID: `{result['txn_id']}`\n"
            f"📝 Note: {note}",
            parse_mode="Markdown",
            reply_markup=back_main_kb(),
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}", reply_markup=back_main_kb())
    return END


# ─────────────────────────── STOCK OUT ────────────────────────────────────────

@require_auth
async def cb_stock_out(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["sout_type"] = "STOCK_OUT"
    await query.edit_message_text(
        "📤 *Stock Out*\n━━━━━━━━━━━━━━━━━━━━\n"
        "Enter the *Product ID* (e.g. `P001`):",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    return SOUT_ID


async def sout_get_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pid = update.message.text.strip().upper()
    sheets: SheetsService = context.bot_data["sheets"]
    prod = sheets.find_product(pid)
    if not prod:
        await update.message.reply_text(
            f"❌ Product `{pid}` not found. Try again:",
            parse_mode="Markdown",
            reply_markup=cancel_kb(),
        )
        return SOUT_ID
    context.user_data["sout_pid"] = pid
    await update.message.reply_text(
        f"✅ Found: *{prod['name']}*\nCurrent Qty: `{prod['quantity']}`\n\n"
        f"Enter the *quantity to remove*:",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    return SOUT_QTY


async def sout_get_qty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        qty = int(update.message.text.strip())
        if qty <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Please enter a positive whole number:")
        return SOUT_QTY
    pid = context.user_data["sout_pid"]
    sheets: SheetsService = context.bot_data["sheets"]
    prod = sheets.find_product(pid)
    if prod and qty > prod["quantity"]:
        await update.message.reply_text(
            f"⚠️ *Insufficient stock!*\n"
            f"Available: `{prod['quantity']}` | Requested: `{qty}`\n"
            f"Enter a smaller quantity:",
            parse_mode="Markdown",
        )
        return SOUT_QTY
    context.user_data["sout_qty"] = qty
    await update.message.reply_text(
        "Add an optional *note*, or type `skip`:",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    return SOUT_NOTE


async def sout_get_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    note = update.message.text.strip()
    if note.lower() == "skip":
        note = "Stock Out"
    pid = context.user_data.pop("sout_pid")
    qty = context.user_data.pop("sout_qty")
    sheets: SheetsService = context.bot_data["sheets"]
    user_id = update.effective_user.id
    try:
        result = sheets.stock_out(pid, qty, note, user_id)
        await update.message.reply_text(
            f"✅ *Stock Out Recorded!*\n\n"
            f"🏷 Product: *{result['name']}*  `[{result['id']}]`\n"
            f"📤 Removed: `-{qty} units`\n"
            f"📦 New Qty: `{result['new_qty']}`\n"
            f"🔖 Txn ID: `{result['txn_id']}`\n"
            f"📝 Note: {note}",
            parse_mode="Markdown",
            reply_markup=back_main_kb(),
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}", reply_markup=back_main_kb())
    return END


# ─────────────────────────── SALE ─────────────────────────────────────────────

@require_auth
async def cb_sale(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🛒 *Record Sale*\n━━━━━━━━━━━━━━━━━━━━\n"
        "Enter the *Product ID* (e.g. `P001`):",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    return SALE_ID


async def sale_get_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pid = update.message.text.strip().upper()
    sheets: SheetsService = context.bot_data["sheets"]
    prod = sheets.find_product(pid)
    if not prod:
        await update.message.reply_text(
            f"❌ Product `{pid}` not found. Try again:",
            parse_mode="Markdown",
            reply_markup=cancel_kb(),
        )
        return SALE_ID
    context.user_data["sale_pid"] = pid
    await update.message.reply_text(
        f"✅ Found: *{prod['name']}*\n"
        f"Selling Price: `${prod['price']:.2f}` | Stock: `{prod['quantity']}`\n\n"
        f"Enter the *quantity sold*:",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    return SALE_QTY


async def sale_get_qty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        qty = int(update.message.text.strip())
        if qty <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Please enter a positive whole number:")
        return SALE_QTY
    pid = context.user_data["sale_pid"]
    sheets: SheetsService = context.bot_data["sheets"]
    prod = sheets.find_product(pid)
    if prod and qty > prod["quantity"]:
        await update.message.reply_text(
            f"⚠️ *Insufficient stock!*\n"
            f"Available: `{prod['quantity']}` | Requested: `{qty}`\n"
            f"Enter a smaller quantity:",
            parse_mode="Markdown",
        )
        return SALE_QTY
    context.user_data["sale_qty"] = qty
    await update.message.reply_text(
        "Add a *customer / note* (optional), or type `skip`:",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    return SALE_NOTE


async def sale_get_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    note = update.message.text.strip()
    if note.lower() == "skip":
        note = "Sale"
    pid = context.user_data.pop("sale_pid")
    qty = context.user_data.pop("sale_qty")
    sheets: SheetsService = context.bot_data["sheets"]
    user_id = update.effective_user.id
    try:
        result = sheets.sale(pid, qty, note, user_id)
        revenue = result["total"]
        profit = qty * (result["price"] - result["cost"])
        await update.message.reply_text(
            f"✅ *Sale Recorded!*\n\n"
            f"🏷 Product: *{result['name']}*  `[{result['id']}]`\n"
            f"🛒 Sold: `{qty} units` @ `${result['price']:.2f}`\n"
            f"💵 Revenue: `${revenue:.2f}`\n"
            f"📈 Gross Profit: `${profit:.2f}`\n"
            f"📦 Remaining Qty: `{result['new_qty']}`\n"
            f"🔖 Txn ID: `{result['txn_id']}`\n"
            f"📝 Note: {note}",
            parse_mode="Markdown",
            reply_markup=back_main_kb(),
        )
        # ── Low stock warning after sale ──────────────────────────────────────
        if result["new_qty"] <= 10:
            await update.message.reply_text(
                f"⚠️ *Low Stock Warning!*\n"
                f"*{result['name']}* now has only `{result['new_qty']}` units left.\n"
                f"Consider restocking soon.",
                parse_mode="Markdown",
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}", reply_markup=back_main_kb())
    return END


# ─────────────────────────── CONVERSATION HANDLERS ───────────────────────────

STOCK_IN_CONV = ConversationHandler(
    entry_points=[CallbackQueryHandler(
        cb_stock_in, pattern="^menu_stock_in$")],
    states={
        SIN_ID:   [MessageHandler(filters.TEXT & ~filters.COMMAND, sin_get_id)],
        SIN_QTY:  [MessageHandler(filters.TEXT & ~filters.COMMAND, sin_get_qty)],
        SIN_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sin_get_note)],
    },
    fallbacks=[
        CallbackQueryHandler(cancel, pattern="^cancel$"),
        CommandHandler("cancel", cancel),
    ],
)

STOCK_OUT_CONV = ConversationHandler(
    entry_points=[CallbackQueryHandler(
        cb_stock_out, pattern="^menu_stock_out$")],
    states={
        SOUT_ID:   [MessageHandler(filters.TEXT & ~filters.COMMAND, sout_get_id)],
        SOUT_QTY:  [MessageHandler(filters.TEXT & ~filters.COMMAND, sout_get_qty)],
        SOUT_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sout_get_note)],
    },
    fallbacks=[
        CallbackQueryHandler(cancel, pattern="^cancel$"),
        CommandHandler("cancel", cancel),
    ],
)

SALE_CONV = ConversationHandler(
    entry_points=[CallbackQueryHandler(cb_sale, pattern="^menu_sale$")],
    states={
        SALE_ID:   [MessageHandler(filters.TEXT & ~filters.COMMAND, sale_get_id)],
        SALE_QTY:  [MessageHandler(filters.TEXT & ~filters.COMMAND, sale_get_qty)],
        SALE_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sale_get_note)],
    },
    fallbacks=[
        CallbackQueryHandler(cancel, pattern="^cancel$"),
        CommandHandler("cancel", cancel),
    ],
)
