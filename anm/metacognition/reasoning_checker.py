# ============================================================
# ANM V0-OpenSource — REASONING QUALITY CHECKER
#  Self-evaluates reasoning quality and detects logical fallacies
# ============================================================

from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re


class LogicalFallacy(Enum):
    """Common logical fallacies to detect."""
    # Formal fallacies
    AFFIRMING_CONSEQUENT = "affirming_consequent"
    DENYING_ANTECEDENT = "denying_antecedent"
    CIRCULAR_REASONING = "circular_reasoning"
    
    # Informal fallacies
    AD_HOMINEM = "ad_hominem"
    APPEAL_TO_AUTHORITY = "appeal_to_authority"
    APPEAL_TO_EMOTION = "appeal_to_emotion"
    FALSE_DICHOTOMY = "false_dichotomy"
    HASTY_GENERALIZATION = "hasty_generalization"
    POST_HOC = "post_hoc"
    SLIPPERY_SLOPE = "slippery_slope"
    STRAW_MAN = "straw_man"
    RED_HERRING = "red_herring"
    
    # Cognitive biases (as fallacies)
    CONFIRMATION_BIAS = "confirmation_bias"
    ANCHORING = "anchoring"
    AVAILABILITY = "availability"


@dataclass
class ReasoningQuality:
    """Assessment of reasoning quality."""
    # Overall score (0-1)
    overall_score: float
    
    # Component scores
    logical_validity: float = 0.0       # Is the logic sound?
    relevance: float = 0.0              # Is the reasoning relevant?
    completeness: float = 0.0           # Are all steps present?
    clarity: float = 0.0                # Is it clear and understandable?
    evidence_support: float = 0.0       # Is it supported by evidence?
    
    # Issues detected
    fallacies_detected: List[Tuple[LogicalFallacy, str]] = field(default_factory=list)
    gaps_detected: List[str] = field(default_factory=list)
    unsupported_claims: List[str] = field(default_factory=list)
    
    # Recommendations
    needs_revision: bool = False
    revision_suggestions: List[str] = field(default_factory=list)
    
    # Metacognitive notes
    reasoning_style: str = "unknown"    # deductive, inductive, abductive, analogical
    chain_length: int = 0
    premise_count: int = 0


