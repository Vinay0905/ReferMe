import argparse
import asyncio
import logging
import sys
from app.db.indexes import create_indexes
from app.db.mongo import close_mongo_connection, connect_to_mongo
from app.ingestion.orchestrator import IngestionOrchestrator
from app.integrations.allen.client import AllenClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger("referme.cli")


async def run_ingest(args):
    print("=" * 65)
    print("ALLEN NEET Test ↔ Topic Intelligence System: Ingestion Runner")
    print("=" * 65)

    await connect_to_mongo()
    await create_indexes()

    mock_mode = None
    if args.mock:
        mock_mode = True
    elif args.live:
        mock_mode = False

    client = AllenClient(mock_mode=mock_mode)
    print(f"Mode: {'MOCK (Offline Fixtures)' if client.mock_mode else 'LIVE (api.allen-live.in)'}")
    print(f"Status Filter: {args.status}")
    print(f"Mode Filter: {args.mode}")
    if args.limit:
        print(f"Test Limit: {args.limit}")
    print("-" * 65)

    orchestrator = IngestionOrchestrator(allen_client=client)
    job = await orchestrator.run(
        status=args.status,
        mode=args.mode,
        max_tests=args.limit
    )

    print("-" * 65)
    print(f"Ingestion Job Completed!")
    print(f"Job ID: {job.id}")
    print(f"Final Status: {job.status.value}")
    print(f"Tests Discovered: {job.discovered_count}")
    print(f"Tests Succeeded: {job.succeeded_count}")
    print(f"Tests Partial: {job.partial_count}")
    print(f"Tests Failed: {job.failed_count}")
    if job.error_summary:
        print("\nErrors encountered:")
        for err in job.error_summary:
            print(f"  - {err}")
    print("=" * 65)

    await close_mongo_connection()


async def run_reset_db(args):
    print("=" * 65)
    print("Resetting Database (Clearing all documents while preserving schema)")
    print("=" * 65)

    from app.db.mongo import get_database
    await connect_to_mongo()
    db = get_database()

    collections = [
        "tests",
        "topics",
        "test_topics",
        "artifacts",
        "syllabus_snapshots",
        "ingestion_jobs"
    ]

    for col_name in collections:
        res = await db[col_name].delete_many({})
        print(f"  - Cleared {res.deleted_count} documents from collection '{col_name}'")

    print("\nRe-verifying indexes...")
    await create_indexes()

    if args.clear_storage:
        import shutil
        from pathlib import Path
        from app.config import get_settings
        storage_dir = Path(get_settings().LOCAL_STORAGE_DIR)
        if storage_dir.exists():
            for child in storage_dir.iterdir():
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
            print(f"  - Cleared downloaded files in {storage_dir}")

    print("\nDatabase successfully reset to clean state!")
    print("=" * 65)
    await close_mongo_connection()


def main():
    parser = argparse.ArgumentParser(description="ALLEN NEET CLI Management Commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Ingestion command
    ingest_parser = subparsers.add_parser("ingest", help="Run the test & syllabus ingestion pipeline")
    ingest_parser.add_argument("--limit", type=int, default=None, help="Maximum number of tests to process")
    ingest_parser.add_argument("--status", type=str, default="all", help="Test status filter (default: all)")
    ingest_parser.add_argument("--mode", type=str, default="all", help="Test mode filter (default: all)")

    mode_group = ingest_parser.add_mutually_exclusive_group()
    mode_group.add_argument("--mock", action="store_true", help="Force offline mock ingestion")
    mode_group.add_argument("--live", action="store_true", help="Force live API ingestion using .env credentials")

    # Reset DB command
    reset_parser = subparsers.add_parser("reset-db", help="Clear all documents from the database while keeping schema and indexes")
    reset_parser.add_argument("--clear-storage", action="store_true", help="Also clear locally downloaded PDF files in storage_data")

    args = parser.parse_args()

    if args.command == "ingest":
        asyncio.run(run_ingest(args))
    elif args.command == "reset-db":
        asyncio.run(run_reset_db(args))


if __name__ == "__main__":
    main()
