# ============================================================
# ANM V0-OpenSource — NOVELTY DETECTION HANDLER
#  Extracted from Router for better modularity
# ============================================================

from __future__ import annotations
from typing import Dict, Any
import logging


class NoveltyHandler:
    """
    Handles novelty detection for Router.
    
    Detects if a query requires a new domain that doesn't exist yet.
    Uses V2 NoveltyDetectorV2 with fallback to keyword-based detection.
    """
    
    # Known domain keywords mapping for fallback detection
    DOMAIN_KEYWORDS = {
        "geology": ["geology", "geological", "tectonic", "seismic", "volcano", "earthquake", "mineral", "rock formation"],
        "astronomy": ["astronomy", "astronomical", "telescope", "nebula", "galaxy", "star formation", "cosmic"],
        "medicine": ["medicine", "medical", "diagnosis", "treatment", "symptom", "disease", "patient", "clinical"],
        "psychology": ["psychology", "psychological", "cognitive", "behavior", "mental", "emotion", "neural"],
        "economics": ["economics", "economic", "market", "finance", "trading", "inflation", "gdp", "economy"],
        "history": ["history", "historical", "ancient", "medieval", "civilization", "empire", "war"],
        "linguistics": ["linguistics", "language", "grammar", "syntax", "semantics", "phonetics", "translation"],
        "art": ["art", "artistic", "painting", "sculpture", "aesthetic", "design", "creative"],
        "philosophy": ["philosophy", "philosophical", "ethics", "metaphysics", "epistemology", "logic"],
    }
    
    def __init__(self, valid_domains: set, config: Dict[str, Any] = None):
        """
        Initialize NoveltyHandler.
        
        Args:
            valid_domains: Set of valid domain names that currently exist
            config: Router configuration dict
        """
        self.valid_domains = valid_domains
        self.config = config or {}
        self._logger = logging.getLogger(__name__)
    
    def detect(self, user_query: str, memory_brief: str) -> Dict[str, Any]:
        """
        Detect if query requires a new domain.
        
        Uses V2 NoveltyDetectorV2 for ML-based detection with embeddings
        and multi-layer analysis. Falls back to keyword matching if unavailable.
        
        Args:
            user_query: The user's query
            memory_brief: Memory context brief
            
        Returns:
            Dict with:
              - requires_new_domain: bool
              - detected_domain: str (the domain name that's missing)
              - confidence: float (0.0-1.0)
              - reasoning: str
              - detection_method: str
              - semantic_distance: float (if V2 available)
              - suggested_domains: List[str] (if V2 available)
        """
        # Try to use V2 Novelty Detector (enhanced with embeddings)
        try:
            from anm.expansion.core.novelty_detector import NoveltyDetectorV2
            
            detector = NoveltyDetectorV2()
            result = detector.detect(user_query, memory_brief)
            
            return {
                "requires_new_domain": result.requires_new_domain,
                "detected_domain": result.detected_domain,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "detection_method": "v2_enhanced",
                "semantic_distance": getattr(result, "semantic_distance", None),
                "suggested_domains": getattr(result, "suggested_domains", []),
            }
        except (ImportError, AttributeError, TypeError, ValueError) as e:
            # Fall back to V1 keyword matching if V2 detector fails
            if self.config.get("verbose", False):
                self._logger.debug(f"NoveltyDetectorV2 unavailable, using fallback: {e}")
        
        # V1 Fallback: Keyword-based detection
        return self._detect_keywords(user_query)
    
    def _detect_keywords(self, user_query: str) -> Dict[str, Any]:
        """
        Fallback keyword-based novelty detection.
        
        Args:
            user_query: The user's query
            
        Returns:
            Dict with detection results
        """
        q_lower = user_query.lower()
        
        # Check if query mentions a domain not in VALID_DOMAINS
        detected_domain = None
        confidence = 0.0
        reasoning = ""
        
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if domain not in self.valid_domains:
                matches = sum(1 for kw in keywords if kw in q_lower)
                if matches > 0:
                    confidence = min(0.3 + (matches * 0.15), 1.0)
                    detected_domain = domain
                    reasoning = f"Query contains {matches} keyword(s) related to '{domain}' domain"
                    break
        
        requires_new_domain = detected_domain is not None and confidence >= 0.4
        
        return {
            "requires_new_domain": requires_new_domain,
            "detected_domain": detected_domain,
            "confidence": confidence,
            "reasoning": reasoning or "No novel domain detected",
            "detection_method": "v1_keywords",
        }

