from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from config import Config
import random
import string
import time
from database import save_link, get_original_link

def generate_random_string(length=8):
    """Generate a random string for the link"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

async def genlink(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /genlink command"""
    message = update.message
    
    if not message or not message.reply_to_message or not message.reply_to_message.text:
        await message.reply_text("Please reply to a message containing a link with /genlink")
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
    await message.reply_text(
        f"{Config.WELCOME_MESSAGE}\n\n{generated_link}",
        reply_markup=reply_markup
    )

async def handle_start_with_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle when someone clicks the generated link"""
    query = update.callback_query
    user_id = query.from_user.id if query else update.message.from_user.id
    
    # Check force subscription
    if not check_force_sub(user_id):
        channels_to_join = "\n".join([f"- {ch['channel_link']}" for ch in Config.FORCE_SUB_CHANNELS])
        if update.message:
            await update.message.reply_text(
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
                await query.edit_message_text(
                    f"{Config.WELCOME_MESSAGE}",
                    reply_markup=reply_markup
                )
            elif update.message:
                await update.message.reply_text(
                    f"{Config.WELCOME_MESSAGE}",
                    reply_markup=reply_markup
                )
            return
    
    # If no valid link found
    if query:
        await query.answer("Invalid or expired link!", show_alert=True)
    elif update.message:
        await update.message.reply_text("Invalid or expired link!")

# Command handlers to register
command_handler = [
    ("genlink", False, genlink),
    ("start", False, handle_start_with_link)
]
