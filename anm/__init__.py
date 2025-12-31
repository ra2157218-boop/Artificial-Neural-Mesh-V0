# ============================================================
#  ANM V0-OpenSource — ARTIFICIAL NEURAL MESH
#  Complete Multi-Agent AI System with Self-Improvement
#  Unified • Optimized • Open Source
# ============================================================

"""
ANM (Artificial Neural Mesh) V0-OpenSource

A modular, safe, controlled, self-upgrading AI system featuring:

CORE CAPABILITIES:
- Multi-domain reasoning via TrueWoT V15 MAX (Web-of-Thought)
- Metacognitive self-awareness and quality control
- Self-improvement through the Expansion Pipeline
- Memory-based learning (LFM + PointGame + Epistemic Humility)
- Safety verification (LawBook + Verifier)
- Universal 2D Simulation (Nebula Engine V3)
- Offline Voice I/O (Whisper + Piper)

ARCHITECTURE:
- Router: Intelligent query classification and domain routing
- Specialists: 12 domain-specific LLM modules
- TrueWoT V15: Metacognitive multi-specialist reasoning engine
- Expansion: Controlled self-improvement pipeline
- Memory Hub: Episodic, semantic, and behavioral memory
- MetaCognition: Comprehensive self-awareness system
- Voice I/O: Offline speech recognition and synthesis

DESIGN PRINCIPLES:
- High-quality, production-ready code
- Thread-safe with optimized concurrency
- Seamless component integration
- Backward compatibility maintained
- Epistemic humility in all learning

Usage:
    from anm import ANM, ANMConfig
    
    # Basic usage
    anm = ANM()
    result = anm.query("Explain quantum entanglement")
    print(result["result"])
    
    # With configuration
    config = ANMConfig(
        parallel_models=4,
        voice_enabled=True,
        hands_free=True,
    )
    anm = ANM(config=config)
    anm.start()  # Hands-free voice mode

VERSION: 0.1.0-opensource (Aurora)
"""

from __future__ import annotations
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from anm.utils.debug_logger import log_debug

__version__ = "0.1.0-opensource"
__codename__ = "Aurora"
__author__ = "ANM Team"


# ============================================================
#  ANM CONFIGURATION
# ============================================================

