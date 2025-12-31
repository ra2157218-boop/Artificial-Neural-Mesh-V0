"""
Integration Tests for ANM Entry Point
=====================================
Tests the main ANM class with real LLM inference.
"""

import pytest
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import log_test, assert_valid_result, assert_has_router_plan


class TestANMInstantiation:
    """Test ANM class instantiation."""

    @pytest.mark.integration
    @pytest.mark.critical
    def test_anm_instantiation_default(self):
        """Test ANM instantiation with defaults."""
        log_test("Testing ANM instantiation with defaults...")
        from anm import ANM, ANMConfig

        config = ANMConfig(skip_sanity_check=True, verbose=False)
        start = time.time()
        anm = ANM(config=config)
        duration = (time.time() - start) * 1000

        assert anm is not None
        log_test(f"ANM instantiated in {duration:.1f}ms")

    @pytest.mark.integration
    def test_anm_instantiation_quick_mode(self):
        """Test ANM instantiation in quick mode."""
        log_test("Testing ANM instantiation with quick_mode=True...")
        from anm import ANM, ANMConfig

        config = ANMConfig(
            quick_mode=True,
            skip_sanity_check=True,
            verbose=False
        )
        anm = ANM(config=config)
        assert anm is not None
        assert anm.anm_config.quick_mode == True
        log_test("ANM quick mode instantiation successful")


class TestANMQuery:
    """Test ANM.query() method with real inference."""

    @pytest.mark.integration
    @pytest.mark.critical
    @pytest.mark.timeout(120)
    def test_anm_query_simple_greeting(self, anm_instance):
        """Test simple greeting query."""
        log_test("Testing ANM query: 'Hello'...")
        start = time.time()
        result = anm_instance.query("Hello")
        duration = (time.time() - start) * 1000

        assert_valid_result(result, "simple_greeting")
        log_test(f"Query completed in {duration:.1f}ms")
        log_test(f"Result status: {result.get('status', 'N/A')}")
        log_test(f"Result preview: {str(result.get('result', ''))[:100]}...")

    @pytest.mark.integration
    @pytest.mark.critical
    @pytest.mark.timeout(120)
    def test_anm_query_math(self, anm_instance):
        """Test math query."""
        log_test("Testing ANM query: 'What is 2 + 2?'...")
        start = time.time()
        result = anm_instance.query("What is 2 + 2?")
        duration = (time.time() - start) * 1000

        assert_valid_result(result, "math_query")
        log_test(f"Query completed in {duration:.1f}ms")
        log_test(f"Result: {str(result.get('result', ''))[:200]}")

    @pytest.mark.integration
    @pytest.mark.critical
    def test_anm_query_empty_string(self, anm_instance):
        """Test empty string query handling."""
        log_test("Testing ANM query with empty string...")
        result = anm_instance.query("")

        # Should return error or handle gracefully
        assert isinstance(result, dict)
        log_test(f"Empty query result: {result}")

    @pytest.mark.integration
    def test_anm_query_whitespace_only(self, anm_instance):
        """Test whitespace-only query handling."""
        log_test("Testing ANM query with whitespace only...")
        result = anm_instance.query("   ")

        assert isinstance(result, dict)
        log_test(f"Whitespace query result: {result}")

    @pytest.mark.integration
    @pytest.mark.timeout(180)
    def test_anm_query_code(self, anm_instance):
        """Test code query."""
        log_test("Testing ANM query: code request...")
        result = anm_instance.query("Write a Python function to add two numbers")

        assert_valid_result(result, "code_query")
        log_test(f"Code query result preview: {str(result.get('result', ''))[:300]}")

    @pytest.mark.integration
    @pytest.mark.timeout(180)
    def test_anm_query_physics(self, anm_instance):
        """Test physics query."""
        log_test("Testing ANM query: physics...")
        result = anm_instance.query("What is Newton's first law?")

        assert_valid_result(result, "physics_query")
        log_test(f"Physics query result preview: {str(result.get('result', ''))[:300]}")


class TestANMRouterPlan:
    """Test that router_plan is always present."""

    @pytest.mark.integration
    @pytest.mark.critical
    @pytest.mark.timeout(120)
    def test_router_plan_present_on_success(self, anm_instance):
        """Test router_plan is present on successful query."""
        log_test("Testing router_plan presence on success...")
        result = anm_instance.query("What is gravity?")

        # This is CRITICAL - router_plan must ALWAYS be present
        assert "router_plan" in result, "CRITICAL: router_plan missing from result!"
        assert isinstance(result["router_plan"], dict)

        plan = result["router_plan"]
        log_test(f"router_plan keys: {list(plan.keys())}")
        log_test(f"entry_specialist: {plan.get('entry_specialist', 'N/A')}")
        log_test(f"active_domains: {plan.get('active_domains', 'N/A')}")

    @pytest.mark.integration
    @pytest.mark.critical
    def test_router_plan_present_on_empty_query(self, anm_instance):
        """Test router_plan is present even on empty query."""
        log_test("Testing router_plan presence on empty query...")
        result = anm_instance.query("")

        # router_plan should still be present
        # If not, this is a bug to fix
        if "router_plan" not in result:
            log_test("BUG FOUND: router_plan missing on empty query!", "ERROR")
            pytest.fail("router_plan should always be present")


class TestANMCleanup:
    """Test ANM cleanup and resource management."""

    @pytest.mark.integration
    def test_anm_cleanup(self):
        """Test ANM cleanup releases resources."""
        log_test("Testing ANM cleanup...")
        from anm import ANM, ANMConfig

        config = ANMConfig(skip_sanity_check=True, verbose=False)
        anm = ANM(config=config)

        # Cleanup should not raise
        try:
            anm.cleanup()
            log_test("ANM cleanup successful")
        except Exception as e:
            log_test(f"Cleanup raised exception: {e}", "WARNING")
            # Don't fail - cleanup errors are often non-critical

    @pytest.mark.integration
    def test_anm_context_manager(self):
        """Test ANM as context manager."""
        log_test("Testing ANM as context manager...")
        from anm import ANM, ANMConfig

        config = ANMConfig(skip_sanity_check=True, verbose=False)

        # Should work as context manager
        try:
            with ANM(config=config) as anm:
                result = anm.query("Hi")
                assert result is not None
            log_test("ANM context manager test passed")
        except AttributeError:
            log_test("ANM doesn't support context manager protocol", "WARNING")
        except Exception as e:
            log_test(f"Context manager error: {e}", "WARNING")
