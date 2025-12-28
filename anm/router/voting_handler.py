# ============================================================
# ANM V0-OpenSource — VOTING HANDLER
#  Extracted from Router for better modularity
# ============================================================

from __future__ import annotations
from typing import Dict, Any, Optional
import logging


class VotingHandler:
    """
    Handles specialists voting system for Router.
    
    Conducts voting among specialists to determine if a new domain
    should be created. Uses V2 VotingSystemV2 with fallback to heuristic voting.
    """
    
    def __init__(self, specialists: Dict[str, Any], config: Dict[str, Any] = None):
        """
        Initialize VotingHandler.
        
        Args:
            specialists: Dict of specialist adapters (e.g., {"general": adapter, ...})
            config: Router configuration dict
        """
        self.specialists = specialists
        self.config = config or {}
        self._logger = logging.getLogger(__name__)
    
    def vote(
        self,
        user_query: str,
        detected_domain: Optional[str],
        novelty_reasoning: str,
        memory_brief: str,
    ) -> Dict[str, Any]:
        """
        Conduct voting among specialists.
        
        Uses V2 VotingSystemV2 for parallel async voting with weighted consensus.
        Falls back to simple heuristic voting if unavailable.
        
        Args:
            user_query: The user's query
            detected_domain: Domain detected by novelty handler
            novelty_reasoning: Reasoning from novelty detection
            memory_brief: Memory context brief
            
        Returns:
            Dict with voting results and consensus level
        """
        if not detected_domain:
            return {"majority_yes": False, "votes": {}, "reasoning": "No domain detected"}
        
        # Try to use V2 Voting System (parallel, weighted)
        try:
            from anm.expansion.core.voting_system import VotingSystemV2
            
            voting_system = VotingSystemV2(timeout_seconds=30.0)
            
            result = voting_system.conduct_vote(
                query=user_query,
                detected_domain=detected_domain,
                novelty_reasoning=novelty_reasoning,
                specialists=self.specialists,
                memory_brief=memory_brief,
            )
            
            return {
                "majority_yes": result.majority_yes,
                "votes": {v.specialist: v.vote_type.value for v in result.votes},
                "yes_count": result.yes_votes,
                "no_count": result.no_votes,
                "consensus_level": result.consensus_level,
                "confidence_band": result.confidence_band,
                "weighted_score": result.weighted_score,
                "reasoning": result.reasoning,
                "voting_method": "v2_parallel",
                "recommended_action": result.recommended_action,
            }
        except (ImportError, AttributeError, TypeError, ValueError) as e:
            # Fall back to V1 heuristic voting if V2 voting system fails
            if self.config.get("verbose", False):
                self._logger.debug(f"VotingSystemV2 unavailable, using fallback: {e}")
        
        # V1 Fallback: Simple heuristic voting
        return self._heuristic_vote()
    
    def _heuristic_vote(self) -> Dict[str, Any]:
        """
        Fallback heuristic voting system.
        
        Returns:
            Dict with voting results
        """
        specialists_to_vote = [
            (domain_name, adapter)
            for domain_name, adapter in self.specialists.items()
            if adapter is not None
        ]
        
        votes = {}
        yes_count = 0
        no_count = 0
        
        # Heuristic: specialists vote YES unless they're "general"
        for domain_name, specialist_adapter in specialists_to_vote:
            response = "YES" if domain_name != "general" else "NO"
            votes[domain_name] = response
            if response == "YES":
                yes_count += 1
            else:
                no_count += 1
        
        majority_yes = yes_count > no_count
        
        return {
            "majority_yes": majority_yes,
            "votes": votes,
            "yes_count": yes_count,
            "no_count": no_count,
            "reasoning": f"{yes_count} specialists voted YES, {no_count} voted NO",
            "voting_method": "v1_heuristic",
        }