@dataclass
class ANMConfig:
    """
    ANM Configuration Options.
    
    Parallel Models:
        parallel_models: Number of parallel R1 model instances (1-10)
        - 1: Minimal resource usage, slower
        - 2: Default, good balance (recommended for most systems)
        - 4: More parallelism, faster but uses more resources
        - 10: Maximum parallelism, requires high-end hardware
    
    Quick Mode:
        quick_mode: Use smaller, faster model without chain-of-thought reasoning
        - True: Uses TinyLlama-1.1B (smaller, faster, direct answers)
        - False: Uses DeepSeek-R1-1.5B (default, with CoT reasoning)
        - Quick mode is ideal for simple queries, faster responses, lower resource usage
    
    Auto Mode:
        auto_mode: ALWAYS ENABLED - Automatically choose quick/normal mode based on query complexity
        - Always True: Analyzes each query and uses quick mode (TinyLLama) for simple queries, normal mode (DeepSeek-R1) for complex ones
        - Smart detection: Considers query length, complexity indicators, domain keywords, and intent
        - Provides best balance: fast for simple queries, thorough for complex ones
        - Cannot be disabled - ensures optimal performance for all queries
    
    Prompt Optimization:
        optimize_prompts: Use small model to refine user prompts before processing
        - True: Prompts are optimized for clarity, specificity, and better routing
        - False: Prompts are used as-is (default)
        - Optimization improves ANM's understanding and routing accuracy
    
    Voice I/O:
        voice_enabled: Enable voice input/output
        hands_free: Continuous listening mode (no touch needed)
        voice_model: Whisper model size (tiny/base/small/medium/large)
        voice_language: Language for STT (None = auto-detect)
        tts_voice: Piper voice name
        tts_speed: Speaking speed (0.5-2.0)
    
    Learning:
        enable_learning: Enable behavioral learning from interactions
    
    Safety:
        skip_sanity_check: Skip startup safety checks
        auto_fix: Auto-fix issues during sanity check
    """
    
    # Parallel Models (MIN=1, MAX=10, DEFAULT=2)
    parallel_models: int = 2
    
    # Voice I/O (Optional)
    voice_enabled: bool = False
    hands_free: bool = False          # Continuous listening (no touch mode)
    voice_model: str = "base"         # Whisper model: tiny/base/small/medium/large
    voice_language: Optional[str] = None  # Auto-detect if None
    tts_voice: str = "en_US-lessac-medium"
    tts_speed: float = 1.0
    wake_word: Optional[str] = None   # Optional wake word (e.g., "hey anm")
    exit_phrase: str = "goodbye"      # Phrase to exit voice mode
    
    # Learning
    enable_learning: bool = True
    
    # Quick Mode (fast, no chain-of-thought)
    quick_mode: bool = False  # Use smaller, faster model without CoT reasoning (ignored if auto_mode=True)
    auto_mode: bool = True  # ALWAYS ENABLED: Automatically choose quick/normal based on query complexity

    # Research Mode (maximum quality, structured PDF output)
    research_mode: bool = False  # Research mode: deterministic routing, authority models, PDF output

    # Prompt Optimization
    optimize_prompts: bool = True  # Use small model to refine user prompts before processing (auto-enabled)

    # Safety
    skip_sanity_check: bool = False
    auto_fix: bool = True
    verbose: bool = True
    
    def __post_init__(self):
        """Validate configuration."""
        # Clamp parallel_models to 1-10
        if self.parallel_models < 1:
            self.parallel_models = 1
        elif self.parallel_models > 10:
            self.parallel_models = 10
        
        # Validate voice_model
        valid_models = ["tiny", "base", "small", "medium", "large"]
        if self.voice_model not in valid_models:
            self.voice_model = "base"
        
        # Validate tts_speed
        if self.tts_speed < 0.5:
            self.tts_speed = 0.5
        elif self.tts_speed > 2.0:
            self.tts_speed = 2.0

        # Research mode validation
        if self.research_mode and self.auto_mode:
            self.auto_mode = False  # Disable auto mode

        if self.research_mode and self.quick_mode:
            raise ValueError("Research mode cannot be used with quick mode")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Router config."""
        return {
            "parallel_r1_workers": self.parallel_models,
            "quick_mode": self.quick_mode,
            "auto_mode": self.auto_mode,
            "research_mode": self.research_mode,
            "optimize_prompts": self.optimize_prompts,
            "voice": {
                "enabled": self.voice_enabled,
                "hands_free": self.hands_free,
                "model": self.voice_model,
                "language": self.voice_language,
                "tts_voice": self.tts_voice,
                "tts_speed": self.tts_speed,
                "wake_word": self.wake_word,
                "exit_phrase": self.exit_phrase,
            },
            "learning": self.enable_learning,
        }


# ============================================================
#  UNIFIED ANM INTERFACE
# ============================================================

class ANM:
    """
    Unified ANM Interface — MAXIMUM LEVEL.
    
    This is the main entry point for interacting with ANM.
    It provides a simple, unified API for all ANM capabilities.
    
    Features:
    - Configurable parallel models (1-10, default 2)
    - Optional voice I/O with hands-free mode
    - Pre-startup sanity check with auto-fix
    - Unified memory system with MemoryHub
    - Continuous learning with LearningEngine
    - Smart strategy recommendations
    
    Usage:
        # Default (2 parallel models, no voice)
        anm = ANM()
        
        # Custom configuration
        from anm import ANM, ANMConfig
        config = ANMConfig(
            parallel_models=4,      # Use 4 parallel R1 instances
            voice_enabled=True,     # Enable voice
            hands_free=True,        # Continuous listening
        )
        anm = ANM(config)
        anm.start()  # Starts hands-free voice mode
    """
    
    def __init__(
        self,
        config: Optional[ANMConfig] = None,
        # Legacy parameters (deprecated, use ANMConfig instead)
        parallel_models: Optional[int] = None,
        voice_enabled: Optional[bool] = None,
        hands_free: Optional[bool] = None,
        skip_sanity_check: bool = False,
        auto_fix: bool = True,
        verbose: bool = True,
        enable_learning: bool = True,
    ):
        """
        Initialize ANM.
        
        Args:
            config: ANMConfig object with all settings
            parallel_models: Number of parallel R1 models (1-10, default 2)
            voice_enabled: Enable voice I/O
            hands_free: Enable hands-free continuous listening
            skip_sanity_check: Skip startup safety checks
            auto_fix: Auto-fix issues during sanity check
            verbose: Print progress messages
            enable_learning: Enable behavioral learning
        """
        # Build config from parameters if not provided
        if config is None:
            config = ANMConfig(
                parallel_models=parallel_models if parallel_models is not None else 2,
                voice_enabled=voice_enabled if voice_enabled is not None else False,
                hands_free=hands_free if hands_free is not None else False,
                enable_learning=enable_learning,
                skip_sanity_check=skip_sanity_check,
                auto_fix=auto_fix,
                verbose=verbose,
            )
        
        # Allow auto_mode to be disabled via config for testing/debugging
        # (Commented out forced override to allow specialist model testing)
        # config.auto_mode = True
        
        self.anm_config = config
        self.config = config.to_dict()  # For Router compatibility
        
        # Don't initialize inference engine here - auto_mode decides per-query
        # Engine will be configured dynamically based on query complexity
        
        # Initialize prompt optimizer if enabled
        self._prompt_optimizer = None
        if config.optimize_prompts:
            from anm.prompt_optimizer import PromptOptimizer
            self._prompt_optimizer = PromptOptimizer(enabled=True)
        
        self._router = None
        self._expansion_engine = None
        self._memory_hub = None
        self._learning_engine = None
        self._metacognition = None
        self._voice_io = None
        self._hands_free_thread = None
        self._hands_free_running = False
        self._initialized = False
        self._sanity_result = None
        self._enable_learning = config.enable_learning
        self._session_count = 0
        
        # Run sanity check unless skipped
        if not config.skip_sanity_check:
            # Check and download ALL required models at startup
            self._run_all_models_check(verbose=config.verbose)
            # Then run regular sanity check
            self._run_sanity_check(auto_fix=config.auto_fix, verbose=config.verbose)
        
        # Initialize voice if enabled
        if config.voice_enabled:
            self._init_voice()
    
    def _run_quick_mode_sanity_check(self, verbose: bool = True) -> bool:
        """
        Run quick mode sanity check to ensure models are downloaded.
        
        Args:
            verbose: Print progress
            
        Returns:
            True if all checks pass
        """
        from anm.system.quick_mode_sanity import QuickModeSanityCheck
        
        if verbose:
            print("Running Quick Mode sanity check...")
        
        checker = QuickModeSanityCheck()
        result = checker.check(ask_permission=False, auto_download=True)
        
        if verbose:
            for msg in result.messages:
                print(f"  {msg}")
        
        if not result.passed:
            if verbose:
                print("\n⚠️  Quick Mode sanity check failed.")
                print("   Please download the required models or disable quick mode.")
            return False
        
        if verbose:
            print("✓ Quick Mode sanity check passed")
        
        return True
    
    def _run_all_models_check(self, verbose: bool = True) -> bool:
        """
        Check and download ALL required models at startup.
        
        This checks all models from settings (base models + domain-specific models).
        
        Args:
            verbose: Print progress
            
        Returns:
            True if all checks pass
        """
        from anm.system.quick_mode_sanity import check_all_models
        
        if verbose:
            print("Running model check...")
            print("(Checking all required models: base models + domain-specific models)")
        
        result = check_all_models(ask_permission=False, auto_download=True, verbose=verbose)
        
        if verbose:
            for msg in result.messages:
                if msg.startswith("  "):  # Only print detailed messages
                    print(msg)
        
        if not result.passed:
            if verbose:
                print("\n⚠️  Model check failed.")
                print("   Some required models are missing and could not be downloaded.")
            return False
        
        if verbose:
            print("✓ All required models are available")
        
        return True
    
    def _run_auto_mode_sanity_check(self, verbose: bool = True) -> bool:
        """
        Run auto mode sanity check to ensure both quick and normal models are downloaded.
        
        Args:
            verbose: Print progress
            
        Returns:
            True if all checks pass
        """
        from anm.system.quick_mode_sanity import QuickModeSanityCheck
        
        if verbose:
            print("Running Auto Mode sanity check...")
            print("(Checking both Quick Mode and Normal Mode models)")
        
        checker = QuickModeSanityCheck()
        result = checker.check_both_models(ask_permission=False, auto_download=True)
        
        if verbose:
            for msg in result.messages:
                print(f"  {msg}")
        
        if not result.passed:
            if verbose:
                print("\n⚠️  Auto Mode sanity check failed.")
                print("   Please download the required models or disable auto mode.")
            return False
        
        if verbose:
            print("✓ Auto Mode sanity check passed")
        
        return True
    
    def _run_sanity_check(self, auto_fix: bool = True, verbose: bool = True) -> bool:
        """
        Run pre-startup sanity check with auto-fix.
        
        Args:
            auto_fix: Attempt to auto-fix issues (up to 3 retries)
            verbose: Print progress
        
        Returns:
            True if all checks pass (or issues were fixed)
        """
        from anm.sanity import SanityChecker, AutoFixer
        
        checker = SanityChecker(verbose=verbose)
        self._sanity_result = checker.run_full_check()
        
        if self._sanity_result.passed:
            return True
        
        # Try auto-fix if enabled
        if auto_fix and self._sanity_result.auto_fixable_issues:
            if verbose:
                print()
                print("🔧 Issues detected - attempting auto-fix...")
            
            fixer = AutoFixer(verbose=verbose)
            fix_results, all_fixed = fixer.fix_all_issues(
                self._sanity_result.auto_fixable_issues
            )
            
            if all_fixed:
                # Re-run sanity check to confirm
                self._sanity_result = checker.run_full_check()
                return self._sanity_result.passed
            else:
                # Some issues couldn't be fixed
                unfixed = [r for r in fix_results if not r.fixed]
                if verbose:
                    print()
                    print("=" * 60)
                    print("🚨 SANITY CHECK FAILED - HUMAN INTERVENTION REQUIRED")
                    print("=" * 60)
                    print()
                    print(f"❌ {len(unfixed)} issues could not be auto-fixed:")
                    for result in unfixed:
                        print(f"   • {result.issue_module}: {result.issue_message}")
                        if result.human_instructions:
                            print(result.human_instructions)
                    print()
                    print("Please fix the issues manually and restart ANM.")
                    print("=" * 60)
                return False
        
        return False
    
    @property
    def sanity_passed(self) -> bool:
        """Check if sanity check passed."""
        return self._sanity_result.passed if self._sanity_result else True
    
    @property
    def sanity_result(self):
        """Get the sanity check result."""
        return self._sanity_result
    
    def _ensure_initialized(self) -> None:
        """Lazy initialization of all components."""
        if self._initialized:
            return
        
        from anm.router.router import Router
        from anm.memory import MemoryHub, LearningEngine
        
        # Core components
        self._router = Router(self.config)
        
        # Expansion engine (optional - requires additional dependencies)
        try:
            from anm.expansion import ExpansionEngineV2, ExpansionConfig
            self._expansion_engine = ExpansionEngineV2(
                ExpansionConfig(**self.config.get("expansion", {}))
            )
        except (ImportError, ModuleNotFoundError) as e:
            # Expansion is optional - log but don't fail
            if self.anm_config.verbose:
                print(f"⚠️  Expansion engine unavailable (optional): {e}")
            self._expansion_engine = None
        
        # Memory and Learning (V2 Maximum Level)
        self._memory_hub = MemoryHub()
        self._learning_engine = LearningEngine()
        
        # MetaCognition (V2 Enhanced Self-Awareness)
        try:
            from anm.metacognition import MetaCognition
            self._metacognition = MetaCognition()
        except ImportError:
            self._metacognition = None
        
        self._initialized = True
    
    def query(self, user_query: str, use_memory: bool = True) -> Dict[str, Any]:
        """
        Process a user query through ANM with full feature utilization.
        
        Features used:
        - Memory context retrieval
        - Strategy recommendations
        - Post-processing learning
        - Pattern recognition
        - Auto mode: automatically chooses quick/normal based on query complexity
        
        Args:
            user_query: The user's question or request
            use_memory: Whether to use memory context
        
        Returns:
            Dict containing the result and metadata
        """
        # Input validation
        if not user_query or not isinstance(user_query, str):
            return {
                "status": "error",
                "result": "Invalid query: query must be a non-empty string",
                "error": "Invalid input",
                "router_plan": None,  # Always include router_plan key
            }

        user_query = user_query.strip()
        if not user_query:
            return {
                "status": "error",
                "result": "Invalid query: query cannot be empty",
                "error": "Empty input",
                "router_plan": None,  # Always include router_plan key
            }
        
        self._ensure_initialized()
        self._session_count += 1
        
        # Optimize prompt if enabled
        optimized_query = user_query
        if self.anm_config.optimize_prompts and self._prompt_optimizer is not None:
            try:
                optimized_query = self._prompt_optimizer.optimize(user_query)
                if optimized_query != user_query and self.anm_config.verbose:
                    print(f"[PROMPT_OPTIMIZER] Refined query for better processing")
            except (AttributeError, ImportError, TypeError, ValueError) as e:
                # If optimization fails, use original query
                if self.anm_config.verbose:
                    print(f"[PROMPT_OPTIMIZER] Optimization failed ({type(e).__name__}), using original query: {e}")
                optimized_query = user_query

        # Research mode: Always use normal mode (no quick, no auto)
        if self.anm_config.research_mode:
            use_quick = False
            if self.anm_config.verbose:
                print("[RESEARCH_MODE] Using full reasoning pipeline with maximum quality")
        else:
            # Auto mode: Check domain first to avoid overriding specialist models
            # For STEM queries (math, physics, chemistry, biology, code), specialists have their own models
            # and should NOT be overridden by Auto Mode

            # Quick coarse domain classification to check if this is a STEM query
            from anm.router.router import Router
            coarse_domain = self._router._coarse_domain_guess(optimized_query) if hasattr(self._router, '_coarse_domain_guess') else "general"

            # Domain specialists that should use their own models
            domain_specialists = {"math", "physics", "chemistry", "biology", "code"}

            # Only use Auto Mode for general queries
            # STEM specialists have Nanbeige4-3B (math/physics/chemistry/biology) and Stable-Code-3B (code)
            if coarse_domain in domain_specialists:
                # Skip Auto Mode - let specialist use its configured model
                use_quick = False
                if self.anm_config.verbose:
                    print(f"[AUTO_MODE] Bypassed for {coarse_domain} specialist (using domain model)")
            else:
                # Use Auto Mode for general queries
                use_quick = self._should_use_quick_mode(optimized_query)
                if self.anm_config.verbose:
                    mode_str = "QUICK (TinyLLama)" if use_quick else "NORMAL (DeepSeek-R1)"
                    print(f"[AUTO_MODE] Query complexity analysis: {mode_str}")

        from anm.system.inference import InferenceConfig, get_inference_engine
        inference_config = InferenceConfig(quick_mode=use_quick)
        get_inference_engine(inference_config)  # This will update the singleton's config
        
        # Get memory context and strategy recommendations
        memory_context = None
        strategy = None
        
        if use_memory:
            memory_context = self._memory_hub.get_context(optimized_query)
            
            # Get strategy recommendation based on learned patterns
            strategy = self._learning_engine.get_strategy(
                optimized_query,
                domains=[],  # Will be determined by Router
            )
        
        # Process the query (use optimized version)
        # Pass quick_mode flag to router based on actual decision
        # For auto mode, pass the per-query decision; for explicit quick mode, pass True
        result = self._router.handle(optimized_query, quick_mode=use_quick, research_mode=self.anm_config.research_mode)
        
        # Add original query to result for reference
        if optimized_query != user_query:
            result["original_query"] = user_query
            result["optimized_query"] = optimized_query
        
        # Add prompt optimization flag to router_plan for LFM learning
        if "router_plan" in result and result["router_plan"] and isinstance(result["router_plan"], dict):
            result["router_plan"]["prompt_optimized"] = (optimized_query != user_query)
        
        # Learn from this interaction
        if self._enable_learning:
            self._learn_from_result(user_query, result, memory_context)
        
        # Add memory insights to result
        if memory_context and memory_context.behavioral_insights:
            result["memory_insights"] = memory_context.behavioral_insights
        
        if strategy and strategy.get("recommendations"):
            result["strategy_used"] = strategy
        
        return result
    
    def _learn_from_result(
        self,
        query: str,
        result: Dict[str, Any],
        memory_context,
    ) -> None:
        """Learn from a completed query."""
        # #region agent log
        try:
            import json
            import time
            log_debug({"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H2", "location": "anm/__init__.py:_learn_from_result", "message": "Entering _learn_from_result", "data": {"has_router_plan_key": "router_plan" in result, "result_keys": list(result.keys())[:10]}, "timestamp": int(time.time() * 1000)})
        except Exception as e:
                logging.warning(f"Debug logging failed: {e}")
            # #endregion
        try:
            # Extract info from result
            domains = result.get("router_plan", {}).get("active_domains", [])
            if not domains:
                domains = ["general"]
            
            verification = result.get("verification", {})
            success = "pass" in str(verification).lower() or "ok" in str(verification).lower()
            
            entry_specialist = result.get("router_plan", {}).get("entry_specialist", "general")
            
            # Extract metrics from result
            processing_time_ms = result.get("processing_time_ms", 0.0)
            wot_steps = result.get("wot_steps", 0)
            
            # Learn from query
            self._learning_engine.learn_from_query(
                query=query,
                domains=domains,
                entry_specialist=entry_specialist,
                result_quality=0.8 if success else 0.4,
                processing_time_ms=processing_time_ms,
                wot_steps=wot_steps,
                success=success,
            )
            
            # Store in memory hub
            self._memory_hub.learn_from_session(
                user_query=query,
                final_answer=result.get("result", ""),
                domains=domains,
                verification=verification if isinstance(verification, dict) else {"status": str(verification)},
                router_plan=result.get("router_plan"),
                lfm_learning=result.get("lfm_report", {}).get("learning_entry"),
                run_id=result.get("log_path", "").split("_")[-1].split(".")[0] if result.get("log_path") else None,
            )
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            # Don't fail query if learning fails - log for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Learning from result failed: {type(e).__name__}: {e}", exc_info=True)
            pass
    
    def _should_use_quick_mode(self, query: str) -> bool:
        """
        SMART AUTO-MODE: Intelligently determine if quick mode should be used for a query.
        
        This method analyzes query complexity, intent, and requirements to make the best decision.
        
        Quick mode (TinyLLama) is used for:
        - Simple greetings and short queries
        - Yes/no questions
        - Simple factual questions (what, who, where, when)
        - Single-word or very short queries
        - Basic lookups and definitions
        
        Normal mode (DeepSeek-R1) is used for:
        - Complex multi-step reasoning
        - Mathematical calculations and derivations
        - Code generation and programming
        - Explanations requiring deep understanding
        - Multi-part questions
        - Technical analysis
        - Creative tasks
        """
        query_lower = query.lower().strip()
        query_len = len(query)
        query_words = query_lower.split()
        word_count = len(query_words)
        
        # ============================================================
        # QUICK MODE INDICATORS (Simple queries)
        # ============================================================
        
        # Very short queries (< 20 chars or < 3 words) -> quick mode
        if query_len < 20 or word_count < 3:
            return True
        
        # Simple greetings -> quick mode
        greetings = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "howdy", "sup"]
        if any(g in query_lower for g in greetings) and query_len < 60:
            return True
        
        # Simple yes/no questions -> quick mode
        yes_no_starters = ["is ", "are ", "can ", "do ", "does ", "did ", "will ", "would ", "should ", "could ", "has ", "have "]
        if any(query_lower.startswith(starter) for starter in yes_no_starters) and query_len < 80 and word_count < 10:
            return True
        
        # Simple factual questions (what/who/where/when) -> quick mode if short
        simple_question_words = ["what is", "what are", "who is", "who are", "where is", "where are", "when is", "when did"]
        if any(qw in query_lower for qw in simple_question_words) and query_len < 100 and word_count < 12:
            # But check if it's asking for explanation (needs normal mode)
            if not any(word in query_lower for word in ["explain", "how", "why", "describe", "detailed"]):
                return True
        
        # Simple definitions -> quick mode
        definition_patterns = ["define", "definition of", "what does", "meaning of"]
        if any(pattern in query_lower for pattern in definition_patterns) and query_len < 80:
            return True
        
        # ============================================================
        # NORMAL MODE INDICATORS (Complex queries)
        # ============================================================
        
        # Long queries (> 250 chars or > 30 words) -> normal mode
        if query_len > 250 or word_count > 30:
            return False
        
        # Multi-part questions -> normal mode
        multi_part_indicators = [" and ", " then ", " also ", " plus ", " including ", " as well as ", " along with "]
        if sum(1 for indicator in multi_part_indicators if indicator in query_lower) >= 2:
            return False
        
        # Complex reasoning indicators -> normal mode
        complex_indicators = [
            "calculate", "solve", "derive", "prove", "implement", "generate", "create", "design",
            "algorithm", "function", "code", "program", "equation", "formula", "theorem", "proof",
            "explain how", "explain why", "step by step", "detailed", "complex", "multiple", "several",
            "analyze", "compare", "contrast", "evaluate", "optimize", "improve", "refactor"
        ]
        if any(indicator in query_lower for indicator in complex_indicators):
            return False
        
        # Math/physics/code keywords -> normal mode
        domain_keywords = [
            # Math
            "integral", "derivative", "matrix", "vector", "calculus", "algebra", "geometry",
            "theorem", "proof", "equation", "formula", "solve", "calculate", "compute",
            # Physics
            "quantum", "relativity", "mechanics", "thermodynamics", "electromagnetic", "wave",
            "particle", "field", "force", "energy", "momentum", "entropy",
            # Code/Programming
            "python", "javascript", "java", "c++", "function", "class", "variable", "loop",
            "recursion", "algorithm", "data structure", "api", "framework", "library",
            "debug", "test", "optimize", "refactor", "implement", "design pattern"
        ]
        if any(keyword in query_lower for keyword in domain_keywords):
            return False
        
        # Explanation requests -> normal mode
        explanation_indicators = ["explain", "describe", "how does", "why does", "what causes", "how to", "why is"]
        if any(indicator in query_lower for indicator in explanation_indicators) and query_len > 50:
            return False
        
        # Creative/design tasks -> normal mode
        creative_indicators = ["write", "create", "design", "build", "develop", "compose", "generate", "invent"]
        if any(indicator in query_lower for indicator in creative_indicators):
            return False
        
        # Questions with multiple requirements -> normal mode
        requirement_indicators = ["include", "with", "and", "also", "plus", "should", "must", "need to"]
        if sum(1 for indicator in requirement_indicators if indicator in query_lower) >= 3:
            return False
        
        # ============================================================
        # DEFAULT DECISION
        # ============================================================
        
        # For medium-length queries (50-150 chars), use normal mode by default
        # to ensure quality, unless clearly simple
        if query_len > 50:
            return False
        
        # Short simple queries -> quick mode
        return True
    
    def expand(
        self,
        query: str,
        memory_brief: str = "",
    ) -> Dict[str, Any]:
        """
        Trigger the self-improvement pipeline.
        
        Args:
            query: Query that requires a new domain
            memory_brief: Optional memory context (auto-generated if empty)
        
        Returns:
            Expansion result
        """
        self._ensure_initialized()
        
        # Auto-generate memory brief if not provided
        if not memory_brief:
            memory_brief = self._memory_hub.build_memory_brief(query)
        
        return self._expansion_engine.run_sync(query, memory_brief)
    
    # ============================================================
    #  SMART FEATURE ACCESS
    # ============================================================
    
    def get_strategy(self, query: str, domains: Optional[list] = None) -> Dict[str, Any]:
        """Get strategy recommendations for a query."""
        self._ensure_initialized()
        return self._learning_engine.get_strategy(query, domains or [])
    
    def get_memory_context(self, query: str) -> "MemoryContext":
        """Get rich memory context for a query."""
        self._ensure_initialized()
        return self._memory_hub.get_context(query)
    
    def get_expertise(self) -> Dict[str, Any]:
        """Get ANM's current expertise levels."""
        self._ensure_initialized()
        return self._memory_hub.get_domain_expertise()
    
    def get_strengths_weaknesses(self) -> Dict[str, list]:
        """Get ANM's strengths and weaknesses."""
        self._ensure_initialized()
        return self._memory_hub.get_strengths_weaknesses()
    
    def get_self_report(self) -> str:
        """Get a self-awareness report."""
        self._ensure_initialized()
        return self._memory_hub.get_self_report()
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        self._ensure_initialized()
        return self._learning_engine.get_stats()
    
    def provide_feedback(
        self,
        feedback_type: str,
        feedback_content: str,
        related_query: Optional[str] = None,
    ) -> None:
        """
        Provide feedback to help ANM learn.
        
        Args:
            feedback_type: "positive", "negative", or "correction"
            feedback_content: The feedback content
            related_query: Optional related query
        """
        self._ensure_initialized()
        self._memory_hub.learn_from_feedback(
            feedback_type, feedback_content, related_query
        )
    
    # ============================================================
    #  PROPERTIES
    # ============================================================
    
    @property
    def router(self):
        """Get the Router instance."""
        self._ensure_initialized()
        return self._router
    
    @property
    def expansion_engine(self):
        """Get the Expansion Engine instance."""
        self._ensure_initialized()
        return self._expansion_engine
    
    @property
    def memory_hub(self):
        """Get the Memory Hub instance."""
        self._ensure_initialized()
        return self._memory_hub
    
    @property
    def learning_engine(self):
        """Get the Learning Engine instance."""
        self._ensure_initialized()
        return self._learning_engine
    
    @property
    def session_count(self) -> int:
        """Get the number of sessions processed."""
        return self._session_count
    
    @property
    def metacognition(self):
        """Get the MetaCognition instance."""
        self._ensure_initialized()
        return self._metacognition
    
    # ============================================================
    #  METACOGNITION (Self-Awareness)
    # ============================================================
    
    def introspect(self) -> str:
        """
        Generate a self-awareness report.
        
        Returns detailed information about:
        - Knowledge boundaries
        - Confidence calibration
        - Reasoning quality
        - Detected biases
        - Cognitive patterns
        """
        self._ensure_initialized()
        if self._metacognition:
            return self._metacognition.generate_introspection_report()
        return "MetaCognition not available"
    
    def assess_query(self, query: str, domain: str = "general") -> Dict[str, Any]:
        """
        Assess a query before processing.
        
        Returns:
            Assessment including readiness, strategy, warnings
        """
        self._ensure_initialized()
        if not self._metacognition:
            return {"error": "MetaCognition not available"}
        
        assessment = self._metacognition.pre_assess(query, domain)
        return {
            "readiness": assessment.overall_readiness,
            "approach": assessment.recommended_approach,
            "should_proceed": assessment.should_proceed,
            "should_defer": assessment.should_defer,
            "cognitive_load": assessment.cognitive_load.level.name,
            "knowledge_status": assessment.knowledge_boundary.status.name,
            "warnings": assessment.warnings,
            "uncertainty_preface": assessment.uncertainty_preface,
        }
    
    def reflect_on_response(
        self,
        query: str,
        reasoning: str,
        answer: str,
        domain: str = "general",
    ) -> Dict[str, Any]:
        """
        Reflect on a completed response.
        
        Returns:
            Reflection including quality, confidence, issues
        """
        self._ensure_initialized()
        if not self._metacognition:
            return {"error": "MetaCognition not available"}
        
        reflection = self._metacognition.reflect(query, reasoning, answer, domain)
        return {
            "quality": reflection.overall_quality,
            "confidence": reflection.confidence.score,
            "confidence_level": reflection.confidence.level.name,
            "uncertainty": reflection.uncertainty.total_uncertainty,
            "reasoning_quality": reflection.reasoning_quality.overall_score,
            "bias_alerts": len(reflection.bias_alerts),
            "needs_revision": reflection.needs_revision,
            "lessons": reflection.lessons_learned,
            "improvements": reflection.improvements_for_next_time,
        }
    
    def should_i_answer(self, query: str, domain: str = "general") -> Tuple[bool, str]:
        """
        Quick check: Should I attempt to answer this?
        
        Returns:
            (should_answer, reason)
        """
        self._ensure_initialized()
        if not self._metacognition:
            return True, "MetaCognition not available, proceeding anyway"
        
        return self._metacognition.should_i_answer(query, domain)
    
    def get_self_model(self) -> Dict[str, Any]:
        """
        Get a comprehensive model of ANM's self-awareness.
        
        Includes:
        - Knowledge domains and coverage
        - Calibration statistics
        - Reasoning patterns
        - Bias history
        - Strategy effectiveness
        """
        self._ensure_initialized()
        if not self._metacognition:
            return {"error": "MetaCognition not available"}
        
        return self._metacognition.get_self_model()
    
    # ============================================================
    #  VOICE I/O
    # ============================================================
    
    def _init_voice(self) -> bool:
        """Initialize voice I/O system."""
        try:
            from anm.voice import VoiceIO, VoiceConfig
            
            voice_cfg = VoiceConfig(
                stt_model=self.anm_config.voice_model,
                stt_language=self.anm_config.voice_language,
                tts_voice=self.anm_config.tts_voice,
                tts_speed=self.anm_config.tts_speed,
            )
            
            self._voice_io = VoiceIO(voice_cfg)
            
            if self._voice_io.available:
                print("✓ Voice I/O initialized")
                return True
            else:
                print("⚠ Voice I/O not available (check audio devices)")
                return False
                
        except ImportError:
            print("⚠ Voice module not available. Install: pip install openai-whisper sounddevice")
            return False
    
    def start(self) -> None:
        """
        Start ANM in hands-free voice mode.
        
        In this mode:
        - ANM continuously listens for speech
        - Processes queries automatically
        - Responds via speech
        - No device touch needed until you say the exit phrase
        
        Exit by saying the exit phrase (default: "goodbye")
        """
        if not self.anm_config.voice_enabled:
            print("Voice not enabled. Use ANMConfig(voice_enabled=True)")
            return
        
        if self._voice_io is None:
            if not self._init_voice():
                return
        
        greeting = "Hello! I'm ANM. I'm listening. Just speak naturally."
        if self.anm_config.hands_free:
            greeting += f" Say '{self.anm_config.exit_phrase}' when you want me to stop."
        
        def process_query(text: str) -> str:
            """Process user query and return response."""
            result = self.query(text)
            return result.get("result", "I couldn't process that.")
        
        print("\n" + "=" * 60)
        print("🎙️  ANM HANDS-FREE MODE")
        print(f"   Parallel models: {self.anm_config.parallel_models}")
        print(f"   Voice model: {self.anm_config.voice_model}")
        print(f"   Exit phrase: \"{self.anm_config.exit_phrase}\"")
        print("=" * 60 + "\n")
        
        self._voice_io.conversation_loop(
            process_fn=process_query,
            greeting=greeting,
            goodbye="Goodbye! Stopping hands-free mode.",
            exit_words=[self.anm_config.exit_phrase, "stop", "quit", "exit"],
        )
    
    def stop(self) -> None:
        """Stop hands-free voice mode."""
        if self._voice_io:
            self._voice_io.stop()
            print("Stopping voice mode...")
    
    def cleanup(self) -> None:
        """
        Cleanup all resources.
        
        This method should be called when ANM is no longer needed
        to ensure proper cleanup of all resources.
        """
        # Stop voice if running
        if self._voice_io:
            self._voice_io.stop()
        
        # Cleanup thread pools
        try:
            from anm.core.thread_pool_manager import get_thread_pool_manager
            pool_manager = get_thread_pool_manager()
            pool_manager.shutdown_all()
        except Exception:
            pass
        
        # Cleanup inference engine
        try:
            from anm.system.inference import get_inference_engine
            engine = get_inference_engine()
            engine.unload_model()
        except Exception:
            pass
        
        # Flush logger
        if hasattr(self, '_logger') and self._logger:
            self._logger.flush()
        
        # Cleanup memory optimizer resources
        try:
            from anm.core.memory_optimizer import cleanup_resources
            cleanup_resources()
        except Exception:
            pass
    
    def __enter__(self) -> "ANM":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - cleanup resources."""
        self.cleanup()
    
    def voice_conversation(
        self,
        greeting: str = "Hello! I'm ANM. How can I help you?",
        goodbye: str = "Goodbye!",
    ) -> None:
        """
        Start a voice conversation with ANM.
        
        Uses:
        - Whisper for speech-to-text (offline)
        - Piper for text-to-speech (offline)
        
        Args:
            greeting: Opening greeting message
            goodbye: Closing message
        """
        if self._voice_io is None:
            if not self._init_voice():
                return
        
        def process_query(text: str) -> str:
            """Process user query and return response."""
            result = self.query(text)
            return result.get("result", "I couldn't process that.")
        
        self._voice_io.conversation_loop(
            process_fn=process_query,
            greeting=greeting,
            goodbye=goodbye,
        )
    
    def listen(self) -> str:
        """
        Listen for speech and return transcribed text.
        
        Returns:
            Transcribed text (empty string if failed)
        """
        if self._voice_io is None:
            if not self._init_voice():
                return ""
        
        return self._voice_io.listen()
    
    def speak(self, text: str) -> bool:
        """
        Speak text using text-to-speech.
        
        Args:
            text: Text to speak
        
        Returns:
            True if successful
        """
        if self._voice_io is None:
            if not self._init_voice():
                return False
        
        return self._voice_io.speak(text)
    
    def voice_query(self) -> Dict[str, Any]:
        """
        Listen for a voice query and process it.
        
        Returns:
            Query result with the spoken response
        """
        text = self.listen()
        if not text:
            return {"result": "I didn't catch that.", "success": False}
        
        result = self.query(text)
        response = result.get("result", "I couldn't process that.")
        
        self.speak(response)
        
        return result
    
    @property
    def voice_available(self) -> bool:
        """Check if voice I/O is available."""
        if self._voice_io:
            return self._voice_io.available
        return False


# ============================================================
#  LAZY IMPORT HELPER
# ============================================================

class _LazyImport:
    """
    Lazy import wrapper that defers module loading until first access.
    
    This reduces startup time and memory footprint by only importing
    modules when they're actually used.
    """
    def __init__(self, module_path: str, import_name: str = None, default=None):
        """
        Initialize lazy import.
        
        Args:
            module_path: Full module path (e.g., 'anm.core')
            import_name: Specific name to import (e.g., 'Router')
                         If None, imports the module itself
            default: Default value if import fails
        """
        self._module_path = module_path
        self._import_name = import_name
        self._default = default
        self._module = None
        self._value = None
        self._loaded = False
    
    def _load(self):
        """Load the module/attribute on first access."""
        if self._loaded:
            return
        
        try:
            module = __import__(self._module_path, fromlist=[self._import_name] if self._import_name else [])
            if self._import_name:
                self._value = getattr(module, self._import_name, self._default)
            else:
                self._value = module
        except (ImportError, AttributeError) as e:
            if self._default is not None:
                self._value = self._default
            else:
                raise ImportError(f"Failed to import {self._module_path}.{self._import_name or ''}: {e}")
        
        self._loaded = True
    
    def __getattr__(self, name):
        """Delegate attribute access to the loaded value."""
        self._load()
        return getattr(self._value, name)
    
    def __call__(self, *args, **kwargs):
        """Allow calling the lazy import if it's callable."""
        self._load()
        return self._value(*args, **kwargs)
    
    def __repr__(self):
        """String representation."""
        if self._loaded:
            return repr(self._value)
        return f"<LazyImport: {self._module_path}.{self._import_name or 'module'}>"


