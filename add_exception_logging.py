#!/usr/bin/env python3
"""
Script to add logging to silent exception handlers.
Part of ANM V0-OpenSource Phase 4 - Quality Improvements.

This script adds appropriate logging to exception handlers that
currently catch exceptions but don't log them.
"""

import re
from pathlib import Path
from typing import List, Tuple


def add_import_if_missing(content: str, file_path: str) -> str:
    """Add logging import if not already present."""
    if "import logging" in content:
        return content

    lines = content.split('\n')
    insert_index = 0

    # Find where to insert the import
    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            insert_index = i + 1
        elif insert_index > 0 and not line.strip().startswith(('from ', 'import ', '#')):
            break

    if insert_index > 0:
        lines.insert(insert_index, 'import logging')
        return '\n'.join(lines)

    # No imports found, add after docstring
    in_docstring = False
    for i, line in enumerate(lines):
        if '"""' in line or "'''" in line:
            in_docstring = not in_docstring
            if not in_docstring:
                lines.insert(i + 1, '')
                lines.insert(i + 2, 'import logging')
                return '\n'.join(lines)

    return content


def add_logging_to_silent_handlers(content: str, file_path: str) -> Tuple[str, int]:
    """
    Add logging to silent exception handlers.

    Patterns to fix:
    1. except Exception:\n        pass
    2. except Exception as e:\n        pass
    3. except (Exception1, Exception2):\n        pass
    """
    count = 0
    lines = content.split('\n')
    modified_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        modified_lines.append(line)

        # Check if this is an except line
        if line.strip().startswith('except ') and line.strip().endswith(':'):
            # Look ahead to see if next line is just "pass"
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                indent = len(next_line) - len(next_line.lstrip())

                if next_line.strip() == 'pass':
                    # Check if exception has 'as e' clause
                    has_as_clause = ' as ' in line

                    # Remove the pass line
                    i += 1  # Skip the pass line

                    # Add logging instead
                    if has_as_clause:
                        # Extract variable name
                        match = re.search(r' as (\w+):', line)
                        if match:
                            var_name = match.group(1)
                            log_line = f'{" " * indent}logging.warning(f"Exception in {Path(file_path).stem}: {{{var_name}}}")'
                        else:
                            log_line = f'{" " * indent}logging.warning("Exception occurred but not logged")'
                    else:
                        # No 'as' clause, need to add one
                        # Modify the except line
                        modified_lines[-1] = line.rstrip(':') + ' as e:'
                        log_line = f'{" " * indent}logging.warning(f"Exception in {Path(file_path).stem}: {{e}}")'

                    modified_lines.append(log_line)
                    count += 1

        i += 1

    return '\n'.join(modified_lines), count


FILES_TO_PROCESS = [
    "anm/system/hardware.py",
    "anm/expansion/device_awareness.py",
    "anm/memory/memory_hub.py",
    "anm/memory/learning_engine.py",
    "anm/sim/engine.py",
    "anm/system/platform.py",
]


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

    # Add import if needed
    original_content = content
    content = add_import_if_missing(content, file_path)

    # Add logging to silent handlers
    new_content, count = add_logging_to_silent_handlers(content, file_path)

    if new_content != original_content:
        # Write back
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ✓ Added logging to {count} exception handlers")
    else:
        print(f"  ✓ No changes needed")


def main():
    """Main function."""
    print("=" * 60)
    print("ANM V0-OpenSource - Add Exception Logging")
    print("Phase 4: Quality Improvements")
    print("=" * 60)
    print()

    total_processed = 0

    for file_path in FILES_TO_PROCESS:
        process_file(file_path)
        total_processed += 1
        print()

    print("=" * 60)
    print(f"✓ Processed {total_processed} files")
    print("=" * 60)


if __name__ == "__main__":
    main()
