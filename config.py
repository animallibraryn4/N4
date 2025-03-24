from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler
from config import Config
from database import get_channels, add_channel, remove_channel
import os

class Config:
    # Bot Token from @BotFather (PTB)
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    # Bot Username
    BOT_USERNAME = os.getenv("BOT_USERNAME", "")
    
    # Telegram API ID and Hash (for Telethon)
    API_ID = int(os.getenv("API_ID", 12345))
    API_HASH = os.getenv("API_HASH", "0123456789abcdef0123456789abcdef")
    
    # Admin IDs
    ADMINS = [int(admin) if admin.isdigit() else admin for admin in os.getenv('ADMINS', '').split(',')]
    
    # Database URI
    DB_URI = os.getenv("DB_URI", "")
    
    # Other configurations...
def manage_channels(update, context):
    """Show channel management interface"""
    user_id = update.message.from_user.id
    
    # Check if user is admin
    if user_id not in Config.ADMINS:
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    channels = get_channels()
    keyboard = []
    
    # Add buttons for each channel
    for channel in channels:
        keyboard.append([
            InlineKeyboardButton(f"Remove {channel['channel_link']}", 
                               callback_data=f"remove_{channel['channel_id']}")
        ])
    
    # Add button to add new channel
    keyboard.append([InlineKeyboardButton("Add New Channel", callback_data="add_channel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "Manage Force Subscribe Channels:",
        reply_markup=reply_markup
    )

def handle_channel_callback(update, context):
    """Handle channel management callbacks"""
    query = update.callback_query
    data = query.data
    
    if data.startswith("remove_"):
        channel_id = int(data.split("_")[1])
        remove_channel(channel_id)
        query.answer("Channel removed successfully!")
        manage_channels(update, context)  # Refresh the interface
    elif data == "add_channel":
        query.message.reply_text("Please send the channel ID and link in format:\n/addchannel channel_id channel_link")
    
    query.answer()

def add_channel_command(update, context):
    """Handle the /addchannel command"""
    user_id = update.message.from_user.id
    
    # Check if user is admin
    if user_id not in Config.ADMINS:
        update.message.reply_text("You are not authorized to use this command.")
        return
    
    if len(context.args) < 2:
        update.message.reply_text("Usage: /addchannel channel_id channel_link")
        return
    
    channel_id = context.args[0]
    channel_link = context.args[1]
    
    try:
        channel_id = int(channel_id)
    except ValueError:
        update.message.reply_text("Channel ID must be a number")
        return
    
    add_channel(channel_id, channel_link)
    update.message.reply_text("Channel added successfully!")

# Command handlers to register
command_handler = [
    ("channels", False, manage_channels),
    ("addchannel", False, add_channel_command),
    (None, True, handle_channel_callback)  # Callback handler
]
