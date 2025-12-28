# ============================================================
# ANM V0-OpenSource — KNOWLEDGE BOUNDARY DETECTOR
#  Know what you know and don't know
# ============================================================

from __future__ import annotations
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class KnowledgeStatus(Enum):
    """Status of knowledge about a topic."""
    KNOWN_WELL = "known_well"           # High confidence, well-trained
    KNOWN_PARTIALLY = "known_partially" # Some knowledge, gaps exist
    KNOWN_OUTDATED = "known_outdated"   # Knowledge may be outdated
    BOUNDARY_EDGE = "boundary_edge"     # At the edge of knowledge
    UNKNOWN = "unknown"                 # Outside training
    UNKNOWABLE = "unknowable"           # Fundamentally unknowable


@dataclass
class BoundaryResult:
    """Result of knowledge boundary analysis."""
    status: KnowledgeStatus
    
    # Confidence about the boundary assessment itself
    boundary_confidence: float
    
    # What we know
    known_aspects: List[str] = field(default_factory=list)
    
    # What we don't know
    unknown_aspects: List[str] = field(default_factory=list)
    
    # Gaps and limitations
    knowledge_gaps: List[str] = field(default_factory=list)
    temporal_limitations: List[str] = field(default_factory=list)
    
    # Recommendations
    should_acknowledge_limits: bool = False
    should_defer_to_expert: bool = False
    should_seek_sources: bool = False
    
    # Metacognitive notes
    domain_coverage: float = 0.0        # 0-1, how much of domain we cover
    recency_score: float = 1.0          # 1 = current, 0 = very outdated
    explanation: str = ""


