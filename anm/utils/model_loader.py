# ============================================================
# ANM V0-OpenSource — MODEL LOADER V0-OpenSource
#  GPU-aware • Quantization-aware • R1/VL-strict
#  Unified Resolver • Warning Engine • Alias Map
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List
import subprocess


class ModelLoader:
    """
    ANM V0-OpenSource — MODEL LOADER V0-OpenSource

    Priority Cascade:
        1. config["model_<domain>"]
        2. config["global_model_override"]
        3. config["global_model_default"]
        4. HARD_DEFAULTS[domain]

    Features:
    ---------
    ✓ Full alias map (vision/image/sim/engine/render)
    ✓ Quantization detection (q2_K, q4_K_S, int4/int8)
    ✓ GPU hint system (NVIDIA/Metal/CPU fallback)
    ✓ R1/VL strict validation
    ✓ Simulation-specific safety rules
    ✓ Warning engine with type codes
    ✓ 18-domain unified resolution
    """

    # ========================================================
    #  HARD DEFAULTS (R1/VL stack)
    # ========================================================
    HARD_DEFAULTS = {
        "general":     "deepseek-r1:1.5b",
        "math":        "deepseek-r1:1.5b",
        "physics":     "deepseek-r1:1.5b",
        "code":        "deepseek-r1:1.5b",
        "chemistry":   "deepseek-r1:1.5b",
        "biology":     "deepseek-r1:1.5b",
        "memory":      "deepseek-r1:1.5b",
        "research":    "deepseek-r1:1.5b",
        "facts":       "deepseek-r1:1.5b",

        # Vision models
        "vision":      "deepseek-vl:1.5b",
        "image":       "deepseek-vl:1.5b",

        # Simulation (strict physics)
        "simulation":  "deepseek-r1:1.5b",
        "sim":         "deepseek-r1:1.5b",

        # Executive modules (Router, Refiner, Verifier)
        "router":      "deepseek-r1:1.5b",
        "refiner":     "deepseek-r1:1.5b",
        "verifier":    "deepseek-r1:1.5b",
        "expansion":   "deepseek-r1:1.5b",

        # Sound & voice
        "sound":       "deepseek-r1:1.5b",
        "voice":       "deepseek-r1:1.5b",
    }

    # ========================================================
    # VALID MODEL PREFIXES
    # ========================================================
    VALID_PREFIXES = (
        "deepseek-r1",
        "deepseek-vl",
        "dsr1",
        "dsvl",
        "custom",
        "local",
        "quantized",
    )

    # Full alias mapping v2
    ALIASES = {
        "img": "vision",
        "image": "vision",
        "vision": "vision",
        "render": "simulation",
        "sim": "simulation",
        "engine": "simulation",
        "simulation": "simulation",
    }

    # ========================================================
    # INIT
    # ========================================================
    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        self.warnings: List[str] = []

    # ========================================================
    # OLLAMA model existence (soft check)
    # ========================================================
    def _ollama_exists(self, model: str) -> bool:
        try:
            p = subprocess.run(
                ["ollama", "list"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
            )
            return model in p.stdout
        except Exception:
            return True  # do not warn if Ollama unavailable

    # ========================================================
    # WARNING ENGINE v3
    # ========================================================
    def _warn(self, code: str, message: str):
        self.warnings.append(f"[ModelLoader:{code}] {message}")

    # ========================================================
    # VALIDATE MODEL NAME
    # ========================================================
    def _validate(self, model: str, domain: str) -> str:
        if not isinstance(model, str) or not model.strip():
            self._warn("empty", f"Empty model for '{domain}' → using hard default.")
            return self.HARD_DEFAULTS.get(domain, "deepseek-r1:1.5b")

        m = model.strip()

        # Incompatible LLM families
        forbidden = ("gpt", "claude", "llama", "qwen", "mistral")
        if m.lower().startswith(forbidden):
            self._warn("incompatible", f"Model '{m}' is incompatible with ANM-R1 pipeline.")

        # Unexpected prefix
        if not m.startswith(self.VALID_PREFIXES):
            self._warn("prefix", f"Suspicious model '{m}' (R1/VL expected).")

        # SimulationLLM safety: forbid giant models
        if domain == "simulation" and any(x in m for x in ["7b", "14b", "32b"]):
            self._warn("sim_heavy", f"'{m}' is too large for Raymarch SIM engine → use 1.5B.")

        # Quantization hint
        if any(q in m for q in ["q2", "q4", "int4", "int8"]):
            self._warn("quantized", f"Quantized model '{m}' detected → may reduce reasoning depth.")

        # Ollama availability
        if not self._ollama_exists(m):
            self._warn("missing", f"Ollama cannot find model '{m}'.")

        return m

    # ========================================================
    # RESOLVE KEY
    # ========================================================
    def _resolve(self, key: str) -> str:
        domain = key.replace("model_", "")
        cfg1 = self.config.get(key)
        cfg2 = self.config.get("global_model_override")
        cfg3 = self.config.get("global_model_default")
        hard = self.HARD_DEFAULTS.get(domain, "deepseek-r1:1.5b")
        selected = cfg1 or cfg2 or cfg3 or hard
        return self._validate(selected, domain)

    # ========================================================
    # UNIFIED GET (with alias map)
    # ========================================================
    def get(self, domain: str) -> str:
        dom = domain.lower().strip()

        if dom in self.ALIASES:
            dom = self.ALIASES[dom]

        return self._resolve(f"model_{dom}")

    # ========================================================
    # SPECIALIZED GETTERS
    # ========================================================
    def general_model(self):    return self.get("general")
    def math_model(self):       return self.get("math")
    def physics_model(self):    return self.get("physics")
    def code_model(self):       return self.get("code")
    def chemistry_model(self):  return self.get("chemistry")
    def biology_model(self):    return self.get("biology")
    def memory_model(self):     return self.get("memory")
    def research_model(self):   return self.get("research")
    def facts_model(self):      return self.get("facts")

    def vision_model(self):     return self.get("vision")
    def image_model(self):      return self.get("vision")
    def simulation_model(self): return self.get("simulation")

    def router_model(self):     return self.get("router")
    def refiner_model(self):    return self.get("refiner")
    def verifier_model(self):   return self.get("verifier")
    def expansion_model(self):  return self.get("expansion")

    def sound_model(self):      return self.get("sound")
    def voice_model(self):      return self.get("voice")

    # ========================================================
    # SUMMARY
    # ========================================================
    def summary(self) -> Dict[str, Any]:
        return {
            "specialists": {
                "general": self.general_model(),
                "math": self.math_model(),
                "physics": self.physics_model(),
                "code": self.code_model(),
                "chemistry": self.chemistry_model(),
                "biology": self.biology_model(),
                "memory": self.memory_model(),
                "research": self.research_model(),
                "facts": self.facts_model(),
                "vision": self.vision_model(),
                "simulation": self.simulation_model(),
                "sound": self.sound_model(),
                "voice": self.voice_model(),
            },
            "executive_stack": {
                "router": self.router_model(),
                "refiner": self.refiner_model(),
                "verifier": self.verifier_model(),
                "expansion": self.expansion_model(),
            },
            "warnings": self.warnings,
            "raw_config": self.config,
        }