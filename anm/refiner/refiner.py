# ============================================================
#  ANM V0-OpenSource — REFINER (Final Answer Composer)
#  High-Quality Answer Generation • MetaCognition Aware
#  Smart Extraction • Quality Optimization • Clear Output
# ============================================================

"""
ANM Refiner - Final Answer Composition Engine

The Refiner takes all domain specialist outputs and composes
a high-quality final answer that:
- Extracts the key insights from each domain
- Resolves contradictions intelligently  
- Formats the answer appropriately for the query type
- Applies quality improvements
- Adds appropriate caveats and confidence levels
"""

from __future__ import annotations
import logging
import re
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from anm.utils.debug_logger import log_debug
from anm.utils.output_utils import clean_thinking_tags, normalize_text
from anm.refiner.constants import (
    MAX_ANSWER_LENGTH,
    MIN_ANSWER_LENGTH,
    MAX_KEY_POINTS,
    MAX_CONCLUSIONS,
    MAX_FORMULAS,
)

from anm.utils.prompts import REFINER_PROMPT
from anm.system.inference import get_inference_engine, InferenceConfig

__all__ = ["Refiner", "RefinerConfig", "RefinedAnswer", "AnswerQuality"]


# ============================================================
#  CONFIGURATION
# ============================================================

class AnswerStyle(Enum):
    """Output style for refined answers."""
    CONCISE = auto()      # Brief, to the point
    DETAILED = auto()     # Full explanation
    TECHNICAL = auto()    # Technical precision
    EDUCATIONAL = auto()  # Teaching style
    CONVERSATIONAL = auto()  # Friendly chat
    STEP_BY_STEP = auto()    # Numbered steps


class AnswerQuality(Enum):
    """Quality assessment of refined answer."""
    EXCELLENT = auto()
    GOOD = auto()
    ACCEPTABLE = auto()
    NEEDS_WORK = auto()
    POOR = auto()


@dataclass
class RefinerConfig:
    """Refiner configuration."""
    default_style: AnswerStyle = AnswerStyle.DETAILED
    max_answer_length: int = MAX_ANSWER_LENGTH
    min_answer_length: int = MIN_ANSWER_LENGTH
    max_tokens: int = 2048
    add_confidence: bool = True
    add_caveats: bool = True
    clean_thinking_tags: bool = True
    format_code_blocks: bool = True
    use_metacognition: bool = True


@dataclass
class RefinedAnswer:
    """The refined final answer with metadata."""
    answer: str
    quality: AnswerQuality
    confidence: float
    style: AnswerStyle
    sources_used: List[str]
    key_points: List[str]
    caveats: List[str]
    word_count: int
    has_code: bool
    has_math: bool
    has_steps: bool
    verification_ready: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


# run_model is imported from anm.system.inference
# Provides direct model loading via llama-cpp-python


# ============================================================
#  REFINER V0-OPENSOURCE
# ============================================================

