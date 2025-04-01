import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bot.db")
    SILENT_MODE = os.getenv("SILENT_MODE", "False").lower() == "true"
