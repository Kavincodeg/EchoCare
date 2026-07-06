import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import certifi

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "EchoCare")

async def main():
    print("Connecting to MongoDB URI:", MONGODB_URI)
    print("Using Certifi CA file:", certifi.where())
    
    # Try connecting with certifi CA file
    client = AsyncIOMotorClient(MONGODB_URI, tlsCAFile=certifi.where())
    db = client[MONGODB_DB_NAME]
    
    try:
        await client.admin.command("ping")
        print("[SUCCESS] Connected successfully using certifi!")
        collections = await db.list_collection_names()
        print("Collections:", collections)
    except Exception as e:
        print("[ERROR] Connection failed:", e)
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
