# MIT-0 License
#
# Copyright (c) 2025 Elevate Human Experiences, LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# MIT License
#
# Copyright (c) 2025 Elevate Human Experiences, LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Database helpers for MongoDB and Redis connections."""

import os
import logging
from typing import Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import redis.asyncio as redis

logger = logging.getLogger(__name__)

MONGODB_CONNECTION = os.environ.get("MONGODB_CONNECTION_STRING", "mongodb://mongodb:27017")
REDIS_CONNECTION = os.environ.get("REDIS_CONNECTION_STRING", "redis://redis:6379")
DB_NAME = os.environ.get("DB_NAME", "chatbot")


class DatabaseHelper:
    """Static helper for MongoDB and Redis connections."""

    _mongo_client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None
    _redis_cache: Optional[redis.Redis] = None

    @staticmethod
    def get_connection_strings() -> tuple[str, str, str]:
        """Get connection strings from environment variables."""
        return MONGODB_CONNECTION, REDIS_CONNECTION, DB_NAME

    @staticmethod
    def get_collection(collection_name: str) -> Any:
        """Get a collection from the MongoDB database asynchronously."""
        if DatabaseHelper._db is None:
            mongodb_connection, _, db_name = DatabaseHelper.get_connection_strings()

            logger.info("Connecting to MongoDB at %s", mongodb_connection)
            DatabaseHelper._mongo_client = AsyncIOMotorClient(mongodb_connection)
            DatabaseHelper._db = DatabaseHelper._mongo_client[db_name]

        if DatabaseHelper._db is None:
            raise RuntimeError("Failed to initialize MongoDB database connection")

        return DatabaseHelper._db.get_collection(collection_name)

    @staticmethod
    def get_cache() -> redis.Redis:
        """Get a shared Redis cache connection."""
        if DatabaseHelper._redis_cache is None:
            _, redis_connection, _ = DatabaseHelper.get_connection_strings()

            logger.info("Connecting to Redis at %s", redis_connection)
            DatabaseHelper._redis_cache = redis.from_url(redis_connection, decode_responses=True)

        if DatabaseHelper._redis_cache is None:
            raise RuntimeError("Failed to initialize Redis cache connection")

        return DatabaseHelper._redis_cache

    @staticmethod
    async def close_connections():
        """Close all database connections."""
        if DatabaseHelper._mongo_client:
            DatabaseHelper._mongo_client.close()
            DatabaseHelper._mongo_client = None
            DatabaseHelper._db = None
            logger.info("MongoDB connection closed")

        if DatabaseHelper._redis_cache:
            await DatabaseHelper._redis_cache.aclose()
            DatabaseHelper._redis_cache = None
            logger.info("Redis connection closed")

    @staticmethod
    async def health_check() -> dict[str, bool]:
        """Check the health of database connections."""
        health_status = {"mongodb": False, "redis": False}

        # Check MongoDB
        try:
            if DatabaseHelper._mongo_client:
                await DatabaseHelper._mongo_client.admin.command("ping")
                health_status["mongodb"] = True
            else:
                # Try to create a new connection for health check
                mongodb_connection, _, _ = DatabaseHelper.get_connection_strings()
                client = None
                try:
                    client = AsyncIOMotorClient(mongodb_connection)
                    await client.admin.command("ping")
                    health_status["mongodb"] = True
                finally:
                    if client:
                        client.close()
        except Exception as e:
            logger.warning("MongoDB health check failed: %s", e)

        # Check Redis
        try:
            cache = DatabaseHelper.get_cache()
            if cache:
                await cache.ping()
                health_status["redis"] = True
        except Exception as e:
            logger.warning("Redis health check failed: %s", e)

        return health_status
