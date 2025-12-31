"""
ANM Research Mode PDF Generator - Academic Format

Generates professional academic-style research PDFs with:
- Two-column layout
- Header/footer with page numbers
- Abstract box with grey background
- Figure placeholders
- Professional typography
"""

from datetime import datetime
import os
import re
from typing import Dict, Any, List, Callable, Optional

try:
    from anm.output.pdf_refiner import PDFRefiner
    PDF_REFINER_AVAILABLE = True
except ImportError:
    PDF_REFINER_AVAILABLE = False
    PDFRefiner = None

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import (
        BaseDocTemplate, Frame, PageTemplate, NextPageTemplate,
        Paragraph, Spacer, PageBreak, Table, TableStyle,
        FrameBreak, KeepTogether, Flowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    # Dummy values for when reportlab is not available
    inch = 72
    cm = 28.35
    letter = (612, 792)
    TA_JUSTIFY = 4
    TA_CENTER = 1
    TA_LEFT = 0
    class Flowable:
        pass
    class colors:
        class HexColor:
            def __init__(self, c): pass
        black = None
        white = None


class GrayBox(Flowable):
    """A flowable that draws a grey background box around content."""

    def __init__(self, content: List[Flowable], width: float, padding: float = 10):
        Flowable.__init__(self)
        self.content = content
        self.box_width = width
        self.padding = padding
        self._fixed_height = None

    def wrap(self, availWidth, availHeight):
        # Calculate height needed for content
        total_height = 0
        for item in self.content:
            w, h = item.wrap(self.box_width - 2 * self.padding, availHeight)
            total_height += h
        self._fixed_height = total_height + 2 * self.padding
        return self.box_width, self._fixed_height

    def draw(self):
        # Draw grey background
        self.canv.setFillColor(colors.HexColor('#f3f4f6'))
        self.canv.setStrokeColor(colors.HexColor('#d1d5db'))
        self.canv.roundRect(0, 0, self.box_width, self._fixed_height, 5, fill=1, stroke=1)

        # Draw content
        y = self._fixed_height - self.padding
        for item in self.content:
            w, h = item.wrap(self.box_width - 2 * self.padding, 1000)
            y -= h
            item.drawOn(self.canv, self.padding, y)


class FigurePlaceholder(Flowable):
    """A flowable that draws a figure placeholder box with caption."""

    def __init__(self, caption: str, fig_num: int, width: float = 3*inch, height: float = 2*inch):
        Flowable.__init__(self)
        self.caption = caption
        self.fig_num = fig_num
        self.box_width = width
        self.box_height = height

    def wrap(self, availWidth, availHeight):
        return self.box_width, self.box_height + 30  # Extra space for caption

    def draw(self):
        # Draw placeholder box
        self.canv.setFillColor(colors.HexColor('#f9fafb'))
        self.canv.setStrokeColor(colors.HexColor('#9ca3af'))
        self.canv.setLineWidth(1)
        self.canv.rect(0, 30, self.box_width, self.box_height, fill=1, stroke=1)

        # Draw "Figure placeholder" text in center
        self.canv.setFillColor(colors.HexColor('#6b7280'))
        self.canv.setFont('Helvetica', 10)
        text_width = self.canv.stringWidth('[Figure Placeholder]', 'Helvetica', 10)
        self.canv.drawString(
            (self.box_width - text_width) / 2,
            30 + self.box_height / 2,
            '[Figure Placeholder]'
        )

        # Draw caption below
        self.canv.setFillColor(colors.black)
        self.canv.setFont('Helvetica-Bold', 9)
        caption_text = f"Fig. {self.fig_num}: {self.caption}"
        self.canv.drawString(0, 10, caption_text)


class ResearchPDFGenerator:
    """
    Generate professional academic research paper format PDF.

    Features:
    - Two-column layout for body text
    - Header with running title and page numbers
    - Footer with generation info
    - Abstract box with grey background
    - Figure placeholders with captions
    - Professional typography
    """

    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is not installed. Install with: pip install reportlab")

        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

        # Store document info for header/footer
        self._short_title = ""
        self._page_count = 0

        # Initialize PDF refiner
        if PDF_REFINER_AVAILABLE and PDFRefiner:
            self.refiner = PDFRefiner()
        else:
            self.refiner = None

    def _setup_custom_styles(self):
        """Create custom paragraph styles for academic format."""

        # Main Title - Large, bold, centered
        self.styles.add(ParagraphStyle(
            name='AcademicTitle',
            fontName='Times-Bold',
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=12,
            textColor=colors.HexColor('#1a1a1a'),
        ))

        # Subtitle / Author line
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            fontName='Times-Roman',
            fontSize=12,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=6,
            textColor=colors.HexColor('#4b5563'),
        ))

        # Abstract text
        self.styles.add(ParagraphStyle(
            name='AbstractText',
            fontName='Times-Roman',
            fontSize=10,
            leading=13,
            alignment=TA_JUSTIFY,
            spaceBefore=6,
            spaceAfter=6,
            textColor=colors.HexColor('#1f2937'),
        ))

        # Keywords
        self.styles.add(ParagraphStyle(
            name='Keywords',
            fontName='Times-Roman',
            fontSize=9,
            leading=12,
            spaceBefore=8,
            textColor=colors.HexColor('#374151'),
        ))

        # Section Header (1. Introduction, 2. Methods, etc.)
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=14,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor('#111827'),
        ))

        # Subsection Header
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=12,
            spaceBefore=10,
            spaceAfter=4,
            textColor=colors.HexColor('#1f2937'),
        ))

        # Body Text - Justified, professional
        self.styles.add(ParagraphStyle(
            name='AcademicBody',
            fontName='Times-Roman',
            fontSize=10,
            leading=13,
            alignment=TA_JUSTIFY,
            spaceBefore=0,
            spaceAfter=8,
            textColor=colors.HexColor('#1f2937'),
        ))

        # Figure Caption
        self.styles.add(ParagraphStyle(
            name='FigureCaption',
            fontName='Helvetica',
            fontSize=9,
            leading=11,
            alignment=TA_LEFT,
            spaceBefore=4,
            spaceAfter=12,
            textColor=colors.HexColor('#374151'),
        ))

        # Table Header
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11,
            alignment=TA_LEFT,
        ))

        # Reference / Appendix
        self.styles.add(ParagraphStyle(
            name='Reference',
            fontName='Times-Roman',
            fontSize=9,
            leading=11,
            leftIndent=20,
            firstLineIndent=-20,
            spaceBefore=4,
            spaceAfter=4,
            textColor=colors.HexColor('#374151'),
        ))

    def _create_header_footer(self, canvas, doc):
        """Draw header and footer on each page."""
        canvas.saveState()

        page_width, page_height = letter

        # Header - only on pages after first
        if doc.page > 1:
            # Left side: Short title
            canvas.setFont('Helvetica', 9)
            canvas.setFillColor(colors.HexColor('#6b7280'))

            # Truncate title if too long
            short_title = self._short_title[:50] + "..." if len(self._short_title) > 50 else self._short_title
            canvas.drawString(72, page_height - 40, f"ANM Research • {short_title}")

            # Right side: Page number
            canvas.drawRightString(page_width - 72, page_height - 40, f"Page {doc.page}")

            # Header line
            canvas.setStrokeColor(colors.HexColor('#e5e7eb'))
            canvas.setLineWidth(0.5)
            canvas.line(72, page_height - 48, page_width - 72, page_height - 48)

        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#9ca3af'))
        canvas.drawString(72, 30, "Generated by ANM V0-OpenSource Research Mode")
        canvas.drawRightString(page_width - 72, 30, datetime.now().strftime("%Y-%m-%d"))

        canvas.restoreState()

    def _create_first_page_header_footer(self, canvas, doc):
        """Draw header and footer for first page (no header, just footer)."""
        canvas.saveState()

        page_width, page_height = letter

        # Footer only on first page
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#9ca3af'))
        canvas.drawString(72, 30, "Generated by ANM V0-OpenSource Research Mode")
        canvas.drawRightString(page_width - 72, 30, datetime.now().strftime("%Y-%m-%d"))

        canvas.restoreState()

    def generate(self, user_query: str, domain_cots: Dict[str, str],
                refined_output: str, verification: Dict[str, Any],
                metacognition: Dict[str, Any], authority_assignments: Dict[str, str],
                wot_steps: int, processing_time_ms: float,
                sources: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Generate academic-style PDF with two-column layout.

        Returns: PDF file path
        """
        # Create output directory
        output_dir = "research_outputs"
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"research_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)

        # Store short title for header
        self._short_title = user_query[:60] if len(user_query) > 60 else user_query

        # Refine content
        if self.refiner:
            domain_cots = self.refiner.refine_all_domains(domain_cots)
            refined_output = self.refiner.refine_summary(refined_output)

        # Page dimensions
        page_width, page_height = letter
        margin = 0.75 * inch
        gutter = 0.25 * inch

        # Calculate column widths
        usable_width = page_width - 2 * margin
        column_width = (usable_width - gutter) / 2

        # Create frames for two-column layout
        # First page: Full width for title/abstract, then two columns
        first_page_full_frame = Frame(
            margin, margin + 50,
            usable_width, page_height - 2 * margin - 50,
            id='first_full'
        )

        # Two-column frames for subsequent pages
        left_frame = Frame(
            margin, margin + 50,
            column_width, page_height - 2 * margin - 100,
            id='left'
        )
        right_frame = Frame(
            margin + column_width + gutter, margin + 50,
            column_width, page_height - 2 * margin - 100,
            id='right'
        )

        # Create page templates
        first_page_template = PageTemplate(
            id='first',
            frames=[first_page_full_frame],
            onPage=self._create_first_page_header_footer
        )

        two_column_template = PageTemplate(
            id='twocol',
            frames=[left_frame, right_frame],
            onPage=self._create_header_footer
        )

        # Create document
        doc = BaseDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=margin,
            leftMargin=margin,
            topMargin=margin,
            bottomMargin=margin
        )
        doc.addPageTemplates([first_page_template, two_column_template])

        # Build story (content)
        story = []

        # First page content (full width)
        story.extend(self._build_title_page(user_query, refined_output, verification, domain_cots))

        # Switch to two-column layout
        story.append(NextPageTemplate('twocol'))
        story.append(PageBreak())

        # Two-column content
        story.extend(self._build_introduction(user_query, domain_cots))
        story.extend(self._build_methods(authority_assignments, wot_steps))
        story.extend(self._build_results(domain_cots))
        story.extend(self._build_discussion(metacognition, refined_output))
        story.extend(self._build_limitations(metacognition, verification))
        story.extend(self._build_conclusions(refined_output))
        story.extend(self._build_sources_section(sources or []))
        story.extend(self._build_appendix(authority_assignments, wot_steps, processing_time_ms))

        # Build PDF
        doc.build(story)

        return filepath

    def _build_title_page(self, query: str, summary: str, verification: Dict[str, Any],
                          domain_cots: Dict[str, str]) -> List[Flowable]:
        """Build first page with title and abstract box."""
        content = []

        content.append(Spacer(1, 0.5*inch))

        # Main Title (Research Question)
        safe_query = self._escape_html(query)
        content.append(Paragraph(safe_query, self.styles['AcademicTitle']))
        content.append(Spacer(1, 0.2*inch))

        # Subtitle - System info
        content.append(Paragraph(
            "ANM V0-OpenSource Research Mode",
            self.styles['Subtitle']
        ))
        content.append(Paragraph(
            f"Automated Multi-Domain Analysis System",
            self.styles['Subtitle']
        ))
        content.append(Spacer(1, 0.3*inch))

        # Abstract Box (grey background)
        abstract_content = []

        # Abstract header
        abstract_content.append(Paragraph(
            "<b>Abstract</b>",
            self.styles['AbstractText']
        ))

        # Abstract text
        abstract_text = summary[:1500] if len(summary) > 1500 else summary
        safe_abstract = self._escape_html(abstract_text)
        abstract_content.append(Paragraph(safe_abstract, self.styles['AbstractText']))

        # Status
        status = verification.get("status", "unknown")
        status_text = "Verified" if status == "approved" else "Under Review"
        abstract_content.append(Paragraph(
            f"<b>Status:</b> {status_text}",
            self.styles['AbstractText']
        ))

        # Keywords (from domains)
        keywords = ', '.join([d.title() for d in domain_cots.keys()])
        abstract_content.append(Paragraph(
            f"<b>Keywords:</b> {keywords}",
            self.styles['Keywords']
        ))

        # Date
        date_str = datetime.now().strftime("%B %d, %Y")
        abstract_content.append(Paragraph(
            f"<b>Generated:</b> {date_str}",
            self.styles['Keywords']
        ))

        # Create grey box
        page_width, _ = letter
        box_width = page_width - 1.5 * inch
        abstract_box = GrayBox(abstract_content, box_width, padding=15)
        content.append(abstract_box)

        content.append(Spacer(1, 0.3*inch))

        return content

    def _build_introduction(self, query: str, domain_cots: Dict[str, str]) -> List[Flowable]:
        """Build Introduction section."""
        content = []

        content.append(Paragraph("1. Introduction", self.styles['SectionHeader']))

        content.append(Paragraph("<b>Research Question</b>", self.styles['SubsectionHeader']))
        safe_query = self._escape_html(query)
        content.append(Paragraph(
            f"This research addresses the following question: {safe_query}",
            self.styles['AcademicBody']
        ))

        content.append(Paragraph("<b>Scope and Approach</b>", self.styles['SubsectionHeader']))
        domains_text = ', '.join([d.title() for d in domain_cots.keys()])
        content.append(Paragraph(
            f"A multi-domain analysis approach was employed, utilizing specialized knowledge "
            f"domains including: {domains_text}. Each domain contributes unique analytical "
            f"frameworks to address the research question comprehensively.",
            self.styles['AcademicBody']
        ))

        return content

    def _build_methods(self, authority_assignments: Dict[str, str], wot_steps: int) -> List[Flowable]:
        """Build Methods section."""
        content = []

        content.append(Paragraph("2. Methods", self.styles['SectionHeader']))

        content.append(Paragraph("<b>Research Methodology</b>", self.styles['SubsectionHeader']))
        content.append(Paragraph(
            "This research was conducted using the Artificial Neural Mesh (ANM) V0-OpenSource "
            "Research Mode, employing a Web-of-Thought (WoT) reasoning framework. The system "
            "utilizes specialized domain models to ensure accuracy and analytical depth.",
            self.styles['AcademicBody']
        ))

        content.append(Paragraph(
            f"The analysis proceeded through {wot_steps} WoT reasoning steps, with each step "
            f"building upon previous domain insights to construct a comprehensive response.",
            self.styles['AcademicBody']
        ))

        # Authority Models Table
        content.append(Paragraph("<b>Authority Model Assignments</b>", self.styles['SubsectionHeader']))

        table_data = [["Domain", "Model"]]
        for domain, model in authority_assignments.items():
            table_data.append([domain.title(), model])

        table = Table(table_data, colWidths=[1.2*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9fafb')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ]))
        content.append(table)
        content.append(Spacer(1, 12))

        # Add figure placeholder for methodology
        content.append(FigurePlaceholder(
            "Web-of-Thought Reasoning Framework",
            fig_num=1,
            width=2.8*inch,
            height=1.5*inch
        ))

        return content

    def _build_results(self, domain_cots: Dict[str, str]) -> List[Flowable]:
        """Build Results section with domain analysis."""
        content = []

        content.append(Paragraph("3. Results", self.styles['SectionHeader']))

        content.append(Paragraph(
            "The following sections present the analysis from each specialized domain.",
            self.styles['AcademicBody']
        ))

        for domain, output in domain_cots.items():
            if not output or not output.strip():
                continue

            content.append(Paragraph(f"<b>{domain.title()} Analysis</b>", self.styles['SubsectionHeader']))

            # Truncate long outputs
            if len(output) > 2000:
                output = output[:2000] + "..."

            safe_output = self._escape_html(output)
            content.append(Paragraph(safe_output, self.styles['AcademicBody']))

        return content

    def _build_discussion(self, metacognition: Dict[str, Any], summary: str) -> List[Flowable]:
        """Build Discussion section."""
        content = []

        content.append(Paragraph("4. Discussion", self.styles['SectionHeader']))

        content.append(Paragraph("<b>Meta-Cognitive Analysis</b>", self.styles['SubsectionHeader']))

        if metacognition:
            for key, value in metacognition.items():
                if value and str(value).strip():
                    label = key.replace('_', ' ').title()
                    safe_value = self._escape_html(str(value)[:500])
                    content.append(Paragraph(f"<b>{label}:</b> {safe_value}", self.styles['AcademicBody']))
        else:
            content.append(Paragraph(
                "Meta-cognitive analysis was performed to assess reasoning quality and confidence levels.",
                self.styles['AcademicBody']
            ))

        content.append(Paragraph("<b>Synthesis</b>", self.styles['SubsectionHeader']))

        # Discussion text
        discussion = summary[:1500] if len(summary) > 1500 else summary
        safe_discussion = self._escape_html(discussion)
        content.append(Paragraph(safe_discussion, self.styles['AcademicBody']))

        return content

    def _build_limitations(self, metacognition: Dict[str, Any], verification: Dict[str, Any]) -> List[Flowable]:
        """Build Limitations section."""
        content = []

        content.append(Paragraph("5. Limitations", self.styles['SectionHeader']))

        # From metacognition
        if metacognition and metacognition.get("limitations"):
            safe_limitations = self._escape_html(str(metacognition["limitations"]))
            content.append(Paragraph(f"<b>Identified Limitations:</b> {safe_limitations}", self.styles['AcademicBody']))

        # From verification
        if verification.get("issues"):
            content.append(Paragraph("<b>Verification Notes:</b>", self.styles['AcademicBody']))
            for issue in verification["issues"][:5]:
                safe_issue = self._escape_html(str(issue))
                content.append(Paragraph(f"• {safe_issue}", self.styles['AcademicBody']))

        if not metacognition.get("limitations") and not verification.get("issues"):
            content.append(Paragraph(
                "This analysis is subject to the inherent limitations of automated reasoning systems, "
                "including potential gaps in domain knowledge and the constraints of available data sources.",
                self.styles['AcademicBody']
            ))

        return content

    def _build_conclusions(self, summary: str) -> List[Flowable]:
        """Build Conclusions section."""
        content = []

        content.append(Paragraph("6. Conclusions", self.styles['SectionHeader']))

        safe_summary = self._escape_html(summary)
        content.append(Paragraph(safe_summary, self.styles['AcademicBody']))

        return content

    def _build_sources_section(self, sources: List[Dict[str, str]]) -> List[Flowable]:
        """Build Sources/References section (Blueprint compliance - Section 7)."""
        content = []

        content.append(FrameBreak())  # Start on new column if needed
        content.append(Paragraph("7. Sources", self.styles['SectionHeader']))

        if not sources:
            content.append(Paragraph(
                "No external sources were used in this research. "
                "All analysis was performed using internal domain knowledge models.",
                self.styles['AcademicBody']
            ))
        else:
            # Group sources by domain
            seen_urls = set()
            for i, source in enumerate(sources, 1):
                url = source.get('url', '')
                if url in seen_urls:
                    continue  # Skip duplicates
                seen_urls.add(url)

                title = self._escape_html(source.get('title', 'Source'))
                safe_url = self._escape_html(url) if url else 'N/A'
                domain = source.get('domain', '')

                source_text = f"[{i}] {title}"
                if safe_url and safe_url != 'N/A':
                    source_text += f" - {safe_url}"
                if domain:
                    source_text += f" (via {domain})"

                content.append(Paragraph(source_text, self.styles['AcademicBody']))

        content.append(Spacer(1, 12))

        return content

    def _build_appendix(self, authority_assignments: Dict[str, str],
                        wot_steps: int, processing_time_ms: float) -> List[Flowable]:
        """Build Appendix section."""
        content = []

        content.append(FrameBreak())  # Start on new column if needed
        content.append(Paragraph("8. Appendix: Technical Details", self.styles['SectionHeader']))

        content.append(Paragraph(f"<b>WoT Reasoning Steps:</b> {wot_steps}", self.styles['AcademicBody']))
        content.append(Paragraph(f"<b>Processing Time:</b> {processing_time_ms/1000:.2f} seconds", self.styles['AcademicBody']))
        content.append(Paragraph(f"<b>Research Mode:</b> Enabled", self.styles['AcademicBody']))
        content.append(Paragraph(f"<b>Authority Models Used:</b> {len(authority_assignments)}", self.styles['AcademicBody']))

        content.append(Spacer(1, 12))

        content.append(Paragraph("<b>System Information</b>", self.styles['SubsectionHeader']))
        content.append(Paragraph(
            "This document was automatically generated using the ANM V0-OpenSource Research Mode, "
            "which employs specialized domain models and Web-of-Thought reasoning to produce "
            "comprehensive research outputs.",
            self.styles['AcademicBody']
        ))

        # Add figure placeholder for system architecture
        content.append(FigurePlaceholder(
            "ANM System Architecture Overview",
            fig_num=2,
            width=2.8*inch,
            height=1.5*inch
        ))

        return content

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters for reportlab."""
        if not isinstance(text, str):
            text = str(text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text
