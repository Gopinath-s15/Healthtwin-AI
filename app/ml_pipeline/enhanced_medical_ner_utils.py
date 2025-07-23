"""
Utility functions for Enhanced Medical NER
Contains fuzzy matching, regex extraction, and normalization functions
"""

import re
import logging
from typing import Dict, List, Tuple, Any, Optional

logger = logging.getLogger(__name__)

try:
    import rapidfuzz
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

def extract_with_regex(text: str, patterns: Dict[str, List[str]]) -> Dict[str, Any]:
    """Extract medical entities using regex patterns"""
    entities = {
        'medications': [],
        'dosages': [],
        'frequencies': [],
        'durations': [],
        'instructions': []
    }
    
    try:
        text_lower = text.lower()
        
        # Extract dosages
        for pattern in patterns.get('dosage_patterns', []):
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                entities['dosages'].append({
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.8,
                    'method': 'regex',
                    'pattern': pattern
                })
        
        # Extract frequencies
        for pattern in patterns.get('frequency_patterns', []):
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                entities['frequencies'].append({
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.8,
                    'method': 'regex',
                    'pattern': pattern
                })
        
        # Extract durations
        for pattern in patterns.get('duration_patterns', []):
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                entities['durations'].append({
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.8,
                    'method': 'regex',
                    'pattern': pattern
                })
        
        # Extract instructions
        for pattern in patterns.get('instruction_patterns', []):
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                entities['instructions'].append({
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.7,
                    'method': 'regex',
                    'pattern': pattern
                })
    
    except Exception as e:
        logger.warning(f"Regex extraction failed: {e}")
    
    return entities

def extract_with_fuzzy_matching(text: str, drug_database: Dict[str, Dict[str, Any]], threshold: float = 0.8) -> Dict[str, Any]:
    """Extract drug names using fuzzy string matching"""
    entities = {
        'medications': [],
        'dosages': [],
        'frequencies': [],
        'durations': [],
        'instructions': []
    }
    
    try:
        if not RAPIDFUZZ_AVAILABLE:
            return _extract_with_basic_fuzzy(text, drug_database, threshold)
        
        # Create list of all drug names and variations
        drug_names = []
        drug_mapping = {}
        
        for drug, info in drug_database.items():
            # Add main drug name
            main_name = drug.replace('_', ' ')
            drug_names.append(main_name)
            drug_mapping[main_name] = (drug, info, 'main_name')
            
            # Add variations
            for variation in info['variations']:
                drug_names.append(variation)
                drug_mapping[variation] = (drug, info, 'variation')
        
        # Split text into words and phrases
        words = text.split()
        
        # Check individual words
        for word in words:
            if len(word) < 3:  # Skip very short words
                continue
            
            # Find best matches
            matches = process.extract(word, drug_names, scorer=fuzz.ratio, limit=3)
            
            for match_text, score, _ in matches:
                if score >= threshold * 100:  # rapidfuzz returns 0-100 scale
                    drug_key, drug_info, match_type = drug_mapping[match_text]
                    
                    entities['medications'].append({
                        'text': word,
                        'matched_drug': match_text,
                        'generic_name': drug_info['generic_name'],
                        'category': drug_info['category'],
                        'confidence': score / 100.0,
                        'method': 'rapidfuzz',
                        'match_type': match_type
                    })
        
        # Check 2-word and 3-word phrases
        for i in range(len(words) - 1):
            phrase2 = ' '.join(words[i:i+2])
            phrase3 = ' '.join(words[i:i+3]) if i < len(words) - 2 else None
            
            for phrase in [phrase2, phrase3]:
                if phrase and len(phrase) > 5:
                    matches = process.extract(phrase, drug_names, scorer=fuzz.partial_ratio, limit=2)
                    
                    for match_text, score, _ in matches:
                        if score >= threshold * 100:
                            drug_key, drug_info, match_type = drug_mapping[match_text]
                            
                            entities['medications'].append({
                                'text': phrase,
                                'matched_drug': match_text,
                                'generic_name': drug_info['generic_name'],
                                'category': drug_info['category'],
                                'confidence': score / 100.0,
                                'method': 'rapidfuzz_phrase',
                                'match_type': match_type
                            })
    
    except Exception as e:
        logger.warning(f"Fuzzy matching failed: {e}")
    
    return entities