def _lazy_import(module_path: str, import_name: str = None, default=None):
    """Create a lazy import wrapper."""
    return _LazyImport(module_path, import_name, default)


# ============================================================
#  MODULE EXPORTS (LAZY LOADED)
# ============================================================

# Core Module (V0-OpenSource) - Lazy loaded
_CORE_AVAILABLE = None
def _get_core_available():
    """Lazy check for core module availability."""
    global _CORE_AVAILABLE
    if _CORE_AVAILABLE is None:
        try:
            __import__('anm.core')
            _CORE_AVAILABLE = True
        except ImportError:
            _CORE_AVAILABLE = False
    return _CORE_AVAILABLE

# Create a simple boolean that checks on first access
class _LazyBool:
    def __init__(self, getter):
        self._getter = getter
    def __bool__(self):
        return self._getter()
    def __repr__(self):
        return str(self._getter())

CORE_AVAILABLE = _LazyBool(_get_core_available)

# Lazy core imports
Domain = _lazy_import('anm.core.types', 'Domain')
QueryType = _lazy_import('anm.core.types', 'QueryType')
ResponseQuality = _lazy_import('anm.core.types', 'ResponseQuality')
ProcessingPhase = _lazy_import('anm.core.types', 'ProcessingPhase')
CoreANMResult = _lazy_import('anm.core.types', 'ANMResult')
QueryResult = _lazy_import('anm.core.types', 'QueryResult')
ReasoningStep = _lazy_import('anm.core.types', 'ReasoningStep')
DomainResult = _lazy_import('anm.core.types', 'DomainResult')
ANMComponent = _lazy_import('anm.core.types', 'ANMComponent')
TimedOperation = _lazy_import('anm.core.types', 'TimedOperation')
LRUCache = _lazy_import('anm.core.cache', 'LRUCache')
TTLCache = _lazy_import('anm.core.cache', 'TTLCache')
QueryCache = _lazy_import('anm.core.cache', 'QueryCache')
CacheStats = _lazy_import('anm.core.cache', 'CacheStats')
cached = _lazy_import('anm.core.cache', 'cached')
WorkerPool = _lazy_import('anm.core.pool', 'WorkerPool')
BatchProcessor = _lazy_import('anm.core.pool', 'BatchProcessor')
RateLimiter = _lazy_import('anm.core.pool', 'RateLimiter')
TaskResult = _lazy_import('anm.core.pool', 'TaskResult')
parallel_map = _lazy_import('anm.core.pool', 'parallel_map')
parallel_filter = _lazy_import('anm.core.pool', 'parallel_filter')
ComponentRegistry = _lazy_import('anm.core.sync', 'ComponentRegistry')
ComponentStatus = _lazy_import('anm.core.sync', 'ComponentStatus')
EventBus = _lazy_import('anm.core.sync', 'EventBus')
StateManager = _lazy_import('anm.core.sync', 'StateManager')
Pipeline = _lazy_import('anm.core.sync', 'Pipeline')
PipelineStage = _lazy_import('anm.core.sync', 'PipelineStage')
ANMSync = _lazy_import('anm.core.sync', 'ANMSync')
get_sync = _lazy_import('anm.core.sync', 'get_sync')

