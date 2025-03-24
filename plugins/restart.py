import os
from pyrogram import Client, filters
from config import ADMIN_ID

@Client.on_message(filters.command("restart") & filters.user(ADMIN_ID))
async def restart_bot(bot, message):
    await message.reply("Bot is restarting...")
    os.system("python3 bot.py")
