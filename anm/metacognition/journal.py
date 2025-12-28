# ============================================================
# ANM V0-OpenSource — METACOGNITIVE JOURNAL
#  Logs metacognitive insights for learning and improvement
# ============================================================

from __future__ import annotations
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import os
import hashlib


class InsightType(Enum):
    """Types of metacognitive insights."""
    CONFIDENCE_CALIBRATION = "confidence_calibration"
    UNCERTAINTY_PATTERN = "uncertainty_pattern"
    REASONING_QUALITY = "reasoning_quality"
    KNOWLEDGE_BOUNDARY = "knowledge_boundary"
    BIAS_DETECTED = "bias_detected"
    STRATEGY_OUTCOME = "strategy_outcome"
    ERROR_PATTERN = "error_pattern"
    SUCCESS_PATTERN = "success_pattern"


@dataclass
class JournalEntry:
    """A single journal entry."""
    timestamp: str
    insight_type: InsightType
    
    # Context
    query_hash: str              # Hash for privacy
    domain: str
    
    # The insight
    observation: str
    metrics: Dict[str, float] = field(default_factory=dict)
    
    # Learning
    lesson_learned: str = ""
    action_taken: str = ""
    outcome: str = ""


class MetaCognitiveJournal:
    """
    Maintains a journal of metacognitive insights.
    
    Purpose:
    - Track patterns in confidence calibration
    - Log reasoning quality trends
    - Record knowledge boundary discoveries
    - Document bias detections
    - Enable learning from experience
    
    Usage:
        journal = MetaCognitiveJournal()
        
        journal.log(
            insight_type=InsightType.CONFIDENCE_CALIBRATION,
            query="What is quantum entanglement?",
            domain="physics",
            observation="Predicted 0.8 confidence, actual was correct",
            metrics={"predicted": 0.8, "actual": 1.0},
            lesson="Physics fundamentals are well-calibrated",
        )
        
        patterns = journal.analyze_patterns()
    """
    
    def __init__(self, journal_path: str = ".anm_cache/metacog_journal.json"):
        self.journal_path = journal_path
        self._entries: List[JournalEntry] = []
        self._load()
    
    def _load(self) -> None:
        """Load journal from disk."""
        if os.path.exists(self.journal_path):
            try:
                with open(self.journal_path, 'r') as f:
                    data = json.load(f)
                    for entry_dict in data.get("entries", []):
                        try:
                            entry = JournalEntry(
                                timestamp=entry_dict["timestamp"],
                                insight_type=InsightType(entry_dict["insight_type"]),
                                query_hash=entry_dict["query_hash"],
                                domain=entry_dict["domain"],
                                observation=entry_dict["observation"],
                                metrics=entry_dict.get("metrics", {}),
                                lesson_learned=entry_dict.get("lesson_learned", ""),
                                action_taken=entry_dict.get("action_taken", ""),
                                outcome=entry_dict.get("outcome", ""),
                            )
                            self._entries.append(entry)
                        except (KeyError, ValueError):
                            continue
            except (json.JSONDecodeError, IOError):
                self._entries = []
    
    def _save(self) -> None:
        """Save journal to disk."""
        os.makedirs(os.path.dirname(self.journal_path), exist_ok=True)
        
        data = {
            "version": "1.0",
            "entries": [
                {
                    "timestamp": e.timestamp,
                    "insight_type": e.insight_type.value,
                    "query_hash": e.query_hash,
                    "domain": e.domain,
                    "observation": e.observation,
                    "metrics": e.metrics,
                    "lesson_learned": e.lesson_learned,
                    "action_taken": e.action_taken,
                    "outcome": e.outcome,
                }
                for e in self._entries[-1000:]  # Keep last 1000
            ]
        }
        
        with open(self.journal_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def log(
        self,
        insight_type: InsightType,
        query: str,
        domain: str,
        observation: str,
        metrics: Optional[Dict[str, float]] = None,
        lesson: str = "",
        action: str = "",
        outcome: str = "",
    ) -> JournalEntry:
        """
        Log a metacognitive insight.
        
        Args:
            insight_type: Type of insight
            query: Original query (will be hashed)
            domain: Domain involved
            observation: What was observed
            metrics: Relevant metrics
            lesson: Lesson learned
            action: Action taken
            outcome: Outcome of action
        
        Returns:
            The created JournalEntry
        """
        entry = JournalEntry(
            timestamp=datetime.now().isoformat(),
            insight_type=insight_type,
            query_hash=self._hash_query(query),
            domain=domain,
            observation=observation,
            metrics=metrics or {},
            lesson_learned=lesson,
            action_taken=action,
            outcome=outcome,
        )
        
        self._entries.append(entry)
        self._save()
        
        return entry
    
    def _hash_query(self, query: str) -> str:
        """Hash query for privacy."""
        return hashlib.sha256(query.encode()).hexdigest()[:12]
    
    def get_recent(self, count: int = 10) -> List[JournalEntry]:
        """Get recent entries."""
        return self._entries[-count:]
    
    def get_by_type(self, insight_type: InsightType) -> List[JournalEntry]:
        """Get entries by type."""
        return [e for e in self._entries if e.insight_type == insight_type]
    
    def get_by_domain(self, domain: str) -> List[JournalEntry]:
        """Get entries by domain."""
        return [e for e in self._entries if e.domain.lower() == domain.lower()]
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in journal entries."""
        if not self._entries:
            return {"total_entries": 0}
        
        # Count by type
        type_counts: Dict[str, int] = {}
        for entry in self._entries:
            t = entry.insight_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        
        # Count by domain
        domain_counts: Dict[str, int] = {}
        for entry in self._entries:
            d = entry.domain
            domain_counts[d] = domain_counts.get(d, 0) + 1
        
        # Aggregate metrics
        confidence_entries = self.get_by_type(InsightType.CONFIDENCE_CALIBRATION)
        if confidence_entries:
            avg_predicted = sum(e.metrics.get("predicted", 0) for e in confidence_entries) / len(confidence_entries)
            avg_actual = sum(e.metrics.get("actual", 0) for e in confidence_entries) / len(confidence_entries)
            calibration_gap = avg_predicted - avg_actual
        else:
            calibration_gap = 0.0
        
        # Common lessons
        lessons = [e.lesson_learned for e in self._entries if e.lesson_learned]
        
        return {
            "total_entries": len(self._entries),
            "entries_by_type": type_counts,
            "entries_by_domain": domain_counts,
            "calibration_gap": calibration_gap,
            "unique_lessons": len(set(lessons)),
            "most_common_type": max(type_counts, key=type_counts.get) if type_counts else None,
            "most_active_domain": max(domain_counts, key=domain_counts.get) if domain_counts else None,
        }
    
    def get_lessons_for_domain(self, domain: str) -> List[str]:
        """Get lessons learned for a domain."""
        entries = self.get_by_domain(domain)
        return [e.lesson_learned for e in entries if e.lesson_learned]
    
    def clear(self) -> None:
        """Clear all entries."""
        self._entries = []
        self._save()
