# ============================================================
# ANM V0-OpenSource — CLOUD DIARY V0-OpenSource MAX
#  LawBook V0-OpenSource Compliant • PAST-ONLY Memory • Full Meta Support
#  Safe Storage for:
#     - LFM Learning Entries
#     - Router Plans
#     - Verifier Snapshots
#     - Observations / Ideas / System Notes
# ============================================================

from __future__ import annotations
from anm.utils.debug_logger import log_debug

import logging
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


# ============================================================
#  Constants
# ============================================================

DIARY_SEPARATOR = "──────────────────────────────────────────────"

DIARY_HEADER = textwrap.dedent(
    """\
    ============================================================
      ANM CLOUD DIARY (V0-OpenSource MAX)
      LawBook V0-OpenSource Compliant • PAST-ONLY Narrative Memory
      This diary stores ANM's PAST experiences and reasoning traces.
      It is NOT guaranteed truth. It is NOT the real world.
      All entries must be interpreted as historical context only.
    ============================================================
    """
)


# ============================================================
#  Unified Diary Entry Object
# ============================================================

@dataclass
class DiaryEntry:
    timestamp: str
    kind: str                          # interaction | observation | idea | system | learning
    specialist: Optional[str] = None
    run_id: Optional[str] = None
    tags: Optional[List[str]] = None
    title: Optional[str] = None

    # content fields
    user: Optional[str] = None
    assistant: Optional[str] = None
    notes: Optional[str] = None

    # Additional metadata
    extra: Optional[Dict[str, Any]] = None


# ============================================================
#  Diary Memory Implementation
# ============================================================

