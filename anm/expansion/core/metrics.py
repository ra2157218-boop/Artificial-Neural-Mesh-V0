# ============================================================
# ANM V0-OpenSource — EXPANSION METRICS (MAXIMUM LEVEL)
#  Real-time Monitoring • Performance Tracking • Analytics
#  Dashboards • Alerts • Historical Analysis
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import os
import time
from collections import defaultdict


@dataclass
class StageMetrics:
    """Metrics for a single pipeline stage."""
    stage_name: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    input_size: int = 0
    output_size: int = 0
    resource_usage: Dict[str, float] = field(default_factory=dict)
    
    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0


@dataclass
class ExpansionRun:
    """Complete metrics for an expansion run."""
    run_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    domain: str = ""
    query: str = ""
    stages: List[StageMetrics] = field(default_factory=list)
    success: bool = False
    error: Optional[str] = None
    human_approval_requested: bool = False
    
    @property
    def total_duration_ms(self) -> float:
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return sum(s.duration_ms for s in self.stages)


class ExpansionMetrics:
    """
    MAXIMUM LEVEL Metrics System.
    
    Features:
    - Real-time stage tracking
    - Performance monitoring
    - Resource usage tracking
    - Historical analytics
    - Success/failure rates
    - Bottleneck identification
    - Alert generation
    """
    
    def __init__(self, storage_dir: str = ".anm_metrics"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        self.current_run: Optional[ExpansionRun] = None
        self.run_history: List[ExpansionRun] = []
        self.stage_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_runs": 0,
            "successful_runs": 0,
            "total_duration_ms": 0.0,
            "avg_duration_ms": 0.0,
            "min_duration_ms": float("inf"),
            "max_duration_ms": 0.0,
            "errors": [],
        })
        
        self._load_history()
    
    def start_run(self, run_id: str, domain: str, query: str) -> None:
        """Start tracking a new expansion run."""
        self.current_run = ExpansionRun(
            run_id=run_id,
            started_at=datetime.now(),
            domain=domain,
            query=query,
        )
    
    def start_stage(self, stage_name: str, input_size: int = 0) -> StageMetrics:
        """Start tracking a pipeline stage."""
        stage = StageMetrics(
            stage_name=stage_name,
            start_time=time.time(),
            input_size=input_size,
        )
        
        if self.current_run:
            self.current_run.stages.append(stage)
        
        return stage
    
    def end_stage(
        self,
        stage: StageMetrics,
        success: bool,
        output_size: int = 0,
        error: Optional[str] = None,
        resource_usage: Optional[Dict[str, float]] = None,
    ) -> None:
        """End tracking a pipeline stage."""
        stage.end_time = time.time()
        stage.success = success
        stage.output_size = output_size
        stage.error = error
        stage.resource_usage = resource_usage or {}
        
        # Update stage stats
        stats = self.stage_stats[stage.stage_name]
        stats["total_runs"] += 1
        if success:
            stats["successful_runs"] += 1
        stats["total_duration_ms"] += stage.duration_ms
        stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["total_runs"]
        stats["min_duration_ms"] = min(stats["min_duration_ms"], stage.duration_ms)
        stats["max_duration_ms"] = max(stats["max_duration_ms"], stage.duration_ms)
        if error:
            stats["errors"].append(error)
    
    def end_run(self, success: bool, error: Optional[str] = None) -> ExpansionRun:
        """End tracking the current expansion run."""
        if not self.current_run:
            raise RuntimeError("No active run to end")
        
        self.current_run.completed_at = datetime.now()
        self.current_run.success = success
        self.current_run.error = error
        
        # Add to history
        self.run_history.append(self.current_run)
        
        # Persist
        self._save_run(self.current_run)
        
        run = self.current_run
        self.current_run = None
        
        return run
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        total_runs = len(self.run_history)
        successful_runs = sum(1 for r in self.run_history if r.success)
        
        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate": successful_runs / max(total_runs, 1),
            "avg_duration_ms": sum(r.total_duration_ms for r in self.run_history) / max(total_runs, 1),
            "domains_expanded": list(set(r.domain for r in self.run_history if r.success)),
            "stage_stats": dict(self.stage_stats),
            "recent_errors": self._get_recent_errors(),
            "bottlenecks": self._identify_bottlenecks(),
        }
    
    def get_stage_performance(self, stage_name: str) -> Dict[str, Any]:
        """Get performance metrics for a specific stage."""
        return dict(self.stage_stats.get(stage_name, {}))
    
    def get_run_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent run history."""
        return [
            {
                "run_id": r.run_id,
                "domain": r.domain,
                "success": r.success,
                "duration_ms": r.total_duration_ms,
                "started_at": r.started_at.isoformat(),
                "stages": len(r.stages),
            }
            for r in self.run_history[-limit:]
        ]
    
    def _get_recent_errors(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent errors."""
        errors = []
        for run in reversed(self.run_history):
            if run.error:
                errors.append({
                    "run_id": run.run_id,
                    "domain": run.domain,
                    "error": run.error,
                    "time": run.started_at.isoformat(),
                })
            for stage in run.stages:
                if stage.error:
                    errors.append({
                        "run_id": run.run_id,
                        "stage": stage.stage_name,
                        "error": stage.error,
                    })
            if len(errors) >= limit:
                break
        return errors[:limit]
    
    def _identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        for stage_name, stats in self.stage_stats.items():
            if stats["total_runs"] < 3:
                continue
            
            # Check for slow stages
            if stats["avg_duration_ms"] > 10000:  # > 10 seconds
                bottlenecks.append({
                    "stage": stage_name,
                    "issue": "slow_execution",
                    "avg_duration_ms": stats["avg_duration_ms"],
                    "severity": "high" if stats["avg_duration_ms"] > 30000 else "medium",
                })
            
            # Check for high failure rate
            failure_rate = 1 - (stats["successful_runs"] / max(stats["total_runs"], 1))
            if failure_rate > 0.3:  # > 30% failure
                bottlenecks.append({
                    "stage": stage_name,
                    "issue": "high_failure_rate",
                    "failure_rate": failure_rate,
                    "severity": "high" if failure_rate > 0.5 else "medium",
                })
        
        return sorted(bottlenecks, key=lambda x: 0 if x["severity"] == "high" else 1)
    
    def _save_run(self, run: ExpansionRun) -> None:
        """Persist a run to disk."""
        run_file = os.path.join(
            self.storage_dir,
            f"run_{run.run_id}_{run.started_at.strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        data = {
            "run_id": run.run_id,
            "started_at": run.started_at.isoformat(),
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "domain": run.domain,
            "query": run.query[:500],
            "success": run.success,
            "error": run.error,
            "total_duration_ms": run.total_duration_ms,
            "stages": [
                {
                    "stage_name": s.stage_name,
                    "duration_ms": s.duration_ms,
                    "success": s.success,
                    "error": s.error,
                }
                for s in run.stages
            ],
        }
        
        with open(run_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def _load_history(self) -> None:
        """Load historical runs from disk."""
        if not os.path.exists(self.storage_dir):
            return
        
        for filename in os.listdir(self.storage_dir):
            if filename.startswith("run_") and filename.endswith(".json"):
                try:
                    with open(os.path.join(self.storage_dir, filename), "r") as f:
                        data = json.load(f)
                    
                    run = ExpansionRun(
                        run_id=data["run_id"],
                        started_at=datetime.fromisoformat(data["started_at"]),
                        completed_at=datetime.fromisoformat(data["completed_at"]) if data["completed_at"] else None,
                        domain=data["domain"],
                        query=data["query"],
                        success=data["success"],
                        error=data.get("error"),
                    )
                    self.run_history.append(run)
                except Exception:
                    pass
