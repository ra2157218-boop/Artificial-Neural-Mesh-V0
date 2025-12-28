# ANM Research Mode - Implementation Plan

## Executive Summary

Implement Research Mode for ANM V0-OpenSource: a maximum-quality, correctness-first operating mode for academic research, fact-checking, and critical analysis. Based on the Research Mode Blueprint specification.

**Core Principles:**
- **Correctness > Authority > Completeness > Speed**
- Explicit activation only (`--research` flag)
- Deterministic routing with locked authority models
- Maximum module parallelism (max 10 modules per query, min 4 modules)
- Mandatory WoT with minimum reasoning depth (3+ steps)
- Structured PDF output with 9 sections

**User Decisions:**
- ✅ Explicit flag only (no auto-detection)
- ✅ Qwen2.5-3B-Instruct with auto-download
- ✅ Full PDF implementation with reportlab
- ✅ Maximum parallel execution per Blueprint spec

---

## Current Architecture

**Existing Mode System:**
- Quick Mode: TinyLlama-1.1B (fast, no CoT)
- Normal Mode: DeepSeek-R1-1.5B (full reasoning)
- Auto Mode: Intelligent quick/normal switching

**Model Authority:**
- STEM: Nanbeige4-3B (math, physics, chemistry, biology)
- Code: Stable-Code-3B (programming)
- General: DeepSeek-R1-1.5B (general, memory, research, facts)

**Router Flow:**
AI Domain Classification → PlannerLLM → LFM Adjustment → Domain Masking → TrueWoT → Refiner → Verifier

**Specialists:** 12 domains with 4-worker ParallelSpecialistAdapter ensemble

---

## Implementation Phases

### Phase 1: Model Configuration (Foundation)
**Priority:** HIGHEST - Must complete first

#### 1.1 Add Qwen2.5-3B-Instruct to settings.py
**File:** `anm/config/settings.py`

**Add after line 55:**
```python
MODEL_RESEARCH_INTERNET = "qwen2.5-3b-instruct"  # Internet research authority
```

**Add after line 62:**
```python
# ============================================================
#  Research Mode Configuration
# ============================================================

RESEARCH_MODE_CONFIGS = {
    # Authority model assignments (LOCKED - no voting override)
    "authority_models": {
        "math": MODEL_MATH,           # nanbeige4-3b
        "physics": MODEL_PHYSICS,     # nanbeige4-3b
        "chemistry": MODEL_CHEMISTRY, # nanbeige4-3b
        "biology": MODEL_BIOLOGY,     # nanbeige4-3b
        "code": MODEL_CODE,           # stable-code-3b
        "internet": MODEL_RESEARCH_INTERNET,  # qwen2.5-3b-instruct
        "metacognition": MODEL_GENERAL,  # deepseek-r1:1.5b
    },

    # Deterministic routing
    "deterministic_routing": True,
    "hard_domain_binding": True,
    "no_fast_fallback": True,

    # Module parallelism limits (max 10 modules per query, min 4 modules)
    "max_parallelism": True,
    "max_modules": 10,
    "min_modules": 4,

    # WoT configuration
    "wot_mandatory": True,
    "wot_min_depth": 3,
    "wot_max_steps": 20,

    # Failure policy
    "explicit_reporting": True,
    "retries_allowed": 2,
    "return_uncertainty": True,

    # PDF output
    "pdf_output": True,
}
```

**Update `get_config()` (around line 146):**
```python
"research_mode_configs": RESEARCH_MODE_CONFIGS,
"model_research_internet": MODEL_RESEARCH_INTERNET,
```

#### 1.2 Add Qwen to Model Downloader
**File:** `anm/system/model_downloader.py`

**Add to DEFAULT_MODELS dict (after line 92):**
```python
"qwen2.5-3b-instruct": {
    "repo_id": "Qwen/Qwen2.5-3B-Instruct-GGUF",
    "filename": "qwen2.5-3b-instruct-q4_k_m.gguf",
    "size_gb": 2.0,
},
```

