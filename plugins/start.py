from pyrogram import Client, filters
from pyrogram.types import Message
from database import db

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    user = message.from_user
    
    # Add user to database
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Log action
    db.log_action(user.id, "start")
    
    # Send welcome message
    await message.reply_text(
        f"👋 Hello {user.first_name}!\n\n"
        "I can download anime episodes from watchanimeworld.net\n\n"
        "📥 **How to use:**\n"
        "1. Send me an episode link from watchanimeworld.net\n"
        "2. I'll download it and send you the video\n"
        "3. Video will have multiple audio tracks (if available)\n"
        "4. Subtitles will be included (if available)\n\n"
        "⚠️ **Note:**\n"
        "• Only episodes from watchanimeworld.net\n"
        "• Queue system (one at a time)\n"
        "• Maximum file size: 2GB\n\n"
        "Just send me a link to get started!"
    )
