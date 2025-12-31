"""
Smart Text Chunking for ANM Memory System

Provides semantic chunking that respects diary structure and preserves context.
"""

import logging
import re
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# Diary separator pattern
DIARY_SEPARATOR = "=" * 70


class SemanticChunker:
    """
    Smart text chunker that respects diary structure and semantic boundaries.

    Features:
    - Preserves diary entry boundaries
    - Respects conversation turns (USER:/ASSISTANT:)
    - Maintains context with overlap
    - Handles metadata preservation
    """

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        respect_diary_structure: bool = True,
    ):
        """
        Initialize semantic chunker.

        Args:
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks
            respect_diary_structure: Respect diary entry boundaries
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.respect_diary_structure = respect_diary_structure

        # Separator hierarchy (priority order)
        self.separators = [
            DIARY_SEPARATOR,  # Highest priority: diary entries
            "\n[ENTRY @",  # Entry markers
            "\n\nUSER:",  # Conversation turns
            "\n\nASSISTANT:",  # Conversation turns
            "\n\n",  # Paragraphs
            "\n",  # Lines
            ". ",  # Sentences
            " ",  # Words
        ]

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Chunk text into semantically coherent pieces.

        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to chunks

        Returns:
            List of chunk dicts with text, metadata, start/end indices
        """
        if not text:
            return []

        metadata = metadata or {}

        # Check if this is diary-formatted text
        is_diary = self._is_diary_format(text)

        if is_diary and self.respect_diary_structure:
            chunks = self._chunk_diary_entries(text)
        else:
            chunks = self._chunk_generic_text(text)

        # Add metadata to chunks
        result_chunks = []
        for idx, (chunk_text, start_idx, end_idx) in enumerate(chunks):
            chunk_meta = metadata.copy()
            chunk_meta["chunk_idx"] = idx
            chunk_meta["chunk_start"] = start_idx
            chunk_meta["chunk_end"] = end_idx
            chunk_meta["chunk_total"] = len(chunks)

            result_chunks.append({
                "text": chunk_text,
                "metadata": chunk_meta,
                "start": start_idx,
                "end": end_idx,
            })

        return result_chunks

    def _is_diary_format(self, text: str) -> bool:
        """Check if text follows diary format."""
        return DIARY_SEPARATOR in text or "[ENTRY @" in text

    def _chunk_diary_entries(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Chunk diary-formatted text, respecting entry boundaries.

        Args:
            text: Diary-formatted text

        Returns:
            List of (chunk_text, start_idx, end_idx) tuples
        """
        chunks = []

        # Split by diary separator
        entries = text.split(DIARY_SEPARATOR)

        current_pos = 0
        for entry_idx, entry in enumerate(entries):
            entry = entry.strip()
            if not entry:
                current_pos += len(DIARY_SEPARATOR)
                continue

            # Check if entry fits in chunk_size
            if len(entry) <= self.chunk_size:
                # Entry fits, add as single chunk
                chunks.append((entry, current_pos, current_pos + len(entry)))
            else:
                # Entry too large, chunk it further
                entry_chunks = self._chunk_large_entry(entry, current_pos)
                chunks.extend(entry_chunks)

            current_pos += len(entry) + len(DIARY_SEPARATOR)

        return chunks

    def _chunk_large_entry(self, entry: str, base_offset: int) -> List[Tuple[str, int, int]]:
        """
        Chunk a large diary entry that exceeds chunk_size.

        Args:
            entry: Large diary entry
            base_offset: Starting position in original text

        Returns:
            List of (chunk_text, start_idx, end_idx) tuples
        """
        chunks = []

        # Try to split by conversation turns first
        turn_pattern = r"(USER:|ASSISTANT:)"
        parts = re.split(turn_pattern, entry)

        current_chunk = ""
        current_start = base_offset

        for part in parts:
            # Skip empty parts
            if not part.strip():
                continue

            # Check if adding this part exceeds chunk_size
            if len(current_chunk) + len(part) <= self.chunk_size:
                current_chunk += part
            else:
                # Save current chunk if not empty
                if current_chunk.strip():
                    chunks.append((
                        current_chunk,
                        current_start,
                        current_start + len(current_chunk)
                    ))

                # Start new chunk with overlap
                if self.overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-self.overlap:]
                    current_chunk = overlap_text + part
                    current_start = current_start + len(current_chunk) - len(overlap_text) - len(part)
                else:
                    current_chunk = part
                    current_start = current_start + len(current_chunk)

        # Add final chunk
        if current_chunk.strip():
            chunks.append((
                current_chunk,
                current_start,
                current_start + len(current_chunk)
            ))

        # If still too large, fall back to generic chunking
        if any(len(chunk[0]) > self.chunk_size * 1.5 for chunk in chunks):
            return self._chunk_generic_text(entry, base_offset)

        return chunks

    def _chunk_generic_text(self, text: str, base_offset: int = 0) -> List[Tuple[str, int, int]]:
        """
        Chunk text using hierarchical separators.

        Args:
            text: Text to chunk
            base_offset: Starting position in original text

        Returns:
            List of (chunk_text, start_idx, end_idx) tuples
        """
        chunks = []
        current_pos = base_offset

        # Try each separator in hierarchy
        for separator in self.separators:
            if separator in text:
                parts = text.split(separator)
                current_chunk = ""
                chunk_start = current_pos

                for part_idx, part in enumerate(parts):
                    # Add separator back (except for first part)
                    if part_idx > 0:
                        part = separator + part

                    # Check if adding this part exceeds chunk_size
                    if len(current_chunk) + len(part) <= self.chunk_size:
                        current_chunk += part
                    else:
                        # Save current chunk if not empty
                        if current_chunk.strip():
                            chunks.append((
                                current_chunk,
                                chunk_start,
                                chunk_start + len(current_chunk)
                            ))

                        # Start new chunk with overlap
                        if self.overlap > 0 and current_chunk:
                            overlap_text = current_chunk[-self.overlap:]
                            current_chunk = overlap_text + part
                            chunk_start = chunk_start + len(current_chunk) - len(overlap_text) - len(part)
                        else:
                            current_chunk = part
                            chunk_start = chunk_start + len(current_chunk)

                # Add final chunk
                if current_chunk.strip():
                    chunks.append((
                        current_chunk,
                        chunk_start,
                        chunk_start + len(current_chunk)
                    ))

                # If chunks are reasonably sized, we're done
                if all(len(c[0]) <= self.chunk_size * 1.2 for c in chunks):
                    return chunks

        # Fallback: simple fixed-size chunking
        if not chunks:
            chunks = self._chunk_fixed_size(text, base_offset)

        return chunks

    def _chunk_fixed_size(self, text: str, base_offset: int = 0) -> List[Tuple[str, int, int]]:
        """
        Fallback: chunk text into fixed-size pieces with overlap.

        Args:
            text: Text to chunk
            base_offset: Starting position in original text

        Returns:
            List of (chunk_text, start_idx, end_idx) tuples
        """
        chunks = []
        start = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]
            chunks.append((
                chunk_text,
                base_offset + start,
                base_offset + end
            ))

            # Move to next chunk with overlap
            start = end - self.overlap

            # Avoid infinite loop
            if self.overlap >= self.chunk_size:
                break

        return chunks

    def estimate_chunks(self, text: str) -> int:
        """
        Estimate number of chunks without actually chunking.

        Args:
            text: Text to estimate

        Returns:
            Estimated number of chunks
        """
        if not text:
            return 0

        text_len = len(text)

        # Account for overlap
        effective_chunk_size = self.chunk_size - self.overlap
        if effective_chunk_size <= 0:
            effective_chunk_size = self.chunk_size

        num_chunks = max(1, (text_len + effective_chunk_size - 1) // effective_chunk_size)

        return num_chunks


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 50,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function for chunking text.

    Args:
        text: Text to chunk
        chunk_size: Target chunk size
        overlap: Overlap between chunks
        metadata: Optional metadata

    Returns:
        List of chunk dicts
    """
    chunker = SemanticChunker(chunk_size=chunk_size, overlap=overlap)
    return chunker.chunk(text, metadata)
