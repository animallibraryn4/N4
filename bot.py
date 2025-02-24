from pyrogram import Client, filters
from pymongo import MongoClient
import time
import random
import string
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

Load config settings

from config import API_ID, API_HASH, BOT_TOKEN, MONGO_URI, ADMINS, FORCE_SUB

Initialize bot and database

bot = Client("link_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = MongoClient(MONGO_URI).link_bot
users = db.users
links = db.links

Database Functions

def get_user(user_id): return users.find_one({"user_id": user_id})

def add_user(user_id): if not get_user(user_id): users.insert_one({"user_id": user_id, "count": 0, "last_time": 0})

def update_user(user_id, data): users.update_one({"user_id": user_id}, {"$set": data})

def store_link(short_code, channel_link): links.insert_one({"short_code": short_code, "channel_link": channel_link})

def get_link(short_code): return links.find_one({"short_code": short_code})

Function to generate short link

def generate_short_link():
return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

Command to start bot

@bot.on_message(filters.private & filters.command("start"))
def start(client, message):
user_id = message.from_user.id
add_user(user_id)
message.reply_text("Send me a channel link to generate a new short link.")

Handling channel links

@bot.on_message(filters.private & filters.regex(r'https://t.me/\S+'))
def create_link(client, message):
user_id = message.from_user.id
channel_link = message.text
user = get_user(user_id)

if user["count"] >= 5:  
    if time.time() - user["last_time"] < 600:  
        remaining = 600 - (time.time() - user["last_time"])  
        message.reply_text(f"You have reached the limit! Wait {int(remaining)} seconds.")  
        return  
    update_user(user_id, {"count": 0, "last_time": time.time()})  

short_code = generate_short_link()  
short_link = f"https://t.me/{client.me.username}?start={short_code}"  

store_link(short_code, channel_link)  
update_user(user_id, {"count": user["count"] + 1, "last_time": time.time()})  

message.reply_text(f"Here is your short link: {short_link}")

Handling short links

@bot.on_message(filters.private & filters.regex(r'^/start \S+'))
def handle_short_link(client, message):
short_code = message.text.split()[1]
link_data = get_link(short_code)

if not link_data:  
    message.reply_text("Invalid link!")  
    return  

message.reply_text(f"Join this channel first: {link_data['channel_link']}",  
                   reply_markup=InlineKeyboardMarkup([  
                       [InlineKeyboardButton("Join Channel", url=link_data['channel_link'])]  
                   ]))

Start the bot

bot.run()

