"""
ANM Test Suite - Shared Fixtures and Configuration
===================================================
This module provides all shared fixtures, helpers, and configuration
for the comprehensive ANM test suite.

IMPORTANT: This is testing/debugging only - NO core code deletion!
"""

import pytest
import sys
import os
import time
import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Test results logging
TEST_LOG_FILE = PROJECT_ROOT / "test_reports" / "test_log.txt"
TEST_RESULTS_JSON = PROJECT_ROOT / "test_reports" / "results.json"

# Global test results storage
_test_results: List[Dict[str, Any]] = []


def log_test(message: str, level: str = "INFO"):
    """Log test message to file and console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)

    # Ensure directory exists
    TEST_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(TEST_LOG_FILE, "a") as f:
        f.write(log_line + "\n")


def record_test_result(
    test_name: str,
    passed: bool,
    duration_ms: float,
    error: Optional[str] = None,
    details: Optional[Dict] = None
):
    """Record test result for final report."""
    result = {
        "test_name": test_name,
        "passed": passed,
        "duration_ms": duration_ms,
        "timestamp": datetime.now().isoformat(),
        "error": error,
        "details": details or {}
    }
    _test_results.append(result)

    # Save incrementally
    with open(TEST_RESULTS_JSON, "w") as f:
        json.dump(_test_results, f, indent=2, default=str)


# ============================================================
# PYTEST HOOKS
# ============================================================

def pytest_configure(config):
    """Called after command line options have been parsed."""
    log_test("=" * 60)
    log_test("ANM V0-OpenSource COMPREHENSIVE TEST SUITE")
    log_test("=" * 60)
    log_test(f"Python version: {sys.version}")
    log_test(f"Project root: {PROJECT_ROOT}")
    log_test("Starting test run...")


def pytest_runtest_setup(item):
    """Called before each test."""
    log_test(f"STARTING: {item.name}")


def pytest_runtest_makereport(item, call):
    """Called after each test phase (setup, call, teardown)."""
    if call.when == "call":
        duration_ms = call.duration * 1000
        if call.excinfo is None:
            log_test(f"PASSED: {item.name} ({duration_ms:.1f}ms)")
            record_test_result(item.name, True, duration_ms)
        else:
            error_msg = str(call.excinfo.value)
            log_test(f"FAILED: {item.name} - {error_msg}", "ERROR")
            record_test_result(
                item.name,
                False,
                duration_ms,
                error=error_msg,
                details={"traceback": str(call.excinfo.traceback)}
            )


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished."""
    passed = sum(1 for r in _test_results if r["passed"])
    failed = sum(1 for r in _test_results if not r["passed"])
    total = len(_test_results)

    log_test("=" * 60)
    log_test("TEST RUN COMPLETE")
    log_test(f"Total: {total} | Passed: {passed} | Failed: {failed}")
    log_test(f"Success rate: {100*passed/total if total > 0 else 0:.1f}%")
    log_test("=" * 60)


# ============================================================
# FIXTURES - ANM Components
# ============================================================

