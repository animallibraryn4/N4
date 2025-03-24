from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from config import config
from database import db
import logging

logger = logging.getLogger(__name__)

async def manage_channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in config.ADMINS:
        await update.message.reply_text("❌ Unauthorized!")
        return
    
    channels = db.get_channels()
    keyboard = [
        [InlineKeyboardButton(f"❌ {ch['channel_link']}", callback_data=f"remove_{ch['channel_id']}")]
        for ch in channels
    ]
    keyboard.append([InlineKeyboardButton("➕ Add Channel", callback_data="add_channel")])
    
    await update.message.reply_text(
        "📢 <b>Channel Manager</b>\n\nCurrent channels:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def handle_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("remove_"):
        channel_id = int(query.data.split("_")[1])
        if db.remove_channel(channel_id):
            await query.edit_message_text("✅ Channel removed!")
        else:
            await query.edit_message_text("❌ Failed to remove channel!")
        await manage_channels(update, context)
    elif query.data == "add_channel":
        await query.edit_message_text(
            "🔗 <b>Add Channel</b>\n\nFormat:\n<code>/addchannel -10012345678 https://t.me/channel</code>",
            parse_mode="HTML"
        )

async def add_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in config.ADMINS:
        await update.message.reply_text("❌ Unauthorized!")
        return
    
    if len(context.args) != 2:
        await update.message.reply_text("⚠️ Usage: /addchannel -10012345678 https://t.me/channel")
        return
    
    try:
        channel_id = int(context.args[0])
        channel_link = context.args[1]
        
        if not channel_link.startswith(("https://t.me/", "t.me/")):
            raise ValueError("Invalid link format")
            
        if db.add_channel(channel_id, channel_link):
            await update.message.reply_text(f"✅ Added: {channel_link}")
        else:
            await update.message.reply_text("❌ Failed to add channel!")
    except ValueError:
        await update.message.reply_text("❌ Invalid ID or link format!")

command_handler = [
    ("channels", False, manage_channels),
    ("addchannel", False, add_channel_command),
    (None, True, handle_channel_callback)
]
