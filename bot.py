from pyrogram import Client
from pyrogram.storage import MemoryStorage  # Import MemoryStorage
from config import API_ID, API_HASH, BOT_TOKEN

import os
from pyrogram import Client, filters

print("🔄 Bot is starting...")

bot = Client(
    "MyBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins")  # Ensure this is correct
    storage=MemoryStorage("my_memory_storage")# Required argument added

print("✅ Plugins loaded successfully!")

if __name__ == "__main__":
    print("Bot is running...")
    bot.run()
    
