from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database.crud import get_channel, create_channel
from utils.decorators import admin_only
from utils.helpers import get_channel_info
from templates.messages import CHANNEL_ADDED_MSG

@admin_only
def add_channel(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text("Please forward a message from the channel you want to add")
    context.user_data['awaiting_channel'] = True

def handle_channel_forward(update: Update, context: CallbackContext, db: Session):
    if not context.user_data.get('awaiting_channel'):
        return
    
    channel_info = get_channel_info(update)
    if not channel_info:
        update.message.reply_text("Invalid channel. Please try again.")
        return
    
    if get_channel(db, channel_info['channel_id']):
        update.message.reply_text("Channel already exists in database.")
        return
    
    create_channel(db, channel_info)
    update.message.reply_text(CHANNEL_ADDED_MSG.format(name=channel_info['name']))
    context.user_data.pop('awaiting_channel', None)
