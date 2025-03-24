import os
import logging
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

# Ensure the bot runs in the correct directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Enable logging for debugging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Fix storage issue by letting Pyrogram use in-memory storage
bot = Client(
    "MyBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    storage=None,  # Fix for "storage" error
    plugins=dict(root="plugins")  # Load command plugins
)

if __name__ == "__main__":
    logging.info("Bot is running...")
    bot.run()
