#!/usr/bin/env python3
# ============================================================
#  ANM-V2 — MAIN ENTRYPOINT (run.py)
#  Unified Interface • Self-Improvement • Sanity Check • Maximum Level
# ============================================================

from __future__ import annotations
import sys
import os
import argparse
from typing import Optional

# Check if running in venv or detect venv Python
def ensure_venv():
    """Ensure we're using the venv Python if venv exists."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(script_dir, "venv", "bin", "python3")
    venv_root = os.path.join(script_dir, "venv")
    
    # If venv doesn't exist, skip the check
    if not os.path.exists(venv_python):
        return
    
    current_python = sys.executable
    venv_python_abs = os.path.abspath(venv_python)
    venv_dir = os.path.dirname(venv_python_abs)
    venv_root_abs = os.path.abspath(venv_root)
    
    # Check if VIRTUAL_ENV is set and points to the correct venv
    virtual_env = os.environ.get("VIRTUAL_ENV")
    if virtual_env:
        virtual_env_abs = os.path.abspath(virtual_env)
        if virtual_env_abs == venv_root_abs:
            # Correct venv is activated, allow it even if python3 points to system Python
            return
    
    # Check if we're using the venv Python directly
    if os.path.abspath(current_python) == venv_python_abs:
        return
    
    # Check if current Python is in the venv directory
    if current_python.startswith(venv_dir):
        return
    
    # Check if venv's site-packages is in sys.path (venv is active but python3 points elsewhere)
    # This handles cases where venv is activated but python3 command still points to system Python
    if any(venv_root_abs in path for path in sys.path):
        # Venv packages are in path, consider it active
        return
    
    # Also check if we can find site-packages in the venv (more lenient check)
    # Look for any Python version's site-packages
    for python_version in ["python3.14", "python3.13", "python3.12", "python3.11", "python3.10", "python3.9"]:
        site_packages = os.path.join(venv_root_abs, "lib", python_version, "site-packages")
        if os.path.exists(site_packages) and site_packages in sys.path:
            # Venv is effectively active
            return
    
    # If we get here, we're not using the venv
    print("⚠️  WARNING: Not using virtual environment Python!")
    print(f"   Current Python: {current_python}")
    print(f"   Expected venv Python: {venv_python_abs}")
    print()
    if virtual_env:
        virtual_env_abs = os.path.abspath(virtual_env)
        if virtual_env_abs != venv_root_abs:
            print(f"   ⚠️  VIRTUAL_ENV is set to a DIFFERENT venv:")
            print(f"      Current: {virtual_env_abs}")
            print(f"      Expected: {venv_root_abs}")
            print()
            print("   💡 Solution: Deactivate the current venv and activate the correct one:")
            print("      deactivate")
            print(f"      source {venv_root}/bin/activate")
            print()
    print("   Quick fixes:")
    print(f"   1. Use venv Python directly: {venv_python} run.py")
    print(f"   2. Activate correct venv: source {venv_root}/bin/activate")
    print("   3. Try: python run.py (instead of python3)")
    print()
    sys.exit(1)

# Check will run in main() before imports


def load_input_from_file(path: str) -> str:
    """Load user query from a file."""
    # Security: Validate path to prevent path traversal attacks
    try:
        # Resolve to absolute path and check it's within safe directories
        abs_path = os.path.abspath(os.path.realpath(path))
        cwd = os.path.abspath(os.getcwd())

        # Allow files in current working directory or subdirectories
        if not abs_path.startswith(cwd):
            print(f"[ERROR] Security: File must be in current directory or subdirectories")
            print(f"[ERROR] Attempted path: {path}")
            sys.exit(1)

        if not os.path.exists(abs_path):
            print(f"[ERROR] File not found: {path}")
            sys.exit(1)

        # Additional check: file must be a regular file (not directory, symlink, etc.)
        if not os.path.isfile(abs_path):
            print(f"[ERROR] Path must be a regular file: {path}")
            sys.exit(1)

        with open(abs_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print(f"[ERROR] Failed to load file: {e}")
        sys.exit(1)


def print_banner():
    """Print ANM banner."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     ___    _   ____  __   _____    __  ____ _   __ ____       ║
