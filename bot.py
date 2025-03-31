# bot.py
from pyrogram import filters, idle, Client
from pyrogram.types import Message
import asyncio
import logging
from typing import List

from aatscrapper import get_anime_urls, get_index_urls
from anilistGen import getAnimeInfo
from indexScrapper import IndexScrapper
from uploader import start_uploader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Move credentials to environment variables
app = Client(
    "bot",
    api_id=22299340,  # Should be in environment variables
    api_hash="09b09f3e2ff1306da4a19888f614d937",  # Should be in environment variables
    bot_token="7632805578:AAHyFiomSTFhIxt56vHnosOREPg2iMU8_TQ",  # Should be in environment variables
)

@app.on_message(filters.command("start") & filters.private & filters.user(5380609667))
async def start(client, message: Message):
    await message.reply_text("Bot is operational!")

@app.on_message(filters.command("get") & filters.private & filters.user(5380609667))
async def handle_upload(client: Client, message: Message):
    """Handle anime upload requests."""
    try:
        proc = await message.reply_text("Processing request...")
        
        # Validate command format
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await proc.edit_text("Usage: /get <url> <quality>")
            return
            
        url, quality = parts[1], parts[2].upper()
        
        if "animeacademy.in" not in url:
            await proc.edit_text("Only animeacademy.in URLs are supported")
            return
            
        await process_anime_upload(client, message, proc, url, quality)
        
    except Exception as e:
        logger.error(f"Error in handle_upload: {e}")
        await message.reply_text(f"Error: {str(e)}")

async def process_anime_upload(client: Client, message: Message, proc: Message, url: str, quality: str):
    """Process anime upload from given URL."""
    try:
        data = get_anime_urls(url)
        
        for qual, links in data["links"]:
            if qual != quality:
                continue
                
            for link in links:
                await asyncio.sleep(5)  # Rate limiting
                await proc.edit_text("Fetching index URLs...")
                
                index_urls = get_index_urls(link)
                if not index_urls:
                    continue
                    
                await process_index_urls(client, message, proc, index_urls)
                
        await proc.delete()
        await message.reply_text("Upload process completed!")
        
    except Exception as e:
        logger.error(f"Error in process_anime_upload: {e}")
        raise

async def process_index_urls(client: Client, message: Message, proc: Message, index_urls: List[str]):
    """Process index URLs and upload files."""
    try:
        await proc.edit_text("Extracting file URLs...")
        files = []
        
        for url in index_urls:
            try:
                file_data = IndexScrapper(url)
                files.extend([i[1] for i in file_data])
                break  # Only process first successful index
            except Exception as e:
                logger.warning(f"Skipping index URL {url}: {e}")
                continue
                
        if files:
            await proc.edit_text("Starting uploads...")
            await new_upload(files, client, message, proc)
            
    except Exception as e:
        logger.error(f"Error in process_index_urls: {e}")
        raise

async def new_upload(urls: List[str], client: Client, message: Message, proc: Message):
    """Handle the upload process for multiple URLs."""
    try:
        for url in urls:
            try:
                await start_uploader(client, message, url, proc)
                await asyncio.sleep(20)  # Rate limiting
            except Exception as e:
                logger.error(f"Failed to upload {url}: {e}")
                await message.reply_text(f"Failed to upload {url}\nError: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in new_upload: {e}")
        raise

@app.on_message(filters.command("post") & filters.private & filters.user(5380609667))
async def post_anime(client: Client, message: Message):
    """Post anime information from AniList."""
    try:
        query = message.text.split(maxsplit=1)[1]
        img, text = getAnimeInfo(query)
        await message.reply_photo(img, caption=text)
    except IndexError:
        await message.reply_text("Usage: /post <anime_name>")
    except Exception as e:
        logger.error(f"Error in post_anime: {e}")
        await message.reply_text(f"Error: {str(e)}")

async def main():
    """Main bot function."""
    logger.info("Starting bot...")
    await app.start()
    await app.send_message(5380609667, "Bot started successfully!")
    logger.info("Bot started successfully!")
    await idle()
    await app.stop()
    logger.info("Bot stopped")

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
