# ============================================================
# ANM V0-OpenSource — DEVICE AWARENESS MODULE
#  Part of Self-Improvement Pipeline (Stage 3.8)
# ============================================================

from __future__ import annotations
from typing import Dict, Any, Optional
import platform
import subprocess
import logging


class DeviceAwareness:
    """
    Device Awareness Module for Self-Improvement Pipeline.
    
    Responsibilities:
      - Checks CPU/GPU/RAM/NPU/Thermals before fine-tuning
      - If hardware is insufficient → requests cloud
      - If cloud unavailable → requests human approval
      - Prevents runaway training & ensures safety
    """
    
    def __init__(self):
        self.device_info: Optional[Dict[str, Any]] = None
        
    def check_device_capabilities(
        self, required_memory_gb: float = 8.0, required_cpu_cores: int = 4
    ) -> Dict[str, Any]:
        """
        Check device capabilities for training.
        
        Args:
            required_memory_gb: Minimum RAM required (GB)
            required_cpu_cores: Minimum CPU cores required
        
        Returns:
            Dict with device info and training capability
        """
        device_info = self._gather_device_info()
        self.device_info = device_info
        
        # Check if device meets requirements
        can_train_locally = (
            device_info.get("memory_gb", 0) >= required_memory_gb and
            device_info.get("cpu_count", 0) >= required_cpu_cores
        )
        
        # Check thermal status (if available)
        thermal_status = self._check_thermal_status()
        
        # If thermals are high, don't train locally
        if thermal_status.get("temperature_high", False):
            can_train_locally = False
        
        return {
            **device_info,
            "can_train_locally": can_train_locally,
            "requires_cloud": not can_train_locally,
            "thermal_status": thermal_status,
            "recommendation": self._get_recommendation(
                can_train_locally, device_info, thermal_status
            ),
        }
    
    def _gather_device_info(self) -> Dict[str, Any]:
        """Gather comprehensive device information."""
        info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "cpu_count": 0,
            "memory_gb": 0.0,
            "has_gpu": False,
            "gpu_info": None,
            "has_npu": False,
            "npu_info": None,
        }
        
        # CPU and Memory (using psutil if available, else fallback)
        try:
            import psutil
            info["cpu_count"] = psutil.cpu_count(logical=True)
            memory = psutil.virtual_memory()
            info["memory_gb"] = round(memory.total / (1024 ** 3), 2)
            info["memory_available_gb"] = round(memory.available / (1024 ** 3), 2)
            info["memory_percent_used"] = memory.percent
        except ImportError:
            # Fallback: try system commands
            try:
                if platform.system() == "Darwin":  # macOS
                    cpu_count = int(
                        subprocess.check_output(["sysctl", "-n", "hw.ncpu"])
                        .decode()
                        .strip()
                    )
                    memory_bytes = int(
                        subprocess.check_output(["sysctl", "-n", "hw.memsize"])
                        .decode()
                        .strip()
                    )
                    info["cpu_count"] = cpu_count
                    info["memory_gb"] = round(memory_bytes / (1024 ** 3), 2)
                elif platform.system() == "Linux":
                    cpu_count = int(
                        subprocess.check_output(["nproc"]).decode().strip()
                    )
                    with open("/proc/meminfo", "r") as f:
                        for line in f:
                            if "MemTotal:" in line:
                                memory_kb = int(line.split()[1])
                                info["memory_gb"] = round(memory_kb / (1024 ** 2), 2)
                                break
                    info["cpu_count"] = cpu_count
            except Exception as e:
                # Last resort: use platform defaults
                logging.warning(f"Failed to get device info, using defaults: {e}")
                info["cpu_count"] = 4  # Conservative default
                info["memory_gb"] = 8.0  # Conservative default
        
        # GPU detection
        info["has_gpu"], info["gpu_info"] = self._detect_gpu()
        
        # NPU detection (for Apple Silicon, etc.)
        info["has_npu"], info["npu_info"] = self._detect_npu()
        
        return info
    
    def _detect_gpu(self) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Detect GPU availability and info."""
        gpu_info = None
        
        # Check for NVIDIA GPU
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                if lines:
                    gpu_info = {
                        "type": "nvidia",
                        "name": lines[0].split(",")[0].strip(),
                        "memory": lines[0].split(",")[1].strip() if "," in lines[0] else "unknown",
                    }
                    return True, gpu_info
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Check for Apple Metal (M-series chips)
        try:
            if platform.system() == "Darwin":
                # Check if Metal is available (simplified check)
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0 and "Metal" in result.stdout:
                    gpu_info = {
                        "type": "apple_metal",
                        "name": "Apple Silicon GPU",
                    }
                    return True, gpu_info
        except Exception as e:
            logging.debug(f"Apple Metal detection failed: {e}")
        
        # Check for AMD GPU (Linux)
        try:
            result = subprocess.run(
                ["lspci"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and "AMD" in result.stdout and "VGA" in result.stdout:
                gpu_info = {
                    "type": "amd",
                    "name": "AMD GPU",
                }
                return True, gpu_info
        except Exception as e:
            logging.debug(f"AMD GPU detection failed: {e}")

        return False, None
    
    def _detect_npu(self) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Detect NPU availability (e.g., Apple Neural Engine)."""
        npu_info = None
        
        # Check for Apple Neural Engine (M-series chips)
        try:
            if platform.system() == "Darwin":
                # Check processor type
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    cpu_brand = result.stdout.strip()
                    if "Apple" in cpu_brand and ("M1" in cpu_brand or "M2" in cpu_brand or "M3" in cpu_brand):
                        npu_info = {
                            "type": "apple_neural_engine",
                            "name": "Apple Neural Engine",
                        }
                        return True, npu_info
        except Exception as e:
            logging.debug(f"NPU detection failed: {e}")

        return False, None
    
    def _check_thermal_status(self) -> Dict[str, Any]:
        """Check thermal status of the device."""
        thermal_status = {
            "temperature_high": False,
            "temperature_celsius": None,
            "thermal_state": "unknown",
        }
        
        # macOS thermal check
        try:
            if platform.system() == "Darwin":
                # Check thermal pressure (simplified)
                result = subprocess.run(
                    ["pmset", "-g", "thermlog"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    output = result.stdout.lower()
                    if "thermal" in output and ("high" in output or "critical" in output):
                        thermal_status["temperature_high"] = True
                        thermal_status["thermal_state"] = "high"
                    else:
                        thermal_status["thermal_state"] = "normal"
        except Exception as e:
            logging.debug(f"macOS thermal check failed: {e}")
        
        # Linux thermal check
        try:
            if platform.system() == "Linux":
                # Check thermal zones
                import os
                thermal_path = "/sys/class/thermal/thermal_zone0/temp"
                if os.path.exists(thermal_path):
                    with open(thermal_path, "r") as f:
                        temp_millidegrees = int(f.read().strip())
                        temp_celsius = temp_millidegrees / 1000.0
                        thermal_status["temperature_celsius"] = temp_celsius
                        
                        # Consider high if > 80°C
                        if temp_celsius > 80:
                            thermal_status["temperature_high"] = True
                            thermal_status["thermal_state"] = "high"
                        else:
                            thermal_status["thermal_state"] = "normal"
        except Exception as e:
            logging.debug(f"Linux thermal check failed: {e}")

        return thermal_status
    
    def _get_recommendation(
        self,
        can_train_locally: bool,
        device_info: Dict[str, Any],
        thermal_status: Dict[str, Any],
    ) -> str:
        """Get recommendation based on device capabilities."""
        if can_train_locally and not thermal_status.get("temperature_high", False):
            return "Local training recommended"
        elif thermal_status.get("temperature_high", False):
            return "Thermal limits reached - cloud training recommended"
        elif device_info.get("memory_gb", 0) < 8.0:
            return "Insufficient RAM - cloud training recommended"
        elif device_info.get("cpu_count", 0) < 4:
            return "Insufficient CPU cores - cloud training recommended"
        else:
            return "Cloud training recommended"
    
    def request_cloud_approval(
        self, reason: str, estimated_cost: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Request human approval for cloud compute.
        
        Returns:
            Dict with approval request details
        """
        return {
            "requires_human_approval": True,
            "reason": reason,
            "estimated_cost": estimated_cost,
            "device_info": self.device_info,
            "message": f"Cloud compute required: {reason}. Approve or deny?",
        }
