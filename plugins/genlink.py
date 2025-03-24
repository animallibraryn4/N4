from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler
from config import Config
import random
import string
import time
from database import save_link, get_original_link

def generate_random_string(length=8):
    """Generate a random string for the link"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def genlink(update, context):
    """Handle the /genlink command"""
    message = update.message
    
    # Check if the message is a reply to a link
    if not message.reply_to_message or not message.reply_to_message.text:
        message.reply_text("Please reply to a message containing a link with /genlink")
        return
    
    # Extract the original link
    original_link = message.reply_to_message.text
    
    # Generate a unique link ID
    link_id = generate_random_string()
    
    # Save to database
    save_link(link_id, original_link, message.from_user.id, int(time.time()) + Config.LINK_EXPIRE_TIME)
    
    # Create the generated link
    generated_link = f"https://t.me/{Config.BOT_USERNAME}?start={link_id}"
    
    # Create buttons
    keyboard = [
        [InlineKeyboardButton(Config.JOIN_BUTTON_TEXT, url=original_link)],
        [InlineKeyboardButton("Share Link", url=f"https://t.me/share/url?url={generated_link}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send the message
    message.reply_text(
        f"{Config.WELCOME_MESSAGE}\n\n{generated_link}",
        reply_markup=reply_markup
    )

def handle_start_with_link(update, context):
    """Handle when someone clicks the generated link"""
    query = update.callback_query if hasattr(update, 'callback_query') else None
    user_id = query.from_user.id if query else update.message.from_user.id
    
    # Check force subscription
    if not check_force_sub(user_id):
        channels_to_join = "\n".join([f"- {ch['channel_link']}" for ch in Config.FORCE_SUB_CHANNELS])
        update.message.reply_text(
            f"Please join these channels first:\n{channels_to_join}",
            disable_web_page_preview=True
        )
        return
    
    # Get the link ID from the start parameter
    link_id = context.args[0] if context.args else None
    
    if link_id:
        original_link = get_original_link(link_id)
        if original_link:
            keyboard = [[InlineKeyboardButton(Config.JOIN_BUTTON_TEXT, url=original_link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if query:
                query.edit_message_text(
                    f"{Config.WELCOME_MESSAGE}",
                    reply_markup=reply_markup
                )
            else:
                update.message.reply_text(
                    f"{Config.WELCOME_MESSAGE}",
                    reply_markup=reply_markup
                )
            return
    
    # If no valid link found
    if query:
        query.answer("Invalid or expired link!", show_alert=True)
    else:
        update.message.reply_text("Invalid or expired link!")

# Command handlers to register
command_handler = [
    ("genlink", False, genlink),
    ("start", False, handle_start_with_link)
]