@pytest.fixture(scope="session")
def project_root():
    """Return project root path."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def anm_config():
    """Create ANMConfig for testing."""
    try:
        from anm import ANMConfig
        config = ANMConfig(
            parallel_models=1,  # Single model for testing
            quick_mode=False,
            auto_mode=True,
            skip_sanity_check=True,
            verbose=True,
            enable_learning=False  # Disable learning during tests
        )
        log_test("ANMConfig created successfully")
        return config
    except Exception as e:
        log_test(f"Failed to create ANMConfig: {e}", "ERROR")
        pytest.skip(f"ANMConfig not available: {e}")


@pytest.fixture(scope="session")
def anm_instance(anm_config):
    """Create session-scoped ANM instance."""
    try:
        from anm import ANM
        log_test("Creating ANM instance...")
        start = time.time()
        anm = ANM(config=anm_config)
        duration = (time.time() - start) * 1000
        log_test(f"ANM instance created in {duration:.1f}ms")
        yield anm
        log_test("Cleaning up ANM instance...")
        try:
            anm.cleanup()
        except:
            pass
    except Exception as e:
        log_test(f"Failed to create ANM instance: {e}", "ERROR")
        log_test(traceback.format_exc(), "ERROR")
        pytest.skip(f"ANM not available: {e}")


@pytest.fixture(scope="session")
def quick_anm():
    """Create ANM instance in quick mode for faster tests."""
    try:
        from anm import ANM, ANMConfig
        config = ANMConfig(
            parallel_models=1,
            quick_mode=True,
            auto_mode=False,
            skip_sanity_check=True,
            verbose=False
        )
        anm = ANM(config=config)
        yield anm
        try:
            anm.cleanup()
        except:
            pass
    except Exception as e:
        pytest.skip(f"Quick ANM not available: {e}")


@pytest.fixture(scope="function")
def router():
    """Create fresh Router instance for each test."""
    try:
        from anm.router.router import Router
        router = Router({})
        log_test("Router instance created")
        return router
    except Exception as e:
        log_test(f"Failed to create Router: {e}", "ERROR")
        pytest.skip(f"Router not available: {e}")


@pytest.fixture(scope="function")
def memory_hub(tmp_path):
    """Create MemoryHub with temporary diary."""
    try:
        from anm.memory.memory_hub import MemoryHub
        diary_path = str(tmp_path / "test_diary.txt")
        hub = MemoryHub(diary_path=diary_path)
        log_test(f"MemoryHub created with diary: {diary_path}")
        return hub
    except Exception as e:
        log_test(f"Failed to create MemoryHub: {e}", "ERROR")
        pytest.skip(f"MemoryHub not available: {e}")


@pytest.fixture(scope="session")
def inference_engine():
    """Get inference engine instance."""
    try:
        from anm.system.inference import get_inference_engine, InferenceConfig
        config = InferenceConfig(quick_mode=True)
        engine = get_inference_engine(config)
        log_test("InferenceEngine obtained")
        return engine
    except Exception as e:
        log_test(f"Failed to get InferenceEngine: {e}", "ERROR")
        pytest.skip(f"InferenceEngine not available: {e}")


# ============================================================
# FIXTURES - Test Data
# ============================================================

@pytest.fixture
def sample_queries():
    """Collection of test queries by domain."""
    return {
        "math": [
            "What is 2 + 2?",
            "Solve x^2 - 4 = 0",
            "What is the derivative of x^3?",
            "Calculate the integral of 2x dx",
            "What is 15% of 200?",
        ],
        "physics": [
            "What is Newton's first law?",
            "Calculate the force on a 5kg mass accelerating at 2 m/s^2",
            "What is the speed of light?",
            "Explain gravity",
            "What is kinetic energy?",
        ],
        "code": [
            "Write a Python function to add two numbers",
            "How do I reverse a string in Python?",
            "What is a for loop?",
            "Explain recursion",
            "Write hello world in Python",
        ],
        "chemistry": [
            "What is H2O?",
            "What is the periodic table?",
            "Explain chemical bonds",
            "What is an atom?",
        ],
        "biology": [
            "What is DNA?",
            "Explain photosynthesis",
            "What is a cell?",
            "What are mitochondria?",
        ],
        "general": [
            "Hello",
            "What is AI?",
            "Tell me a joke",
            "What is the capital of France?",
            "How are you?",
        ],
        "edge_cases": [
            "",  # Empty
            " ",  # Whitespace
            "a" * 10000,  # Very long
            "!@#$%^&*()",  # Special chars
            "SELECT * FROM users",  # SQL-like
            "<script>alert('xss')</script>",  # XSS-like
        ]
    }


@pytest.fixture
def simple_query():
    """A simple query for basic tests."""
    return "What is 2 + 2?"


@pytest.fixture
def complex_query():
    """A complex query requiring multi-step reasoning."""
    return "Explain the relationship between quantum mechanics and general relativity, and why unifying them is challenging."


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def assert_valid_result(result: Dict[str, Any], test_name: str = ""):
    """Assert that a result dict has the expected structure."""
    assert isinstance(result, dict), f"{test_name}: Result should be a dict"

    # Must have either result or status
    has_result = "result" in result
    has_status = "status" in result
    assert has_result or has_status, f"{test_name}: Result must have 'result' or 'status' key"

    # If status is error, should have error message
    if has_status and result.get("status") == "error":
        assert "error" in result or "result" in result, f"{test_name}: Error status should have error message"

    return True


def assert_has_router_plan(result: Dict[str, Any]):
    """Assert router_plan is present (critical requirement)."""
    assert "router_plan" in result, "router_plan must ALWAYS be present in result"
    assert isinstance(result["router_plan"], dict), "router_plan must be a dict"


def measure_time(func):
    """Decorator to measure function execution time."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration_ms = (time.time() - start) * 1000
        return result, duration_ms
    return wrapper


def safe_import(module_path: str):
    """Safely import a module, returning None if failed."""
    try:
        parts = module_path.rsplit(".", 1)
        if len(parts) == 2:
            module = __import__(parts[0], fromlist=[parts[1]])
            return getattr(module, parts[1])
        else:
            return __import__(module_path)
    except Exception as e:
        log_test(f"Failed to import {module_path}: {e}", "WARNING")
        return None