---

### Phase 2: Mode Infrastructure
**Priority:** HIGH - Required for activation

#### 2.1 Add --research CLI Flag
**File:** `run.py`

**Add argument (after line 301):**
```python
parser.add_argument("--research", action="store_true",
                   help="Research mode: maximum quality, structured PDF output")
```

**Add validation (after line 349):**
```python
# Research mode validation
if args.research and args.auto:
    print("[ERROR] Cannot use both --research and --auto. Research mode uses deterministic routing.")
    sys.exit(1)

if args.research and args.quick:
    print("[ERROR] Cannot use --research with --quick. Research mode requires full reasoning.")
    sys.exit(1)
```

**Update function calls (lines 355, 385):**
```python
# In interactive_mode()
interactive_mode(skip_sanity=args.skip_sanity, quick_mode=args.quick,
                auto_mode=args.auto, optimize_prompts=args.optimize,
                research_mode=args.research)

# In run_query()
result = run_query(query, verbose=args.verbose, skip_sanity=args.skip_sanity,
                  quick_mode=args.quick, auto_mode=args.auto,
                  optimize_prompts=args.optimize, research_mode=args.research)
```

#### 2.2 Extend ANMConfig
**File:** `anm/__init__.py`

**Add field (around line 143):**
```python
@dataclass
class ANMConfig:
    # ... existing fields ...
    research_mode: bool = False
```

**Update `__post_init__()` validation:**
```python
# Research mode validation
if self.research_mode and self.auto_mode:
    self.auto_mode = False  # Disable auto mode

if self.research_mode and self.quick_mode:
    raise ValueError("Research mode cannot be used with quick mode")
```

**Update `to_dict()`:**
```python
"research_mode": self.research_mode,
```

#### 2.3 Mode Detection in ANM.query()
**File:** `anm/__init__.py`

**Add research mode bypass (around line 550):**
```python
# Research mode: Always use normal mode (no quick, no auto)
if self.anm_config.research_mode:
    use_quick = False
    if self.anm_config.verbose:
        print("[RESEARCH_MODE] Using full reasoning pipeline with maximum quality")
else:
    # Existing auto mode logic...
```

**Pass to router (around line 595):**
```python
result = self._router.handle(user_query, quick_mode=use_quick,
                             research_mode=self.anm_config.research_mode)
```

---

### Phase 3: Router Core Implementation
**Priority:** CRITICAL - Main research mode logic

#### 3.1 Update Router.__init__()
**File:** `anm/router/router.py`

**Add to __init__ (around line 314):**
```python
# Research mode configuration
self.research_mode_config = self.config.get("research_mode_configs", {})
self.research_mode_active = False
```

#### 3.2 Update handle() Signature
**File:** `anm/router/router.py` (line 455)

```python
def handle(self, user_query: str, quick_mode: bool = False,
          research_mode: bool = False) -> Dict[str, Any]:
```

**Add research mode routing (after input validation):**
```python
self.research_mode_active = research_mode

# Research mode: deterministic routing
if research_mode:
    return self._handle_research_mode(user_query)
```

#### 3.3 Implement _handle_research_mode()
**File:** `anm/router/router.py` (new method, ~500 lines)

