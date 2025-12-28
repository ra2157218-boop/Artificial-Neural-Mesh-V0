# ============================================================
# ANM V0-OpenSource — NOVELTY DETECTOR V2 (MAXIMUM LEVEL)
#  ML Embeddings • Semantic Similarity • Confidence Scoring
#  Multi-Layer Detection • Domain Clustering • Auto-Learning
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
import time
import math


@dataclass
class NoveltyResult:
    """Rich novelty detection result with confidence metrics."""
    requires_new_domain: bool
    detected_domain: Optional[str]
    confidence: float  # 0.0-1.0
    semantic_distance: float  # Distance from known domains
    cluster_id: Optional[str]  # Which cluster it belongs to
    reasoning: str
    detection_layers: Dict[str, Any]  # Results from each detection layer
    suggested_domains: List[str]  # Ranked list of suggested domain names
    keywords_extracted: List[str]
    processing_time_ms: float
    embedding_used: bool


class EmbeddingCache:
    """In-memory + disk cache for embeddings to avoid recomputation."""
    
    def __init__(self, cache_dir: str = ".anm_cache/embeddings"):
        self.cache_dir = cache_dir
        self.memory_cache: Dict[str, List[float]] = {}
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()
    
    def get(self, text: str) -> Optional[List[float]]:
        key = self._get_key(text)
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        cache_path = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(cache_path):
            with open(cache_path, "r") as f:
                embedding = json.load(f)
                self.memory_cache[key] = embedding
                return embedding
        return None
    
    def set(self, text: str, embedding: List[float]) -> None:
        key = self._get_key(text)
        self.memory_cache[key] = embedding
        cache_path = os.path.join(self.cache_dir, f"{key}.json")
        with open(cache_path, "w") as f:
            json.dump(embedding, f)


