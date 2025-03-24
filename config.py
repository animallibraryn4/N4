from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database import get_channels, add_channel, remove_channel
import os
import logging

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class Config:
    # Bot Token from @BotFather
    BOT_TOKEN = os.getenv("BOT_TOKEN", "7632805578:AAHyFiomSTFhIxt56vHnosOREPg2iMU8_TQ")
    
    # Bot Username
    BOT_USERNAME = os.getenv("BOT_USERNAME", "N4_Links_bot")
    
    # Telegram API ID and Hash
    API_ID = int(os.getenv("API_ID", 22299340))
    API_HASH = os.getenv("API_HASH", "09b09f3e2ff1306da4a19888f614d937")
    
    # Admin IDs
    ADMINS = [int(admin) for admin in os.getenv('ADMINS', '5380609667').split(',') if admin]
    
    # Database URI
    DB_URI = os.getenv("DB_URI", "mongodb+srv://gerbil77001:lkFEusnWzXwe53NU@cluster0.mkeei.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

config = Config()

async def manage_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show channel management interface"""
    user_id = update.effective_user.id
    
    # Check if user is admin
    if user_id not in config.ADMINS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    channels = get_channels()
    keyboard = []
    
    # Add buttons for each channel
    for channel in channels:
        keyboard.append([
            InlineKeyboardButton(
                f"Remove {channel['channel_link']}", 
                callback_data=f"remove_{channel['channel_id']}"
            )
        ])
    
    # Add button to add new channel
    keyboard.append([InlineKeyboardButton("Add New Channel", callback_data="add_channel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Manage Force Subscribe Channels:",
        reply_markup=reply_markup
    )

async def handle_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle channel management callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("remove_"):
        channel_id = int(data.split("_")[1])
        remove_channel(channel_id)
        await query.edit_message_text(text="Channel removed successfully!")
        await manage_channels(update, context)  # Refresh the interface
    elif data == "add_channel":
        await query.edit_message_text(
            text="Please send the channel ID and link in format:\n"
                 "/addchannel channel_id channel_link"
        )

async def add_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /addchannel command"""
    user_id = update.effective_user.id
    
    # Check if user is admin
    if user_id not in config.ADMINS:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addchannel channel_id channel_link")
        return
    
    channel_id = context.args[0]
    channel_link = context.args[1]
    
    try:
        channel_id = int(channel_id)
    except ValueError:
        await update.message.reply_text("Channel ID must be a number")
        return
    
    add_channel(channel_id, channel_link)
    await update.message.reply_text("Channel added successfully!")

def setup_handlers(application):
    """Set up all command handlers"""
    application.add_handler(CommandHandler("channels", manage_channels))
    application.add_handler(CommandHandler("addchannel", add_channel_command))
    application.add_handler(CallbackQueryHandler(handle_channel_callback))

def main():
    """Start the bot"""
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    setup_handlers(application)
    
    logger.info("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
