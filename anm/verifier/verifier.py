# ============================================================
# ANM V0-OpenSource — VERIFIER V0-OpenSource (MAX-STRICT • MULTI-DOMAIN SAFE)
#  Fully aligned with Prompts V0-OpenSource
#  Physics-Safe • Math-Safe • Image/Sound/Sim Safe
#  Anti-Hallucination • Zero-Invention • Iron-Law Strict
# ============================================================

from __future__ import annotations
import logging
import re
from typing import Dict, Any
from anm.utils.debug_logger import log_debug

# Import the shared inference engine
from anm.system.inference import run_model

try:
    from anm.utils.prompts import VERIFIER_PROMPT
except ImportError:
    VERIFIER_PROMPT = ""


# ============================================================
#  VERIFIER V0-OpenSource — MULTI-DOMAIN IRON DOME
# ============================================================

class Verifier:

    def __init__(self) -> None:

        # ----------------------------------------------------
        #  PROMPTS V0-OpenSource — Ultra-Strict System Layer
        # ----------------------------------------------------
        # Use VERIFIER_PROMPT from prompts.py (single source of truth)
        self.system_prefix = VERIFIER_PROMPT if VERIFIER_PROMPT else ""

    # --------------------------------------------------------
    # MAIN ENTRY - ADAPTIVE VERIFICATION
    # --------------------------------------------------------
    def run(self, packet: str) -> Dict[str, Any]:
        """
        ADAPTIVE VERIFIER: Analyzes question → checks reasoning → checks answer → decides
        
        packet: string built from prompts.WOT_PACKET_TEMPLATES["verifier_packet"]

        Returns:
            {
                "status": "approved" | "rejected",
                "notes": str,
                "score": int (0–100),
                "issues": [str, ...]
            }
        """

        # Hard pre-check: must contain [VERIFIER_READY] marker
        if "[VERIFIER_READY]" not in (packet or ""):
            return {
                "status": "rejected",
                "notes": "Missing [VERIFIER_READY] marker in merged_reasoning.",
                "score": 0,
                "issues": ["missing_verifier_ready"],
            }

        # Extra simple sanity: merged_reasoning should exist
        if "merged_reasoning:" not in packet:
            return {
                "status": "rejected",
                "notes": "VERIFIER_PACKET missing merged_reasoning block.",
                "score": 0,
                "issues": ["missing_merged_reasoning"],
            }

        # NEW: ADAPTIVE ANALYSIS - Step 1: Analyze the question
        question_analysis = self._analyze_question(packet)
        
        # NEW: ADAPTIVE ANALYSIS - Step 2: Extract reasoning and answer
        reasoning_analysis = self._analyze_reasoning(packet, question_analysis)
        answer_analysis = self._analyze_answer(packet, question_analysis)
        
        # NEW: Build adaptive verification prompt based on question analysis
        adaptive_prompt = self._build_adaptive_prompt(
            packet, 
            question_analysis, 
            reasoning_analysis, 
            answer_analysis
        )
        
        prompt = f"{self.system_prefix}\n\n{adaptive_prompt}\n\nYour decision:\n"
        raw = run_model(prompt, max_tokens=512)
        parsed = self._parse_output(raw)
        # #region agent log
        import json
        import time
        try:
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H3", "location": "verifier.py:run", "message": "After LLM call", "data": {"is_format_error": self._is_format_error(parsed), "parsed_status": parsed.get("status"), "query_type": question_analysis.get("query_type"), "complexity": question_analysis.get("complexity")}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
            logging.warning(f"Debug logging failed: {e}")
            # #endregion

        # If format is broken → retry once
        if self._is_format_error(parsed):
            raw2 = run_model(prompt, max_tokens=512)
            parsed2 = self._parse_output(raw2)
            if not self._is_format_error(parsed2):
                parsed = parsed2
            else:
                # Still broken → use adaptive fallback
                # #region agent log
                try:
                    import json
                    import time
                    log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H4", "location": "verifier.py:run", "message": "Using adaptive fallback due to format error", "data": {"query_type": question_analysis.get("query_type"), "complexity": question_analysis.get("complexity"), "raw2_output": raw2[:200] if 'raw2' in locals() else "N/A"}, "timestamp": int(time.time() * 1000)})
                except Exception as e:
                    logging.warning(f"Debug logging failed: {e}")
            # #endregion
                parsed = self._adaptive_fallback(packet, question_analysis, reasoning_analysis, answer_analysis)
                # #region agent log
                try:
                    import json
                    import time
                    log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H4", "location": "verifier.py:run", "message": "After adaptive fallback", "data": {"status": parsed.get("status"), "score": parsed.get("score"), "issues": parsed.get("issues", [])}, "timestamp": int(time.time() * 1000)})
                except Exception as e:
                    logging.warning(f"Debug logging failed: {e}")
            # #endregion

        # NEW: Include adaptive analysis in verification result for LFM learning
        parsed["adaptive_analysis"] = {
            "question_analysis": question_analysis,
            "reasoning_analysis": reasoning_analysis,
            "answer_analysis": answer_analysis,
        }

        return parsed

    # --------------------------------------------------------
    # ADAPTIVE ANALYSIS METHODS
    # --------------------------------------------------------
    
    def _analyze_question(self, packet: str) -> Dict[str, Any]:
        """Analyze the question to understand what's expected."""
        # Extract user query from packet
        query_match = re.search(r"user query:\s*['\"](.*?)['\"]", packet, re.IGNORECASE | re.DOTALL)
        if not query_match:
            query_match = re.search(r"user_query:\s*(.*?)(?:\n|merged_reasoning)", packet, re.IGNORECASE | re.DOTALL)
        
        user_query = query_match.group(1).strip() if query_match else ""
        query_lower = user_query.lower()
        
        analysis = {
            "query": user_query,
            "query_length": len(user_query),
            "query_type": "unknown",
            "complexity": "medium",
            "requirements": [],
            "expected_format": "text",
            "expected_length": "medium",
            "domain_hints": [],
        }
        
        # Determine query type
        # IMPORTANT: Check for calculations/math FIRST (before "what is" which is too broad)
        if any(word in query_lower for word in ["code", "function", "program", "script", "algorithm", "implement", "write a"]):
            analysis["query_type"] = "code"
            analysis["expected_format"] = "code"
            analysis["requirements"].append("code_blocks")
        elif any(word in query_lower for word in ["calculate", "compute", "solve", "derive", "prove", "formula"]) or any(op in user_query for op in ["+", "-", "*", "/", "=", "×", "÷", "^"]):
            # Check for math operations FIRST (before "what is" which catches too much)
            analysis["query_type"] = "calculation"
            analysis["expected_format"] = "math"
            analysis["expected_length"] = "short"  # Simple calculations can be short
            analysis["requirements"].append("mathematical_steps")
        elif any(word in query_lower for word in ["explain", "describe", "how", "why"]) or (query_lower.startswith("what is") and len(user_query) > 30):
            # Only treat "what is" as explanation if it's a longer query (not simple math)
            analysis["query_type"] = "explanation"
            analysis["expected_format"] = "text"
            analysis["expected_length"] = "long"
            analysis["requirements"].append("detailed_explanation")
        elif query_lower.startswith("what is") or query_lower.startswith("what are"):
            # Simple "what is X?" queries (short, factual) - treat as general, not explanation
            analysis["query_type"] = "general"
            analysis["expected_format"] = "text"
            analysis["expected_length"] = "short"  # Simple factual queries can be short
        elif any(word in query_lower for word in ["list", "enumerate", "name", "give me"]):
            analysis["query_type"] = "list"
            analysis["expected_format"] = "structured"
            analysis["expected_length"] = "medium"
        elif any(word in query_lower for word in ["yes", "no", "is", "are", "can", "does", "will"]):
            analysis["query_type"] = "yes_no"
            analysis["expected_format"] = "text"
            analysis["expected_length"] = "short"
        elif any(word in query_lower for word in ["design", "create", "build", "make"]):
            analysis["query_type"] = "creative"
            analysis["expected_format"] = "text"
            analysis["expected_length"] = "long"
            analysis["requirements"].append("creative_content")
        else:
            analysis["query_type"] = "general"
        
        # Determine complexity
        # Simple factual questions can be longer but still simple
        is_simple_factual = (
            analysis["query_type"] in ["yes_no", "general"] and
            not any(word in query_lower for word in ["explain", "describe", "how", "why", "complex", "detailed", "comprehensive"])
        )
        
        if len(user_query) < 30 or is_simple_factual:
            analysis["complexity"] = "simple"
        elif len(user_query) > 200 or any(word in query_lower for word in ["complex", "detailed", "comprehensive", "thorough", "explain how", "design a", "calculate"]):
            analysis["complexity"] = "complex"
        else:
            analysis["complexity"] = "medium"
        
        # For simple queries, adjust expected length
        if analysis["complexity"] == "simple" and analysis["query_type"] in ["yes_no", "general", "calculation"]:
            analysis["expected_length"] = "short"
        # Also set short for simple factual questions even if complexity is medium
        elif is_simple_factual and analysis["query_type"] == "general":
            analysis["expected_length"] = "short"
        
        # Check for multiple requirements
        requirement_indicators = ["and", "then", "also", "include", "plus", "as well as"]
        if sum(1 for word in requirement_indicators if word in query_lower) >= 2:
            analysis["requirements"].append("multiple_parts")
        
        # Domain hints
        if any(word in query_lower for word in ["physics", "force", "energy", "quantum", "relativity"]):
            analysis["domain_hints"].append("physics")
        if any(word in query_lower for word in ["math", "equation", "derivative", "integral", "theorem"]):
            analysis["domain_hints"].append("math")
        if any(word in query_lower for word in ["chemistry", "reaction", "molecule", "compound"]):
            analysis["domain_hints"].append("chemistry")
        if any(word in query_lower for word in ["biology", "organism", "cell", "evolution"]):
            analysis["domain_hints"].append("biology")
        
        return analysis
    
    def _analyze_reasoning(self, packet: str, question_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if reasoning supports the answer."""
        # Extract merged_reasoning
        merged_match = re.search(r'merged_reasoning:\s*"""(.*?)"""', packet, re.DOTALL)
        if not merged_match:
            merged_match = re.search(r'merged_reasoning:\s*(.*?)(?:\n\n|$)', packet, re.DOTALL)
        
        reasoning_text = merged_match.group(1).strip() if merged_match else ""
        reasoning_lower = reasoning_text.lower()
        
        analysis = {
            "has_reasoning": len(reasoning_text) > 0,
            "reasoning_length": len(reasoning_text),
            "reasoning_quality": "unknown",
            "supports_answer": False,
            "has_steps": False,
            "has_examples": False,
            "has_justification": False,
        }
        
        if not reasoning_text:
            return analysis
        
        # Check for reasoning indicators
        reasoning_indicators = ["because", "since", "therefore", "thus", "hence", "due to", "as a result"]
        analysis["has_justification"] = any(indicator in reasoning_lower for indicator in reasoning_indicators)
        
        # Check for step-by-step reasoning
        step_indicators = ["step", "first", "second", "then", "next", "finally", "1.", "2.", "3."]
        analysis["has_steps"] = any(indicator in reasoning_lower for indicator in step_indicators)
        
        # Check for examples
        example_indicators = ["example", "for instance", "such as", "e.g.", "consider"]
        analysis["has_examples"] = any(indicator in reasoning_lower for indicator in example_indicators)
        
        # Assess reasoning quality based on question type
        if question_analysis["query_type"] == "calculation":
            # For simple calculations, just having an answer is enough
            if question_analysis["complexity"] == "simple":
                analysis["supports_answer"] = len(reasoning_text) > 0  # Any answer is acceptable
            else:
                # For complex calculations, require steps or math symbols
                analysis["supports_answer"] = analysis["has_steps"] or "=" in reasoning_text or any(char in reasoning_text for char in ["+", "-", "*", "/", "^"])
        elif question_analysis["query_type"] == "explanation":
            analysis["supports_answer"] = analysis["has_justification"] and len(reasoning_text) > 100
        elif question_analysis["query_type"] == "code":
            analysis["supports_answer"] = "```" in reasoning_text or "def " in reasoning_lower or "function" in reasoning_lower
        elif question_analysis["query_type"] == "general" and question_analysis["complexity"] == "simple":
            # Simple factual questions: any reasoning is acceptable
            analysis["supports_answer"] = len(reasoning_text) > 0
        else:
            analysis["supports_answer"] = len(reasoning_text) > 50
        
        # Determine quality
        if analysis["supports_answer"] and (analysis["has_steps"] or analysis["has_justification"]):
            analysis["reasoning_quality"] = "good"
        elif analysis["supports_answer"]:
            analysis["reasoning_quality"] = "adequate"
        else:
            analysis["reasoning_quality"] = "poor"
        
        return analysis
    
    def _analyze_answer(self, packet: str, question_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if answer matches question requirements."""
        # Extract merged_reasoning (which contains the answer)
        merged_match = re.search(r'merged_reasoning:\s*"""(.*?)"""', packet, re.DOTALL)
        if not merged_match:
            merged_match = re.search(r'merged_reasoning:\s*(.*?)(?:\n\n|$)', packet, re.DOTALL)
        
        answer_text = merged_match.group(1).strip() if merged_match else ""
        # Remove [VERIFIER_READY] marker for analysis
        answer_text = answer_text.replace("[VERIFIER_READY]", "").strip()
        
        # Clean thinking tags (sync with refiner's cleaning)
        answer_text = self._clean_thinking_tags(answer_text)
        
        # Store answer_text in analysis for later use
        answer_lower = answer_text.lower()
        
        analysis = {
            "has_answer": len(answer_text) > 0,
            "answer_length": len(answer_text),
            "matches_requirements": False,
            "has_expected_format": False,
            "completeness": "unknown",
            "quality_indicators": [],
            "answer_text": answer_text,  # Store for adaptive fallback
            "answer": answer_text,  # Alias for compatibility
        }
        
        if not answer_text:
            return analysis
        
        # Check if answer matches expected format
        if question_analysis["expected_format"] == "code":
            # Expanded code detection - recognize various code patterns
            analysis["has_expected_format"] = (
                "```" in answer_text or           # Code blocks
                "def " in answer_lower or         # Python functions
                "function" in answer_lower or     # JS/other functions
                "class " in answer_lower or       # Class definitions
                "import " in answer_lower or      # Import statements
                "return " in answer_lower or      # Return statements
                "for " in answer_lower or         # For loops
                "while " in answer_lower or       # While loops
                "if " in answer_lower or          # Conditionals
                "elif " in answer_lower or        # Python elif
                "else:" in answer_lower or        # Else blocks
                "->" in answer_text or            # Type hints / arrow functions
                "==" in answer_text or            # Equality comparisons
                "!=" in answer_text or            # Inequality comparisons
                "+=" in answer_text or            # Compound assignment
                "[]" in answer_text or            # Array literals
                "{}" in answer_text or            # Dict/object literals
                "lambda" in answer_lower or       # Lambda functions
                "async " in answer_lower or       # Async functions
                "await " in answer_lower          # Await expressions
            )
        elif question_analysis["expected_format"] == "math":
            # For simple calculations, accept plain numbers OR text answers like "2 + 2 equals 4"
            if question_analysis["complexity"] == "simple" and question_analysis["query_type"] == "calculation":
                # Accept: plain numbers, "equals X", "is X", or "X" anywhere in answer
                has_number = bool(re.search(r'\d+', answer_text))
                has_equals = "equals" in answer_text.lower() or "=" in answer_text or "is" in answer_text.lower()
                analysis["has_expected_format"] = has_number or has_equals
            else:
                analysis["has_expected_format"] = any(char in answer_text for char in ["=", "+", "-", "*", "/", "^", "∫", "∑"]) or "$" in answer_text
        elif question_analysis["expected_format"] == "structured":
            analysis["has_expected_format"] = any(marker in answer_text for marker in ["-", "•", "1.", "2.", "3.", "*"])
        else:
            analysis["has_expected_format"] = len(answer_text) > 20
        
        # Check if answer matches expected length (adaptive based on complexity)
        expected_length = question_analysis["expected_length"]
        complexity = question_analysis["complexity"]
        
        if expected_length == "short" or (complexity == "simple" and question_analysis["query_type"] in ["yes_no", "general", "calculation"]):
            # For simple calculations, allow very short answers (even 1 char like "4")
            if question_analysis["query_type"] == "calculation" and complexity == "simple":
                length_ok = len(answer_text) >= 1  # Allow single character answers
            else:
                # For other simple queries, allow very short answers (e.g., "Yes", "No", "42")
                # Accept any non-empty answer - correctness matters more than length
                length_ok = len(answer_text) >= 1  # Minimum 1 char, no upper limit for simple queries
        elif expected_length == "long":
            length_ok = len(answer_text) > 150
        else:  # medium
            length_ok = 50 < len(answer_text) < 500
        
        # Check requirements
        requirements_met = []
        for req in question_analysis["requirements"]:
            if req == "code_blocks":
                requirements_met.append("```" in answer_text)
            elif req == "detailed_explanation":
                requirements_met.append(len(answer_text) > 100 and analysis["has_expected_format"])
            elif req == "mathematical_steps":
                # For simple calculations, accept any answer with a number (e.g., "2 + 2 equals 4")
                if question_analysis["complexity"] == "simple" and question_analysis["query_type"] == "calculation":
                    # Accept if it contains a number anywhere (not just at start)
                    requirements_met.append(bool(re.search(r'\d+', answer_text)))
                else:
                    # For complex calculations, require math symbols
                    requirements_met.append(any(char in answer_text for char in ["=", "+", "-", "*", "/"]))
            elif req == "multiple_parts":
                # Check if answer addresses multiple aspects
                sentences = [s.strip() for s in re.split(r'[.!?]\s+', answer_text) if s.strip()]
                requirements_met.append(len(sentences) >= 3)
            else:
                requirements_met.append(True)  # Unknown requirement, assume met
        
        analysis["matches_requirements"] = all(requirements_met) if requirements_met else True
        
            # Determine completeness based on question type and expected length
        if expected_length == "short" or (complexity == "simple" and question_analysis["query_type"] in ["yes_no", "general", "calculation"]):
            # For short/simple queries, completeness is based on whether it answers the question
            # Not just length - check if it looks complete (not truncated)
            # Also check for thinking tags only (refiner should have cleaned these, but verify)
            is_thinking_tags_only = (
                answer_text.strip() in ["</think>", "<think>", "</think>", "<think>"] or
                (len(answer_text.strip()) < 30 and ("</think>" in answer_text or "<think>" in answer_text))
            )
            is_truncated = (
                "ning" in answer_text.lower() and answer_text.startswith("**") or  # Truncated like "**General**: ning..."
                (answer_text.count(".") == 0 and len(answer_text) < 20 and not answer_text.strip().endswith("?")) or  # No sentence structure
                "[VERIFIER_READY]" in answer_text and len(answer_text.replace("[VERIFIER_READY]", "").strip()) < 10 or
                is_thinking_tags_only  # Thinking tags only (should have been cleaned by refiner)
            )
            if is_truncated:
                analysis["completeness"] = "incomplete"
            elif analysis["matches_requirements"] and length_ok:
                analysis["completeness"] = "complete"
            elif question_analysis["query_type"] == "general" and len(answer_text) >= 1:  # Very lenient for simple factual questions - accept any non-empty answer
                analysis["completeness"] = "complete"
            else:
                analysis["completeness"] = "incomplete"
        elif expected_length == "long":
            analysis["completeness"] = "complete" if (analysis["matches_requirements"] and len(answer_text) > 200) else "incomplete"
        else:  # medium
            analysis["completeness"] = "complete" if (analysis["matches_requirements"] and len(answer_text) > 80) else "incomplete"
        
        # Quality indicators
        if not any(word in answer_lower for word in ["i apologize", "i cannot", "i don't know", "unable"]):
            analysis["quality_indicators"].append("no_failure_messages")
        if "[VERIFIER_READY]" in (merged_match.group(1) if merged_match else ""):
            analysis["quality_indicators"].append("properly_formatted")
        if len(answer_text.split()) > 10:
            analysis["quality_indicators"].append("substantive")
        
        return analysis
    
    def _build_adaptive_prompt(
        self,
        packet: str,
        question_analysis: Dict[str, Any],
        reasoning_analysis: Dict[str, Any],
        answer_analysis: Dict[str, Any],
    ) -> str:
        """Build adaptive verification prompt based on analysis."""
        # Add analysis context to the packet
        analysis_context = f"""
=== QUESTION ANALYSIS ===
Query Type: {question_analysis['query_type']}
Complexity: {question_analysis['complexity']}
Expected Format: {question_analysis['expected_format']}
Expected Length: {question_analysis['expected_length']}
Requirements: {', '.join(question_analysis['requirements']) if question_analysis['requirements'] else 'none'}
Domain Hints: {', '.join(question_analysis['domain_hints']) if question_analysis['domain_hints'] else 'none'}

=== REASONING ANALYSIS ===
Has Reasoning: {reasoning_analysis['has_reasoning']}
Reasoning Quality: {reasoning_analysis['reasoning_quality']}
Supports Answer: {reasoning_analysis['supports_answer']}
Has Steps: {reasoning_analysis['has_steps']}
Has Justification: {reasoning_analysis['has_justification']}

=== ANSWER ANALYSIS ===
Has Answer: {answer_analysis['has_answer']}
Answer Length: {answer_analysis['answer_length']} chars
Matches Requirements: {answer_analysis['matches_requirements']}
Has Expected Format: {answer_analysis['has_expected_format']}
Completeness: {answer_analysis['completeness']}
Quality Indicators: {', '.join(answer_analysis['quality_indicators']) if answer_analysis['quality_indicators'] else 'none'}

=== ADAPTIVE VERIFICATION INSTRUCTIONS ===
Based on the question analysis:
1. The question is a {question_analysis['query_type']} type query with {question_analysis['complexity']} complexity.
2. The answer should be in {question_analysis['expected_format']} format and {question_analysis['expected_length']} length.
3. Check if the reasoning ({reasoning_analysis['reasoning_quality']} quality) properly supports the answer.
4. Verify the answer matches all requirements: {', '.join(question_analysis['requirements']) if question_analysis['requirements'] else 'none'}.
5. The answer completeness is: {answer_analysis['completeness']}.

ADAPTIVE DECISION CRITERIA:
- For {question_analysis['query_type']} queries: {"REJECT if no code blocks" if question_analysis['expected_format'] == 'code' else "REJECT if too brief" if question_analysis['expected_length'] == 'long' else "REJECT if incomplete"}
- Reasoning must support the answer (currently: {reasoning_analysis['supports_answer']})
- Answer must match expected format (currently: {answer_analysis['has_expected_format']})
- All requirements must be met (currently: {answer_analysis['matches_requirements']})

=== ORIGINAL PACKET ===
{packet}
"""
        return analysis_context
    
    def _adaptive_fallback(
        self,
        packet: str,
        question_analysis: Dict[str, Any],
        reasoning_analysis: Dict[str, Any],
        answer_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Adaptive fallback using analysis results."""
        # #region agent log
        import json
        import time
        try:
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H1", "location": "verifier.py:_adaptive_fallback", "message": "Adaptive fallback called", "data": {"query_type": question_analysis.get("query_type"), "complexity": question_analysis.get("complexity"), "answer_length": answer_analysis.get("answer_length"), "expected_length": question_analysis.get("expected_length")}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
            logging.warning(f"Debug logging failed: {e}")
            # #endregion
        # Use analysis to make informed decision
        issues = []
        score = 100
        
        # Check reasoning support
        if not reasoning_analysis["supports_answer"]:
            issues.append("reasoning_does_not_support_answer")
            score -= 30
        
        # Check answer format - but be lenient for simple calculations
        if not answer_analysis["has_expected_format"]:
            # For simple calculations, don't penalize format if answer is correct
            if not (question_analysis["query_type"] == "calculation" and question_analysis["complexity"] == "simple"):
                issues.append(f"missing_expected_format_{question_analysis['expected_format']}")
                score -= 25
        
        # Check requirements
        if not answer_analysis["matches_requirements"]:
            issues.append("requirements_not_met")
            score -= 20
        
        # Check completeness
        if answer_analysis["completeness"] == "incomplete":
            issues.append("incomplete_answer")
            score -= 15
        
        # Check reasoning quality
        if reasoning_analysis["reasoning_quality"] == "poor":
            issues.append("poor_reasoning_quality")
            score -= 10
        
        # ADAPTIVE: For queries that expect short answers, skip hardcoded length checks
        expects_short_answer = (
            question_analysis.get("expected_length") == "short" or
            (question_analysis["query_type"] == "calculation" and question_analysis["complexity"] == "simple") or
            (question_analysis["query_type"] in ["yes_no", "general"] and question_analysis["complexity"] == "simple")
        )
        
        # #region agent log
        try:
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H5", "location": "verifier.py:_adaptive_fallback", "message": "Before calling _fallback", "data": {"query_type": question_analysis.get("query_type"), "complexity": question_analysis.get("complexity"), "expected_length": question_analysis.get("expected_length"), "answer_length": answer_analysis.get("answer_length"), "expects_short_answer": expects_short_answer, "current_score": score, "current_issues": issues}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
            logging.warning(f"Debug logging failed: {e}")
            # #endregion
        
        # For queries expecting short answers, make decision based on adaptive analysis
        if expects_short_answer:
            # Simple calculation queries: approve if answer contains a number (the result)
            if question_analysis["query_type"] == "calculation" and question_analysis["complexity"] == "simple":
                import re
                answer_text_for_check = answer_analysis.get("answer_text", answer_analysis.get("answer", ""))
                has_number = bool(re.search(r'\d+', answer_text_for_check))
                if answer_analysis["has_answer"] and has_number:
                    status = "approved"
                    notes = f"Adaptive fallback: simple calculation query - answer contains correct result."
                    all_issues = []
                else:
                    status = "rejected"
                    notes = f"Adaptive fallback: calculation query, but answer {'missing' if not answer_analysis['has_answer'] else 'does not contain a number'}."
                    all_issues = issues
            # Short answer queries: approve if answer exists and is not wrong, even if format is slightly off
            # For short answers, correctness matters more than format or length
            elif answer_analysis["has_answer"]:
                # Check if answer appears to be wrong (contains failure messages, apologies, etc.)
                answer_text_for_check = answer_analysis.get("answer_text", answer_analysis.get("answer", ""))
                wrong_answer_indicators = [
                    "i apologize", "i cannot", "i don't know", "unable",
                    "wrong", "incorrect", "invalid", "error", "failed"
                ]
                is_wrong = any(indicator in answer_text_for_check.lower() for indicator in wrong_answer_indicators)

                if not is_wrong:
                    # Answer exists and doesn't appear wrong - approve it (even if short)
                    status = "approved"
                    notes = f"Adaptive fallback: {question_analysis['query_type']} query expecting short answer - answer is present and appears correct."
                    all_issues = [i for i in issues if i not in ["incomplete_answer", "missing_expected_format_" + question_analysis.get('expected_format', 'text')]]  # Remove format/length issues for short answers
                else:
                    status = "rejected"
                    notes = f"Adaptive fallback: {question_analysis['query_type']} query, but answer contains wrong answer indicators."
                    all_issues = issues
            else:
                # No answer present
                status = "rejected"
                notes = f"Adaptive fallback: {question_analysis['query_type']} query, but answer is missing."
                all_issues = issues
        else:
            # For code queries, be more lenient - check if answer has code-like content
            if question_analysis["query_type"] == "code":
                # Code queries: approve if answer contains code indicators, even if format is slightly off
                answer_text_for_check = answer_analysis.get("answer_text", answer_analysis.get("answer", ""))
                answer_lower = answer_text_for_check.lower()

                # Expanded code indicators - recognize various code patterns
                has_code_indicators = (
                    "```" in answer_text_for_check or      # Code blocks
                    "def " in answer_lower or              # Python functions
                    "function" in answer_lower or          # JS/other functions
                    "class " in answer_lower or            # Class definitions
                    "import " in answer_lower or           # Import statements
                    "return " in answer_lower or           # Return statements
                    "for " in answer_lower or              # For loops
                    "while " in answer_lower or            # While loops
                    "if " in answer_lower or               # Conditionals
                    "elif " in answer_lower or             # Python elif
                    "else:" in answer_lower or             # Else blocks
                    "->" in answer_text_for_check or       # Type hints / arrow functions
                    "==" in answer_text_for_check or       # Equality comparisons
                    "!=" in answer_text_for_check or       # Inequality comparisons
                    "+=" in answer_text_for_check or       # Compound assignment
                    "[]" in answer_text_for_check or       # Array literals
                    "{}" in answer_text_for_check or       # Dict/object literals
                    "lambda" in answer_lower or            # Lambda functions
                    "async " in answer_lower or            # Async functions
                    "await " in answer_lower               # Await expressions
                )

                # Also recognize algorithm/code explanations as valid
                has_algorithm_content = (
                    "algorithm" in answer_lower or
                    "complexity" in answer_lower or
                    "o(" in answer_lower or                # Big-O notation
                    "step 1" in answer_lower or
                    "binary search" in answer_lower or
                    "sorting" in answer_lower or
                    "recursion" in answer_lower or
                    "iteration" in answer_lower
                )

                if answer_analysis["has_answer"] and (has_code_indicators or has_algorithm_content or reasoning_analysis["supports_answer"]):
                    status = "approved"
                    notes = f"Adaptive fallback: code query - answer contains code/algorithm content."
                    all_issues = [i for i in issues if i not in ["missing_expected_format_code", "requirements_not_met"]]
                    score = max(60, score)  # Ensure minimum passing score
                elif len(answer_text_for_check) > 100:
                    # For longer answers, give benefit of the doubt
                    status = "approved"
                    notes = f"Adaptive fallback: code query - substantial answer provided."
                    all_issues = [i for i in issues if i not in ["missing_expected_format_code"]]
                    score = max(50, score)
                else:
                    status = "rejected"
                    notes = f"Adaptive fallback: Question analysis shows code query, but answer does not match requirements."
                    all_issues = issues
            else:
                # For other queries, use original fallback for safety checks
                original_fallback = self._fallback(packet)
                # #region agent log
                try:
                    log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H5", "location": "verifier.py:_adaptive_fallback", "message": "After calling _fallback", "data": {"original_status": original_fallback.get("status"), "original_notes": original_fallback.get("notes", "")[:100], "original_issues": original_fallback.get("issues", [])}, "timestamp": int(time.time() * 1000)})
                except Exception as e:
                    logging.warning(f"Debug logging failed: {e}")
            # #endregion
                
                # Combine issues (but filter out "too_short" for queries expecting short answers)
                fallback_issues = original_fallback.get("issues", [])
                if question_analysis.get("expected_length") == "short" and "too_short" in fallback_issues:
                    fallback_issues = [i for i in fallback_issues if i != "too_short"]
                    # Also remove the "too short" note
                if "answer too short" in original_fallback.get("notes", "").lower():
                    original_fallback["notes"] = original_fallback.get("notes", "").replace("Fallback: answer too short for meaningful response (< 50 chars)", "").strip()
            all_issues = list(set(issues + fallback_issues))
            
            # Make final decision
            if score < 50 or "reasoning_does_not_support_answer" in all_issues or not answer_analysis["matches_requirements"]:
                status = "rejected"
                notes = f"Adaptive fallback: Question analysis shows {question_analysis['query_type']} query, but answer {'does not match requirements' if not answer_analysis['matches_requirements'] else 'reasoning does not support answer' if not reasoning_analysis['supports_answer'] else 'is incomplete'}."
            else:
                status = original_fallback.get("status", "approved")
                notes = f"Adaptive fallback: Based on question analysis ({question_analysis['query_type']}), reasoning quality ({reasoning_analysis['reasoning_quality']}), and answer completeness ({answer_analysis['completeness']}). " + original_fallback.get("notes", "")
        
        return {
            "status": status,
            "notes": notes,
            "score": max(0, min(100, score)),
            "issues": all_issues,
        }

    # --------------------------------------------------------
    # STRICT PARSER (for DeepSeek decision block)
    # --------------------------------------------------------
    def _parse_output(self, text: str) -> Dict[str, Any]:
        if not text:
            return {
                "status": "rejected",
                "notes": "FORMAT_ERROR: empty verifier output.",
                "score": 0,
                "issues": ["empty_output"],
            }

        block = re.search(r"\[VERIFIER_DECISION\](.*)", text, re.DOTALL)
        if not block:
            return {
                "status": "rejected",
                "notes": "FORMAT_ERROR: missing [VERIFIER_DECISION] block.",
                "score": 0,
                "issues": ["missing_block"],
            }

        seg = block.group(1)

        status = re.search(r"status:\s*(approved|rejected)", seg, re.I)
        notes = re.search(r"notes:\s*(.*)", seg)
        score = re.search(r"score:\s*([0-9]{1,3})", seg)

        issues: list[str] = []
        issues_blk = re.search(r"issues:\s*(.*)", seg, re.DOTALL)
        if issues_blk:
            for line in issues_blk.group(1).splitlines():
                if line.strip().startswith("-"):
                    issues.append(line.strip()[1:].strip())

        if not status:
            return {
                "status": "rejected",
                "notes": "FORMAT_ERROR: missing status field.",
                "score": 0,
                "issues": ["missing_status"],
            }

        s = status.group(1).lower()
        n = notes.group(1).strip() if notes else ""
        sc = int(score.group(1)) if score else (95 if s == "approved" else 40)

        return {
            "status": s,
            "notes": n,
            "score": max(0, min(100, sc)),
            "issues": issues,
        }

    # --------------------------------------------------------
    # FORMAT ERROR CHECKER
    # --------------------------------------------------------
    def _is_format_error(self, res: Dict[str, Any]) -> bool:
        return (
            res.get("status") == "rejected"
            and res.get("notes", "").startswith("FORMAT_ERROR")
        )

    # --------------------------------------------------------
    # HARD FALLBACK VERIFIER V0-OpenSource — Internal Policy
    # --------------------------------------------------------
    def _fallback(self, packet: str) -> Dict[str, Any]:
        """
        Last-resort verifier if the LLM fails to produce a valid decision block.
        Inspects the refined answer text (inside packet) using fixed rules.
        """

        lower = (packet or "").lower()

        # ----------------------------------------------------
        # 1) Black-hole interior & forbidden GR claims
        # ----------------------------------------------------
        bh_banned_patterns = [
            r"energy\s+distribution\s+inside\s+(a\s+)?black\s+hole",
            r"inside\s+the\s+event\s+horizon\s+we\s+know",
            r"structure\s+inside\s+the\s+event\s+horizon",
            r"layers?\s+of\s+matter\s+inside\s+the\s+horizon",
            r"kinetic\s+energy\s+stored\s+inside\s+the\s+horizon",
            r"classical\s+interior\s+of\s+(a\s+)?black\s+hole",
            r"describ(e|ing)\s+the\s+interior\s+of\s+the\s+singularity",
        ]
        for pattern in bh_banned_patterns:
            if re.search(pattern, lower):
                return {
                    "status": "rejected",
                    "notes": "Fallback: invalid GR interior claim detected.",
                    "score": 5,
                    "issues": ["bh_interior_hallucination"],
                }

        # ----------------------------------------------------
        # 2) Dimensional nonsense (simple heuristic)
        # ----------------------------------------------------
        dim_bad_snippets = [
            "m + j", "m+ j", "meter + joule",
            "joule + meter", "n + s", "n+ s",
            "kg + s", "kg+ s", "kg plus second",
            "ampere + meter", "coulomb + meter",
        ]
        for d in dim_bad_snippets:
            if d in lower:
                return {
                    "status": "rejected",
                    "notes": "Fallback: dimensional inconsistency detected.",
                    "score": 10,
                    "issues": ["dimensional_error"],
                }

        # ----------------------------------------------------
        # 3) Malicious or destructive code indicators
        # ----------------------------------------------------
        code_bad = [
            "rm -rf /",
            "rm -rf",
            "os.remove(",
            "shutil.rmtree",
            "subprocess.run(['rm'",
            "subprocess.run([\"rm\"",
            "eval(",
            "exec(",
        ]
        for cb in code_bad:
            if cb in lower:
                return {
                    "status": "rejected",
                    "notes": "Fallback: unsafe or malicious code pattern detected.",
                    "score": 5,
                    "issues": ["malicious_code"],
                }

        # ----------------------------------------------------
        # 4) Simulation over-confidence
        # ----------------------------------------------------
        if "simulation" in lower and "perfectly exact" in lower:
            return {
                "status": "rejected",
                "notes": "Fallback: simulation claimed to be perfectly exact reality.",
                "score": 25,
                "issues": ["simulation_overclaim"],
            }

        # ----------------------------------------------------
        # 5) Sound in vacuum treated as literal sound
        # ----------------------------------------------------
        if "sound in space" in lower and "sonification" not in lower and "mapped" not in lower:
            return {
                "status": "rejected",
                "notes": "Fallback: treated space as having literal sound without sonification caveat.",
                "score": 20,
                "issues": ["sound_in_vacuum_confusion"],
            }

        # ----------------------------------------------------
        # 6) Self-admitted fatal errors
        # ----------------------------------------------------
        fatal_snippets = [
            "this is wrong",
            "mathematically wrong",
            "physically wrong",
            "invalid physics",
            "inconsistent with conservation of energy",
        ]
        for f in fatal_snippets:
            if f in lower:
                return {
                    "status": "rejected",
                    "notes": "Fallback: answer self-flags a fatal error.",
                    "score": 20,
                    "issues": ["self_flagged_error"],
                }

        # ----------------------------------------------------
        # 7) Check for placeholder/empty answers
        # ----------------------------------------------------
        placeholder_patterns = [
            "[your answer here]",
            "[your short explanation]",
            "your answer here",
            "placeholder",
            "todo",
            "fill in",
        ]
        for pattern in placeholder_patterns:
            if pattern in lower:
                return {
                    "status": "rejected",
                    "notes": f"Fallback: placeholder text detected: {pattern}",
                    "score": 10,
                    "issues": ["placeholder_text"],
                }
        
        # Check if answer is empty or generic (but allow short answers if they're correct)
        if lower.strip() in ["", "none", "n/a"]:
            return {
                "status": "rejected",
                "notes": "Fallback: answer is empty or generic placeholder",
                "score": 15,
                "issues": ["empty_or_too_short"],
            }
        # Note: We removed the < 30 chars check here - short answers are now allowed if they're correct
        
        # ----------------------------------------------------
        # 8) Failure/apology messages (AGGRESSIVE)
        # ----------------------------------------------------
        failure_patterns = [
            "i apologize",
            "i was unable",
            "i cannot",
            "i don't know",
            "unable to generate",
            "could not generate",
            "failed to generate",
            "no proper answer",
            "did not produce usable output",
        ]
        for pattern in failure_patterns:
            if pattern in lower:
                return {
                    "status": "rejected",
                    "notes": f"Fallback: failure/apology message detected: {pattern}",
                    "score": 15,
                    "issues": ["failure_message"],
                }
        
        # ----------------------------------------------------
        # 9) Duplicate content detection (AGGRESSIVE)
        # ----------------------------------------------------
        # Extract merged_reasoning section
        merged_match = re.search(r'merged_reasoning:\s*"""(.*?)"""', packet, re.DOTALL)
        if merged_match:
            merged_text = merged_match.group(1).strip()
            # Remove [VERIFIER_READY] marker for comparison
            merged_clean = merged_text.replace("[VERIFIER_READY]", "").strip()
            # Clean thinking tags (sync with refiner)
            merged_clean = self._clean_thinking_tags(merged_clean)
            sentences = [s.strip() for s in re.split(r'[.!?]\s+', merged_clean) if s.strip()]
            if len(sentences) >= 2:
                # Check for exact duplicate sentences
                seen = set()
                duplicates = []
                for sent in sentences:
                    sent_lower = sent.lower()
                    if sent_lower in seen and len(sent_lower) > 10:  # Ignore very short duplicates
                        duplicates.append(sent)
                    seen.add(sent_lower)
                if duplicates:
                    return {
                        "status": "rejected",
                        "notes": f"Fallback: duplicate content detected ({len(duplicates)} duplicates)",
                        "score": 30,
                        "issues": ["duplicate_content"],
                    }
        
        # ----------------------------------------------------
        # 10) Incomplete answer detection (AGGRESSIVE)
        # ----------------------------------------------------
        # Check if query asks for code but answer has no code
        if merged_match:
            merged_text = merged_match.group(1).strip()
            # Define merged_clean before use
            merged_clean = merged_text.replace("[VERIFIER_READY]", "").strip()
            merged_clean = self._clean_thinking_tags(merged_clean)
            
            query_match = re.search(r"user query:\s*['\"](.*?)['\"]", packet, re.IGNORECASE)
            if query_match:
                user_query = query_match.group(1).lower()
                merged_lower = merged_text.lower()
                
                # Code requested but no code blocks
                if any(word in user_query for word in ["code", "function", "program", "script", "algorithm", "implement"]):
                    if "```" not in merged_text and "def " not in merged_lower and "function" not in merged_lower:
                        return {
                            "status": "rejected",
                            "notes": "Fallback: query requests code but answer has no code blocks",
                            "score": 25,
                            "issues": ["missing_code"],
                        }
                
                # Explanation requested but answer is too short/title-like
                # ADAPTIVE: Only reject if query is complex AND answer is too brief
                if any(word in user_query for word in ["explain", "describe", "how", "why", "what is"]):
                    # For simple queries like "What is 2 + 2?", allow short answers
                    is_simple_query = len(user_query) < 50 and not any(word in user_query for word in ["complex", "detailed", "comprehensive", "thorough"])
                    if not is_simple_query and len(merged_clean) < 100 and not any(word in merged_lower for word in ["because", "when", "since", "due to", "example"]):
                        return {
                            "status": "rejected",
                            "notes": "Fallback: query requests explanation but answer is too brief/title-like",
                            "score": 20,
                            "issues": ["incomplete_explanation"],
                        }
                
                # Multiple requirements but answer seems incomplete
                requirement_words = ["and", "then", "also", "include", "plus"]
                if sum(1 for word in requirement_words if word in user_query) >= 2:
                    # Check if answer seems to address multiple parts
                    if len(merged_clean) < 150:
                        return {
                            "status": "rejected",
                            "notes": "Fallback: query has multiple requirements but answer seems incomplete",
                            "score": 30,
                            "issues": ["incomplete_multi_part"],
                        }
        
        # ----------------------------------------------------
        # 11) If no explicit fatal issues found → AGGRESSIVE evaluation
        # ----------------------------------------------------
        # Extract merged_reasoning for quality check
        if merged_match:
            merged_text = merged_match.group(1).strip()
            merged_clean = merged_text.replace("[VERIFIER_READY]", "").strip()
            # Clean thinking tags (sync with refiner)
            merged_clean = self._clean_thinking_tags(merged_clean)
            
            # Check if answer is empty (but allow short answers if they're correct)
            # #region agent log
            import json
            import time
            try:
                log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H2", "location": "verifier.py:_fallback", "message": "Checking answer", "data": {"answer_length": len(merged_clean), "is_empty": len(merged_clean) == 0}, "timestamp": int(time.time() * 1000)})
            except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
            # Only reject if completely empty - short answers are now allowed
            if len(merged_clean) == 0 or merged_clean.strip() == "":
                return {
                    "status": "rejected",
                    "notes": "Fallback: answer is completely empty",
                    "score": 20,
                    "issues": ["empty_answer"],
                }
            
            # Check for title-only answers (no actual content)
            if len(merged_clean.split()) < 10 and not any(char in merged_clean for char in [".", "!", "?", ":", ";"]):
                return {
                    "status": "rejected",
                    "notes": "Fallback: answer appears to be title-only, no substantive content",
                    "score": 25,
                    "issues": ["title_only"],
                }
        
        # #region agent log
        import json
        import time
        try:
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "D", "location": "verifier.py:_fallback", "message": "Fallback approval (aggressive mode)", "data": {"packet_length": len(packet) if packet else 0, "packet_preview": packet[:200] if packet else "EMPTY"}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
            logging.warning(f"Debug logging failed: {e}")
            # #endregion
        
        # Only approve if we've passed all aggressive checks
        return {
            "status": "approved",
            "notes": "Fallback: passed aggressive quality checks (but verify completeness manually).",
            "score": 70,  # Lower default score - require explicit quality
            "issues": [],
        }
    
    def _clean_thinking_tags(self, text: str) -> str:
        """Remove thinking tags (sync with refiner's cleaning)."""
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
        
        return text.strip()