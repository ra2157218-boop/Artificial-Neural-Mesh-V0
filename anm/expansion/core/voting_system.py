# ============================================================
# ANM V0-OpenSource — VOTING SYSTEM V2 (MAXIMUM LEVEL)
#  Parallel Async Voting • Weighted Consensus • Confidence Bands
#  Byzantine Fault Tolerance • Vote Aggregation • Justification
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from enum import Enum
import time
import json
import hashlib


class VoteType(Enum):
    """Types of votes a specialist can cast."""
    STRONG_YES = "strong_yes"      # Definitely needs new module
    YES = "yes"                     # Probably needs new module
    UNCERTAIN = "uncertain"         # Can't determine
    NO = "no"                       # Can handle this
    STRONG_NO = "strong_no"         # Definitely can handle this
    ABSTAIN = "abstain"            # No opinion / not relevant


@dataclass
class Vote:
    """Rich vote object with metadata."""
    specialist: str
    vote_type: VoteType
    confidence: float  # 0.0-1.0
    reasoning: str
    processing_time_ms: float
    can_partially_handle: bool = False  # Can handle some aspects
    suggested_collaboration: List[str] = field(default_factory=list)  # Other domains to involve
    
    @property
    def weight(self) -> float:
        """Get weighted vote value."""
        base_weights = {
            VoteType.STRONG_YES: 2.0,
            VoteType.YES: 1.0,
            VoteType.UNCERTAIN: 0.0,
            VoteType.NO: -1.0,
            VoteType.STRONG_NO: -2.0,
            VoteType.ABSTAIN: 0.0,
        }
        return base_weights[self.vote_type] * self.confidence


@dataclass
class VotingResult:
    """Comprehensive voting result with detailed breakdown."""
    majority_yes: bool
    consensus_level: str  # "unanimous", "strong", "moderate", "weak", "split"
    total_votes: int
    yes_votes: int
    no_votes: int
    abstain_votes: int
    weighted_score: float  # Weighted average (-2 to +2)
    confidence_band: str  # "high", "medium", "low"
    votes: List[Vote]
    reasoning: str
    processing_time_ms: float
    quorum_reached: bool
    recommended_action: str  # "expand", "collaborate", "handle_existing", "escalate"


