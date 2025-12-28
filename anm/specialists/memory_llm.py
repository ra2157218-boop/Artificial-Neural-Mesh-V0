# ============================================================
#  ANM V0-OpenSource — Memory Specialist
#  Episodic Memory & Diary Integration
# ============================================================

"""
ANM Memory Specialist - Memory retrieval and integration.

Capabilities:
- Episodic memory retrieval
- Semantic pattern matching
- Diary context extraction
- Working memory management
- Multi-modal memory access
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import re

from anm.specialists.base import (
    BaseSpecialist,
    SpecialistConfig,
    SpecialistDomain,
    run_model,
)

# Import prompt
try:
    from anm.utils.prompts import MEMORY_PROMPT
except ImportError:
    MEMORY_PROMPT = ""

# Import memory systems
try:
    from anm.memory.diary_memory import DiaryMemory
    DIARY_AVAILABLE = True
except ImportError:
    DiaryMemory = None
    DIARY_AVAILABLE = False

__all__ = ["MemoryLLM"]


class MemoryLLM(BaseSpecialist):
    """
    ANM V0-OpenSource Memory Specialist.
    
    Handles memory operations including:
    - Episodic memory (past interactions)
    - Semantic memory (patterns, knowledge)
    - Visual memory (image-tagged episodes)
    - Simulation memory (past simulations)
    - Working memory (recent context)
    
    Key principle: All memory is PAST CONTEXT only,
    not guaranteed current truth.
    """
    
    REQUIRED_PREFIX = "In the past, ANM"
    
    def __init__(
        self,
        config: Optional[SpecialistConfig] = None,
        diary: Optional[Any] = None,
        **kwargs,
    ):
        super().__init__(config=config, **kwargs)
        
        # Initialize diary
        if diary:
            self.diary = diary
        elif DIARY_AVAILABLE:
            self.diary = DiaryMemory()
        else:
            self.diary = None
        # #region agent log
        try:
            import json
            import time
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "M1", "location": "memory_llm.py:__init__", "message": "MemoryLLM initialized", "data": {"DIARY_AVAILABLE": DIARY_AVAILABLE, "has_diary": self.diary is not None, "diary_type": type(self.diary).__name__ if self.diary else "None", "diary_path": str(self.diary.diary_path) if self.diary else "None"}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
    
    @property
    def domain(self) -> SpecialistDomain:
        return SpecialistDomain.MEMORY
    
    def _get_system_prompt(self) -> str:
        # Use MEMORY_PROMPT from prompts.py (single source of truth)
        return MEMORY_PROMPT if MEMORY_PROMPT else ""
    
    def query(
        self,
        user_query: str,
        limit_blocks: int = 8,
        use_recent_fallback: bool = True,
    ) -> Dict[str, Any]:
        """
        Query memory systems for relevant context.
        
        Args:
            user_query: The query to search for
            limit_blocks: Max memory blocks to retrieve
            use_recent_fallback: Fall back to recent if no match
            
        Returns:
            Dict with structured memory context
        """
        result = {
            "query": user_query,
            "blocks": [],
            "memory_summary": "",
            "highlights": [],
            "episodic": [],
            "semantic": [],
            "visual": [],
            "audio": [],
            "simulation": [],
            "meta": {},
            "working_memory": {},
        }
        
        if not self.diary:
            result["memory_summary"] = "No diary memory available."
            return result
        
        try:
            # Query diary using search_blocks
            blocks = self.diary.search_blocks(
                text_query=user_query,
                limit=limit_blocks
            )
            
            if not blocks and use_recent_fallback:
                blocks = self.diary.recent_blocks(limit=limit_blocks)
            
            result["blocks"] = blocks
            
            # Categorize blocks
            for block in blocks:
                # search_blocks returns dicts with "raw" field containing the full block text
                text = block.get("raw", "") if isinstance(block, dict) else str(block)
                
                if "[SIM]" in text or "simulation" in text.lower():
                    result["simulation"].append(text)
                elif "[VISUAL]" in text or "[IMAGE]" in text:
                    result["visual"].append(text)
                elif "[AUDIO]" in text or "[SOUND]" in text:
                    result["audio"].append(text)
                else:
                    result["episodic"].append(text)
            
            # Generate summary
            if blocks:
                result["memory_summary"] = self._summarize_blocks(blocks, user_query)
                result["highlights"] = self._extract_highlights(blocks)
            else:
                result["memory_summary"] = "In the past, ANM found no relevant memories."
            
        except Exception as e:
            result["memory_summary"] = f"Memory query error: {e}"
        
        return result
    
    def _summarize_blocks(self, blocks: List[Any], query: str) -> str:
        """Return raw memory blocks - no summarization."""
        # MemoryLLM should just show memory, not explain it
        # Return a simple statement that memory was found
        if blocks:
            return f"Found {len(blocks)} relevant memory block(s)."
        else:
            return "No relevant memory found."
    
    def _extract_highlights(self, blocks: List[Any]) -> List[str]:
        """Extract key highlights from blocks."""
        highlights = []
        
        for block in blocks[:5]:
            text = block.get("raw", str(block)) if isinstance(block, dict) else str(block)
            
            # Extract first meaningful sentence
            sentences = text.split(".")
            if sentences:
                highlight = sentences[0].strip()[:150]
                if highlight:
                    highlights.append(highlight)
        
        return highlights
    
    def run(self, wot_packet: str) -> str:
        """
        Process WoT packet for memory retrieval.
        Uses TinyLLama (quick_mode) for any LLM operations.
        """
        # Switch to TinyLLama (quick_mode) for MemoryLLM
        from anm.system.inference import get_inference_engine, InferenceConfig
        
        # Save current engine state
        current_engine = get_inference_engine()
        original_quick_mode = current_engine.config.quick_mode if current_engine.config else False
        
        # Use TinyLLama (quick_mode=True) for MemoryLLM
        memory_config = InferenceConfig(
            quick_mode=True,  # Use TinyLLama for MemoryLLM
            max_tokens=512,  # Shorter responses for memory operations
            temperature=0.3,  # Lower temperature for direct answers
        )
        memory_engine = get_inference_engine(memory_config)
        
        try:
            # Extract query from packet
            query = self._extract_query(wot_packet)
            
            # Query memory
            memory_result = self.query(query)
            
            # Build response
            response = self._format_memory_response(memory_result)
            
            # Ensure WOT_REQUEST
            if "WOT_REQUEST:" not in response:
                response += "\n\nWOT_REQUEST: NONE"
            
            # Ensure CONFIDENCE and EFFICIENCY markers
            if "CONFIDENCE:" not in response:
                confidence = "HIGH" if memory_result.get("blocks") else "LOW"
                response += f"\nCONFIDENCE: {confidence}"
            if "EFFICIENCY:" not in response:
                response += "\nEFFICIENCY: EFFICIENT"
            
            return response
        finally:
            # Restore original engine mode
            if original_quick_mode != True:
                restore_config = InferenceConfig(quick_mode=original_quick_mode)
                get_inference_engine(restore_config)
    
    def _extract_query(self, wot_packet: str) -> str:
        """Extract query from WoT packet."""
        for line in wot_packet.split("\n"):
            if "USER_QUERY:" in line:
                return line.split("USER_QUERY:", 1)[1].strip()
            if "MEMORY_QUERY:" in line:
                return line.split("MEMORY_QUERY:", 1)[1].strip()
        
        return wot_packet[:500]
    
    def _format_memory_response(self, result: Dict[str, Any]) -> str:
        """Format memory result for WoT - just show blocks, no explanations."""
        lines = [
            "[MEMORY_CONTEXT]",
            f"Query: {result['query']}",
            "",
        ]
        
        # Show raw memory blocks directly - no summaries or explanations
        if result["blocks"]:
            lines.append("MEMORY BLOCKS (PAST CONTEXT ONLY):")
            lines.append("")
            
            # Show blocks by category
            if result["episodic"]:
                lines.append("[EPISODIC]")
                for e in result["episodic"][:5]:
                    # Show full block, truncated if too long
                    block_text = e[:1000] if len(e) > 1000 else e
                    lines.append(block_text)
                    lines.append("")
            
            if result["visual"]:
                lines.append("[VISUAL]")
                for v in result["visual"][:3]:
                    block_text = v[:1000] if len(v) > 1000 else v
                    lines.append(block_text)
                    lines.append("")
            
            if result["simulation"]:
                lines.append("[SIMULATION]")
                for s in result["simulation"][:3]:
                    block_text = s[:1000] if len(s) > 1000 else s
                    lines.append(block_text)
                    lines.append("")
            
            if result["audio"]:
                lines.append("[AUDIO]")
                for a in result["audio"][:3]:
                    block_text = a[:1000] if len(a) > 1000 else a
                    lines.append(block_text)
                    lines.append("")
        else:
            lines.append("No relevant memory found.")
            lines.append("")
        
        lines.append("NOTE: All above is PAST context only, not current truth.")
        
        return "\n".join(lines)
    
    def _build_meta_block(self, text: str) -> str:
        """Build meta with memory-specific info."""
        base_meta = super()._build_meta_block(text)
        
        mem_meta = [
            "",
            "[MEMORY_STATUS]",
            f"diary_available: {self.diary is not None}",
            f"past_context_only: yes",
        ]
        
        return base_meta + "\n".join(mem_meta)
    
    def log_session(
        self,
        *,
        user_query: str,
        final_answer: str,
        verification: Optional[Dict[str, Any]] = None,
        router_plan: Optional[Dict[str, Any]] = None,
        active_domains: Optional[List[str]] = None,
        run_id: Optional[str] = None,
        lfm_report: Optional[Dict[str, Any]] = None,
        point_game_stats: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a full ANM session to diary memory.
        
        This is called by Router after processing a query.
        """
        # #region agent log
        try:
            import json
            import time
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "M1", "location": "memory_llm.py:log_session", "message": "log_session called", "data": {"has_diary": self.diary is not None, "diary_type": type(self.diary).__name__ if self.diary else "None", "user_query": user_query[:100]}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        if not self.diary:
            # #region agent log
            try:
                import json
                import time
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "M1", "location": "memory_llm.py:log_session", "message": "Diary is None, returning early", "data": {"DIARY_AVAILABLE": DIARY_AVAILABLE}, "timestamp": int(time.time() * 1000)}) + "\n")
            except: pass
            # #endregion
            return
        
        # Extract LFM learning entry if available
        lfm_learning_entry = None
        if lfm_report:
            lfm_learning_entry = lfm_report.get("learning_entry") or lfm_report.get("summary")
        
        # Build tags
        tags: List[str] = ["anm_session"]
        if active_domains:
            tags.extend(f"domain:{d}" for d in active_domains)
        
        # Build notes
        notes_lines: List[str] = []
        
        if verification:
            status = verification.get("status", "unknown")
            score = verification.get("score")
            notes_lines.append(f"Verifier status: {status}")
            if score is not None:
                notes_lines.append(f"Verifier score: {score}")
            v_notes = verification.get("notes")
            if v_notes:
                notes_lines.append(f"Verifier notes: {v_notes}")
        
        if router_plan:
            entry = router_plan.get("entry_specialist")
            max_steps = router_plan.get("max_steps")
            reason = router_plan.get("reason")
            
            if entry:
                notes_lines.append(f"Entry specialist: {entry}")
            if max_steps:
                notes_lines.append(f"Max steps: {max_steps}")
            if reason:
                notes_lines.append(f"Router reason: {reason}")
        
        if point_game_stats:
            notes_lines.append(f"PointGame stats: {point_game_stats}")
        
        notes = "\n".join(notes_lines) if notes_lines else None
        
        # Build extra metadata
        extra: Dict[str, Any] = {}
        if verification:
            extra["verification"] = verification
        if router_plan:
            extra["router_plan"] = router_plan
        if active_domains:
            extra["active_domains"] = active_domains
        if lfm_report:
            extra["lfm"] = lfm_report
        if point_game_stats:
            extra["point_game"] = point_game_stats
        
        # Log interaction to diary
        # #region agent log
        try:
            import json
            import time
            with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "M3", "location": "memory_llm.py:log_session", "message": "Before calling diary.log_interaction", "data": {"has_diary": self.diary is not None, "final_answer_length": len(final_answer)}, "timestamp": int(time.time() * 1000)}) + "\n")
        except: pass
        # #endregion
        try:
            self.diary.log_interaction(
                user_query=user_query,
                assistant_reply=final_answer,
                specialist="Router/Refiner",
                run_id=run_id,
                tags=tags,
                notes=notes,
                title="ANM Session Episode",
                extra=extra,
            )
            
            # Also log LFM learning entry separately if available
            if lfm_learning_entry:
                self.diary.log_learning(
                    learning_entry=lfm_learning_entry,
                    specialist="LFM",
                    run_id=run_id,
                    tags=["lfm", "learning"],
                )
        except Exception as e:
            # Don't fail if logging fails, but we should know about it
            # #region agent log
            try:
                import json
                import time
                with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "M3", "location": "memory_llm.py:log_session", "message": "diary.log_interaction raised exception", "data": {"error_type": type(e).__name__, "error_msg": str(e)[:200]}, "timestamp": int(time.time() * 1000)}) + "\n")
            except: pass
            # #endregion
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to log session to diary: {e}", exc_info=True)