# Router & Executive - Lazy loaded
Router = _lazy_import('anm.router.router', 'Router')
Refiner = _lazy_import('anm.refiner.refiner', 'Refiner')
RefinerConfig = _lazy_import('anm.refiner.refiner', 'RefinerConfig')
RefinedAnswer = _lazy_import('anm.refiner.refiner', 'RefinedAnswer')
AnswerQuality = _lazy_import('anm.refiner.refiner', 'AnswerQuality')
AnswerStyle = _lazy_import('anm.refiner.refiner', 'AnswerStyle')
Verifier = _lazy_import('anm.verifier.verifier', 'Verifier')

# WoT V15 MAX - Lazy loaded
_WOT_V15_AVAILABLE = None
def _get_wot_available():
    """Lazy check for WoT V15 availability."""
    global _WOT_V15_AVAILABLE
    if _WOT_V15_AVAILABLE is None:
        try:
            __import__('anm.wot.wot_engine_v15')
            _WOT_V15_AVAILABLE = True
        except ImportError:
            _WOT_V15_AVAILABLE = False
    return _WOT_V15_AVAILABLE

WOT_V15_AVAILABLE = _LazyBool(_get_wot_available)

try:
    TrueWoTMax = _lazy_import('anm.wot.wot_engine_v15', 'TrueWoTMax')
    WoTConfig = _lazy_import('anm.wot.wot_engine_v15', 'WoTConfig')
    WoTMode = _lazy_import('anm.wot.wot_engine_v15', 'WoTMode')
    WoTResult = _lazy_import('anm.wot.wot_engine_v15', 'WoTResult')
    TrueWoT = TrueWoTMax  # Alias
