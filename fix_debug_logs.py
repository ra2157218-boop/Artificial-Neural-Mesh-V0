#!/usr/bin/env python3
"""
Script to replace hardcoded debug log paths with centralized debug logger.
Part of ANM V0-OpenSource Phase 1 remediation.
"""

import re
import os
from pathlib import Path

# Files to process (remaining files with hardcoded paths)
FILES_TO_PROCESS = [
    "anm/router/planner_llm.py",
    "anm/system/inference.py",
    "anm/verifier/verifier.py",
    "anm/memory/diary_memory.py",
    "anm/refiner/refiner.py",
    "anm/specialists/base.py",
    "anm/specialists/memory_llm.py",
    "anm/__init__.py",
]

HARDCODED_PATH = '"/Users/syedabdurrehman/ANM V0-OpenSource/.cursor/debug.log"'

def add_import_if_missing(content: str, file_path: str) -> str:
    """Add debug logger import if not already present."""
    import_line = "from anm.utils.debug_logger import log_debug"

    if import_line in content:
        return content

    # Find where to insert the import
    # Look for existing imports
    lines = content.split('\n')
    insert_index = 0

    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            insert_index = i + 1
        elif insert_index > 0 and not line.strip().startswith(('from ', 'import ', '#')):
            # Found end of import block
            break

    # Insert the import
    if insert_index > 0:
        lines.insert(insert_index, import_line)
        return '\n'.join(lines)
    else:
        # No imports found, add after docstring/comments
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('#') and '"""' not in line and "'''" not in line:
                lines.insert(i, import_line)
                lines.insert(i, '')
                return '\n'.join(lines)

    return content

def replace_debug_logs(content: str) -> tuple[str, int]:
    """Replace hardcoded debug log writes with log_debug() calls."""
    count = 0

    # Pattern 1: Simple write (single line)
    pattern1 = r'with open\(' + re.escape(HARDCODED_PATH) + r', "a"\) as f:\s*\n\s*f\.write\(json\.dumps\(([^)]+)\) \+ "\\n"\)'

    def replace1(match):
        nonlocal count
        count += 1
        data = match.group(1)
        return f'log_debug({data})'

    content = re.sub(pattern1, replace1, content)

    # Pattern 2: Multi-line with proper indentation
    pattern2 = r'(\s*)with open\(' + re.escape(HARDCODED_PATH) + r', "a"\) as f:\s*\n\s*f\.write\(json\.dumps\((.+?)\) \+ "\\n"\)'

    def replace2(match):
        nonlocal count
        count += 1
        indent = match.group(1)
        data = match.group(2)
        return f'{indent}log_debug({data})'

    content = re.sub(pattern2, replace2, content, flags=re.DOTALL)

    # Replace bare except: pass with proper exception handling
    content = re.sub(
        r'except:\s*pass\s*\n\s*# #endregion',
        r'except Exception as e:\n                logging.warning(f"Debug logging failed: {e}")\n            # #endregion',
        content
    )

    # Also fix standalone except: pass near debug logs
    content = re.sub(
        r'(\s+)except:\s*pass(\s*\n\s*# #endregion)',
        r'\1except Exception as e:\n\1    logging.warning(f"Debug logging failed: {e}")\2',
        content
    )

    return content, count

def add_logging_import_if_missing(content: str) -> str:
    """Add logging import if not present."""
    if 'import logging' not in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                # Add after first import
                if 'import logging' not in lines[i]:
                    lines.insert(i + 1, 'import logging')
                    return '\n'.join(lines)
    return content

def process_file(file_path: str) -> None:
    """Process a single file."""
    full_path = Path(file_path)

    if not full_path.exists():
        print(f"❌ File not found: {file_path}")
        return

    print(f"Processing: {file_path}")

    # Read file
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if file has hardcoded paths
    if HARDCODED_PATH not in content:
        print(f"  ✓ No hardcoded paths found")
        return

    # Add imports
    content = add_import_if_missing(content, file_path)
    content = add_logging_import_if_missing(content)

    # Replace debug logs
    new_content, count = replace_debug_logs(content)

    if count > 0:
        # Write back
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ✓ Replaced {count} hardcoded debug log calls")
    else:
        print(f"  ⚠ No replacements made (pattern mismatch)")

def main():
    """Main function."""
    print("="* 60)
    print("ANM V0-OpenSource - Debug Log Path Replacement")
    print("Phase 1: Critical Fixes")
    print("="* 60)
    print()

    total_processed = 0

    for file_path in FILES_TO_PROCESS:
        process_file(file_path)
        total_processed += 1
        print()

    print("="* 60)
    print(f"✓ Processed {total_processed} files")
    print("="* 60)

if __name__ == "__main__":
    main()
