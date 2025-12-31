"""
ANM PDF Refiner Module

Refines raw domain outputs and content into clean, research-grade PDF content
that matches the Blueprint's vision for Research Mode output.

This module ensures:
- All technical markers and metadata are removed
- Content is structured and professional
- Research-grade quality output
- Alignment with Blueprint specifications
"""

import re
from typing import Dict, Any, List, Optional


class PDFRefiner:
    """
    Refines raw ANM outputs into clean, research-grade PDF content.
    
    Per Blueprint: "The PDF is generated from validated internal outputs,
    not raw chat text."
    """
    
    def __init__(self):
        # Patterns to remove (comprehensive list)
        self._marker_patterns = [
            # System markers
            r'\[CLOUD_DIARY_BRIEF\]',
            r'\[RESEARCH MODE:.*?\]',
            r'\[RESEARCH_MODE:.*?\]',
            r'\[CROSS-DOMAIN_CONTEXTS?\].*?\]',
            r'\[VERIFIER.*?\]',
            r'\[WOT.*?\]',
            r'\[DOMAIN.*?\]',
            r'\[PHYSICS\]:.*?',
            r'\[CHEMISTRY\]:.*?',
            r'\[GENERAL\]:.*?',
            r'\[FACTS\]:.*?',
            
            # Memory markers
            r'ANM CLOUD DIARY.*?Compliant.*?PAST-ONLY',
            r'EPISODIC TRACE.*?interactions\):',
            r'SUMMARY.*?compressed PAST context\):',
            r'Found \d+ relevant memory block\(s\)\.',
            r'PAST HIGHLIGHTS:.*?',
            r'NOTE:.*?truth\.',
            
            # Internet research markers
            r'--- INTERNET RESEARCH CONTEXT ---',
            r'--- END INTERNET RESEARCH ---',
            r'INTERNET RESEARCH CONTEXT',
            r'END INTERNET RESEARCH',
            
            # WoT markers
            r'--- WoT PACKET.*?---',
            r'WoT PACKET.*?VIEW\)',
            r'Final WOT REQUEST:',
            r'WOT REQUEST:.*',
            r'WOT_REQUEST:.*',
            
            # Metadata blocks and internal notes
            r'\[.*?_ANALYSIS\].*?',
            r'\[.*?_METRICS\].*?',
            r'\[.*?_METADATA\].*?',
            r'confidence_score:.*?\d+',
            r'efficiency_score:.*?\d+',
            r'processing_time_ms:.*?\d+',
            r'version:.*?',
            r'physics_area:.*?',
            r'molecules_mentioned:.*?\d+',
            r'has_balanced_equation:.*?',
            r'safety_addressed:.*?',
            r'conservation_mentioned:.*?',
            r'has_dimensional_analysis:.*?',
            r'speculation_risk:.*?',
            r'astrophysics.*?conservation',
            
            # Internal reasoning patterns (aggressive removal)
            r'Then:.*?CONFIDENCE.*?EFFICIENCY',
            r'But wait:.*?',
            r'So I will proceed.*?',
            r'So how will.*?',
            r'It\'s possible that.*?',
            r'Then what should we do',
            r'However, our.*?domain',
            r'But there is no.*?',
            r'We have a search result error.*?',
            r'that\'s not our domain.*?',
            r'Alternatively, note that.*?',
            r'So if there are no.*?',
            r'However, note that.*?',
            r'The redacted blocks.*?',
            r'because of the redacted blocks',
            r'which were redacted',
            
            # Domain-specific internal notes
            r'\[CHEMISTRY\]:\s*chemistry is not the primary focus.*?',
            r'\[PHYSICS\]:\s*\.\.\.',
            r'chemistry is not the primary focus here.*?',
            r'The user\'s query is entirely within.*?',
            r'Therefore, no need to request another domain.*?',
            
            # Instruction patterns
            r'INSTRUCTIONS?:.*?',
            r'Be honest about limitations\.',
            r'If needed, request another domain:',
            r'When done.*?',
            r'Read ALL domain reasoning',
            r'Build on previous insights',
            r'Fix inconsistencies in YOUR domain',
            r'If you need another domain',
            r'None yet.*?first domain\.',
            r'This is the first domain\.',
            
            # Query repetition
            r'The user\'s query is:.*?\"',
            r'They also provided.*?packet.*?includes:',
            r'Query:.*?',
        ]
        
        # Thinking tags and markers
        self._thinking_patterns = [
            r'<think>.*?</think>',
            r'</?think>',
            r'<think>.*?</think>',
            r'</?redacted_reasoning>',
            r'Thinking\.\.\..*?\n',
            r'THINKING\.\.\..*?\n',
        ]
        
        # Answer extraction patterns
        self._answer_patterns = [
            r'<answer>(.*?)</answer>',
            r'ANSWER \(write directly.*?\):',
            r'ANSWER:',
            r'Final Answer:',
            r'THE ANSWER:',
        ]
    
    def refine_domain_output(self, domain: str, raw_output: str) -> str:
        """
        Refine a single domain's output into clean research content.
        
        Args:
            domain: Domain name (e.g., "physics", "chemistry")
            raw_output: Raw domain specialist output
            
        Returns:
            Cleaned, research-grade content
        """
        if not raw_output or not raw_output.strip():
            return ""
        
        text = raw_output
        
        # Step 1: Remove all system markers
        for pattern in self._marker_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)
        
        # Step 2: Remove thinking tags
        for pattern in self._thinking_patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Step 3: Extract answer content if wrapped in tags
        for pattern in self._answer_patterns:
            match = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
            if match:
                if pattern.startswith('<answer>'):
                    text = match.group(1)
                else:
                    # Remove the marker, keep content after it
                    text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Step 4: Clean line by line
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            
            # Skip empty or very short lines
            if not stripped or len(stripped) < 10:
                continue
            
            # Skip instruction-like lines and internal reasoning
            skip_phrases = [
                'instructions:', 'cross-domain', 'research mode:', 'research_mode:',
                'none yet', 'first domain', 'build on', 'read all', 'fix inconsistencies',
                'if you need', 'wot_request', 'verifier_ready', 'answer (write directly',
                'cloud diary', 'episodic trace', 'past highlights', 'summary (compressed',
                'found', 'relevant memory', 'internet research context', 'end internet research',
                'wot packet', 'final wot request', 'confidence_score', 'efficiency_score',
                'processing_time', 'version:', 'physics_area', 'molecules_mentioned',
                'has_balanced_equation', 'safety_addressed', 'chemistry_analysis',
                'efficiency_metrics', 'be honest', 'request another', 'when done',
                # Internal reasoning patterns
                'then: confidence', 'but wait:', 'so i will proceed', 'so how will',
                'it\'s possible that', 'then what should we do', 'however, our',
                'but there is no', 'we have a search result error', 'that\'s not our domain',
                'alternatively, note that', 'so if there are no', 'however, note that',
                'the redacted blocks', 'because of the redacted blocks', 'which were redacted',
                'chemistry is not the primary focus', 'the user\'s query is entirely within',
                'therefore, no need to request', 'conservation_mentioned', 'has_dimensional_analysis',
                'speculation_risk', 'astrophysics conservation',
            ]
            
            if any(phrase in stripped.lower() for phrase in skip_phrases):
                continue
            
            # Skip lines that are just separators or markers
            if re.match(r'^[=\-_\s]+$', stripped):
                continue
            
            cleaned_lines.append(stripped)
        
        text = '\n'.join(cleaned_lines)
        
        # Step 5: Remove duplicate sentences and internal reasoning
        sentences = re.split(r'[.!?]\s+', text)
        seen = set()
        unique_sentences = []
        for sent in sentences:
            sent_clean = sent.strip()
            if not sent_clean or len(sent_clean) < 15:
                continue
            
            # Skip sentences that are clearly internal reasoning
            if any(phrase in sent_clean.lower() for phrase in [
                'then: confidence', 'but wait', 'so i will proceed', 'so how will',
                'it\'s possible that', 'then what should we do', 'however, our',
                'but there is no', 'we have a search result error', 'that\'s not our domain',
                'alternatively, note that', 'so if there are no', 'however, note that',
                'the redacted blocks', 'because of the redacted blocks', 'which were redacted',
                'chemistry is not the primary focus', 'the user\'s query is entirely within',
                'therefore, no need to request', 'conservation_mentioned', 'has_dimensional_analysis',
                'speculation_risk', 'astrophysics conservation',
            ]):
                continue
            
            # Skip metadata sentences
            if re.match(r'^[a-z_]+:\s*(none|true|false|\d+|medium|high|low)', sent_clean.lower()):
                continue
            
            sent_normalized = sent_clean.lower()
            # Check for near-duplicates (fuzzy matching)
            is_duplicate = False
            for seen_sent in seen:
                # If 80% similar, consider duplicate
                similarity = self._sentence_similarity(sent_normalized, seen_sent)
                if similarity > 0.8:
                    is_duplicate = True
                    break
            if not is_duplicate:
                seen.add(sent_normalized)
                unique_sentences.append(sent_clean)
        
        result = '. '.join(unique_sentences)
        
        # Step 6: Extract meaningful paragraphs
        paragraphs = result.split('\n\n')
        meaningful_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if len(para) > 50:
                # Remove any remaining markers
                para = re.sub(r'^.*?\[.*?\].*?$', '', para, flags=re.MULTILINE)
                para = para.strip()
                if para and len(para) > 50:
                    meaningful_paragraphs.append(para)
        
        if meaningful_paragraphs:
            result = '\n\n'.join(meaningful_paragraphs)
        else:
            result = result.strip()
        
        # Step 7: Final cleanup - remove any remaining artifacts
        result = re.sub(r'\s+', ' ', result)  # Normalize whitespace
        result = re.sub(r'\n\s*\n\s*\n+', '\n\n', result)  # Remove excessive newlines
        result = result.strip()
        
        return result
    
    def refine_all_domains(self, domain_cots: Dict[str, str]) -> Dict[str, str]:
        """
        Refine all domain outputs.
        
        Args:
            domain_cots: Dictionary mapping domain names to raw outputs
            
        Returns:
            Dictionary mapping domain names to refined outputs
        """
        refined = {}
        for domain, raw_output in domain_cots.items():
            refined[domain] = self.refine_domain_output(domain, raw_output)
        return refined
    
    def refine_summary(self, raw_summary: str) -> str:
        """
        Refine the executive summary / final conclusions.
        
        Args:
            raw_summary: Raw summary text
            
        Returns:
            Cleaned, professional summary
        """
        if not raw_summary or not raw_summary.strip():
            return "No summary available."
        
        text = raw_summary
        
        # Remove markdown headers
        text = re.sub(r'\*\*[A-Z][a-z]+\*\*:\s*', '', text)
        
        # Remove all markers
        for pattern in self._marker_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)
        
        # Remove thinking tags
        for pattern in self._thinking_patterns:
            text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove ANSWER markers
        text = re.sub(r'ANSWER.*?:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[VERIFIER.*?\]', '', text, flags=re.IGNORECASE)
        
        # Remove domain-specific internal notes
        text = re.sub(r'\[CHEMISTRY\]:.*?', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'\[PHYSICS\]:.*?', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'\[GENERAL\]:.*?', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove duplicate sentences and internal reasoning
        sentences = re.split(r'[.!?]\s+', text)
        seen = set()
        unique_sentences = []
        for sent in sentences:
            sent_clean = sent.strip()
            if not sent_clean or len(sent_clean) < 20:
                continue
            
            # Skip internal reasoning sentences
            if any(phrase in sent_clean.lower() for phrase in [
                'chemistry is not the primary focus', 'the user\'s query is entirely within',
                'therefore, no need to request', 'then: confidence', 'but wait',
                'so i will proceed', 'however, our', 'but there is no',
            ]):
                continue
            
            sent_normalized = sent_clean.lower()
            # Check for duplicates (exact and near-duplicates)
            is_duplicate = False
            for seen_sent in seen:
                if sent_normalized == seen_sent:
                    is_duplicate = True
                    break
                # Check similarity
                similarity = self._sentence_similarity(sent_normalized, seen_sent)
                if similarity > 0.85:  # Higher threshold for summary
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen.add(sent_normalized)
                unique_sentences.append(sent_clean)
        
        result = '. '.join(unique_sentences)
        
        # Extract first meaningful paragraph
        paragraphs = result.split('\n\n')
        for para in paragraphs:
            para = para.strip()
            if len(para) > 50:
                return para
        
        # Fallback: return first 800 chars at sentence boundary
        if len(result) > 800:
            cut_point = result[:800].rfind('.')
            if cut_point > 200:
                result = result[:cut_point + 1]
            else:
                result = result[:800] + "..."
        
        return result.strip()
    
    def _sentence_similarity(self, sent1: str, sent2: str) -> float:
        """
        Calculate similarity between two sentences (simple word overlap).
        
        Returns:
            Similarity score between 0.0 and 1.0
        """
        words1 = set(sent1.split())
        words2 = set(sent2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)