except Exception:
    TrueWoTMax = _lazy_import('anm.wot.wot_engine', 'TrueWoT')
    TrueWoT = TrueWoTMax
    WoTConfig = None
    WoTMode = None
    WoTResult = None

# Specialists (V0-OpenSource) - Lazy loaded
BaseSpecialist = _lazy_import('anm.specialists.base', 'BaseSpecialist')
SpecialistConfig = _lazy_import('anm.specialists.base', 'SpecialistConfig')
SpecialistResult = _lazy_import('anm.specialists.base', 'SpecialistResult')
SpecialistDomain = _lazy_import('anm.specialists.base', 'SpecialistDomain')
GeneralLLM = _lazy_import('anm.specialists.general_llm', 'GeneralLLM')
MathLLM = _lazy_import('anm.specialists.math_llm', 'MathLLM')
PhysicsLLM = _lazy_import('anm.specialists.physics_llm', 'PhysicsLLM')
CodeLLM = _lazy_import('anm.specialists.code_llm', 'CodeLLM')
ChemistryLLM = _lazy_import('anm.specialists.chemistry_llm', 'ChemistryLLM')
BiologyLLM = _lazy_import('anm.specialists.biology_llm', 'BiologyLLM')
MemoryLLM = _lazy_import('anm.specialists.memory_llm', 'MemoryLLM')
ResearchLLM = _lazy_import('anm.specialists.research_llm', 'ResearchLLM')
FactsLLM = _lazy_import('anm.specialists.facts_llm', 'FactsLLM')
SoundLLM = _lazy_import('anm.specialists.sound_llm', 'SoundLLM')
SimulationLLM = _lazy_import('anm.specialists.simulation_llm', 'SimulationLLM', default=None)
ImageLLM = _lazy_import('anm.specialists.image_llm', 'ImageLLM', default=None)
InternetLLM = _lazy_import('anm.specialists.internet_llm', 'InternetLLM', default=None)
WebSearcher = _lazy_import('anm.specialists.internet_llm', 'WebSearcher', default=None)

