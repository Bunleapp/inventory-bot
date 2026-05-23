"""
handlers/products.py  ─  Add, Delete, View, Search product conversations
"""
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters,
)

from services.sheets import SheetsService
from utils.auth import require_auth
from utils.keyboards import products_menu_kb, back_main_kb, cancel_kb
from utils.formatters import fmt_product, fmt_product_list
from handlers.states import (
    ADD_NAME, ADD_PRICE, ADD_COST, ADD_QTY,
    DEL_ID, SEARCH_Q,
)

END = ConversationHandler.END


# ─────────────────────────── ADD PRODUCT ──────────────────────────────────────

@require_auth
async def cb_prod_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "➕ *Add New Product*\n━━━━━━━━━━━━━━━━━━━━\n"
        "Step 1/4 — Enter the *product name*:",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    return ADD_NAME


async def add_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["new_prod"] = {"name": update.message.text.strip()}
    await update.message.reply_text(
        "Step 2/4 — Enter the *selling price* (e.g. `12.50`):",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    return ADD_PRICE


async def add_get_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        price = float(update.message.text.strip().replace("$", ""))
        if price < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Invalid price. Enter a positive number:")
        return ADD_PRICE
    context.user_data["new_prod"]["price"] = price
    await update.message.reply_text(
        "Step 3/4 — Enter the *cost / purchase price* (e.g. `8.00`):",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    return ADD_COST


async def add_get_cost(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        cost = float(update.message.text.strip().replace("$", ""))
        if cost < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Invalid cost. Enter a positive number:")
        return ADD_COST
    context.user_data["new_prod"]["cost"] = cost
    await update.message.reply_text(
        "Step 4/4 — Enter the *initial quantity*:",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    return ADD_QTY


async def add_get_qty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        qty = int(update.message.text.strip())
        if qty < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Invalid quantity. Enter a whole number ≥ 0:")
        return ADD_QTY

    d = context.user_data["new_prod"]
    d["quantity"] = qty
    sheets: SheetsService = context.bot_data["sheets"]
    user_id = update.effective_user.id

    try:
        prod = sheets.add_product(
            d["name"], d["price"], d["cost"], qty, user_id)
        margin = ((prod["price"] - prod["cost"]) /
                  prod["price"] * 100) if prod["price"] else 0
        await update.message.reply_text(
            f"✅ *Product Added Successfully!*\n\n{fmt_product(prod)}\n"
            f"\n📈 Margin: `{margin:.1f}%`",
            parse_mode="Markdown",
            reply_markup=back_main_kb(),
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to add product: {e}",
                                        reply_markup=back_main_kb())

    context.user_data.pop("new_prod", None)
    return END


# ─────────────────────────── DELETE PRODUCT ───────────────────────────────────

@require_auth
async def cb_prod_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🗑️ *Delete Product*\n━━━━━━━━━━━━━━━━━━━━\n"
        "Enter the *Product ID* to delete (e.g. `P001`):",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    return DEL_ID


async def del_get_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pid = update.message.text.strip().upper()
    sheets: SheetsService = context.bot_data["sheets"]
    prod = sheets.find_product(pid)
    if not prod:
        await update.message.reply_text(
            f"❌ Product `{pid}` not found. Try again or /cancel:",
            parse_mode="Markdown",
        )
        return DEL_ID

    context.user_data["del_pid"] = pid
    await update.message.reply_text(
        f"⚠️ *Confirm Deletion*\n\n{fmt_product(prod)}\n\n"
        f"This action cannot be undone. Type `YES` to confirm:",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    return DEL_ID + 1  # reuse same state group — see conversation definition


async def del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text.upper() != "YES":
        await update.message.reply_text("❌ Deletion cancelled.", reply_markup=back_main_kb())
        return END

    pid = context.user_data.pop("del_pid", None)
    sheets: SheetsService = context.bot_data["sheets"]
    user_id = update.effective_user.id
    try:
        deleted = sheets.delete_product(pid, user_id)
        if deleted:
            await update.message.reply_text(
                f"✅ Product `{pid}` has been deleted.",
                parse_mode="Markdown",
                reply_markup=back_main_kb(),
            )
        else:
            await update.message.reply_text(
                f"❌ Could not delete `{pid}`. It may have already been removed.",
                parse_mode="Markdown",
                reply_markup=back_main_kb(),
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}", reply_markup=back_main_kb())
    return END


# ─────────────────────────── VIEW ALL PRODUCTS ────────────────────────────────

@require_auth
async def cb_prod_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    sheets: SheetsService = context.bot_data["sheets"]
    try:
        products = sheets.get_all_products()
        if not products:
            await query.edit_message_text(
                "📦 No products found. Add your first product!",
                reply_markup=products_menu_kb(),
            )
            return
        # Paginate: send in chunks of 10
        chunks = [products[i:i+10] for i in range(0, len(products), 10)]
        header = f"📦 *All Products* ({len(products)} total)\n━━━━━━━━━━━━━━━━━━━━\n\n"
        for idx, chunk in enumerate(chunks):
            text = (header if idx == 0 else "") + fmt_product_list(chunk)
            kb = back_main_kb() if idx == len(chunks) - 1 else None
            await query.message.reply_text(text, parse_mode="Markdown",
                                           reply_markup=kb)
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}", reply_markup=back_main_kb())


# ─────────────────────────── SEARCH ───────────────────────────────────────────

@require_auth
async def cb_prod_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔍 *Search Products*\n━━━━━━━━━━━━━━━━━━━━\n"
        "Enter a product name or ID to search:",
        parse_mode="Markdown",
        reply_markup=cancel_kb(),
    )
    return SEARCH_Q


async def search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.message.text.strip()
    sheets: SheetsService = context.bot_data["sheets"]
    try:
        results = sheets.search_products(q)
        if not results:
            await update.message.reply_text(
                f"🔍 No products matched *\"{q}\"*.",
                parse_mode="Markdown",
                reply_markup=back_main_kb(),
            )
        else:
            text = (
                f"🔍 *Search Results for \"{q}\"* ({len(results)} found)\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                + fmt_product_list(results)
            )
            await update.message.reply_text(
                text, parse_mode="Markdown", reply_markup=back_main_kb()
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}", reply_markup=back_main_kb())
    return END


# ─────────────────────────── CANCEL ───────────────────────────────────────────

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            "❌ Operation cancelled.",
            reply_markup=back_main_kb(),
        )
    else:
        await update.message.reply_text("❌ Operation cancelled.",
                                        reply_markup=back_main_kb())
    context.user_data.clear()
    return END


# ─────────────────────────── CONVERSATION HANDLERS ───────────────────────────

DEL_CONFIRM = DEL_ID + 1   # second state for delete confirmation

ADD_PRODUCT_CONV = ConversationHandler(
    entry_points=[CallbackQueryHandler(cb_prod_add, pattern="^prod_add$")],
    states={
        ADD_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, add_get_name)],
        ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_get_price)],
        ADD_COST:  [MessageHandler(filters.TEXT & ~filters.COMMAND, add_get_cost)],
        ADD_QTY:   [MessageHandler(filters.TEXT & ~filters.COMMAND, add_get_qty)],
    },
    fallbacks=[
        CallbackQueryHandler(cancel, pattern="^cancel$"),
        CommandHandler("cancel", cancel),
    ],
)

DELETE_PRODUCT_CONV = ConversationHandler(
    entry_points=[CallbackQueryHandler(
        cb_prod_delete, pattern="^prod_delete$")],
    states={
        DEL_ID:      [MessageHandler(filters.TEXT & ~filters.COMMAND, del_get_id)],
        DEL_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, del_confirm)],
    },
    fallbacks=[
        CallbackQueryHandler(cancel, pattern="^cancel$"),
        CommandHandler("cancel", cancel),
    ],
)

SEARCH_CONV = ConversationHandler(
    entry_points=[CallbackQueryHandler(
        cb_prod_search, pattern="^prod_search$")],
    states={
        SEARCH_Q: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_query)],
    },
    fallbacks=[
        CallbackQueryHandler(cancel, pattern="^cancel$"),
        CommandHandler("cancel", cancel),
    ],
)
