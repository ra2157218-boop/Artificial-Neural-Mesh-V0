# ============================================================
# ANM V0-OpenSource — MEMORY HUB (EPISTEMIC HUMILITY)
#  
#  CRITICAL PRINCIPLE: Memories are OBSERVATIONS, not TRUTHS
#  
#  What we store:
#  - Behavioral patterns (what approaches work)
#  - Process observations (what happened)
#  - Success/failure signals (outcomes)
#  - Domain interaction history (not content)
#  
#  What we DON'T treat as truth:
#  - Query content (users may be wrong)
#  - Answer content (answers may be wrong)
#  - User corrections (users may be mistaken)
#  - Any claims about reality
#  
#  All memories are tagged as PAST OBSERVATIONS, not verified facts.
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import os
import logging

from anm.memory.diary_memory import DiaryMemory
from anm.memory.working_memory import WorkingMemory
from anm.memory.episodic_memory import EpisodicMemory
from anm.memory.semantic_memory import SemanticMemory
from anm.memory.meta_memory import MetaMemory


class ObservationType(Enum):
    """Type of observation stored in memory."""
    BEHAVIORAL = "behavioral"      # How ANM behaved
    PROCESS = "process"            # What process occurred
    OUTCOME = "outcome"            # Success/failure signal
    USER_INPUT = "user_input"      # User provided (NOT verified)
    PATTERN = "pattern"            # Detected pattern
    ERROR = "error"                # Error occurrence


@dataclass
class MemoryContext:
    """Rich context from all memory systems."""
    query: str
    episodic_observations: List[Dict[str, Any]]  # Past OBSERVATIONS
    meta_patterns: List[Dict[str, Any]]          # Behavioral PATTERNS
    recent_behaviors: List[Dict[str, Any]]       # Recent process BEHAVIORS
    working_snapshot: Dict[str, Any]
    relevance_score: float
    behavioral_insights: List[str]               # Process insights only
    epistemic_note: str = "All memories are OBSERVATIONS, not verified truths"


@dataclass
class BehavioralInsight:
    """
    An insight about ANM's BEHAVIOR, not content truth.
    """
    type: str  # pattern, process, weakness, strength, approach
    description: str
    confidence: float
    source_observations: int
    domains: List[str]
    timestamp: str
    epistemic_status: str = "behavioral"  # Always behavioral