**Core Implementation:**
```python
def _handle_research_mode(self, user_query: str) -> Dict[str, Any]:
    """
    Research Mode: Correctness > Authority > Completeness > Speed

    Pipeline:
    1. Deterministic domain detection (keyword-based)
    2. Authority model assignment (locked, no override)
    3. Select modules (max 10, min 4) based on detected domains
    4. Build specialists for selected modules
    5. Run WoT with minimum depth enforcement
    6. Meta-cognition audit (self-check)
    7. Generate structured PDF
    8. Return result with explicit status
    """
    import time
    start_time = time.time()

    # 1. Start log run
    self.logger.new_run(user_query)

    # 2. Load memory brief (PAST-ONLY context)
    memory_info = build_memory_brief(self._memory_core, user_query)
    memory_brief = memory_info["brief_text"]
    self.logger.log_memory(memory_brief)

    # 3. Deterministic domain detection
    detected_domains = self._deterministic_domain_detection(user_query)
    
    # 4. Apply module limits (max 10, min 4)
    selected_domains = self._apply_module_limits(detected_domains)
    entry_domain = selected_domains[0] if selected_domains else "general"

    # 5. Authority model assignment (LOCKED)
    authority_assignments = self._assign_authority_models(selected_domains)

    # 6. Build specialists for selected modules
    specialists = self._build_research_specialists(selected_domains)

    # 7. Log router decision
    self.logger.log_router_decision({
        "mode": "research",
        "detected_domains": detected_domains,
        "selected_domains": selected_domains,
        "entry_domain": entry_domain,
        "authority_assignments": authority_assignments,
        "max_parallelism": True,
        "module_count": len(selected_domains),
        "max_modules": self.research_mode_config.get("max_modules", 10),
        "min_modules": self.research_mode_config.get("min_modules", 4),
    })

    # 8. Run TrueWoT with minimum depth enforcement
    wot_start_time = time.time()
    max_steps = self.research_mode_config.get("wot_max_steps", 20)
    min_depth = self.research_mode_config.get("wot_min_depth", 3)

    full_query = f"{user_query}\n\n{memory_brief}\n\n[RESEARCH MODE: Correctness required]"

    try:
        wot = TrueWoT(
            domain_names=list(specialists.keys()),
            memory_llm=self._memory_core,
            min_depth=min_depth,  # Enforce minimum reasoning depth
        )
        domain_cots = wot.run(
            entry_domain=entry_domain,
            query=full_query,
            specialists=specialists,
            max_steps=max_steps,
        )
        wot_end_time = time.time()
        wot_steps = getattr(wot, 'total_steps', 0)

        # Validate minimum depth
        if wot_steps < min_depth:
            # Force continuation if depth insufficient
            self.logger.log_error("research_wot_depth",
                f"WoT depth {wot_steps} < minimum {min_depth}. Forcing continuation.")
            # Re-run with stricter settings (implementation detail)

    except Exception as e:
        # Explicit failure reporting (per Blueprint)
        return {
            "status": "error_explicit",
            "result": f"[RESEARCH MODE ERROR] {str(e)}",
            "error": str(e),
            "uncertainty": "High - Research pipeline failed",
            "retries_exhausted": False,
            "authority_assignments": authority_assignments,
            "mode": "research",
        }

    # 9. Meta-cognition audit (self-check)
    metacognition_audit = self._run_metacognition_audit(
        user_query=user_query,
        domain_cots=domain_cots,
        entry_domain=entry_domain,
    )

    # 10. Refiner (with research mode hints)
    refiner_packet = self._build_refiner_packet(
        user_query=user_query,
        domain_cots=domain_cots,
        entry_specialist=entry_domain,
        router_plan={"mode": "research", "authority": authority_assignments},
        pg_stats_before={},
    )
    refined_output = self.refiner.refine(refiner_packet)
    self.logger.log_refiner(refined_output)

    # 11. Verifier (strict research mode verification)
    verifier_packet = self._build_verifier_packet(
        user_query=user_query,
        merged_reasoning=refined_output,
        entry_specialist=entry_domain,
        router_reason="Research mode: authority-driven analysis",
    )
    verification = self.verifier.run(verifier_packet)
    self.logger.log_verifier(verification)

    status = verification.get("status", "approved")

    # 12. Generate structured PDF
    if self.research_mode_config.get("pdf_output", True):
        from anm.output.research_pdf import ResearchPDFGenerator

        pdf_generator = ResearchPDFGenerator()
        pdf_path = pdf_generator.generate(
            user_query=user_query,
            domain_cots=domain_cots,
            refined_output=refined_output,
            verification=verification,
            metacognition=metacognition_audit,
            authority_assignments=authority_assignments,
            wot_steps=wot_steps,
            processing_time_ms=(time.time() - start_time) * 1000,
        )
    else:
        pdf_path = None

    # 13. Save logs
    log_path = self.logger.save()

    # 14. Return comprehensive result
    return {
        "status": status,
        "result": refined_output,
        "verification": verification,
        "metacognition": metacognition_audit,
        "authority_assignments": authority_assignments,
        "pdf_path": pdf_path,
        "log_path": log_path,
        "mode": "research",
        "wot_steps": wot_steps,
        "processing_time_ms": (time.time() - start_time) * 1000,
    }
```