_INTERNET_LLM_AVAILABLE = None
def _get_internet_available():
    """Lazy check for InternetLLM availability."""
    global _INTERNET_LLM_AVAILABLE
    if _INTERNET_LLM_AVAILABLE is None:
        try:
            __import__('anm.specialists.internet_llm')
            _INTERNET_LLM_AVAILABLE = True
        except ImportError:
            _INTERNET_LLM_AVAILABLE = False
    return _INTERNET_LLM_AVAILABLE

INTERNET_LLM_AVAILABLE = _LazyBool(_get_internet_available)

# Memory (V2 Epistemic Humility) - Lazy loaded
DiaryMemory = _lazy_import('anm.memory.diary_memory', 'DiaryMemory')
MemoryHub = _lazy_import('anm.memory.memory_hub', 'MemoryHub')
MemoryContext = _lazy_import('anm.memory.memory_hub', 'MemoryContext')
BehavioralInsight = _lazy_import('anm.memory.memory_hub', 'BehavioralInsight')
ObservationType = _lazy_import('anm.memory.memory_hub', 'ObservationType')
LearningEngine = _lazy_import('anm.memory.learning_engine', 'LearningEngine')
EpistemicStatus = _lazy_import('anm.memory.memory_hub', 'EpistemicStatus')

# Learning - Lazy loaded
LFMModule = _lazy_import('anm.lfm.lfm_module', 'LFMModule')
PointGame = _lazy_import('anm.learning.point_game', 'PointGame')

