from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from config import ADMINS
from helper_func import encode
import random
import string
from database.database import link_data

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('new'))
async def new_link_handler(client: Client, message: Message):
    # Extract the URL from the command
    try:
        _, url = message.text.split(' ', 1)
        if not url.startswith(('http://', 'https://')):
            await message.reply_text("Please provide a valid URL starting with http:// or https://")
            return
    except ValueError:
        await message.reply_text("Usage: /new <URL>")
        return

    # Generate a unique hash for this link
    hash = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    
    # Store the link in database
    await link_data.insert_one({
        'hash': hash,
        'original_url': url,
        'clicks': 0
    })

    # Create the bot link
    base64_string = await encode(f"link-{hash}")
    bot_link = f"https://t.me/{client.username}?start={base64_string}"

    # Send the generated link to admin
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={bot_link}')]
    ])
    
    await message.reply_text(
        f"<b>🔗 Link forwarding created:</b>\n\n"
        f"<b>Original URL:</b> {url}\n\n"
        f"<b>Bot Link:</b> {bot_link}",
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )
