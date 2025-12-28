"""
ANM Research Mode Markdown Generator

Generates structured research markdown files with 9 sections (PDF fallback).
"""

from datetime import datetime
import os
from typing import Dict, Any


class ResearchMarkdownGenerator:
    """
    Generate structured research markdown with 9 sections (PDF fallback).

    Same 9 sections as PDF:
    1. Title Page
    2. Executive Summary
    3. Research Question & Scope
    4. Sources & Data
    5. Analysis
    6. Meta-Cognition
    7. Limitations
    8. Conclusions
    9. Appendix
    """

    def generate(self, user_query: str, domain_cots: Dict[str, str],
                refined_output: str, verification: Dict[str, Any],
                metacognition: Dict[str, Any], authority_assignments: Dict[str, str],
                wot_steps: int, processing_time_ms: float) -> str:
        """
        Generate markdown with 9-section structure.

        Returns: Markdown file path
        """
        # Create output directory
        output_dir = "research_outputs"
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"research_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)

        # Build markdown content
        content = []

        # Section 1: Title
        content.append("# ANM Research Mode\n")
        content.append(f"## {user_query}\n")
        timestamp_str = datetime.now().strftime("%B %d, %Y at %H:%M")
        content.append(f"*Generated: {timestamp_str}*\n")
        content.append("\n---\n\n")

        # Section 2: Executive Summary
        status = verification.get("status", "unknown")
        content.append("## Executive Summary\n\n")
        content.append(f"**Verification Status:** {status.upper()}\n\n")
        summary = refined_output[:500] + "..." if len(refined_output) > 500 else refined_output
        content.append(f"{summary}\n\n")
        content.append("---\n\n")

        # Section 3: Research Question & Scope
        content.append("## Research Question & Scope\n\n")
        content.append(f"**Query:** {user_query}\n\n")
        content.append(f"**Domains Analyzed:** {', '.join(domain_cots.keys())}\n\n")
        content.append("---\n\n")

        # Section 4: Sources & Data
        content.append("## Sources & Data\n\n")
        content.append("### Authority Model Assignments\n\n")
        for domain, model in authority_assignments.items():
            content.append(f"- **{domain.title()}:** `{model}`\n")
        content.append("\n---\n\n")

        # Section 5: Analysis (domain outputs)
        content.append("## Analysis\n\n")
        for domain, output in domain_cots.items():
            content.append(f"### {domain.title()}\n\n")
            # First 1000 chars
            analysis_text = output[:1000]
            if len(output) > 1000:
                analysis_text += "... (truncated)"
            content.append(f"{analysis_text}\n\n")
        content.append("---\n\n")

        # Section 6: Meta-Cognition
        content.append("## Meta-Cognition & Cross-Checks\n\n")
        if metacognition:
            for key, value in metacognition.items():
                label = key.replace('_', ' ').title()
                content.append(f"- **{label}:** {value}\n")
        else:
            content.append("No meta-cognition data available.\n")
        content.append("\n---\n\n")

        # Section 7: Limitations
        content.append("## Limitations & Uncertainty\n\n")

        # From metacognition
        if metacognition and "limitations" in metacognition:
            content.append(f"**Identified Limitations:** {metacognition['limitations']}\n\n")

        # From verification issues
        if verification.get("issues"):
            content.append("**Verification Issues:**\n")
            for issue in verification["issues"][:5]:  # Top 5 issues
                content.append(f"- {issue}\n")
        else:
            content.append("No significant limitations identified.\n")

        content.append("\n---\n\n")

        # Section 8: Conclusions
        content.append("## Final Conclusions\n\n")
        content.append(f"{refined_output}\n\n")
        content.append("---\n\n")

        # Section 9: Appendix
        content.append("## Appendix\n\n")
        content.append("### Technical Details\n\n")
        content.append(f"- **WoT Steps:** {wot_steps}\n")
        content.append(f"- **Processing Time:** {processing_time_ms:.2f}ms\n")
        content.append(f"- **Research Mode:** Enabled\n")
        content.append(f"- **Authority Models:** {len(authority_assignments)}\n\n")
        content.append("*Generated with ANM V0-OpenSource Research Mode*\n")

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(''.join(content))

        return filepath
