"""
Unit Tests for ANMConfig
========================
Tests configuration validation and edge cases.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import log_test


class TestANMConfig:
    """Test ANMConfig validation and behavior."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_anm_config_import(self):
        """Test that ANMConfig can be imported."""
        log_test("Testing ANMConfig import...")
        try:
            from anm import ANMConfig
            assert ANMConfig is not None
            log_test("ANMConfig imported successfully")
        except ImportError as e:
            pytest.fail(f"Failed to import ANMConfig: {e}")

    @pytest.mark.unit
    @pytest.mark.critical
    def test_anm_config_default_instantiation(self):
        """Test ANMConfig with default values."""
        log_test("Testing ANMConfig default instantiation...")
        from anm import ANMConfig
        config = ANMConfig()
        assert config is not None
        log_test(f"Default config created: parallel_models={config.parallel_models}")

    @pytest.mark.unit
    def test_anm_config_parallel_models_clamping_low(self):
        """Test that parallel_models < 1 is clamped to 1."""
        log_test("Testing parallel_models clamping (low)...")
        from anm import ANMConfig
        config = ANMConfig(parallel_models=0)
        assert config.parallel_models >= 1, "parallel_models should be clamped to at least 1"
        log_test(f"parallel_models=0 clamped to {config.parallel_models}")

    @pytest.mark.unit
    def test_anm_config_parallel_models_clamping_high(self):
        """Test that parallel_models > 10 is clamped to 10."""
        log_test("Testing parallel_models clamping (high)...")
        from anm import ANMConfig
        config = ANMConfig(parallel_models=100)
        assert config.parallel_models <= 10, "parallel_models should be clamped to at most 10"
        log_test(f"parallel_models=100 clamped to {config.parallel_models}")

    @pytest.mark.unit
    def test_anm_config_quick_mode(self):
        """Test quick_mode configuration."""
        log_test("Testing quick_mode configuration...")
        from anm import ANMConfig
        config = ANMConfig(quick_mode=True)
        assert config.quick_mode == True
        log_test("quick_mode=True set correctly")

    @pytest.mark.unit
    def test_anm_config_research_mode(self):
        """Test research_mode configuration."""
        log_test("Testing research_mode configuration...")
        from anm import ANMConfig
        config = ANMConfig(research_mode=True)
        assert config.research_mode == True
        log_test("research_mode=True set correctly")

    @pytest.mark.unit
    def test_anm_config_auto_mode_default(self):
        """Test that auto_mode is enabled by default."""
        log_test("Testing auto_mode default...")
        from anm import ANMConfig
        config = ANMConfig()
        # auto_mode should be True by default
        assert hasattr(config, 'auto_mode')
        log_test(f"auto_mode default: {config.auto_mode}")

    @pytest.mark.unit
    def test_anm_config_all_attributes_exist(self):
        """Test that all expected attributes exist."""
        log_test("Testing ANMConfig attributes...")
        from anm import ANMConfig
        config = ANMConfig()

        expected_attrs = [
            'parallel_models', 'quick_mode', 'auto_mode', 'research_mode',
            'verbose', 'skip_sanity_check'
        ]

        for attr in expected_attrs:
            assert hasattr(config, attr), f"ANMConfig missing attribute: {attr}"
            log_test(f"  {attr}: {getattr(config, attr)}")

        log_test("All expected attributes present")