class VotingSystemV2:
    """
    MAXIMUM LEVEL Voting System.
    
    Features:
    - Parallel async voting for all specialists
    - Weighted vote scoring based on domain relevance
    - Byzantine fault tolerance (handles slow/failed specialists)
    - Confidence-based vote weighting
    - Consensus level detection
    - Collaboration suggestions
    - Vote caching and deduplication
    """
    
    # Domain expertise weights for different query types
    DOMAIN_EXPERTISE_WEIGHTS = {
        "technical": {"code": 1.5, "physics": 1.3, "math": 1.3, "chemistry": 1.2},
        "scientific": {"physics": 1.5, "chemistry": 1.5, "biology": 1.5, "research": 1.3},
        "factual": {"facts": 1.5, "research": 1.4, "memory": 1.2},
        "creative": {"general": 1.3, "sound": 1.2, "image": 1.2},
        "analytical": {"math": 1.5, "physics": 1.4, "code": 1.3},
    }
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        max_workers: int = 8,
        timeout_seconds: float = 30.0,
        quorum_percentage: float = 0.6,
    ):
        self.config = config or {}
        self.max_workers = max_workers
        self.timeout = timeout_seconds
        self.quorum_percentage = quorum_percentage
        self.vote_cache: Dict[str, VotingResult] = {}
    
    def conduct_vote(
        self,
        query: str,
        detected_domain: str,
        novelty_reasoning: str,
        specialists: Dict[str, Any],
        memory_brief: str = "",
    ) -> VotingResult:
        """
        Conduct parallel voting across all specialists.
        
        Returns comprehensive VotingResult with consensus analysis.
        """
        start_time = time.time()
        
        # Check cache
        cache_key = self._get_cache_key(query, detected_domain)
        if cache_key in self.vote_cache:
            cached = self.vote_cache[cache_key]
            cached.reasoning = f"[CACHED] {cached.reasoning}"
            return cached
        
        # Prepare voting packet
        voting_packet = self._create_voting_packet(
            query, detected_domain, novelty_reasoning, memory_brief
        )
        
        # Collect votes in parallel
        votes = self._collect_votes_parallel(
            voting_packet, specialists, detected_domain
        )
        
        # Analyze votes
        result = self._analyze_votes(votes, detected_domain)
        
        # Calculate total processing time
        result.processing_time_ms = (time.time() - start_time) * 1000
        
        # Cache result
        self.vote_cache[cache_key] = result
        
        return result
    
    def _create_voting_packet(
        self,
        query: str,
        detected_domain: str,
        novelty_reasoning: str,
        memory_brief: str,
    ) -> str:
        """Create a standardized voting packet for specialists."""
        return f"""[EXPANSION VOTING REQUEST]

The ANM Router has detected a potential need for a new specialist domain.

QUERY: {query}

DETECTED DOMAIN: {detected_domain}

NOVELTY ANALYSIS:
{novelty_reasoning}

MEMORY CONTEXT:
{memory_brief[:500] if memory_brief else "None available"}

YOUR TASK:
Evaluate whether ANM needs a new '{detected_domain}' specialist module, or if existing specialists can handle this query adequately.

RESPONSE FORMAT (JSON):
{{
  "vote": "STRONG_YES" | "YES" | "UNCERTAIN" | "NO" | "STRONG_NO" | "ABSTAIN",
  "confidence": 0.0-1.0,
  "reasoning": "Your justification",
  "can_partially_handle": true/false,
  "suggested_collaboration": ["domain1", "domain2"]
}}

[END VOTING REQUEST]"""
    
    def _collect_votes_parallel(
        self,
        voting_packet: str,
        specialists: Dict[str, Any],
        detected_domain: str,
    ) -> List[Vote]:
        """Collect votes from all specialists in parallel."""
        votes: List[Vote] = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for domain_name, specialist in specialists.items():
                future = executor.submit(
                    self._get_specialist_vote,
                    domain_name,
                    specialist,
                    voting_packet,
                    detected_domain,
                )
                futures[future] = domain_name
            
            for future in as_completed(futures, timeout=self.timeout):
                domain_name = futures[future]
                try:
                    vote = future.result(timeout=5.0)
                    if vote:
                        votes.append(vote)
                except TimeoutError:
                    # Add abstain vote for timed-out specialists
                    votes.append(Vote(
                        specialist=domain_name,
                        vote_type=VoteType.ABSTAIN,
                        confidence=0.0,
                        reasoning="Specialist timed out",
                        processing_time_ms=self.timeout * 1000,
                    ))
                except Exception as e:
                    # Add abstain vote for failed specialists
                    votes.append(Vote(
                        specialist=domain_name,
                        vote_type=VoteType.ABSTAIN,
                        confidence=0.0,
                        reasoning=f"Error: {str(e)}",
                        processing_time_ms=0.0,
                    ))
        
        return votes
    
    def _get_specialist_vote(
        self,
        domain_name: str,
        specialist: Any,
        voting_packet: str,
        detected_domain: str,
    ) -> Optional[Vote]:
        """Get vote from a single specialist."""
        start_time = time.time()
        
        try:
            # Call specialist's run method
            if hasattr(specialist, 'run'):
                response = specialist.run(voting_packet)
            else:
                # Fallback for adapters
                response = str(specialist)
            
            # Parse response
            vote = self._parse_vote_response(
                domain_name, response, detected_domain
            )
            
            vote.processing_time_ms = (time.time() - start_time) * 1000
            return vote
            
        except Exception as e:
            return Vote(
                specialist=domain_name,
                vote_type=VoteType.ABSTAIN,
                confidence=0.0,
                reasoning=f"Failed to get vote: {str(e)}",
                processing_time_ms=(time.time() - start_time) * 1000,
            )
    
    def _parse_vote_response(
        self,
        domain_name: str,
        response: str,
        detected_domain: str,
    ) -> Vote:
        """Parse specialist response into a Vote object."""
        # Try to extract JSON from response
        try:
            import re
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                
                vote_str = data.get("vote", "ABSTAIN").upper()
                vote_type = VoteType[vote_str] if vote_str in VoteType.__members__ else VoteType.ABSTAIN
                
                return Vote(
                    specialist=domain_name,
                    vote_type=vote_type,
                    confidence=float(data.get("confidence", 0.5)),
                    reasoning=data.get("reasoning", "No reasoning provided"),
                    processing_time_ms=0.0,
                    can_partially_handle=data.get("can_partially_handle", False),
                    suggested_collaboration=data.get("suggested_collaboration", []),
                )
        except Exception:
            pass
        
        # Fallback: Heuristic parsing
        response_lower = response.lower()
        
        if "strong yes" in response_lower or "definitely need" in response_lower:
            vote_type = VoteType.STRONG_YES
            confidence = 0.9
        elif "yes" in response_lower or "need new" in response_lower or "cannot handle" in response_lower:
            vote_type = VoteType.YES
            confidence = 0.7
        elif "strong no" in response_lower or "definitely can handle" in response_lower:
            vote_type = VoteType.STRONG_NO
            confidence = 0.9
        elif "no" in response_lower or "can handle" in response_lower:
            vote_type = VoteType.NO
            confidence = 0.7
        elif "uncertain" in response_lower or "not sure" in response_lower:
            vote_type = VoteType.UNCERTAIN
            confidence = 0.5
        else:
            # Default based on domain relevance
            vote_type = VoteType.YES if domain_name != "general" else VoteType.NO
            confidence = 0.5
        
        return Vote(
            specialist=domain_name,
            vote_type=vote_type,
            confidence=confidence,
            reasoning=response[:200] if response else "No response",
            processing_time_ms=0.0,
        )
    
    def _analyze_votes(self, votes: List[Vote], detected_domain: str) -> VotingResult:
        """Analyze collected votes and determine consensus."""
        if not votes:
            return VotingResult(
                majority_yes=False,
                consensus_level="none",
                total_votes=0,
                yes_votes=0,
                no_votes=0,
                abstain_votes=0,
                weighted_score=0.0,
                confidence_band="low",
                votes=[],
                reasoning="No votes collected",
                processing_time_ms=0.0,
                quorum_reached=False,
                recommended_action="escalate",
            )
        
        # Count votes by type
        yes_votes = sum(1 for v in votes if v.vote_type in (VoteType.STRONG_YES, VoteType.YES))
        no_votes = sum(1 for v in votes if v.vote_type in (VoteType.STRONG_NO, VoteType.NO))
        abstain_votes = sum(1 for v in votes if v.vote_type in (VoteType.ABSTAIN, VoteType.UNCERTAIN))
        
        total_votes = len(votes)
        active_votes = total_votes - abstain_votes
        
        # Calculate weighted score
        weighted_score = sum(v.weight for v in votes) / max(active_votes, 1)
        
        # Check quorum
        quorum_reached = (active_votes / total_votes) >= self.quorum_percentage if total_votes > 0 else False
        
        # Determine majority
        majority_yes = yes_votes > no_votes and weighted_score > 0
        
        # Determine consensus level
        if active_votes == 0:
            consensus_level = "none"
        elif yes_votes == active_votes or no_votes == active_votes:
            consensus_level = "unanimous"
        elif abs(weighted_score) > 1.5:
            consensus_level = "strong"
        elif abs(weighted_score) > 0.8:
            consensus_level = "moderate"
        elif abs(weighted_score) > 0.3:
            consensus_level = "weak"
        else:
            consensus_level = "split"
        
        # Determine confidence band
        avg_confidence = sum(v.confidence for v in votes) / total_votes
        if avg_confidence >= 0.8:
            confidence_band = "high"
        elif avg_confidence >= 0.5:
            confidence_band = "medium"
        else:
            confidence_band = "low"
        
        # Determine recommended action
        if majority_yes and consensus_level in ("unanimous", "strong"):
            recommended_action = "expand"
        elif majority_yes and any(v.can_partially_handle for v in votes):
            recommended_action = "collaborate"
        elif not majority_yes and consensus_level in ("unanimous", "strong"):
            recommended_action = "handle_existing"
        else:
            recommended_action = "escalate"
        
        # Build reasoning
        reasoning_parts = [
            f"{yes_votes}/{total_votes} voted YES",
            f"{no_votes}/{total_votes} voted NO",
            f"Weighted score: {weighted_score:.2f}",
            f"Consensus: {consensus_level}",
        ]
        
        # Add collaboration suggestions
        all_suggestions = []
        for v in votes:
            all_suggestions.extend(v.suggested_collaboration)
        if all_suggestions:
            unique_suggestions = list(set(all_suggestions))
            reasoning_parts.append(f"Suggested collaborations: {', '.join(unique_suggestions)}")
        
        return VotingResult(
            majority_yes=majority_yes,
            consensus_level=consensus_level,
            total_votes=total_votes,
            yes_votes=yes_votes,
            no_votes=no_votes,
            abstain_votes=abstain_votes,
            weighted_score=weighted_score,
            confidence_band=confidence_band,
            votes=votes,
            reasoning="; ".join(reasoning_parts),
            processing_time_ms=0.0,
            quorum_reached=quorum_reached,
            recommended_action=recommended_action,
        )
    
    def _get_cache_key(self, query: str, detected_domain: str) -> str:
        """Generate cache key for voting result."""
        content = f"{query}|{detected_domain}"
        return hashlib.md5(content.encode()).hexdigest()
