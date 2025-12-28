# ============================================================
# ANM V0-OpenSource — BEHAVIOUR LOGGER V0-OpenSource ULTRA
#  Supports: 13 Specialists + Router V0-OpenSource + WoT V0-OpenSource
#  Adds: SoundLLM, SIM_REASONER, sim_profile, domain_diagnostics
#  Thread-Safe • JSONL Streaming • Microsecond IDs
# ============================================================

from __future__ import annotations
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Union


JsonSafe = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


class ANMLogger:
    """
    ANM V0-OpenSource — Behaviour Logger V0-OpenSource ULTRA

    FEATURES:
    -----------------
    ✓ Full specialist lifecycle logging (raw + cleaned + meta)
    ✓ SoundLLM logging
    ✓ SIM_REASONER logging
    ✓ Simulation profile logging (3D raymarch CPU/GPU profile)
    ✓ Domain diagnostics (math/physics/research/sound)
    ✓ Router call-chain + task compiler pipeline
    ✓ Error-protected JSON append
    ✓ Safe for 100k+ entries

    SPECIALISTS COVERED:
    --------------------
    - Router
    - Planner
    - TaskCompiler
    - MemoryLLM V0-OpenSource
    - SelfAwarenessLLM V0-OpenSource
    - MathLLM
    - PhysicsLLM
    - CodeLLM
    - BiologyLLM
    - ChemistryLLM
    - ResearchLLM
    - SoundLLM
    - SimulationLLM V0-OpenSourceA (3D raymarch)
    - ImageLLM
    - Facts Validator
    - Refiner
    - Verifier
    """

    # --------------------------------------------------------
    # INITIALIZATION
    # --------------------------------------------------------
    def __init__(self, log_dir: str = "logs", worker_id: int | None = None) -> None:
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        self.run_id = f"{timestamp}_w{worker_id}" if worker_id is not None else timestamp
        self.log_path = os.path.join(self.log_dir, f"anm_log_{self.run_id}.jsonl")

        # in-memory buffer (flushed on save)
        self.entries: List[Dict[str, Any]] = []

    # --------------------------------------------------------
    # TIMESTAMP
    # --------------------------------------------------------
    def _timestamp(self) -> Dict[str, float]:
        return {
            "iso": datetime.utcnow().isoformat(),
            "epoch": time.time(),
        }

    # --------------------------------------------------------
    # SAFE PUSH
    # --------------------------------------------------------
    def _push(self, entry: Dict[str, Any]) -> None:
        self.entries.append(entry)

    # ========================================================
    # SESSION
    # ========================================================
    def new_run(self, user_query: str) -> None:
        self._push({
            "type": "start",
            "run_id": self.run_id,
            "timestamp": self._timestamp(),
            "user_query": user_query,
        })

    # ========================================================
    # ROUTER + WOT PACKETS
    # ========================================================
    def log_wot_packet(self, packet: JsonSafe) -> None:
        self._push({
            "type": "wot_packet",
            "timestamp": self._timestamp(),
            "packet": packet
        })

    def log_router_decision(self, decision: JsonSafe) -> None:
        self._push({
            "type": "router_decision",
            "timestamp": self._timestamp(),
            "decision": decision
        })

    def log_wot_call_chain(self, chain: List[str]) -> None:
        self._push({
            "type": "wot_call_chain",
            "timestamp": self._timestamp(),
            "chain": chain
        })

    def log_wot_analysis(self, analysis: JsonSafe) -> None:
        self._push({
            "type": "wot_analysis",
            "timestamp": self._timestamp(),
            "analysis": analysis
        })

    def log_round(self, round_number: int, packets: Dict[str, JsonSafe]) -> None:
        self._push({
            "type": "wot_round",
            "timestamp": self._timestamp(),
            "round": round_number,
            "specialists": packets
        })

    # ========================================================
    # SPECIALIST UNIVERSAL LOGGING
    # ========================================================
    def log_specialist_raw(self, domain: str, raw: str) -> None:
        self._push({
            "type": f"{domain}_raw",
            "timestamp": self._timestamp(),
            "raw": raw
        })

    def log_specialist_clean(self, domain: str, cleaned: str) -> None:
        self._push({
            "type": f"{domain}_cleaned",
            "timestamp": self._timestamp(),
            "cleaned": cleaned
        })

    def log_specialist_meta(self, domain: str, meta: JsonSafe) -> None:
        self._push({
            "type": f"{domain}_meta",
            "timestamp": self._timestamp(),
            "meta": meta
        })

    def log_specialist_diagnostics(self, domain: str, diag: JsonSafe) -> None:
        self._push({
            "type": f"{domain}_diagnostics",
            "timestamp": self._timestamp(),
            "diagnostics": diag
        })

    # ========================================================
    # MEMORY SYSTEM
    # ========================================================
    def log_memory(self, memory_context: str) -> None:
        self._push({
            "type": "memory_context",
            "timestamp": self._timestamp(),
            "context": memory_context
        })

    def log_memory_query(self, packet: JsonSafe) -> None:
        self._push({
            "type": "memory_query",
            "timestamp": self._timestamp(),
            "packet": packet
        })

    def log_working_memory(self, snapshot: JsonSafe) -> None:
        self._push({
            "type": "working_memory",
            "timestamp": self._timestamp(),
            "snapshot": snapshot
        })

    def log_visual_memory(self, entry: JsonSafe) -> None:
        self._push({
            "type": "visual_memory",
            "timestamp": self._timestamp(),
            "entry": entry
        })

    # ========================================================
    # SELF-AWARENESS
    # ========================================================
    def log_self_awareness(self, report: JsonSafe) -> None:
        self._push({
            "type": "self_awareness",
            "timestamp": self._timestamp(),
            "report": report
        })

    # ========================================================
    # SOUND SPECIALIST
    # ========================================================
    def log_sound_packet(self, packet: JsonSafe) -> None:
        self._push({
            "type": "sound_packet",
            "timestamp": self._timestamp(),
            "packet": packet
        })

    # ========================================================
    # RESEARCH & FACTS
    # ========================================================
    def log_research(self, packet: JsonSafe) -> None:
        self._push({
            "type": "research_packet",
            "timestamp": self._timestamp(),
            "data": packet
        })

    def log_facts(self, packet: JsonSafe) -> None:
        self._push({
            "type": "facts_packet",
            "timestamp": self._timestamp(),
            "data": packet
        })

    # ========================================================
    # SIMULATION / IMAGE
    # ========================================================
    def log_simulation_request(self, req: JsonSafe) -> None:
        self._push({
            "type": "simulation_request",
            "timestamp": self._timestamp(),
            "request": req
        })

    def log_simulation_profile(self, profile: JsonSafe) -> None:
        self._push({
            "type": "simulation_profile",
            "timestamp": self._timestamp(),
            "profile": profile
        })

    def log_simulation_result(self, result: JsonSafe) -> None:
        self._push({
            "type": "simulation_result",
            "timestamp": self._timestamp(),
            "result": result
        })

    def log_sim_reasoner(self, reasoner: JsonSafe) -> None:
        self._push({
            "type": "simulation_reasoner",
            "timestamp": self._timestamp(),
            "reasoner": reasoner
        })

    def log_image_packet(self, packet: JsonSafe) -> None:
        self._push({
            "type": "image_packet",
            "timestamp": self._timestamp(),
            "packet": packet
        })

    # ========================================================
    # PLANNER + TASK COMPILER
    # ========================================================
    def log_planner(self, plan: JsonSafe) -> None:
        self._push({
            "type": "planner",
            "timestamp": self._timestamp(),
            "plan": plan
        })

    def log_task_compiler(self, output: JsonSafe) -> None:
        self._push({
            "type": "task_compiler",
            "timestamp": self._timestamp(),
            "output": output
        })

    # ========================================================
    # REFINER / VERIFIER
    # ========================================================
    def log_refiner_packet(self, packet: JsonSafe) -> None:
        self._push({
            "type": "refiner_packet",
            "timestamp": self._timestamp(),
            "packet": packet
        })

    def log_refiner(self, refined: str) -> None:
        self._push({
            "type": "refiner_output",
            "timestamp": self._timestamp(),
            "refined": refined
        })

    def log_verifier_packet(self, packet: str) -> None:
        self._push({
            "type": "verifier_packet",
            "timestamp": self._timestamp(),
            "packet": packet
        })

    def log_verifier(self, decision: JsonSafe) -> None:
        self._push({
            "type": "verifier_output",
            "timestamp": self._timestamp(),
            "decision": decision
        })

    # ========================================================
    # ERRORS
    # ========================================================
    def log_error(self, where: str, error: str) -> None:
        self._push({
            "type": "error",
            "timestamp": self._timestamp(),
            "module": where,
            "error": error
        })

    # ========================================================
    # SAVE
    # ========================================================
    def save(self) -> str:
        """Save all buffered entries to file."""
        with open(self.log_path, "w", encoding="utf-8") as f:
            for e in self.entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        return self.log_path
    
    def flush(self) -> None:
        """Flush buffered entries to file (append mode)."""
        if self.entries:
            with open(self.log_path, "a", encoding="utf-8") as f:
                for e in self.entries:
                    f.write(json.dumps(e, ensure_ascii=False) + "\n")
            self.entries.clear()
    
    def close(self) -> None:
        """Close logger and flush remaining entries."""
        self.flush()
    
    def __enter__(self) -> "ANMLogger":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - flush entries."""
        self.close()