import os
import asyncio
import time
import requests
import urllib
from bs4 import BeautifulSoup as bs
from pyrogram import Client, filters, idle
from pyrogram.types import Message

# Create client
app = Client(
    "bot",
    api_id=22299340,
    api_hash="09b09f3e2ff1306da4a19888f614d937",
    bot_token="7632805578:AAHyFiomSTFhIxt56vHnosOREPg2iMU8_TQ",
)

# Helper functions
def get_animekaizoku_urls(url):
    """Scrape download links from AnimeKaizoku"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = bs(r.content, "html.parser")
        anime_data = {}
        
        title = soup.find("h1", class_="entry-title")
        anime_data["title"] = title.text.strip() if title else "Unknown Title"
        anime_data["links"] = []
        
        # Find all download quality sections
        for quality_section in soup.find_all("div", class_="su-box"):
            title = quality_section.find("div", class_="su-box-title")
            if not title or "download" not in title.text.lower():
                continue
                
            quality = title.text.strip().split()[0]  # Get quality (HD, SD, etc)
            links = []
            
            # Find all download buttons
            for link in quality_section.find_all("a", class_="su-button"):
                if "href" in link.attrs:
                    links.append(link["href"])
                    
            if links:
                anime_data["links"].append((quality, links))
                
        return anime_data
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return None

def get_direct_download_links(url):
    """Get direct download links from AnimeKaizoku's redirect pages"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        r = requests.get(url, headers=headers, allow_redirects=False, timeout=10)
        if 300 <= r.status_code < 400:
            return [r.headers.get("Location")]
        return []
    except Exception as e:
        print(f"Error getting direct links from {url}: {str(e)}")
        return []

async def download_file(url, message):
    """Download file with progress updates"""
    try:
        local_filename = url.split('/')[-1]
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        async with requests.Session() as session:
            async with session.get(url, headers=headers, timeout=30, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0
                last_update = 0
                
                with open(local_filename, 'wb') as f:
                    async for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress every 5 seconds
                            if time.time() - last_update > 5:
                                await message.edit_text(
                                    f"Downloading: {downloaded//1024//1024}MB / {total_size//1024//1024}MB"
                                )
                                last_update = time.time()
                                
        return local_filename
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return None

# Bot commands
@app.on_message(filters.command("start") & filters.private & filters.user(5380609667))
async def start(client, message: Message):
    await message.reply_text("Bot is working! Use /get [url] [quality] to download anime")

@app.on_message(filters.command("get") & filters.private & filters.user(5380609667))
async def handle_download(client: Client, message: Message):
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await message.reply_text("Usage: /get [url] [quality]")
            return
            
        url = parts[1]
        quality = parts[2].upper()
        
        proc = await message.reply_text("Fetching download links...")
        
        if "animekaizoku.xyz" not in url:
            await proc.edit_text("Only AnimeKaizoku links are supported (animekaizoku.xyz)")
            return
            
        data = get_animekaizoku_urls(url)
        if not data or not data.get("links"):
            await proc.edit_text("Could not find any download links on that page")
            return
            
        # Find matching quality
        download_links = []
        for q, links in data["links"]:
            if quality in q:
                download_links.extend(links)
                
        if not download_links:
            await proc.edit_text(f"No {quality} links found. Available qualities: {', '.join([q[0] for q in data['links']])}")
            return
            
        # Process each download link
        success_count = 0
        for link in download_links:
            await proc.edit_text(f"Processing {link}...")
            
            # Get direct download links
            direct_links = get_direct_download_links(link)
            if not direct_links:
                await message.reply_text(f"Couldn't get direct link for {link}")
                continue
                
            # Download each file
            for dl_link in direct_links:
                try:
                    filename = await download_file(dl_link, proc)
                    if not filename:
                        continue
                        
                    await client.send_document(
                        chat_id=message.chat.id,
                        document=filename,
                        caption=f"Downloaded from {url}"
                    )
                    success_count += 1
                    if os.path.exists(filename):
                        os.remove(filename)
                    await asyncio.sleep(10)  # Rate limiting
                except Exception as e:
                    await message.reply_text(f"Failed to download {dl_link}: {str(e)}")
                    
        await proc.delete()
        await message.reply_text(f"Download completed! {success_count} files downloaded successfully")
        
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")

# Start the bot
async def main():
    await app.start()
    print("Bot started!")
    await idle()
    await app.stop()
    print("Bot stopped!")

if __name__ == "__main__":
    asyncio.run(main())
