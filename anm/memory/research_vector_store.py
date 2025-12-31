"""
Research Knowledge Base Vector Store

Specialized vector store for indexing and retrieving accumulated research outputs.
Enables RAG for ResearchLLM to avoid repeating past research.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class ResearchVectorStore:
    """
    Specialized vector store for research knowledge base.

    Features:
    - Index PDF/Markdown research outputs
    - Semantic search for related past research
    - Domain and topic filtering
    - Automatic deduplication
    - Graceful fallback if vector store unavailable
    """

    def __init__(
        self,
        persist_directory: str = ".anm_cache/research_kb",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize research knowledge base.

        Args:
            persist_directory: Directory for persistent storage
            embedding_model: Sentence-transformers model name
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize base vector store
        self._vector_store = VectorStore(
            collection_name="research_knowledge_base",
            persist_directory=str(self.persist_directory),
            embedding_model=embedding_model,
        )

        self._available = self._vector_store.is_available()

        if self._available:
            logger.info(f"Research Knowledge Base initialized: {self.persist_directory}")
        else:
            logger.warning("Research KB unavailable, research history disabled")

    def is_available(self) -> bool:
        """Check if research KB is available."""
        return self._available

    def add_research_output(
        self,
        query: str,
        research_content: str,
        metadata: Optional[Dict[str, Any]] = None,
        output_path: Optional[str] = None,
    ) -> List[str]:
        """
        Add research output to knowledge base.

        Args:
            query: Original research query
            research_content: Full research output (PDF/Markdown content)
            metadata: Optional metadata (domains, topics, timestamp, etc.)
            output_path: Path to output file (PDF/MD)

        Returns:
            List of document IDs added
        """
        if not self._available:
            logger.warning("Research KB unavailable, skipping indexing")
            return []

        try:
            # Prepare metadata
            kb_metadata = {
                "query": query[:500],  # Original query
                "type": "research",
                "format": self._detect_format(output_path),
            }

            # Add user-provided metadata
            if metadata:
                kb_metadata.update(metadata)

            # Add output path if provided
            if output_path:
                kb_metadata["output_path"] = str(output_path)

            # Extract sections for better chunking
            sections = self._extract_sections(research_content)

            doc_ids = []

            # Index each section separately
            for section in sections:
                section_metadata = kb_metadata.copy()
                section_metadata["section_title"] = section.get("title", "")

                ids = self._vector_store.add(
                    text=section.get("content", ""),
                    metadata=section_metadata,
                    chunk_size=512,
                )
                doc_ids.extend(ids)

            logger.info(f"Indexed research output: {len(doc_ids)} chunks from {len(sections)} sections")
            return doc_ids

        except Exception as e:
            logger.error(f"Failed to add research output to KB: {e}")
            return []

    def search_related_research(
        self,
        query: str,
        limit: int = 5,
        domain_filter: Optional[List[str]] = None,
        min_similarity: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Search for past research related to current query.

        Args:
            query: Current research query
            limit: Maximum results
            domain_filter: Optional domain filter
            min_similarity: Minimum similarity threshold

        Returns:
            List of related research sections with metadata
        """
        if not self._available:
            return []

        try:
            # Build metadata filter
            metadata_filter = {"type": "research"}
            if domain_filter:
                metadata_filter["domains"] = {"$in": domain_filter}

            # Search vector store
            results = self._vector_store.search(
                query=query,
                limit=limit,
                metadata_filter=metadata_filter,
                min_similarity=min_similarity,
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "query": result.get("metadata", {}).get("query", ""),
                    "content": result.get("text", ""),
                    "section": result.get("metadata", {}).get("section_title", ""),
                    "similarity": result.get("similarity", 0.0),
                    "metadata": result.get("metadata", {}),
                })

            return formatted_results

        except Exception as e:
            logger.error(f"Failed to search research KB: {e}")
            return []

    def get_research_summary(self, query: str, limit: int = 3) -> str:
        """
        Get a summary of past related research for context.

        Args:
            query: Current query
            limit: Max past research to include

        Returns:
            Formatted summary string
        """
        if not self._available:
            return ""

        try:
            related = self.search_related_research(query=query, limit=limit)

            if not related:
                return ""

            summary_lines = ["## Past Related Research:\n"]

            for idx, item in enumerate(related, start=1):
                past_query = item.get("query", "")
                section = item.get("section", "")
                similarity = item.get("similarity", 0.0)
                content = item.get("content", "")[:300]  # First 300 chars

                summary_lines.append(f"**{idx}. {past_query}**")
                if section:
                    summary_lines.append(f"   Section: {section}")
                summary_lines.append(f"   Similarity: {similarity:.2f}")
                summary_lines.append(f"   Preview: {content}...\n")

            return "\n".join(summary_lines)

        except Exception as e:
            logger.error(f"Failed to generate research summary: {e}")
            return ""

    def _detect_format(self, output_path: Optional[str]) -> str:
        """Detect output format from path."""
        if not output_path:
            return "unknown"

        path = Path(output_path)
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            return "pdf"
        elif suffix in [".md", ".markdown"]:
            return "markdown"
        else:
            return "unknown"

    def _extract_sections(self, content: str) -> List[Dict[str, str]]:
        """
        Extract sections from research content.

        Args:
            content: Research content (markdown format expected)

        Returns:
            List of {title, content} dicts
        """
        sections = []

        # Split by markdown headers (##)
        lines = content.split("\n")
        current_section = {"title": "Introduction", "content": ""}

        for line in lines:
            if line.startswith("## "):
                # Save previous section
                if current_section["content"].strip():
                    sections.append(current_section)

                # Start new section
                current_section = {
                    "title": line.replace("##", "").strip(),
                    "content": ""
                }
            else:
                current_section["content"] += line + "\n"

        # Add final section
        if current_section["content"].strip():
            sections.append(current_section)

        # If no sections found, treat entire content as one section
        if not sections:
            sections = [{"title": "Research Output", "content": content}]

        return sections

    def count(self) -> int:
        """Get total number of research chunks indexed."""
        if not self._available:
            return 0

        return self._vector_store.count()

    def clear(self) -> bool:
        """
        Clear all research knowledge base (use with caution).

        Returns:
            True if successful
        """
        if not self._available:
            return False

        try:
            # ChromaDB doesn't have a clear method, need to recreate collection
            logger.warning("Clear operation not implemented for safety")
            return False
        except Exception as e:
            logger.error(f"Failed to clear research KB: {e}")
            return False

    def close(self) -> None:
        """
        Close the research vector store and release resources.

        This method is safe to call multiple times.
        """
        if hasattr(self, '_vector_store') and self._vector_store:
            try:
                # Close underlying VectorStore
                if hasattr(self._vector_store, 'close'):
                    self._vector_store.close()
                self._vector_store = None
                self._available = False
                logger.info("ResearchVectorStore closed successfully")
            except Exception as e:
                logger.warning(f"Error closing ResearchVectorStore: {e}")

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
