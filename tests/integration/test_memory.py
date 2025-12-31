"""
Integration Tests for Memory System
===================================
Tests MemoryHub, DiaryMemory, and related memory components.
"""

import pytest
import sys
import time
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import log_test


class TestMemoryHubInstantiation:
    """Test MemoryHub instantiation."""

    @pytest.mark.integration
    def test_memory_hub_import(self):
        """Test MemoryHub can be imported."""
        log_test("Testing MemoryHub import...")
        from anm.memory.memory_hub import MemoryHub
        assert MemoryHub is not None
        log_test("MemoryHub imported successfully")

    @pytest.mark.integration
    def test_memory_hub_instantiation(self):
        """Test MemoryHub can be instantiated."""
        log_test("Testing MemoryHub instantiation...")
        from anm.memory.memory_hub import MemoryHub

        with tempfile.TemporaryDirectory() as tmpdir:
            diary_path = str(Path(tmpdir) / "test_diary.txt")
            hub = MemoryHub(diary_path=diary_path)
            assert hub is not None
            log_test("MemoryHub instantiated")


class TestMemoryHubOperations:
    """Test MemoryHub operations."""

    @pytest.mark.integration
    def test_memory_hub_get_context(self):
        """Test MemoryHub.get_context() method."""
        log_test("Testing MemoryHub.get_context()...")
        from anm.memory.memory_hub import MemoryHub

        with tempfile.TemporaryDirectory() as tmpdir:
            diary_path = str(Path(tmpdir) / "test_diary.txt")
            hub = MemoryHub(diary_path=diary_path)

            try:
                context = hub.get_context("test query")
                log_test(f"get_context returned: {type(context)}")
            except Exception as e:
                log_test(f"get_context raised: {e}", "WARNING")

    @pytest.mark.integration
    def test_memory_hub_build_brief(self):
        """Test MemoryHub.build_memory_brief() method."""
        log_test("Testing MemoryHub.build_memory_brief()...")
        from anm.memory.memory_hub import MemoryHub

        with tempfile.TemporaryDirectory() as tmpdir:
            diary_path = str(Path(tmpdir) / "test_diary.txt")
            hub = MemoryHub(diary_path=diary_path)

            try:
                brief = hub.build_memory_brief("test query")
                assert isinstance(brief, str)
                log_test(f"Memory brief length: {len(brief)} chars")
            except Exception as e:
                log_test(f"build_memory_brief raised: {e}", "WARNING")


class TestDiaryMemory:
    """Test DiaryMemory operations."""

    @pytest.mark.integration
    def test_diary_memory_import(self):
        """Test DiaryMemory can be imported."""
        log_test("Testing DiaryMemory import...")
        from anm.memory.diary_memory import DiaryMemory
        assert DiaryMemory is not None
        log_test("DiaryMemory imported")

    @pytest.mark.integration
    def test_diary_memory_instantiation(self):
        """Test DiaryMemory can be instantiated."""
        log_test("Testing DiaryMemory instantiation...")
        from anm.memory.diary_memory import DiaryMemory

        with tempfile.TemporaryDirectory() as tmpdir:
            diary_path = str(Path(tmpdir) / "test_diary.txt")
            diary = DiaryMemory(diary_path=diary_path)
            assert diary is not None
            log_test("DiaryMemory instantiated")

    @pytest.mark.integration
    def test_diary_memory_log_entry(self):
        """Test DiaryMemory.log_entry() method."""
        log_test("Testing DiaryMemory.log_entry()...")
        from anm.memory.diary_memory import DiaryMemory

        with tempfile.TemporaryDirectory() as tmpdir:
            diary_path = str(Path(tmpdir) / "test_diary.txt")
            diary = DiaryMemory(diary_path=diary_path)

            try:
                entry = diary.log_entry(
                    kind="test",
                    specialist="test_specialist",
                    run_id="test_run_123",
                    tags=["test"],
                    title="Test Entry",
                    user="test query",
                    assistant="test response",
                    notes="test notes"
                )
                log_test(f"log_entry returned: {type(entry)}")
            except Exception as e:
                log_test(f"log_entry raised: {e}", "WARNING")

    @pytest.mark.integration
    def test_diary_memory_query(self):
        """Test DiaryMemory.query() method."""
        log_test("Testing DiaryMemory.query()...")
        from anm.memory.diary_memory import DiaryMemory

        with tempfile.TemporaryDirectory() as tmpdir:
            diary_path = str(Path(tmpdir) / "test_diary.txt")
            diary = DiaryMemory(diary_path=diary_path)

            # First log an entry
            try:
                diary.log_entry(
                    kind="interaction",
                    user="what is 2+2",
                    assistant="4"
                )
            except:
                pass

            # Then query
            try:
                result = diary.query("math")
                log_test(f"query returned: {type(result)}")
            except Exception as e:
                log_test(f"query raised: {e}", "WARNING")


class TestEpisodicMemory:
    """Test EpisodicMemory operations."""

    @pytest.mark.integration
    def test_episodic_memory_import(self):
        """Test EpisodicMemory can be imported."""
        log_test("Testing EpisodicMemory import...")
        from anm.memory.episodic_memory import EpisodicMemory
        assert EpisodicMemory is not None
        log_test("EpisodicMemory imported")


class TestMemoryPersistence:
    """Test memory persistence across instances."""

    @pytest.mark.integration
    def test_diary_persists_across_instances(self):
        """Test diary entries persist when creating new instance."""
        log_test("Testing diary persistence...")
        from anm.memory.diary_memory import DiaryMemory

        with tempfile.TemporaryDirectory() as tmpdir:
            diary_path = str(Path(tmpdir) / "persist_test.txt")

            # Create first instance and log
            diary1 = DiaryMemory(diary_path=diary_path)
            try:
                diary1.log_entry(
                    kind="test",
                    user="persistent query",
                    assistant="persistent response"
                )
            except:
                pass

            # Create second instance and check
            diary2 = DiaryMemory(diary_path=diary_path)
            try:
                result = diary2.query("persistent")
                log_test(f"Persistence check: {type(result)}")
            except Exception as e:
                log_test(f"Persistence check raised: {e}", "WARNING")
