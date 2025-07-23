#!/usr/bin/env python3
"""
Prescription Layout Analyzer for structured handwritten prescriptions
Specifically designed for clinic prescription pads with predefined sections
"""

import cv2
import numpy as np
from PIL import Image
import pytesseract
from typing import Dict, List, Tuple, Optional
import logging
import re

logger = logging.getLogger(__name__)

class PrescriptionLayoutAnalyzer:
    """Analyzes prescription layout and extracts structured information"""
    
    def __init__(self):
        """Initialize the prescription layout analyzer"""
        self.prescription_sections = {
            'header': {'keywords': ['dr.', 'clinic', 'hospital', 'physician'], 'region': 'top'},
            'patient_info': {'keywords': ['name:', 'age:', 'sex:', 'date:'], 'region': 'upper'},
            'prescription_area': {'keywords': ['rx', 'r/', 'medicines'], 'region': 'middle'},
            'footer': {'keywords': ['address', 'phone', 'appointment'], 'region': 'bottom'}
        }
        
        # Common handwritten medication patterns for Indian prescriptions
        self.medication_patterns = [
            # Topical medications
            r'[A-Za-z]+\s*gel\s*[rf]?\s*[/]?\s*[A-Za-z]*',
            r'[A-Za-z]+\s*cream\s*[rf]?\s*[/]?\s*[A-Za-z]*',
            r'[A-Za-z]+\s*ointment\s*[rf]?\s*[/]?\s*[A-Za-z]*',
            
            # Oral medications
            r'[A-Za-z]+\s*\d+\s*mg\s*[rf]?\s*[/]?\s*[A-Za-z]*',
            r'[A-Za-z]+\s*tablet\s*[rf]?\s*[/]?\s*[A-Za-z]*',
            r'[A-Za-z]+\s*cap\s*[rf]?\s*[/]?\s*[A-Za-z]*',
            
            # Frequency patterns
            r'\d+\s*x\s*\d+',  # 2 x 3
            r'\d+\s*week[s]?',  # 3 weeks
            r'\d+\s*day[s]?',   # 7 days
            
            # Common abbreviations
            r'[A-Za-z]+\s*[rf]\s*[/]?\s*[A-Za-z]*',  # r/f patterns
            r'[A-Za-z]+\s*[0-9]+\s*[rf]\s*[/]?\s*[A-Za-z]*',  # medicine + number + r/f
        ]
        
        # Common medical abbreviations in Indian prescriptions
        self.medical_abbreviations = {
            'r/f': 'as required',
            'rf': 'as required', 
            'bd': 'twice daily',
            'tds': 'three times daily',
            'qds': 'four times daily',
            'od': 'once daily',
            'sos': 'as needed',
            'ac': 'before meals',
            'pc': 'after meals',
            'hs': 'at bedtime'
        }
    
    def analyze_prescription_layout(self, image: np.ndarray) -> Dict:
        """
        Analyze the layout of a prescription and extract structured information
        """
        results = {
            'success': False,
            'layout_detected': False,
            'sections': {},
            'medications': [],
            'instructions': [],
            'confidence': 0.0
        }
        
        try:
            # Detect prescription layout
            sections = self._detect_prescription_sections(image)
            
            if sections:
                results['layout_detected'] = True
                results['sections'] = sections
                
                # Extract medications from prescription area
                if 'prescription_area' in sections:
                    medications = self._extract_medications_from_section(
                        image, sections['prescription_area']
                    )
                    results['medications'] = medications
                
                # Extract instructions
                instructions = self._extract_instructions_from_sections(image, sections)
                results['instructions'] = instructions
                
                # Calculate overall confidence
                confidence = self._calculate_layout_confidence(sections, medications, instructions)
                results['confidence'] = confidence
                
                results['success'] = True
                logger.info(f"Layout analysis successful: {len(medications)} medications found")
            
        except Exception as e:
            logger.error(f"Layout analysis failed: {e}")
        
        return results
    
    def _detect_prescription_sections(self, image: np.ndarray) -> Dict:
        """Detect different sections of the prescription"""
        sections = {}
        
        try:
            height, width = image.shape[:2]
            
            # Define approximate regions based on typical prescription layout
            regions = {
                'header': (0, 0, width, height // 4),  # Top 25%
                'patient_info': (0, height // 4, width, height // 2),  # Next 25%
                'prescription_area': (0, height // 2, width, 3 * height // 4),  # Middle 25%
                'footer': (0, 3 * height // 4, width, height)  # Bottom 25%
            }
            
            for section_name, (x, y, x2, y2) in regions.items():
                section_image = image[y:y2, x:x2]
                
                # Extract text from section
                try:
                    text = pytesseract.image_to_string(
                        section_image, 
                        config='--psm 6 --oem 3'
                    ).strip()
                    
                    if text and len(text) > 3:  # Valid text found
                        sections[section_name] = {
                            'region': (x, y, x2, y2),
                            'text': text,
                            'confidence': self._calculate_section_confidence(text, section_name)
                        }
                        
                except Exception as e:
                    logger.warning(f"Failed to extract text from {section_name}: {e}")
                    continue
            
            return sections
            
        except Exception as e:
            logger.error(f"Section detection failed: {e}")
            return {}
    
    def _extract_medications_from_section(self, image: np.ndarray, section_info: Dict) -> List[Dict]:
        """Extract medications from the prescription area"""
        medications = []
        
        try:
            x, y, x2, y2 = section_info['region']
            section_image = image[y:y2, x:x2]
            
            # Apply multiple OCR configurations for better handwriting recognition
            ocr_configs = [
                '--psm 6 --oem 3',
                '--psm 8 --oem 1',
                '--psm 7 --oem 3',
                '--psm 4 --oem 3',
            ]
            
            all_text_results = []
            
            for config in ocr_configs:
                try:
                    # Get detailed OCR data
                    data = pytesseract.image_to_data(
                        section_image,
                        config=config,
                        output_type=pytesseract.Output.DICT
                    )
                    
                    # Extract lines with reasonable confidence
                    lines = self._group_words_into_lines(data)
                    all_text_results.extend(lines)
                    
                except Exception as e:
                    logger.warning(f"OCR config {config} failed: {e}")
                    continue
            
            # Process extracted lines to find medications
            for line_text in all_text_results:
                if len(line_text.strip()) < 3:
                    continue
                
                # Look for medication patterns
                medications.extend(self._parse_medication_line(line_text))
            
            # Remove duplicates and low-confidence results
            medications = self._deduplicate_medications(medications)
            
        except Exception as e:
            logger.error(f"Medication extraction failed: {e}")
        
        return medications
    
    def _group_words_into_lines(self, ocr_data: Dict) -> List[str]:
        """Group OCR words into logical lines"""
        lines = []
        
        try:
            # Group words by approximate Y coordinate
            word_groups = {}
            
            for i, conf in enumerate(ocr_data['conf']):
                if conf > 20:  # Minimum confidence threshold
                    word = ocr_data['text'][i].strip()
                    if len(word) > 0:
                        y = ocr_data['top'][i]
                        
                        # Group words within 10 pixels vertically
                        line_key = y // 10
                        if line_key not in word_groups:
                            word_groups[line_key] = []
                        
                        word_groups[line_key].append({
                            'word': word,
                            'x': ocr_data['left'][i],
                            'conf': conf
                        })
            
            # Convert groups to lines
            for line_key in sorted(word_groups.keys()):
                words = sorted(word_groups[line_key], key=lambda x: x['x'])
                line_text = ' '.join([w['word'] for w in words])
                if len(line_text.strip()) > 2:
                    lines.append(line_text)
            
        except Exception as e:
            logger.error(f"Line grouping failed: {e}")
        
        return lines
    
    def _parse_medication_line(self, line_text: str) -> List[Dict]:
        """Parse a line of text to extract medication information"""
        medications = []
        
        try:
            # Clean the line
            line_text = line_text.strip()
            
            # Look for medication patterns
            for pattern in self.medication_patterns:
                matches = re.finditer(pattern, line_text, re.IGNORECASE)
                for match in matches:
                    med_text = match.group().strip()
                    
                    if len(med_text) > 2:  # Valid medication text
                        medication = self._parse_medication_details(med_text, line_text)
                        if medication:
                            medications.append(medication)
            
            # Also look for standalone medication names
            words = line_text.split()
            for i, word in enumerate(words):
                if self._looks_like_medication_name(word):
                    # Look for dosage and instructions in surrounding words
                    context = ' '.join(words[max(0, i-2):min(len(words), i+3)])
                    medication = self._parse_medication_details(word, context)
                    if medication:
                        medications.append(medication)
            
        except Exception as e:
            logger.error(f"Medication parsing failed: {e}")
        
        return medications
    
    def _parse_medication_details(self, med_text: str, context: str) -> Optional[Dict]:
        """Parse detailed medication information"""
        try:
            medication = {
                'name': '',
                'dosage': '',
                'form': '',
                'frequency': '',
                'duration': '',
                'instructions': '',
                'raw_text': med_text,
                'confidence': 0.7
            }
            
            # Extract medication name (first significant word)
            words = med_text.split()
            if words:
                medication['name'] = words[0].title()
            
            # Extract dosage
            dosage_match = re.search(r'\d+\s*(mg|ml|gm|g)', context, re.IGNORECASE)
            if dosage_match:
                medication['dosage'] = dosage_match.group()
            
            # Extract form
            form_match = re.search(r'(gel|cream|tablet|cap|capsule|syrup|ointment)', context, re.IGNORECASE)
            if form_match:
                medication['form'] = form_match.group().lower()
            
            # Extract frequency
            freq_match = re.search(r'(\d+\s*x\s*\d+|bd|tds|od|qds)', context, re.IGNORECASE)
            if freq_match:
                freq = freq_match.group().lower()
                medication['frequency'] = self.medical_abbreviations.get(freq, freq)
            
            # Extract duration
            duration_match = re.search(r'\d+\s*(week[s]?|day[s]?|month[s]?)', context, re.IGNORECASE)
            if duration_match:
                medication['duration'] = duration_match.group()
            
            # Extract special instructions
            instruction_match = re.search(r'(r/?f|rf|sos|ac|pc|hs)', context, re.IGNORECASE)
            if instruction_match:
                instr = instruction_match.group().lower()
                medication['instructions'] = self.medical_abbreviations.get(instr, instr)
            
            # Only return if we have at least a name
            if medication['name'] and len(medication['name']) > 1:
                return medication
            
        except Exception as e:
            logger.error(f"Medication detail parsing failed: {e}")
        
        return None
    
    def _looks_like_medication_name(self, word: str) -> bool:
        """Check if a word looks like a medication name"""
        if len(word) < 3:
            return False
        
        # Skip common non-medication words
        skip_words = {'the', 'and', 'for', 'with', 'from', 'this', 'that', 'name', 'age', 'sex', 'date'}
        if word.lower() in skip_words:
            return False
        
        # Must contain letters
        if not re.search(r'[a-zA-Z]', word):
            return False
        
        # Common medication name patterns
        if re.search(r'(cin|zole|pril|olol|ine|ate|ide)$', word, re.IGNORECASE):
            return True
        
        # Check if it's a reasonable length and has vowels/consonants
        vowels = set('aeiou')
        consonants = set('bcdfghjklmnpqrstvwxyz')
        
        word_lower = word.lower()
        has_vowels = any(c in vowels for c in word_lower)
        has_consonants = any(c in consonants for c in word_lower)
        
        return has_vowels and has_consonants and 3 <= len(word) <= 15
    
    def _deduplicate_medications(self, medications: List[Dict]) -> List[Dict]:
        """Remove duplicate medications and keep the best ones"""
        if not medications:
            return []
        
        # Group by similar names
        unique_meds = {}
        
        for med in medications:
            name = med['name'].lower()
            
            # Check if this is similar to an existing medication
            found_similar = False
            for existing_name in unique_meds.keys():
                if self._are_similar_names(name, existing_name):
                    # Keep the one with more information
                    if self._medication_completeness(med) > self._medication_completeness(unique_meds[existing_name]):
                        unique_meds[existing_name] = med
                    found_similar = True
                    break
            
            if not found_similar:
                unique_meds[name] = med
        
        return list(unique_meds.values())
    
    def _are_similar_names(self, name1: str, name2: str) -> bool:
        """Check if two medication names are similar"""
        # Simple similarity check
        if name1 == name2:
            return True
        
        # Check if one is contained in the other
        if name1 in name2 or name2 in name1:
            return True
        
        # Check edit distance for short names
        if len(name1) <= 5 and len(name2) <= 5:
            return abs(len(name1) - len(name2)) <= 1
        
        return False
    
    def _medication_completeness(self, medication: Dict) -> int:
        """Calculate how complete a medication entry is"""
        score = 0
        if medication.get('name'): score += 1
        if medication.get('dosage'): score += 1
        if medication.get('form'): score += 1
        if medication.get('frequency'): score += 1
        if medication.get('duration'): score += 1
        if medication.get('instructions'): score += 1
        return score
    
    def _extract_instructions_from_sections(self, image: np.ndarray, sections: Dict) -> List[str]:
        """Extract general instructions from all sections"""
        instructions = []
        
        for section_name, section_info in sections.items():
            text = section_info.get('text', '')
            
            # Look for instruction patterns
            instruction_patterns = [
                r'apply\s+[^.]*',
                r'take\s+[^.]*',
                r'use\s+[^.]*',
                r'\d+\s*times?\s*daily',
                r'before\s+meals?',
                r'after\s+meals?',
                r'at\s+bedtime'
            ]
            
            for pattern in instruction_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    instruction = match.group().strip()
                    if len(instruction) > 5:
                        instructions.append(instruction)
        
        return list(set(instructions))  # Remove duplicates
    
    def _calculate_section_confidence(self, text: str, section_name: str) -> float:
        """Calculate confidence for a section based on expected keywords"""
        if not text:
            return 0.0
        
        expected_keywords = self.prescription_sections.get(section_name, {}).get('keywords', [])
        
        confidence = 0.0
        text_lower = text.lower()
        
        for keyword in expected_keywords:
            if keyword in text_lower:
                confidence += 0.2
        
        # Bonus for reasonable text length
        if 10 <= len(text) <= 200:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _calculate_layout_confidence(self, sections: Dict, medications: List, instructions: List) -> float:
        """Calculate overall layout analysis confidence"""
        confidence = 0.0
        
        # Base confidence from sections detected
        confidence += len(sections) * 0.1
        
        # Bonus for medications found
        confidence += len(medications) * 0.2
        
        # Bonus for instructions found
        confidence += len(instructions) * 0.1
        
        # Bonus for prescription area detected
        if 'prescription_area' in sections:
            confidence += 0.3
        
        return min(confidence, 1.0)
