from pyrogram import Client
from pyrogram.storage import MemoryStorage  # Memory storage import करें
from config import API_ID, API_HASH, BOT_TOKEN

bot = Client(
    "MyBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins"),
    storage=MemoryStorage()  # SQLite के बजाय मेमोरी स्टोरेज का उपयोग करें
)

if __name__ == "__main__":
    print("Bot is running...")
    bot.run()
