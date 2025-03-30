import asyncio
from pyrogram import filters, idle, Client
from pyrogram.types import Message
from pyrogram import filters, idle, Client
from pyrogram.types import Message

from aatscrapper import get_anime_urls, get_index_urls
from anilistGen import getAnimeInfo
from indexScrapper import IndexScrapper
from uploader import start_uploader

app = Client(
    "bot",
    api_id=22299340,
    api_hash="09b09f3e2ff1306da4a19888f614d937",
    bot_token="7548613937:AAGK2KhZcUnumGQJ-oY5bh8B9ojU4uI8sBQ",
)


@app.on_message(filters.command("start") & filters.private & filters.user(5336360484))
async def start(client, message: Message):
    await message.reply_text("Working...")


@app.on_message(filters.command("get") & filters.private & filters.user(5336360484))
@app.on_message(filters.command("get") & filters.private & filters.user(5336360484))
async def newUpload(client: Client, message: Message):
    try:
        proc = await message.reply_text("Getting Archive Urls...")
        
        if len(message.text.split()) < 3:
            return await proc.edit_text("Usage: /get <url> <quality>")
            
        url = message.text.split(" ", 2)[1]
        quality = message.text.split(" ", 2)[2].upper()

        if "animeacademy.in" not in url:
            return await proc.edit_text("Only animeacademy.in URLs are supported")

        data = get_anime_urls(url)
        if not data or not data.get("links"):
            return await proc.edit_text("No download links found")

        for quality_data in data["links"]:
            if quality_data[0] == quality:
                for archive_url in quality_data[1]:
                    await proc.edit_text(f"Processing {quality} quality links...")
                    await asyncio.sleep(5)
                    
                    try:
                        index_urls = get_index_urls(archive_url)
                        if not index_urls:
                            continue
                            
                        files = []
                        for index_url in index_urls:
                            try:
                                file_data = IndexScrapper(index_url)
                                files.extend([i[1] for i in file_data])
                                break  # Only process first successful index
                            except Exception as e:
                                continue
                                
                        if files:
                            await proc.edit_text(f"Found {len(files)} files, starting upload...")
                            await upload_files(files, client, message, proc)
                            
                    except Exception as e:
                        await message.reply_text(f"Error processing {archive_url}: {str(e)}")
                        continue
                        
        await proc.delete()
        await message.reply_text("Process completed!")
        
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")


async def newUpload(urls, client: Client, message: Message, proc: Message):
    try:
        for url in urls:
            try:
                await start_uploader(client, message, url, proc)
            except Exception as e:
                await message.reply_text(f"Failed to upload {url}\n\n" + str(e))
            await asyncio.sleep(20)
    except Exception as e:
        await message.reply_text(str(e))


@app.on_message(filters.command("post") & filters.private & filters.user(5336360484))
async def postAnime(client: Client, message: Message):
    try:
        id = message.text.split(" ", 1)[1]
        img, text = getAnimeInfo(id)

        await message.reply_photo(img, caption=text)
    except Exception as e:
        await message.reply_text(str(e))


async def main():
    print("Starting...")
    await app.start()
    await app.send_message(5380609667, "Bot started!")
    print("Bot started!")
    await idle()
    await app.stop()
    print("Bot stopped!")


import asyncio

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
