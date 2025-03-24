from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@Client.on_message(filters.command("genlink"))
async def generate_link(bot, message):
    if not message.reply_to_message or not message.reply_to_message.text:
        return await message.reply("Please reply to a message containing a link.")

    original_link = message.reply_to_message.text
    generated_link = f"https://yourbot.com/{message.chat.id}/{message.message_id}"

    button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Join Channel", url=original_link)]]
    )

    await message.reply("Here is your link! Click below to proceed:", reply_markup=button)