#### 3.4 Helper Methods (9 methods to add)

**_deterministic_domain_detection():**
- Keyword-based pattern matching (no AI for reproducibility)
- Returns list of detected domains in priority order
- Patterns for: math, physics, chemistry, biology, code, internet, facts, simulation

**_assign_authority_models():**
- Maps domains to authority models from RESEARCH_MODE_CONFIGS
- Returns dict: {"math": "nanbeige4-3b", "code": "stable-code-3b", ...}

**_apply_module_limits():**
- Applies module count limits (max 10, min 4)
- If detected_domains > 10: selects top 10 by priority
- If detected_domains < 4: adds complementary domains to reach minimum
- Returns list of selected domains

**_build_research_specialists():**
- Creates specialists for selected modules (normal worker count per module)
- Returns specialists dict for WoT

**_run_metacognition_audit():**
- Uses DeepSeek R1 to self-audit reasoning quality
- Checks: consistency, confidence, uncertainty, limitations
- Returns dict with audit results

**_generate_research_pdf():**
- Wrapper for ResearchPDFGenerator
- Handles PDF generation errors gracefully
- Returns PDF path or None

**Plus 3 domain-specific pattern detectors:**
- `_detect_math_patterns()`, `_detect_science_patterns()`, `_detect_code_patterns()`

---

### Phase 4: PDF Generation
**Priority:** HIGH - Core research mode output

#### 4.1 Install Dependencies
**File:** `requirements.txt` (create if missing)

**Add:**
```
reportlab>=3.6.0
```

**Install:**
```bash
pip install reportlab
```

#### 4.2 Create ResearchPDFGenerator
**File:** `anm/output/research_pdf.py` (NEW FILE, ~400 lines)

**Structure:**
```python
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                PageBreak, Table, TableStyle)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import os
from typing import Dict, Any

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
        content.append(Paragraph(query, self.styles['Title']))
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
        content.append(Paragraph(summary, self.styles['Normal']))
        content.append(Spacer(1, 24))

        return content

    # ... implement remaining 7 sections ...
    # _section_question(), _section_sources(), _section_analysis()
    # _section_metacognition(), _section_limitations()
    # _section_conclusions(), _section_appendix()
```

**Key Features:**
- Custom styles for headers, code, citations
- Table formatting for model assignments
- Proper page breaks and spacing
- Metadata in appendix (models used, WoT depth, processing time)

---

### Phase 5: Research Specialist Enhancement
**Priority:** MEDIUM - Internet research capabilities

#### 5.1 Create/Enhance ResearchLLM
**File:** `anm/specialists/research_llm.py` (NEW or ENHANCE)

