# ANM V0-OpenSource Comprehensive Test Report

**Date:** 2025-12-30
**Test Framework:** pytest 9.0.2
**Python Version:** 3.14.0
**Platform:** macOS Darwin 26.2 (Apple Silicon M-series)

---

## Executive Summary

| Category | Tests Run | Passed | Failed | Success Rate |
|----------|-----------|--------|--------|--------------|
| Unit Tests | 26 | 26 | 0 | **100%** |
| Router Tests | 11 | 11 | 0 | **100%** |
| Memory Tests | 10 | 10 | 0 | **100%** |
| Specialist Tests | 15 | 15 | 0 | **100%** |
| ANM Entry Tests | 12 | 11 | 1 | 92% |
| Stress Tests | 4 | 3 | 1 | 75% |
| **TOTAL** | **78** | **76** | **2** | **97.4%** |

---

## Critical Bugs Found

### BUG #1: Novelty Detector False Positive (CRITICAL)

**Location:** `anm/expansion/core/novelty_detector.py:140-144`

**Description:**
The novelty detector incorrectly flags queries containing "law" as requiring a new "law" (legal) domain specialist, even when "law" refers to physics laws (Newton's law, thermodynamics law, etc.).

**Test Case Failed:**
- `test_anm_query_physics` - "What is Newton's first law?"
- `test_long_query_1000_chars` - Contains "meaning of life"

**Root Cause:**
```python
# Line 140-144 in novelty_detector.py
"law": {
    "keywords": ["law", "legal", "court", "judge", ...],
    "weight": 1.1,
}
```
The keyword "law" matches without context awareness.

**Impact:**
1. VotingHandler.vote() is triggered unnecessarily
2. 8 specialists are polled in parallel (30s timeout each)
3. TimeoutError: 7 (of 8) futures unfinished
4. Query completely fails

**Recommended Fix:**
```python
# Option 1: Add physics exclusion patterns
"law": {
    "keywords": ["law", "legal", "court", ...],
    "exclude_patterns": ["newton", "physics", "first law", "second law",
                         "thermodynamics", "conservation"],
    "weight": 1.1,
}

# Option 2: Add to physics keywords
"physics": {
    "keywords": ["physics", "force", "newton's law", "first law",
                 "second law", "third law", ...],
}

# Option 3: Increase confidence threshold
self.keyword_confidence_threshold = 0.5  # from 0.3

# Option 4: Add exception handling in voting
try:
    voting_result = self.voting_handler.vote(...)
except TimeoutError:
    voting_result = {"majority_yes": False, "skipped": True}
```

---

### BUG #2: ChromaDB Missing (MEDIUM)

**Location:** `anm/memory/vector_store.py:89`

**Description:**
ChromaDB is not installed, causing vector search to be disabled.

**Warning Message:**
```
ChromaDB not available: No module named 'chromadb'. Vector search disabled.
```

**Impact:**
- Semantic memory search unavailable
- Falls back to keyword-only search
- Memory relevance may be degraded

**Fix:**
```bash
pip install chromadb
```

---

### BUG #3: Deprecated datetime.utcnow() (LOW)

**Location:** `anm/utils/logger.py:74`

**Description:**
Using deprecated `datetime.datetime.utcnow()` method.

**Warning:**
```
DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled
for removal in a future version. Use timezone-aware objects to represent
datetimes in UTC: datetime.datetime.now(datetime.UTC).
```

**Fix:**
```python
# Change from:
"iso": datetime.utcnow().isoformat()

# To:
"iso": datetime.now(datetime.UTC).isoformat()
```

---

## Test Results by Module

### Unit Tests (26/26 - 100%)

| Test | Status | Time |
|------|--------|------|
| test_anm_config_import | PASSED | 3.5ms |
| test_anm_config_default_instantiation | PASSED | 0.2ms |
| test_anm_config_parallel_models_clamping_low | PASSED | 0.2ms |
| test_anm_config_parallel_models_clamping_high | PASSED | 0.2ms |
| test_anm_config_quick_mode | PASSED | 0.2ms |
| test_anm_config_research_mode | PASSED | 0.2ms |
| test_anm_config_auto_mode_default | PASSED | 0.1ms |
| test_anm_config_all_attributes_exist | PASSED | 0.4ms |
| test_import_anm_main | PASSED | 0.2ms |
| test_import_anm_class | PASSED | 0.2ms |
| test_import_config_settings | PASSED | 70.6ms |
| test_import_core_types | PASSED | 15.3ms |
| test_import_router | PASSED | 53.7ms |
| test_import_planner_llm | PASSED | 0.2ms |
| test_import_base_specialist | PASSED | 0.2ms |
| test_import_general_llm | PASSED | 0.2ms |
| test_import_math_llm | PASSED | 0.2ms |
| test_import_physics_llm | PASSED | 0.2ms |
| test_import_code_llm | PASSED | 0.2ms |
| test_import_memory_hub | PASSED | 0.2ms |
| test_import_diary_memory | PASSED | 0.2ms |
| test_import_inference | PASSED | 0.2ms |
| test_import_hardware | PASSED | 0.1ms |
| test_import_metacognition | PASSED | 6.8ms |
| test_import_refiner | PASSED | 0.2ms |
| test_import_verifier | PASSED | 0.2ms |

### Router Tests (11/11 - 100%)

| Test | Status | Time |
|------|--------|------|
| test_router_instantiation | PASSED | 48.5ms |
| test_router_with_config | PASSED | 0.6ms |
| test_router_handle_simple_query | PASSED | 26.8s |
| test_router_handle_quick_mode | PASSED | 64.9s |
| test_router_handle_research_mode | PASSED | 90.7s |
| test_router_handle_empty_query | PASSED | 2.4ms |
| test_math_domain_detection | PASSED | 98.5s |
| test_code_domain_detection | PASSED | 92.4s |
| test_physics_domain_detection | PASSED | 62.2s |
| test_router_handles_none_gracefully | PASSED | 1.8ms |
| test_router_handles_special_characters | PASSED | 45.3s |

### Specialist Tests (15/15 - 100%)

| Test | Status | Time |
|------|--------|------|
| test_base_specialist_import | PASSED | 69.0ms |
| test_base_specialist_is_abstract | PASSED | 0.2ms |
| test_general_llm_instantiation | PASSED | 0.2ms |
| test_general_llm_run | PASSED | 3.3s |
| test_math_llm_instantiation | PASSED | 0.9ms |
| test_math_llm_run | PASSED | 22.5s |
| test_physics_llm_instantiation | PASSED | 0.6ms |
| test_physics_llm_run | PASSED | 7.8s |
| test_code_llm_instantiation | PASSED | 0.7ms |
| test_code_llm_run | PASSED | 51.2s |
| test_chemistry_llm_instantiation | PASSED | 0.2ms |
| test_biology_llm_instantiation | PASSED | 0.2ms |
| test_memory_llm_instantiation | PASSED | 0.9ms |
| test_research_llm_instantiation | PASSED | 0.2ms |
| test_wot_request_in_general_output | PASSED | 8.0s |

### Memory Tests (10/10 - 100%)

| Test | Status | Time |
|------|--------|------|
| test_memory_hub_import | PASSED | 8.0ms |
| test_memory_hub_instantiation | PASSED | 1.2ms |
| test_memory_hub_get_context | PASSED | 0.7ms |
| test_memory_hub_build_brief | PASSED | 0.8ms |
| test_diary_memory_import | PASSED | 0.1ms |
| test_diary_memory_instantiation | PASSED | 0.6ms |
| test_diary_memory_log_entry | PASSED | 0.6ms |
| test_diary_memory_query | PASSED | 0.5ms |
| test_episodic_memory_import | PASSED | 0.1ms |
| test_diary_persists_across_instances | PASSED | 0.6ms |

---

## Performance Observations

1. **Model Loading Time:** ~0.6-1.0 seconds per model load
2. **Simple Query (Hello):** ~24 seconds
3. **Math Query:** ~45 seconds
4. **Code Query:** ~36-51 seconds
5. **Research Mode Query:** ~90 seconds
6. **Specialist .run():** 3-51 seconds depending on complexity

---

## Recommendations

### Immediate Fixes (Priority 1)

1. **Fix Novelty Detector False Positives**
   - Add context-aware keyword matching
   - Add exclude patterns for physics terms in "law" domain
   - Add try/except around voting with graceful fallback

2. **Install ChromaDB**
   - `pip install chromadb`
   - Enable vector-based semantic search

### Short-term Improvements (Priority 2)

1. **Increase Voting Timeout or Add Graceful Handling**
   - Current: 30 seconds
   - Recommended: 60 seconds OR catch TimeoutError and skip voting

2. **Fix Deprecated datetime.utcnow()**
   - Replace with timezone-aware datetime

### Long-term Improvements (Priority 3)

1. **Add More Test Coverage**
   - WoT Engine modes (beam search, consensus, metacognitive)
   - Expansion pipeline
   - Voice I/O (if available)

2. **Performance Optimization**
   - Model caching improvements
   - Parallel specialist execution optimization

---

## Test Files Created

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── pytest.ini                     # Configuration
├── unit/
│   ├── __init__.py
│   ├── test_anm_config.py        # 8 tests
│   └── test_imports.py           # 18 tests
├── integration/
│   ├── __init__.py
│   ├── test_anm_entry.py         # 12 tests
│   ├── test_router.py            # 11 tests
│   ├── test_specialists.py       # 15 tests
│   └── test_memory.py            # 10 tests
├── domains/
│   ├── __init__.py
│   └── test_domain_queries.py    # Domain tests
├── stress/
│   ├── __init__.py
│   └── test_edge_cases.py        # 14 tests
├── modes/
│   └── __init__.py
├── errors/
│   └── __init__.py
└── fixtures/
    └── __init__.py
```

---

## Running Tests

```bash
# Run all tests
python run_tests.py

# Run unit tests only
python -m pytest tests/unit/ -v

# Run integration tests
python -m pytest tests/integration/ -v

# Run with HTML report
python -m pytest tests/ --html=test_reports/report.html --self-contained-html
```

---

**Report Generated:** 2025-12-30 22:30:00 UTC
**Total Test Duration:** ~20 minutes
