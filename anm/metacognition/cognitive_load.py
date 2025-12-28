# ============================================================
# ANM V0-OpenSource — COGNITIVE LOAD TRACKER
#  Estimates processing complexity and resource usage
# ============================================================

from __future__ import annotations
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import re
import math


class LoadLevel(Enum):
    """Cognitive load levels."""
    MINIMAL = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    EXTREME = 5


@dataclass
class LoadFactors:
    """Breakdown of cognitive load factors."""
    # Query complexity
    query_length: float = 0.0
    query_ambiguity: float = 0.0
    multi_part: float = 0.0
    
    # Domain complexity
    domain_count: int = 0
    domain_difficulty: float = 0.0
    cross_domain: float = 0.0
    
    # Reasoning complexity
    reasoning_depth: int = 0
    reasoning_breadth: int = 0
    abstraction_level: float = 0.0
    
    # Memory load
    context_size: int = 0
    working_memory: float = 0.0
    
    # Calculated total
    total_load: float = 0.0
    level: LoadLevel = LoadLevel.MODERATE
    
    # Recommendations
    should_simplify: bool = False
    should_decompose: bool = False
    bottlenecks: List[str] = field(default_factory=list)


class CognitiveLoadTracker:
    """
    Tracks and estimates cognitive load during processing.
    
    Factors considered:
    - Query complexity (length, ambiguity, multi-part)
    - Domain complexity (number, difficulty, cross-domain)
    - Reasoning complexity (depth, breadth, abstraction)
    - Memory load (context size, working memory usage)
    
    Usage:
        tracker = CognitiveLoadTracker()
        
        load = tracker.estimate(
            query="Explain the relationship between quantum mechanics and general relativity",
            domains=["physics", "math"],
            context_tokens=2000,
        )
        
        print(f"Load level: {load.level.name}")
        if load.should_decompose:
            print("Recommend breaking into sub-questions")
    """
    
    # Domain difficulty ratings
    DOMAIN_DIFFICULTY = {
        "general": 0.3,
        "facts": 0.3,
        "memory": 0.2,
        "math": 0.6,
        "physics": 0.7,
        "chemistry": 0.6,
        "biology": 0.5,
        "code": 0.5,
        "research": 0.5,
        "philosophy": 0.7,
        "creative": 0.4,
        "simulation": 0.8,
        "image": 0.4,
    }
    
    # Abstract concept indicators
    ABSTRACT_INDICATORS = [
        "concept", "theory", "principle", "abstract", "metaphysical",
        "consciousness", "existence", "meaning", "infinity", "paradox",
        "relationship", "connection", "synthesis", "integration",
    ]
    
    def __init__(self):
        self._load_history: List[LoadFactors] = []
        self._current_session_load: float = 0.0
    
    def estimate(
        self,
        query: str,
        domains: List[str],
        context_tokens: int = 0,
        reasoning_steps: int = 0,
        specialists_invoked: int = 1,
    ) -> LoadFactors:
        """
        Estimate cognitive load for a query.
        
        Args:
            query: The user's query
            domains: Active domains
            context_tokens: Tokens in context
            reasoning_steps: Number of reasoning steps
            specialists_invoked: Number of specialists used
        
        Returns:
            LoadFactors with detailed breakdown
        """
        bottlenecks = []
        
        # Query complexity
        query_length = self._assess_query_length(query)
        query_ambiguity = self._assess_ambiguity(query)
        multi_part = self._assess_multi_part(query)
        
        if query_length > 0.7:
            bottlenecks.append("Long query")
        if query_ambiguity > 0.6:
            bottlenecks.append("Ambiguous query")
        if multi_part > 0.5:
            bottlenecks.append("Multi-part question")
        
        # Domain complexity
        domain_count = len(domains)
        domain_difficulty = max(
            (self.DOMAIN_DIFFICULTY.get(d.lower(), 0.5) for d in domains),
            default=0.5
        )
        cross_domain = self._assess_cross_domain(domains)
        
        if domain_count > 3:
            bottlenecks.append("Many domains involved")
        if cross_domain > 0.6:
            bottlenecks.append("Cross-domain reasoning required")
        
        # Reasoning complexity
        reasoning_depth = reasoning_steps
        reasoning_breadth = specialists_invoked
        abstraction_level = self._assess_abstraction(query)
        
        if reasoning_depth > 10:
            bottlenecks.append("Deep reasoning chain")
        if abstraction_level > 0.7:
            bottlenecks.append("High abstraction level")
        
        # Memory load
        context_size = context_tokens
        working_memory = self._estimate_working_memory(
            query, domain_count, reasoning_steps
        )
        
        if context_size > 4000:
            bottlenecks.append("Large context window")
        if working_memory > 0.8:
            bottlenecks.append("High working memory usage")
        
        # Calculate total load
        total_load = self._calculate_total_load(
            query_length, query_ambiguity, multi_part,
            domain_count, domain_difficulty, cross_domain,
            reasoning_depth, reasoning_breadth, abstraction_level,
            context_size, working_memory,
        )
        
        level = self._load_to_level(total_load)
        
        # Recommendations
        should_simplify = level in [LoadLevel.HIGH, LoadLevel.EXTREME]
        should_decompose = multi_part > 0.5 or (domain_count > 2 and cross_domain > 0.5)
        
        factors = LoadFactors(
            query_length=query_length,
            query_ambiguity=query_ambiguity,
            multi_part=multi_part,
            domain_count=domain_count,
            domain_difficulty=domain_difficulty,
            cross_domain=cross_domain,
            reasoning_depth=reasoning_depth,
            reasoning_breadth=reasoning_breadth,
            abstraction_level=abstraction_level,
            context_size=context_size,
            working_memory=working_memory,
            total_load=total_load,
            level=level,
            should_simplify=should_simplify,
            should_decompose=should_decompose,
            bottlenecks=bottlenecks,
        )
        
        self._load_history.append(factors)
        self._current_session_load = total_load
        
        return factors
    
    def _assess_query_length(self, query: str) -> float:
        """Assess load from query length."""
        words = len(query.split())
        # Normalize: 0 words = 0, 100+ words = 1
        return min(1.0, words / 100)
    
    def _assess_ambiguity(self, query: str) -> float:
        """Assess query ambiguity."""
        ambiguity = 0.0
        
        # Vague words
        vague = ["thing", "stuff", "something", "anything", "whatever", "somehow"]
        for v in vague:
            if v in query.lower():
                ambiguity += 0.15
        
        # Pronouns without clear reference
        pronouns = ["it", "they", "this", "that", "these", "those"]
        pronoun_count = sum(1 for p in pronouns if f" {p} " in query.lower())
        ambiguity += min(0.3, pronoun_count * 0.1)
        
        # Multiple interpretations
        if "or" in query.lower():
            ambiguity += 0.1
        
        return min(1.0, ambiguity)
    
    def _assess_multi_part(self, query: str) -> float:
        """Assess if query has multiple parts."""
        multi = 0.0
        
        # Question marks
        q_count = query.count("?")
        if q_count > 1:
            multi += 0.2 * q_count
        
        # Conjunctions
        conjunctions = [" and ", " also ", " additionally ", " furthermore ", " plus "]
        for conj in conjunctions:
            if conj in query.lower():
                multi += 0.15
        
        # Numbered items
        if re.search(r'\d+\.|\d+\)', query):
            multi += 0.3
        
        return min(1.0, multi)
    
    def _assess_cross_domain(self, domains: List[str]) -> float:
        """Assess cross-domain complexity."""
        if len(domains) <= 1:
            return 0.0
        
        # Different domain "families" increase complexity
        families = {
            "formal": {"math", "physics", "code"},
            "natural": {"biology", "chemistry"},
            "social": {"philosophy", "creative"},
            "factual": {"facts", "research", "memory"},
        }
        
        domain_families = set()
        for domain in domains:
            for family, members in families.items():
                if domain.lower() in members:
                    domain_families.add(family)
        
        # More families = more cross-domain load
        return min(1.0, len(domain_families) * 0.25)
    
    def _assess_abstraction(self, query: str) -> float:
        """Assess abstraction level of query."""
        abstract = 0.0
        query_lower = query.lower()
        
        for indicator in self.ABSTRACT_INDICATORS:
            if indicator in query_lower:
                abstract += 0.15
        
        # Meta-questions
        meta = ["what is", "why does", "how can", "meaning of"]
        for m in meta:
            if m in query_lower:
                abstract += 0.1
        
        return min(1.0, abstract)
    
    def _estimate_working_memory(
        self,
        query: str,
        domain_count: int,
        reasoning_steps: int,
    ) -> float:
        """Estimate working memory usage."""
        # Base load from query
        load = len(query.split()) / 200  # Normalized
        
        # Each domain adds load
        load += domain_count * 0.1
        
        # Reasoning steps add load
        load += reasoning_steps * 0.05
        
        return min(1.0, load)
    
    def _calculate_total_load(
        self,
        query_length: float, query_ambiguity: float, multi_part: float,
        domain_count: int, domain_difficulty: float, cross_domain: float,
        reasoning_depth: int, reasoning_breadth: int, abstraction: float,
        context_size: int, working_memory: float,
    ) -> float:
        """Calculate total cognitive load."""
        # Weighted sum
        query_load = 0.3 * query_length + 0.3 * query_ambiguity + 0.4 * multi_part
        
        domain_load = (
            0.3 * min(1.0, domain_count / 5) +
            0.4 * domain_difficulty +
            0.3 * cross_domain
        )
        
        reasoning_load = (
            0.4 * min(1.0, reasoning_depth / 20) +
            0.3 * min(1.0, reasoning_breadth / 5) +
            0.3 * abstraction
        )
        
        memory_load = (
            0.5 * min(1.0, context_size / 8000) +
            0.5 * working_memory
        )
        
        # Combine with weights
        total = (
            0.25 * query_load +
            0.25 * domain_load +
            0.30 * reasoning_load +
            0.20 * memory_load
        )
        
        return min(1.0, total)
    
    def _load_to_level(self, load: float) -> LoadLevel:
        """Convert load score to level."""
        if load < 0.2:
            return LoadLevel.MINIMAL
        elif load < 0.4:
            return LoadLevel.LOW
        elif load < 0.6:
            return LoadLevel.MODERATE
        elif load < 0.8:
            return LoadLevel.HIGH
        else:
            return LoadLevel.EXTREME
    
    def get_current_load(self) -> float:
        """Get current session load."""
        return self._current_session_load
    
    def get_load_history(self) -> List[float]:
        """Get history of load levels."""
        return [f.total_load for f in self._load_history]
    
    def get_average_load(self) -> float:
        """Get average load across history."""
        if not self._load_history:
            return 0.0
        return sum(f.total_load for f in self._load_history) / len(self._load_history)
