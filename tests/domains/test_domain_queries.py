"""
Domain-Specific Query Tests
===========================
Tests queries across all domains with real LLM inference.
"""

import pytest
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import log_test, assert_valid_result


class TestMathQueries:
    """Test math domain queries."""

    @pytest.mark.domain
    @pytest.mark.timeout(180)
    def test_math_simple_arithmetic(self, anm_instance):
        """Test simple arithmetic query."""
        log_test("Testing math: simple arithmetic...")
        result = anm_instance.query("What is 15 + 27?")
        assert_valid_result(result, "math_arithmetic")
        log_test(f"Result: {str(result.get('result', ''))[:200]}")

    @pytest.mark.domain
    @pytest.mark.timeout(180)
    def test_math_algebra(self, anm_instance):
        """Test algebra query."""
        log_test("Testing math: algebra...")
        result = anm_instance.query("Solve for x: 2x + 5 = 15")
        assert_valid_result(result, "math_algebra")
        log_test(f"Result: {str(result.get('result', ''))[:200]}")

    @pytest.mark.domain
    @pytest.mark.timeout(180)
    def test_math_calculus(self, anm_instance):
        """Test calculus query."""
        log_test("Testing math: calculus...")
        result = anm_instance.query("What is the derivative of x^3?")
        assert_valid_result(result, "math_calculus")
        log_test(f"Result: {str(result.get('result', ''))[:200]}")

    @pytest.mark.domain
    @pytest.mark.timeout(180)
    def test_math_percentage(self, anm_instance):
        """Test percentage calculation."""
        log_test("Testing math: percentage...")
        result = anm_instance.query("What is 25% of 200?")
        assert_valid_result(result, "math_percentage")
        log_test(f"Result: {str(result.get('result', ''))[:200]}")


class TestPhysicsQueries:
    """Test physics domain queries."""

    @pytest.mark.domain
    @pytest.mark.timeout(180)
    def test_physics_newton_law(self, anm_instance):
        """Test Newton's law query."""
        log_test("Testing physics: Newton's law...")
        result = anm_instance.query("What is Newton's second law?")
        assert_valid_result(result, "physics_newton")
        log_test(f"Result: {str(result.get('result', ''))[:200]}")

    @pytest.mark.domain
    @pytest.mark.timeout(180)
    def test_physics_force_calculation(self, anm_instance):
        """Test force calculation query."""
        log_test("Testing physics: force calculation...")
        result = anm_instance.query("Calculate the force on a 10kg object accelerating at 5 m/s^2")
        assert_valid_result(result, "physics_force")
        log_test(f"Result: {str(result.get('result', ''))[:200]}")

    @pytest.mark.domain
    @pytest.mark.timeout(180)
    def test_physics_energy(self, anm_instance):
        """Test energy concept query."""
        log_test("Testing physics: energy...")
        result = anm_instance.query("What is kinetic energy?")
        assert_valid_result(result, "physics_energy")
        log_test(f"Result: {str(result.get('result', ''))[:200]}")


class TestCodeQueries:
    """Test code domain queries."""

    @pytest.mark.domain
    @pytest.mark.timeout(180)
    def test_code_simple_function(self, anm_instance):
        """Test simple function request."""
        log_test("Testing code: simple function...")
        result = anm_instance.query("Write a Python function to add two numbers")
        assert_valid_result(result, "code_function")
        log_test(f"Result: {str(result.get('result', ''))[:300]}")

    @pytest.mark.domain
    @pytest.mark.timeout(180)
    def test_code_algorithm(self, anm_instance):
        """Test algorithm request."""
        log_test("Testing code: algorithm...")
        result = anm_instance.query("How do I implement binary search in Python?")
        assert_valid_result(result, "code_algorithm")
        log_test(f"Result: {str(result.get('result', ''))[:300]}")

    @pytest.mark.domain
    @pytest.mark.timeout(180)
    def test_code_explanation(self, anm_instance):
        """Test code explanation request."""
        log_test("Testing code: explanation...")
        result = anm_instance.query("What is a for loop?")
        assert_valid_result(result, "code_explanation")
        log_test(f"Result: {str(result.get('result', ''))[:300]}")


class TestChemistryQueries:
    """Test chemistry domain queries."""

    @pytest.mark.domain
    @pytest.mark.timeout(180)
    def test_chemistry_molecule(self, anm_instance):
        """Test molecule query."""
        log_test("Testing chemistry: molecule...")
        result = anm_instance.query("What is H2O?")
        assert_valid_result(result, "chemistry_molecule")
        log_test(f"Result: {str(result.get('result', ''))[:200]}")

    @pytest.mark.domain
    @pytest.mark.timeout(180)
    def test_chemistry_bonds(self, anm_instance):
        """Test chemical bonds query."""
        log_test("Testing chemistry: bonds...")
        result = anm_instance.query("What is a covalent bond?")
        assert_valid_result(result, "chemistry_bonds")
        log_test(f"Result: {str(result.get('result', ''))[:200]}")


class TestBiologyQueries:
    """Test biology domain queries."""

    @pytest.mark.domain
    @pytest.mark.timeout(180)
    def test_biology_cell(self, anm_instance):
        """Test cell biology query."""
        log_test("Testing biology: cell...")
        result = anm_instance.query("What is a cell?")
        assert_valid_result(result, "biology_cell")
        log_test(f"Result: {str(result.get('result', ''))[:200]}")

    @pytest.mark.domain
    @pytest.mark.timeout(180)
    def test_biology_dna(self, anm_instance):
        """Test DNA query."""
        log_test("Testing biology: DNA...")
        result = anm_instance.query("What is DNA?")
        assert_valid_result(result, "biology_dna")
        log_test(f"Result: {str(result.get('result', ''))[:200]}")


class TestGeneralQueries:
    """Test general domain queries."""

    @pytest.mark.domain
    @pytest.mark.timeout(180)
    def test_general_greeting(self, anm_instance):
        """Test greeting query."""
        log_test("Testing general: greeting...")
        result = anm_instance.query("Hello, how are you?")
        assert_valid_result(result, "general_greeting")
        log_test(f"Result: {str(result.get('result', ''))[:200]}")

    @pytest.mark.domain
    @pytest.mark.timeout(180)
    def test_general_factual(self, anm_instance):
        """Test factual query."""
        log_test("Testing general: factual...")
        result = anm_instance.query("What is the capital of France?")
        assert_valid_result(result, "general_factual")
        log_test(f"Result: {str(result.get('result', ''))[:200]}")

    @pytest.mark.domain
    @pytest.mark.timeout(180)
    def test_general_ai(self, anm_instance):
        """Test AI explanation query."""
        log_test("Testing general: AI...")
        result = anm_instance.query("What is artificial intelligence?")
        assert_valid_result(result, "general_ai")
        log_test(f"Result: {str(result.get('result', ''))[:200]}")
