# Error Fixing Plan - ANM V0-OpenSource

## Executive Summary
This plan outlines fixes for **26 identified bugs** in the ANM V0-OpenSource codebase. Bugs are categorized by severity and organized by module for systematic resolution.

**Status**: Ready for Implementation
**Exception Handling**: Keep existing (no changes to silent except blocks)
**Approach**: Module-by-module fixes with incremental testing

---

## Bug Statistics

| Severity | Count | Impact |
|----------|-------|--------|
| **Critical** | 3 | System-breaking, unreachable code |
| **High** | 4 | Runtime errors, crashes |
| **Medium** | 17 | Data flow issues, integration problems |
| **Low** | 2 | Logic improvements, edge cases |
| **TOTAL** | **26** | |

---

## Critical Bugs (Fix Immediately)

### BUG-001: Unreachable Code in Novelty Detector
**File**: `anm/expansion/core/novelty_detector.py`
**Lines**: 289-320
**Severity**: 🔴 CRITICAL

**Problem**:
```python
def _embedding_detection(self, query: str, memory_brief: str) -> Optional[NoveltyResult]:
    try:
        # ... code ...
    except (AttributeError, ImportError, ModuleNotFoundError) as e:
        # Handle NumPy/pyarrow compatibility issues
        return None  # ⚠️ EARLY RETURN - Lines 294-318 become UNREACHABLE

        # Compare with domain embeddings  <-- NEVER EXECUTED
        domain_similarities: Dict[str, float] = {}
        for domain_name, domain_embedding in self.domain_embeddings.items():
            # ... 25 lines of core logic that never runs ...
```

**Impact**: Embedding-based novelty detection ALWAYS fails, falling back to keyword-only detection. This severely degrades the system's ability to detect novel domains.

**Fix**:
1. Remove the early `return None` at line 292
2. Replace with logging: `self._logger.warning(f"Embedding module unavailable: {e}")`
3. Continue to embedding comparison logic
4. Return proper NoveltyResult or None after logic completes

---

### BUG-002: Unreachable Code in Refiner Fallback
**File**: `anm/refiner/refiner.py`
**Lines**: 836-874
**Severity**: 🔴 CRITICAL

**Problem**:
```python
def _fallback_compose(self, packet: Dict[str, Any]) -> str:
    # Lines 797-836: Build parts list
    parts = []
    # ... code that builds parts ...

def _clean_malformed_instructions(self, text: str) -> str:  # Line 837 - NEW FUNCTION
    """Clean malformed WOT_REQUEST and other instruction markers."""
    # ... cleaning logic ...

    # Lines 867-874 are inside _clean_malformed_instructions but reference
    # variables from _fallback_compose - UNREACHABLE/WRONG SCOPE
    if parts:  # ⚠️ 'parts' doesn't exist in this function!
        answer = "\n\n".join(parts)
    else:
        answer = "[Refiner fallback: no valid specialist output]"

    return answer
```

**Impact**: The `_fallback_compose` function never properly assembles the final answer. It builds the `parts` list but never joins them into the final output. Fallback composition completely fails.

**Fix**:
1. Move lines 867-874 back into `_fallback_compose` before it ends
2. Ensure proper indentation so final assembly is reachable
3. `_clean_malformed_instructions` should remain a separate function but not contain the assembly logic

---

### BUG-003: UnboundLocalError in Verifier Adaptive Fallback
**File**: `anm/verifier/verifier.py`
**Lines**: 571-627
**Severity**: 🔴 CRITICAL

**Problem**:
```python
def _adaptive_fallback(self, packet: str, ...) -> Dict[str, Any]:
    # ... analyze question and answer ...

    if expects_short_answer:
        # Path 1: Sets status, notes, all_issues in various branches
        if question_analysis["query_type"] == "calculation":
            status = "approved"
            notes = "..."
            all_issues = [...]
        elif answer_analysis["has_answer"]:
            # ... sets variables
        else:
            # ... sets variables
    else:
        # Path 2: Different logic
        fallback_issues = []  # Line 572
        original_fallback = None  # Line 573

        if question_analysis["query_type"] == "code":
            # ... may or may not set status, notes, all_issues
        else:
            # ... uses original_fallback but might not set status/notes

    # Line 614 - ⚠️ Variables may be unbound!
    all_issues = list(set(issues + fallback_issues))  # fallback_issues unbound in Path 1

    return {
        "status": status,  # ⚠️ May be unbound
        "notes": notes,    # ⚠️ May be unbound
        # ...
    }
```

