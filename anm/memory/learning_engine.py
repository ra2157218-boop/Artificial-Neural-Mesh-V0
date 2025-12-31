# ============================================================
# ANM V0-OpenSource — LEARNING ENGINE (EPISTEMIC HUMILITY)
#  
#  CRITICAL PRINCIPLE: Learn PATTERNS, not "truths"
#  
#  What ANM learns:
#  - BEHAVIORAL patterns (what approaches work)
#  - PROCESS patterns (which specialist combos succeed)
#  - ERROR patterns (what causes failures)
#  - PERFORMANCE patterns (success rates per domain)
#  
#  What ANM does NOT learn as truth:
#  - Query content (may contain false claims)
#  - Answer content (may be wrong)
#  - User statements (users can be mistaken)
#  
#  All observations are marked as:
#  - "OBSERVED" not "TRUE"
#  - "PAST" not "FACT"
#  - "CLAIMED" not "VERIFIED"
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
import os
import hashlib
import logging


class EpistemicStatus(Enum):
    """
    Epistemic status of learned information.
    ANM NEVER treats learned content as absolute truth.
    """
    OBSERVED = "observed"        # Saw this happen, no truth claim
    INFERRED = "inferred"        # Pattern detected, may be coincidence
    BEHAVIORAL = "behavioral"    # Process worked/didn't work
    USER_CLAIMED = "user_claimed"  # User said this, NOT verified
    UNVERIFIED = "unverified"    # No verification possible
    TENTATIVE = "tentative"      # Weak evidence
    STATISTICAL = "statistical"  # Based on success rate patterns


@dataclass
class LearningEvent:
    """A learning event to process."""
    type: str  # behavior, error, feedback, pattern
    data: Dict[str, Any]
    epistemic_status: EpistemicStatus = EpistemicStatus.OBSERVED
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    processed: bool = False


@dataclass
class StrategyRule:
    """
    A learned strategy rule.
    
    NOTE: Strategies are about WHAT WORKS, not about content truth.
    """
    condition: str          # When this BEHAVIOR applies
    action: str             # What approach to take
    confidence: float       # Statistical confidence
    success_count: int      # Times this approach succeeded
    failure_count: int      # Times this approach failed
    domains: List[str]      # Related domains
    epistemic_status: EpistemicStatus = EpistemicStatus.BEHAVIORAL