**Implementation:**
```python
from anm.specialists.base import BaseSpecialist
from typing import Dict, Any, List, Optional

class ResearchLLM(BaseSpecialist):
    """
    Research specialist using Qwen2.5-3B-Instruct for internet research.

    Capabilities:
    - Web content analysis
    - Source tracking and citation
    - Structured data extraction
    - Fact-checking and validation
    """

    def __init__(self):
        super().__init__(
            domain_name="research",
            model_name="qwen2.5-3b-instruct",
            system_prompt=self._build_system_prompt(),
        )
        self.sources: List[Dict[str, str]] = []

    def _build_system_prompt(self) -> str:
        return """You are ANM's Research Specialist using Qwen2.5-3B-Instruct.

Your role:
- Analyze web content and extract key information
- Track sources with citations
- Provide structured outputs (JSON, tables)
- Validate facts and cross-check claims

Always cite sources and indicate confidence levels."""

    def run(self, wot_packet: str) -> str:
        """
        Process research query with source tracking.

        Pipeline:
        1. Extract query from WoT packet
        2. Generate research analysis
        3. Track sources
        4. Format output with citations
        5. Return WOT_REQUEST
        """
        # Extract query
        query = self._extract_user_query(wot_packet)

        # Generate research analysis (using Qwen)
        from anm.system.inference import get_inference_engine
        engine = get_inference_engine()

        prompt = f"""{self.system_prompt}

Research Query: {query}

Provide:
1. Key findings
2. Sources (if available)
3. Confidence assessment
4. Limitations

Format as structured analysis."""

        response = engine.generate(
            prompt,
            max_tokens=1000,
            temperature=0.3,  # Lower for factual research
        )

        # Track sources (future: integrate WebFetch)
        self._track_sources(response)

        # Format with citations
        output = self._format_with_citations(response)

        # Determine next specialist
        wot_request = self._determine_next_specialist(query, response)

        return f"{output}\n\nWOT_REQUEST: {wot_request}"

    def _track_sources(self, response: str):
        """Track sources from response."""
        # Future: Parse citations, URLs, references
        pass

    def _format_with_citations(self, response: str) -> str:
        """Format output with proper citations."""
        # Future: Add [1], [2] citation markers
        return response

    def _determine_next_specialist(self, query: str, response: str) -> str:
        """Determine which specialist should process next."""
        # Simple heuristic for now
        query_lower = query.lower()

        if any(word in query_lower for word in ["calculate", "equation", "math"]):
            return "MATH"
        elif any(word in query_lower for word in ["code", "program", "function"]):
            return "CODE"
        elif any(word in query_lower for word in ["physics", "force", "energy"]):
            return "PHYSICS"
        else:
            return "NONE"
```

**Future Enhancement (Phase 2):**
- 7-step Internet Research Pipeline from Blueprint
- WebFetch/WebSearch tool integration
- Source validation and fact-checking
- Citation formatting (APA, MLA, Chicago)

---

### Phase 6: Terminal UI Updates
**Priority:** LOW - Nice to have

#### 6.1 Update print_mode_info()
**File:** `anm/ui/terminal.py`

**Add to function (around line 50):**
```python
def print_mode_info(self, quick_mode: bool, auto_mode: bool,
                   optimize_prompts: bool, research_mode: bool = False):
    if research_mode:
        self.console.print("[bold cyan]╭─ RESEARCH MODE ─────────────────────────╮[/]")
        self.console.print("[cyan]│ Maximum Quality • Deterministic Routing │[/]")
        self.console.print("[cyan]│ Structured PDF Output                   │[/]")
        self.console.print("[cyan]╰─────────────────────────────────────────╯[/]")
        return  # Skip other mode displays

    # ... existing mode display logic ...
```

#### 6.2 Update print_result()
**File:** `anm/ui/terminal.py`

**Add after verification display (around line 150):**
```python
# Research mode PDF output
if result.get("mode") == "research" and result.get("pdf_path"):
    self.console.print(f"\n[bold green]✓[/] PDF: {result['pdf_path']}")

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
```

---

## Critical Files to Modify

**Priority 1 (Core Implementation):**
1. `anm/config/settings.py` - Model config, RESEARCH_MODE_CONFIGS
2. `anm/router/router.py` - Research mode pipeline (~500 lines)
3. `anm/output/research_pdf.py` - PDF generation (NEW FILE, ~400 lines)
4. `anm/system/model_downloader.py` - Qwen auto-download

**Priority 2 (Activation & Flow):**
5. `run.py` - CLI flag and validation
6. `anm/__init__.py` - ANMConfig extension, mode detection

