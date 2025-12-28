"""
ANM Research Mode PDF Generator

Generates structured research PDFs with 9 sections per Blueprint specification.
"""

from datetime import datetime
import os
from typing import Dict, Any

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    PageBreak, Table, TableStyle)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class ResearchPDFGenerator:
    """
    Generate structured research PDF with 9 sections per Blueprint spec.

    Sections:
    1. Title Page
    2. Executive Summary
    3. Research Question & Scope
    4. Sources & Data (authority model assignments)
    5. Analysis (domain specialist outputs)
    6. Meta-Cognition & Cross-Checks
    7. Limitations & Uncertainty
    8. Final Conclusions
    9. Appendix (models, WoT metrics, logs)
    """

    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is not installed. Install with: pip install reportlab")

        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Create custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
        ))

        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2563eb'),
            spaceBefore=12,
            spaceAfter=6,
        ))

        # Subsection header style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e40af'),
            spaceBefore=10,
            spaceAfter=4,
        ))

        # Code style
        self.styles.add(ParagraphStyle(
            name='Code',
            parent=self.styles['Code'],
            fontSize=9,
            fontName='Courier',
            leftIndent=20,
            textColor=colors.HexColor('#1f2937'),
        ))

    def generate(self, user_query: str, domain_cots: Dict[str, str],
                refined_output: str, verification: Dict[str, Any],
                metacognition: Dict[str, Any], authority_assignments: Dict[str, str],
                wot_steps: int, processing_time_ms: float) -> str:
        """
        Generate PDF with 9-section structure.

        Returns: PDF file path
        """
        # Create output directory
        output_dir = "research_outputs"
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"research_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)

        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=letter,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)

        # Build content
        story = []

        # Section 1: Title Page
        story.extend(self._section_title(user_query))
        story.append(PageBreak())

        # Section 2: Executive Summary
        story.extend(self._section_summary(refined_output, verification))

        # Section 3: Research Question & Scope
        story.extend(self._section_question(user_query, domain_cots))

        # Section 4: Sources & Data
        story.extend(self._section_sources(authority_assignments))

        # Section 5: Analysis
        story.extend(self._section_analysis(domain_cots))

        # Section 6: Meta-Cognition
        story.extend(self._section_metacognition(metacognition))

        # Section 7: Limitations
        story.extend(self._section_limitations(metacognition, verification))

        # Section 8: Conclusions
        story.extend(self._section_conclusions(refined_output))

        # Section 9: Appendix
        story.extend(self._section_appendix(authority_assignments,
                                            wot_steps, processing_time_ms))

        # Build PDF
        doc.build(story)

        return filepath

    def _section_title(self, query: str):
        """Section 1: Title Page"""
        content = []

        content.append(Spacer(1, 2*inch))
        content.append(Paragraph("ANM Research Mode", self.styles['CustomTitle']))
        content.append(Spacer(1, 0.5*inch))

        # Escape HTML characters in query
        safe_query = self._escape_html(query)
        content.append(Paragraph(safe_query, self.styles['Title']))
        content.append(Spacer(1, 0.3*inch))

        timestamp = datetime.now().strftime("%B %d, %Y at %H:%M")
        content.append(Paragraph(f"<i>Generated: {timestamp}</i>",
                                self.styles['Normal']))

        return content

    def _section_summary(self, refined_output: str, verification: Dict[str, Any]):
        """Section 2: Executive Summary"""
        content = []

        content.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        content.append(Spacer(1, 12))

        # Verification status
        status = verification.get("status", "unknown")
        status_color = "green" if status == "approved" else "red"
        content.append(Paragraph(
            f"<b>Verification Status:</b> <font color='{status_color}'>{status.upper()}</font>",
            self.styles['Normal']
        ))
        content.append(Spacer(1, 12))

        # Extract first 500 chars of refined output
        summary = refined_output[:500] + "..." if len(refined_output) > 500 else refined_output
        safe_summary = self._escape_html(summary)
        content.append(Paragraph(safe_summary, self.styles['Normal']))
        content.append(Spacer(1, 24))

        return content

    def _section_question(self, user_query: str, domain_cots: Dict[str, str]):
        """Section 3: Research Question & Scope"""
        content = []

        content.append(Paragraph("Research Question & Scope", self.styles['SectionHeader']))
        content.append(Spacer(1, 12))

        content.append(Paragraph("<b>Query:</b>", self.styles['Normal']))
        safe_query = self._escape_html(user_query)
        content.append(Paragraph(safe_query, self.styles['Normal']))
        content.append(Spacer(1, 12))

        content.append(Paragraph(f"<b>Domains Analyzed:</b> {', '.join(domain_cots.keys())}",
                                self.styles['Normal']))
        content.append(Spacer(1, 24))

        return content

    def _section_sources(self, authority_assignments: Dict[str, str]):
        """Section 4: Sources & Data"""
        content = []

        content.append(Paragraph("Sources & Data", self.styles['SectionHeader']))
        content.append(Spacer(1, 12))

        content.append(Paragraph("Authority Model Assignments", self.styles['SubsectionHeader']))
        content.append(Spacer(1, 8))

        # Create table
        table_data = [["Domain", "Authority Model"]]
        for domain, model in authority_assignments.items():
            table_data.append([domain.title(), model])

        table = Table(table_data, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        content.append(table)
        content.append(Spacer(1, 24))

        return content

    def _section_analysis(self, domain_cots: Dict[str, str]):
        """Section 5: Analysis (domain outputs)"""
        content = []

        content.append(Paragraph("Analysis", self.styles['SectionHeader']))
        content.append(Spacer(1, 12))

        for domain, output in domain_cots.items():
            content.append(Paragraph(f"{domain.title()}", self.styles['SubsectionHeader']))
            content.append(Spacer(1, 6))

            safe_output = self._escape_html(output[:1000])  # First 1000 chars
            if len(output) > 1000:
                safe_output += "... (truncated)"
            content.append(Paragraph(safe_output, self.styles['Normal']))
            content.append(Spacer(1, 12))

        content.append(Spacer(1, 12))

        return content

    def _section_metacognition(self, metacognition: Dict[str, Any]):
        """Section 6: Meta-Cognition & Cross-Checks"""
        content = []

        content.append(Paragraph("Meta-Cognition & Cross-Checks", self.styles['SectionHeader']))
        content.append(Spacer(1, 12))

        if metacognition:
            for key, value in metacognition.items():
                label = key.replace('_', ' ').title()
                safe_value = self._escape_html(str(value))
                content.append(Paragraph(f"<b>{label}:</b> {safe_value}", self.styles['Normal']))
                content.append(Spacer(1, 6))
        else:
            content.append(Paragraph("No meta-cognition data available.", self.styles['Normal']))

        content.append(Spacer(1, 24))

        return content

    def _section_limitations(self, metacognition: Dict[str, Any], verification: Dict[str, Any]):
        """Section 7: Limitations & Uncertainty"""
        content = []

        content.append(Paragraph("Limitations & Uncertainty", self.styles['SectionHeader']))
        content.append(Spacer(1, 12))

        # From metacognition
        if metacognition and "limitations" in metacognition:
            safe_limitations = self._escape_html(str(metacognition["limitations"]))
            content.append(Paragraph(f"<b>Identified Limitations:</b> {safe_limitations}",
                                    self.styles['Normal']))
            content.append(Spacer(1, 8))

        # From verification issues
        if verification.get("issues"):
            content.append(Paragraph("<b>Verification Issues:</b>", self.styles['Normal']))
            for issue in verification["issues"][:5]:  # Top 5 issues
                safe_issue = self._escape_html(str(issue))
                content.append(Paragraph(f"• {safe_issue}", self.styles['Normal']))
            content.append(Spacer(1, 8))

        content.append(Spacer(1, 24))

        return content

    def _section_conclusions(self, refined_output: str):
        """Section 8: Final Conclusions"""
        content = []

        content.append(Paragraph("Final Conclusions", self.styles['SectionHeader']))
        content.append(Spacer(1, 12))

        safe_output = self._escape_html(refined_output)
        content.append(Paragraph(safe_output, self.styles['Normal']))
        content.append(Spacer(1, 24))

        return content

    def _section_appendix(self, authority_assignments: Dict[str, str],
                         wot_steps: int, processing_time_ms: float):
        """Section 9: Appendix (technical details)"""
        content = []

        content.append(Paragraph("Appendix", self.styles['SectionHeader']))
        content.append(Spacer(1, 12))

        content.append(Paragraph("Technical Details", self.styles['SubsectionHeader']))
        content.append(Spacer(1, 8))

        content.append(Paragraph(f"<b>WoT Steps:</b> {wot_steps}", self.styles['Normal']))
        content.append(Paragraph(f"<b>Processing Time:</b> {processing_time_ms:.2f}ms",
                                self.styles['Normal']))
        content.append(Paragraph(f"<b>Research Mode:</b> Enabled", self.styles['Normal']))
        content.append(Paragraph(f"<b>Authority Models:</b> {len(authority_assignments)}",
                                self.styles['Normal']))
        content.append(Spacer(1, 12))

        content.append(Paragraph("<i>Generated with ANM V0-OpenSource Research Mode</i>",
                                self.styles['Normal']))

        return content

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters for reportlab."""
        if not isinstance(text, str):
            text = str(text)

        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text
