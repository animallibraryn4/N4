from functools import wraps
from config import Config
from telegram import Update
from telegram.ext import CallbackContext

def admin_only(func):
    @wraps(func)
    def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in Config.ADMIN_IDS:
            update.message.reply_text("You are not authorized to use this command.")
            return
        return func(update, context, *args, **kwargs)
    return wrapped
