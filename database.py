from pymongo import MongoClient, ASCENDING
from config import MONGO_URI
from datetime import datetime

# Initialize MongoDB connection
client = MongoClient(MONGO_URI)
db = client.link_bot
users = db.users
links = db.links

# Ensure indexes for performance and uniqueness
users.create_index([("user_id", ASCENDING)], unique=True)
links.create_index([("short_code", ASCENDING)], unique=True)

# User management functions
def get_user(user_id):
    """Fetch a user document by user_id."""
    return users.find_one({"user_id": user_id})

def add_user(user_id):
    """Add a new user if they don't exist."""
    users.update_one(
        {"user_id": user_id}, 
        {"$setOnInsert": {"count": 0, "last_time": datetime.utcnow()}}, 
        upsert=True
    )

def update_user(user_id, data):
    """Update user data."""
    users.update_one({"user_id": user_id}, {"$set": data})

def update_user_time(user_id):
    """Update the last request time for a user."""
    users.update_one({"user_id": user_id}, {"$set": {"last_time": datetime.utcnow()}})

# Link management functions
def store_link(short_code, channel_link):
    """Store a generated short code with its corresponding channel link."""
    links.insert_one({"short_code": short_code, "channel_link": channel_link})

def get_link(short_code):
    """Retrieve a channel link using the short code."""
    return links.find_one({"short_code": short_code})