class DiaryMemory:
    """
    CLOUD DIARY V0-OpenSource MAX — Append-only, human-readable,
    LawBook V0-OpenSource compliant, and designed for:

        - LFM learning logs
        - Router plans
        - Verifier summaries
        - Past interactions
        - High-level CoT summaries (NOT full CoTs)
        - Observations + internal ideas

    Never treated as truth; always "In the past, ANM..."
    """

    def __init__(
        self,
        diary_path: str | Path = "anm_diary.txt",
        enable_vector_search: bool = True,
    ) -> None:
        self.diary_path = Path(diary_path)
        self._ensure_header()

        # Vector search support (optional, graceful fallback)
        self._vector_enabled = enable_vector_search
        self._vector_store = None
        if enable_vector_search:
            self._init_vector_store()

    # --------------------------------------------------------
    #  Vector Store Initialization
    # --------------------------------------------------------

    def _init_vector_store(self) -> None:
        """Initialize vector store for semantic search (graceful fallback)."""
        try:
            from anm.memory.vector_store import VectorStore

            collection_name = f"diary_{self.diary_path.stem}"
            self._vector_store = VectorStore(collection_name=collection_name)

            if self._vector_store.is_available():
                logger.info(f"Vector search enabled for diary: {self.diary_path}")
            else:
                logger.warning("Vector store unavailable, falling back to keyword search")
                self._vector_enabled = False

        except Exception as e:
            logger.warning(f"Failed to initialize vector store: {e}. Using keyword search only.")
            self._vector_enabled = False

    # --------------------------------------------------------
    #  Initial Diary Header
    # --------------------------------------------------------

    def _ensure_header(self) -> None:
        """Ensure header exists; create file if missing."""
        if not self.diary_path.exists() or self.diary_path.stat().st_size == 0:
            self.diary_path.parent.mkdir(parents=True, exist_ok=True)
            with self.diary_path.open("w", encoding="utf-8") as f:
                f.write(DIARY_HEADER.strip() + "\n\n")
                f.write(f"# Diary created (UTC): {self._now_iso()}\n\n")

    @staticmethod
    def _now_iso() -> str:
        """UTC timestamp."""
        return datetime.now(timezone.utc).isoformat()


    # ============================================================
    #  Public Logging APIs
    # ============================================================

    def log_interaction(
        self,
        *,
        user_query: str,
        assistant_reply: str,
        specialist: Optional[str] = None,
        run_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
        title: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log full user ↔ assistant interaction."""
        # #region agent log
        try:
            import json
            import time
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "M3", "location": "diary_memory.py:log_interaction", "message": "log_interaction called", "data": {"diary_path": str(self.diary_path), "user_query": user_query[:100], "assistant_reply_length": len(assistant_reply)}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
        entry = DiaryEntry(
            timestamp=self._now_iso(),
            kind="interaction",
            specialist=specialist,
            run_id=run_id,
            tags=tags or [],
            title=title or "User–Assistant Interaction",
            user=user_query[:1000],
            assistant=assistant_reply[:2000],
            notes=notes,
            extra=extra or {},
        )
        self._append_entry(entry)


    def log_observation(
        self,
        *,
        text: str,
        specialist: Optional[str] = None,
        run_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        title: Optional[str] = "Observation",
        notes: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """General internal observation (meta, behaviour, cross-domain patterns)."""
        entry = DiaryEntry(
            timestamp=self._now_iso(),
            kind="observation",
            specialist=specialist,
            run_id=run_id,
            tags=tags or [],
            title=title,
            assistant=text.strip()[:2000],
            notes=notes,
            extra=extra or {},
        )
        self._append_entry(entry)


    def log_idea(
        self,
        *,
        idea: str,
        specialist: Optional[str] = None,
        tags: Optional[List[str]] = None,
        run_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
    ) -> None:
        """Log design thought, innovation, or future plan seed."""
        entry = DiaryEntry(
            timestamp=self._now_iso(),
            kind="idea",
            specialist=specialist,
            run_id=run_id,
            tags=tags or [],
            title="Idea",
            assistant=idea.strip()[:2000],
            notes=notes,
            extra=extra or {},
        )
        self._append_entry(entry)


    def log_system(
        self,
        *,
        message: str,
        tags: Optional[List[str]] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """System-level note (boot, upgrade, migration)."""
        entry = DiaryEntry(
            timestamp=self._now_iso(),
            kind="system",
            specialist="SYSTEM",
            tags=tags or [],
            title="System Note",
            assistant=message,
            extra=extra or {},
        )
        self._append_entry(entry)


    def log_learning(
        self,
        *,
        learning_entry: str,
        specialist: Optional[str] = "LFM",
        tags: Optional[List[str]] = None,
        run_id: Optional[str] = None,
        notes: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        NEW: Dedicated storage for LFM learning entries.
        (Completely LawBook V0-OpenSource compliant and PAST-ONLY)
        """
        entry = DiaryEntry(
            timestamp=self._now_iso(),
            kind="learning",
            specialist=specialist,
            run_id=run_id,
            tags=tags or ["lfm", "learning"],
            title="Learning Entry (LFM)",
            assistant=learning_entry.strip()[:5000],
            notes=notes,
            extra=extra or {},
        )
        self._append_entry(entry)


    # ============================================================
    #  Append + Render
    # ============================================================

    def _append_entry(self, entry: DiaryEntry) -> None:
        # #region agent log
        try:
            import json
            import time
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "M4", "location": "diary_memory.py:_append_entry", "message": "_append_entry called", "data": {"diary_path": str(self.diary_path), "entry_kind": entry.kind, "entry_timestamp": entry.timestamp}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
        block = self._render_entry(entry)
        try:
            with self.diary_path.open("a", encoding="utf-8") as f:
                f.write(DIARY_SEPARATOR + "\n")
                f.write(block)
                f.write("\n\n")

            # Index in vector store (non-blocking)
            if self._vector_enabled and self._vector_store:
                self._index_entry_in_vector_store(entry, block)

            # #region agent log
            try:
                import json
                import time
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "M4", "location": "diary_memory.py:_append_entry", "message": "_append_entry succeeded", "data": {"diary_path": str(self.diary_path), "file_size_after": self.diary_path.stat().st_size if self.diary_path.exists() else 0}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
        except Exception as e:
            # #region agent log
            try:
                import json
                import time
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "M4", "location": "diary_memory.py:_append_entry", "message": "_append_entry failed", "data": {"error_type": type(e).__name__, "error_msg": str(e)[:200], "diary_path": str(self.diary_path)}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
            raise

    def _index_entry_in_vector_store(self, entry: DiaryEntry, block: str) -> None:
        """
        Index diary entry in vector store (non-blocking, graceful fallback).

        Args:
            entry: DiaryEntry object
            block: Rendered text block
        """
        try:
            # Prepare metadata for vector store
            metadata = {
                "kind": entry.kind or "",
                "specialist": entry.specialist or "",
                "timestamp": entry.timestamp or "",
                "tags": ",".join(entry.tags) if entry.tags else "",
                "title": entry.title or "",
            }

            # Add optional fields
            if entry.run_id:
                metadata["run_id"] = entry.run_id

            # Add to vector store
            self._vector_store.add(
                text=block,
                metadata=metadata,
                chunk_size=512,  # Chunk large entries
            )

        except Exception as e:
            # Non-critical, log and continue
            logger.debug(f"Failed to index entry in vector store: {e}")

    def _render_entry(self, e: DiaryEntry) -> str:
        lines: List[str] = []

        # Header
        lines.append(f"[ENTRY @ {e.timestamp}]")
        lines.append(f"TYPE: {e.kind}")
        if e.specialist:
            lines.append(f"SPECIALIST: {e.specialist}")
        if e.run_id:
            lines.append(f"RUN_ID: {e.run_id}")
        if e.tags:
            lines.append("TAGS: " + ", ".join(e.tags))
        if e.title:
            lines.append(f"TITLE: {e.title}")
        lines.append("")

        # Body
        if e.user:
            lines.append("USER:")
            lines.append(textwrap.indent(e.user.strip(), "  "))
            lines.append("")

        if e.assistant:
            label = "ASSISTANT:" if e.kind == "interaction" else "TEXT:"
            lines.append(label)
            lines.append(textwrap.indent(e.assistant.strip(), "  "))
            lines.append("")

        if e.notes:
            lines.append("NOTES:")
            lines.append(textwrap.indent(e.notes.strip(), "  "))
            lines.append("")

        if e.extra:
            lines.append("EXTRA:")
            for k, v in e.extra.items():
                lines.append(f"  - {k}: {v}")
            lines.append("")

        return "\n".join(lines).rstrip()


    # ============================================================
    #  Reading Helpers
    # ============================================================

    def _read_all(self) -> str:
        if not self.diary_path.exists():
            return ""
        return self.diary_path.read_text(encoding="utf-8")

    def _split_blocks(self) -> List[str]:
        text = self._read_all()
        if not text:
            return []
        return [b.strip() for b in text.split(DIARY_SEPARATOR) if b.strip()]

    def read_tail(self, max_chars: int = 4000) -> str:
        """Return last N chars (recent history context)."""
        if not self.diary_path.exists():
            return ""

        size = self.diary_path.stat().st_size
        start = max(0, size - max_chars)
        with self.diary_path.open("r", encoding="utf-8") as f:
            if start > 0:
                f.seek(start)
                f.readline()  # discard partial start line
            return f.read().strip()


    # ============================================================
    #  Advanced Search
    # ============================================================

    def _parse_block_meta(self, block: str) -> Dict[str, Any]:
        lines = block.splitlines()
        meta = {
            "timestamp": None,
            "kind": None,
            "specialist": None,
            "run_id": None,
            "tags": [],
            "title": None,
            "raw": block.strip(),
        }

        for ln in lines[:10]:
            s = ln.strip()
            if s.startswith("[ENTRY @"):
                meta["timestamp"] = s.replace("[ENTRY @", "").replace("]", "").strip()
            elif s.startswith("TYPE:"):
                meta["kind"] = s[5:].strip()
            elif s.startswith("SPECIALIST:"):
                meta["specialist"] = s[11:].strip()
            elif s.startswith("RUN_ID:"):
                meta["run_id"] = s[7:].strip()
            elif s.startswith("TAGS:"):
                tag_str = s[5:].strip()
                if tag_str:
                    meta["tags"] = [t.strip() for t in tag_str.split(",") if t.strip()]
            elif s.startswith("TITLE:"):
                meta["title"] = s[6:].strip()

        return meta


    def search(
        self,
        keyword: str,
        max_hits: int = 5,
    ) -> List[str]:
        """Legacy raw block search."""
        if not keyword.strip():
            return []
        lower = keyword.lower()
        blocks = self._split_blocks()

        hits = []
        for b in reversed(blocks):
            if lower in b.lower():
                hits.append(b)
            if len(hits) >= max_hits:
                break
        return hits


    def search_blocks(
        self,
        *,
        text_query: Optional[str] = None,
        kinds: Optional[List[str]] = None,
        specialists: Optional[List[str]] = None,
        any_tags: Optional[List[str]] = None,
        all_tags: Optional[List[str]] = None,
        limit: int = 10,
        use_semantic: bool = True,
        semantic_weight: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Advanced metadata search with optional semantic enhancement.

        Args:
            text_query: Text query string
            kinds: Filter by entry kinds
            specialists: Filter by specialists
            any_tags: Match any of these tags
            all_tags: Match all of these tags
            limit: Maximum results
            use_semantic: Enable semantic search (hybrid with keyword)
            semantic_weight: Weight for semantic results (0.0-1.0)

        Returns:
            List of matching diary entries with metadata
        """
        # ALWAYS perform keyword search (backward compatibility)
        keyword_results = self._keyword_search_blocks(
            text_query=text_query,
            kinds=kinds,
            specialists=specialists,
            any_tags=any_tags,
            all_tags=all_tags,
            limit=limit * 2,  # Get more candidates for merging
        )

        # Semantic enhancement if enabled and available
        if use_semantic and self._vector_enabled and self._vector_store and text_query:
            try:
                semantic_results = self._semantic_search_blocks(
                    text_query=text_query,
                    kinds=kinds,
                    specialists=specialists,
                    any_tags=any_tags,
                    all_tags=all_tags,
                    limit=limit * 2,
                )

                # Merge using hybrid search
                merged_results = self._merge_search_results(
                    keyword_results=keyword_results,
                    semantic_results=semantic_results,
                    semantic_weight=semantic_weight,
                )

                return merged_results[:limit]

            except Exception as e:
                logger.warning(f"Semantic search failed, falling back to keyword: {e}")
                # Fallback to keyword results
                return keyword_results[:limit]

        # Return keyword results only
        return keyword_results[:limit]

    def _keyword_search_blocks(
        self,
        *,
        text_query: Optional[str] = None,
        kinds: Optional[List[str]] = None,
        specialists: Optional[List[str]] = None,
        any_tags: Optional[List[str]] = None,
        all_tags: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Original keyword-based search (kept for backward compatibility)."""
        blocks = self._split_blocks()
        out: List[Dict[str, Any]] = []

        q = text_query.lower() if text_query else None
        kinds_set = {k.lower() for k in kinds} if kinds else None
        specs_set = {s.lower() for s in specialists} if specialists else None
        any_tags_set = {t.lower() for t in any_tags} if any_tags else None
        all_tags_set = {t.lower() for t in all_tags} if all_tags else None

        for b in reversed(blocks):
            meta = self._parse_block_meta(b)

            if kinds_set and meta["kind"] and meta["kind"].lower() not in kinds_set:
                continue
            if specs_set and meta["specialist"] and meta["specialist"].lower() not in specs_set:
                continue

            block_tags = {t.lower() for t in meta.get("tags", [])}
            if any_tags_set and not (block_tags & any_tags_set):
                continue
            if all_tags_set and not all_tags_set.issubset(block_tags):
                continue

            if q and q not in meta["raw"].lower():
                continue

            out.append(meta)
            if len(out) >= limit:
                break

        return out

    def _semantic_search_blocks(
        self,
        *,
        text_query: str,
        kinds: Optional[List[str]] = None,
        specialists: Optional[List[str]] = None,
        any_tags: Optional[List[str]] = None,
        all_tags: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Semantic search using vector store."""
        if not self._vector_store:
            return []

        # Build metadata filter for ChromaDB
        metadata_filter = {}
        if kinds:
            metadata_filter["kind"] = {"$in": kinds}
        if specialists:
            metadata_filter["specialist"] = {"$in": specialists}

        # Note: ChromaDB metadata filtering has limitations
        # Tag filtering is done post-retrieval

        # Perform semantic search
        results = self._vector_store.search(
            query=text_query,
            limit=limit * 2,  # Get more for tag filtering
            metadata_filter=metadata_filter if metadata_filter else None,
        )

        # Post-filter by tags
        filtered_results = []
        for result in results:
            metadata = result.get("metadata", {})

            # Parse tags from metadata
            tags_str = metadata.get("tags", "")
            result_tags = {t.strip().lower() for t in tags_str.split(",") if t.strip()}

            # Apply tag filters
            if any_tags:
                any_tags_set = {t.lower() for t in any_tags}
                if not (result_tags & any_tags_set):
                    continue

            if all_tags:
                all_tags_set = {t.lower() for t in all_tags}
                if not all_tags_set.issubset(result_tags):
                    continue

            # Convert to diary format
            filtered_results.append({
                "timestamp": metadata.get("timestamp"),
                "kind": metadata.get("kind"),
                "specialist": metadata.get("specialist"),
                "tags": list(result_tags),
                "title": metadata.get("title"),
                "raw": result.get("text", ""),
                "similarity": result.get("similarity", 0.0),
            })

            if len(filtered_results) >= limit:
                break

        return filtered_results

    def _merge_search_results(
        self,
        keyword_results: List[Dict[str, Any]],
        semantic_results: List[Dict[str, Any]],
        semantic_weight: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Merge keyword and semantic results using Reciprocal Rank Fusion.

        Args:
            keyword_results: Results from keyword search
            semantic_results: Results from semantic search
            semantic_weight: Weight for semantic results (0.0-1.0)

        Returns:
            Merged and re-ranked results
        """
        from collections import defaultdict

        keyword_weight = 1.0 - semantic_weight
        scores = defaultdict(float)
        result_map = {}
        k = 60  # RRF constant

        # Score keyword results
        for rank, result in enumerate(keyword_results, start=1):
            result_id = result.get("timestamp", "") + result.get("raw", "")[:50]
            scores[result_id] += keyword_weight * (1.0 / (k + rank))
            if result_id not in result_map:
                result_map[result_id] = result

        # Score semantic results
        for rank, result in enumerate(semantic_results, start=1):
            result_id = result.get("timestamp", "") + result.get("raw", "")[:50]
            scores[result_id] += semantic_weight * (1.0 / (k + rank))
            if result_id not in result_map:
                result_map[result_id] = result

        # Sort by score
        ranked_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        # Build final results
        merged_results = []
        for result_id in ranked_ids:
            result = result_map[result_id].copy()
            result["rrf_score"] = scores[result_id]
            merged_results.append(result)

        return merged_results


    def recent_blocks(self, limit: int = 10) -> List[Dict[str, Any]]:
        blocks = self._split_blocks()
        out = []
        for b in reversed(blocks):
            out.append(self._parse_block_meta(b))
            if len(out) >= limit:
                break
        return out