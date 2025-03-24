from config import Config
from pymongo import MongoClient
import time

# Initialize MongoDB client
client = MongoClient(Config.DB_URI)
db = client.telegram_link_bot

def save_link(link_id, original_link, user_id, expire_time):
    """Save generated link to database"""
    db.links.insert_one({
        "link_id": link_id,
        "original_link": original_link,
        "user_id": user_id,
        "created_at": time.time(),
        "expire_time": expire_time
    })

def get_original_link(link_id):
    """Get original link from database"""
    link = db.links.find_one({"link_id": link_id})
    return link["original_link"] if link else None

def get_channels():
    """Get all force subscribe channels"""
    return list(db.channels.find({}))

def add_channel(channel_id, channel_link):
    """Add a new force subscribe channel"""
    db.channels.insert_one({
        "channel_id": channel_id,
        "channel_link": channel_link,
        "added_at": time.time()
    })
    # Update config
    Config.FORCE_SUB_CHANNELS.append({
        "channel_id": channel_id,
        "channel_link": channel_link
    })

def remove_channel(channel_id):
    """Remove a force subscribe channel"""
    db.channels.delete_one({"channel_id": channel_id})
    # Update config
    Config.FORCE_SUB_CHANNELS = [ch for ch in Config.FORCE_SUB_CHANNELS if ch["channel_id"] != channel_id]

def get_last_restart():
    """Get last restart time"""
    restart = db.restarts.find_one({})
    return restart["timestamp"] if restart else None

def save_last_restart(timestamp):
    """Save restart time"""
    db.restarts.update_one({}, {"$set": {"timestamp": timestamp}}, upsert=True)

def check_force_sub(user_id):
    """Check if user is subscribed to all force subscribe channels"""
    # This would require checking Telegram API to verify subscriptions
    # Placeholder implementation
    return True