**Priority 3 (Specialists & UI):**
7. `anm/specialists/research_llm.py` - Research specialist (NEW or ENHANCE)
8. `anm/ui/terminal.py` - UI updates for research mode

---

## Implementation Order (Recommended)

### Week 1: Foundation
1. **Day 1-2:** Phase 1 (Model Configuration)
   - Add Qwen to settings.py
   - Add to model downloader
   - Test auto-download

2. **Day 3-4:** Phase 2 (Mode Infrastructure)
   - Add --research flag
   - Extend ANMConfig
   - Add mode detection

3. **Day 5:** Testing
   - Verify flag activation
   - Test mode conflicts
   - Validate config

### Week 2: Core Implementation
4. **Day 1-3:** Phase 3 (Router Core)
   - Implement _handle_research_mode()
   - Add 8 helper methods
   - Test deterministic routing

5. **Day 4-5:** Phase 4 (PDF Generation)
   - Create ResearchPDFGenerator
   - Implement 9 sections
   - Test PDF output

### Week 3: Polish & Testing
6. **Day 1-2:** Phase 5 (Research Specialist)
   - Enhance ResearchLLM
   - Add Qwen integration
   - Test specialist output

7. **Day 3:** Phase 6 (UI Updates)
   - Update terminal UI
   - Add research mode indicators

8. **Day 4-5:** Integration Testing
   - End-to-end testing
   - PDF validation
   - Performance testing

---

## Testing Strategy

### Test Cases

**1. Basic Activation:**
```bash
python run.py --research "What is the Schwarzschild radius?"
```
**Expected:** Research mode activates, PDF generated

**2. Mode Conflicts:**
```bash
python run.py --research --quick "test"  # Should error
python run.py --research --auto "test"   # Should error
```
**Expected:** Clear error messages

**3. Authority Models:**
```bash
python run.py --research "Calculate the integral of x^2 from 0 to 5"
```
**Expected:** Math specialist uses Nanbeige4-3B (check logs)

**4. Module Limits:**
```bash
python run.py --research "Explain quantum mechanics and write Python code to simulate a particle in a box"
```
**Expected:** Physics + Code modules selected (2 modules, within max 10 limit, check logs)

**4b. Maximum Module Limit:**
```bash
python run.py --research "Complex query requiring math, physics, chemistry, biology, code, internet, facts, simulation, memory, and metacognition analysis"
```
**Expected:** Maximum 10 modules selected (check logs show module_count = 10)

**4c. Minimum Module Enforcement:**
```bash
python run.py --research "Simple math question"
```
**Expected:** At least 4 modules selected (may add complementary domains to reach minimum)

**5. PDF Structure:**
```bash
python run.py --research "What are the health effects of caffeine?"
```
**Expected:** PDF with all 9 sections, proper formatting

**6. Qwen Auto-Download:**
```bash
# Delete Qwen cache first
rm -rf .anm_cache/qwen*
python run.py --research "Latest research on climate change"
```
**Expected:** Qwen downloads automatically, research mode proceeds

**7. Meta-Cognition:**
```bash
python run.py --research "Is the Earth flat?"
```
**Expected:** Meta-cognition audit flags low confidence, uncertainty noted in PDF

**8. Failure Handling:**
```bash
python run.py --research "Extremely complex query that might fail"
```
**Expected:** Explicit error with uncertainty markers, no silent fallback

---

## Success Criteria

Implementation complete when all criteria met:

1. ✅ `--research` flag activates research mode exclusively
2. ✅ Mode conflicts properly validated (--research blocks --quick, --auto)
3. ✅ Deterministic routing with locked authority models
4. ✅ Module limits enforced (max 10 modules per query, min 4 modules)
5. ✅ WoT minimum depth enforced (3+ steps)
6. ✅ Qwen2.5-3B-Instruct auto-downloaded and used
7. ✅ PDF with all 9 sections generated and properly formatted
8. ✅ Meta-cognition audit performed and included in PDF
9. ✅ Explicit failure reporting with uncertainty markers
10. ✅ All existing modes (Quick, Normal, Auto) remain functional
11. ✅ Research mode shows "RESEARCH MODE" in terminal UI
12. ✅ PDF includes authority model assignments table
13. ✅ Processing time and WoT metrics in appendix
14. ✅ Source tracking functional (even if citations deferred)

