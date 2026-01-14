import asyncio
import logging
from pyrogram import Client, idle
from config import API_ID, API_HASH, BOT_TOKEN
from database import db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    # Create client
    app = Client(
        "animebot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        plugins={"root": "plugins"},
        sleep_threshold=30
    )
    
    # Start bot
    await app.start()
    
    # Get bot info
    me = await app.get_me()
    logger.info(f"Bot started: @{me.username}")
    
    # Start queue processor
    from plugins.queue import process_queue
    asyncio.create_task(process_queue(app))
    
    # Idle
    await idle()
    
    # Stop
    await app.stop()
    db.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