# MetaCognition (V2 Enhanced Self-Awareness) - Lazy loaded
_METACOGNITION_AVAILABLE = None
def _get_metacognition_available():
    """Lazy check for MetaCognition availability."""
    global _METACOGNITION_AVAILABLE
    if _METACOGNITION_AVAILABLE is None:
        try:
            __import__('anm.metacognition.metacognition')
            _METACOGNITION_AVAILABLE = True
        except ImportError:
            _METACOGNITION_AVAILABLE = False
    return _METACOGNITION_AVAILABLE

METACOGNITION_AVAILABLE = _LazyBool(_get_metacognition_available)

MetaCognition = _lazy_import('anm.metacognition.metacognition', 'MetaCognition', default=None)
MetaCognitiveAssessment = _lazy_import('anm.metacognition.metacognition', 'MetaCognitiveAssessment', default=None)
MetaCognitiveReflection = _lazy_import('anm.metacognition.metacognition', 'MetaCognitiveReflection', default=None)
ConfidenceCalibrator = _lazy_import('anm.metacognition.confidence', 'ConfidenceCalibrator', default=None)
ConfidenceLevel = _lazy_import('anm.metacognition.confidence', 'ConfidenceLevel', default=None)
UncertaintyQuantifier = _lazy_import('anm.metacognition.uncertainty', 'UncertaintyQuantifier', default=None)
UncertaintyType = _lazy_import('anm.metacognition.uncertainty', 'UncertaintyType', default=None)
CognitiveLoadTracker = _lazy_import('anm.metacognition.cognitive_load', 'CognitiveLoadTracker', default=None)
LoadLevel = _lazy_import('anm.metacognition.cognitive_load', 'LoadLevel', default=None)
ReasoningQualityChecker = _lazy_import('anm.metacognition.reasoning_checker', 'ReasoningQualityChecker', default=None)
KnowledgeBoundaryDetector = _lazy_import('anm.metacognition.knowledge_boundary', 'KnowledgeBoundaryDetector', default=None)
KnowledgeStatus = _lazy_import('anm.metacognition.knowledge_boundary', 'KnowledgeStatus', default=None)
BiasDetector = _lazy_import('anm.metacognition.bias_detector', 'BiasDetector', default=None)
BiasType = _lazy_import('anm.metacognition.bias_detector', 'BiasType', default=None)
MetaCognitiveJournal = _lazy_import('anm.metacognition.journal', 'MetaCognitiveJournal', default=None)
StrategyEvaluator = _lazy_import('anm.metacognition.strategy_evaluator', 'StrategyEvaluator', default=None)

# Expansion (V2) - Lazy loaded
ExpansionEngineV2 = _lazy_import('anm.expansion.expansion_engine_v2', 'ExpansionEngineV2')
ExpansionConfig = _lazy_import('anm.expansion.expansion_engine_v2', 'ExpansionConfig')
NoveltyDetectorV2 = _lazy_import('anm.expansion.core.novelty_detector', 'NoveltyDetectorV2')
VotingSystemV2 = _lazy_import('anm.expansion.core.voting_system', 'VotingSystemV2')
MultiSourceDiscovery = _lazy_import('anm.expansion.discovery.multi_source', 'MultiSourceDiscovery')
CodeWriterV2 = _lazy_import('anm.expansion.code.writer_v2', 'CodeWriterV2')
LoRATrainer = _lazy_import('anm.expansion.training.lora_trainer', 'LoRATrainer')

# System Module (Cross-Platform Support) - Lazy loaded
_SYSTEM_MODULE_AVAILABLE = None
def _get_system_available():
    """Lazy check for System module availability."""
    global _SYSTEM_MODULE_AVAILABLE
    if _SYSTEM_MODULE_AVAILABLE is None:
        try:
            __import__('anm.system.platform')
            _SYSTEM_MODULE_AVAILABLE = True
        except ImportError:
            _SYSTEM_MODULE_AVAILABLE = False
    return _SYSTEM_MODULE_AVAILABLE

SYSTEM_MODULE_AVAILABLE = _LazyBool(_get_system_available)

Platform = _lazy_import('anm.system.platform', 'Platform', default=None)
PlatformInfo = _lazy_import('anm.system.platform', 'PlatformInfo', default=None)
get_platform = _lazy_import('anm.system.platform', 'get_platform', default=None)
get_platform_info = _lazy_import('anm.system.platform', 'get_platform_info', default=None)
is_windows = _lazy_import('anm.system.platform', 'is_windows', default=None)
is_macos = _lazy_import('anm.system.platform', 'is_macos', default=None)
is_linux = _lazy_import('anm.system.platform', 'is_linux', default=None)
HardwareInfo = _lazy_import('anm.system.hardware', 'HardwareInfo', default=None)
CPUInfo = _lazy_import('anm.system.hardware', 'CPUInfo', default=None)
GPUInfo = _lazy_import('anm.system.hardware', 'GPUInfo', default=None)
MemoryInfo = _lazy_import('anm.system.hardware', 'MemoryInfo', default=None)
get_hardware_info = _lazy_import('anm.system.hardware', 'get_hardware_info', default=None)
get_cpu_info = _lazy_import('anm.system.hardware', 'get_cpu_info', default=None)
get_gpu_info = _lazy_import('anm.system.hardware', 'get_gpu_info', default=None)
get_memory_info = _lazy_import('anm.system.hardware', 'get_memory_info', default=None)
can_run_local_llm = _lazy_import('anm.system.hardware', 'can_run_local_llm', default=None)
ANMPaths = _lazy_import('anm.system.paths', 'ANMPaths', default=None)
get_anm_paths = _lazy_import('anm.system.paths', 'get_anm_paths', default=None)
ensure_directories = _lazy_import('anm.system.paths', 'ensure_directories', default=None)
DependencyManager = _lazy_import('anm.system.dependencies', 'DependencyManager', default=None)
Dependency = _lazy_import('anm.system.dependencies', 'Dependency', default=None)
DependencyStatus = _lazy_import('anm.system.dependencies', 'DependencyStatus', default=None)
check_dependencies = _lazy_import('anm.system.dependencies', 'check_dependencies', default=None)
install_dependency = _lazy_import('anm.system.dependencies', 'install_dependency', default=None)
auto_setup = _lazy_import('anm.system.dependencies', 'auto_setup', default=None)