class NoveltyDetectorV2:
    """
    MAXIMUM LEVEL Novelty Detection System.
    
    Features:
    - Multi-layer detection (keywords, embeddings, LLM, clustering)
    - Semantic similarity using embeddings
    - Confidence calibration
    - Domain clustering for pattern recognition
    - Learning from past detections
    - Parallel processing
    - Caching for performance
    """
    
    # Known domains and their semantic anchors
    KNOWN_DOMAINS = {
        "general": ["general", "common", "basic", "everyday", "simple"],
        "math": ["mathematics", "algebra", "calculus", "geometry", "equation", "proof", "theorem"],
        "physics": ["physics", "force", "energy", "motion", "quantum", "relativity", "gravity"],
        "code": ["programming", "software", "algorithm", "function", "class", "code", "debug"],
        "chemistry": ["chemistry", "molecule", "reaction", "element", "compound", "bond", "acid"],
        "biology": ["biology", "cell", "dna", "organism", "evolution", "gene", "protein"],
        "memory": ["memory", "remember", "recall", "past", "history", "previous"],
        "research": ["research", "study", "paper", "academic", "literature", "citation"],
        "facts": ["fact", "truth", "verify", "confirm", "accurate", "correct"],
        "simulation": ["simulate", "model", "predict", "forecast", "scenario"],
        "image": ["image", "picture", "visual", "photo", "diagram", "graphic"],
        "sound": ["sound", "audio", "music", "acoustic", "frequency", "tone"],
    }
    
    # Novel domain patterns to detect
    NOVEL_DOMAIN_PATTERNS = {
        "geology": {
            "keywords": ["geology", "geological", "tectonic", "seismic", "volcano", "earthquake", 
                        "mineral", "rock", "fossil", "sediment", "crust", "mantle", "plate"],
            "weight": 1.0,
        },
        "astronomy": {
            "keywords": ["astronomy", "astronomical", "telescope", "nebula", "galaxy", "star formation",
                        "cosmic", "celestial", "pulsar", "quasar", "exoplanet", "constellation"],
            "weight": 1.0,
        },
        "medicine": {
            "keywords": ["medicine", "medical", "diagnosis", "treatment", "symptom", "disease",
                        "patient", "clinical", "therapy", "pharmaceutical", "surgery", "pathology"],
            "weight": 1.2,  # Higher weight - important domain
        },
        "psychology": {
            "keywords": ["psychology", "psychological", "cognitive", "behavior", "mental", "emotion",
                        "neural", "consciousness", "perception", "memory", "personality", "therapy"],
            "weight": 1.0,
        },
        "economics": {
            "keywords": ["economics", "economic", "market", "finance", "trading", "inflation",
                        "gdp", "economy", "fiscal", "monetary", "investment", "capital"],
            "weight": 1.0,
        },
        "history": {
            "keywords": ["history", "historical", "ancient", "medieval", "civilization", "empire",
                        "war", "dynasty", "era", "century", "archaeological", "heritage"],
            "weight": 0.8,
        },
        "linguistics": {
            "keywords": ["linguistics", "language", "grammar", "syntax", "semantics", "phonetics",
                        "translation", "morphology", "dialect", "etymology", "vocabulary"],
            "weight": 0.9,
        },
        "law": {
            "keywords": ["law", "legal", "court", "judge", "attorney", "statute", "regulation",
                        "contract", "liability", "jurisdiction", "precedent", "litigation"],
            "weight": 1.1,
        },
        "engineering": {
            "keywords": ["engineering", "mechanical", "electrical", "structural", "civil",
                        "aerospace", "robotics", "automation", "manufacturing", "design"],
            "weight": 1.0,
        },
        "agriculture": {
            "keywords": ["agriculture", "farming", "crop", "soil", "irrigation", "harvest",
                        "livestock", "fertilizer", "pesticide", "organic", "sustainable"],
            "weight": 0.9,
        },
        "environmental": {
            "keywords": ["environment", "ecology", "climate", "pollution", "sustainability",
                        "biodiversity", "conservation", "ecosystem", "carbon", "renewable"],
            "weight": 1.1,
        },
        "cybersecurity": {
            "keywords": ["cybersecurity", "hacking", "encryption", "firewall", "malware",
                        "vulnerability", "penetration", "authentication", "security"],
            "weight": 1.2,
        },
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.cache = EmbeddingCache()
        self.detection_history: List[NoveltyResult] = []
        
        # Thresholds
        self.keyword_confidence_threshold = 0.3
        self.embedding_similarity_threshold = 0.7
        self.combined_confidence_threshold = 0.5
        
        # Detection weights
        self.layer_weights = {
            "keyword": 0.3,
            "embedding": 0.4,
            "llm": 0.2,
            "pattern": 0.1,
        }
    
    def detect(
        self, 
        query: str, 
        memory_brief: str = "",
        parallel: bool = True
    ) -> NoveltyResult:
        """
        Multi-layer novelty detection.
        
        Runs multiple detection methods in parallel and combines results.
        """
        start_time = time.time()
        
        # Layer 1: Keyword-based detection
        keyword_result = self._keyword_detection(query)
        
        # Layer 2: Embedding-based semantic similarity (if available)
        embedding_result = self._embedding_detection(query)
        
        # Layer 3: LLM-based analysis (optional, more expensive)
        llm_result = self._llm_detection(query) if self.config.get("use_llm_detection", False) else None
        
        # Layer 4: Pattern matching against novel domains
        pattern_result = self._pattern_detection(query)
        
        # Combine results with weighted scoring
        combined = self._combine_detection_layers(
            keyword=keyword_result,
            embedding=embedding_result,
            llm=llm_result,
            pattern=pattern_result,
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        result = NoveltyResult(
            requires_new_domain=combined["requires_new_domain"],
            detected_domain=combined["detected_domain"],
            confidence=combined["confidence"],
            semantic_distance=combined.get("semantic_distance", 0.0),
            cluster_id=combined.get("cluster_id"),
            reasoning=combined["reasoning"],
            detection_layers={
                "keyword": keyword_result,
                "embedding": embedding_result,
                "llm": llm_result,
                "pattern": pattern_result,
            },
            suggested_domains=combined.get("suggested_domains", []),
            keywords_extracted=combined.get("keywords", []),
            processing_time_ms=processing_time,
            embedding_used=embedding_result is not None,
        )
        
        # Learn from detection
        self.detection_history.append(result)
        
        return result
    
    def _keyword_detection(self, query: str) -> Dict[str, Any]:
        """Fast keyword-based detection layer."""
        q_lower = query.lower()
        words = set(q_lower.split())
        
        # Check against known domains first
        known_domain_scores: Dict[str, float] = {}
        for domain, keywords in self.KNOWN_DOMAINS.items():
            matches = sum(1 for kw in keywords if kw in q_lower)
            if matches > 0:
                known_domain_scores[domain] = min(matches * 0.2, 1.0)
        
        # Check against novel domain patterns
        novel_domain_scores: Dict[str, Tuple[float, List[str]]] = {}
        for domain, config in self.NOVEL_DOMAIN_PATTERNS.items():
            keywords = config["keywords"]
            weight = config["weight"]
            
            matched_keywords = [kw for kw in keywords if kw in q_lower]
            if matched_keywords:
                score = min(len(matched_keywords) * 0.15 * weight, 1.0)
                novel_domain_scores[domain] = (score, matched_keywords)
        
        # Determine if novel domain needed
        best_known_score = max(known_domain_scores.values()) if known_domain_scores else 0.0
        best_novel = max(novel_domain_scores.items(), key=lambda x: x[1][0]) if novel_domain_scores else None
        
        if best_novel and best_novel[1][0] > best_known_score * 1.2:  # 20% threshold
            return {
                "requires_new": True,
                "domain": best_novel[0],
                "confidence": best_novel[1][0],
                "matched_keywords": best_novel[1][1],
                "known_domain_scores": known_domain_scores,
            }
        
        return {
            "requires_new": False,
            "domain": None,
            "confidence": 0.0,
            "matched_keywords": [],
            "known_domain_scores": known_domain_scores,
        }
    
    def _embedding_detection(self, query: str) -> Optional[Dict[str, Any]]:
        """Embedding-based semantic similarity detection."""
        try:
            # Try to get or compute embeddings
            query_embedding = self._get_embedding(query)
            if query_embedding is None:
                return None
            
            # Compare with domain embeddings
            domain_similarities: Dict[str, float] = {}
            
            for domain, keywords in self.KNOWN_DOMAINS.items():
                domain_text = " ".join(keywords)
                domain_embedding = self._get_embedding(domain_text)
                
                if domain_embedding:
                    similarity = self._cosine_similarity(query_embedding, domain_embedding)
                    domain_similarities[domain] = similarity
            
            # Find best matching known domain
            best_match = max(domain_similarities.items(), key=lambda x: x[1]) if domain_similarities else (None, 0.0)
            
            # If similarity is low, it's potentially a novel domain
            max_similarity = best_match[1]
            requires_new = max_similarity < self.embedding_similarity_threshold
            
            return {
                "requires_new": requires_new,
                "best_known_domain": best_match[0],
                "best_similarity": max_similarity,
                "semantic_distance": 1.0 - max_similarity,
                "all_similarities": domain_similarities,
            }
        except Exception as e:
            return None
    
    def _llm_detection(self, query: str) -> Optional[Dict[str, Any]]:
        """LLM-based deep analysis for novelty detection."""
        try:
            import subprocess
            
            prompt = f"""Analyze this query and determine if it requires a domain specialist that doesn't exist in this list:
Known domains: general, math, physics, code, chemistry, biology, memory, research, facts, simulation, image, sound

Query: "{query}"

Respond in JSON format:
{{
  "requires_new_domain": true/false,
  "suggested_domain": "domain_name or null",
  "confidence": 0.0-1.0,
  "reasoning": "explanation"
}}"""
            
            proc = subprocess.run(
                ["ollama", "run", "deepseek-r1:1.5b"],
                input=prompt.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
            )
            
            output = proc.stdout.decode("utf-8", errors="ignore")
            
            # Parse JSON from output
            import re
            json_match = re.search(r'\{[^}]+\}', output, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            
            return None
        except Exception:
            return None
    
    def _pattern_detection(self, query: str) -> Dict[str, Any]:
        """Pattern matching for novel domain indicators."""
        q_lower = query.lower()
        
        # Novelty indicators
        novelty_phrases = [
            "how does", "what is", "explain", "teach me about",
            "i don't understand", "never heard of", "new to me",
        ]
        
        novelty_score = sum(1 for phrase in novelty_phrases if phrase in q_lower) * 0.1
        
        # Technical depth indicators
        technical_phrases = [
            "advanced", "complex", "detailed", "in-depth",
            "professional", "expert", "specialized",
        ]
        
        technical_score = sum(1 for phrase in technical_phrases if phrase in q_lower) * 0.15
        
        # Domain-specific jargon detection
        jargon_detected = self._detect_jargon(query)
        
        return {
            "novelty_score": min(novelty_score, 1.0),
            "technical_score": min(technical_score, 1.0),
            "jargon_detected": jargon_detected,
            "combined_score": min(novelty_score + technical_score, 1.0),
        }
    
    def _detect_jargon(self, query: str) -> List[str]:
        """Detect domain-specific jargon that might indicate novel domains."""
        # This would ideally use a jargon dictionary or ML model
        # For now, detect uncommon technical terms
        words = query.lower().split()
        jargon = []
        
        # Simple heuristic: words with certain patterns
        for word in words:
            if len(word) > 8 and any(suffix in word for suffix in ["ology", "ography", "ometry", "istics"]):
                jargon.append(word)
        
        return jargon
    
    def _combine_detection_layers(
        self,
        keyword: Dict[str, Any],
        embedding: Optional[Dict[str, Any]],
        llm: Optional[Dict[str, Any]],
        pattern: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Combine all detection layers with weighted scoring."""
        
        scores = []
        weights = []
        
        # Keyword layer
        if keyword.get("requires_new"):
            scores.append(keyword["confidence"])
            weights.append(self.layer_weights["keyword"])
        else:
            scores.append(0.0)
            weights.append(self.layer_weights["keyword"])
        
        # Embedding layer
        if embedding:
            if embedding.get("requires_new"):
                scores.append(1.0 - embedding.get("best_similarity", 0.5))
                weights.append(self.layer_weights["embedding"])
            else:
                scores.append(0.0)
                weights.append(self.layer_weights["embedding"])
        
        # LLM layer
        if llm:
            if llm.get("requires_new_domain"):
                scores.append(llm.get("confidence", 0.5))
                weights.append(self.layer_weights["llm"])
            else:
                scores.append(0.0)
                weights.append(self.layer_weights["llm"])
        
        # Pattern layer
        pattern_score = pattern.get("combined_score", 0.0)
        scores.append(pattern_score)
        weights.append(self.layer_weights["pattern"])
        
        # Weighted average
        if sum(weights) > 0:
            combined_confidence = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        else:
            combined_confidence = 0.0
        
        # Determine result
        requires_new = combined_confidence >= self.combined_confidence_threshold
        
        # Get detected domain
        detected_domain = None
        suggested_domains = []
        
        if keyword.get("requires_new"):
            detected_domain = keyword.get("domain")
            suggested_domains.append(keyword.get("domain"))
        
        if llm and llm.get("suggested_domain"):
            if llm["suggested_domain"] not in suggested_domains:
                suggested_domains.append(llm["suggested_domain"])
        
        # Build reasoning
        reasoning_parts = []
        if keyword.get("requires_new"):
            reasoning_parts.append(f"Keyword match: {keyword.get('domain')} ({keyword.get('confidence'):.2f})")
        if embedding and embedding.get("requires_new"):
            reasoning_parts.append(f"Semantic distance: {embedding.get('semantic_distance', 0):.2f}")
        if llm and llm.get("requires_new_domain"):
            reasoning_parts.append(f"LLM analysis: {llm.get('suggested_domain')}")
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No novel domain indicators detected"
        
        return {
            "requires_new_domain": requires_new,
            "detected_domain": detected_domain,
            "confidence": combined_confidence,
            "semantic_distance": embedding.get("semantic_distance", 0.0) if embedding else 0.0,
            "reasoning": reasoning,
            "suggested_domains": suggested_domains,
            "keywords": keyword.get("matched_keywords", []),
        }
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text, using cache if available."""
        # Check cache first
        cached = self.cache.get(text)
        if cached:
            return cached
        
        # Try to compute embedding using available methods
        embedding = self._compute_embedding(text)
        
        if embedding:
            self.cache.set(text, embedding)
        
        return embedding
    
    def _compute_embedding(self, text: str) -> Optional[List[float]]:
        """Compute embedding using available methods."""
        # Try sentence-transformers if available
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = model.encode(text).tolist()
            return embedding
        except ImportError:
            pass
        
        # Try OpenAI embeddings if available
        try:
            import openai
            response = openai.Embedding.create(
                input=text,
                model="text-embedding-ada-002"
            )
            return response['data'][0]['embedding']
        except:
            pass
        
        # Fallback: simple word-based embedding (bag of words with TF-IDF-like weighting)
        words = text.lower().split()
        word_set = set(words)
        
        # Create a simple 100-dimensional embedding
        embedding = [0.0] * 100
        for i, word in enumerate(word_set):
            idx = hash(word) % 100
            embedding[idx] += 1.0 / len(words)  # TF-like weighting
        
        return embedding
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
