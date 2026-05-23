"""
handlers/export_handler.py  ─  Export CSV / PDF reports
"""
import io
from datetime import datetime

import pytz
from telegram import Update
from telegram.ext import ContextTypes

from config.settings import TIMEZONE
from services.sheets import SheetsService
from services.export import (
    export_products_csv,
    export_transactions_csv,
    export_inventory_pdf,
    export_transactions_pdf,
)
from utils.auth import require_auth
from utils.keyboards import export_menu_kb, back_main_kb


def _ts() -> str:
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz).strftime("%Y%m%d_%H%M")


@require_auth
async def cb_export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    sheets: SheetsService = context.bot_data["sheets"]

    await query.edit_message_text("⏳ Generating export, please wait…")

    try:
        ts = _ts()

        if data == "export_prod_csv":
            buf = export_products_csv(sheets)
            await query.message.reply_document(
                document=buf,
                filename=f"inventory_products_{ts}.csv",
                caption="📄 *Products Export (CSV)*",
                parse_mode="Markdown",
            )

        elif data == "export_txn_csv":
            buf = export_transactions_csv(sheets)
            await query.message.reply_document(
                document=buf,
                filename=f"inventory_transactions_{ts}.csv",
                caption="📑 *Transactions Export (CSV)*",
                parse_mode="Markdown",
            )

        elif data == "export_prod_pdf":
            buf = export_inventory_pdf(sheets)
            await query.message.reply_document(
                document=buf,
                filename=f"inventory_report_{ts}.pdf",
                caption="📄 *Inventory Report (PDF)*",
                parse_mode="Markdown",
            )

        elif data == "export_txn_pdf":
            buf = export_transactions_pdf(sheets)
            await query.message.reply_document(
                document=buf,
                filename=f"transactions_report_{ts}.pdf",
                caption="📑 *Transaction History (PDF)*",
                parse_mode="Markdown",
            )

        await query.message.reply_text(
            "✅ Export complete! Choose another:",
            reply_markup=export_menu_kb(),
        )

    except Exception as e:
        await query.message.reply_text(
            f"❌ Export failed: {e}",
            reply_markup=back_main_kb(),
        )