# Simulation (optional - may have GPU dependencies) - Lazy loaded
_SIMULATION_AVAILABLE = None
def _get_simulation_available():
    """Lazy check for Simulation availability."""
    global _SIMULATION_AVAILABLE
    if _SIMULATION_AVAILABLE is None:
        try:
            __import__('anm.sim.engine')
            _SIMULATION_AVAILABLE = True
        except ImportError:
            _SIMULATION_AVAILABLE = False
    return _SIMULATION_AVAILABLE

SIMULATION_AVAILABLE = _LazyBool(_get_simulation_available)

SimulationEngine = _lazy_import('anm.sim.engine', 'SimulationEngine', default=None)
SimulationEngine2D = _lazy_import('anm.sim.engine_2d', 'SimulationEngine2D', default=None)
SimulationRequest = _lazy_import('anm.sim.types', 'SimulationRequest', default=None)
SimulationResult = _lazy_import('anm.sim.types', 'SimulationResult', default=None)

# Utils - Lazy loaded
ANMLogger = _lazy_import('anm.utils.logger', 'ANMLogger')

# Sanity Check - Lazy loaded
SanityChecker = _lazy_import('anm.sanity.sanity_checker', 'SanityChecker')
SanityResult = _lazy_import('anm.sanity.sanity_checker', 'SanityResult')
AutoFixer = _lazy_import('anm.sanity.auto_fixer', 'AutoFixer')

# Voice I/O (Offline STT/TTS) - Lazy loaded
_VOICE_AVAILABLE = None
def _get_voice_available():
    """Lazy check for Voice module availability."""
    global _VOICE_AVAILABLE
    if _VOICE_AVAILABLE is None:
        try:
            __import__('anm.voice.voice_io')
            _VOICE_AVAILABLE = True
        except ImportError:
            _VOICE_AVAILABLE = False
    return _VOICE_AVAILABLE

VOICE_AVAILABLE = _LazyBool(_get_voice_available)

VoiceIO = _lazy_import('anm.voice.voice_io', 'VoiceIO', default=None)
VoiceConfig = _lazy_import('anm.voice.voice_io', 'VoiceConfig', default=None)
WhisperSTT = _lazy_import('anm.voice.stt', 'WhisperSTT', default=None)
STTConfig = _lazy_import('anm.voice.stt', 'STTConfig', default=None)
PiperTTS = _lazy_import('anm.voice.tts', 'PiperTTS', default=None)
TTSConfig = _lazy_import('anm.voice.tts', 'TTSConfig', default=None)

__all__ = [
    # Main interface
    "ANM",
    "ANMConfig",
    "__version__",
    "__codename__",
    
    # Core Module (V0-OpenSource)
    "CORE_AVAILABLE",
    "Domain",
    "QueryType",
    "ResponseQuality",
    "ProcessingPhase",
    "ANMResult",
    "QueryResult",
    "ReasoningStep",
    "DomainResult",
    "ANMComponent",
    "TimedOperation",
    "LRUCache",
    "TTLCache",
    "QueryCache",
    "CacheStats",
    "cached",
    "WorkerPool",
    "BatchProcessor",
    "RateLimiter",
    "TaskResult",
    "parallel_map",
    "parallel_filter",
    "ComponentRegistry",
    "EventBus",
    "StateManager",
    "Pipeline",
    "PipelineStage",
    "ANMSync",
    "get_sync",
    "ComponentStatus",
    
    # Router & Executive
    "Router",
    "TrueWoT",
    "Refiner",
    "RefinerConfig",
    "RefinedAnswer",
    "AnswerQuality",
    "AnswerStyle",
    "Verifier",
    
    # Specialists (V0-OpenSource)
    "BaseSpecialist",
    "SpecialistConfig",
    "SpecialistResult",
    "SpecialistDomain",
    "GeneralLLM",
    "MathLLM",
    "PhysicsLLM",
    "CodeLLM",
    "ChemistryLLM",
    "BiologyLLM",
    "MemoryLLM",
    "ResearchLLM",
    "FactsLLM",
    "SoundLLM",
    "SimulationLLM",
    "ImageLLM",
    "InternetLLM",
    "WebSearcher",
    "INTERNET_LLM_AVAILABLE",
    
    # Memory (V2 Epistemic Humility)
    "DiaryMemory",
    "MemoryHub",
    "MemoryContext",
    "BehavioralInsight",
    "ObservationType",
    "LearningEngine",
    "EpistemicStatus",
    
    # Learning
    "LFMModule",
    "PointGame",
    
    # System Module
    "Platform",
    "PlatformInfo",
    "get_platform",
    "get_platform_info",
    "is_windows",
    "is_macos",
    "is_linux",
    "HardwareInfo",
    "CPUInfo",
    "GPUInfo",
    "MemoryInfo",
    "get_hardware_info",
    "get_cpu_info",
    "get_gpu_info",
    "get_memory_info",
    "can_run_local_llm",
    "ANMPaths",
    "get_anm_paths",
    "ensure_directories",
    "DependencyManager",
    "check_dependencies",
    "auto_setup",
    "SYSTEM_MODULE_AVAILABLE",
    
    # Expansion
    "ExpansionEngineV2",
    "ExpansionConfig",
    "NoveltyDetectorV2",
    "VotingSystemV2",
    "MultiSourceDiscovery",
    "CodeWriterV2",
    "LoRATrainer",
    
    # Simulation
    "SimulationEngine",
    "SimulationEngine2D",
    "SimulationRequest",
    "SimulationResult",
    "SIMULATION_AVAILABLE",
    
    # Utils
    "ANMLogger",
    
    # Sanity Check
    "SanityChecker",
    "SanityResult",
    "AutoFixer",
    
    # Voice I/O (Offline)
    "VoiceIO",
    "VoiceConfig",
    "WhisperSTT",
    "STTConfig",
    "PiperTTS",
    "TTSConfig",
    "VOICE_AVAILABLE",
    
    # MetaCognition (Self-Awareness)
    "MetaCognition",
    "MetaCognitiveAssessment",
    "MetaCognitiveReflection",
    "ConfidenceCalibrator",
    "ConfidenceLevel",
    "UncertaintyQuantifier",
    "UncertaintyType",
    "CognitiveLoadTracker",
    "LoadLevel",
    "ReasoningQualityChecker",
    "KnowledgeBoundaryDetector",
    "KnowledgeStatus",
    "BiasDetector",
    "BiasType",
    "MetaCognitiveJournal",
    "StrategyEvaluator",
    "METACOGNITION_AVAILABLE",
    
    # WoT V15 MAX
    "TrueWoTMax",
    "TrueWoT",
    "WoTConfig",
    "WoTMode",
    "WoTResult",
    "WOT_V15_AVAILABLE",
]


# ============================================================
#  QUICK SANITY CHECK FUNCTION
# ============================================================

def run_sanity_check(verbose: bool = True, auto_fix: bool = False) -> SanityResult:
    """
    Run ANM sanity check without creating an ANM instance.
    
    Args:
        verbose: Print progress
        auto_fix: Attempt to auto-fix issues
    
    Returns:
        SanityResult with all issues found
    """
    checker = SanityChecker(verbose=verbose)
    result = checker.run_full_check()
    
    if not result.passed and auto_fix and result.auto_fixable_issues:
        fixer = AutoFixer(verbose=verbose)
        fixer.fix_all_issues(result.auto_fixable_issues)
        # Re-run to get updated result
        result = checker.run_full_check()
    
    return result
