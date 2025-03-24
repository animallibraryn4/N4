from config import Config
from pymongo import MongoClient, ReturnDocument
from typing import Optional, List, Dict
import time

class Database:
    def __init__(self):
        self.client = MongoClient(Config.DB_URI)
        self.db = self.client.telegram_link_bot
        
        # Create indexes for faster queries
        self._create_indexes()
    
    def _create_indexes(self):
        """Create necessary database indexes"""
        self.db.links.create_index("link_id", unique=True)
        self.db.links.create_index("expire_time", expireAfterSeconds=0)
        self.db.channels.create_index("channel_id", unique=True)
    
    # Link Management
    def save_link(self, link_id: str, original_link: str, user_id: int, expire_time: int) -> None:
        """Save generated link to database"""
        self.db.links.insert_one({
            "link_id": link_id,
            "original_link": original_link,
            "user_id": user_id,
            "created_at": time.time(),
            "expire_time": expire_time
        })
    
    def get_original_link(self, link_id: str) -> Optional[str]:
        """Get original link from database"""
        link = self.db.links.find_one({"link_id": link_id})
        return link.get("original_link") if link else None
    
    # Channel Management
    def get_channels(self) -> List[Dict]:
        """Get all force subscribe channels"""
        return list(self.db.channels.find({}, {"_id": 0}))
    
    def add_channel(self, channel_id: int, channel_link: str) -> bool:
        """Add a new force subscribe channel"""
        try:
            result = self.db.channels.update_one(
                {"channel_id": channel_id},
                {"$set": {
                    "channel_link": channel_link,
                    "added_at": time.time()
                }},
                upsert=True
            )
            return result.acknowledged
        except:
            return False
    
    def remove_channel(self, channel_id: int) -> bool:
        """Remove a force subscribe channel"""
        result = self.db.channels.delete_one({"channel_id": channel_id})
        return result.deleted_count > 0
    
    # Restart Management
    def get_last_restart(self) -> Optional[float]:
        """Get last restart time"""
        restart = self.db.restarts.find_one({})
        return restart.get("timestamp") if restart else None
    
    def save_last_restart(self, timestamp: float) -> None:
        """Save restart time"""
        self.db.restarts.update_one(
            {},
            {"$set": {"timestamp": timestamp}},
            upsert=True
        )
    
    # Subscription Verification
    def check_force_sub(self, user_id: int) -> bool:
        """
        Check if user is subscribed to all force subscribe channels
        Note: Actual Telegram API check should be implemented separately
        """
        # Placeholder - implement actual check with Telegram API
        return True
    
    # User Management
    def add_user(self, user_id: int, username: str = None) -> None:
        """Add or update user in database"""
        self.db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "username": username,
                "last_seen": time.time()
            }},
            upsert=True
        )
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user data from database"""
        return self.db.users.find_one({"user_id": user_id}, {"_id": 0})

# Initialize database instance
db = Database()
