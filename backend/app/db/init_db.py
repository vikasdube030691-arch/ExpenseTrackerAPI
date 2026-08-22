"""MongoDB schema/index initialization and migration script for ExpenseTrackerAPI.

Usage (from backend/, with the venv active):
    python -m app.db.init_db                # create collections + indexes only
    python -m app.db.init_db --with-samples  # also seed one sample document per collection
"""

import argparse
import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.db.collections import Collections
from app.db.indexes import create_all_indexes
from app.db.mongodb import close_mongo_connection, connect_to_mongo, mongodb
from app.db.sample_data import build_sample_documents

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def ensure_collections(database: AsyncIOMotorDatabase) -> None:
    existing = await database.list_collection_names()
    for name in Collections.all():
        if name not in existing:
            await database.create_collection(name)
            logger.info("Created collection '%s'", name)


async def seed_sample_documents(database: AsyncIOMotorDatabase) -> None:
    documents = build_sample_documents()
    for collection_name, docs in documents.items():
        if not docs:
            continue
        await database[collection_name].delete_many({"_seed": True})
        await database[collection_name].insert_many(docs)
        logger.info("Inserted %d sample document(s) into '%s'", len(docs), collection_name)


async def init_database(*, with_samples: bool = False) -> None:
    await connect_to_mongo()
    database = mongodb.database
    assert database is not None

    await ensure_collections(database)

    created = await create_all_indexes(database)
    for collection_name, names in created.items():
        logger.info("Indexes on '%s': %s", collection_name, ", ".join(names))

    if with_samples:
        await seed_sample_documents(database)

    await close_mongo_connection()


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize the ExpenseTrackerAPI MongoDB database")
    parser.add_argument(
        "--with-samples", action="store_true", help="Insert one sample document per collection"
    )
    args = parser.parse_args()

    logger.info("Initializing database '%s' at %s", settings.mongodb_db_name, settings.mongodb_uri)
    asyncio.run(init_database(with_samples=args.with_samples))
    logger.info("Database initialization complete")


if __name__ == "__main__":
    main()
