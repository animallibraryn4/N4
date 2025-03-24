from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["YourBotDatabase"]
force_sub_collection = db["force_subscription"]
