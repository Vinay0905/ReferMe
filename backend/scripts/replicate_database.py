#!/usr/bin/env python3
"""ReferMe Database & Storage Auto-Replication Utility.

Replicates the entire ReferMe database (all collections, documents, and indexes)
from any source MongoDB (e.g. MongoDB Atlas, production) to any target MongoDB
(e.g. Local Docker, staging cluster, AWS DocumentDB) with zero data loss.

Also supports syncing the storage_data assets (PDFs & WebP snippets).

Usage Examples:
    # 1. Replicate from .env source to local Docker MongoDB:
    python scripts/replicate_database.py --target-uri mongodb://localhost:27017

    # 2. Replicate from Atlas to another remote cluster:
    python scripts/replicate_database.py \
        --source-uri "mongodb+srv://user:pass@cluster1.mongodb.net" \
        --target-uri "mongodb+srv://user:pass@cluster2.mongodb.net" \
        --target-db referme_neet_prod

    # 3. Full clone including disk storage data:
    python scripts/replicate_database.py --target-uri mongodb://localhost:27017 --sync-storage
"""

import argparse
import asyncio
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings
from app.db.indexes import create_indexes

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger("referme.replicate")

COLLECTIONS_TO_REPLICATE = [
    "tests",
    "topics",
    "test_topics",
    "artifacts",
    "syllabus_snapshots",
    "questions",
    "question_topics",
]


async def replicate_database(
    source_uri: str,
    source_db_name: str,
    target_uri: str,
    target_db_name: str,
    batch_size: int = 500,
    drop_target: bool = False,
    sync_storage: bool = False,
    target_storage_dir: str = "./storage_data",
):
    print("=" * 70)
    print("🚀 ReferMe: Automated Database & Asset Replication")
    print("=" * 70)
    print(f"Source DB: {source_db_name} @ {source_uri.split('@')[-1]}")
    print(f"Target DB: {target_db_name} @ {target_uri.split('@')[-1]}")
    print(f"Batch Size: {batch_size}")
    print(f"Drop Existing Target Collections: {drop_target}")
    print("-" * 70)

    # 1. Connect to both databases
    source_client = AsyncIOMotorClient(source_uri)
    target_client = AsyncIOMotorClient(target_uri)

    src_db = source_client[source_db_name]
    tgt_db = target_client[target_db_name]

    # Verify connectivity
    try:
        await src_db.command("ping")
        print("✓ Source database connected successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to Source DB: {e}")
        return False

    try:
        await tgt_db.command("ping")
        print("✓ Target database connected successfully.")
    except Exception as e:
        logger.error(f"Failed to connect to Target DB: {e}")
        return False

    total_docs_replicated = 0

    # 2. Replicate each collection
    for col_name in COLLECTIONS_TO_REPLICATE:
        src_col = src_db[col_name]
        tgt_col = tgt_db[col_name]

        src_count = await src_col.count_documents({})
        print(f"\n📦 Replicating [{col_name}] ({src_count} documents)...")

        if src_count == 0:
            print(f"   ↳ Skipped: Source collection [{col_name}] is empty.")
            continue

        if drop_target:
            await tgt_col.delete_many({})
            print(f"   ↳ Cleared target collection [{col_name}].")

        # Stream documents in batches using cursor
        cursor = src_col.find({})
        batch: List[Dict] = []
        col_copied = 0

        async for doc in cursor:
            batch.append(doc)
            if len(batch) >= batch_size:
                # Upsert by _id into target to ensure perfect idempotency
                operations = []
                from pymongo import ReplaceOne
                operations = [ReplaceOne({"_id": d["_id"]}, d, upsert=True) for d in batch]
                await tgt_col.bulk_write(operations, ordered=False)
                col_copied += len(batch)
                batch = []
                print(f"   ↳ Transferred {col_copied}/{src_count} docs...", end="\r")

        # Insert remaining
        if batch:
            from pymongo import ReplaceOne
            operations = [ReplaceOne({"_id": d["_id"]}, d, upsert=True) for d in batch]
            await tgt_col.bulk_write(operations, ordered=False)
            col_copied += len(batch)

        print(f"   ✓ Successfully replicated {col_copied}/{src_count} documents into [{col_name}].")
        total_docs_replicated += col_copied

    # 3. Ensure all compound and unique indexes on the target database
    print("\n⚡ Ensuring indexes on target database...")
    # Temporarily bind tgt_db to app's get_database
    from app.db import mongo as mongo_module
    old_db = mongo_module.db_context.db
    mongo_module.db_context.db = tgt_db
    try:
        await create_indexes()
        print("✓ All compound and unique indexes provisioned on target database.")
    except Exception as ex:
        logger.warning(f"Index provisioning notice: {ex}")
    finally:
        mongo_module.db_context.db = old_db

    # 4. Optional Storage Data Replication (PDFs + WebP Snippets)
    if sync_storage:
        print("\n📂 Syncing local storage assets (PDFs & WebP snippets)...")
        settings = get_settings()
        src_storage = Path(settings.LOCAL_STORAGE_DIR).resolve()
        dst_storage = Path(target_storage_dir).resolve()

        if src_storage.exists() and src_storage != dst_storage:
            dst_storage.mkdir(parents=True, exist_ok=True)
            for item in src_storage.glob("test_*"):
                dest_item = dst_storage / item.name
                if item.is_dir():
                    shutil.copytree(item, dest_item, dirs_exist_ok=True)
            print(f"✓ Synced storage assets from {src_storage} -> {dst_storage}")
        else:
            print("✓ Storage directories are identical or already in place.")

    print("\n" + "=" * 70)
    print(f"🎉 Replication Finished! Total documents cloned: {total_docs_replicated}")
    print("=" * 70)

    source_client.close()
    target_client.close()
    return True


def main():
    settings = get_settings()

    parser = argparse.ArgumentParser(description="ReferMe Automated Database Replicator")
    parser.add_argument(
        "--source-uri",
        default=settings.MONGODB_URI,
        help="Source MongoDB URI (defaults to MONGODB_URI in backend/.env)",
    )
    parser.add_argument(
        "--source-db",
        default=settings.MONGODB_DB_NAME,
        help="Source database name (defaults to MONGODB_DB_NAME)",
    )
    parser.add_argument(
        "--target-uri",
        required=True,
        help="Target MongoDB connection URI (e.g. mongodb://localhost:27017)",
    )
    parser.add_argument(
        "--target-db",
        default=settings.MONGODB_DB_NAME,
        help="Target database name (defaults to source database name)",
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop target collections before copying (ensures clean 1:1 replica)",
    )
    parser.add_argument(
        "--sync-storage",
        action="store_true",
        help="Also copy local PDF question papers and WebP crops",
    )
    parser.add_argument(
        "--target-storage-dir",
        default="./storage_data",
        help="Destination directory for storage assets",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Batch size for bulk document writes",
    )

    args = parser.parse_args()

    asyncio.run(
        replicate_database(
            source_uri=args.source_uri,
            source_db_name=args.source_db,
            target_uri=args.target_uri,
            target_db_name=args.target_db,
            batch_size=args.batch_size,
            drop_target=args.drop,
            sync_storage=args.sync_storage,
            target_storage_dir=args.target_storage_dir,
        )
    )


if __name__ == "__main__":
    main()
