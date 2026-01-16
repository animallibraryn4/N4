import os
from typing import List

class Config:
    # Bot Information
    AUTHOR = "Yash-Kun"
    LICENSED_UNDER = "GNU GPL V-3.0"
    
    # Telegram Configuration (Update these in .env or here)
    API_ID = int(os.getenv("API_ID", "22299340"))
    API_HASH = os.getenv("API_HASH", "")
    MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN", "7765824536:AAFxnM5qftx3LWjLjxKsnXeuLf3XMXo950o")
    CLIENT_BOT_TOKEN = os.getenv("CLIENT_BOT_TOKEN", "7906213903:AAEvUmwjmwTHC9NtayJ2NLbYsROQdaOeZR0")
    
    # Chat IDs
    OWNER_IDS = [int(x) for x in os.getenv("OWNER_IDS", "5380609667").split(",")]
    MAIN_CHANNEL = int(os.getenv("MAIN_CHANNEL", "-1001896877147"))
    FILES_CHANNEL = int(os.getenv("FILES_CHANNEL", "-1001896877147"))
    PRODUCTION_CHAT = int(os.getenv("PRODUCTION_CHAT", "-1001925970923"))
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "mongodb+srv://mikota4432:jkJDQuZH6o8pxxZe@cluster0.2vngilq.mongodb.net/?retryWrites=true&w=majority")
    DATABASE_NAME = "AAB"
    
    # File Paths
    DOWNLOADS_DIR = "./downloads"
    THUMBNAIL_URL = "https://files.catbox.moe/50drro.jpg"
    LOG_FILE = "bot.log"
    
    # RSS Feed
    RSS_URL = "https://subsplease.org/rss"
    
    # Intervals (in seconds)
    ANIME_CHECK_INTERVAL = 300
    WORKER_CHECK_INTERVAL = 300
    
    # Post Template
    POST_TEMPLATE = """🔸 {}
➖〰️➖〰️➖〰️➖〰️➖〰️
🔸 Episode - {}
〰️➖〰️➖〰️➖〰️➖〰️➖
🔸 Status - {}
➖〰️➖〰️➖〰️➖〰️➖〰️
🔸 Quality - Sub
〰️➖〰️➖〰️➖〰️➖〰️➖
"""

config = Config()

