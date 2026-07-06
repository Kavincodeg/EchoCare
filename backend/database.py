import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import certifi

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "echocare")

_client: AsyncIOMotorClient = None
_db = None


async def connect_db():
    global _client, _db
    _client = AsyncIOMotorClient(MONGODB_URI, tlsCAFile=certifi.where())
    _db = _client[MONGODB_DB_NAME]
    # Verify connection
    await _client.admin.command("ping")
    print(f"[OK] Connected to MongoDB Atlas -- database: {MONGODB_DB_NAME}")


async def close_db():
    global _client
    if _client:
        _client.close()
        print("MongoDB connection closed")


def get_db():
    return _db
