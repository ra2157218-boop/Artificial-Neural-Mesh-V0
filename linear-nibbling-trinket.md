# VDB + RAG Integration Plan for ANM V0-OpenSource

## Overview

Integrate **ChromaDB** vector database and **RAG** (Retrieval-Augmented Generation) into ANM to enable:
1. **Semantic Memory Enhancement**: Upgrade keyword-based search with semantic similarity across all memory layers
2. **Research Knowledge Base**: Accumulate and retrieve research findings over time

**User Requirements:**
- Vector DB: ChromaDB (persistent, lightweight, offline)
- Embeddings: sentence-transformers (all-MiniLM-L6-v2, 384-dim) - already in codebase
- Chunking: Smart chunking respecting diary structure
- Use cases: Both semantic memory + research KB

**Key Principles:**
- ✅ Reuse existing embedding infrastructure from `novelty_detector.py`
- ✅ Maintain 100% backward compatibility
- ✅ Preserve epistemic humility (observations, not truths)
- ✅ Work offline (no API keys)
- ✅ Non-destructive (enhance, don't replace)

---

## Implementation Phases

### Phase 1: Core VDB Infrastructure

#### 1.1 Create Vector Store Wrapper

**NEW FILE:** `anm/memory/vector_store.py` (~400 lines)

**Purpose:** ChromaDB wrapper that integrates with existing embedding infrastructure

**Key Components:**
- Reuse `EmbeddingCache` from `novelty_detector.py` (lines 34-64)
- Use same `all-MiniLM-L6-v2` model (384-dim embeddings)
- ChromaDB client with persistent storage at `.anm_cache/chroma/`
- Smart chunking integration
- Metadata filtering (kind, specialist, tags)
- Hybrid search (keyword + semantic fusion)

**API Design:**
```python
class VectorStore:
    def add(text, metadata, doc_id, chunk_size=512) -> List[str]
    def search(query, limit, metadata_filter, min_similarity) -> List[Dict]
    def hybrid_search(query, keyword_filter, metadata_filter, limit) -> List[Dict]
    def delete(doc_ids) -> None
    def rebuild_index(force) -> Dict
```

**Integration Points:**
- Reuses `novelty_detector.EmbeddingCache` for caching
- Stores embeddings in ChromaDB collections
- Supports metadata filtering matching diary's existing structure

---

#### 1.2 Create Smart Chunker

**NEW FILE:** `anm/utils/chunking.py` (~200 lines)

**Purpose:** Semantic chunking that respects diary entry structure

**Features:**
- Respects `DIARY_SEPARATOR` from diary_memory.py
- Preserves section headers (USER:, ASSISTANT:, NOTES:, etc.)
- Smart overlap for context continuity
- Extracts metadata from chunks
- Falls back to generic chunking for non-diary text

**API Design:**
```python
class SemanticChunker:
    def chunk(text) -> List[Dict[str, Any]]  # Returns chunks with start/end indices
    def _chunk_diary_entry(text) -> List[Dict]
    def _chunk_generic_text(text) -> List[Dict]
    def _extract_metadata(text) -> Dict
```

---

### Phase 2: Memory Layer Enhancement

#### 2.1 Enhance DiaryMemory with Semantic Search

**MODIFY:** `anm/memory/diary_memory.py`

**Critical Changes:**

1. **Add vector store initialization** (lazy, optional):
```python
# In __init__ (after line 82)
self._vector_store: Optional[VectorStore] = None
self._vector_enabled = False

# New method
def enable_vector_search(self, vector_store=None) -> None
```

2. **Index new entries in _append_entry** (after line 278):
```python
# After successful write
if self._vector_enabled and self._vector_store:
    metadata = {timestamp, kind, specialist, tags, ...}
    self._vector_store.add(text=block, metadata=metadata, doc_id=...)
```

3. **Enhance search_blocks with hybrid search** (replace lines 406-447):
```python
def search_blocks(
    text_query=None,
    kinds=None,
    specialists=None,
    any_tags=None,
    all_tags=None,
    limit=10,
    use_semantic=True,  # NEW PARAMETER (default True)
) -> List[Dict]:
    # Always run keyword search (backward compatibility)
    keyword_results = self._keyword_search_blocks(...)

    # If semantic enabled AND text query provided
    if use_semantic and self._vector_enabled and text_query:
        semantic_results = self._semantic_search_blocks(...)
        merged = self._merge_search_results(keyword_results, semantic_results, limit)
        return merged

    return keyword_results[:limit]
```

4. **Add new methods:**
   - `_keyword_search_blocks()` - Rename existing implementation
   - `_semantic_search_blocks()` - New semantic search via vector store
   - `_merge_search_results()` - Reciprocal Rank Fusion for hybrid results

**Backward Compatibility:**
- Existing API unchanged (optional `use_semantic` parameter)
- Keyword search ALWAYS runs (fallback safety)
- Non-fatal indexing (diary writes succeed even if vector indexing fails)
- If vector store disabled/unavailable: returns keyword results only

---

#### 2.2 Update Memory Layers

**MODIFY:** `anm/memory/episodic_memory.py` (line 136-176)
```python
def query(user_query, limit_blocks=6, use_semantic=True):  # NEW PARAMETER
    blocks = self.diary.search_blocks(
        text_query=user_query,
        kinds=["interaction", "learning", "idea"],
        use_semantic=use_semantic,  # Pass through
        limit=limit_blocks,
    )
```

**MODIFY:** `anm/memory/semantic_memory.py` (line 154-195)
```python
def query(text_query, limit=10, use_semantic=True):  # NEW PARAMETER
    blocks = self.diary.search_blocks(
        text_query=text_query,
        kinds=["idea", "observation"],
        use_semantic=use_semantic,  # Pass through
        limit=limit,
    )
```

**MODIFY:** `anm/memory/meta_memory.py` (line 229-251)
```python
def search(query, limit=5, use_semantic=True):  # NEW PARAMETER
    blocks = self.diary.search_blocks(
        text_query=query,
        kinds=["observation", "learning"],
        use_semantic=use_semantic,  # Pass through
        limit=limit,
    )
```

---

#### 2.3 Update MemoryHub Orchestrator

**MODIFY:** `anm/memory/memory_hub.py` (lines 96-118)

**Changes:**
```python
def __init__(
    diary_path="anm_diary.txt",
    enable_vector_search=True,  # NEW: from settings
):
    self.diary = DiaryMemory(diary_path)

    # NEW: Enable vector search if configured
    if enable_vector_search:
        try:
            from anm.memory.vector_store import VectorStore
            vector_store = VectorStore(
                collection_name="anm_diary_memory",
                persist_directory=".anm_cache/chroma/diary",
            )
            self.diary.enable_vector_search(vector_store)
        except Exception:
            pass  # Non-fatal: continue without vector search

    # Rest unchanged (working, episodic, semantic, meta memory)
```

---

### Phase 3: Research Knowledge Base

#### 3.1 Create Research Vector Store

**NEW FILE:** `anm/memory/research_vector_store.py` (~300 lines)

**Purpose:** Specialized vector store for accumulated research findings

**Features:**
- Separate ChromaDB collection for research outputs
- Rich metadata (query, domains, authority_models, timestamp, verification_status)
- Index PDF/Markdown sections separately (Summary, Analysis, Conclusions)
- Retrieval methods for research specialists

**API Design:**
```python
class ResearchVectorStore:
    def add_research_output(
        query: str,
        research_content: str,
        metadata: Dict[str, Any],
        sections: Optional[Dict[str, str]] = None,
    ) -> List[str]

    def search_related_research(
        query: str,
        limit: int = 5,
        domain_filter: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]

    def get_research_stats() -> Dict[str, Any]
```

---

#### 3.2 Integrate Knowledge Base into ResearchLLM

**MODIFY:** `anm/specialists/research_llm.py` (lines 188-282)

**Changes:**
```python
class ResearchLLM:
    def __init__(
        backend=None,
        research_kb: Optional[ResearchVectorStore] = None,  # NEW
    ):
        self.backend = backend or DuckDuckGoBackend()
        self.research_kb = research_kb  # NEW

    def run(self, wot_packet: str) -> str:
        query = self._extract_query_from_wot_packet(wot_packet)

        # EXISTING: Web search
        hits = self.backend.search(query, max_results=6)
        search_dump = self._format_hits(hits)

        # NEW: Search knowledge base for related past research
        kb_context = ""
        if self.research_kb:
            try:
                related = self.research_kb.search_related_research(query=query, limit=3)
                if related:
                    kb_context = self._format_kb_results(related)
            except Exception:
                pass  # Non-fatal

        # Build prompt with BOTH web search AND knowledge base
        prompt = (
            self.system_prefix
            + "\n\n--- WoT PACKET ---\n" + wot_packet
            + "\n\n--- CURRENT WEB SEARCH ---\n" + search_dump
        )

        if kb_context:
            prompt += (
                "\n\n--- PAST RESEARCH (KNOWLEDGE BASE) ---\n"
                + kb_context
                + "\n\nNote: Verify against current results. Use as context only."
            )

        # Rest unchanged (DeepSeek analysis, META generation)
```

**NEW METHOD:**
```python
def _format_kb_results(self, results: List[Dict]) -> str:
    """Format knowledge base results for prompt."""
    formatted = []
    for r in results:
        formatted.append(
            f"[Past Research @ {r['metadata']['timestamp']}]\n"
            f"Query: {r['metadata']['original_query']}\n"
            f"Findings: {r['text'][:300]}...\n"
            f"Relevance: {r['similarity']:.2f}\n"
        )
    return "\n".join(formatted)
```

---

#### 3.3 Update Router to Provide Research KB

**MODIFY:** `anm/router/router.py` (lines 366-370, ResearchLLM initialization)

**Changes:**
```python
# In Router.__init__, around line 366
try:
    from anm.memory.research_vector_store import ResearchVectorStore
    research_kb = ResearchVectorStore()
except Exception:
    research_kb = None

# When creating research specialist
if ResearchLLM is not None:
    self.research = ParallelSpecialistAdapter(
        ResearchLLM,
        n_workers=self.parallel_workers,
        name="research",
        worker_kwargs={"research_kb": research_kb},  # NEW
    )
```

---

#### 3.4 Hook Research Output Indexing

**MODIFY:** `anm/router/router.py` (in `_handle_research_mode`, after line 1241)

**Changes:**
```python
# After PDF/Markdown generation (line 1241)
if output_path and research_kb:
    try:
        research_kb.add_research_output(
            query=user_query,
            research_content=refined_output,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "authority_assignments": authority_assignments,
                "wot_steps": wot_steps,
                "verification_status": status,
                "output_format": output_format,
            },
            sections={
                "summary": refined_output[:500],
                "analysis": domain_cots,
                "metacognition": metacognition_audit,
            },
        )
    except Exception:
        pass  # Non-fatal
```

---

### Phase 4: Configuration & Dependencies

#### 4.1 Add Vector Store Configuration

**MODIFY:** `anm/config/settings.py` (after line 248)

**NEW SECTION:**
```python
# ============================================================
#  Vector Database & RAG Configuration
# ============================================================

VECTOR_SEARCH_ENABLED = True
VECTOR_DB_DIR = ".anm_cache/chroma"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
EMBEDDING_CACHE_DIR = ".anm_cache/embeddings"

CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

SEMANTIC_SEARCH_LIMIT = 10
MIN_SIMILARITY_THRESHOLD = 0.5

RESEARCH_KB_ENABLED = True
RESEARCH_KB_CHUNK_SIZE = 1024
RESEARCH_KB_RETENTION_DAYS = 365

AUTO_INDEX_EXISTING_DIARY = False
INDEX_BATCH_SIZE = 100

def get_config() -> dict:
    return {
        # ... existing config ...

        # Vector store config
        "vector_search_enabled": VECTOR_SEARCH_ENABLED,
        "vector_db_dir": VECTOR_DB_DIR,
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dim": EMBEDDING_DIM,
        "chunk_size": CHUNK_SIZE,
        "research_kb_enabled": RESEARCH_KB_ENABLED,
    }
```

---

#### 4.2 Add Dependencies

**MODIFY:** `anm/system/dependencies.py` (add to REQUIRED_PACKAGES)

**NEW:**
```python
REQUIRED_PACKAGES = {
    # ... existing ...
    "chromadb": "chromadb",
    "sentence-transformers": "sentence_transformers",
}
```

**Install Command:**
```bash
pip install chromadb>=0.4.0 sentence-transformers>=2.2.0
```

---

### Phase 5: Migration & Utilities

#### 5.1 Create Migration Script

**NEW FILE:** `anm/system/vector_migration.py` (~200 lines)

**Purpose:** One-time migration of existing diary entries to vector store

**Features:**
- Batch processing (100 entries at a time)
- Skip already-indexed entries (check ChromaDB)
- Progress reporting with rich UI
- Error handling and resume capability

**Usage:**
```bash
python -m anm.system.vector_migration --diary anm_diary.txt --batch-size 100
```

**Key Methods:**
```python
class VectorMigration:
    def migrate_diary(diary_path, vector_store, batch_size=100)
    def get_migration_progress() -> Dict
    def resume_migration(checkpoint_path)
```

---

## Critical Files Summary

### NEW FILES (5 files):

1. **`anm/memory/vector_store.py`** - ChromaDB wrapper, core semantic search
2. **`anm/utils/chunking.py`** - Smart chunking for diary structure
3. **`anm/memory/research_vector_store.py`** - Research knowledge base
4. **`anm/system/vector_migration.py`** - Migration script for existing diary
5. **`tests/test_vector_store.py`** - Unit tests for vector store

### MODIFIED FILES (9 files):

1. **`anm/memory/diary_memory.py`** - Add semantic search, hybrid fusion
2. **`anm/memory/episodic_memory.py`** - Pass semantic flag
3. **`anm/memory/semantic_memory.py`** - Pass semantic flag
4. **`anm/memory/meta_memory.py`** - Pass semantic flag
5. **`anm/memory/memory_hub.py`** - Initialize vector store
6. **`anm/specialists/research_llm.py`** - Integrate knowledge base retrieval
7. **`anm/router/router.py`** - Pass research KB, hook output indexing
8. **`anm/config/settings.py`** - Add vector store configuration
9. **`anm/output/research_pdf.py` or `research_markdown.py`** - Optional: add metadata hook

---

## Key Integration Points

### Embedding Layer (Shared):
- Reuse `novelty_detector.EmbeddingCache` (lines 34-64)
- Reuse `_compute_embedding()` method (lines 499-531)
- Same model: `all-MiniLM-L6-v2` (384-dim)
- Disk cache: `.anm_cache/embeddings/`

### Memory Search Flow:
```
User Query
  ↓
DiaryMemory.search_blocks(use_semantic=True)
  ↓
├─ Keyword Search (always runs)
└─ Semantic Search (if enabled)
  ↓
Hybrid Fusion (Reciprocal Rank Fusion)
  ↓
Return Top K Results
```

### Research Flow:
```
Research Query
  ↓
ResearchLLM.run()
  ↓
├─ Web Search (DuckDuckGo)
└─ Knowledge Base Search (ChromaDB)
  ↓
Combine Contexts → DeepSeek Analysis
  ↓
Save Output → Index in Knowledge Base
```

---

## Success Criteria

- ✅ Semantic search finds relevant entries missed by keyword search
- ✅ Hybrid search outperforms keyword-only baseline
- ✅ Research KB retrieves related past research
- ✅ Migration completes without errors
- ✅ Search latency < 1 second
- ✅ Zero crashes from vector search failures (graceful fallback)
- ✅ Backward compatibility maintained (existing code works unchanged)
- ✅ Offline operation confirmed (no API keys needed)
- ✅ Epistemic humility preserved (observations, not truths)

---

## Risk Mitigation

1. **Backward Compatibility:**
   - All new parameters optional with safe defaults
   - Keyword search always runs (fallback)
   - Non-fatal vector operations (try/except)

2. **Performance:**
   - Lazy vector store initialization
   - Embedding caching (reuse novelty_detector cache)
   - Batch indexing for migration
   - Configurable limits and thresholds

3. **Data Integrity:**
   - Append-only diary preserved (no changes to storage)
   - Vector store separate from diary (rebuild anytime)
   - Metadata extraction, no content modification

4. **Error Handling:**
   - ChromaDB import failures → graceful fallback
   - Embedding failures → fallback to keyword search
   - Indexing failures → log warning, continue operation

---

## Implementation Order

1. **Phase 1.1-1.2:** Core infrastructure (vector_store.py, chunking.py)
2. **Phase 4.2:** Install dependencies (chromadb, sentence-transformers)
3. **Phase 2.1:** DiaryMemory enhancement (hybrid search)
4. **Phase 2.2-2.4:** Memory layer updates (episodic, semantic, meta)
5. **Phase 2.3:** MemoryHub integration
6. **Phase 3.1:** Research vector store
7. **Phase 3.2-3.4:** ResearchLLM + Router integration
8. **Phase 4.1:** Configuration
9. **Phase 5.1:** Migration script
10. **Testing:** Comprehensive testing & validation

---

This plan provides a phased, non-breaking integration of VDB and RAG that enhances ANM's memory and research capabilities while preserving all existing functionality.