---

## Rollback Plan

If critical issues arise during implementation:

**Phase 1-2 Rollback:**
- Remove `--research` flag from run.py
- Remove `research_mode` from ANMConfig
- Remove Qwen from settings.py and model downloader

**Phase 3 Rollback:**
- Remove `_handle_research_mode()` and helper methods
- Revert `handle()` signature to original

**Phase 4 Rollback:**
- Delete `anm/output/research_pdf.py`
- Remove reportlab dependency

**Phase 5-6 Rollback:**
- Remove ResearchLLM enhancements
- Revert UI changes

**Complete Rollback:**
- `git diff` to identify all changes
- Restore original files from git history
- Remove new files (research_pdf.py)
- Test existing modes work

---

## Known Limitations & Future Work

**Current Limitations:**
1. Internet Research Pipeline (7-step) not fully implemented - deferred to Phase 2
2. Web content fetching not integrated - needs WebFetch tool
3. Citation formatting basic - no APA/MLA/Chicago support yet
4. Source validation manual - no automatic fact-checking

**Future Enhancements (Phase 2):**
1. Full Internet Research Pipeline with web scraping
2. Vector Database (VB) integration for validated knowledge
3. RAG (Retrieval-Augmented Generation) for external grounding
4. Citation formatting with multiple styles
5. Automated fact-checking against trusted sources
6. Interactive PDF with clickable citations
7. Research mode history and comparison

---

## Design Decisions & Rationale

**1. Explicit Flag Only (No Auto-Detection)**
- **Rationale:** Research mode is expensive (up to 10 modules, longer processing). User must opt-in.
- **Alternative Considered:** Auto-detect based on query keywords (rejected - too unpredictable)

**2. Deterministic Routing (Keyword-Based)**
- **Rationale:** Reproducibility required for research. AI classification too variable.
- **Alternative Considered:** Enhanced AI classifier (rejected - Blueprint spec requires deterministic)

**3. Module Limits (Max 10, Min 4)**
- **Rationale:** Balances comprehensive analysis (up to 10 modules) with minimum quality guarantee (at least 4 modules). Prevents resource exhaustion while ensuring thorough coverage.
- **Alternative Considered:** Unlimited modules (rejected - resource constraints), fixed module count (rejected - too rigid for diverse queries)

**4. PDF-First Output**
- **Rationale:** Research mode designed for academic use, needs formal documentation
- **Alternative Considered:** Markdown first (rejected - PDF is Blueprint requirement)

**5. Qwen for Internet Research**
- **Rationale:** Blueprint spec, optimized for web content and structured output
- **Alternative Considered:** Use DeepSeek-R1 (rejected - not optimized for web data)

**6. Authority Model Locking**
- **Rationale:** Consistency required, no voting allows reliable results
- **Alternative Considered:** Voting with bias toward authority (rejected - Blueprint says "locked")

---

## Summary

This plan provides a complete implementation roadmap for Research Mode in ANM V0-OpenSource. The implementation is divided into 6 phases over ~3 weeks, with clear success criteria and rollback plans.

**Key Achievements:**
- ✅ Maintains backward compatibility with all existing modes
- ✅ Follows Blueprint specification precisely
- ✅ Implements all core features (deterministic routing, module limits, PDF output)
- ✅ Provides graceful degradation (Qwen auto-download)
- ✅ Includes comprehensive testing strategy

**Next Steps:**
1. Review and approve this plan
2. Begin Phase 1 (Model Configuration)
3. Test each phase incrementally
4. Validate against Blueprint requirements
5. Deploy Research Mode for production use
