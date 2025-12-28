# ============================================================
#  ANM V0-OpenSource — General Specialist
#  High-Level Reasoning & Task Routing
# ============================================================

"""
ANM General Specialist - High-level reasoning and routing.

Responsibilities:
- Task decomposition and classification
- Routing to appropriate specialists
- Integration planning
- High-level reasoning
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List

from anm.specialists.base import (
    BaseSpecialist,
    SpecialistConfig,
    SpecialistDomain,
)
from anm.utils.prompts import GENERAL_PROMPT

__all__ = ["GeneralLLM"]


class GeneralLLM(BaseSpecialist):
    """
    ANM V0-OpenSource General Specialist.
    
    High-level reasoning specialist that:
    - Decomposes complex queries
    - Routes to appropriate domain specialists
    - Plans multi-step solutions
    - Integrates cross-domain reasoning
    
    Does NOT:
    - Perform detailed calculations
    - Generate code
    - Make factual claims without verification
    """
    
    @property
    def domain(self) -> SpecialistDomain:
        return SpecialistDomain.GENERAL
    
    def run(self, wot_packet: str) -> str:
        """
        Override run to handle simple greetings directly.
        """
        # Extract query from packet (WoT uses "USER QUERY:" with space, query on next line)
        query = ""
        if "USER QUERY:" in wot_packet:
            lines = wot_packet.split("\n")
            # Find the line with "USER QUERY:"
            for i, line in enumerate(lines):
                if "USER QUERY:" in line:
                    # Query is typically on the next line(s) until we hit an empty line or section header
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()
                        # Stop at empty line or section headers
                        if not next_line or next_line.startswith("MEMORY") or next_line.startswith("CROSS") or next_line.startswith("COT"):
                            break
                        if next_line:
                            query = next_line
                            break
                    break
        
        # Handle simple greetings
        if self._is_simple_greeting(query):
            greeting_response = f"""Hello! I'm ANM (Artificial Neural Mesh), a multi-agent AI system. I'm here to help you with a wide range of tasks including:

- Mathematical calculations and proofs
- Physics analysis and simulations
- Code generation and debugging
- Scientific research and explanations
- And much more!

How can I assist you today?

[DOMAIN_HEALTH]
domain: general
confidence: high
uncertainty: low
version: 0.1.0-opensource

[GLOBAL_RULES]
passed: True
risk_level: low
violations: none

[ROUTER_HINTS]
task_type: greeting
suggested_specialist: general
complexity: low

WOT_REQUEST: NONE"""
            return greeting_response
        
        # Detect simple arithmetic queries and route to math
        import re
        if query:
            arithmetic_pattern = re.search(r'\d+\s*[+\-*/]\s*\d+', query.lower())
            if arithmetic_pattern:
                return f"""This is a simple arithmetic question that should be handled by the MATH specialist.

[DOMAIN_HEALTH]
domain: general
confidence: high
uncertainty: low
version: 0.1.0-opensource

[GLOBAL_RULES]
passed: True
risk_level: low
violations: none

[ROUTER_HINTS]
task_type: calculation
suggested_specialist: math
complexity: low

WOT_REQUEST: MATH"""
        
        # For other queries, use the base implementation
        result = super().run(wot_packet)
        
        # If we got "produced no output", try to provide basic routing
        if "[GENERAL produced no output]" in result:
            # Provide minimal routing guidance
            if query:
                query_lower = query.lower()
                if any(k in query_lower for k in ["capital", "population", "founded", "located"]):
                    return result.replace("WOT_REQUEST: NONE", "WOT_REQUEST: FACTS")
                elif any(k in query_lower for k in ["python", "code", "function", "algorithm"]):
                    return result.replace("WOT_REQUEST: NONE", "WOT_REQUEST: CODE")
        
        return result
    
    def _get_system_prompt(self) -> str:
        # Use the optimized base prompt from prompts.py
        return GENERAL_PROMPT if GENERAL_PROMPT else ""
    
    def _build_meta_block(self, text: str) -> str:
        """Build meta with router hints."""
        base_meta = super()._build_meta_block(text)
        
        # Add router hints
        task_type = self._infer_task_type(text)
        suggested_domain = self._infer_suggested_domain(text)
        
        hints = [
            "",
            "[ROUTER_HINTS]",
            f"task_type: {task_type}",
            f"suggested_specialist: {suggested_domain}",
            f"complexity: {self._assess_complexity(text)}",
        ]
        
        return base_meta + "\n".join(hints)
    
    def _infer_task_type(self, text: str) -> str:
        """Infer task type from text."""
        lower = text.lower()
        
        type_keywords = {
            "derivation": ["derive", "proof", "prove", "theorem"],
            "calculation": ["calculate", "compute", "solve", "find the value"],
            "explanation": ["explain", "what is", "how does", "describe"],
            "comparison": ["compare", "versus", "difference between", "vs"],
            "design": ["design", "create", "build", "implement"],
            "analysis": ["analyze", "examine", "investigate"],
            "simulation": ["simulate", "model", "scenario"],
            "research": ["research", "find out", "look up", "search"],
            "creative": ["story", "imagine", "create a world"],
        }
        
        for task_type, keywords in type_keywords.items():
            if any(kw in lower for kw in keywords):
                return task_type
        
        return "general"
    
    def _infer_suggested_domain(self, text: str) -> str:
        """Suggest which domain should handle this."""
        lower = text.lower()
        
        domain_keywords = {
            "math": ["integral", "derivative", "equation", "matrix", "calculate"],
            "physics": ["force", "energy", "quantum", "relativity", "motion"],
            "code": ["python", "function", "algorithm", "program", "code"],
            "chemistry": ["reaction", "molecule", "compound", "chemical"],
            "biology": ["cell", "protein", "gene", "organism", "evolution"],
            "internet": ["current", "latest", "news", "search", "find online"],
            "facts": ["true", "verify", "accurate", "citation"],
            "simulation": ["simulate", "model", "scenario", "visualize"],
        }
        
        for domain, keywords in domain_keywords.items():
            if any(kw in lower for kw in keywords):
                return domain
        
        return "general"
    
    def _assess_complexity(self, text: str) -> str:
        """Assess task complexity."""
        lower = text.lower()
        
        # Simple greetings are low complexity
        greetings = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]
        if any(g in lower for g in greetings) and len(lower.split()) <= 3:
            return "low"
        
        # Count complexity indicators
        complexity_markers = [
            "and", "then", "also", "furthermore",
            "step", "first", "second", "finally",
            "multiple", "various", "several",
        ]
        
        count = sum(1 for m in complexity_markers if m in lower)
        
        if count >= 5:
            return "high"
        elif count >= 2:
            return "medium"
        return "low"
    
    def _is_simple_greeting(self, query: str) -> bool:
        """Check if query is a simple greeting."""
        lower = query.lower().strip()
        greetings = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "howdy"]
        
        # Check if it's just a greeting (1-3 words)
        words = lower.split()
        if len(words) <= 3:
            return any(g in lower for g in greetings)
        return False
