"""
Vector Store for ANM Memory System

Provides ChromaDB-backed semantic search with embedding cache integration.
Reuses existing EmbeddingCache from novelty_detector for efficiency.
"""

import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class VectorStore:
    """
    ChromaDB-backed vector store with embedding cache integration.

    Features:
    - Persistent vector storage with metadata filtering
    - Reuses existing EmbeddingCache from novelty_detector
    - Smart chunking integration for long texts
    - Hybrid search (keyword + semantic) with Reciprocal Rank Fusion
    - Graceful fallback if ChromaDB unavailable
    """

    def __init__(
        self,
        collection_name: str = "anm_memory",
        persist_directory: str = ".anm_cache/chroma",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize vector store.

        Args:
            collection_name: Name of ChromaDB collection
            persist_directory: Directory for persistent storage
            embedding_model: Sentence-transformers model name
        """
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.embedding_model = embedding_model
        self._available = False
        self._collection = None
        self._client = None
        self._embedding_cache = None

        # Try to initialize
        self._initialize()

    def _initialize(self) -> None:
        """Initialize ChromaDB client and embedding cache."""
        try:
            # Import ChromaDB
            import chromadb
            from chromadb.config import Settings

            # Import embedding cache from utils (decoupled from expansion module)
            from anm.utils.embeddings import EmbeddingCache

            # Create persist directory
            self.persist_directory.mkdir(parents=True, exist_ok=True)

            # Initialize ChromaDB client
            self._client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
            )

            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},  # Cosine similarity
            )

            # Initialize embedding cache (reuse existing infrastructure)
            self._embedding_cache = EmbeddingCache()

            self._available = True
            logger.info(f"VectorStore initialized: collection={self.collection_name}, persist={self.persist_directory}")

        except ImportError as e:
            logger.warning(f"ChromaDB not available: {e}. Vector search disabled.")
            self._available = False
        except Exception as e:
            logger.error(f"Failed to initialize VectorStore: {e}")
            self._available = False

    def is_available(self) -> bool:
        """Check if vector store is available."""
        return self._available

    def _compute_embedding(self, text: str) -> Optional[List[float]]:
        """
        Compute embedding for text, using cache if available.

        Args:
            text: Text to embed

        Returns:
            384-dim embedding vector or None if failed
        """
        if not self._embedding_cache:
            return None

        try:
            # Check cache first
            embedding = self._embedding_cache.get(text)
            if embedding is not None:
                return embedding

            # Compute new embedding
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(self.embedding_model)
            embedding = model.encode(text, convert_to_numpy=True).tolist()

            # Cache it
            self._embedding_cache.put(text, embedding)

            return embedding

        except Exception as e:
            logger.error(f"Failed to compute embedding: {e}")
            return None

    def add(
        self,
        text: str,
        metadata: Dict[str, Any],
        doc_id: Optional[str] = None,
        chunk_size: int = 512,
    ) -> List[str]:
        """
        Add text to vector store with optional chunking.

        Args:
            text: Text to add
            metadata: Metadata dict (kind, specialist, tags, etc.)
            doc_id: Optional document ID (auto-generated if None)
            chunk_size: Maximum chunk size (0 = no chunking)

        Returns:
            List of document IDs added
        """
        if not self._available:
            logger.warning("VectorStore not available, skipping add")
            return []

        try:
            # Generate doc_id if not provided
            if doc_id is None:
                doc_id = self._generate_doc_id(text, metadata)

            # Chunk text if needed
            if chunk_size > 0 and len(text) > chunk_size:
                chunks = self._chunk_text(text, chunk_size)
            else:
                chunks = [(text, 0, len(text))]

            doc_ids = []
            embeddings = []
            documents = []
            metadatas = []

            for idx, (chunk_text, start_idx, end_idx) in enumerate(chunks):
                # Generate chunk ID
                chunk_id = f"{doc_id}_chunk_{idx}" if len(chunks) > 1 else doc_id

                # Compute embedding
                embedding = self._compute_embedding(chunk_text)
                if embedding is None:
                    logger.warning(f"Failed to compute embedding for chunk {idx}, skipping")
                    continue

                # Prepare chunk metadata
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_idx"] = idx
                chunk_metadata["chunk_start"] = start_idx
                chunk_metadata["chunk_end"] = end_idx
                chunk_metadata["doc_id"] = doc_id

                doc_ids.append(chunk_id)
                embeddings.append(embedding)
                documents.append(chunk_text)
                metadatas.append(chunk_metadata)

            # Add to ChromaDB
            if doc_ids:
                self._collection.add(
                    ids=doc_ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,
                )
                logger.debug(f"Added {len(doc_ids)} chunks to vector store")

            return doc_ids

        except Exception as e:
            logger.error(f"Failed to add to vector store: {e}")
            return []

    def search(
        self,
        query: str,
        limit: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None,
        min_similarity: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search in vector store.

        Args:
            query: Search query
            limit: Maximum results
            metadata_filter: Optional metadata filters (e.g., {"kind": "research"})
            min_similarity: Minimum similarity threshold (0.0-1.0)

        Returns:
            List of results with text, metadata, and similarity score
        """
        if not self._available:
            logger.warning("VectorStore not available, returning empty results")
            return []

        try:
            # Compute query embedding
            query_embedding = self._compute_embedding(query)
            if query_embedding is None:
                logger.warning("Failed to compute query embedding")
                return []

            # Query ChromaDB
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=metadata_filter,
            )

            # Format results
            formatted_results = []
            if results and results["ids"] and len(results["ids"]) > 0:
                for idx in range(len(results["ids"][0])):
                    # Extract data
                    doc_id = results["ids"][0][idx]
                    document = results["documents"][0][idx]
                    metadata = results["metadatas"][0][idx]
                    distance = results["distances"][0][idx]

                    # Convert distance to similarity (ChromaDB returns cosine distance)
                    similarity = 1.0 - distance

                    # Filter by minimum similarity
                    if similarity < min_similarity:
                        continue

                    formatted_results.append({
                        "id": doc_id,
                        "text": document,
                        "metadata": metadata,
                        "similarity": similarity,
                    })

            return formatted_results

        except Exception as e:
            logger.error(f"Failed to search vector store: {e}")
            return []

    def hybrid_search(
        self,
        query: str,
        keyword_results: List[Dict[str, Any]],
        limit: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None,
        semantic_weight: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining keyword and semantic results using Reciprocal Rank Fusion.

        Args:
            query: Search query
            keyword_results: Results from keyword search
            limit: Maximum results
            metadata_filter: Optional metadata filters
            semantic_weight: Weight for semantic results (0.0-1.0)

        Returns:
            Merged and re-ranked results
        """
        if not self._available:
            # Fallback to keyword results only
            return keyword_results[:limit]

        try:
            # Get semantic results
            semantic_results = self.search(
                query=query,
                limit=limit * 2,  # Get more candidates
                metadata_filter=metadata_filter,
            )

            # Apply Reciprocal Rank Fusion
            merged_results = self._reciprocal_rank_fusion(
                keyword_results=keyword_results,
                semantic_results=semantic_results,
                semantic_weight=semantic_weight,
            )

            return merged_results[:limit]

        except Exception as e:
            logger.error(f"Failed to perform hybrid search: {e}")
            # Fallback to keyword results
            return keyword_results[:limit]

    def _reciprocal_rank_fusion(
        self,
        keyword_results: List[Dict[str, Any]],
        semantic_results: List[Dict[str, Any]],
        semantic_weight: float = 0.5,
        k: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        Merge results using Reciprocal Rank Fusion algorithm.

        RRF score = Σ(1 / (k + rank))

        Args:
            keyword_results: Results from keyword search
            semantic_results: Results from semantic search
            semantic_weight: Weight for semantic results (0.0-1.0)
            k: RRF constant (default 60)

        Returns:
            Merged and re-ranked results
        """
        keyword_weight = 1.0 - semantic_weight
        scores = defaultdict(float)
        result_map = {}

        # Score keyword results
        for rank, result in enumerate(keyword_results, start=1):
            result_id = result.get("id") or result.get("text", "")[:50]
            scores[result_id] += keyword_weight * (1.0 / (k + rank))
            if result_id not in result_map:
                result_map[result_id] = result

        # Score semantic results
        for rank, result in enumerate(semantic_results, start=1):
            result_id = result.get("id") or result.get("text", "")[:50]
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

    def _chunk_text(self, text: str, chunk_size: int, overlap: int = 50) -> List[Tuple[str, int, int]]:
        """
        Simple text chunking with overlap.

        Args:
            text: Text to chunk
            chunk_size: Maximum chunk size
            overlap: Overlap between chunks

        Returns:
            List of (chunk_text, start_idx, end_idx) tuples
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            chunks.append((chunk_text, start, end))
            start = end - overlap

            # Avoid infinite loop
            if overlap >= chunk_size:
                break

        return chunks

    def _generate_doc_id(self, text: str, metadata: Dict[str, Any]) -> str:
        """
        Generate unique document ID from text and metadata.

        Args:
            text: Document text
            metadata: Document metadata

        Returns:
            Unique document ID
        """
        # Create hash from text + key metadata
        content = text[:200]  # First 200 chars
        kind = metadata.get("kind", "")
        specialist = metadata.get("specialist", "")
        timestamp = metadata.get("timestamp", "")

        hash_input = f"{content}:{kind}:{specialist}:{timestamp}"
        doc_hash = hashlib.md5(hash_input.encode()).hexdigest()[:12]

        return f"doc_{doc_hash}"

    def delete(self, doc_ids: List[str]) -> bool:
        """
        Delete documents from vector store.

        Args:
            doc_ids: List of document IDs to delete

        Returns:
            True if successful
        """
        if not self._available:
            return False

        try:
            self._collection.delete(ids=doc_ids)
            logger.debug(f"Deleted {len(doc_ids)} documents from vector store")
            return True
        except Exception as e:
            logger.error(f"Failed to delete from vector store: {e}")
            return False

    def count(self) -> int:
        """Get total number of documents in vector store."""
        if not self._available:
            return 0

        try:
            return self._collection.count()
        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            return 0

    def close(self) -> None:
        """
        Close the vector store and release resources.

        This method is safe to call multiple times.
        """
        if self._client:
            try:
                # ChromaDB client doesn't have explicit close method in all versions
                # but we can clear our reference
                self._client = None
                self._collection = None
                self._available = False
                logger.info(f"VectorStore '{self.collection_name}' closed successfully")
            except Exception as e:
                logger.warning(f"Error closing VectorStore: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures proper cleanup."""
        self.close()
        return False  # Don't suppress exceptions

    def __del__(self):
        """Destructor - cleanup on garbage collection."""
        try:
            self.close()
        except Exception:
            pass  # Ignore errors during cleanup
