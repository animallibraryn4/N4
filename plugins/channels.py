from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from database import force_sub_collection

async def get_force_sub_channels():
    channels = await force_sub_collection.find().to_list(None)
    return [ch["channel"] for ch in channels]

@Client.on_message(filters.private & ~filters.command("start"))
async def force_sub(bot, message):
    channels = await get_force_sub_channels()
    
    for channel in channels:
        try:
            user = await bot.get_chat_member(channel, message.from_user.id)
            if user.status not in ["member", "administrator", "creator"]:
                raise UserNotParticipant
        except UserNotParticipant:
            return await message.reply(f"Please join our channel {channel} first!", disable_web_page_preview=True)
