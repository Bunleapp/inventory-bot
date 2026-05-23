"""
utils/auth.py  ─  Telegram user authentication middleware
"""
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from config.settings import ALLOWED_USER_IDS


def require_auth(func):
    """Decorator: blocks any user not in ALLOWED_USER_IDS."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not user or user.id not in ALLOWED_USER_IDS:
            name = user.first_name if user else "Unknown"
            uid = user.id if user else "?"
            await update.effective_message.reply_text(
                f"🚫 *Access Denied*\n\n"
                f"Hello {name}, you are not authorised to use this bot.\n"
                f"Your Telegram ID: `{uid}`\n\n"
                f"Ask the administrator to add your ID to the allowed list.",
                parse_mode="Markdown",
            )
            return
        return await func(update, context)
    return wrapper
