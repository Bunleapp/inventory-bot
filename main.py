"""
main.py  ─  Telegram Inventory Management Bot  ·  Entry Point
"""
from handlers import (
    cmd_start, cmd_help, cmd_dashboard, cmd_low_stock, cmd_history,
    cb_main_menu,
    ADD_PRODUCT_CONV, DELETE_PRODUCT_CONV, SEARCH_CONV, cb_prod_view,
    STOCK_IN_CONV, STOCK_OUT_CONV, SALE_CONV,
    cb_export,
    setup_scheduler,
)
from services.sheets import SheetsService
import config.settings as cfg
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
)
from telegram import Update
import sys
import logging
logging.getLogger("telegram.ext").setLevel(logging.ERROR)


# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def main() -> None:
    # ── Validate config ────────────────────────────────────────────────────────
    try:
        cfg.validate()
    except EnvironmentError as e:
        logger.critical(str(e))
        sys.exit(1)

    # ── Initialise Google Sheets service ──────────────────────────────────────
    logger.info("Connecting to Google Sheets…")
    try:
        sheets = SheetsService()
        logger.info("Google Sheets connected ✓")
    except Exception as e:
        logger.critical(f"Failed to connect to Google Sheets: {e}")
        sys.exit(1)

    # ── Build Application ──────────────────────────────────────────────────────
    app = (
        Application.builder()
        .token(cfg.BOT_TOKEN)
        .build()
    )
    app.bot_data["sheets"] = sheets

    # ── Register Conversation Handlers (must be first) ─────────────────────────
    app.add_handler(ADD_PRODUCT_CONV)
    app.add_handler(DELETE_PRODUCT_CONV)
    app.add_handler(SEARCH_CONV)
    app.add_handler(STOCK_IN_CONV)
    app.add_handler(STOCK_OUT_CONV)
    app.add_handler(SALE_CONV)

    # ── Register Command Handlers ──────────────────────────────────────────────
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("help",      cmd_help))
    app.add_handler(CommandHandler("dashboard", cmd_dashboard))
    app.add_handler(CommandHandler("lowstock",  cmd_low_stock))
    app.add_handler(CommandHandler("history",   cmd_history))

    # ── Register Callback Handlers ─────────────────────────────────────────────
    # Products: view (no conversation needed)
    app.add_handler(CallbackQueryHandler(cb_prod_view,  pattern="^prod_view$"))

    # Export
    app.add_handler(CallbackQueryHandler(
        cb_export,
        pattern="^export_(prod|txn)_(csv|pdf)$",
    ))

    # Main-menu routing (dashboard, history, low_stock, products sub-menu, back)
    app.add_handler(CallbackQueryHandler(
        cb_main_menu,
        pattern="^(back_main|menu_dashboard|menu_products|menu_history|menu_low_stock|menu_export)$",
    ))

    # ── Start Scheduler ────────────────────────────────────────────────────────
    scheduler = setup_scheduler(app)
    scheduler.start()
    logger.info(
        f"Low-stock scheduler started (every {cfg.LOW_STOCK_CHECK_INTERVAL} min)"
    )

    # ── Run Bot ────────────────────────────────────────────────────────────────
    logger.info("Bot is running… Press Ctrl+C to stop.")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

    scheduler.shutdown()
    logger.info("Bot stopped.")


if __name__ == "__main__":
    main()
