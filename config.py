import os
import logging

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class Config:
    # Bot Token from @BotFather
    BOT_TOKEN = os.getenv("BOT_TOKEN", "7632805578:AAHyFiomSTFhIxt56vHnosOREPg2iMU8_TQ")
    
    # Bot Username
    BOT_USERNAME = os.getenv("BOT_USERNAME", "N4_Links_bot")
    
    # Telegram API ID and Hash
    API_ID = int(os.getenv("API_ID", 22299340))
    API_HASH = os.getenv("API_HASH", "09b09f3e2ff1306da4a19888f614d937")
    
    # Admin IDs
    ADMINS = [int(admin) for admin in os.getenv('ADMINS', '5380609667').split(',') if admin]
    
    # Database URI
    DB_URI = os.getenv("DB_URI", "mongodb+srv://gerbil77001:lkFEusnWzXwe53NU@cluster0.mkeei.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    
    # Message configurations
    WELCOME_MESSAGE = "Here is your link! Click below to proceed:"
    JOIN_BUTTON_TEXT = "Join Channel"
    LINK_EXPIRE_TIME = 86400  # 24 hours
    RESTART_COOLDOWN = 300  # 5 minutes

# Single config instance
config = Config()
