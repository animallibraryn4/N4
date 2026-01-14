from pyrogram import Client, filters
from pyrogram.types import Message
import re
from urllib.parse import urlparse
from plugins.utils import is_valid_url, extract_domain
from database import db

from pyrogram import Client, filters
from pyrogram.types import Message
from plugins.debug import debug_url
import asyncio

@Client.on_message(filters.command("debug") & filters.private)
async def debug_command(client, message: Message):
    """Debug command to test URLs"""
    if len(message.command) < 2:
        await message.reply_text("Usage: /debug <url>")
        return
    
    url = message.command[1]
    msg = await message.reply_text(f"🔍 Debugging {url}...")
    
    try:
        result = await debug_url(url)
        await msg.edit_text(
            f"✅ Debug complete:\n"
            f"• Iframes: {result['iframes']}\n"
            f"• Video tags: {result['videos']}\n"
            f"• Player divs: {result['player_divs']}\n"
            f"• Video URLs in scripts: {result['video_urls_in_scripts']}"
        )
    except Exception as e:
        await msg.edit_text(f"❌ Debug failed: {str(e)}")

# Allowed domains
ALLOWED_DOMAINS = [
    "watchanimeworld.net",
    "www.watchanimeworld.net"
]

# Episode URL pattern
EPISODE_PATTERN = r'/episode/'

@Client.on_message(filters.private & ~filters.command("start"))
async def link_handler(client, message: Message):
    """Handle incoming messages and validate URLs"""
    
    text = message.text or message.caption
    
    if not text:
        await message.reply_text("Please send a valid episode URL.")
        return
    
    # Extract URL from text
    urls = re.findall(r'https?://[^\s]+', text)
    
    if not urls:
        await message.reply_text("No valid URL found in your message.")
        return
    
    url = urls[0]
    
    # Validate URL
    if not is_valid_url(url):
        await message.reply_text("Invalid URL format.")
        return
    
    # Check domain
    domain = extract_domain(url)
    if domain not in ALLOWED_DOMAINS:
        await message.reply_text(
            f"❌ Domain not allowed.\n"
            f"Only links from watchanimeworld.net are supported."
        )
        return
    
    # Check if it's an episode URL
    if not re.search(EPISODE_PATTERN, url):
        await message.reply_text(
            "❌ This doesn't look like an episode URL.\n"
            "Please send a direct episode link (containing /episode/)."
        )
        return
    
    # Log URL reception
    db.log_action(
        user_id=message.from_user.id,
        action="url_received",
        details=f"URL: {url}"
    )
    
    # Add to queue
    from plugins.queue import add_to_queue
    await add_to_queue(client, message, url)

