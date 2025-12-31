#!/usr/bin/env python3
"""
Vector Store Migration Script

Migrates existing diary entries to vector store for semantic search.
Run this once after setting up VDB+RAG to index existing memory.

Usage:
    python -m anm.system.vector_migration --diary anm_diary.txt
    python -m anm.system.vector_migration --diary anm_diary.txt --batch-size 50 --dry-run
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_diary_to_vector_store(
    diary_path: str,
    batch_size: int = 100,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Migrate existing diary entries to vector store.

    Args:
        diary_path: Path to diary file
        batch_size: Entries to process per batch
        dry_run: If True, don't actually write to vector store

    Returns:
        Migration statistics
    """
    try:
        from anm.memory.diary_memory import DiaryMemory
        from anm.memory.vector_store import VectorStore
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        return {"error": str(e)}

    # Validate diary file
    diary_file = Path(diary_path)
    if not diary_file.exists():
        logger.error(f"Diary file not found: {diary_path}")
        return {"error": f"File not found: {diary_path}"}

    logger.info(f"Starting migration of diary: {diary_path}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Dry run: {dry_run}")

    # Initialize diary (with vector search DISABLED to avoid circular indexing)
    diary = DiaryMemory(diary_path=diary_path, enable_vector_search=False)

    # Initialize vector store manually
    collection_name = f"diary_{diary_file.stem}"
    vector_store = VectorStore(collection_name=collection_name)

    if not vector_store.is_available():
        logger.error("Vector store not available. Install ChromaDB: pip install chromadb")
        return {"error": "Vector store unavailable"}

    # Get all diary blocks
    logger.info("Reading diary blocks...")
    blocks = diary._split_blocks()
    total_blocks = len(blocks)

    logger.info(f"Found {total_blocks} diary entries")

    if dry_run:
        logger.info("DRY RUN - No changes will be made")

    # Process in batches
    processed = 0
    indexed = 0
    failed = 0

    for i in range(0, total_blocks, batch_size):
        batch = blocks[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        logger.info(f"Processing batch {batch_num}/{(total_blocks + batch_size - 1) // batch_size}")

        for block in batch:
            try:
                # Parse metadata
                meta = diary._parse_block_meta(block)

                # Skip if empty
                if not meta.get("raw"):
                    continue

                # Prepare metadata for vector store
                metadata = {
                    "kind": meta.get("kind") or "",
                    "specialist": meta.get("specialist") or "",
                    "timestamp": meta.get("timestamp") or "",
                    "tags": ",".join(meta.get("tags", [])),
                    "title": meta.get("title") or "",
                }

                # Add to vector store
                if not dry_run:
                    doc_ids = vector_store.add(
                        text=meta["raw"],
                        metadata=metadata,
                        chunk_size=512,
                    )

                    if doc_ids:
                        indexed += len(doc_ids)
                    else:
                        failed += 1
                else:
                    # Dry run: just count
                    indexed += 1

                processed += 1

                # Progress update
                if processed % 50 == 0:
                    logger.info(f"Progress: {processed}/{total_blocks} entries processed")

            except Exception as e:
                logger.error(f"Failed to process entry: {e}")
                failed += 1

    # Final statistics
    stats = {
        "total_entries": total_blocks,
        "processed": processed,
        "indexed_chunks": indexed,
        "failed": failed,
        "dry_run": dry_run,
    }

    logger.info("=" * 60)
    logger.info("MIGRATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total entries: {stats['total_entries']}")
    logger.info(f"Processed: {stats['processed']}")
    logger.info(f"Indexed chunks: {stats['indexed_chunks']}")
    logger.info(f"Failed: {stats['failed']}")

    if dry_run:
        logger.info("\nThis was a DRY RUN - no changes were made")
        logger.info("Run without --dry-run to perform actual migration")
    else:
        logger.info(f"\nVector store count: {vector_store.count()}")

    return stats


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Migrate existing diary entries to vector store"
    )
    parser.add_argument(
        "--diary",
        type=str,
        default="anm_diary.txt",
        help="Path to diary file (default: anm_diary.txt)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Entries to process per batch (default: 100)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run - don't actually write to vector store"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run migration
    stats = migrate_diary_to_vector_store(
        diary_path=args.diary,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    )

    # Exit with error code if failed
    if "error" in stats:
        sys.exit(1)

    if stats.get("failed", 0) > 0:
        logger.warning(f"Migration completed with {stats['failed']} failures")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
