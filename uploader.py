from pyrogram.types import Message
import requests
from math import floor
import time

import os

try:
    os.mkdir("files")
except:
    pass


async def download(url, proc: Message):
    r = requests.get(url, stream=True)

    total_size = floor(int(r.headers.get("content-length", 0)) / (1024 * 1024))

    ext = url.split(".")[-1]

    t1 = time.time()
    mbDownloaded = 0

    with open(f"file.{ext}", "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
            mbDownloaded += 1

            t2 = time.time()

            if (t2 - t1) > 5:
                try:
                    await proc.edit_text(
                        f"Downloading : {mbDownloaded} / {total_size} MB"
                    )
                    mbDownloaded = 0
                    t1 = t2
                except:
                    pass

    return f"file.{ext}"


import os
import urllib


def get_file_name(url):
    x = url.split("/")[-1]
    x = urllib.parse.unquote(x)
    ext = x.split(".")[-1]
    x = x.split("-AAT[")[0].strip().replace(".", " ").replace("-", " ") + " [@animestorys_1]." + ext
    return x


t3 = 0


async def uploadProgress(current, total, message: Message):
    global t3

    t4 = time.time()

    if (t4 - t3) > 5:
        total = floor(total / (1024 * 1024))
        current = floor(current / (1024 * 1024))
        try:
            await message.edit_text(f"Uploading : {current} / {total} MB")
            t3 = t4
        except:
            pass


from pyrogram import Client


async def start_uploader(client: Client, message: Message, url: str, proc: Message):
    global t3

    await proc.edit_text(f"Processing : `{url}`")

    file = await download(url, proc)
    filename = get_file_name(url)
    os.rename(file, "./files/" + filename)

    caption = f"🧿 **File :** `{filename}`"

    t3 = time.time()
    await client.send_document(
        chat_id="animestorys_1",
        document="./files/" + filename,
        thumb="thumb.jpeg",
        caption=caption,
        file_name=filename,
        force_document=True,
        progress=uploadProgress,
        progress_args=(proc,),
    )

    os.remove("./files/" + filename)
