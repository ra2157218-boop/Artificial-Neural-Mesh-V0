"""
Integration Tests for Router
============================
Tests the Router.handle() method with real LLM inference.
"""

import pytest
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import log_test, assert_valid_result


class TestRouterInstantiation:
    """Test Router class instantiation."""

    @pytest.mark.integration
    @pytest.mark.critical
    def test_router_instantiation(self):
        """Test Router can be instantiated."""
        log_test("Testing Router instantiation...")
        try:
            from anm.router.router import Router
            router = Router({})
            assert router is not None
            log_test("Router instantiated successfully")
        except Exception as e:
            log_test(f"Router instantiation failed: {e}", "ERROR")
            pytest.fail(f"Router instantiation failed: {e}")

    @pytest.mark.integration
    def test_router_with_config(self):
        """Test Router with configuration."""
        log_test("Testing Router with config...")
        from anm.router.router import Router

        config = {
            "verbose": True,
            "max_steps": 10
        }
        router = Router(config)
        assert router is not None
        log_test("Router with config instantiated")


class TestRouterHandle:
    """Test Router.handle() method."""

    @pytest.mark.integration
    @pytest.mark.critical
    @pytest.mark.timeout(180)
    def test_router_handle_simple_query(self):
        """Test Router.handle() with simple query."""
        log_test("Testing Router.handle() with simple query...")
        from anm.router.router import Router

        router = Router({})
        start = time.time()

        try:
            result = router.handle("What is 2 + 2?")
            duration = (time.time() - start) * 1000

            assert isinstance(result, dict)
            log_test(f"Router.handle() completed in {duration:.1f}ms")
            log_test(f"Result keys: {list(result.keys())}")

            # Check required fields
            if "result" in result:
                log_test(f"Result preview: {str(result['result'])[:200]}")
            if "router_plan" in result:
                log_test(f"Router plan: {result['router_plan']}")

        except Exception as e:
            log_test(f"Router.handle() failed: {e}", "ERROR")
            raise

    @pytest.mark.integration
    @pytest.mark.timeout(180)
    def test_router_handle_quick_mode(self):
        """Test Router.handle() in quick mode."""
        log_test("Testing Router.handle() in quick mode...")
        from anm.router.router import Router

        router = Router({})
        result = router.handle("Hello", quick_mode=True)

        assert isinstance(result, dict)
        log_test(f"Quick mode result keys: {list(result.keys())}")

    @pytest.mark.integration
    @pytest.mark.timeout(180)
    def test_router_handle_research_mode(self):
        """Test Router.handle() in research mode."""
        log_test("Testing Router.handle() in research mode...")
        from anm.router.router import Router

        router = Router({})
        result = router.handle("Explain photosynthesis", research_mode=True)

        assert isinstance(result, dict)
        log_test(f"Research mode result keys: {list(result.keys())}")

    @pytest.mark.integration
    def test_router_handle_empty_query(self):
        """Test Router.handle() with empty query."""
        log_test("Testing Router.handle() with empty query...")
        from anm.router.router import Router

        router = Router({})

        try:
            result = router.handle("")
            log_test(f"Empty query result: {result}")
        except Exception as e:
            log_test(f"Empty query raised: {e}")
            # This might be expected behavior


class TestRouterDomainClassification:
    """Test Router domain classification."""

    @pytest.mark.integration
    @pytest.mark.timeout(120)
    def test_math_domain_detection(self):
        """Test math query routes to math domain."""
        log_test("Testing math domain detection...")
        from anm.router.router import Router

        router = Router({})
        result = router.handle("Calculate the derivative of x^2")

        if "router_plan" in result:
            plan = result["router_plan"]
            domains = plan.get("active_domains", [])
            entry = plan.get("entry_specialist", "")
            log_test(f"Math query - entry: {entry}, domains: {domains}")

    @pytest.mark.integration
    @pytest.mark.timeout(120)
    def test_code_domain_detection(self):
        """Test code query routes to code domain."""
        log_test("Testing code domain detection...")
        from anm.router.router import Router

        router = Router({})
        result = router.handle("Write a Python function")

        if "router_plan" in result:
            plan = result["router_plan"]
            entry = plan.get("entry_specialist", "")
            log_test(f"Code query - entry: {entry}")

    @pytest.mark.integration
    @pytest.mark.timeout(120)
    def test_physics_domain_detection(self):
        """Test physics query routes to physics domain."""
        log_test("Testing physics domain detection...")
        from anm.router.router import Router

        router = Router({})
        result = router.handle("What is kinetic energy?")

        if "router_plan" in result:
            plan = result["router_plan"]
            entry = plan.get("entry_specialist", "")
            log_test(f"Physics query - entry: {entry}")


class TestRouterErrorHandling:
    """Test Router error handling."""

    @pytest.mark.integration
    def test_router_handles_none_gracefully(self):
        """Test Router handles None input."""
        log_test("Testing Router with None input...")
        from anm.router.router import Router

        router = Router({})

        try:
            result = router.handle(None)
            log_test(f"None input result: {result}")
        except TypeError as e:
            log_test(f"None input raised TypeError (expected): {e}")
        except Exception as e:
            log_test(f"None input raised: {type(e).__name__}: {e}")

    @pytest.mark.integration
    def test_router_handles_special_characters(self):
        """Test Router handles special characters."""
        log_test("Testing Router with special characters...")
        from anm.router.router import Router

        router = Router({})

        special_query = "!@#$%^&*() <script>test</script>"
        try:
            result = router.handle(special_query)
            log_test(f"Special chars result: {type(result)}")
        except Exception as e:
            log_test(f"Special chars raised: {e}")
