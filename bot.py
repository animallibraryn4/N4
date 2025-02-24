from pyrogram import Client, filters from pymongo import MongoClient import time import random import string

Load config settings

from config import API_ID, API_HASH, BOT_TOKEN, MONGO_URI, ADMINS, FORCE_SUB

Initialize bot and database

bot = Client("link_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN) db = MongoClient(MONGO_URI).link_bot users = db.users links = db.links

Function to generate short link

def generate_short_link(): return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

Command to generate new link

@bot.on_message(filters.private & filters.command("start")) def start(client, message): user_id = message.from_user.id user = users.find_one({"user_id": user_id}) if not user: users.insert_one({"user_id": user_id, "count": 0, "last_time": 0}) message.reply_text("Send me a channel link to generate a new short link.")

@bot.on_message(filters.private & filters.regex(r'https://t.me/\S+')) def create_link(client, message): user_id = message.from_user.id channel_link = message.text user = users.find_one({"user_id": user_id})

if user["count"] >= 5:
    if time.time() - user["last_time"] < 600:
        remaining = 600 - (time.time() - user["last_time"])
        message.reply_text(f"You have reached the limit! Wait {int(remaining)} seconds.")
        return
    users.update_one({"user_id": user_id}, {"$set": {"count": 0, "last_time": time.time()}})

short_code = generate_short_link()
short_link = f"https://t.me/{bot.me.username}?start={short_code}"

links.insert_one({"short_code": short_code, "channel_link": channel_link})
users.update_one({"user_id": user_id}, {"$inc": {"count": 1}, "$set": {"last_time": time.time()}})

message.reply_text(f"Here is your short link: {short_link}")

@bot.on_message(filters.private & filters.regex(r'^/start \S+')) def handle_short_link(client, message): short_code = message.text.split()[1] link_data = links.find_one({"short_code": short_code})

if not link_data:
    message.reply_text("Invalid link!")
    return

message.reply_text(f"Join this channel first: {link_data['channel_link']}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Join Channel", url=link_data['channel_link'])]
                    ]))

Start the bot

bot.run()


