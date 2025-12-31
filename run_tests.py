#!/usr/bin/env python3
"""
ANM V0-OpenSource Test Runner
=============================
Comprehensive test runner with HTML report and console output.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py --unit       # Run unit tests only
    python run_tests.py --quick      # Run quick tests (no slow markers)
    python run_tests.py --critical   # Run critical tests only
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime


# Colors for console output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_fail(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text):
    print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")


def setup_directories():
    """Create necessary directories."""
    dirs = [
        Path("test_reports"),
        Path("tests/unit"),
        Path("tests/integration"),
        Path("tests/domains"),
        Path("tests/stress"),
        Path("tests/errors"),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def run_tests(args=None):
    """Run pytest with the specified arguments."""
    if args is None:
        args = []

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_report = f"test_reports/report_{timestamp}.html"

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        f"--html={html_report}",
        "--self-contained-html",
        "--timeout=180",
    ] + args

    print_header("ANM V0-OpenSource Test Suite")
    print_info(f"Python: {sys.version.split()[0]}")
    print_info(f"Working directory: {os.getcwd()}")
    print_info(f"HTML report: {html_report}")
    print_info(f"Command: {' '.join(cmd)}")
    print()

    start_time = time.time()

    # Run pytest
    result = subprocess.run(cmd, capture_output=False)

    duration = time.time() - start_time

    print_header("Test Run Complete")
    print_info(f"Duration: {duration:.1f} seconds")
    print_info(f"HTML Report: {html_report}")

    # Try to load and summarize results
    results_file = Path("test_reports/results.json")
    if results_file.exists():
        try:
            with open(results_file) as f:
                results = json.load(f)

            passed = sum(1 for r in results if r.get("passed"))
            failed = sum(1 for r in results if not r.get("passed"))
            total = len(results)

            print()
            print_header("Summary")
            print_success(f"Passed: {passed}")
            if failed > 0:
                print_fail(f"Failed: {failed}")
            print_info(f"Total: {total}")
            print_info(f"Success Rate: {100*passed/total if total > 0 else 0:.1f}%")

            # List failures
            if failed > 0:
                print()
                print_header("Failed Tests")
                for r in results:
                    if not r.get("passed"):
                        print_fail(f"{r['test_name']}")
                        if r.get("error"):
                            print(f"   Error: {r['error'][:100]}...")

        except Exception as e:
            print_warning(f"Could not load results.json: {e}")

    return result.returncode


def main():
    args = sys.argv[1:]

    # Parse custom arguments
    pytest_args = []

    if "--unit" in args:
        pytest_args.extend(["-m", "unit"])
        args.remove("--unit")
    elif "--quick" in args:
        pytest_args.extend(["-m", "not slow"])
        args.remove("--quick")
    elif "--critical" in args:
        pytest_args.extend(["-m", "critical"])
        args.remove("--critical")
    elif "--integration" in args:
        pytest_args.extend(["tests/integration/"])
        args.remove("--integration")

    # Pass remaining args to pytest
    pytest_args.extend(args)

    setup_directories()
    exit_code = run_tests(pytest_args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
