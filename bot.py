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

# Set an explicit path for session storage
SESSION_FILE = os.path.join(os.getcwd(), "MyBot.session")

bot = Client(
    SESSION_FILE,  # Using an absolute path to prevent SQLite errors
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins")  # Load command plugins
)

if __name__ == "__main__":
    logging.info("Bot is running...")
    bot.run()
