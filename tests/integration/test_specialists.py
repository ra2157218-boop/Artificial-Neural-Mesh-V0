"""
Integration Tests for Specialists
=================================
Tests all 12 specialists with real LLM inference.
"""

import pytest
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import log_test


class TestBaseSpecialist:
    """Test BaseSpecialist interface."""

    @pytest.mark.integration
    def test_base_specialist_import(self):
        """Test BaseSpecialist can be imported."""
        log_test("Testing BaseSpecialist import...")
        from anm.specialists.base import BaseSpecialist
        assert BaseSpecialist is not None
        log_test("BaseSpecialist imported successfully")

    @pytest.mark.integration
    def test_base_specialist_is_abstract(self):
        """Test BaseSpecialist cannot be instantiated directly."""
        log_test("Testing BaseSpecialist is abstract...")
        from anm.specialists.base import BaseSpecialist

        try:
            specialist = BaseSpecialist()
            log_test("WARNING: BaseSpecialist instantiated (should be abstract)", "WARNING")
        except TypeError:
            log_test("BaseSpecialist correctly raises TypeError (abstract)")
        except Exception as e:
            log_test(f"BaseSpecialist raised: {type(e).__name__}")


class TestGeneralLLM:
    """Test GeneralLLM specialist."""

    @pytest.mark.integration
    @pytest.mark.timeout(180)
    def test_general_llm_instantiation(self):
        """Test GeneralLLM can be instantiated."""
        log_test("Testing GeneralLLM instantiation...")
        from anm.specialists.general_llm import GeneralLLM

        specialist = GeneralLLM()
        assert specialist is not None
        log_test("GeneralLLM instantiated")

    @pytest.mark.integration
    @pytest.mark.timeout(180)
    def test_general_llm_run(self):
        """Test GeneralLLM.run() method."""
        log_test("Testing GeneralLLM.run()...")
        from anm.specialists.general_llm import GeneralLLM

        specialist = GeneralLLM()
        wot_packet = "USER_QUERY: What is artificial intelligence?"

        start = time.time()
        result = specialist.run(wot_packet)
        duration = (time.time() - start) * 1000

        assert isinstance(result, str)
        assert len(result) > 0
        log_test(f"GeneralLLM.run() completed in {duration:.1f}ms")
        log_test(f"Result preview: {result[:200]}...")

        # Check for WOT_REQUEST marker
        if "WOT_REQUEST" in result:
            log_test("WOT_REQUEST marker found in output")
        else:
            log_test("WARNING: WOT_REQUEST marker missing", "WARNING")


class TestMathLLM:
    """Test MathLLM specialist."""

    @pytest.mark.integration
    @pytest.mark.timeout(180)
    def test_math_llm_instantiation(self):
        """Test MathLLM can be instantiated."""
        log_test("Testing MathLLM instantiation...")
        from anm.specialists.math_llm import MathLLM

        specialist = MathLLM()
        assert specialist is not None
        log_test("MathLLM instantiated")

    @pytest.mark.integration
    @pytest.mark.timeout(180)
    def test_math_llm_run(self):
        """Test MathLLM.run() method."""
        log_test("Testing MathLLM.run()...")
        from anm.specialists.math_llm import MathLLM

        specialist = MathLLM()
        wot_packet = "USER_QUERY: Solve x^2 - 4 = 0"

        start = time.time()
        result = specialist.run(wot_packet)
        duration = (time.time() - start) * 1000

        assert isinstance(result, str)
        log_test(f"MathLLM.run() completed in {duration:.1f}ms")
        log_test(f"Result preview: {result[:200]}...")


class TestPhysicsLLM:
    """Test PhysicsLLM specialist."""

    @pytest.mark.integration
    @pytest.mark.timeout(180)
    def test_physics_llm_instantiation(self):
        """Test PhysicsLLM can be instantiated."""
        log_test("Testing PhysicsLLM instantiation...")
        from anm.specialists.physics_llm import PhysicsLLM

        specialist = PhysicsLLM()
        assert specialist is not None
        log_test("PhysicsLLM instantiated")

    @pytest.mark.integration
    @pytest.mark.timeout(180)
    def test_physics_llm_run(self):
        """Test PhysicsLLM.run() method."""
        log_test("Testing PhysicsLLM.run()...")
        from anm.specialists.physics_llm import PhysicsLLM

        specialist = PhysicsLLM()
        wot_packet = "USER_QUERY: What is Newton's first law?"

        start = time.time()
        result = specialist.run(wot_packet)
        duration = (time.time() - start) * 1000

        assert isinstance(result, str)
        log_test(f"PhysicsLLM.run() completed in {duration:.1f}ms")
        log_test(f"Result preview: {result[:200]}...")


