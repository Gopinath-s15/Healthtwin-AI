#!/usr/bin/env python3
"""
Specialized parser for handwritten medications in Indian prescriptions
Handles common OCR errors and medication name variations
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

class HandwrittenMedicationParser:
    """Specialized parser for handwritten medication names"""
    
    def __init__(self):
        """Initialize the medication parser"""
        
        # Common Indian medication names with variations and OCR errors
        self.medication_database = {
            # Topical medications
            'mupirocin': {
                'variations': ['mupiro', 'mupir', 'mupi', 'milly', 'mily', 'milli'],
                'forms': ['gel', 'cream', 'ointment'],
                'category': 'topical_antibiotic',
                'common_strengths': ['2%']
            },
            'betamethasone': {
                'variations': ['beta', 'betam', 'betan', 'dextt', 'dext', 'dexa'],
                'forms': ['gel', 'cream', 'lotion'],
                'category': 'topical_steroid',
                'common_strengths': ['0.1%', '0.05%']
            },
            'clotrimazole': {
                'variations': ['clotri', 'clot', 'clotr', 'candid'],
                'forms': ['gel', 'cream', 'powder'],
                'category': 'antifungal',
                'common_strengths': ['1%']
            },
            'fusidic': {
                'variations': ['fusid', 'fusi', 'fuci', 'fucid'],
                'forms': ['gel', 'cream'],
                'category': 'topical_antibiotic',
                'common_strengths': ['2%']
            },
            'hydrocortisone': {
                'variations': ['hydro', 'cortis', 'cort', 'hc'],
                'forms': ['gel', 'cream', 'lotion'],
                'category': 'topical_steroid',
                'common_strengths': ['1%', '2.5%']
            },
            
            # Oral medications
            'azithromycin': {
                'variations': ['azithro', 'azee', 'azith', 'zithro'],
                'forms': ['tablet', 'capsule', 'suspension'],
                'category': 'antibiotic',
                'common_strengths': ['250mg', '500mg']
            },
            'doxycycline': {
                'variations': ['doxy', 'doxcy', 'vibra'],
                'forms': ['tablet', 'capsule'],
                'category': 'antibiotic',
                'common_strengths': ['100mg', '200mg']
            },
            'cetirizine': {
                'variations': ['cetiri', 'cetri', 'zyrtec', 'alerid'],
                'forms': ['tablet', 'syrup'],
                'category': 'antihistamine',
                'common_strengths': ['10mg', '5mg']
            },
            'prednisolone': {
                'variations': ['pred', 'predni', 'wyso'],
                'forms': ['tablet'],
                'category': 'steroid',
                'common_strengths': ['5mg', '10mg', '20mg']
            }
        }
        
        # Common OCR error patterns
        self.ocr_corrections = {
            # Common character substitutions
            '0': 'o', '1': 'l', '5': 's', '6': 'g', '8': 'b',
            'rn': 'm', 'cl': 'd', 'li': 'h', 'vv': 'w'
        }
        
        # Medication form indicators
        self.form_indicators = {
            'gel': ['gel', 'jel', 'gal', 'gei'],
            'cream': ['cream', 'crm', 'crem', 'crearn'],
            'tablet': ['tab', 'tablet', 'tabs', 'tbl'],
            'capsule': ['cap', 'caps', 'capsule'],
            'ointment': ['oint', 'ointment', 'ont'],
            'lotion': ['lotion', 'lot', 'ltn'],
            'drops': ['drops', 'drp', 'drop']
        }
        
        # Dosage patterns
        self.dosage_patterns = [
            r'\d+\s*mg',
            r'\d+\s*ml',
            r'\d+\s*%',
            r'\d+\s*gm',
            r'\d+\s*g'
        ]
        
        # Frequency patterns
        self.frequency_patterns = {
            'bd': 'twice daily',
            'tds': 'three times daily',
            'qds': 'four times daily',
            'od': 'once daily',
            'sos': 'as needed',
            'x': 'times',
            'rf': 'as required'
        }
    
    def parse_handwritten_medications(self, text: str) -> List[Dict]:
        """Parse handwritten medications from OCR text"""
        medications = []
        
        try:
            # Clean and preprocess text
            cleaned_text = self._preprocess_text(text)
            
            # Split into lines and analyze each
            lines = cleaned_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if len(line) < 3:
                    continue
                
                # Look for medication patterns in the line
                found_medications = self._extract_medications_from_line(line)
                medications.extend(found_medications)
            
            # Remove duplicates and improve quality
            medications = self._deduplicate_and_improve(medications)
            
            logger.info(f"Parsed {len(medications)} medications from handwritten text")
            
        except Exception as e:
            logger.error(f"Medication parsing failed: {e}")
        
        return medications
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess OCR text to fix common errors"""
        # Apply OCR corrections
        for error, correction in self.ocr_corrections.items():
            text = text.replace(error, correction)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR artifacts
        text = re.sub(r'[^\w\s\.\-\%\/]', ' ', text)
        
        return text
    
    def _extract_medications_from_line(self, line: str) -> List[Dict]:
        """Extract medications from a single line of text"""
        medications = []
        
        try:
            # Look for medication name patterns
            words = line.split()
            
            for i, word in enumerate(words):
                if len(word) < 3:
                    continue
                
                # Check if this word matches a known medication
                medication_match = self._find_medication_match(word)
                
                if medication_match:
                    # Extract additional information from surrounding context
                    context = ' '.join(words[max(0, i-2):min(len(words), i+4)])
                    
                    medication = self._build_medication_info(
                        medication_match, word, context, line
                    )
                    
                    if medication:
                        medications.append(medication)
                
                # Also check for medication patterns (name + form + dosage)
                elif self._looks_like_medication_pattern(word, words, i):
                    medication = self._parse_medication_pattern(words, i, line)
                    if medication:
                        medications.append(medication)
        
        except Exception as e:
            logger.error(f"Line parsing failed: {e}")
        
        return medications
    
    def _find_medication_match(self, word: str) -> Optional[Tuple[str, Dict]]:
        """Find if a word matches a known medication"""
        word_lower = word.lower()
        
        # Direct match
        if word_lower in self.medication_database:
            return (word_lower, self.medication_database[word_lower])
        
        # Check variations
        for med_name, med_info in self.medication_database.items():
            variations = med_info.get('variations', [])
            
            # Exact variation match
            if word_lower in variations:
                return (med_name, med_info)
            
            # Fuzzy match for variations
            for variation in variations:
                if fuzz.ratio(word_lower, variation) > 80:
                    return (med_name, med_info)
        
        # Fuzzy match for medication names
        best_match = process.extractOne(
            word_lower, 
            list(self.medication_database.keys()),
            score_cutoff=75
        )
        
        if best_match:
            med_name = best_match[0]
            return (med_name, self.medication_database[med_name])
        
        return None
    
    def _looks_like_medication_pattern(self, word: str, words: List[str], index: int) -> bool:
        """Check if this looks like a medication pattern"""
        # Look for patterns like "word + gel", "word + mg", etc.
        if index + 1 < len(words):
            next_word = words[index + 1].lower()
            
            # Check for form indicators
            for form, indicators in self.form_indicators.items():
                if any(indicator in next_word for indicator in indicators):
                    return True
            
            # Check for dosage patterns
            for pattern in self.dosage_patterns:
                if re.search(pattern, next_word, re.IGNORECASE):
                    return True
        
        return False
    
    def _parse_medication_pattern(self, words: List[str], index: int, line: str) -> Optional[Dict]:
        """Parse a medication pattern from words"""
        try:
            medication = {
                'name': words[index].title(),
                'dosage': '',
                'form': '',
                'frequency': '',
                'instructions': '',
                'raw_text': line,
                'confidence': 0.6,
                'category': 'unknown'
            }
            
            # Look for form and dosage in surrounding words
            context_words = words[index:min(len(words), index + 4)]
            context_text = ' '.join(context_words)
            
            # Extract form
            for form, indicators in self.form_indicators.items():
                for indicator in indicators:
                    if indicator in context_text.lower():
                        medication['form'] = form
                        break
            
            # Extract dosage
            for pattern in self.dosage_patterns:
                match = re.search(pattern, context_text, re.IGNORECASE)
                if match:
                    medication['dosage'] = match.group()
                    break
            
            # Extract frequency
            for freq_abbr, freq_full in self.frequency_patterns.items():
                if freq_abbr in context_text.lower():
                    medication['frequency'] = freq_full
                    break
            
            # Only return if we have meaningful information
            if medication['form'] or medication['dosage']:
                return medication
        
        except Exception as e:
            logger.error(f"Pattern parsing failed: {e}")
        
        return None
    
    def _build_medication_info(self, match: Tuple[str, Dict], original_word: str, 
                              context: str, line: str) -> Dict:
        """Build complete medication information"""
        med_name, med_info = match
        
        medication = {
            'name': med_name.title(),
            'original_text': original_word,
            'dosage': '',
            'form': '',
            'frequency': '',
            'instructions': '',
            'raw_text': line,
            'confidence': 0.8,
            'category': med_info.get('category', 'unknown')
        }
        
        # Extract form from context
        possible_forms = med_info.get('forms', [])
        for form in possible_forms:
            if form in context.lower():
                medication['form'] = form
                break
        
        # Extract dosage from context
        common_strengths = med_info.get('common_strengths', [])
        for strength in common_strengths:
            if strength.lower() in context.lower():
                medication['dosage'] = strength
                break
        
        # If no specific dosage found, look for patterns
        if not medication['dosage']:
            for pattern in self.dosage_patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    medication['dosage'] = match.group()
                    break
        
        # Extract frequency
        for freq_abbr, freq_full in self.frequency_patterns.items():
            if freq_abbr in context.lower():
                medication['frequency'] = freq_full
                break
        
        return medication
    
    def _deduplicate_and_improve(self, medications: List[Dict]) -> List[Dict]:
        """Remove duplicates and improve medication information"""
        if not medications:
            return []
        
        # Group by similar names
        grouped = {}
        
        for med in medications:
            name = med['name'].lower()
            
            # Find if this is similar to an existing medication
            found_group = None
            for existing_name in grouped.keys():
                if fuzz.ratio(name, existing_name) > 85:
                    found_group = existing_name
                    break
            
            if found_group:
                # Merge with existing
                existing = grouped[found_group]
                merged = self._merge_medications(existing, med)
                grouped[found_group] = merged
            else:
                grouped[name] = med
        
        return list(grouped.values())
    
    def _merge_medications(self, med1: Dict, med2: Dict) -> Dict:
        """Merge two medication dictionaries"""
        merged = med1.copy()
        
        # Take the more complete information
        for key in ['dosage', 'form', 'frequency', 'instructions']:
            if not merged.get(key) and med2.get(key):
                merged[key] = med2[key]
            elif len(med2.get(key, '')) > len(merged.get(key, '')):
                merged[key] = med2[key]
        
        # Take higher confidence
        merged['confidence'] = max(med1.get('confidence', 0), med2.get('confidence', 0))
        
        # Combine raw text
        if med2.get('raw_text') and med2['raw_text'] not in merged.get('raw_text', ''):
            merged['raw_text'] = f"{merged.get('raw_text', '')} | {med2['raw_text']}"
        
        return merged
