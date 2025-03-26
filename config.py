import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot Token
    TOKEN = os.getenv("TOKEN", "7632805578:AAHyFiomSTFhIxt56vHnosOREPg2iMU8_TQ")
    
    # Anime World Website
    BASE_URL = "https://anime-world.co"
    SEARCH_URL = f"{BASE_URL}/category/anime/"
    
    # Database Channel ID (where anime will be uploaded)
    DB_CHANNEL_ID = int(os.getenv("DB_CHANNEL_ID", -1001896877147))
    
    # Admin User IDs (who can approve uploads)
    ADMINS = list(map(int, os.getenv("ADMINS", "5380609667").split()))
    
    # Download Settings
    MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB
    ALLOWED_QUALITIES = ["360p", "480p", "720p", "1080p"]
