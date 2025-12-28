# ============================================================
#  ANM V0-OpenSource — Biology Specialist
#  Life Sciences & Biological Systems
# ============================================================

"""
ANM Biology Specialist - Biological reasoning and analysis.

Capabilities:
- Cell biology and genetics
- Molecular biology
- Physiology and anatomy
- Ecology and evolution
- Microbiology
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
import re

from anm.specialists.base import (
    BaseSpecialist,
    SpecialistConfig,
    SpecialistDomain,
)

try:
    from anm.utils.prompts import BIOLOGY_PROMPT
except ImportError:
    BIOLOGY_PROMPT = ""

__all__ = ["BiologyLLM"]


class BiologyLLM(BaseSpecialist):
    """
    ANM V0-OpenSource Biology Specialist.
    
    Handles biology reasoning including:
    - Cell biology (organelles, processes)
    - Genetics (DNA, RNA, inheritance)
    - Molecular biology (proteins, enzymes)
    - Physiology (organ systems)
    - Evolution and ecology
    
    Features:
    - Pathway analysis
    - Gene expression reasoning
    - Evolutionary context
    - Systems biology perspective
    """
    
    @property
    def domain(self) -> SpecialistDomain:
        return SpecialistDomain.BIOLOGY
    
    def _get_system_prompt(self) -> str:
        base = BIOLOGY_PROMPT if BIOLOGY_PROMPT else ""
        
        return f"""
{base}

You are the BIOLOGY SPECIALIST of ANM V0-OpenSource.

ROLE:
- Explain biological processes and mechanisms
- Analyze genetic and molecular systems
- Describe physiological functions
- Provide evolutionary context
- Integrate across biological scales

CAPABILITIES:
- Cell Biology: organelles, cell cycle, signaling
- Genetics: inheritance, gene expression, mutations
- Molecular: DNA, RNA, proteins, enzymes
- Physiology: organ systems, homeostasis
- Ecology: ecosystems, populations, evolution
- Microbiology: bacteria, viruses, fungi

CRITICAL RULES:
1. Distinguish hypothesis from established science
2. Note when evidence is limited
3. Consider evolutionary context
4. Respect biological complexity
5. No medical diagnosis or treatment advice

ETHICS:
- No biometric identification claims
- No genetic determinism statements
- Respect privacy in genetic discussions
- Acknowledge uncertainty in predictions

OUTPUT FORMAT:
For processes:
- Describe mechanism step-by-step
- Note key molecules/structures
- Explain regulation
- Provide context (cell type, organism)

For analysis:
- State what is known
- Note uncertainties
- Provide evolutionary perspective if relevant
"""
    
    def _build_meta_block(self, text: str) -> str:
        """Build meta with biology-specific info."""
        base_meta = super()._build_meta_block(text)
        
        # Biology-specific analysis
        bio_area = self._detect_biology_area(text)
        processes = self._detect_processes(text)
        organisms = self._detect_organisms(text)
        
        bio_meta = [
            "",
            "[BIOLOGY_ANALYSIS]",
            f"biology_area: {bio_area}",
            f"processes_mentioned: {len(processes)}",
            f"organisms_mentioned: {len(organisms)}",
            f"has_mechanism: {self._has_mechanism(text)}",
            f"has_evolutionary_context: {self._has_evolution(text)}",
        ]
        
        return base_meta + "\n".join(bio_meta)
    
    def _detect_biology_area(self, text: str) -> str:
        """Detect which area of biology is discussed."""
        lower = text.lower()
        
        areas = {
            "genetics": ["gene", "dna", "rna", "chromosome", "mutation", "inheritance"],
            "cell_biology": ["cell", "organelle", "mitochondria", "nucleus", "membrane"],
            "molecular": ["protein", "enzyme", "amino acid", "transcription", "translation"],
            "physiology": ["organ", "tissue", "blood", "heart", "brain", "muscle"],
            "ecology": ["ecosystem", "population", "species", "habitat", "biodiversity"],
            "evolution": ["evolution", "natural selection", "adaptation", "phylogeny"],
            "microbiology": ["bacteria", "virus", "fungi", "microbe", "pathogen"],
            "immunology": ["immune", "antibody", "antigen", "lymphocyte", "inflammation"],
        }
        
        for area, keywords in areas.items():
            if any(kw in lower for kw in keywords):
                return area
        
        return "general"
    
    def _detect_processes(self, text: str) -> List[str]:
        """Detect biological processes mentioned."""
        lower = text.lower()
        processes = []
        
        process_keywords = [
            "transcription", "translation", "replication",
            "respiration", "photosynthesis", "metabolism",
            "mitosis", "meiosis", "cell division",
            "signaling", "apoptosis", "differentiation",
        ]
        
        for proc in process_keywords:
            if proc in lower:
                processes.append(proc)
        
        return processes
    
    def _detect_organisms(self, text: str) -> List[str]:
        """Detect organisms mentioned."""
        lower = text.lower()
        organisms = []
        
        organism_keywords = [
            "human", "mouse", "rat", "bacteria", "yeast",
            "plant", "animal", "mammal", "insect", "fish",
            "virus", "fungi", "cell line", "e. coli",
        ]
        
        for org in organism_keywords:
            if org in lower:
                organisms.append(org)
        
        return organisms
    
    def _has_mechanism(self, text: str) -> bool:
        """Check if mechanism is described."""
        lower = text.lower()
        markers = ["step", "then", "next", "followed by", "leads to", "causes"]
        return any(m in lower for m in markers)
    
    def _has_evolution(self, text: str) -> bool:
        """Check if evolutionary context is present."""
        lower = text.lower()
        markers = ["evolution", "evolved", "ancestor", "selection", "adaptation"]
        return any(m in lower for m in markers)