class ReasoningQualityChecker:
    """
    Evaluates the quality of ANM's reasoning.
    
    Checks for:
    - Logical validity and soundness
    - Relevance to the question
    - Completeness of reasoning chain
    - Clarity of explanation
    - Evidence support
    - Common logical fallacies
    
    Usage:
        checker = ReasoningQualityChecker()
        
        quality = checker.evaluate(
            query="Why is the sky blue?",
            reasoning="Light from the sun scatters. Blue light scatters more. Therefore the sky is blue.",
            conclusion="The sky appears blue because of Rayleigh scattering.",
        )
        
        print(f"Quality: {quality.overall_score:.2f}")
        for fallacy, context in quality.fallacies_detected:
            print(f"Fallacy: {fallacy.name}")
    """
    
    # Fallacy indicators
    FALLACY_PATTERNS = {
        LogicalFallacy.CIRCULAR_REASONING: [
            r"because it (is|does)",
            r"by definition",
            r"that's just how it is",
        ],
        LogicalFallacy.APPEAL_TO_AUTHORITY: [
            r"experts say",
            r"scientists believe",
            r"according to authorities",
            r"everyone knows",
        ],
        LogicalFallacy.HASTY_GENERALIZATION: [
            r"all \w+ are",
            r"every \w+ is",
            r"never",
            r"always",
            r"none of",
        ],
        LogicalFallacy.FALSE_DICHOTOMY: [
            r"either .* or",
            r"only two options",
            r"must be one or the other",
        ],
        LogicalFallacy.POST_HOC: [
            r"after .* therefore because",
            r"happened after .* so caused",
        ],
        LogicalFallacy.SLIPPERY_SLOPE: [
            r"will lead to",
            r"eventually cause",
            r"first step towards",
            r"domino effect",
        ],
    }
    
    # Reasoning connectors
    LOGICAL_CONNECTORS = [
        "therefore", "thus", "hence", "so", "consequently",
        "because", "since", "as", "given that", "if",
        "implies", "leads to", "results in", "follows that",
    ]
    
    def __init__(self):
        self._quality_history: List[ReasoningQuality] = []
    
    def evaluate(
        self,
        query: str,
        reasoning: str,
        conclusion: str,
        expected_domains: Optional[List[str]] = None,
    ) -> ReasoningQuality:
        """
        Evaluate reasoning quality.
        
        Args:
            query: The original question
            reasoning: The reasoning chain/explanation
            conclusion: The final conclusion
            expected_domains: Expected domains for relevance check
        
        Returns:
            ReasoningQuality assessment
        """
        fallacies = []
        gaps = []
        unsupported = []
        suggestions = []
        
        # 1. Check logical validity
        logical_validity = self._check_logical_validity(reasoning)
        if logical_validity < 0.6:
            suggestions.append("Strengthen logical connections between premises")
        
        # 2. Check relevance
        relevance = self._check_relevance(query, reasoning, conclusion)
        if relevance < 0.6:
            suggestions.append("Ensure reasoning directly addresses the question")
        
        # 3. Check completeness
        completeness, chain_length = self._check_completeness(reasoning)
        if completeness < 0.6:
            gaps.append("Reasoning chain may have missing steps")
            suggestions.append("Add intermediate reasoning steps")
        
        # 4. Check clarity
        clarity = self._check_clarity(reasoning)
        if clarity < 0.6:
            suggestions.append("Simplify and clarify the explanation")
        
        # 5. Check evidence support
        evidence_support, unsupported = self._check_evidence(reasoning)
        if evidence_support < 0.6:
            suggestions.append("Provide more evidence or citations")
        
        # 6. Detect fallacies
        fallacies = self._detect_fallacies(reasoning)
        for fallacy, context in fallacies:
            suggestions.append(f"Review potential {fallacy.value}: {context[:50]}...")
        
        # 7. Identify reasoning style
        reasoning_style = self._identify_style(reasoning)
        
        # 8. Count premises
        premise_count = self._count_premises(reasoning)
        
        # Calculate overall score
        overall = (
            0.25 * logical_validity +
            0.20 * relevance +
            0.20 * completeness +
            0.15 * clarity +
            0.20 * evidence_support
        )
        
        # Penalty for fallacies
        overall -= len(fallacies) * 0.05
        overall = max(0.0, min(1.0, overall))
        
        quality = ReasoningQuality(
            overall_score=overall,
            logical_validity=logical_validity,
            relevance=relevance,
            completeness=completeness,
            clarity=clarity,
            evidence_support=evidence_support,
            fallacies_detected=fallacies,
            gaps_detected=gaps,
            unsupported_claims=unsupported,
            needs_revision=overall < 0.6 or len(fallacies) > 0,
            revision_suggestions=suggestions,
            reasoning_style=reasoning_style,
            chain_length=chain_length,
            premise_count=premise_count,
        )
        
        self._quality_history.append(quality)
        return quality
    
    def _check_logical_validity(self, reasoning: str) -> float:
        """Check for logical structure and connectors."""
        score = 0.5  # Base score
        
        # Check for logical connectors
        connector_count = sum(
            1 for conn in self.LOGICAL_CONNECTORS
            if conn in reasoning.lower()
        )
        score += min(0.3, connector_count * 0.05)
        
        # Check for structured format
        if re.search(r'\d+\.|•|-|\*', reasoning):
            score += 0.1  # Has structure
        
        # Check for if-then structure
        if re.search(r'if .+ then', reasoning.lower()):
            score += 0.1
        
        return min(1.0, score)
    
    def _check_relevance(
        self,
        query: str,
        reasoning: str,
        conclusion: str,
    ) -> float:
        """Check if reasoning is relevant to query."""
        query_words = set(query.lower().split())
        reasoning_words = set(reasoning.lower().split())
        conclusion_words = set(conclusion.lower().split())
        
        # Remove common words
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "to", "of", "and", "or", "in", "on", "for", "with"}
        query_words -= stopwords
        reasoning_words -= stopwords
        conclusion_words -= stopwords
        
        # Check overlap
        if not query_words:
            return 0.5
        
        reasoning_overlap = len(query_words & reasoning_words) / len(query_words)
        conclusion_overlap = len(query_words & conclusion_words) / len(query_words)
        
        return 0.6 * reasoning_overlap + 0.4 * conclusion_overlap
    
    def _check_completeness(self, reasoning: str) -> Tuple[float, int]:
        """Check if reasoning chain is complete."""
        # Count reasoning steps
        sentences = re.split(r'[.!?]', reasoning)
        steps = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        chain_length = len(steps)
        
        # Very short chains may be incomplete
        if chain_length < 2:
            return 0.4, chain_length
        elif chain_length < 4:
            return 0.6, chain_length
        else:
            return 0.8, chain_length
    
    def _check_clarity(self, reasoning: str) -> float:
        """Check reasoning clarity."""
        score = 0.7  # Base score
        
        # Long sentences reduce clarity
        sentences = re.split(r'[.!?]', reasoning)
        avg_length = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
        if avg_length > 30:
            score -= 0.2
        elif avg_length > 20:
            score -= 0.1
        
        # Jargon/complexity indicators
        complex_words = ["notwithstanding", "heretofore", "aforementioned", "whereby"]
        for word in complex_words:
            if word in reasoning.lower():
                score -= 0.05
        
        # Structure helps clarity
        if re.search(r'\d+\.|first|second|third|finally', reasoning.lower()):
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _check_evidence(self, reasoning: str) -> Tuple[float, List[str]]:
        """Check for evidence and identify unsupported claims."""
        unsupported = []
        
        # Evidence indicators
        evidence_markers = [
            "according to", "research shows", "studies indicate",
            "data suggests", "evidence shows", "for example",
            "specifically", "in particular", "as demonstrated",
        ]
        
        evidence_count = sum(1 for marker in evidence_markers if marker in reasoning.lower())
        
        # Check for unsupported claims
        strong_claims = re.findall(r'(?:is|are|will|must|always|never)[^.!?]{20,}[.!?]', reasoning)
        for claim in strong_claims:
            if not any(marker in claim.lower() for marker in evidence_markers):
                unsupported.append(claim.strip()[:100])
        
        score = min(1.0, 0.3 + evidence_count * 0.15)
        score -= len(unsupported) * 0.05
        
        return max(0.0, score), unsupported[:5]  # Max 5 unsupported claims
    
    def _detect_fallacies(self, reasoning: str) -> List[Tuple[LogicalFallacy, str]]:
        """Detect potential logical fallacies."""
        fallacies = []
        reasoning_lower = reasoning.lower()
        
        for fallacy, patterns in self.FALLACY_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, reasoning_lower)
                if matches:
                    # Find context
                    for match in matches[:1]:  # First match only
                        idx = reasoning_lower.find(match if isinstance(match, str) else match[0])
                        start = max(0, idx - 20)
                        end = min(len(reasoning), idx + 50)
                        context = reasoning[start:end]
                        fallacies.append((fallacy, context))
                    break
        
        return fallacies
    
    def _identify_style(self, reasoning: str) -> str:
        """Identify the reasoning style used."""
        lower = reasoning.lower()
        
        # Deductive indicators
        if any(word in lower for word in ["therefore", "must be", "necessarily", "if...then"]):
            if "all" in lower or "every" in lower:
                return "deductive"
        
        # Inductive indicators
        if any(word in lower for word in ["probably", "likely", "suggests", "indicates"]):
            return "inductive"
        
        # Abductive indicators
        if any(word in lower for word in ["best explanation", "most likely", "hypothesis"]):
            return "abductive"
        
        # Analogical indicators
        if any(word in lower for word in ["similar to", "like", "analogous", "compared to"]):
            return "analogical"
        
        return "mixed"
    
    def _count_premises(self, reasoning: str) -> int:
        """Count number of premises in reasoning."""
        # Look for premise indicators
        premise_indicators = ["because", "since", "given that", "as", "due to"]
        count = sum(1 for ind in premise_indicators if ind in reasoning.lower())
        return max(1, count)
    
    def get_average_quality(self) -> float:
        """Get average reasoning quality."""
        if not self._quality_history:
            return 0.0
        return sum(q.overall_score for q in self._quality_history) / len(self._quality_history)
    
    def get_common_issues(self) -> Dict[str, int]:
        """Get most common issues."""
        fallacy_counts: Dict[str, int] = {}
        for quality in self._quality_history:
            for fallacy, _ in quality.fallacies_detected:
                fallacy_counts[fallacy.value] = fallacy_counts.get(fallacy.value, 0) + 1
        return fallacy_counts
