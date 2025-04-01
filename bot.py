import os
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot configuration
API_ID = 22299340
API_HASH = "09b09f3e2ff1306da4a19888f614d937"
BOT_TOKEN = "7632805578:AAHyFiomSTFhIxt56vHnosOREPg2iMU8_TQ"
AUTHORIZED_USER = 5380609667  # Your user ID

# Create client
app = Client(
    "animekaizoku_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    logger.debug(f"Received start command from {message.from_user.id}")
    if message.from_user.id == AUTHORIZED_USER:
        await message.reply_text("✅ Bot is working! Try /test command")
    else:
        await message.reply_text("❌ Unauthorized access")
        logger.warning(f"Unauthorized access attempt from {message.from_user.id}")

@app.on_message(filters.command("test") & filters.private)
async def test_command(client: Client, message: Message):
    logger.debug(f"Received test command from {message.from_user.id}")
    if message.from_user.id == AUTHORIZED_USER:
        await message.reply_text("🔔 Bot is responsive!")
        logger.info("Successfully responded to test command")
    else:
        await message.reply_text("❌ Unauthorized access")

async def main():
    await app.start()
    logger.info("Bot started successfully!")
    
    # Get bot info to verify connection
    me = await app.get_me()
    logger.info(f"Bot username: @{me.username}")
    logger.info(f"Bot ID: {me.id}")
    
    # Send startup notification
    try:
        await app.send_message(AUTHORIZED_USER, "🤖 Bot started successfully!")
    except Exception as e:
        logger.error(f"Couldn't send startup message: {e}")
    
    await idle()

if __name__ == "__main__":
    logger.info("Starting bot...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Bot shutdown complete")
