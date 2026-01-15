import os
from typing import List
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

class Config:
    # Bot Information
    AUTHOR = "Yash-Kun"
    LICENSED_UNDER = "GNU GPL V-3.0"
    
    # Telegram Configuration - FROM ENVIRONMENT VARIABLES
    API_ID = int(os.getenv("API_ID", 22299340))
    API_HASH = os.getenv("API_HASH", "09b09f3e2ff1306da4a19888f614d937")
    MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN", "7906213903:AAEvUmwjmwTHC9NtayJ2NLbYsROQdaOeZR0")
    CLIENT_BOT_TOKEN = os.getenv("CLIENT_BOT_TOKEN", "7765824536:AAFxnM5qftx3LWjLjxKsnXeuLf3XMXo950o")
    
    # Chat IDs
    OWNER_IDS = ["5380609667"]
    MAIN_CHANNEL = -1001896877147
    FILES_CHANNEL = -1001896877147
    PRODUCTION_CHAT = -1001925970923
    
    # Database - FROM ENVIRONMENT VARIABLES
    DATABASE_URL = os.getenv("DATABASE_URL", "mongodb+srv://mikota4432:jkJDQuZH6o8pxxZe@cluster0.2vngilq.mongodb.net/?retryWrites=true&w=majority")
    DATABASE_NAME = "AAB"
    
    # File Paths
    DOWNLOADS_DIR = "./downloads"
    THUMBNAIL_URL = "https://files.catbox.moe/50drro.jpg"
    LOG_FILE = "logging.txt"
    
    # RSS Feed
    RSS_URL = "http://subsplease.org/rss"
    
    # AniList API
    ANILIST_URL = "https://graphql.anilist.co"
    
    # Post Template
    POST_TEMPLATE = """
🔸 {}
➖〰️➖〰️➖〰️➖〰️➖〰️
🔸 Episode - {}
〰️➖〰️➖〰️➖〰️➖〰️➖
🔸 Status - {}
➖〰️➖〰️➖〰️➖〰️➖〰️
🔸 Quality - Sub
〰️➖〰️➖〰️➖〰️➖〰️➖
"""
    
    # Check Intervals (in seconds)
    ANIME_CHECK_INTERVAL = 300  # 5 minutes
    WORKER_CHECK_INTERVAL = 300  # 5 minutes

    def validate(self):
        """Validate required configuration"""
        missing = []
        if not self.API_HASH:
            missing.append("API_HASH")
        if not self.MAIN_BOT_TOKEN:
            missing.append("MAIN_BOT_TOKEN")
        if not self.CLIENT_BOT_TOKEN:
            missing.append("CLIENT_BOT_TOKEN")
        if not self.DATABASE_URL:
            missing.append("DATABASE_URL")
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

config = Config()


