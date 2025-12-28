# ============================================================
#  ANM V0-OpenSource — Terminal UI
#  Beautiful Rich-based Terminal Interface
# ============================================================

"""
ANM Terminal UI - Rich-based interactive terminal interface.

Features:
- Beautiful banners and formatting
- Interactive prompt with history
- Status panels and progress bars
- Colored output
- Live updates
- Command history
"""

from __future__ import annotations
from typing import Optional, Dict, Any, Callable, List, Tuple
import sys
import re
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.prompt import Prompt
    from rich.markdown import Markdown
    from rich.layout import Layout
    from rich.live import Live
    from rich.align import Align
    from rich.syntax import Syntax
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback to basic print
    Console = None
    Panel = None
    Text = None
    Table = None
    Progress = None
    Prompt = None
    Markdown = None
    Layout = None
    Live = None
    Align = None
    Syntax = None
    box = None

# Try to import pyperclip for copy functionality
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False
    pyperclip = None

__all__ = ["TerminalUI", "RICH_AVAILABLE"]


class TerminalUI:
    """Beautiful terminal UI for ANM using Rich."""
    
    def __init__(self):
        """Initialize terminal UI."""
        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None
            print("⚠️  Rich not available. Install with: pip install rich")
    
    def print_banner(self) -> None:
        """Print beautiful ANM banner."""
        if not RICH_AVAILABLE:
            self._print_banner_fallback()
            return
        
        banner_text = """
╔═══════════════════════════════════════════════════════════════╗
║     ___    _   ____  __   _____    __  ____ _   __ ____       ║
║    /   |  / | / /  |/  / / ___/   /  |/  (_) | / //___ \\     ║
║   / /| | /  |/ / /|_/ /  \\__ \\   / /|_/ / /  |/ /  __/ /     ║
║  / ___ |/ /|  / /  / /  ___/ /  / /  / / / /|  / / __/       ║
║ /_/  |_/_/ |_/_/  /_/  /____/  /_/  /_/_/_/ |_/ /____/       ║
║                                                               ║
║         Artificial Neural Mesh V0-OpenSource                 ║
║       Multi-Agent • Self-Improving • LawBook Aligned         ║
╚═══════════════════════════════════════════════════════════════╝
"""
        
        self.console.print(Panel(
            banner_text.strip(),
            border_style="bright_blue",
            box=box.DOUBLE,
            padding=(1, 2),
        ))
        self.console.print()
    
    def _print_banner_fallback(self) -> None:
        """Fallback banner without Rich."""
        print("""
╔═══════════════════════════════════════════════════════════════╗
║     ___    _   ____  __   _____    __  ____ _   __ ____       ║
║    /   |  / | / /  |/  / / ___/   /  |/  (_) | / //___ \\     ║
║   / /| | /  |/ / /|_/ /  \\__ \\   / /|_/ / /  |/ /  __/ /     ║
║  / ___ |/ /|  / /  / /  ___/ /  / /  / / / /|  / / __/       ║
║ /_/  |_/_/ |_/_/  /_/  /____/  /_/  /_/_/_/ |_/ /____/       ║
║                                                               ║
║         Artificial Neural Mesh V0-OpenSource                 ║
║       Multi-Agent • Self-Improving • LawBook Aligned         ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    def print_status(self, status: Dict[str, Any]) -> None:
        """Print system status in a beautiful table."""
        if not RICH_AVAILABLE:
            self._print_status_fallback(status)
            return
        
        table = Table(title="ANM System Status", box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")
        
        components = [
            ("Router", status.get("router", "Active"), "Intelligent query routing"),
            ("TrueWoT", status.get("wot", "Active"), "Polymath reasoning engine"),
            ("Expansion Engine", status.get("expansion", "V2 Maximum Level"), "Self-improvement pipeline"),
            ("Memory Hub", status.get("memory", "Cloud Diary Active"), "Episodic & semantic memory"),
            ("Safety", status.get("safety", "LawBook v1.2 Aligned"), "Verifier & LawBook"),
            ("Sanity Check", "✅ Passed" if status.get("sanity_passed", False) else "❌ Failed", "System validation"),
        ]
        
        for component, stat, details in components:
            table.add_row(component, stat, details)
        
        self.console.print(table)
        self.console.print()
    
    def _print_status_fallback(self, status: Dict[str, Any]) -> None:
        """Fallback status without Rich."""
        print("\n[STATUS]")
        print("  - Router: Active")
        print("  - TrueWoT: Active (Polymath Mode)")
        print("  - Expansion Engine: V2 Maximum Level")
        print("  - Memory: Cloud Diary Active")
        print("  - Safety: LawBook v1.2 Aligned")
        print(f"  - Sanity: {'✅ Passed' if status.get('sanity_passed', False) else '❌ Failed'}\n")
    
    def print_mode_info(self, quick_mode: bool = False, auto_mode: bool = False, optimize_prompts: bool = False, research_mode: bool = False) -> None:
        """Print mode information."""
        if not RICH_AVAILABLE:
            self._print_mode_info_fallback(quick_mode, auto_mode, optimize_prompts, research_mode)
            return

        # Research mode takes precedence
        if research_mode:
            if RICH_AVAILABLE:
                from rich.text import Text
                research_text = Text.assemble(
                    ("╭─ RESEARCH MODE ", "bold cyan"),
                    ("─────────────────────────╮\n", "cyan"),
                    ("│ ", "cyan"),
                    ("Maximum Quality • Deterministic Routing ", "bold white"),
                    ("│\n", "cyan"),
                    ("│ ", "cyan"),
                    ("Structured PDF Output                   ", "white"),
                    ("│\n", "cyan"),
                    ("╰─────────────────────────────────────────╯", "cyan")
                )
                self.console.print(research_text)
                self.console.print()
            return  # Skip other mode displays

        modes = []
        if optimize_prompts:
            modes.append(Text("✨ Prompt Optimization", style="bright_yellow"))
        if auto_mode:
            modes.append(Text("🤖 Auto Mode", style="bright_cyan"))
        elif quick_mode:
            modes.append(Text("⚡ Quick Mode", style="bright_green"))

        if modes:
            mode_text = Text("Active Modes: ", style="bold") + Text(" • ").join(modes)
            self.console.print(Panel(mode_text, border_style="blue", box=box.ROUNDED))
            self.console.print()

    def _print_mode_info_fallback(self, quick_mode: bool, auto_mode: bool, optimize_prompts: bool, research_mode: bool = False) -> None:
        """Fallback mode info without Rich."""
        if research_mode:
            print("╭─ RESEARCH MODE ─────────────────────────╮")
            print("│ Maximum Quality • Deterministic Routing │")
            print("│ Structured PDF Output                   │")
            print("╰─────────────────────────────────────────╯\n")
            return

        if optimize_prompts:
            print("✨ Prompt Optimization: Refining prompts for better processing\n")
        if auto_mode:
            print("🤖 Auto Mode: Automatically choosing quick/normal mode based on query complexity\n")
        elif quick_mode:
            print("⚡ Quick Mode: Using smaller, faster model (no chain-of-thought)\n")
    
    def print_processing(self, query: str) -> None:
        """Show processing indicator."""
        if not RICH_AVAILABLE:
            print(f"\n[PROCESSING] {query[:50]}...")
            return
        
        self.console.print()
        # Processing will be shown via progress bar in calling code
    
    def _extract_code_blocks(self, text: str) -> Tuple[str, List[Tuple[str, str]]]:
        """
        Extract code blocks from text.
        
        Returns:
            Tuple of (text_without_code, list of (language, code) tuples)
        """
        code_blocks = []
        # Pattern to match code blocks: ```language\ncode\n```
        pattern = r'```(\w+)?\n(.*?)```'
        
        def replace_code(match):
            language = match.group(1) or "text"
            code = match.group(2).strip()
            code_blocks.append((language, code))
            return f"[CODE_BLOCK_{len(code_blocks) - 1}]"
        
        # Replace code blocks with placeholders
        text_without_code = re.sub(pattern, replace_code, text, flags=re.DOTALL)
        
        return text_without_code, code_blocks
    
    def _copy_to_clipboard(self, text: str) -> bool:
        """Copy text to clipboard if available."""
        if CLIPBOARD_AVAILABLE and pyperclip:
            try:
                pyperclip.copy(text)
                return True
            except Exception:
                return False
        return False
    
    def print_result(self, result: Dict[str, Any], show_metadata: bool = True) -> None:
        """Print query result beautifully - only shows verified refiner response with separate code boxes."""
        if not RICH_AVAILABLE:
            self._print_result_fallback(result)
            return
        
        # Check verification status
        verification = result.get("verification", {})
        status = verification.get("status", "unknown")
        
        # Get the result text (may be None or empty)
        result_text = result.get("result", "")
        if result_text is None:
            result_text = ""
        
        # Clean up the result text - remove [VERIFIER_READY] and other markers
        if result_text:
            # Remove all variations of VERIFIER_READY marker
            result_text = re.sub(r'\[VERIFIER_READY\]', '', result_text, flags=re.IGNORECASE)
            result_text = re.sub(r'\[/VERIFIER_ready\]', '', result_text, flags=re.IGNORECASE)
            result_text = re.sub(r'\[VERIFIER_ready\]', '', result_text, flags=re.IGNORECASE)
            result_text = result_text.strip()
        
        # Handle different verification statuses
        if status == "error":
            # Show error message with details
            error_msg = verification.get("notes", "An error occurred during verification")
            error_details = result.get("error", "")
            
            error_content = f"[bold red]Verification Error[/bold red]\n\n{error_msg}"
            if error_details:
                error_content += f"\n\n[dim]Details: {error_details}[/dim]"
            
            # Also show the result if available (for debugging)
            if result_text and len(result_text) > 10:
                error_content += f"\n\n[dim]Generated response (may be incomplete):[/dim]\n[dim]{result_text[:200]}...[/dim]" if len(result_text) > 200 else f"\n\n[dim]Generated response:[/dim]\n[dim]{result_text}[/dim]"
            
            error_panel = Panel(
                error_content,
                title="[bold red]Verification Error[/bold red]",
                border_style="red",
                box=box.ROUNDED,
                padding=(1, 2),
            )
            self.console.print(error_panel)
            self.console.print()
            return
        
        elif status == "rejected":
            # Show rejection message with reason
            rejection_reason = verification.get("notes", "Quality check failed")
            issues = verification.get("issues", [])
            
            rejection_content = f"[bold red]Answer was rejected by Verifier[/bold red]\n\n[bold]Reason:[/bold] {rejection_reason}"
            
            if issues:
                rejection_content += f"\n\n[bold]Issues found:[/bold]"
                for issue in issues[:5]:  # Show max 5 issues
                    rejection_content += f"\n  • {issue}"
                if len(issues) > 5:
                    rejection_content += f"\n  ... and {len(issues) - 5} more"
            
            # Show the result if available (for debugging) - but mark it as rejected
            if result_text and len(result_text) > 10:
                rejection_content += f"\n\n[dim yellow]Generated response (rejected):[/dim yellow]\n[dim]{result_text[:300]}...[/dim]" if len(result_text) > 300 else f"\n\n[dim yellow]Generated response (rejected):[/dim yellow]\n[dim]{result_text}[/dim]"
            
            rejection_panel = Panel(
                rejection_content,
                title="[bold red]Verification Failed[/bold red]",
                border_style="red",
                box=box.ROUNDED,
                padding=(1, 2),
            )
            self.console.print(rejection_panel)
            self.console.print()
            return
        
        elif status != "approved":
            # Unknown status - show warning but still display result
            warning_panel = Panel(
                f"[bold yellow]Warning: Verification status is '{status}'[/bold yellow]\n\n"
                "Result may not be fully verified.",
                title="[bold yellow]Verification Warning[/bold yellow]",
                border_style="yellow",
                box=box.ROUNDED,
                padding=(1, 2),
            )
            self.console.print(warning_panel)
            self.console.print()
        
        # If no result text, show appropriate message
        if not result_text or len(result_text.strip()) < 5:
            empty_panel = Panel(
                "[dim]No response generated. This may indicate an error in the processing pipeline.[/dim]",
                title="[bold yellow]Empty Response[/bold yellow]",
                border_style="yellow",
                box=box.ROUNDED,
                padding=(1, 2),
            )
            self.console.print(empty_panel)
            self.console.print()
            return
        
        # Clean thinking tags (sync with refiner/verifier)
        result_text = self._clean_thinking_tags(result_text) if result_text else ""
        
        # Ensure result_text is not None or empty after cleaning
        if not result_text or len(result_text.strip()) < 5:
            empty_panel = Panel(
                "[dim]Response was too short or empty after cleaning.[/dim]",
                title="[bold yellow]Empty Response[/bold yellow]",
                border_style="yellow",
                box=box.ROUNDED,
                padding=(1, 2),
            )
            self.console.print(empty_panel)
            self.console.print()
            return
        
        # Extract code blocks
        text_without_code, code_blocks = self._extract_code_blocks(result_text)
        
        # Clean up text without code - remove code block placeholders
        clean_text = text_without_code.strip()
        # Remove empty lines and clean up
        clean_text = re.sub(r'\n\s*\n\s*\n', '\n\n', clean_text)  # Remove multiple blank lines
        clean_text = clean_text.strip()
        
        # Display text content (if any)
        if clean_text:
            result_panel = Panel(
                Markdown(clean_text) if len(clean_text) > 100 else clean_text,
                title="[bold green]ANM Response[/bold green]",
                border_style="green",
                box=box.ROUNDED,
                padding=(1, 2),
            )
            self.console.print(result_panel)
            self.console.print()
        
        # Display code blocks in separate boxes with copy buttons
        for idx, (language, code) in enumerate(code_blocks):
            # Determine language for syntax highlighting
            lang_map = {
                "python": "python",
                "py": "python",
                "javascript": "javascript",
                "js": "javascript",
                "java": "java",
                "cpp": "cpp",
                "c++": "cpp",
                "c": "c",
                "html": "html",
                "css": "css",
                "sql": "sql",
                "bash": "bash",
                "sh": "bash",
                "shell": "bash",
                "json": "json",
                "yaml": "yaml",
                "yml": "yaml",
                "markdown": "markdown",
                "md": "markdown",
            }
            syntax_lang = lang_map.get(language.lower(), "text")
            
            # Create syntax-highlighted code
            if Syntax:
                syntax = Syntax(code, syntax_lang, theme="monokai", line_numbers=True, word_wrap=True)
            else:
                syntax = code
            
            # Create title with copy button indicator
            # Rich Panel titles support markup, so we can use spacing
            title_text = "[bold cyan]Code[/bold cyan]"
            if language and language.lower() != "text":
                title_text += f" [dim]({language})[/dim]"
            # Add copy indicator - Rich will handle the spacing
            title_text += " [dim]• 📋 Copy[/dim]"
            
            # Create code panel
            code_panel = Panel(
                syntax,
                title=title_text,
                border_style="cyan",
                box=box.ROUNDED,
                padding=(1, 2),
            )
            self.console.print(code_panel)
            
            # Auto-copy to clipboard if available (for convenience)
            if CLIPBOARD_AVAILABLE:
                if self._copy_to_clipboard(code):
                    # Show brief confirmation (subtle)
                    pass  # Silent copy - users can paste directly
            
            self.console.print()
        
        # If no content at all (only code blocks), show a message
        if not clean_text and not code_blocks:
            empty_panel = Panel(
                "[dim]No content to display[/dim]",
                title="[bold yellow]Empty Response[/bold yellow]",
                border_style="yellow",
                box=box.ROUNDED,
                padding=(1, 2),
            )
            self.console.print(empty_panel)
            self.console.print()

        # Research mode output (PDF or Markdown)
        if result.get("mode") == "research" and result.get("output_path"):
            output_format = result.get("output_format", "unknown")
            format_icon = "📄" if output_format == "pdf" else "📝" if output_format == "markdown" else "📋"
            format_color = "green" if output_format == "pdf" else "yellow"

            self.console.print(f"\n[bold {format_color}]✓[/] {format_icon} {output_format.upper()}: {result['output_path']}")

            if result.get("authority_assignments"):
                self.console.print("\n[bold]Authority Models:[/]")
                for domain, model in result["authority_assignments"].items():
                    self.console.print(f"  • {domain}: [cyan]{model}[/]")

            if result.get("metacognition"):
                meta = result["metacognition"]
                if meta.get("confidence"):
                    self.console.print(f"\n[bold]Confidence:[/] {meta['confidence']}")
                if meta.get("uncertainty"):
                    self.console.print(f"[bold]Uncertainty:[/] {meta['uncertainty']}")

            self.console.print()

    def _print_result_fallback(self, result: Dict[str, Any]) -> None:
        """Fallback result printing without Rich - only shows verified refiner response."""
        # Check verification status
        verification = result.get("verification", {})
        status = verification.get("status", "unknown")
        
        # Get the result text
        result_text = result.get("result", "")
        if result_text is None:
            result_text = ""
        
        # Clean up the result text - remove [VERIFIER_READY] and other markers
        if result_text:
            result_text = re.sub(r'\[VERIFIER_READY\]', '', result_text, flags=re.IGNORECASE)
            result_text = re.sub(r'\[/VERIFIER_ready\]', '', result_text, flags=re.IGNORECASE)
            result_text = re.sub(r'\[VERIFIER_ready\]', '', result_text, flags=re.IGNORECASE)
            result_text = result_text.strip()
        
        # Handle different verification statuses
        if status == "error":
            print("\n" + "=" * 60)
            print("VERIFICATION ERROR")
            print("=" * 60)
            print(f"Error: {verification.get('notes', 'An error occurred during verification')}")
            if result.get("error"):
                print(f"Details: {result.get('error')}")
            if result_text and len(result_text) > 10:
                print(f"\nGenerated response (may be incomplete):\n{result_text[:200]}...")
            print("=" * 60)
            print()
            return
        
        elif status == "rejected":
            print("\n" + "=" * 60)
            print("VERIFICATION FAILED")
            print("=" * 60)
            print(f"Reason: {verification.get('notes', 'Quality check failed')}")
            issues = verification.get("issues", [])
            if issues:
                print(f"Issues: {', '.join(issues[:5])}")
            if result_text and len(result_text) > 10:
                print(f"\nGenerated response (rejected):\n{result_text[:300]}...")
            print("=" * 60)
            print()
            return
        
        elif status != "approved":
            print("\n" + "=" * 60)
            print(f"VERIFICATION WARNING: Status is '{status}'")
            print("=" * 60)
            print("Result may not be fully verified.")
            print("=" * 60)
            print()
        
        # If no result text, show message
        if not result_text or len(result_text.strip()) < 5:
            print("\n" + "=" * 60)
            print("EMPTY RESPONSE")
            print("=" * 60)
            print("No response generated.")
            print("=" * 60)
            print()
            return
        
        # Clean thinking tags (sync with refiner/verifier)
        result_text = self._clean_thinking_tags(result_text) if result_text else ""
        
        # Ensure result_text is not None or empty after cleaning
        if not result_text or len(result_text.strip()) < 5:
            print("\n" + "=" * 60)
            print("EMPTY RESPONSE")
            print("=" * 60)
            print("Response was too short or empty after cleaning.")
            print("=" * 60)
            print()
            return
        
        # Extract code blocks
        text_without_code, code_blocks = self._extract_code_blocks(result_text)
        clean_text = text_without_code.strip()
        clean_text = re.sub(r'\n\s*\n\s*\n', '\n\n', clean_text)
        clean_text = clean_text.strip()
        
        # Display text content
        if clean_text:
            print("\n" + "=" * 60)
            print("RESULT")
            print("=" * 60)
            print(clean_text)
            print("=" * 60)
            print()
        
        # Display code blocks separately
        for idx, (language, code) in enumerate(code_blocks):
            print("\n" + "=" * 60)
            print(f"CODE{' (' + language + ')' if language else ''}")
            print("=" * 60)
            print(code)
            print("=" * 60)
            if CLIPBOARD_AVAILABLE:
                self._copy_to_clipboard(code)
                print("(Code copied to clipboard)")
            print()
        
        # If no content
        if not clean_text and not code_blocks:
            print("\n" + "=" * 60)
            print("EMPTY RESPONSE")
            print("=" * 60)
            print()
    
    def print_error(self, error: str) -> None:
        """Print error message."""
        if not RICH_AVAILABLE:
            print(f"[ERROR] {error}")
            return
        
        self.console.print(f"[bold red]❌ Error:[/bold red] {error}")
    
    def print_success(self, message: str) -> None:
        """Print success message."""
        if not RICH_AVAILABLE:
            print(f"[SUCCESS] {message}")
            return
        
        self.console.print(f"[bold green]✅ {message}[/bold green]")
    
    def print_info(self, message: str) -> None:
        """Print info message."""
        if not RICH_AVAILABLE:
            print(f"[INFO] {message}")
            return
        
        self.console.print(f"[cyan]ℹ️  {message}[/cyan]")
    
    def print_warning(self, message: str) -> None:
        """Print warning message."""
        if not RICH_AVAILABLE:
            print(f"[WARNING] {message}")
            return
        
        self.console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")
    
    def prompt(self, text: str = "ANM> ", default: Optional[str] = None) -> str:
        """Get user input with prompt."""
        if not RICH_AVAILABLE:
            return input(text)
        
        return Prompt.ask(f"[bold cyan]{text}[/bold cyan]", default=default)
    
    def print_help(self) -> None:
        """Print help information."""
        if not RICH_AVAILABLE:
            self._print_help_fallback()
            return
        
        help_table = Table(title="ANM Commands", box=box.ROUNDED, show_header=True, header_style="bold magenta")
        help_table.add_column("Command", style="cyan", no_wrap=True)
        help_table.add_column("Description", style="white")
        
        commands = [
            ("<query>", "Process a query through ANM"),
            ("expand <domain>", "Test expansion for a domain"),
            ("sanity", "Run sanity check (no auto-fix)"),
            ("sanity fix", "Run sanity check with auto-fix"),
            ("status", "Show system status"),
            ("help", "Show this help"),
            ("exit", "Exit interactive mode"),
        ]
        
        for cmd, desc in commands:
            help_table.add_row(cmd, desc)
        
        self.console.print(help_table)
        self.console.print()
    
    def _print_help_fallback(self) -> None:
        """Fallback help without Rich."""
        print("\n[COMMANDS]")
        print("  <query>       - Process a query through ANM")
        print("  expand <dom>  - Test expansion for a domain")
        print("  sanity        - Run sanity check (no auto-fix)")
        print("  sanity fix    - Run sanity check with auto-fix")
        print("  status        - Show system status")
        print("  exit          - Exit interactive mode")
        print("  help          - Show this help\n")
    
    def create_progress(self) -> Progress:
        """Create a progress bar context manager."""
        if not RICH_AVAILABLE:
            return None
        
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        )
    
    def print_optimization_info(self, original: str, optimized: str) -> None:
        """Print prompt optimization information."""
        if not RICH_AVAILABLE:
            print("\n" + "=" * 60)
            print("PROMPT OPTIMIZATION")
            print("=" * 60)
            print(f"Original:  {original}")
            print(f"Optimized: {optimized}")
            print("=" * 60)
            return
        
        opt_table = Table(title="Prompt Optimization", box=box.ROUNDED, show_header=False)
        opt_table.add_column("Type", style="cyan", width=10)
        opt_table.add_column("Text", style="white")
        
        opt_table.add_row("Original", original)
        opt_table.add_row("Optimized", optimized)
        
        self.console.print(opt_table)
        self.console.print()
    
    def print_sanity_check(self, passed: bool, issues: list = None) -> None:
        """Print sanity check results."""
        if not RICH_AVAILABLE:
            status = "✅ Passed" if passed else "❌ Failed"
            print(f"\n[SANITY CHECK] {status}")
            if issues:
                for issue in issues:
                    print(f"  - {issue}")
            return
        
        if passed:
            self.console.print("[bold green]✅ Sanity Check Passed[/bold green]")
        else:
            self.console.print("[bold red]❌ Sanity Check Failed[/bold red]")
            if issues:
                for issue in issues:
                    self.console.print(f"  [yellow]⚠️  {issue}[/yellow]")
        self.console.print()
    
    def clear(self) -> None:
        """Clear the console."""
        if not RICH_AVAILABLE:
            import os
            os.system('clear' if os.name != 'nt' else 'cls')
            return
        
        self.console.clear()
    
    def _clean_thinking_tags(self, text: str) -> str:
        """Remove thinking tags (sync with refiner/verifier)."""
        if not text:
            return ""
        
        bad_patterns = [
            r"</?redacted_reasoning>",
            r"<think>.*?</think>",
            r"</?think>",
            r"<think>.*?</think>",
            r"<\|begin_of_text\|>",
            r"<\|end_of_text\|>",
            r"Thinking\.\.\..*?\n",
            r"Done thinking:.*?\n",
            r"Analysis:.*?\n",
            r"\[internal\].*?\[/internal\]",
        ]
        
        for pattern in bad_patterns:
            text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove standalone thinking tags on their own lines
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip lines that are only thinking tags
            if stripped in ['</think>', '<think>', '</think>', '<think>', '']:
                continue
            # Skip lines that start with thinking tags
            if (stripped.startswith('</think>') or 
                stripped.startswith('<think>') or
                stripped.startswith('</think>') or
                stripped.startswith('<think>')):
                continue
            cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Clean up multiple blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()

