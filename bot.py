from pyrogram import Client
from pyrogram.storage import MemoryStorage  # Import MemoryStorage
from config import API_ID, API_HASH, BOT_TOKEN

bot = Client(
    "MyBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins"),
    storage=MemoryStorage("Anime_Library_N4")  # Required argument added
)

if __name__ == "__main__":
    print("Bot is running...")
    bot.run()
