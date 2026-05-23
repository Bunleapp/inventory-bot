"""
handlers/scheduler.py  ─  Periodic low-stock alert notifications
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import Application

from config.settings import ALLOWED_USER_IDS, LOW_STOCK_THRESHOLD, LOW_STOCK_CHECK_INTERVAL, TIMEZONE
from services.sheets import SheetsService
from utils.formatters import fmt_low_stock

logger = logging.getLogger(__name__)


async def _send_low_stock_alerts(app: Application) -> None:
    sheets: SheetsService = app.bot_data.get("sheets")
    if not sheets:
        return
    try:
        low = sheets.get_low_stock_products(LOW_STOCK_THRESHOLD)
        if not low:
            return
        text = (
            "🔔 *Scheduled Low Stock Alert*\n"
            f"(Threshold: ≤ {LOW_STOCK_THRESHOLD} units)\n\n"
            + fmt_low_stock(low)
        )
        for uid in ALLOWED_USER_IDS:
            try:
                await app.bot.send_message(chat_id=uid, text=text, parse_mode="Markdown")
            except Exception as e:
                logger.warning(f"Could not notify user {uid}: {e}")
    except Exception as e:
        logger.error(f"Low-stock scheduler error: {e}")


def setup_scheduler(app: Application) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        _send_low_stock_alerts,
        trigger="interval",
        minutes=LOW_STOCK_CHECK_INTERVAL,
        args=[app],
        id="low_stock_alert",
        replace_existing=True,
    )
    return scheduler
