import os
import asyncio
import time
import requests
from bs4 import BeautifulSoup as bs
from pyrogram import Client, filters, idle
from pyrogram.types import Message
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot configuration
API_ID = 22299340
API_HASH = "09b09f3e2ff1306da4a19888f614d937"
BOT_TOKEN = "7632805578:AAHyFiomSTFhIxt56vHnosOREPg2iMU8_TQ"
AUTHORIZED_USER = 5380609667

# Create client
app = Client(
    "animekaizoku_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Common headers for requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def debug_request(response):
    """Debug HTTP requests"""
    logger.debug(f"Request URL: {response.url}")
    logger.debug(f"Status Code: {response.status_code}")
    logger.debug(f"Response Headers: {response.headers}")
    if len(response.text) < 500:
        logger.debug(f"Response Text: {response.text}")

async def fetch_url(url):
    """Fetch URL with error handling"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        debug_request(response)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return None

def get_animekaizoku_urls(url):
    """Scrape download links from AnimeKaizoku with improved parsing"""
    logger.info(f"Scraping AnimeKaizoku page: {url}")
    response = fetch_url(url)
    if not response:
        return None

    try:
        soup = bs(response.content, 'html.parser')
        anime_data = {"title": "", "links": []}

        # Extract title
        title_tag = soup.find('h1', class_='entry-title')
        anime_data["title"] = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

        # Find download sections
        download_sections = soup.find_all('div', class_='su-box')
        if not download_sections:
            logger.warning("No download sections found")

        for section in download_sections:
            title = section.find('div', class_='su-box-title')
            if not title or 'download' not in title.get_text(strip=True).lower():
                continue

            quality = title.get_text(strip=True).split()[0]
            links = []
            
            for link in section.find_all('a', class_='su-button'):
                href = link.get('href')
                if href and not href.startswith('javascript'):
                    links.append(href)

            if links:
                anime_data["links"].append((quality, links))
                logger.info(f"Found {len(links)} {quality} links")

        return anime_data if anime_data["links"] else None

    except Exception as e:
        logger.error(f"Error parsing AnimeKaizoku page: {str(e)}")
        return None

async def process_download(client: Client, message: Message, url: str, quality: str):
    """Handle the complete download process"""
    proc_msg = await message.reply_text(f"🔄 Processing {quality} links from {url}...")

    # Step 1: Get anime page data
    anime_data = get_animekaizoku_urls(url)
    if not anime_data:
        await proc_msg.edit_text("❌ Could not extract download links from this page")
        return

    # Step 2: Find matching quality links
    quality_links = []
    for q, links in anime_data["links"]:
        if quality.upper() in q.upper():
            quality_links.extend(links)

    if not quality_links:
        available = ", ".join([q[0] for q in anime_data["links"]])
        await proc_msg.edit_text(f"❌ No {quality} links found. Available qualities: {available}")
        return

    # Step 3: Process each download link
    success_count = 0
    for index, link in enumerate(quality_links, 1):
        try:
            await proc_msg.edit_text(f"🔗 Processing link {index}/{len(quality_links)}...")

            # Get final download URL
            response = await fetch_url(link)
            if not response:
                continue

            if 300 <= response.status_code < 400:
                download_url = response.headers.get('Location')
                if not download_url:
                    continue

                # Download the file
                await proc_msg.edit_text(f"⬇️ Downloading file {index}...")
                try:
                    file_path = await download_file(download_url, proc_msg)
                    if not file_path:
                        continue

                    # Send to Telegram
                    await proc_msg.edit_text(f"📤 Uploading file {index}...")
                    await client.send_document(
                        chat_id=message.chat.id,
                        document=file_path,
                        caption=f"📁 {anime_data['title']} - {quality}",
                        progress=progress_callback,
                        progress_args=(proc_msg,)
                    )
                    success_count += 1

                finally:
                    if os.path.exists(file_path):
                        os.remove(file_path)

            await asyncio.sleep(5)  # Rate limiting

        except Exception as e:
            logger.error(f"Error processing link {link}: {str(e)}")
            continue

    # Final report
    result_msg = f"✅ Download complete! {success_count}/{len(quality_links)} files downloaded successfully"
    await proc_msg.edit_text(result_msg)
    logger.info(result_msg)

# Bot command handlers
@app.on_message(filters.command("start") & filters.private & filters.user(AUTHORIZED_USER))
async def start_command(client, message: Message):
    await message.reply_text(
        "🎌 AnimeKaizoku Download Bot\n\n"
        "Usage:\n"
        "/get [URL] [QUALITY] - Download anime from AnimeKaizoku\n\n"
        "Example:\n"
        "/get https://animekaizoku.xyz/one-piece-episode-1080/ HD"
    )

@app.on_message(filters.command("get") & filters.private & filters.user(AUTHORIZED_USER))
async def get_command(client: Client, message: Message):
    try:
        args = message.text.split(maxsplit=2)
        if len(args) < 3:
            await message.reply_text("⚠️ Usage: /get [URL] [QUALITY]\nExample: /get https://animekaizoku.xyz/one-piece-episode-1080/ HD")
            return

        url = args[1].strip()
        quality = args[2].strip().upper()

        if "animekaizoku.xyz" not in url:
            await message.reply_text("❌ Only AnimeKaizoku.xyz links are supported")
            return

        await process_download(client, message, url, quality)

    except Exception as e:
        logger.error(f"Error in get_command: {str(e)}")
        await message.reply_text(f"❌ An error occurred: {str(e)}")

async def main():
    await app.start()
    logger.info("Bot started successfully!")
    await idle()
    await app.stop()
    logger.info("Bot stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
