# ============================================================
#  ANM V0-OpenSource — Prompt Optimizer
#  Small model that refines user prompts for better ANM performance
# ============================================================

"""
ANM Prompt Optimizer - Refines user prompts using a small, fast model.

This module uses a lightweight model to:
- Clarify ambiguous queries
- Add context for better routing
- Improve prompt structure
- Enhance specificity
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from anm.system.inference import InferenceConfig, get_inference_engine, InferenceEngine


class PromptOptimizer:
    """
    Optimizes user prompts for better ANM performance.
    
    Uses a small, fast model to refine prompts by:
    - Clarifying ambiguous language
    - Adding missing context
    - Improving structure
    - Enhancing specificity
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize the prompt optimizer.
        
        Args:
            enabled: Whether prompt optimization is enabled
        """
        self.enabled = enabled
        
    def _get_engine(self) -> tuple[InferenceEngine, bool]:
        """
        Get the inference engine for prompt optimization (always uses quick mode).
        
        Returns:
            Tuple of (engine, original_quick_mode) to restore later
        """
        # Save current engine state to restore later
        current_engine = get_inference_engine()
        original_quick_mode = current_engine.config.quick_mode if current_engine.config else False
        
        # Temporarily switch to quick mode for optimization
        config = InferenceConfig(
            quick_mode=True,
            quick_max_tokens=256,  # Short responses for prompt refinement
            quick_temperature=0.2,  # Low temperature for consistent refinement
        )
        engine = get_inference_engine(config)
        
        return engine, original_quick_mode
    
    def optimize(self, user_prompt: str, context: Optional[str] = None) -> str:
        """
        Optimize a user prompt for better ANM processing.
        
        Args:
            user_prompt: The original user prompt
            context: Optional context about what the user is trying to do
        
        Returns:
            Optimized prompt
        """
        if not self.enabled:
            return user_prompt
        
        # Skip optimization for very short prompts (likely already clear)
        if len(user_prompt.strip()) < 10:
            return user_prompt
        
        original_quick_mode = None
        try:
            engine, original_quick_mode = self._get_engine()
            
            # Build optimization prompt
            optimization_prompt = self._build_optimization_prompt(user_prompt, context)
            
            # Get optimized version
            optimized = engine.generate(optimization_prompt, max_tokens=256)
            
            # Clean and validate the optimized prompt
            optimized = self._clean_optimized_prompt(optimized, user_prompt)
            
            return optimized
            
        except Exception as e:
            # If optimization fails, return original prompt
            # Log error for debugging (only if optimization was attempted)
            if self.enabled:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Prompt optimization failed: {e}", exc_info=True)
            return user_prompt
        finally:
            # Always restore original engine mode if it was changed
            if original_quick_mode is not None:
                try:
                    current_engine = get_inference_engine()
                    if current_engine.config.quick_mode != original_quick_mode:
                        # Restore original mode
                        restore_config = InferenceConfig(quick_mode=original_quick_mode)
                        get_inference_engine(restore_config)
                except Exception:
                    # Don't fail if restore fails - log for debugging
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug("Failed to restore inference engine mode after optimization", exc_info=True)
    
    def _build_optimization_prompt(self, user_prompt: str, context: Optional[str] = None) -> str:
        """Build the prompt for the optimizer model."""
        base_prompt = f"""You are a prompt optimizer for ANM (Artificial Neural Mesh), a multi-agent AI system.

Your task: Refine the user's prompt to make it clearer, more specific, and better suited for ANM's multi-domain reasoning system.

RULES:
1. Keep the user's intent and meaning exactly the same
2. Add clarity and specificity where needed
3. Structure the prompt for better domain routing (math, physics, code, etc.)
4. Remove ambiguity
5. Keep it concise - don't add unnecessary words
6. If the prompt is already clear, return it mostly unchanged

USER PROMPT:
{user_prompt}
"""
        
        if context:
            base_prompt += f"\nCONTEXT: {context}\n"
        
        base_prompt += "\nOPTIMIZED PROMPT (refined version only, no explanation):"
        
        return base_prompt
    
    def _clean_optimized_prompt(self, optimized: str, original: str) -> str:
        """Clean and validate the optimized prompt."""
        # Remove common prefixes/suffixes the model might add
        prefixes_to_remove = [
            "Optimized prompt:",
            "Refined prompt:",
            "Here's the optimized version:",
            "OPTIMIZED PROMPT:",
            "REFINED:",
        ]

        cleaned = optimized.strip()

        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()

        # Remove quotes if the model wrapped it
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        if cleaned.startswith("'") and cleaned.endswith("'"):
            cleaned = cleaned[1:-1]

        # Validate: don't return empty or too different
        if not cleaned or len(cleaned) < 5:
            return original

        # If optimized version is way longer, might be adding too much
        if len(cleaned) > len(original) * 3:
            return original

        # CRITICAL FIX: Check for query meaning corruption
        # If the optimizer completely changed the question, reject it
        original_lower = original.lower()
        cleaned_lower = cleaned.lower()

        # Extract key question words from original
        key_words = []
        if "what is" in original_lower or "what's" in original_lower:
            key_words.append("what")
        if "when" in original_lower:
            key_words.append("when")
        if "where" in original_lower:
            key_words.append("where")
        if "who" in original_lower:
            key_words.append("who")
        if "why" in original_lower:
            key_words.append("why")
        if "how" in original_lower:
            key_words.append("how")

        # Check if question type changed (e.g., "what" -> "when")
        if key_words:
            if not any(word in cleaned_lower for word in key_words):
                # Question type changed - reject optimization
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Prompt optimizer changed question type. Original: '{original}' -> Optimized: '{cleaned}'. Rejecting optimization.")
                return original

        # Check for key nouns/entities in factual questions
        # Extract potential entities (capitalized words, numbers, quoted terms)
        import re
        original_entities = set(re.findall(r'\b[A-Z][a-z]+\b|\b\d+\b', original))
        cleaned_entities = set(re.findall(r'\b[A-Z][a-z]+\b|\b\d+\b', cleaned))

        # If original had entities and they're all missing, likely corrupted
        if original_entities and not original_entities.intersection(cleaned_entities):
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Prompt optimizer removed all entities. Original: '{original}' -> Optimized: '{cleaned}'. Rejecting optimization.")
            return original

        return cleaned.strip()
    
    def optimize_batch(self, prompts: list[str]) -> list[str]:
        """
        Optimize multiple prompts.
        
        Args:
            prompts: List of user prompts
        
        Returns:
            List of optimized prompts
        """
        if not self.enabled:
            return prompts
        
        return [self.optimize(prompt) for prompt in prompts]
    
    def is_enabled(self) -> bool:
        """Check if prompt optimization is enabled."""
        return self.enabled
    
    def enable(self) -> None:
        """Enable prompt optimization."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable prompt optimization."""
        self.enabled = False


__all__ = ["PromptOptimizer"]