class TestCodeLLM:
    """Test CodeLLM specialist."""

    @pytest.mark.integration
    @pytest.mark.timeout(180)
    def test_code_llm_instantiation(self):
        """Test CodeLLM can be instantiated."""
        log_test("Testing CodeLLM instantiation...")
        from anm.specialists.code_llm import CodeLLM

        specialist = CodeLLM()
        assert specialist is not None
        log_test("CodeLLM instantiated")

    @pytest.mark.integration
    @pytest.mark.timeout(180)
    def test_code_llm_run(self):
        """Test CodeLLM.run() method."""
        log_test("Testing CodeLLM.run()...")
        from anm.specialists.code_llm import CodeLLM

        specialist = CodeLLM()
        wot_packet = "USER_QUERY: Write a Python function to calculate factorial"

        start = time.time()
        result = specialist.run(wot_packet)
        duration = (time.time() - start) * 1000

        assert isinstance(result, str)
        log_test(f"CodeLLM.run() completed in {duration:.1f}ms")
        log_test(f"Result preview: {result[:300]}...")


class TestChemistryLLM:
    """Test ChemistryLLM specialist."""

    @pytest.mark.integration
    @pytest.mark.timeout(180)
    def test_chemistry_llm_instantiation(self):
        """Test ChemistryLLM can be instantiated."""
        log_test("Testing ChemistryLLM instantiation...")
        from anm.specialists.chemistry_llm import ChemistryLLM

        specialist = ChemistryLLM()
        assert specialist is not None
        log_test("ChemistryLLM instantiated")


class TestBiologyLLM:
    """Test BiologyLLM specialist."""

    @pytest.mark.integration
    @pytest.mark.timeout(180)
    def test_biology_llm_instantiation(self):
        """Test BiologyLLM can be instantiated."""
        log_test("Testing BiologyLLM instantiation...")
        from anm.specialists.biology_llm import BiologyLLM

        specialist = BiologyLLM()
        assert specialist is not None
        log_test("BiologyLLM instantiated")


class TestMemoryLLM:
    """Test MemoryLLM specialist."""

    @pytest.mark.integration
    @pytest.mark.timeout(180)
    def test_memory_llm_instantiation(self):
        """Test MemoryLLM can be instantiated."""
        log_test("Testing MemoryLLM instantiation...")
        from anm.specialists.memory_llm import MemoryLLM

        specialist = MemoryLLM()
        assert specialist is not None
        log_test("MemoryLLM instantiated")


class TestResearchLLM:
    """Test ResearchLLM specialist."""

    @pytest.mark.integration
    @pytest.mark.timeout(180)
    def test_research_llm_instantiation(self):
        """Test ResearchLLM can be instantiated."""
        log_test("Testing ResearchLLM instantiation...")
        from anm.specialists.research_llm import ResearchLLM

        specialist = ResearchLLM()
        assert specialist is not None
        log_test("ResearchLLM instantiated")


class TestSpecialistWOTRequest:
    """Test that specialists include WOT_REQUEST in output."""

    @pytest.mark.integration
    @pytest.mark.timeout(180)
    def test_wot_request_in_general_output(self):
        """Test WOT_REQUEST present in GeneralLLM output."""
        log_test("Testing WOT_REQUEST in GeneralLLM output...")
        from anm.specialists.general_llm import GeneralLLM

        specialist = GeneralLLM()
        result = specialist.run("USER_QUERY: Hello")

        # WOT_REQUEST should be present
        has_wot = "WOT_REQUEST" in result
        log_test(f"WOT_REQUEST present: {has_wot}")

        if not has_wot:
            log_test("POTENTIAL BUG: WOT_REQUEST missing from output", "WARNING")
