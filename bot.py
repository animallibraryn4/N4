import os
import asyncio
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserMigrate

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
AUTHORIZED_USER = 5380609667

# Create client with DC5 settings
app = Client(
    "animekaizoku_bot_dc5",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=1,
    ipv6=False
)

@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    if message.from_user.id == AUTHORIZED_USER:
        await message.reply_text("✅ Bot is working! Try /test")
    else:
        await message.reply_text("❌ Unauthorized")

@app.on_message(filters.command("test") & filters.private)
async def test_command(client: Client, message: Message):
    if message.from_user.id == AUTHORIZED_USER:
        await message.reply_text("🔔 Bot is responsive!")
    else:
        await message.reply_text("❌ Unauthorized")

async def run_bot():
    retries = 0
    max_retries = 3
    
    while retries < max_retries:
        try:
            await app.start()
            me = await app.get_me()
            logger.info(f"Bot @{me.username} started!")
            
            # Verify connection
            try:
                await app.send_message(AUTHORIZED_USER, "🤖 Bot started successfully!")
            except Exception as e:
                logger.error(f"Startup message failed: {e}")
            
            await idle()
            break
            
        except UserMigrate as e:
            logger.error(f"Migration error: DC{e.x}")
            retries += 1
            await asyncio.sleep(5)
            
        except FloodWait as e:
            logger.error(f"Flood wait: {e.x}s")
            await asyncio.sleep(e.x)
            retries += 1
            
        except Exception as e:
            logger.error(f"Error: {e}")
            retries += 1
            await asyncio.sleep(5)
            
        finally:
            await app.stop()
            logger.info("Bot stopped")

if __name__ == "__main__":
    logger.info("Starting bot...")
    asyncio.run(run_bot())