class MemoryHub:
    """
    MEMORY HUB V2 — EPISTEMIC HUMILITY
    
    Core Principle: Store OBSERVATIONS and BEHAVIORS, not "truths".
    
    ✅ What we store and learn from:
    - Behavioral patterns (what approaches work)
    - Process observations (what happened)
    - Success/failure outcomes (objective signals)
    - Domain performance stats (objective metrics)
    - Error patterns (what went wrong)
    
    ❌ What we NEVER treat as truth:
    - Content from queries (users may be wrong)
    - Content from answers (answers may be wrong)
    - User "corrections" (users may be mistaken)
    - Any claims about reality from any source
    
    All memories are explicitly tagged as PAST OBSERVATIONS.
    """
    
    def __init__(
        self,
        diary_path: str = "anm_diary.txt",
        insights_path: str = ".anm_cache/behavioral_insights.json",
    ):
        # Core diary (backbone for all persistent memory)
        try:
            self.diary = DiaryMemory(diary_path)
        except Exception as e:
            logging.error(f"Failed to initialize DiaryMemory: {e}")
            raise
        
        # Memory layers with error handling
        try:
            self.working = WorkingMemory(max_items=128)
        except Exception as e:
            logging.error(f"Failed to initialize WorkingMemory: {e}")
            raise
        
        try:
            self.episodic = EpisodicMemory(self.diary)
        except Exception as e:
            logging.error(f"Failed to initialize EpisodicMemory: {e}")
            raise

        try:
            self.semantic = SemanticMemory(self.diary)
        except Exception as e:
            logging.error(f"Failed to initialize SemanticMemory: {e}")
            raise

        try:
            self.meta = MetaMemory(self.diary)
        except Exception as e:
            logging.error(f"Failed to initialize MetaMemory: {e}")
            raise

        # Behavioral insights storage with directory creation
        self.insights_path = insights_path
        try:
            os.makedirs(os.path.dirname(insights_path), exist_ok=True)
        except (OSError, PermissionError) as e:
            logging.warning(f"Cannot create insights directory: {e}. Using in-memory only.")
            self.insights_path = None
        
        self._insights: List[BehavioralInsight] = self._load_insights()
        
        # Session tracking (OBJECTIVE metrics)
        self._session_count = 0
        self._domain_interactions: Dict[str, int] = {}
        self._outcome_history: Dict[str, List[bool]] = {}  # Success/fail only
    
    # ============================================================
    #  UNIFIED CONTEXT RETRIEVAL
    # ============================================================
    
    def get_context(
        self,
        query: str,
        domains: Optional[List[str]] = None,
        limit_per_source: int = 5,
    ) -> MemoryContext:
        """
        Get BEHAVIORAL context from memory systems.
        
        Returns OBSERVATIONS and PATTERNS, not "facts".
        """
        # Episodic (past process observations)
        episodic_result = self.episodic.query(query, limit_blocks=limit_per_source)
        episodic_observations = episodic_result.get("blocks", [])
        
        # Mark all as observations
        for obs in episodic_observations:
            obs["epistemic_status"] = "past_observation"
        
        # Meta (behavioral patterns about ANM)
        meta_result = self.meta.search(text_query=query, limit=limit_per_source)
        meta_patterns = meta_result.get("blocks", [])
        
        # Recent behaviors
        recent_behaviors = self.episodic.recent_learning(limit=limit_per_source)
        
        # Working memory snapshot
        working_snapshot = self.working.snapshot()
        
        # Calculate relevance (structural, not content-based)
        relevance_score = self._calculate_structural_relevance(
            query, episodic_observations
        )
        
        # Extract behavioral insights
        behavioral_insights = self._get_behavioral_insights(query, domains)
        
        return MemoryContext(
            query=query,
            episodic_observations=episodic_observations,
            meta_patterns=meta_patterns,
            recent_behaviors=recent_behaviors,
            working_snapshot=working_snapshot,
            relevance_score=relevance_score,
            behavioral_insights=behavioral_insights,
        )
    
    def build_memory_brief(
        self,
        query: str,
        max_chars: int = 2000,
    ) -> str:
        """
        Build a concise BEHAVIORAL memory brief.
        
        This provides PROCESS context, not content "facts".
        """
        context = self.get_context(query)
        
        lines = [
            "[MEMORY CONTEXT - BEHAVIORAL OBSERVATIONS]",
            "⚠️ Note: These are PAST OBSERVATIONS, not verified truths",
        ]
        
        # Add behavioral insights (process-oriented)
        if context.behavioral_insights:
            lines.append("\n📋 Behavioral Patterns:")
            for insight in context.behavioral_insights[:3]:
                lines.append(f"  - {insight[:100]}")
        
        # Add domain performance (objective stats)
        performance = self.get_domain_performance()
        if performance:
            lines.append("\n📊 Domain Performance (objective metrics):")
            for domain, data in list(performance.items())[:3]:
                rate = data.get("success_rate", 0) * 100
                lines.append(f"  - {domain}: {rate:.0f}% success rate")
        
        # Add meta patterns (behavioral only)
        if context.meta_patterns:
            lines.append("\n🔍 Behavioral Patterns:")
            for pattern in context.meta_patterns[:2]:
                title = pattern.get("title", "")[:50]
                lines.append(f"  - {title}")
        
        brief = "\n".join(lines)
        return brief[:max_chars]
    
    # ============================================================
    #  BEHAVIORAL LEARNING (Not content learning)
    # ============================================================
    
    def record_session_behavior(
        self,
        query_type: str,
        domains: List[str],
        process_succeeded: bool,
        processing_time_ms: float,
        wot_steps: int,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record BEHAVIORAL observation from a session.
        
        We record:
        - Query TYPE (not content)
        - Which domains were involved
        - Whether process succeeded
        - Processing metrics
        
        We do NOT record:
        - Query content as truth
        - Answer content as knowledge
        - Any claims about reality
        """
        self._session_count += 1
        
        # Update domain interaction counts (objective metric)
        for domain in domains:
            self._domain_interactions[domain] = self._domain_interactions.get(domain, 0) + 1
        
        # Track outcome (success/failure signal only)
        for domain in domains:
            if domain not in self._outcome_history:
                self._outcome_history[domain] = []
            self._outcome_history[domain].append(process_succeeded)
            # Keep last 50 outcomes only
            self._outcome_history[domain] = self._outcome_history[domain][-50:]
        
        # Extract behavioral insights (process patterns only)
        if process_succeeded and len(domains) > 1:
            self._maybe_add_collaboration_insight(domains)
        
        # Log to meta memory (behavioral pattern)
        if self._session_count % 10 == 0:
            self._analyze_behavioral_patterns()
        
        return {
            "recorded": True,
            "observation_type": ObservationType.BEHAVIORAL.value,
            "session_count": self._session_count,
            "note": "Recorded PROCESS behavior, not content truth",
        }
    
    def record_error_observation(
        self,
        error_type: str,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record that an error OCCURRED.
        
        We record:
        - Error TYPE (not error content as truth)
        - Which domain was involved
        
        We do NOT record:
        - Error message content as fact
        - Any claims from error context
        """
        self.meta.log_drift(
            drift_type="error_occurrence",
            description=f"Error type: {error_type} in domain: {domain or 'unknown'}",
            extra={"domain": domain, "epistemic_status": "observed_error"},
        )
        
        # Add behavioral insight
        insight = BehavioralInsight(
            type="weakness",
            description=f"Error pattern: {error_type} in {domain or 'unknown'}",
            confidence=0.7,
            source_observations=1,
            domains=[domain] if domain else [],
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._insights.append(insight)
        self._save_insights()
        
        return {
            "recorded": True,
            "observation_type": ObservationType.ERROR.value,
            "note": "Recorded error OCCURRENCE, not error content as truth",
        }
    
    def record_feedback_signal(
        self,
        feedback_type: str,  # positive, negative
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record feedback SIGNAL (not content).
        
        We record:
        - That feedback was given (signal)
        - Type of feedback (positive/negative)
        
        We do NOT record:
        - Feedback content as truth
        - User corrections as verified facts
        """
        # Track as outcome signal
        if domain:
            if domain not in self._outcome_history:
                self._outcome_history[domain] = []
            self._outcome_history[domain].append(feedback_type == "positive")
        
        self._save_insights()
        
        return {
            "recorded": True,
            "observation_type": ObservationType.OUTCOME.value,
            "feedback_signal": feedback_type,
            "note": "Recorded feedback SIGNAL only, not content as truth",
        }
    
    # ============================================================
    #  BEHAVIORAL PATTERN RECOGNITION
    # ============================================================
    
    def get_domain_performance(self) -> Dict[str, Dict[str, Any]]:
        """
        Get OBJECTIVE performance metrics for each domain.
        
        These are measurable statistics, not content claims.
        """
        performance = {}
        
        for domain, count in self._domain_interactions.items():
            outcomes = self._outcome_history.get(domain, [])
            success_rate = sum(outcomes) / len(outcomes) if outcomes else 0.5
            
            performance[domain] = {
                "interactions": count,
                "success_rate": round(success_rate, 2),
                "performance_level": self._calculate_performance_level(count, success_rate),
                "epistemic_status": "objective_metric",
            }
        
        return performance
    
    def get_behavioral_strengths_weaknesses(self) -> Dict[str, List[str]]:
        """
        Identify ANM's behavioral strengths and weaknesses.
        
        Based on OBJECTIVE metrics, not content evaluation.
        """
        strengths = []
        weaknesses = []
        
        for domain, data in self.get_domain_performance().items():
            if data["success_rate"] >= 0.8 and data["interactions"] >= 5:
                strengths.append(
                    f"{domain} (success rate: {data['success_rate']*100:.0f}% - objective metric)"
                )
            elif data["success_rate"] < 0.6 and data["interactions"] >= 3:
                weaknesses.append(
                    f"{domain} (success rate: {data['success_rate']*100:.0f}% - objective metric)"
                )
        
        # Add from behavioral insights
        for insight in self._insights:
            if insight.type == "strength":
                strengths.append(f"{insight.description[:80]} (behavioral pattern)")
            elif insight.type == "weakness":
                weaknesses.append(f"{insight.description[:80]} (behavioral pattern)")
        
        return {
            "strengths": strengths[:10],
            "weaknesses": weaknesses[:10],
            "note": "Based on OBJECTIVE metrics and behavioral patterns",
        }
    
    def get_recommended_approach(
        self,
        query_type: str,
        domains: List[str],
    ) -> Dict[str, Any]:
        """
        Get recommended APPROACH based on past behaviors.
        
        Recommendations are about WHAT TO DO, not about content truth.
        """
        recommendations = []
        confidence = 0.5
        
        # Check domain performance (objective)
        performance = self.get_domain_performance()
        for domain in domains:
            if domain in performance:
                data = performance[domain]
                if data["success_rate"] < 0.6:
                    recommendations.append(
                        f"⚠️ {domain} has lower success rate - more verification needed"
                    )
                elif data["success_rate"] >= 0.9:
                    recommendations.append(f"✅ {domain} is strong - high confidence")
                    confidence += 0.1
        
        # Check for similar behavioral patterns
        context = self.get_context(query_type, domains, limit_per_source=3)
        if context.relevance_score > 0.7:
            recommendations.append("📚 Similar behavior patterns found - apply past approach")
            confidence += 0.2
        
        # Add behavioral insights
        for insight in self._insights:
            if insight.type == "approach" and any(d in insight.domains for d in domains):
                recommendations.append(f"💡 {insight.description[:80]}")
        
        return {
            "recommendations": recommendations,
            "confidence": min(confidence, 1.0),
            "based_on_sessions": self._session_count,
            "note": "Recommendations are about APPROACH, not content truth",
        }
    
    # ============================================================
    #  INTERNAL HELPERS
    # ============================================================
    
    def _calculate_structural_relevance(
        self,
        query: str,
        observations: List[Dict],
    ) -> float:
        """
        Calculate STRUCTURAL relevance (query type matching).
        
        NOT content-based relevance.
        """
        if not observations:
            return 0.0
        
        # Match on structural patterns, not content claims
        query_patterns = set(query.lower().split()[:5])  # First 5 words only
        score = 0.0
        
        for obs in observations:
            raw = obs.get("raw", "").lower()
            structural_match = sum(1 for w in query_patterns if w in raw[:100])
            score += structural_match / max(len(query_patterns), 1)
        
        return min(score / max(len(observations), 1), 1.0)
    
    def _calculate_performance_level(self, count: int, success_rate: float) -> str:
        """Calculate performance level (objective metric)."""
        if count < 3:
            return "insufficient_data"
        elif count < 10:
            return "learning" if success_rate < 0.7 else "developing"
        elif count < 50:
            return "developing" if success_rate < 0.8 else "proficient"
        else:
            return "proficient" if success_rate < 0.9 else "expert"
    
    def _maybe_add_collaboration_insight(self, domains: List[str]) -> None:
        """Add insight about domain collaboration (behavioral pattern)."""
        domain_combo = "+".join(sorted(domains))
        
        existing = [
            i for i in self._insights
            if i.type == "approach" and domain_combo in i.description
        ]
        
        if existing:
            existing[0].confidence = min(existing[0].confidence + 0.1, 1.0)
            existing[0].source_observations += 1
        else:
            insight = BehavioralInsight(
                type="approach",
                description=f"Domain collaboration {domain_combo} works well (behavioral pattern)",
                confidence=0.6,
                source_observations=1,
                domains=domains,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            self._insights.append(insight)
        
        self._save_insights()
    
    def _analyze_behavioral_patterns(self) -> None:
        """Analyze behavioral patterns periodically."""
        sw = self.get_behavioral_strengths_weaknesses()
        
        if sw["strengths"]:
            self.meta.log_pattern(
                title="Behavioral Strengths",
                pattern=f"Strong domains (objective): {', '.join(sw['strengths'][:5])}",
                modules=["MemoryHub"],
            )
        
        if sw["weaknesses"]:
            self.meta.log_pattern(
                title="Areas for Improvement",
                pattern=f"Weaker domains (objective): {', '.join(sw['weaknesses'][:5])}",
                modules=["MemoryHub"],
            )
    
    def _get_behavioral_insights(
        self,
        query: str,
        domains: Optional[List[str]],
    ) -> List[str]:
        """Get BEHAVIORAL insights for the query."""
        relevant = []
        
        for insight in self._insights:
            # Check domain match
            if domains and insight.domains:
                if any(d in domains for d in insight.domains):
                    relevant.append(f"[BEHAVIOR] {insight.description}")
                    continue
        
        return relevant[:5]
    
    def _load_insights(self) -> List[BehavioralInsight]:
        """Load behavioral insights from disk."""
        if not self.insights_path or not os.path.exists(self.insights_path):
            return []
        
        try:
            with open(self.insights_path, "r") as f:
                data = json.load(f)
                return [
                    BehavioralInsight(**item) for item in data
                ]
        except Exception as e:
            logging.warning(f"Failed to load behavioral insights: {e}")
            return []
    
    def _save_insights(self) -> None:
        """Save behavioral insights to disk."""
        if not self.insights_path:
            # In-memory only mode - skip saving
            return
        
        try:
            data = [
                {
                    "type": i.type,
                    "description": i.description,
                    "confidence": i.confidence,
                    "source_observations": i.source_observations,
                    "domains": i.domains,
                    "timestamp": i.timestamp,
                    "epistemic_status": i.epistemic_status,
                }
                for i in self._insights[-100:]
            ]
            with open(self.insights_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.warning(f"Failed to save behavioral insights: {e}")
    
    # ============================================================
    #  WORKING MEMORY INTEGRATION
    # ============================================================
    
    def add_to_working(
        self,
        domain: str,
        role: str,
        note: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add item to working memory (session context)."""
        self.working.add(domain=domain, role=role, note=note, meta=meta)
    
    def clear_working(self) -> None:
        """Clear working memory for new session."""
        self.working.clear()
    
    def get_working_snapshot(self) -> Dict[str, Any]:
        """Get current working memory state."""
        return self.working.snapshot()
    
    # ============================================================
    #  STATS & REPORTING
    # ============================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics (objective metrics)."""
        return {
            "session_count": self._session_count,
            "domain_interactions": self._domain_interactions,
            "insights_count": len(self._insights),
            "performance": self.get_domain_performance(),
            "behavioral_sw": self.get_behavioral_strengths_weaknesses(),
            "epistemic_note": "All stats are OBJECTIVE metrics, not content claims",
        }
    
    def get_self_report(self) -> str:
        """Generate a behavioral self-report."""
        stats = self.get_stats()
        sw = stats["behavioral_sw"]
        
        lines = [
            "=" * 50,
            "ANM BEHAVIORAL REPORT",
            "⚠️ All observations are PAST BEHAVIORS, not truths",
            "=" * 50,
            f"\n📊 Sessions Observed: {stats['session_count']}",
            f"💡 Behavioral Insights: {stats['insights_count']}",
            "",
        ]
        
        if sw["strengths"]:
            lines.append("✅ Behavioral Strengths:")
            for s in sw["strengths"][:5]:
                lines.append(f"   - {s}")
        
        if sw["weaknesses"]:
            lines.append("\n⚠️ Areas for Improvement:")
            for w in sw["weaknesses"][:5]:
                lines.append(f"   - {w}")
        
        lines.append("")
        lines.append("📈 Domain Performance (Objective Metrics):")
        for domain, data in stats["performance"].items():
            level = data.get("performance_level", "unknown")
            rate = data.get("success_rate", 0) * 100
            lines.append(f"   - {domain}: {level} ({rate:.0f}% success)")
        
        lines.append("")
        lines.append("=" * 50)
        lines.append("Note: These are BEHAVIORAL patterns, not truth claims")
        
        return "\n".join(lines)