class LearningEngine:
    """
    LEARNING ENGINE V2 — EPISTEMIC HUMILITY
    
    Core Principle: Learn HOW TO BEHAVE, not WHAT IS TRUE.
    
    ✅ What we learn:
    - Query TYPE patterns (explanation, calculation, etc.)
    - Which entry specialists work for which query types
    - Which domain combinations collaborate well
    - What approaches lead to successful outcomes
    - Error patterns to avoid
    - Processing efficiency patterns
    
    ❌ What we NEVER learn as truth:
    - Content from user queries (users may be wrong)
    - Content from answers (answers may be wrong)
    - User "corrections" (users may be mistaken)
    - Claims about reality from any source
    
    All learned information is tagged with EpistemicStatus.
    """
    
    def __init__(
        self,
        storage_path: str = ".anm_cache/learning",
    ):
        self.storage_path = storage_path
        try:
            os.makedirs(storage_path, exist_ok=True)
        except (OSError, PermissionError) as e:
            logging.warning(f"Cannot create learning storage directory {storage_path}: {e}. Using in-memory only.")
            self.storage_path = None
        
        # Behavioral patterns only
        self._strategy_rules: List[StrategyRule] = self._load_strategies()
        self._behavioral_patterns: Dict[str, Dict[str, Any]] = self._load_behavioral_patterns()
        self._pending_events: List[LearningEvent] = []
        
        # Statistics (these are OBJECTIVE observations)
        self._total_learnings = 0
        self._session_learnings = 0
    
    # ============================================================
    #  BEHAVIORAL LEARNING (What approaches work)
    # ============================================================
    
    def learn_from_behavior(
        self,
        query_type: str,
        domains: List[str],
        entry_specialist: str,
        process_succeeded: bool,
        processing_time_ms: float,
        wot_steps: int,
    ) -> Dict[str, Any]:
        """
        Learn from BEHAVIORAL outcome (what approach worked).
        
        This learns:
        - Query type → entry specialist effectiveness
        - Domain collaboration success rates
        - Processing efficiency patterns
        
        This does NOT learn:
        - Whether query content was true
        - Whether answer content was true
        - Any claims about reality
        """
        learnings = []
        
        # Pattern key is about BEHAVIOR, not content
        pattern_key = f"behavior_{query_type}_{'+'.join(sorted(domains))}"
        
        if pattern_key not in self._behavioral_patterns:
            self._behavioral_patterns[pattern_key] = {
                "query_type": query_type,
                "domains": domains,
                "total_attempts": 0,
                "successes": 0,
                "avg_time_ms": 0.0,
                "avg_steps": 0.0,
                "entry_specialists": {},  # Track which starters work
                "epistemic_status": EpistemicStatus.BEHAVIORAL.value,
            }
        
        pattern = self._behavioral_patterns[pattern_key]
        pattern["total_attempts"] += 1
        if process_succeeded:
            pattern["successes"] += 1
        
        # Update running averages
        n = pattern["total_attempts"]
        pattern["avg_time_ms"] = ((n - 1) * pattern["avg_time_ms"] + processing_time_ms) / n
        pattern["avg_steps"] = ((n - 1) * pattern["avg_steps"] + wot_steps) / n
        
        # Track entry specialist effectiveness
        if entry_specialist not in pattern["entry_specialists"]:
            pattern["entry_specialists"][entry_specialist] = {"success": 0, "fail": 0}
        if process_succeeded:
            pattern["entry_specialists"][entry_specialist]["success"] += 1
        else:
            pattern["entry_specialists"][entry_specialist]["fail"] += 1
        
        # Maybe create behavioral strategy rule
        if pattern["total_attempts"] >= 5:
            success_rate = pattern["successes"] / pattern["total_attempts"]
            
            if success_rate >= 0.8:
                best_entry = max(
                    pattern["entry_specialists"].items(),
                    key=lambda x: x[1]["success"] / max(x[1]["success"] + x[1]["fail"], 1),
                )
                
                rule = StrategyRule(
                    condition=f"Query type: {query_type}, Domains: {domains}",
                    action=f"Start with {best_entry[0]} (behavioral pattern)",
                    confidence=success_rate,
                    success_count=pattern["successes"],
                    failure_count=pattern["total_attempts"] - pattern["successes"],
                    domains=domains,
                    epistemic_status=EpistemicStatus.BEHAVIORAL,
                )
                
                # Add if not duplicate
                if not any(r.condition == rule.condition for r in self._strategy_rules):
                    self._strategy_rules.append(rule)
                    learnings.append(f"New behavioral pattern: {rule.action}")
        
        self._total_learnings += 1
        self._session_learnings += 1
        self._save_all()
        
        return {
            "learned": True,
            "learning_type": "behavioral",
            "epistemic_status": EpistemicStatus.BEHAVIORAL.value,
            "pattern_stats": {
                "success_rate": pattern["successes"] / max(pattern["total_attempts"], 1),
                "total_attempts": pattern["total_attempts"],
            },
            "new_learnings": learnings,
            "note": "This is a BEHAVIORAL pattern, not a truth claim about content",
        }
    
    def learn_from_collaboration(
        self,
        trace: List[Dict[str, Any]],
        process_succeeded: bool,
    ) -> Dict[str, Any]:
        """
        Learn from specialist collaboration patterns.
        
        This learns:
        - Which specialist sequences work well
        - Effective handoff patterns
        
        This does NOT learn anything about content truth.
        """
        if not trace:
            return {"learned": False}
        
        # Extract specialist sequence (BEHAVIORAL pattern)
        sequence = [step.get("specialist", "unknown") for step in trace]
        sequence_key = "collab_" + hashlib.md5("->".join(sequence).encode()).hexdigest()[:8]
        
        pattern = self._behavioral_patterns.setdefault(
            sequence_key,
            {
                "type": "collaboration",
                "sequence": sequence,
                "success": 0,
                "fail": 0,
                "epistemic_status": EpistemicStatus.BEHAVIORAL.value,
            },
        )
        
        if process_succeeded:
            pattern["success"] += 1
        else:
            pattern["fail"] += 1
        
        return {
            "learned": True,
            "learning_type": "collaboration",
            "epistemic_status": EpistemicStatus.BEHAVIORAL.value,
            "sequence": sequence,
            "success_rate": pattern["success"] / max(pattern["success"] + pattern["fail"], 1),
        }
    
    # ============================================================
    #  ERROR PATTERN LEARNING
    # ============================================================
    
    def learn_from_error_pattern(
        self,
        error_type: str,
        error_context: str,  # WHAT happened, not truth about content
        domain: Optional[str],
    ) -> Dict[str, Any]:
        """
        Learn error PATTERNS to avoid them.
        
        This learns:
        - What types of errors occur in what contexts
        - Patterns that lead to failures
        
        This does NOT learn:
        - Whether error messages contain true claims
        - Content from error context
        """
        error_key = f"error_pattern_{error_type}_{domain or 'general'}"
        
        if error_key not in self._behavioral_patterns:
            self._behavioral_patterns[error_key] = {
                "type": "error_pattern",
                "error_type": error_type,
                "domain": domain,
                "occurrence_count": 0,
                "contexts_hash": [],  # Store hashes, not content
                "epistemic_status": EpistemicStatus.OBSERVED.value,
            }
        
        pattern = self._behavioral_patterns[error_key]
        pattern["occurrence_count"] += 1
        
        # Store context hash only (no content learning)
        context_hash = hashlib.md5(error_context.encode()).hexdigest()[:8]
        pattern["contexts_hash"].append(context_hash)
        pattern["contexts_hash"] = pattern["contexts_hash"][-10:]  # Keep recent
        
        # Create avoidance rule if pattern is common
        if pattern["occurrence_count"] >= 3:
            rule = StrategyRule(
                condition=f"Error pattern: {error_type} in {domain}",
                action=f"Add validation before {domain or 'processing'} (error avoidance)",
                confidence=0.7,
                success_count=0,
                failure_count=pattern["occurrence_count"],
                domains=[domain] if domain else [],
                epistemic_status=EpistemicStatus.BEHAVIORAL,
            )
            
            if not any(r.condition == rule.condition for r in self._strategy_rules):
                self._strategy_rules.append(rule)
        
        self._save_all()
        
        return {
            "learned": True,
            "learning_type": "error_pattern",
            "epistemic_status": EpistemicStatus.OBSERVED.value,
            "occurrence_count": pattern["occurrence_count"],
            "note": "Learning error PATTERN, not content truth",
        }
    
    # ============================================================
    #  FEEDBACK HANDLING (with epistemic caution)
    # ============================================================
    
    def record_feedback(
        self,
        feedback_type: str,  # positive, negative, correction
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record feedback SIGNAL (not content).
        
        We record:
        - That positive/negative feedback was given (behavioral signal)
        - Which domain was involved
        
        We do NOT learn:
        - Feedback content as truth
        - User corrections as verified facts
        - User claims as reality
        """
        feedback_key = f"feedback_{feedback_type}_{domain or 'general'}"
        
        pattern = self._behavioral_patterns.setdefault(
            feedback_key,
            {
                "type": "feedback_signal",
                "feedback_type": feedback_type,
                "domain": domain,
                "count": 0,
                "epistemic_status": EpistemicStatus.USER_CLAIMED.value,
                "note": "Feedback recorded as SIGNAL, not verified truth",
            },
        )
        
        pattern["count"] += 1
        self._save_all()
        
        return {
            "recorded": True,
            "feedback_type": feedback_type,
            "epistemic_status": EpistemicStatus.USER_CLAIMED.value,
            "note": "Recorded feedback SIGNAL only. Content NOT treated as truth.",
        }
    
    # ============================================================
    #  STRATEGY RECOMMENDATIONS (Behavioral only)
    # ============================================================
    
    def get_strategy(
        self,
        query_type: str,
        domains: List[str],
    ) -> Dict[str, Any]:
        """
        Get recommended BEHAVIORAL strategy.
        
        Recommendations are about:
        - What approaches have worked before
        - What patterns to follow
        - What to avoid
        
        NOT about truth claims.
        """
        recommendations = []
        confidence = 0.5
        
        # Check behavioral patterns
        pattern_key = f"behavior_{query_type}_{'+'.join(sorted(domains))}"
        
        if pattern_key in self._behavioral_patterns:
            pattern = self._behavioral_patterns[pattern_key]
            if pattern.get("total_attempts", 0) >= 3:
                success_rate = pattern["successes"] / pattern["total_attempts"]
                
                if success_rate >= 0.8:
                    recommendations.append(
                        f"✅ This approach has {success_rate*100:.0f}% success rate (behavioral pattern)"
                    )
                    confidence += 0.2
                elif success_rate < 0.5:
                    recommendations.append(
                        f"⚠️ This approach has low success ({success_rate*100:.0f}%) - try different entry"
                    )
                    confidence -= 0.1
                
                # Recommend best entry (based on BEHAVIOR, not content)
                if pattern.get("entry_specialists"):
                    best = max(
                        pattern["entry_specialists"].items(),
                        key=lambda x: x[1]["success"] / max(x[1]["success"] + x[1]["fail"], 1),
                    )
                    recommendations.append(f"💡 Best entry approach: {best[0]}")
        
        # Check for error patterns to avoid
        for key, pattern in self._behavioral_patterns.items():
            if pattern.get("type") == "error_pattern":
                if pattern.get("domain") in domains:
                    if pattern["occurrence_count"] >= 3:
                        recommendations.append(
                            f"⚠️ Error pattern detected in {pattern.get('domain')} - extra validation needed"
                        )
        
        # Apply strategy rules (all behavioral)
        for rule in self._strategy_rules:
            if any(d in rule.domains for d in domains) and rule.confidence >= 0.6:
                recommendations.append(f"📋 {rule.action}")
                confidence += rule.confidence * 0.1
        
        return {
            "recommendations": recommendations[:8],
            "confidence": min(max(confidence, 0.0), 1.0),
            "query_type": query_type,
            "epistemic_note": "All recommendations are BEHAVIORAL patterns, not truth claims",
        }
    
    def get_optimal_entry_specialist(
        self,
        query_type: str,
        domains: List[str],
        available_specialists: List[str],
    ) -> str:
        """Predict optimal entry based on BEHAVIORAL patterns."""
        pattern_key = f"behavior_{query_type}_{'+'.join(sorted(domains))}"
        
        if pattern_key in self._behavioral_patterns:
            pattern = self._behavioral_patterns[pattern_key]
            if pattern.get("entry_specialists"):
                candidates = [
                    (k, v) for k, v in pattern["entry_specialists"].items()
                    if k in available_specialists
                ]
                if candidates:
                    best = max(
                        candidates,
                        key=lambda x: x[1]["success"] / max(x[1]["success"] + x[1]["fail"], 1),
                        default=None,
                    )
                    if best and best[1]["success"] >= 2:
                        return best[0]
        
        # Default to first domain specialist
        for domain in domains:
            if domain in available_specialists:
                return domain
        
        return available_specialists[0] if available_specialists else "general"
    
    # ============================================================
    #  QUERY CLASSIFICATION (Pattern matching, not content)
    # ============================================================
    
    def classify_query_type(self, query: str) -> str:
        """
        Classify query by STRUCTURE, not content truth.
        
        This is pattern matching on query FORM, not evaluation of content.
        """
        q = query.lower()
        
        # Structural patterns (not content evaluation)
        if any(w in q for w in ["what is", "define", "explain", "describe"]):
            return "explanation"
        elif any(w in q for w in ["how to", "how do", "how can", "steps"]):
            return "howto"
        elif any(w in q for w in ["why", "reason", "cause"]):
            return "reasoning"
        elif any(w in q for w in ["compare", "difference", "vs", "versus"]):
            return "comparison"
        elif any(w in q for w in ["calculate", "compute", "solve", "equation"]):
            return "calculation"
        elif any(w in q for w in ["code", "program", "function", "implement"]):
            return "coding"
        elif any(w in q for w in ["simulate", "visualize", "show", "demonstrate"]):
            return "simulation"
        else:
            return "general"
    
    # ============================================================
    #  PERSISTENCE (Behavioral patterns only)
    # ============================================================
    
    def _save_all(self) -> None:
        """Save all behavioral patterns."""
        if not self.storage_path:
            # In-memory only mode - skip saving
            return
        
        try:
            # Save strategies
            with open(os.path.join(self.storage_path, "strategies.json"), "w") as f:
                json.dump([
                    {
                        "condition": r.condition,
                        "action": r.action,
                        "confidence": r.confidence,
                        "success_count": r.success_count,
                        "failure_count": r.failure_count,
                        "domains": r.domains,
                        "epistemic_status": r.epistemic_status.value,
                    }
                    for r in self._strategy_rules[-50:]
                ], f, indent=2)
            
            # Save behavioral patterns
            with open(os.path.join(self.storage_path, "behavioral_patterns.json"), "w") as f:
                limited = dict(list(self._behavioral_patterns.items())[-100:])
                json.dump(limited, f, indent=2)
                
        except Exception:
            pass
    
    def _load_strategies(self) -> List[StrategyRule]:
        """Load saved strategies."""
        if not self.storage_path:
            return []
        
        path = os.path.join(self.storage_path, "strategies.json")
        if not os.path.exists(path):
            return []
        
        try:
            with open(path, "r") as f:
                data = json.load(f)
                return [
                    StrategyRule(
                        condition=item["condition"],
                        action=item["action"],
                        confidence=item["confidence"],
                        success_count=item["success_count"],
                        failure_count=item["failure_count"],
                        domains=item["domains"],
                        epistemic_status=EpistemicStatus(item.get("epistemic_status", "behavioral")),
                    )
                    for item in data
                ]
        except Exception:
            return []
    
    def _load_behavioral_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load saved behavioral patterns."""
        if not self.storage_path:
            return {}
        
        path = os.path.join(self.storage_path, "behavioral_patterns.json")
        if not os.path.exists(path):
            return {}
        
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    
    # ============================================================
    #  STATS
    # ============================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        return {
            "total_learnings": self._total_learnings,
            "session_learnings": self._session_learnings,
            "strategy_rules": len(self._strategy_rules),
            "behavioral_patterns": len(self._behavioral_patterns),
            "epistemic_note": "All learnings are BEHAVIORAL patterns, not truth claims",
        }
    
    def reset_session(self) -> None:
        """Reset session-specific counters."""
        self._session_learnings = 0
