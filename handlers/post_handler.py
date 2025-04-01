from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database.crud import get_post, create_post
from utils.decorators import admin_only
from templates.messages import POST_CREATION_START_MSG

@admin_only
def create_post(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text(POST_CREATION_START_MSG)
    context.user_data['post_creation'] = {'step': 1}

def handle_post_content(update: Update, context: CallbackContext, db: Session):
    if not context.user_data.get('post_creation'):
        return
    
    step = context.user_data['post_creation']['step']
    
    if step == 1:  # Waiting for channel selection
        handle_channel_selection(update, context)
    elif step == 2:  # Waiting for post content
        handle_post_text(update, context)
    elif step == 3:  # Waiting for media
        handle_post_media(update, context)
    elif step == 4:  # Waiting for buttons
        handle_post_buttons(update, context, db)