**Impact**: UnboundLocalError crashes the verifier when processing certain query types. Different code paths leave variables undefined.

**Fix**:
Initialize ALL variables at the start of the function:
```python
def _adaptive_fallback(self, packet: str, ...) -> Dict[str, Any]:
    # Initialize all variables upfront
    fallback_issues = []
    original_fallback = None
    status = "approved"
    notes = ""
    all_issues = []

    # ... rest of logic ...
```

---

## High Severity Bugs

### BUG-004: Hardcoded Absolute Paths
**File**: `anm/refiner/refiner.py`
**Lines**: 142, 281, 602, 617, 952
**Severity**: 🟠 HIGH

**Problem**:
```python
with open("/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log", "a") as f:
```

**Impact**: Code fails on any other system or user account. Not portable.

**Fix**:
Replace with relative path:
```python
import os
debug_log = os.path.join(os.getcwd(), ".cursor", "debug.log")
os.makedirs(os.path.dirname(debug_log), exist_ok=True)
with open(debug_log, "a") as f:
```

---

### BUG-005: Missing Import
**File**: `anm/refiner/refiner.py`
**Line**: 143
**Severity**: 🟠 HIGH

**Problem**:
```python
"timestamp": int(time.time() * 1000)  # time module not imported!
```

**Impact**: NameError when agent logging triggers.

**Fix**:
Add to imports at top of file:
```python
import time
```

---

### BUG-006: Potential KeyError in Verifier Fallback
**File**: `anm/verifier/verifier.py`
**Lines**: 897-936
**Severity**: 🟠 HIGH

**Problem**:
```python
if merged_match:
    merged_text = merged_match.group(1).strip()
    query_match = re.search(r"user query:...", packet, re.IGNORECASE)
    if query_match:
        user_query = query_match.group(1).lower()
        merged_lower = merged_text.lower()

        # ... later ...
        if len(merged_clean) < 100:  # ⚠️ merged_clean may not exist!
```

**Impact**: NameError when merged_match path doesn't define merged_clean.

**Fix**:
Initialize `merged_clean = ""` before the conditional blocks.

---

### BUG-007: Missing WoT Engine File Reference
**Severity**: 🟠 HIGH

**Problem**: Code references `anm/wot/wot_engine.py` but file may not exist.

**Fix**:
Create the file or update imports to handle ImportError gracefully.

---

## Medium Severity Bugs

### BUG-008: Division by Zero
**File**: `anm/expansion/core/novelty_detector.py`
**Line**: 538
**Severity**: 🟡 MEDIUM

**Problem**:
```python
embedding[idx] += 1.0 / len(words)  # Fails if words is empty
```

**Fix**:
```python
if len(words) > 0:
    embedding[idx] += 1.0 / len(words)
```

---

### BUG-009: Race Condition in Singleton
**File**: `anm/core/memory_optimizer.py`
**Lines**: 326-340
**Severity**: 🟡 MEDIUM

**Problem**: Double-checked locking not thread-safe in Python.

**Fix**: Use module-level instance or proper threading lock pattern.

---

### BUG-010: Inefficient Memory Info Access
**File**: `anm/core/memory_optimizer.py`
**Line**: 166
**Severity**: 🟡 MEDIUM

**Problem**:
```python
return process.memory_info().peak_wss / 1024 / 1024 if hasattr(process.memory_info(), 'peak_wss') else 0.0
```

**Fix**:
```python
mem_info = process.memory_info()
return mem_info.peak_wss / 1024 / 1024 if hasattr(mem_info, 'peak_wss') else 0.0
```

---

### BUG-011 to BUG-024: Additional Medium Severity Issues
*(See full bug report in main plan file for details)*

- Missing None checks before string operations
- Inconsistent error handling (bare except)
- Potential NoneType iteration
- Missing type validation
- Inconsistent return types
- File handle cleanup issues
- Memory leak in monitor loop
- Router-specialist communication gaps
- Verifier complexity issues

---

## Low Severity Bugs

### BUG-025: Incorrect Confidence Calculation
**File**: `anm/refiner/refiner.py`
**Lines**: 1002-1025
**Severity**: 🟢 LOW

**Problem**: Confidence can exceed 1.0 before clamping.

**Fix**: Use multiplicative factors or cap during calculation.

---

### BUG-026: String Cleaning Edge Case
**File**: `anm/refiner/refiner.py`
**Lines**: 1116-1118
**Severity**: 🟢 LOW

**Problem**:
```python
answer = re.sub(r'\s*\.\s*$', '', answer)  # Removes ALL trailing periods
# "The answer is 3.14" → "The answer is 3"
```

