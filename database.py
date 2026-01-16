import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger

# Try to import motor, fall back to synchronous pymongo
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    MOTOR_AVAILABLE = True
except ImportError:
    logger.warning("Motor not available, falling back to pymongo")
    MOTOR_AVAILABLE = False
    import pymongo

from config import config

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.collections = {}
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            if MOTOR_AVAILABLE:
                self.client = AsyncIOMotorClient(
                    config.DATABASE_URL,
                    serverSelectionTimeoutMS=5000
                )
                # Test connection
                await self.client.admin.command('ping')
                self.db = self.client[config.DATABASE_NAME]
            else:
                # Fall back to synchronous pymongo
                import pymongo
                self.client = pymongo.MongoClient(config.DATABASE_URL)
                self.client.admin.command('ping')  # Test connection
                self.db = self.client[config.DATABASE_NAME]
            
            # Initialize collections
            self.collections = {
                'last_added': self.db['last_added'],
                'remain': self.db['remain'],
                'worker': self.db['worker'],
                'files': self.db['files']
            }
            
            # Initialize database
            await self._initialize_database()
            
            logger.info("Database connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    async def _initialize_database(self):
        """Initialize database with required documents"""
        # Ensure collections have required documents
        collections_to_init = ['last_added', 'worker', 'remain']
        
        for collection_name in collections_to_init:
            coll = self.collections[collection_name]
            
            # Check if document exists
            if collection_name == 'last_added':
                doc = await self._find_one(coll, {"_id": 1})
                if not doc:
                    await self._insert_one(coll, {"_id": 1, "hash": None})
            
            elif collection_name == 'worker':
                doc = await self._find_one(coll, {"_id": 1})
                if not doc:
                    await self._insert_one(coll, {"_id": 1, "working": False})
            
            elif collection_name == 'remain':
                doc = await self._find_one(coll, {"_id": 1})
                if not doc:
                    await self._insert_one(coll, {"_id": 1, "list": []})
    
    async def _find_one(self, collection, query):
        """Find one document with async/sync support"""
        if MOTOR_AVAILABLE:
            return await collection.find_one(query)
        else:
            return collection.find_one(query)
    
    async def _insert_one(self, collection, document):
        """Insert one document with async/sync support"""
        if MOTOR_AVAILABLE:
            return await collection.insert_one(document)
        else:
            return collection.insert_one(document)
    
    async def _update_one(self, collection, query, update):
        """Update one document with async/sync support"""
        if MOTOR_AVAILABLE:
            return await collection.update_one(query, update, upsert=True)
        else:
            return collection.update_one(query, update, upsert=True)
    
    async def get_last_hash(self) -> Optional[str]:
        """Get last processed RSS hash"""
        doc = await self._find_one(self.collections['last_added'], {"_id": 1})
        return doc.get("hash") if doc else None
    
    async def update_last_hash(self, hash_value: str):
        """Update last hash"""
        await self._update_one(
            self.collections['last_added'],
            {"_id": 1},
            {"$set": {"hash": hash_value}}
        )
    
    async def add_remaining_anime(self, anime_list: List[Dict]):
        """Add anime to queue"""
        current = await self._find_one(self.collections['remain'], {"_id": 1})
        if current:
            current_list = current.get("list", [])
            current_list.extend(anime_list)
            await self._update_one(
                self.collections['remain'],
                {"_id": 1},
                {"$set": {"list": current_list}}
            )
        else:
            await self._insert_one(self.collections['remain'], {
                "_id": 1,
                "list": anime_list
            })
    
    async def get_remaining_anime(self) -> List[Dict]:
        """Get anime queue"""
        doc = await self._find_one(self.collections['remain'], {"_id": 1})
        return doc.get("list", []) if doc else []
    
    async def update_remaining_anime(self, anime_list: List[Dict]):
        """Update anime queue"""
        await self._update_one(
            self.collections['remain'],
            {"_id": 1},
            {"$set": {"list": anime_list}}
        )
    
    async def is_worker_busy(self) -> bool:
        """Check if worker is busy"""
        doc = await self._find_one(self.collections['worker'], {"_id": 1})
        return doc.get("working", False) if doc else False
    
    async def set_worker_status(self, busy: bool):
        """Set worker status"""
        await self._update_one(
            self.collections['worker'],
            {"_id": 1},
            {"$set": {"working": busy}}
        )
    
    async def add_file_record(self, name: str, file_hash: str, message_id: int):
        """Add file to database"""
        await self._insert_one(self.collections['files'], {
            "name": name,
            "hash": file_hash,
            "message_id": message_id,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def get_file_by_hash(self, file_hash: str) -> Optional[Dict]:
        """Get file by hash"""
        return await self._find_one(self.collections['files'], {"hash": file_hash})
    
    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            return await self.connect()
        except Exception as e:
            logger.error(f"Database test failed: {e}")
            return False
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")

# Global async database instance
db = Database()
