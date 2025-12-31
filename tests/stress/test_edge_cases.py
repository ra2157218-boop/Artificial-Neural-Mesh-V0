"""
Stress Tests and Edge Cases
===========================
Tests edge cases, malformed inputs, and stress scenarios.
"""

import pytest
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.conftest import log_test, assert_valid_result


class TestEmptyInputs:
    """Test empty and whitespace inputs."""

    @pytest.mark.stress
    @pytest.mark.critical
    def test_empty_string_query(self, anm_instance):
        """Test empty string query."""
        log_test("Testing empty string query...")
        result = anm_instance.query("")

        assert isinstance(result, dict)
        log_test(f"Empty string result: {result}")

    @pytest.mark.stress
    def test_whitespace_only_query(self, anm_instance):
        """Test whitespace-only query."""
        log_test("Testing whitespace-only query...")
        result = anm_instance.query("   \t\n   ")

        assert isinstance(result, dict)
        log_test(f"Whitespace result: {result}")

    @pytest.mark.stress
    def test_none_handling(self, anm_instance):
        """Test None input handling."""
        log_test("Testing None input...")
        try:
            result = anm_instance.query(None)
            log_test(f"None input result: {result}")
        except TypeError as e:
            log_test(f"None raised TypeError (expected): {e}")
        except Exception as e:
            log_test(f"None raised {type(e).__name__}: {e}")


class TestLongInputs:
    """Test very long inputs."""

    @pytest.mark.stress
    @pytest.mark.timeout(300)
    def test_long_query_1000_chars(self, anm_instance):
        """Test query with 1000 characters."""
        log_test("Testing 1000 char query...")
        long_query = "What is " + "the meaning of life " * 50  # ~1000 chars

        start = time.time()
        result = anm_instance.query(long_query)
        duration = (time.time() - start) * 1000

        assert isinstance(result, dict)
        log_test(f"1000 char query completed in {duration:.1f}ms")

    @pytest.mark.stress
    @pytest.mark.timeout(300)
    @pytest.mark.slow
    def test_long_query_5000_chars(self, anm_instance):
        """Test query with 5000 characters."""
        log_test("Testing 5000 char query...")
        long_query = "Explain in detail " + "the concept of " * 250  # ~5000 chars

        start = time.time()
        result = anm_instance.query(long_query)
        duration = (time.time() - start) * 1000

        assert isinstance(result, dict)
        log_test(f"5000 char query completed in {duration:.1f}ms")


class TestSpecialCharacters:
    """Test special characters and potential injection."""

    @pytest.mark.stress
    @pytest.mark.timeout(180)
    def test_special_characters_basic(self, anm_instance):
        """Test basic special characters."""
        log_test("Testing special characters...")
        special_query = "What is !@#$%^&*()?"

        result = anm_instance.query(special_query)
        assert isinstance(result, dict)
        log_test(f"Special chars result type: {type(result)}")

    @pytest.mark.stress
    @pytest.mark.timeout(180)
    def test_unicode_characters(self, anm_instance):
        """Test unicode characters."""
        log_test("Testing unicode characters...")
        unicode_query = "What is the meaning of 你好世界?"

        result = anm_instance.query(unicode_query)
        assert isinstance(result, dict)
        log_test(f"Unicode result type: {type(result)}")

    @pytest.mark.stress
    @pytest.mark.timeout(180)
    def test_emoji_characters(self, anm_instance):
        """Test emoji characters."""
        log_test("Testing emoji characters...")
        emoji_query = "What does 🎉🎊🎁 mean?"

        result = anm_instance.query(emoji_query)
        assert isinstance(result, dict)
        log_test(f"Emoji result type: {type(result)}")

    @pytest.mark.stress
    def test_sql_like_input(self, anm_instance):
        """Test SQL-like input (not a real threat but edge case)."""
        log_test("Testing SQL-like input...")
        sql_query = "SELECT * FROM users WHERE name = 'test'"

        result = anm_instance.query(sql_query)
        assert isinstance(result, dict)
        log_test(f"SQL-like result: {type(result)}")

    @pytest.mark.stress
    def test_html_like_input(self, anm_instance):
        """Test HTML-like input."""
        log_test("Testing HTML-like input...")
        html_query = "<script>alert('test')</script> What is this?"

        result = anm_instance.query(html_query)
        assert isinstance(result, dict)
        log_test(f"HTML-like result: {type(result)}")


class TestRepeatedCharacters:
    """Test repeated character inputs."""

    @pytest.mark.stress
    @pytest.mark.timeout(180)
    def test_repeated_letters(self, anm_instance):
        """Test repeated letters."""
        log_test("Testing repeated letters...")
        repeated = "a" * 500

        result = anm_instance.query(repeated)
        assert isinstance(result, dict)
        log_test(f"Repeated letters result: {type(result)}")

    @pytest.mark.stress
    @pytest.mark.timeout(180)
    def test_repeated_question_marks(self, anm_instance):
        """Test repeated question marks."""
        log_test("Testing repeated question marks...")
        repeated = "What" + "?" * 100

        result = anm_instance.query(repeated)
        assert isinstance(result, dict)
        log_test(f"Repeated ? result: {type(result)}")


class TestMultipleQueries:
    """Test multiple sequential queries."""

    @pytest.mark.stress
    @pytest.mark.timeout(600)
    @pytest.mark.slow
    def test_10_sequential_queries(self, anm_instance):
        """Test 10 sequential queries."""
        log_test("Testing 10 sequential queries...")

        queries = [
            "What is 2+2?",
            "Hello",
            "What is Python?",
            "Explain gravity",
            "Write hello world",
            "What is DNA?",
            "What is H2O?",
            "What is AI?",
            "Solve x=5",
            "What is energy?",
        ]

        results = []
        total_time = 0

        for i, q in enumerate(queries):
            start = time.time()
            result = anm_instance.query(q)
            duration = (time.time() - start) * 1000
            total_time += duration

            results.append(result)
            log_test(f"Query {i+1}/10 completed in {duration:.1f}ms")

        success_count = sum(1 for r in results if r.get("status") != "error")
        log_test(f"Sequential queries: {success_count}/10 successful, total time: {total_time:.1f}ms")


class TestRapidSuccession:
    """Test queries in rapid succession."""

    @pytest.mark.stress
    @pytest.mark.timeout(300)
    def test_rapid_queries(self, anm_instance):
        """Test 5 queries in rapid succession."""
        log_test("Testing rapid succession queries...")

        queries = ["Hi", "Hello", "Hey", "Greetings", "Howdy"]
        results = []

        start = time.time()
        for q in queries:
            result = anm_instance.query(q)
            results.append(result)
        total = (time.time() - start) * 1000

        success_count = sum(1 for r in results if isinstance(r, dict))
        log_test(f"Rapid queries: {success_count}/5 successful in {total:.1f}ms total")