class KnowledgeBoundaryDetector:
    """
    Detects and maps the boundaries of ANM's knowledge.
    
    Key capabilities:
    1. Identify what we know well vs poorly
    2. Detect knowledge gaps
    3. Identify outdated information
    4. Recognize unknowable questions
    5. Recommend when to defer
    
    Usage:
        detector = KnowledgeBoundaryDetector()
        
        result = detector.analyze(
            query="What will the stock market do tomorrow?",
            domain="finance",
        )
        
        if result.status == KnowledgeStatus.UNKNOWABLE:
            print("This is fundamentally unpredictable")
    """
    
    # Topics with high knowledge coverage
    WELL_KNOWN_TOPICS = {
        "basic_math", "algebra", "calculus", "geometry",
        "classical_physics", "mechanics", "thermodynamics",
        "programming", "python", "javascript", "algorithms",
        "chemistry_basics", "biology_basics",
        "common_facts", "geography", "history_major_events",
    }
    
    # Topics with partial/limited knowledge
    PARTIAL_KNOWLEDGE = {
        "advanced_physics", "quantum_mechanics", "relativity",
        "cutting_edge_research", "recent_discoveries",
        "specialized_medicine", "advanced_chemistry",
        "specific_legal", "niche_technical",
    }
    
    # Topics likely outdated (cutoff-sensitive)
    TIME_SENSITIVE = {
        "current_events", "news", "politics", "stock_prices",
        "weather", "sports_scores", "celebrity_news",
        "technology_trends", "software_versions",
    }
    
    # Fundamentally unknowable
    UNKNOWABLE = {
        "future_predictions", "lottery_numbers", "stock_tomorrow",
        "exact_timing", "random_outcomes", "consciousness",
        "meaning_of_life", "after_death", "god_existence",
    }
    
    # Domain knowledge estimates
    DOMAIN_COVERAGE = {
        "math": 0.85,
        "physics": 0.75,
        "chemistry": 0.70,
        "biology": 0.70,
        "code": 0.80,
        "general": 0.65,
        "facts": 0.60,
        "research": 0.55,
        "creative": 0.75,
        "philosophy": 0.60,
        "medical": 0.50,
        "legal": 0.45,
        "financial": 0.50,
    }
    
    def __init__(self, knowledge_cutoff: str = "2024-01"):
        self.knowledge_cutoff = knowledge_cutoff
        self._boundary_history: List[BoundaryResult] = []
    
    def analyze(
        self,
        query: str,
        domain: str,
        topics_mentioned: Optional[List[str]] = None,
    ) -> BoundaryResult:
        """
        Analyze knowledge boundaries for a query.
        
        Args:
            query: The user's query
            domain: Primary domain
            topics_mentioned: Specific topics in the query
        
        Returns:
            BoundaryResult with boundary analysis
        """
        query_lower = query.lower()
        topics = topics_mentioned or []
        
        known_aspects = []
        unknown_aspects = []
        knowledge_gaps = []
        temporal_limitations = []
        
        # 1. Check for unknowable questions
        unknowable_score = self._check_unknowable(query_lower)
        if unknowable_score > 0.7:
            return BoundaryResult(
                status=KnowledgeStatus.UNKNOWABLE,
                boundary_confidence=unknowable_score,
                unknown_aspects=["This question asks about fundamentally unknowable information"],
                should_acknowledge_limits=True,
                explanation="This query asks about something that cannot be known with certainty.",
            )
        
        # 2. Check for time-sensitive queries
        temporal_score = self._check_temporal(query_lower, domain)
        if temporal_score > 0.6:
            temporal_limitations.append(f"Information may be outdated (knowledge cutoff: {self.knowledge_cutoff})")
        
        # 3. Assess domain coverage
        domain_coverage = self.DOMAIN_COVERAGE.get(domain.lower(), 0.5)
        
        # 4. Check topic-level knowledge
        for topic in topics:
            topic_lower = topic.lower().replace(" ", "_")
            if topic_lower in self.WELL_KNOWN_TOPICS:
                known_aspects.append(f"Good coverage of {topic}")
            elif topic_lower in self.PARTIAL_KNOWLEDGE:
                knowledge_gaps.append(f"Limited coverage of {topic}")
            elif topic_lower in self.TIME_SENSITIVE:
                temporal_limitations.append(f"{topic} information may be outdated")
        
        # 5. Check query-level indicators
        specific_indicators = self._extract_specific_indicators(query_lower)
        unknown_aspects.extend(specific_indicators.get("unknown", []))
        known_aspects.extend(specific_indicators.get("known", []))
        
        # 6. Determine overall status
        status = self._determine_status(
            unknowable_score, temporal_score, domain_coverage,
            len(known_aspects), len(unknown_aspects), len(knowledge_gaps)
        )
        
        # 7. Calculate recency
        recency = 1.0 - temporal_score
        
        # 8. Determine recommendations
        should_acknowledge = status in [
            KnowledgeStatus.BOUNDARY_EDGE,
            KnowledgeStatus.UNKNOWN,
            KnowledgeStatus.KNOWN_OUTDATED,
        ]
        should_defer = status == KnowledgeStatus.UNKNOWN and domain in ["medical", "legal", "financial"]
        should_seek = status in [KnowledgeStatus.KNOWN_OUTDATED, KnowledgeStatus.KNOWN_PARTIALLY]
        
        result = BoundaryResult(
            status=status,
            boundary_confidence=0.7,  # Meta-confidence
            known_aspects=known_aspects,
            unknown_aspects=unknown_aspects,
            knowledge_gaps=knowledge_gaps,
            temporal_limitations=temporal_limitations,
            should_acknowledge_limits=should_acknowledge,
            should_defer_to_expert=should_defer,
            should_seek_sources=should_seek,
            domain_coverage=domain_coverage,
            recency_score=recency,
            explanation=self._generate_explanation(status, domain, temporal_limitations),
        )
        
        self._boundary_history.append(result)
        return result
    
    def _check_unknowable(self, query: str) -> float:
        """Check if query asks for unknowable information."""
        score = 0.0
        
        # Future predictions
        future_indicators = ["will happen", "going to happen", "predict", "tomorrow", "next year", "in the future"]
        for ind in future_indicators:
            if ind in query:
                score += 0.2
        
        # Random outcomes
        random_indicators = ["lottery", "dice", "random", "gamble"]
        for ind in random_indicators:
            if ind in query:
                score += 0.3
        
        # Metaphysical questions
        metaphysical = ["meaning of life", "consciousness", "free will", "god", "afterlife", "soul"]
        for ind in metaphysical:
            if ind in query:
                score += 0.25
        
        # Exact future states
        if "exact" in query and any(f in query for f in ["price", "value", "number"]):
            score += 0.3
        
        return min(1.0, score)
    
    def _check_temporal(self, query: str, domain: str) -> float:
        """Check if query is time-sensitive."""
        score = 0.0
        
        # Time-sensitive domains
        if domain.lower() in ["news", "current_events", "finance", "politics", "weather"]:
            score += 0.4
        
        # Temporal indicators
        temporal = ["current", "latest", "today", "now", "recent", "2024", "2025", "this year"]
        for ind in temporal:
            if ind in query:
                score += 0.15
        
        # Version/update indicators
        version = ["version", "update", "release", "new"]
        for ind in version:
            if ind in query:
                score += 0.1
        
        return min(1.0, score)
    
    def _extract_specific_indicators(self, query: str) -> Dict[str, List[str]]:
        """Extract specific known/unknown indicators from query."""
        result = {"known": [], "unknown": []}
        
        # Highly specific queries may be outside knowledge
        if query.count("specific") > 0 or query.count("exact") > 0:
            result["unknown"].append("Highly specific details may not be in training")
        
        # Personal/private information
        personal = ["my", "your", "personal", "private", "secret"]
        if any(p in query for p in personal):
            result["unknown"].append("Personal/private information is not available")
        
        # Well-known facts
        factual = ["what is", "definition", "meaning of", "explain"]
        if any(f in query for f in factual):
            result["known"].append("General definitions and explanations are well-covered")
        
        return result
    
    def _determine_status(
        self,
        unknowable: float,
        temporal: float,
        coverage: float,
        known_count: int,
        unknown_count: int,
        gap_count: int,
    ) -> KnowledgeStatus:
        """Determine overall knowledge status."""
        if unknowable > 0.7:
            return KnowledgeStatus.UNKNOWABLE
        
        if temporal > 0.6:
            return KnowledgeStatus.KNOWN_OUTDATED
        
        if unknown_count > known_count and gap_count > 2:
            return KnowledgeStatus.UNKNOWN
        
        if coverage < 0.4 or gap_count > 1:
            return KnowledgeStatus.BOUNDARY_EDGE
        
        if coverage < 0.6 or gap_count > 0:
            return KnowledgeStatus.KNOWN_PARTIALLY
        
        return KnowledgeStatus.KNOWN_WELL
    
    def _generate_explanation(
        self,
        status: KnowledgeStatus,
        domain: str,
        temporal: List[str],
    ) -> str:
        """Generate human-readable explanation."""
        explanations = {
            KnowledgeStatus.KNOWN_WELL: f"I have strong coverage of {domain} topics.",
            KnowledgeStatus.KNOWN_PARTIALLY: f"I have partial knowledge of {domain}, with some gaps.",
            KnowledgeStatus.KNOWN_OUTDATED: f"My {domain} knowledge may be outdated. " + (temporal[0] if temporal else ""),
            KnowledgeStatus.BOUNDARY_EDGE: f"This query is at the edge of my {domain} knowledge.",
            KnowledgeStatus.UNKNOWN: f"This is outside my training in {domain}.",
            KnowledgeStatus.UNKNOWABLE: "This asks for information that cannot be known with certainty.",
        }
        return explanations.get(status, "Knowledge status uncertain.")
    
    def get_domain_summary(self) -> Dict[str, Any]:
        """Get summary of knowledge across domains."""
        return {
            "domain_coverage": self.DOMAIN_COVERAGE.copy(),
            "knowledge_cutoff": self.knowledge_cutoff,
            "well_known_count": len(self.WELL_KNOWN_TOPICS),
            "partial_count": len(self.PARTIAL_KNOWLEDGE),
            "time_sensitive_count": len(self.TIME_SENSITIVE),
        }
    
    def acknowledge_limitation(self, query: str, domain: str) -> str:
        """Generate an appropriate limitation acknowledgment."""
        result = self.analyze(query, domain)
        
        if result.status == KnowledgeStatus.UNKNOWABLE:
            return "I cannot provide a definitive answer as this is fundamentally uncertain."
        elif result.status == KnowledgeStatus.UNKNOWN:
            return f"This is outside my knowledge in {domain}. I recommend consulting an expert."
        elif result.status == KnowledgeStatus.KNOWN_OUTDATED:
            return f"My information on this may be outdated (cutoff: {self.knowledge_cutoff})."
        elif result.status == KnowledgeStatus.BOUNDARY_EDGE:
            return "I have limited knowledge on this specific topic."
        else:
            return ""
