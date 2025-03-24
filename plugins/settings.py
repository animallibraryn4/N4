from pyrogram import Client, filters
from config import ADMIN_ID
from database import force_sub_collection

@Client.on_message(filters.command("setchannel") & filters.user(ADMIN_ID))
async def set_channel(bot, message):
    """ Change the force subscription channels dynamically. """
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("Usage: /setchannel @channel_username")

    new_channel = args[1]
    if not new_channel.startswith("@"):
        return await message.reply("Invalid format. Use @channel_username")

    # Remove existing channels and set new one
    await force_sub_collection.delete_many({})
    await force_sub_collection.insert_one({"channel": new_channel})

    await message.reply(f"Force subscription channel updated: {new_channel}")

@Client.on_message(filters.command("addchannel") & filters.user(ADMIN_ID))
async def add_channel(bot, message):
    """ Add a new force subscription channel. """
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("Usage: /addchannel @channel_username")

    new_channel = args[1]
    if not new_channel.startswith("@"):
        return await message.reply("Invalid format. Use @channel_username")

    await force_sub_collection.insert_one({"channel": new_channel})
    await message.reply(f"Channel {new_channel} added for force subscription.")

@Client.on_message(filters.command("removechannel") & filters.user(ADMIN_ID))
async def remove_channel(bot, message):
    """ Remove a force subscription channel. """
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("Usage: /removechannel @channel_username")

    remove_channel = args[1]
    await force_sub_collection.delete_one({"channel": remove_channel})
    await message.reply(f"Channel {remove_channel} removed from force subscription.")

@Client.on_message(filters.command("listchannels") & filters.user(ADMIN_ID))
async def list_channels(bot, message):
    """ List all force subscription channels. """
    channels = await force_sub_collection.find().to_list(None)
    channel_list = "\n".join([ch["channel"] for ch in channels])
    await message.reply(f"Force Subscription Channels:\n{channel_list}")
