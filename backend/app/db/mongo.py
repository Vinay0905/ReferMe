import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings

logger = logging.getLogger(__name__)


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


db_context = MongoDB()


async def connect_to_mongo():
    settings = get_settings()
    logger.info("Connecting to MongoDB...")
    db_context.client = AsyncIOMotorClient(
        settings.MONGODB_URI,
        serverSelectionTimeoutMS=5000
    )
    try:
        # Verify connection
        await db_context.db.command("ping")
        logger.info(f"Connected to MongoDB database: {settings.MONGODB_DB_NAME}")
    except Exception as exc:
        logger.error(
            f"Failed to connect to MongoDB at '{settings.MONGODB_URI}': {exc}. "
            "Please check MONGODB_URI in your .env file and ensure your MongoDB Atlas cluster is active "
            "and your IP address is whitelisted in Atlas Network Access."
        )
        raise exc


async def close_mongo_connection():
    if db_context.client:
        logger.info("Closing MongoDB connection...")
        db_context.client.close()
        logger.info("MongoDB connection closed.")


def get_database() -> AsyncIOMotorDatabase:
    if db_context.db is None:
        raise RuntimeError("Database is not initialized. Call connect_to_mongo first.")
    return db_context.db
