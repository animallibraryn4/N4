from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from config import Config
from database import get_channels, add_channel, remove_channel
import logging

logger = logging.getLogger(__name__)

async def manage_channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show channel management interface"""
    user_id = update.message.from_user.id
    
    # Check if user is admin
    if user_id not in Config.ADMINS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    channels = get_channels()
    keyboard = []
    
    # Add buttons for each channel
    for channel in channels:
        keyboard.append([
            InlineKeyboardButton(
                f"❌ Remove {channel['channel_link']}", 
                callback_data=f"remove_{channel['channel_id']}"
            )
        ])
    
    # Add button to add new channel
    keyboard.append([
        InlineKeyboardButton("➕ Add New Channel", callback_data="add_channel")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📢 <b>Force Subscribe Channel Manager</b>\n\n"
        "Current channels (click to remove):",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def handle_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle channel management callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("remove_"):
        channel_id = int(data.split("_")[1])
        remove_channel(channel_id)
        await query.edit_message_text("✅ Channel removed successfully!")
        await manage_channels(update, context)  # Refresh the interface
        
    elif data == "add_channel":
        await query.edit_message_text(
            "🔗 <b>Add New Force-Sub Channel</b>\n\n"
            "Send command in this format:\n"
            "<code>/addchannel channel_id channel_link</code>\n\n"
            "Example:\n"
            "<code>/addchannel -10012345678 https://t.me/your_channel</code>",
            parse_mode="HTML"
        )

async def add_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /addchannel command"""
    user_id = update.message.from_user.id
    
    # Check if user is admin
    if user_id not in Config.ADMINS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ <b>Usage:</b>\n"
            "<code>/addchannel channel_id channel_link</code>\n\n"
            "Example:\n"
            "<code>/addchannel -10012345678 https://t.me/your_channel</code>",
            parse_mode="HTML"
        )
        return
    
    channel_id = context.args[0]
    channel_link = context.args[1]
    
    try:
        channel_id = int(channel_id)
        if channel_id > 0:  # Channel IDs should be negative
            channel_id = -channel_id
    except ValueError:
        await update.message.reply_text("❌ Channel ID must be a number")
        return
    
    # Validate link format
    if not channel_link.startswith(("https://t.me/", "t.me/")):
        await update.message.reply_text("❌ Channel link must start with https://t.me/")
        return
    
    add_channel(channel_id, channel_link)
    await update.message.reply_text(
        f"✅ Channel added successfully!\n\n"
        f"<b>ID:</b> <code>{channel_id}</code>\n"
        f"<b>Link:</b> {channel_link}",
        parse_mode="HTML"
    )

# Command handlers to register
command_handler = [
    ("channels", False, manage_channels),
    ("addchannel", False, add_channel_command),
    (None, True, handle_channel_callback)  # Callback handler
]
