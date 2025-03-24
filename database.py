from pymongo import MongoClient
from typing import Optional, List, Dict
import time

class Database:
    def __init__(self, db_uri: str):
        self.client = MongoClient(db_uri)
        self.db = self.client.telegram_link_bot
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes"""
        self.db.links.create_index("link_id", unique=True)
        self.db.links.create_index("expire_time", expireAfterSeconds=0)
        self.db.channels.create_index("channel_id", unique=True)
    
    # Link methods
    def save_link(self, link_id: str, original_link: str, user_id: int, expire_time: int) -> None:
        self.db.links.insert_one({
            "link_id": link_id,
            "original_link": original_link,
            "user_id": user_id,
            "created_at": time.time(),
            "expire_time": expire_time
        })
    
    def get_original_link(self, link_id: str) -> Optional[str]:
        link = self.db.links.find_one({"link_id": link_id})
        return link.get("original_link") if link else None
    
    # Channel methods
    def get_channels(self) -> List[Dict]:
        return list(self.db.channels.find({}, {"_id": 0}))
    
    def add_channel(self, channel_id: int, channel_link: str) -> bool:
        try:
            result = self.db.channels.update_one(
                {"channel_id": channel_id},
                {"$set": {"channel_link": channel_link, "added_at": time.time()}},
                upsert=True
            )
            return result.acknowledged
        except:
            return False
    
    def remove_channel(self, channel_id: int) -> bool:
        result = self.db.channels.delete_one({"channel_id": channel_id})
        return result.deleted_count > 0
    
    # Other methods
    def check_force_sub(self, user_id: int) -> bool:
        """Placeholder - implement actual Telegram API check"""
        return True

# Initialize in bot.py
db = None