║    /   |  / | / /  |/  / / ___/   /  |/  (_) | / //___ \\     ║
║   / /| | /  |/ / /|_/ /  \\__ \\   / /|_/ / /  |/ /  __/ /     ║
║  / ___ |/ /|  / /  / /  ___/ /  / /  / / / /|  / / __/       ║
║ /_/  |_/_/ |_/_/  /_/  /____/  /_/  /_/_/_/ |_/ /____/       ║
║                                                               ║
║         Artificial Neural Mesh V2 — Maximum Level            ║
║       Multi-Agent • Self-Improving • LawBook Aligned         ║
╚═══════════════════════════════════════════════════════════════╝
""")


def run_sanity_check(auto_fix: bool = False) -> bool:
    """
    Run ANM sanity check.
    
    Returns:
        True if passed, False otherwise
    """
    from anm import run_sanity_check as sanity_check
    
    result = sanity_check(verbose=True, auto_fix=auto_fix)
    return result.passed


def run_query(query: str, verbose: bool = False, skip_sanity: bool = False, quick_mode: bool = False, auto_mode: bool = False, optimize_prompts: bool = False, research_mode: bool = False) -> dict:
    """Run a query through ANM."""
    from anm import ANM, ANMConfig
    
    config = ANMConfig(
        skip_sanity_check=skip_sanity,
        auto_fix=True,
        verbose=verbose,
        quick_mode=quick_mode,
        auto_mode=auto_mode,
        optimize_prompts=optimize_prompts,
        research_mode=research_mode,
    )
    anm = ANM(config)
    
    if not anm.sanity_passed:
        print("[ERROR] Sanity check failed. Please fix issues before running queries.")
        sys.exit(1)
    
    if verbose:
        print(f"[INFO] Processing query: {query[:100]}...")
    
    result = anm.query(query)
    return result


def run_expansion_test(domain: str, verbose: bool = False) -> dict:
    """Test the expansion pipeline for a domain."""
    from anm.expansion import ExpansionEngineV2, ExpansionConfig
    
    if verbose:
        print(f"[INFO] Testing expansion for domain: {domain}")
    
    engine = ExpansionEngineV2(ExpansionConfig(
        use_qlora=True,
        require_human_approval=False,  # For testing
    ))
    
    result = engine.run_sync(
        query=f"Explain advanced concepts in {domain}",
        memory_brief="",
    )
    
    return result


def interactive_mode(skip_sanity: bool = False, quick_mode: bool = False, auto_mode: bool = False, optimize_prompts: bool = False, research_mode: bool = False):
    """Run ANM in interactive mode with beautiful terminal UI."""
    from anm import ANM, ANMConfig
    from anm.ui import TerminalUI
    
    ui = TerminalUI()
    ui.print_banner()
    
    # Run sanity check first
    if not skip_sanity:
        ui.print_info("Running pre-startup sanity check...")
        ui.console.print() if ui.console else print()
    
    # Track research mode state (can be toggled)
    current_research_mode = research_mode
    
    ui.print_mode_info(quick_mode, auto_mode, optimize_prompts, current_research_mode)

    config = ANMConfig(
        skip_sanity_check=skip_sanity,
        auto_fix=True,
        quick_mode=quick_mode,
        auto_mode=auto_mode,
        optimize_prompts=optimize_prompts,
        research_mode=current_research_mode,
    )
    anm = ANM(config)
    
    if not anm.sanity_passed:
        ui.print_error("Sanity check failed. Please fix issues before using ANM.")
        return
    
    ui.print_success("ANM is ready! Type 'help' for commands or 'exit' to quit.")
    ui.console.print() if ui.console else print()
    
    while True:
        try:
            # Update prompt based on research mode
            if current_research_mode:
                prompt_text = "ANM [Research Mode Active]> "
            else:
                prompt_text = "ANM> "
            
            user_input = ui.prompt(prompt_text).strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                ui.print_success("Goodbye!")
                break
            
            # Research mode toggle command
            if user_input.lower() == "research":
                current_research_mode = not current_research_mode
                # Reinitialize ANM with new research mode
                config = ANMConfig(
                    skip_sanity_check=skip_sanity,
                    auto_fix=True,
                    quick_mode=False,  # Research mode disables quick mode
                    auto_mode=False,   # Research mode disables auto mode
                    optimize_prompts=optimize_prompts,
                    research_mode=current_research_mode,
                )
                anm = ANM(config)
                
                if current_research_mode:
                    ui.print_success("🔬 Research Mode Activated!")
                    ui.print_info("Maximum quality mode with structured PDF output enabled.")
                else:
                    ui.print_success("🔬 Research Mode Deactivated")
                    ui.print_info("Returned to normal mode.")
                ui.console.print() if ui.console else print()
                continue
            
            # Exit research mode with "normal" or "exit research"
            if user_input.lower() in ["normal", "exit research"]:
                if current_research_mode:
                    current_research_mode = False
                    config = ANMConfig(
                        skip_sanity_check=skip_sanity,
                        auto_fix=True,
                        quick_mode=quick_mode,
                        auto_mode=auto_mode,
                        optimize_prompts=optimize_prompts,
                        research_mode=False,
                    )
                    anm = ANM(config)
                    ui.print_success("🔬 Research Mode Deactivated")
                    ui.print_info("Returned to normal mode.")
                    ui.console.print() if ui.console else print()
                else:
                    ui.print_info("Research mode is not active.")
                continue
            
            if user_input.lower().startswith("expand "):
                domain = user_input[7:].strip()
                ui.print_info(f"Testing expansion for: {domain}")
                result = run_expansion_test(domain, verbose=True)
                ui.print_success(result.get('message', result.get('error', 'Unknown')))
                ui.console.print() if ui.console else print()
                continue
            
            if user_input.lower() == "sanity":
                ui.print_info("Running full sanity check...")
                passed = run_sanity_check(auto_fix=False)
                ui.print_sanity_check(passed)
                continue
            
            if user_input.lower() == "sanity fix":
                ui.print_info("Running sanity check with auto-fix...")
                passed = run_sanity_check(auto_fix=True)
                ui.print_sanity_check(passed)
                continue
            
            if user_input.lower() == "status":
                status_dict = {
                    "router": "Active",
                    "wot": "Active (Polymath Mode)",
                    "expansion": "V2 Maximum Level",
                    "memory": "Cloud Diary Active",
                    "safety": "LawBook v1.2 Aligned",
                    "sanity_passed": anm.sanity_passed,
                }
                if current_research_mode:
                    status_dict["research_mode"] = "Active"
                ui.print_status(status_dict)
                continue
            
            if user_input.lower() == "help":
                ui.print_help()
                continue
            
            # Process as regular query (with current research mode)
            ui.print_processing(user_input)
            
            # Update ANM config if research mode changed
            if anm.anm_config.research_mode != current_research_mode:
                config = ANMConfig(
                    skip_sanity_check=skip_sanity,
                    auto_fix=True,
                    quick_mode=False if current_research_mode else quick_mode,
                    auto_mode=False if current_research_mode else auto_mode,
                    optimize_prompts=optimize_prompts,
                    research_mode=current_research_mode,
                )
                anm = ANM(config)
            
            progress = ui.create_progress()
            if progress:
                with progress:
                    task = progress.add_task("[cyan]Processing...", total=None)
                    result = anm.query(user_input)
                    progress.update(task, completed=True)
            else:
                result = anm.query(user_input)
            
            # Show optimization info if prompt was optimized
            if result.get("optimized_query") and result.get("original_query"):
                ui.print_optimization_info(
                    result['original_query'],
                    result['optimized_query']
                )
            
            # Print result
            ui.print_result(result)
            
        except KeyboardInterrupt:
            ui.print_warning("Interrupted. Type 'exit' to quit.")
        except Exception as e:
            ui.print_error(str(e))


def main():
    """Main entry point."""
    # Ensure we're using venv Python before doing anything
    ensure_venv()
    
    parser = argparse.ArgumentParser(
        description="ANM-V2 — Artificial Neural Mesh",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                          # Interactive mode (with sanity check)
  python run.py "What is quantum physics?"  # Single query
  python run.py -f query.txt             # Query from file
  python run.py --expand geology         # Test expansion
  python run.py --sanity                 # Run sanity check only
  python run.py --sanity --fix           # Sanity check with auto-fix
  python run.py --skip-sanity            # Skip sanity check
        """
    )
    
    parser.add_argument("query", nargs="?", help="Query to process")
    parser.add_argument("-f", "--file", help="Load query from file")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--expand", metavar="DOMAIN", help="Test expansion for a domain")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--version", action="store_true", help="Show version")
    parser.add_argument("--quick", action="store_true", help="Quick mode: use smaller, faster model (no chain-of-thought)")
    parser.add_argument("--auto", action="store_true", help="Auto mode: automatically choose quick/normal based on query complexity")
    parser.add_argument("--research", action="store_true", help="Research mode: maximum quality, structured PDF output")
    parser.add_argument("--optimize", action="store_true", help="Optimize prompts: refine user prompts using small model for better processing")

    # Sanity check options
    parser.add_argument("--sanity", action="store_true", help="Run sanity check only")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues (use with --sanity)")
    parser.add_argument("--skip-sanity", action="store_true", help="Skip sanity check on startup")
    
    args = parser.parse_args()
    
    # Show version
    if args.version:
        from anm import __version__
        print(f"ANM v{__version__}")
        return
    
    # Sanity check only
    if args.sanity:
        from anm.ui import TerminalUI
        ui = TerminalUI()
        ui.print_banner()
        ui.print_info("Running ANM Sanity Check...")
        ui.console.print() if ui.console else print()
        passed = run_sanity_check(auto_fix=args.fix)
        ui.print_sanity_check(passed)
        sys.exit(0 if passed else 1)
    
    # Test expansion
    if args.expand:
        from anm.ui import TerminalUI
        ui = TerminalUI()
        ui.print_banner()
        if not args.skip_sanity:
            ui.print_info("Running pre-startup sanity check...")
            ui.console.print() if ui.console else print()
            if not run_sanity_check(auto_fix=True):
                ui.print_error("Sanity check failed.")
                sys.exit(1)
        
        ui.print_info(f"Testing expansion for domain: {args.expand}")
        result = run_expansion_test(args.expand, verbose=args.verbose)
        
        if result.get("success"):
            ui.print_success(result.get('message', 'Success'))
        else:
            ui.print_error(result.get('message', result.get('error', 'Failed')))
        return
    
    # Validate mode flags
    if args.quick and args.auto:
        print("[ERROR] Cannot use both --quick and --auto. Choose one.")
        sys.exit(1)

    # Research mode validation
    if args.research and args.auto:
        print("[ERROR] Cannot use both --research and --auto. Research mode uses deterministic routing.")
        sys.exit(1)

    if args.research and args.quick:
        print("[ERROR] Cannot use --research with --quick. Research mode requires full reasoning.")
        sys.exit(1)

    # Interactive mode
    if args.interactive or (not args.query and not args.file):
        interactive_mode(skip_sanity=args.skip_sanity, quick_mode=args.quick, auto_mode=args.auto, optimize_prompts=args.optimize, research_mode=args.research)
        return

    # Single query mode
    from anm.ui import TerminalUI

    ui = TerminalUI()
    ui.print_banner()

    ui.print_mode_info(args.quick, args.auto, args.optimize, args.research)
    
    if args.file:
        query = load_input_from_file(args.file)
        ui.print_info(f"Loaded query from: {args.file}")
    else:
        query = args.query
    
    ui.print_info(f"Query: {query[:100]}{'...' if len(query) > 100 else ''}")
    ui.console.print() if ui.console else print()
    
    if not args.skip_sanity:
        ui.print_info("Running pre-startup check...")
        ui.console.print() if ui.console else print()
    
    ui.print_processing(query)
    
    progress = ui.create_progress()
    if progress:
        with progress:
            task = progress.add_task("[cyan]Processing...", total=None)
            result = run_query(query, verbose=args.verbose, skip_sanity=args.skip_sanity, quick_mode=args.quick, auto_mode=args.auto, optimize_prompts=args.optimize, research_mode=args.research)
            progress.update(task, completed=True)
    else:
        result = run_query(query, verbose=args.verbose, skip_sanity=args.skip_sanity, quick_mode=args.quick, auto_mode=args.auto, optimize_prompts=args.optimize, research_mode=args.research)
    
    # Show optimization info if prompt was optimized
    if result.get("optimized_query") and result.get("original_query"):
        ui.print_optimization_info(
            result['original_query'],
            result['optimized_query']
        )
    
    # Print result
    ui.print_result(result)


if __name__ == "__main__":
    main()