**Fix**: Only remove standalone periods, not those in numbers.

---

## Implementation Plan

### Phase 1: Critical Fixes (Priority 1)
**Estimated Time**: 2-3 hours
**Files**: 3 files

1. ✅ Fix BUG-001: Novelty detector unreachable code
2. ✅ Fix BUG-002: Refiner fallback unreachable code
3. ✅ Fix BUG-003: Verifier unbound variables

**Testing**: Run novelty detection, refiner fallback, and verifier with various query types

---

### Phase 2: High Severity Fixes (Priority 2)
**Estimated Time**: 1-2 hours
**Files**: 2 files

4. ✅ Fix BUG-004: Remove hardcoded paths
5. ✅ Fix BUG-005: Add missing import
6. ✅ Fix BUG-006: Fix verifier KeyError
7. ✅ Fix BUG-007: Handle missing WoT engine

**Testing**: Run full system on different user accounts, test all verifier paths

---

### Phase 3: Medium Severity Fixes (Priority 3)
**Estimated Time**: 3-4 hours
**Files**: 5 files

8. ✅ Fix division by zero (BUG-008)
9. ✅ Fix singleton race condition (BUG-009)
10. ✅ Fix inefficient memory access (BUG-010)
11. ✅ Add None checks throughout
12. ✅ Fix bare except clauses
13. ✅ Fix memory leaks
14. ✅ Improve type validation

**Testing**: Long-running tests, concurrent access tests, memory profiling

---

### Phase 4: Low Severity Fixes (Priority 4)
**Estimated Time**: 1 hour
**Files**: 1 file

15. ✅ Improve confidence calculation (BUG-025)
16. ✅ Fix string cleaning (BUG-026)

**Testing**: Unit tests for edge cases

---

## Testing Strategy

### Unit Tests
- Test each fixed function independently
- Focus on edge cases that triggered bugs
- Mock dependencies to isolate issues

### Integration Tests
- Test novelty detection → voting → expansion flow
- Test router → specialists → refiner → verifier flow
- Test memory system under load

### Regression Tests
- Ensure fixes don't break existing functionality
- Run full test suite after each phase
- Compare outputs before/after fixes

### Manual Tests
1. Run queries that trigger novelty detection
2. Test verifier with various query types (calculation, code, explanation)
3. Test refiner fallback with malformed specialist outputs
4. Test on different systems/user accounts (portability)
5. Run long sessions to check for memory leaks

---

## Files to Modify

### Critical Files (Phase 1)
1. `anm/expansion/core/novelty_detector.py` - Fix unreachable embedding logic
2. `anm/refiner/refiner.py` - Fix unreachable fallback assembly
3. `anm/verifier/verifier.py` - Fix unbound variables

### High Priority Files (Phase 2)
4. `anm/refiner/refiner.py` - Remove hardcoded paths, add import
5. `anm/verifier/verifier.py` - Fix KeyError risks
6. `anm/wot/wot_engine.py` - Create or handle missing file

### Medium Priority Files (Phase 3)
7. `anm/core/memory_optimizer.py` - Fix race condition, memory leak
8. `anm/expansion/core/novelty_detector.py` - Fix division by zero
9. `anm/prompt_optimizer.py` - Fix return type issues

---

## Rollback Plan

If any fixes cause issues:
1. Git commit after each phase for easy rollback
2. Keep original code in comments temporarily
3. Have backup of critical files before changes
4. Test each phase independently before moving to next

---

## Success Criteria

✅ **All 3 critical bugs fixed** - No unreachable code, no unbound variables
✅ **All 4 high severity bugs fixed** - No hardcoded paths, all imports present
✅ **System runs without crashes** - Can handle all query types
✅ **Tests pass** - Unit, integration, and regression tests succeed
✅ **Portability verified** - Works on different systems/accounts
✅ **No memory leaks** - Long-running sessions stable

---

## Notes

- **Exception handling**: Keeping existing `except: pass` blocks as requested
- **Testing**: Manual testing required for unreachable code fixes
- **Priority**: Focus on critical and high severity first
- **Incremental**: Fix and test one module at a time
- **Documentation**: Update comments for fixed code sections

---

## Next Steps

1. Review this plan
2. Confirm fix priority and approach
3. Begin Phase 1: Critical fixes
4. Test after each phase
5. Move to next phase only after validation

---

**Total Estimated Time**: 7-10 hours for all phases
**Minimum Viable Fix**: Phase 1 + Phase 2 (3-5 hours)
