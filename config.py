from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Config(BaseSettings):
    # Bot Information
    AUTHOR: str = "Yash-Kun"
    LICENSED_UNDER: str = "GNU GPL V-3.0"
    
    # Telegram Configuration
    API_ID: int = 22299340
    API_HASH: str = "09b09f3e2ff1306da4a19888f614d937"
    MAIN_BOT_TOKEN: str = "7765824536:AAFxnM5qftx3LWjLjxKsnXeuLf3XMXo950o"
    CLIENT_BOT_TOKEN: str = "7906213903:AAEvUmwjmwTHC9NtayJ2NLbYsROQdaOeZR0"
    
    # Chat IDs
    OWNER_IDS: List[int] = [5380609667]
    MAIN_CHANNEL: int = -1001896877147
    FILES_CHANNEL: int = -1001896877147
    PRODUCTION_CHAT: int = -1001925970923
    
    # Database
    DATABASE_URL: str = "mongodb+srv://mikota4432:jkJDQuZH6o8pxxZe@cluster0.2vngilq.mongodb.net/?retryWrites=true&w=majority"
    DATABASE_NAME: str = "AAB"
    
    # File Paths
    DOWNLOADS_DIR: str = "./downloads"
    THUMBNAIL_URL: str = "https://files.catbox.moe/50drro.jpg"
    LOG_FILE: str = "bot.log"
    
    # RSS Feed
    RSS_URL: str = "https://subsplease.org/rss"
    
    # Intervals (in seconds)
    ANIME_CHECK_INTERVAL: int = 300  # 5 minutes
    WORKER_CHECK_INTERVAL: int = 300  # 5 minutes
    
    # Post Template
    POST_TEMPLATE: str = """🔸 {0}
➖〰️➖〰️➖〰️➖〰️➖〰️
🔸 Episode - {1}
〰️➖〰️➖〰️➖〰️➖〰️➖
🔸 Status - {2}
➖〰️➖〰️➖〰️➖〰️➖〰️
🔸 Quality - Sub
〰️➖〰️➖〰️➖〰️➖〰️➖
"""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

config = Config()

