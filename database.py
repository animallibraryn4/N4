from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client.link_bot
users = db.users
links = db.links

def get_user(user_id):
    return users.find_one({"user_id": user_id})

def add_user(user_id):
    if not get_user(user_id):
        users.insert_one({"user_id": user_id, "count": 0, "last_time": 0})

def update_user(user_id, data):
    users.update_one({"user_id": user_id}, {"$set": data})

def store_link(short_code, channel_link):
    links.insert_one({"short_code": short_code, "channel_link": channel_link})

def get_link(short_code):
    return links.find_one({"short_code": short_code})