class Refiner:
    """
    ANM V0-OpenSource Final Answer Refiner.
    
    Takes all domain specialist outputs and composes a high-quality,
    coherent final answer that:
    
    1. EXTRACTS key insights from each domain
    2. RESOLVES contradictions between domains
    3. FORMATS appropriately for the query type
    4. OPTIMIZES for clarity and accuracy
    5. ADDS confidence levels and caveats
    6. PREPARES for verification
    
    Quality Features:
    - Smart content extraction from domain outputs
    - Contradiction detection and resolution
    - Style adaptation based on query type
    - Code and math formatting
    - Confidence calibration
    - Caveat generation for uncertain claims
    """
    
    def __init__(
        self,
        config: Optional[RefinerConfig] = None,
    ) -> None:
        self.config = config or RefinerConfig()
        self._metacog = None
    
    # --------------------------------------------------------
    #  MAIN ENTRY - REFINE
    # --------------------------------------------------------
    
    def refine(self, packet: Dict[str, Any]) -> str:
        """
        Main refinement entry point.
        
        Args:
            packet: Dict containing domain outputs and metadata
            
        Returns:
            Refined answer string with [VERIFIER_READY] marker
        """
        # #region agent log
        import json
        try:
            domain_outputs = {k: v for k, v in packet.items() if k.endswith("_rounds")}
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "D", "location": "refiner.py:refine", "message": "Refiner called", "data": {"user_query": packet.get("user_query", "")[:100], "domain_outputs_keys": list(domain_outputs.keys()), "domain_outputs_lengths": {k: len(v) if v else 0 for k, v in domain_outputs.items()}, "has_empty_outputs": any(not v or not v.strip() or "[produced no output]" in v for v in domain_outputs.values() if v)}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
        
        # Check if this is a simple greeting/casual query - pass through without modification
        user_query = packet.get("user_query", "").lower().strip()
        if self._is_simple_greeting(user_query):
            # For simple greetings, just extract the main response from general specialist
            domain_outputs = self._extract_domain_outputs(packet)
            general_output = domain_outputs.get("general", "")
            if general_output:
                # Clean up the output and return it directly
                cleaned = self._clean_output(general_output)
                # Remove meta blocks for simple greetings
                cleaned = re.sub(r'\[DOMAIN_HEALTH\].*?\[ROUTER_HINTS\].*?WOT_REQUEST:.*', '', cleaned, flags=re.DOTALL)
                cleaned = cleaned.strip()
                if cleaned:
                    return self._ensure_verifier_ready(cleaned)
        
        # Extract and analyze all inputs
        domain_outputs = self._extract_domain_outputs(packet)
        task_meta = packet.get("task_meta", {}) or {}
        anm_stats = packet.get("anm_stats", {}) or {}
        
        # Determine optimal style
        style = self._determine_style(task_meta, domain_outputs)
        
        # Extract key content from each domain
        extracted = self._extract_key_content(domain_outputs)
        
        # Check for contradictions
        contradictions = self._detect_contradictions(extracted)
        
        # Build the refined answer
        refined = self._compose_answer(
            extracted=extracted,
            contradictions=contradictions,
            style=style,
            task_meta=task_meta,
            anm_stats=anm_stats,
            packet=packet,
        )
        
        # Quality improvements
        refined = self._improve_quality(refined, style)
        
        # CRITICAL: Block empty output BEFORE adding verifier marker
        # If refined is empty or just [VERIFIER_READY], use fallback
        if not refined or not refined.strip() or refined.strip() in ["", "None", "N/A"] or (len(refined.strip()) <= 20 and "[VERIFIER_READY]" in refined):
            logging.error("Refiner produced empty output - using emergency fallback")
            user_query = packet.get("user_query", "your query")
            # Try to extract any content from domain outputs
            domain_outputs = self._extract_domain_outputs(packet)
            fallback_content = []
            for domain, output in domain_outputs.items():
                if output and output.strip() and "[produced no output]" not in output.lower():
                    # Clean and extract first meaningful sentence
                    cleaned = self._clean_output(output)
                    if cleaned and len(cleaned.strip()) > 20:
                        # Get first sentence
                        sentences = re.split(r'[.!?]\s+', cleaned)
                        for sent in sentences:
                            if len(sent.strip()) > 20 and not self._is_instruction_text(sent):
                                fallback_content.append(f"**{domain.title()}**: {sent.strip()}")
                                break
                        if fallback_content:
                            break
            
            if fallback_content:
                refined = "\n\n".join(fallback_content[:3])
            else:
                # Last resort: provide helpful error message
                refined = f"I apologize, but I encountered an issue while processing your query: '{user_query}'. The system was unable to generate a proper response. Please try rephrasing your question or check if all required models are loaded correctly."
        
        # Add verification marker (only if we have actual content)
        if refined and refined.strip() and len(refined.strip()) > 20:
            refined = self._ensure_verifier_ready(refined)
        
        return refined
    
    def _is_simple_greeting(self, query: str) -> bool:
        """Check if query is a simple greeting."""
        if not query:
            return False
        
        greetings = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", 
                     "good evening", "howdy", "what's up", "sup"]
        
        query_lower = query.lower().strip()
        # Check if it's just a greeting (1-3 words)
        words = query_lower.split()
        if len(words) <= 3:
            return any(g in query_lower for g in greetings)
        
        return False
    
    def refine_full(self, packet: Dict[str, Any]) -> RefinedAnswer:
        """
        Full refinement with detailed result.
        
        Returns:
            RefinedAnswer with full metadata
        """
        answer = self.refine(packet)
        
        # Analyze the answer
        has_code = "```" in answer or "def " in answer or "function " in answer
        has_math = any(sym in answer for sym in ["=", "∫", "∑", "√", "π", "×"])
        has_steps = bool(re.search(r'\d+\.\s+', answer))
        
        # Extract key points
        key_points = self._extract_key_points(answer)
        
        # Determine caveats
        caveats = self._extract_caveats(answer)
        
        # Calculate confidence
        confidence = self._calculate_confidence(answer, packet)
        
        # Assess quality
        quality = self._assess_quality(answer, packet)
        
        # Sources used
        sources = [d for d, o in self._extract_domain_outputs(packet).items() if o and o.strip()]
        
        return RefinedAnswer(
            answer=answer,
            quality=quality,
            confidence=confidence,
            style=self._determine_style(packet.get("task_meta", {}), {}),
            sources_used=sources,
            key_points=key_points,
            caveats=caveats,
            word_count=len(answer.split()),
            has_code=has_code,
            has_math=has_math,
            has_steps=has_steps,
            verification_ready="[VERIFIER_READY]" in answer,
        )
    
    # --------------------------------------------------------
    #  CONTENT EXTRACTION
    # --------------------------------------------------------
    
    def _extract_domain_outputs(self, packet: Dict[str, Any]) -> Dict[str, str]:
        """Extract all domain outputs from packet."""
        domains = [
            "general", "math", "physics", "code", "chemistry", "biology",
            "memory", "research", "facts", "simulation", "sound", "image"
        ]
        
        outputs = {}
        for domain in domains:
            key = f"{domain}_rounds"
            raw = packet.get(key, "")
            outputs[domain] = self._clean_input(raw)
        
        return outputs
    
    def _extract_key_content(self, domain_outputs: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Extract key content from each domain's output."""
        extracted = {}
        
        # #region agent log
        import json
        import time
        try:
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "C", "location": "refiner.py:_extract_key_content", "message": "Extract key content start", "data": {"domains": list(domain_outputs.keys()), "output_lengths": {k: len(v) if v else 0 for k, v in domain_outputs.items()}}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
        
        for domain, output in domain_outputs.items():
            # #region agent log
            try:
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "C", "location": "refiner.py:_extract_key_content", "message": "Processing domain output", "data": {"domain": domain, "output_length": len(output) if output else 0, "output_preview": output[:150] if output else "EMPTY", "is_empty": not output or output.strip() in ["", "None", "N/A"], "has_no_output_marker": "[produced no output]" in output if output else False}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
            # Skip empty outputs and "produced no output" markers
            if not output or (isinstance(output, str) and output.strip() in ["", "None", "N/A"]):
                continue
            # Skip outputs that indicate no content was produced
            if isinstance(output, str) and ("[produced no output]" in output.lower() or (output.strip().startswith("[") and "produced no output" in output.lower())):
                continue
            
            extracted[domain] = {
                "raw": output,
                "main_points": self._extract_main_points(output),
                "conclusions": self._extract_conclusions(output),
                "formulas": self._extract_formulas(output),
                "code": self._extract_code_blocks(output),
                "confidence_markers": self._detect_confidence_markers(output),
                "uncertainty_markers": self._detect_uncertainty_markers(output),
            }
        
        return extracted
    
    def _extract_main_points(self, text: str) -> List[str]:
        """Extract main points from text."""
        points = []
        
        # Skip malformed output (repetitive instructions)
        if self._is_malformed_instruction(text):
            # Try to extract any actual content that's not instructions
            # Look for sentences that don't contain instruction keywords
            sentences = re.split(r'[.!?]\s+', text)
            for sent in sentences:
                sent = sent.strip()
                if len(sent) > 20 and not self._is_instruction_text(sent):
                    points.append(sent)
            return points[:MAX_KEY_POINTS]
        
        # Look for bullet points
        for match in re.finditer(r'[-•*]\s+(.+?)(?=\n|$)', text):
            points.append(match.group(1).strip())
        
        # Look for numbered points
        for match in re.finditer(r'\d+[.)]\s+(.+?)(?=\n|$)', text):
            points.append(match.group(1).strip())
        
        # Look for key phrases
        key_markers = ["therefore", "thus", "in conclusion", "the answer is", "result:"]
        for marker in key_markers:
            if marker in text.lower():
                idx = text.lower().find(marker)
                end = text.find("\n", idx)
                if end == -1:
                    end = min(idx + 200, len(text))
                points.append(text[idx:end].strip())

        return points[:MAX_KEY_POINTS]
    
    def _is_malformed_instruction(self, text: str) -> bool:
        """Check if text is malformed (repetitive instructions)."""
        text_lower = text.lower()
        # Check for repetitive instruction patterns
        instruction_keywords = ["provide", "provid", "end with", "wot_request", "concise", "summary"]
        instruction_count = sum(1 for kw in instruction_keywords if kw in text_lower)
        # If text has many instruction keywords but little actual content, it's likely malformed
        if instruction_count >= 3 and len(text) < 500:
            return True
        # Check for exact repetition
        if text.count("Provid") >= 2 or text.count("provide") >= 2:
            return True
        return False
    
    def _is_instruction_text(self, text: str) -> bool:
        """Check if text is an instruction rather than content."""
        text_lower = text.lower()
        instruction_phrases = [
            "provide", "provid", "end with", "wot_request", "concise", "summary",
            "your reasoning", "your answer", "write", "complete"
        ]
        return any(phrase in text_lower for phrase in instruction_phrases)
    
    def _extract_conclusions(self, text: str) -> List[str]:
        """Extract conclusions from text."""
        conclusions = []
        
        # Look for conclusion markers
        patterns = [
            r"(?:therefore|thus|hence|so|consequently)[,:]?\s*(.+?)(?:\.|$)",
            r"(?:in conclusion|to conclude|finally)[,:]?\s*(.+?)(?:\.|$)",
            r"(?:the answer is|the result is)[:]?\s*(.+?)(?:\.|$)",
            r"WOT_REQUEST:\s*NONE.*?(?:\n|$)(.+?)(?:\n|$)",
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                conc = match.group(1).strip()
                if len(conc) > 10:
                    conclusions.append(conc)

        return conclusions[:MAX_CONCLUSIONS]
    
    def _extract_formulas(self, text: str) -> List[str]:
        """Extract mathematical formulas."""
        formulas = []
        
        # LaTeX style
        for match in re.finditer(r'\$(.+?)\$', text):
            formulas.append(match.group(1))
        
        # Equation patterns
        for match in re.finditer(r'([A-Za-z_]+\s*=\s*[^,\n]{3,50})', text):
            formulas.append(match.group(1))

        return formulas[:MAX_FORMULAS]
    
    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extract code blocks."""
        blocks = []
        
        # Fenced code blocks
        for match in re.finditer(r'```[\w]*\n?(.*?)```', text, re.DOTALL):
            blocks.append(match.group(1).strip())
        
        # Indented code
        for match in re.finditer(r'\n((?:    .+\n)+)', text):
            blocks.append(match.group(1).strip())
        
        return blocks
    
    def _detect_confidence_markers(self, text: str) -> List[str]:
        """Detect confidence-indicating phrases."""
        markers = []
        high_conf = ["definitely", "certainly", "clearly", "proven", "established"]
        
        lower = text.lower()
        for marker in high_conf:
            if marker in lower:
                markers.append(marker)
        
        return markers
    
    def _detect_uncertainty_markers(self, text: str) -> List[str]:
        """Detect uncertainty-indicating phrases."""
        markers = []
        uncertain = [
            "maybe", "perhaps", "possibly", "might", "could be",
            "not sure", "uncertain", "unclear", "approximately",
            "estimated", "roughly", "about"
        ]
        
        lower = text.lower()
        for marker in uncertain:
            if marker in lower:
                markers.append(marker)
        
        return markers
    
    # --------------------------------------------------------
    #  CONTRADICTION DETECTION
    # --------------------------------------------------------
    
    def _detect_contradictions(
        self,
        extracted: Dict[str, Dict[str, Any]],
    ) -> List[Tuple[str, str, str]]:
        """
        Detect contradictions between domain outputs.
        
        Returns:
            List of (domain1, domain2, description) tuples
        """
        contradictions = []
        
        domains = list(extracted.keys())
        for i, d1 in enumerate(domains):
            for d2 in domains[i+1:]:
                # Check for opposing conclusions
                conc1 = " ".join(extracted[d1].get("conclusions", []))
                conc2 = " ".join(extracted[d2].get("conclusions", []))
                
                if self._are_contradictory(conc1, conc2):
                    contradictions.append((
                        d1, d2,
                        f"Potential disagreement between {d1} and {d2} conclusions"
                    ))
        
        return contradictions
    
    def _are_contradictory(self, text1: str, text2: str) -> bool:
        """Simple heuristic for contradiction detection."""
        if not text1 or not text2:
            return False
        
        # Check for negation patterns
        negatives = ["not", "no", "never", "impossible", "incorrect", "wrong", "false"]
        
        lower1, lower2 = text1.lower(), text2.lower()
        
        for neg in negatives:
            # One has negation, other doesn't, but share key words
            has_neg_1 = neg in lower1
            has_neg_2 = neg in lower2
            
            if has_neg_1 != has_neg_2:
                # Check for shared content words
                words1 = set(w for w in lower1.split() if len(w) > 4)
                words2 = set(w for w in lower2.split() if len(w) > 4)
                if len(words1 & words2) >= 2:
                    return True
        
        return False
    
    # --------------------------------------------------------
    #  STYLE DETERMINATION
    # --------------------------------------------------------
    
    def _determine_style(
        self,
        task_meta: Dict[str, Any],
        domain_outputs: Dict[str, str],
    ) -> AnswerStyle:
        """Determine the best answer style."""
        task_type = task_meta.get("task_type", "").lower()
        audience = task_meta.get("audience", "intermediate").lower()
        detail = task_meta.get("detail_level", "medium").lower()
        
        # Task type based
        if task_type in ["proof", "derivation", "calculation"]:
            return AnswerStyle.STEP_BY_STEP
        
        if task_type in ["tutorial", "explain", "teach"]:
            return AnswerStyle.EDUCATIONAL
        
        if task_type in ["quick", "brief", "tldr"]:
            return AnswerStyle.CONCISE
        
        if task_type in ["technical", "specification", "documentation"]:
            return AnswerStyle.TECHNICAL
        
        if task_type in ["chat", "casual", "discussion"]:
            return AnswerStyle.CONVERSATIONAL
        
        # Audience based
        if audience in ["beginner", "novice", "child"]:
            return AnswerStyle.EDUCATIONAL
        
        if audience in ["expert", "professional", "researcher"]:
            return AnswerStyle.TECHNICAL
        
        # Detail based
        if detail == "high":
            return AnswerStyle.DETAILED
        
        if detail == "low":
            return AnswerStyle.CONCISE
        
        return self.config.default_style
    
    # --------------------------------------------------------
    #  ANSWER COMPOSITION
    # --------------------------------------------------------
    
    def _compose_answer(
        self,
        extracted: Dict[str, Dict[str, Any]],
        contradictions: List[Tuple[str, str, str]],
        style: AnswerStyle,
        task_meta: Dict[str, Any],
        anm_stats: Dict[str, Any],
        packet: Dict[str, Any],
    ) -> str:
        """Compose the final answer from extracted content."""
        
        # Build comprehensive prompt for the LLM
        prompt = self._build_composition_prompt(
            extracted, contradictions, style, task_meta, anm_stats, packet
        )
        
        # Get LLM composition using R1 model (same as specialists) for Refiner
        # Save current engine state
        current_engine = get_inference_engine()
        original_quick_mode = current_engine.config.quick_mode if current_engine.config else False
        
        # Use R1 model (quick_mode=False) for Refiner to match specialist quality
        refiner_config = InferenceConfig(
            quick_mode=False,  # Use R1 model instead of TinyLlama for better quality
            max_tokens=2048,  # Allow longer responses for composition
            temperature=0.7,  # Standard temperature for R1 model
        )
        refiner_engine = get_inference_engine(refiner_config)
        
        try:
            raw_answer = refiner_engine.generate(prompt, max_tokens=2048)
            # #region agent log
            try:
                import json
                import time
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "R1", "location": "refiner.py:_compose_answer", "message": "Raw answer from LLM", "data": {"raw_answer_length": len(raw_answer) if raw_answer else 0, "raw_answer_preview": raw_answer[:200] if raw_answer else "EMPTY", "has_thinking_tags": "</think>" in raw_answer if raw_answer else False}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
        finally:
            # Restore original engine mode
            if original_quick_mode != False:
                restore_config = InferenceConfig(quick_mode=original_quick_mode)
                get_inference_engine(restore_config)
        
        # Clean the output
        answer = self._clean_output(raw_answer) if raw_answer else ""
        # #region agent log
        try:
            import json
            import time
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "R2", "location": "refiner.py:_compose_answer", "message": "After cleaning output", "data": {"cleaned_answer_length": len(answer) if answer else 0, "cleaned_answer_preview": answer[:200] if answer else "EMPTY", "is_too_short": len(answer) < 20 if answer else True}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
        
        # Ensure answer is not None
        if answer is None:
            answer = ""
        
        # Remove thinking tags (CRITICAL - must be done early)
        if self.config.clean_thinking_tags:
            answer = self._clean_thinking_tags(answer) if answer else ""
        
        # Ensure answer is still not None after cleaning
        if answer is None:
            answer = ""
        
        # CRITICAL: Check if answer is just [VERIFIER_READY] or empty after cleaning
        if not answer or answer.strip() in ["", "[VERIFIER_READY]", "None", "N/A"] or len(answer.strip()) < 20:
            # #region agent log
            try:
                import json
                import time
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "R1", "location": "refiner.py:_compose_answer", "message": "Answer too short or empty after cleaning, using fallback", "data": {"answer_length": len(answer) if answer else 0, "answer_preview": answer[:100] if answer else "EMPTY"}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
            answer = self._fallback_compose(extracted, style, packet)
        
        # If LLM failed, use fallback composition
        # Check for thinking tags only (common R1 model issue)
        is_thinking_tags_only = (
            answer and (
                answer.strip() in ["</think>", "<think>"] or
                (len(answer.strip()) < 50 and ("</think>" in answer or "<think>" in answer)) or
                answer.strip().startswith("</think>") or
                answer.strip().endswith("</think>")
            )
        )
        if not answer or "[Refiner ERROR" in answer or len(answer) < 20 or is_thinking_tags_only:
            # #region agent log
            try:
                import json
                import time
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "R1", "location": "refiner.py:_compose_answer", "message": "Triggering fallback", "data": {"reason": "thinking_tags_only" if is_thinking_tags_only else "too_short" if len(answer) < 20 else "error", "answer_length": len(answer)}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
            answer = self._fallback_compose(extracted, style, packet)
        
        # Ensure answer is not None before checking
        if answer is None:
            answer = ""
        
        # Check if answer is still a placeholder or too short
        if not answer or answer.strip() in ["[Your answer here]", "[your answer here]", ""] or len(answer.strip()) < 10:
            # Try to get answer from packet directly
            user_query = packet.get("user_query", "")
            if not extracted:
                answer = f"I apologize, but I was unable to generate a proper answer. The domain specialists did not produce usable output for your query: '{user_query}'. Please try rephrasing your question or check if all required models are loaded correctly."
            else:
                answer = self._fallback_compose(extracted, style, packet)
        
        # Final cleanup of thinking tags (in case fallback also has them)
        if self.config.clean_thinking_tags:
            answer = self._clean_thinking_tags(answer)
        
        return answer
    
    def _build_composition_prompt(
        self,
        extracted: Dict[str, Dict[str, Any]],
        contradictions: List[Tuple[str, str, str]],
        style: AnswerStyle,
        task_meta: Dict[str, Any],
        anm_stats: Dict[str, Any],
        packet: Dict[str, Any],
    ) -> str:
        """Build the composition prompt."""
        
        # Style instructions
        style_guide = self._get_style_guide(style)
        
        # Build domain summaries
        domain_blocks = []
        for domain, content in extracted.items():
            conclusions = content.get("conclusions", [])
            main_points = content.get("main_points", [])
            formulas = content.get("formulas", [])
            uncertainty = content.get("uncertainty_markers", [])
            
            block = f"""
=== {domain.upper()} ===
Main Points: {'; '.join(main_points[:3]) if main_points else 'None extracted'}
Conclusions: {'; '.join(conclusions[:2]) if conclusions else 'None'}
Formulas: {', '.join(formulas[:3]) if formulas else 'None'}
Uncertainty: {', '.join(uncertainty) if uncertainty else 'Low'}
Raw Output (truncated):
{content['raw'][:800]}...
"""
            domain_blocks.append(block)
        
        domains_text = "\n".join(domain_blocks)
        
        # Contradiction notes
        contradiction_text = ""
        if contradictions:
            contradiction_text = "\n[CONTRADICTIONS DETECTED]\n"
            for d1, d2, desc in contradictions:
                contradiction_text += f"- {desc}\n"
            contradiction_text += "Please resolve these by prioritizing: Research > Facts > Physics/Math > General\n"
        
        # Task context
        task_type = task_meta.get("task_type", "general")
        risk = task_meta.get("risk_level", "medium")
        user_query = packet.get("user_query", "")
        
        prompt = f"""
{REFINER_PROMPT}

USER QUESTION: {user_query}

{style_guide}

[DOMAIN SPECIALIST OUTPUTS]
{domains_text}

{contradiction_text}

CRITICAL REMINDER: 
- Write the ACTUAL ANSWER directly. Start writing the answer immediately.
- NO chain-of-thought (no "Let me...", "I'll...", "First...", "To answer this...").
- NO reasoning steps or meta-commentary about the answer.
- NO thinking tags like <think>, </think>, <think>, </think>.
- Just write the answer as if you are directly responding to the user.
- If the specialist outputs contain repetitive instructions or malformed text, extract the actual content and ignore the instructions.

Answer the user's question: "{user_query}"

ANSWER (write directly, no CoT, no thinking tags):
"""
        return prompt
    
    def _get_style_guide(self, style: AnswerStyle) -> str:
        """Get style-specific instructions."""
        guides = {
            AnswerStyle.CONCISE: """
[STYLE: CONCISE]
- Keep answer brief (2-4 sentences)
- Focus on the core answer only
- No unnecessary elaboration
- Direct and to the point
""",
            AnswerStyle.DETAILED: """
[STYLE: DETAILED]
- Provide comprehensive explanation
- Include relevant context
- Cover multiple aspects
- Support claims with reasoning
""",
            AnswerStyle.TECHNICAL: """
[STYLE: TECHNICAL]
- Use precise technical terminology
- Include formulas and specifications
- Be exact and rigorous
- Cite relevant principles
""",
            AnswerStyle.EDUCATIONAL: """
[STYLE: EDUCATIONAL]
- Explain concepts clearly
- Use analogies when helpful
- Build understanding step by step
- Define technical terms
""",
            AnswerStyle.CONVERSATIONAL: """
[STYLE: CONVERSATIONAL]
- Friendly, approachable tone
- Natural language
- Feel free to use "you" and "we"
- Keep it engaging
""",
            AnswerStyle.STEP_BY_STEP: """
[STYLE: STEP-BY-STEP]
- Number each step clearly
- Show work and reasoning
- One concept per step
- Build to final answer
""",
        }
        return guides.get(style, guides[AnswerStyle.DETAILED])
    
    def _fallback_compose(
        self,
        extracted: Dict[str, Dict[str, Any]],
        style: AnswerStyle,
        packet: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Fallback composition without LLM."""
        parts = []
        
        # Collect all conclusions
        for domain, content in extracted.items():
            conclusions = content.get("conclusions", [])
            if conclusions:
                parts.append(f"**{domain.title()}**: {conclusions[0]}")
        
        if not parts:
            # Use main points instead
            for domain, content in extracted.items():
                points = content.get("main_points", [])
                if points:
                    parts.append(f"**{domain.title()}**: {points[0]}")
        
        if not parts:
            # Last resort: use raw outputs (but skip "produced no output" markers)
            for domain, content in extracted.items():
                raw = content.get("raw", "")
                if raw and len(raw) > 20 and "[produced no output]" not in raw.lower():
                    # Clean malformed instructions from raw output
                    cleaned_raw = self._clean_malformed_instructions(raw)
                    if cleaned_raw and len(cleaned_raw.strip()) > 10:
                        # Take first meaningful paragraph
                        para = cleaned_raw.split("\n\n")[0][:300]
                        if para and len(para.strip()) > 10:
                            parts.append(f"**{domain.title()}**: {para}")
                    elif raw and len(raw.strip()) > 10:
                        # If cleaning removed everything, use original but truncated
                        para = raw.split("\n\n")[0][:200]
                        if para and len(para.strip()) > 10:
                            parts.append(f"**{domain.title()}**: {para}")
        
        # Build answer from parts (FIXED: this was unreachable code before)
        if parts:
            answer = "\n\n".join(parts)
        else:
            # No usable content - provide helpful error
            user_query = packet.get("user_query", "your query") if packet else "your query"
            answer = f"I apologize, but I was unable to generate a proper answer. The domain specialists did not produce usable output for your query: '{user_query}'. This may indicate that the models need to be loaded or the query needs to be rephrased."
        
        return answer
    
    def _clean_malformed_instructions(self, text: str) -> str:
        """Remove repetitive instruction text from malformed specialist output."""
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip lines that are clearly instructions
            if self._is_instruction_text(stripped):
                continue
            # Skip lines with WOT_REQUEST markers
            if "wot_request" in stripped.lower() or "end with" in stripped.lower():
                continue
            cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines)
        # Remove excessive repetition
        sentences = result.split('.')
        seen = set()
        unique_sentences = []
        for sent in sentences:
            sent_clean = sent.strip().lower()
            if sent_clean and sent_clean not in seen and len(sent_clean) > 10:
                seen.add(sent_clean)
                unique_sentences.append(sent.strip())
        
        return '. '.join(unique_sentences)
    
    # --------------------------------------------------------
    #  QUALITY IMPROVEMENTS
    # --------------------------------------------------------
    
    def _improve_quality(self, answer: str, style: AnswerStyle) -> str:
        """Apply quality improvements to the answer."""
        
        # Clean thinking tags
        if self.config.clean_thinking_tags:
            answer = self._clean_thinking_tags(answer)
        
        # Format code blocks
        if self.config.format_code_blocks:
            answer = self._format_code_blocks(answer)
        
        # Remove excessive whitespace
        while "\n\n\n" in answer:
            answer = answer.replace("\n\n\n", "\n\n")
        
        # Ensure proper ending
        answer = answer.strip()
        if not answer.endswith((".", "!", "?", "```", "]")):
            if not answer.endswith("\n"):
                answer += "."
        
        return answer
    
    def _clean_thinking_tags(self, text: str) -> str:
        """Remove R1 thinking artifacts and reasoning tags."""
        if not text:
            return ""
        
        bad_patterns = [
            r"</?redacted_reasoning>",
            r"<think>.*?</think>",
            r"</?think>",
            r"<think>.*?</think>",
            r"<\|begin_of_text\|>",
            r"<\|end_of_text\|>",
            r"Thinking\.\.\..*?\n",
            r"Done thinking:.*?\n",
            r"Analysis:.*?\n",
            r"\[internal\].*?\[/internal\]",
            r"=======.*?=======",  # Git conflict markers
            r">>>>>>>.*?REPLACE",  # Git conflict markers
            r"<<<<<<<.*?<<<<<<<",  # Git conflict markers
        ]
        
        for pattern in bad_patterns:
            text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove standalone thinking tags on their own lines
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip lines that are only thinking tags
            if stripped in ['</think>', '<think>', '</think>', '<think>', '']:
                continue
            # Skip lines that start with thinking tags
            if (stripped.startswith('</think>') or 
                stripped.startswith('<think>') or
                stripped.startswith('</think>') or
                stripped.startswith('<think>')):
                continue
            cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Clean up multiple blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        result = text.strip()
        # #region agent log
        try:
            import json
            import time
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "R2", "location": "refiner.py:_clean_thinking_tags", "message": "Cleaned thinking tags", "data": {"original_length": len(text) if text else 0, "cleaned_length": len(result), "result_preview": result[:100] if result else "EMPTY"}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
        return result
    
    def _format_code_blocks(self, text: str) -> str:
        """Ensure code blocks are properly formatted."""
        # Add language hints to bare code blocks
        text = re.sub(r'```\n(def |class |import )', r'```python\n\1', text)
        text = re.sub(r'```\n(function |const |let |var )', r'```javascript\n\1', text)
        text = re.sub(r'```\n(#include|int main)', r'```cpp\n\1', text)
        
        return text
    
    # --------------------------------------------------------
    #  ANALYSIS HELPERS
    # --------------------------------------------------------
    
    def _extract_key_points(self, answer: str) -> List[str]:
        """Extract key points from final answer."""
        points = []
        
        # Numbered points
        for match in re.finditer(r'\d+[.)]\s*(.+?)(?=\n\d+[.)]|\n\n|$)', answer):
            points.append(match.group(1).strip())
        
        # Bullet points
        for match in re.finditer(r'[-•*]\s*(.+?)(?=\n[-•*]|\n\n|$)', answer):
            points.append(match.group(1).strip())
        
        return points[:5]
    
    def _extract_caveats(self, answer: str) -> List[str]:
        """Extract caveats from answer."""
        caveats = []
        
        caveat_markers = [
            r"(?:note|caveat|warning|important)[:\s]+(.+?)(?:\.|$)",
            r"(?:assuming|if we assume)[:\s]+(.+?)(?:\.|$)",
            r"(?:approximately|roughly|about)[:\s]+(.+?)(?:\.|$)",
        ]
        
        for pattern in caveat_markers:
            for match in re.finditer(pattern, answer, re.IGNORECASE):
                caveats.append(match.group(1).strip())
        
        return caveats
    
    def _calculate_confidence(self, answer: str, packet: Dict[str, Any]) -> float:
        """Calculate confidence in the answer."""
        confidence = 0.7  # Base
        
        # Adjust based on uncertainty markers
        uncertainty_words = ["maybe", "possibly", "uncertain", "might", "could"]
        for word in uncertainty_words:
            if word in answer.lower():
                confidence -= 0.05
        
        # Adjust based on confidence markers
        confidence_words = ["definitely", "certainly", "proven", "established"]
        for word in confidence_words:
            if word in answer.lower():
                confidence += 0.05
        
        # Adjust based on answer quality
        if len(answer) > 200:
            confidence += 0.05
        
        if "```" in answer or "=" in answer:  # Has code/formulas
            confidence += 0.05
        
        return max(0.1, min(1.0, confidence))
    
    def _assess_quality(self, answer: str, packet: Dict[str, Any]) -> AnswerQuality:
        """Assess the quality of the answer."""
        score = 0.0
        
        # Length check
        word_count = len(answer.split())
        if word_count >= self.config.min_answer_length:
            score += 0.2
        if word_count >= 100:
            score += 0.1
        
        # Structure check
        if re.search(r'\d+[.)]\s', answer):  # Has numbered points
            score += 0.15
        if "```" in answer:  # Has code
            score += 0.1
        
        # Completeness
        if "[VERIFIER_READY]" in answer:
            score += 0.15
        
        # No errors
        if "[ERROR" not in answer:
            score += 0.15
        
        # Content quality (has conclusions)
        if any(m in answer.lower() for m in ["therefore", "thus", "conclusion"]):
            score += 0.15
        
        # Map to quality level
        if score >= 0.8:
            return AnswerQuality.EXCELLENT
        elif score >= 0.6:
            return AnswerQuality.GOOD
        elif score >= 0.4:
            return AnswerQuality.ACCEPTABLE
        elif score >= 0.2:
            return AnswerQuality.NEEDS_WORK
        return AnswerQuality.POOR
    
    # --------------------------------------------------------
    #  UTILITIES
    # --------------------------------------------------------
    
    def _clean_input(self, text: Any) -> str:
        """Clean input text."""
        if not isinstance(text, str):
            return str(text) if text else ""
        
        text = text.strip()
        
        # Remove thinking artifacts
        bad = [
            "Thinking...", "thinking...", "<think>", "</think>",
            "analysis:", "Analysis:", "Done thinking:",
            "<|begin_of_text|>", "<|end_of_text|>",
        ]
        for b in bad:
            text = text.replace(b, "")
        
        return text.strip()
    
    def _clean_output(self, text: str) -> str:
        """Clean LLM output using centralized utilities."""
        if not text:
            return ""

        # Use centralized cleaning utilities
        text = clean_thinking_tags(text)
        text = normalize_text(text)

        return text
    
    def _ensure_verifier_ready(self, answer: str) -> str:
        """Ensure answer has single [VERIFIER_READY] at end."""
        # CRITICAL: Never allow completely empty answer
        if not answer or not answer.strip() or answer.strip() in ["", "None", "N/A"]:
            # Return minimal placeholder that will be caught by refine() validation
            return "[VERIFIER_READY]"
        
        # Remove any existing markers
        answer = answer.replace("[VERIFIER_READY]", "")
        
        # Clean up incomplete endings like "ANSWER:." or "ANSWER:" or just "."
        answer = answer.strip()
        # Remove trailing incomplete patterns
        answer = re.sub(r'\s*ANSWER:\s*\.?\s*$', '', answer, flags=re.IGNORECASE)
        answer = re.sub(r'\s*\.\s*$', '', answer)  # Remove trailing period if it's the only thing
        answer = answer.strip()
        
        # CRITICAL: If after cleaning answer is empty, return placeholder
        if not answer or answer.strip() == "":
            return "[VERIFIER_READY]"

        # Add single marker at end
        answer = answer + "\n\n[VERIFIER_READY]"

        return answer