def _extract_with_basic_fuzzy(text: str, drug_database: Dict[str, Dict[str, Any]], threshold: float = 0.8) -> Dict[str, Any]:
    """Basic fuzzy matching using difflib when rapidfuzz is not available"""
    from difflib import SequenceMatcher
    
    entities = {
        'medications': [],
        'dosages': [],
        'frequencies': [],
        'durations': [],
        'instructions': []
    }
    
    try:
        text_lower = text.lower()
        words = text_lower.split()
        
        for drug, info in drug_database.items():
            all_names = [drug.replace('_', ' ')] + info['variations']
            
            for name in all_names:
                name_lower = name.lower()
                
                # Check if drug name appears in text
                if name_lower in text_lower:
                    entities['medications'].append({
                        'text': name,
                        'generic_name': info['generic_name'],
                        'category': info['category'],
                        'confidence': 0.9,
                        'method': 'basic_fuzzy_exact'
                    })
                    continue
                
                # Check fuzzy matching for individual words
                for word in words:
                    if len(word) < 3:
                        continue
                    
                    similarity = SequenceMatcher(None, word, name_lower).ratio()
                    if similarity >= threshold:
                        entities['medications'].append({
                            'text': word,
                            'matched_drug': name,
                            'generic_name': info['generic_name'],
                            'category': info['category'],
                            'confidence': similarity,
                            'method': 'basic_fuzzy'
                        })
    
    except Exception as e:
        logger.warning(f"Basic fuzzy matching failed: {e}")
    
    return entities

def merge_entities(base_entities: Dict[str, Any], new_entities: Dict[str, Any]) -> Dict[str, Any]:
    """Merge entities from different extraction methods"""
    try:
        for entity_type in ['medications', 'dosages', 'frequencies', 'durations', 'instructions']:
            if entity_type in new_entities:
                base_entities[entity_type].extend(new_entities[entity_type])
        
        return base_entities
    
    except Exception as e:
        logger.warning(f"Entity merging failed: {e}")
        return base_entities

def normalize_entities(entities: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize and deduplicate extracted entities"""
    try:
        for entity_type in ['medications', 'dosages', 'frequencies', 'durations', 'instructions']:
            if entity_type in entities:
                # Remove duplicates based on text similarity
                entities[entity_type] = _deduplicate_entities(entities[entity_type])
                
                # Sort by confidence
                entities[entity_type].sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        # Calculate overall confidence scores
        entities['confidence_scores'] = _calculate_confidence_scores(entities)
        
        return entities
    
    except Exception as e:
        logger.warning(f"Entity normalization failed: {e}")
        return entities

def _deduplicate_entities(entity_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate entities based on text similarity"""
    if not entity_list:
        return entity_list
    
    deduplicated = []
    
    for entity in entity_list:
        is_duplicate = False
        entity_text = entity.get('text', '').lower().strip()
        
        for existing in deduplicated:
            existing_text = existing.get('text', '').lower().strip()
            
            # Check for exact match or high similarity
            if entity_text == existing_text:
                is_duplicate = True
                # Keep the one with higher confidence
                if entity.get('confidence', 0) > existing.get('confidence', 0):
                    deduplicated.remove(existing)
                    deduplicated.append(entity)
                break
            elif RAPIDFUZZ_AVAILABLE:
                similarity = fuzz.ratio(entity_text, existing_text) / 100.0
                if similarity > 0.9:
                    is_duplicate = True
                    if entity.get('confidence', 0) > existing.get('confidence', 0):
                        deduplicated.remove(existing)
                        deduplicated.append(entity)
                    break
        
        if not is_duplicate:
            deduplicated.append(entity)
    
    return deduplicated

def _calculate_confidence_scores(entities: Dict[str, Any]) -> Dict[str, float]:
    """Calculate overall confidence scores for each entity type"""
    confidence_scores = {}
    
    for entity_type in ['medications', 'dosages', 'frequencies', 'durations', 'instructions']:
        entity_list = entities.get(entity_type, [])
        if entity_list:
            confidences = [e.get('confidence', 0) for e in entity_list]
            confidence_scores[entity_type] = sum(confidences) / len(confidences)
        else:
            confidence_scores[entity_type] = 0.0
    
    return confidence_scores
