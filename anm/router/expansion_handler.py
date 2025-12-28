# ============================================================
# ANM V0-OpenSource — EXPANSION HANDLER
#  Extracted from Router for better modularity
# ============================================================

from __future__ import annotations
from typing import Dict, Any, Optional
import logging


class ExpansionHandler:
    """
    Handles expansion engine triggering for Router.
    
    Triggers the expansion engine when a new domain is needed.
    Uses V2 ExpansionEngineV2 with fallback to V1.
    """
    
    def __init__(self, specialists: Dict[str, Any], config: Dict[str, Any] = None):
        """
        Initialize ExpansionHandler.
        
        Args:
            specialists: Dict of specialist adapters
            config: Router configuration dict
        """
        self.specialists = specialists
        self.config = config or {}
        self._logger = logging.getLogger(__name__)
    
    def trigger(
        self,
        user_query: str,
        detected_domain: Optional[str],
        novelty_reasoning: str,
        voting_result: Dict[str, Any],
        memory_brief: str,
    ) -> Dict[str, Any]:
        """
        Trigger expansion engine.
        
        Uses V2 ExpansionEngineV2 with full pipeline (discovery, training, etc).
        Falls back to V1 if unavailable.
        
        Args:
            user_query: The user's query
            detected_domain: Domain detected by novelty handler
            novelty_reasoning: Reasoning from novelty detection
            voting_result: Results from voting system
            memory_brief: Memory context brief
            
        Returns:
            Dict with expansion status and results
        """
        # Try V2 Expansion Engine first (maximum level)
        try:
            from anm.expansion import ExpansionEngineV2, ExpansionConfig
            
            expansion_engine = ExpansionEngineV2(ExpansionConfig(
                use_qlora=True,
                require_human_approval=True,
                create_checkpoints=True,
            ))
            
            # Run expansion (synchronous)
            expansion_result = expansion_engine.run_sync(
                query=user_query,
                memory_brief=memory_brief,
                specialists=self.specialists,
            )
            
            return {
                "expansion_triggered": True,
                "expansion_result": expansion_result,
                "engine_version": "v2",
            }
        except (ImportError, AttributeError, TypeError, ValueError) as e_v2:
            # Try V1 Expansion Engine as fallback
            try:
                from anm.expansion.expansion_engine import ExpansionEngine
                
                expansion_engine = ExpansionEngine()
                expansion_result = expansion_engine.start_expansion(
                    user_query=user_query,
                    new_domain=detected_domain,
                    novelty_reasoning=novelty_reasoning,
                    voting_result=voting_result,
                )
                
                return {
                    "expansion_triggered": True,
                    "expansion_result": expansion_result,
                    "engine_version": "v1",
                }
            except (ImportError, AttributeError, TypeError, ValueError) as e_v1:
                self._logger.warning(
                    f"Expansion Engine failed (V2: {type(e_v2).__name__}, V1: {type(e_v1).__name__})"
                )
                return {
                    "expansion_triggered": False,
                    "error": f"V2: {type(e_v2).__name__}, V1: {type(e_v1).__name__}",
                    "message": "Expansion Engine failed",
                }

