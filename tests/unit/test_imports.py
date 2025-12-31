"""
Unit Tests for Module Imports
=============================
Tests that all ANM modules can be imported without errors.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import log_test


class TestCoreImports:
    """Test core module imports."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_import_anm_main(self):
        """Test importing main ANM module."""
        log_test("Testing import: anm")
        try:
            import anm
            assert anm is not None
            log_test(f"anm module imported, version: {getattr(anm, '__version__', 'unknown')}")
        except Exception as e:
            pytest.fail(f"Failed to import anm: {e}")

    @pytest.mark.unit
    @pytest.mark.critical
    def test_import_anm_class(self):
        """Test importing ANM class."""
        log_test("Testing import: ANM class")
        try:
            from anm import ANM
            assert ANM is not None
            log_test("ANM class imported successfully")
        except Exception as e:
            pytest.fail(f"Failed to import ANM class: {e}")

    @pytest.mark.unit
    def test_import_config_settings(self):
        """Test importing config settings."""
        log_test("Testing import: anm.config.settings")
        try:
            from anm.config import settings
            assert settings is not None
            log_test("settings module imported")
        except Exception as e:
            pytest.fail(f"Failed to import settings: {e}")

    @pytest.mark.unit
    def test_import_core_types(self):
        """Test importing core types."""
        log_test("Testing import: anm.core.types")
        try:
            from anm.core import types
            assert types is not None
            log_test("types module imported")
        except Exception as e:
            pytest.fail(f"Failed to import types: {e}")


class TestRouterImports:
    """Test router module imports."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_import_router(self):
        """Test importing Router."""
        log_test("Testing import: Router")
        try:
            from anm.router.router import Router
            assert Router is not None
            log_test("Router class imported")
        except Exception as e:
            pytest.fail(f"Failed to import Router: {e}")

    @pytest.mark.unit
    def test_import_planner_llm(self):
        """Test importing PlannerLLM."""
        log_test("Testing import: PlannerLLM")
        try:
            from anm.router.planner_llm import PlannerLLM
            assert PlannerLLM is not None
            log_test("PlannerLLM class imported")
        except Exception as e:
            pytest.fail(f"Failed to import PlannerLLM: {e}")


class TestSpecialistImports:
    """Test specialist module imports."""

    @pytest.mark.unit
    def test_import_base_specialist(self):
        """Test importing BaseSpecialist."""
        log_test("Testing import: BaseSpecialist")
        try:
            from anm.specialists.base import BaseSpecialist
            assert BaseSpecialist is not None
            log_test("BaseSpecialist class imported")
        except Exception as e:
            pytest.fail(f"Failed to import BaseSpecialist: {e}")

    @pytest.mark.unit
    def test_import_general_llm(self):
        """Test importing GeneralLLM."""
        log_test("Testing import: GeneralLLM")
        try:
            from anm.specialists.general_llm import GeneralLLM
            assert GeneralLLM is not None
            log_test("GeneralLLM class imported")
        except Exception as e:
            pytest.fail(f"Failed to import GeneralLLM: {e}")

    @pytest.mark.unit
    def test_import_math_llm(self):
        """Test importing MathLLM."""
        log_test("Testing import: MathLLM")
        try:
            from anm.specialists.math_llm import MathLLM
            assert MathLLM is not None
            log_test("MathLLM class imported")
        except Exception as e:
            pytest.fail(f"Failed to import MathLLM: {e}")

    @pytest.mark.unit
    def test_import_physics_llm(self):
        """Test importing PhysicsLLM."""
        log_test("Testing import: PhysicsLLM")
        try:
            from anm.specialists.physics_llm import PhysicsLLM
            assert PhysicsLLM is not None
            log_test("PhysicsLLM class imported")
        except Exception as e:
            pytest.fail(f"Failed to import PhysicsLLM: {e}")

    @pytest.mark.unit
    def test_import_code_llm(self):
        """Test importing CodeLLM."""
        log_test("Testing import: CodeLLM")
        try:
            from anm.specialists.code_llm import CodeLLM
            assert CodeLLM is not None
            log_test("CodeLLM class imported")
        except Exception as e:
            pytest.fail(f"Failed to import CodeLLM: {e}")


class TestMemoryImports:
    """Test memory module imports."""

    @pytest.mark.unit
    def test_import_memory_hub(self):
        """Test importing MemoryHub."""
        log_test("Testing import: MemoryHub")
        try:
            from anm.memory.memory_hub import MemoryHub
            assert MemoryHub is not None
            log_test("MemoryHub class imported")
        except Exception as e:
            pytest.fail(f"Failed to import MemoryHub: {e}")

    @pytest.mark.unit
    def test_import_diary_memory(self):
        """Test importing DiaryMemory."""
        log_test("Testing import: DiaryMemory")
        try:
            from anm.memory.diary_memory import DiaryMemory
            assert DiaryMemory is not None
            log_test("DiaryMemory class imported")
        except Exception as e:
            pytest.fail(f"Failed to import DiaryMemory: {e}")


class TestSystemImports:
    """Test system module imports."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_import_inference(self):
        """Test importing inference module."""
        log_test("Testing import: inference")
        try:
            from anm.system import inference
            assert inference is not None
            log_test("inference module imported")
        except Exception as e:
            pytest.fail(f"Failed to import inference: {e}")

    @pytest.mark.unit
    def test_import_hardware(self):
        """Test importing hardware module."""
        log_test("Testing import: hardware")
        try:
            from anm.system import hardware
            assert hardware is not None
            log_test("hardware module imported")
        except Exception as e:
            pytest.fail(f"Failed to import hardware: {e}")


class TestMetacognitionImports:
    """Test metacognition module imports."""

    @pytest.mark.unit
    def test_import_metacognition(self):
        """Test importing metacognition module."""
        log_test("Testing import: metacognition")
        try:
            from anm.metacognition import metacognition
            assert metacognition is not None
            log_test("metacognition module imported")
        except Exception as e:
            pytest.fail(f"Failed to import metacognition: {e}")


class TestRefinerVerifierImports:
    """Test refiner and verifier imports."""

    @pytest.mark.unit
    def test_import_refiner(self):
        """Test importing Refiner."""
        log_test("Testing import: Refiner")
        try:
            from anm.refiner.refiner import Refiner
            assert Refiner is not None
            log_test("Refiner class imported")
        except Exception as e:
            pytest.fail(f"Failed to import Refiner: {e}")

    @pytest.mark.unit
    def test_import_verifier(self):
        """Test importing Verifier."""
        log_test("Testing import: Verifier")
        try:
            from anm.verifier.verifier import Verifier
            assert Verifier is not None
            log_test("Verifier class imported")
        except Exception as e:
            pytest.fail(f"Failed to import Verifier: {e}")
