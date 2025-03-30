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
    bot_token="7632805578:AAHyFiomSTFhIxt56vHnosOREPg2iMU8_TQ",
)


@app.on_message(filters.command("start") & filters.private & filters.user(5336360484))
async def start(client, message: Message):
    await message.reply_text("Working...")


@app.on_message(filters.command("get") & filters.private & filters.user(5336360484))
async def newUpload(client: Client, message: Message):
    try:
        proc = await message.reply_text("Getting Archive Urls...")

        url = message.text.split(" ", 2)[1]
        quality = message.text.split(" ", 2)[2].upper()

        if "animeacademy.in" in url:
            data = get_anime_urls(url)

            for i in data["links"]:
                if i[0] != quality:
                    continue

                for j in i[1]:
                    await asyncio.sleep(5)
                    await proc.edit_text("Getting Index Urls...")

                    data = get_index_urls(j)
                    await asyncio.sleep(5)

                    await proc.edit_text("Getting File Urls...")

                    files = []

                    for i in data:
                        await asyncio.sleep(5)
                        try:
                            data = IndexScrapper(i)

                            text = "Files : \n\n"

                            for i in data:
                                files.append(i[1])
                            break
                        except Exception as e:
                            continue

                    await asyncio.sleep(5)
                    await proc.edit_text("Starting Upload...")
                    await newUpload(files, client, message, proc)

                await proc.delete()
                await message.reply_text("Upload Completed!")
        else:
            await proc.edit_text("Invalid URL")

    except Exception as e:
        await message.reply_text(str(e))


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
