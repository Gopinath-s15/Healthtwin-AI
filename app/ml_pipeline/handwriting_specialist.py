#!/usr/bin/env python3
"""
Specialized handwriting OCR processor for medical prescriptions
Optimized for handwritten medical prescriptions with specific preprocessing
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from typing import Dict, List, Tuple, Optional
import logging
import re
import sys
import os

# Import the prescription layout analyzer and medication parser
sys.path.append(os.path.dirname(__file__))
try:
    from prescription_layout_analyzer import PrescriptionLayoutAnalyzer
    LAYOUT_ANALYZER_AVAILABLE = True
except ImportError as e:
    LAYOUT_ANALYZER_AVAILABLE = False
    logging.warning(f"Layout analyzer not available: {e}")

try:
    from handwritten_medication_parser import HandwrittenMedicationParser
    MEDICATION_PARSER_AVAILABLE = True
except ImportError as e:
    MEDICATION_PARSER_AVAILABLE = False
    logging.warning(f"Medication parser not available: {e}")

logger = logging.getLogger(__name__)

class HandwritingSpecialist:
    """Specialized processor for handwritten medical prescriptions"""
    
    def __init__(self):
        """Initialize the handwriting specialist"""
        self.medical_keywords = [
            'tablet', 'capsule', 'syrup', 'cream', 'gel', 'ointment', 'drops',
            'mg', 'ml', 'gm', 'twice', 'thrice', 'daily', 'morning', 'evening',
            'night', 'before', 'after', 'food', 'meal', 'empty', 'stomach',
            'apply', 'take', 'use', 'days', 'weeks', 'month'
        ]

        # Initialize layout analyzer if available
        if LAYOUT_ANALYZER_AVAILABLE:
            self.layout_analyzer = PrescriptionLayoutAnalyzer()
        else:
            self.layout_analyzer = None

        # Initialize medication parser if available
        if MEDICATION_PARSER_AVAILABLE:
            self.medication_parser = HandwrittenMedicationParser()
        else:
            self.medication_parser = None
        
        # Common handwritten medication patterns
        self.medication_patterns = [
            r'[A-Za-z]+\s*\d+\s*mg',  # Medicine + dosage
            r'[A-Za-z]+\s*gel',       # Topical gels
            r'[A-Za-z]+\s*cream',     # Topical creams
            r'[A-Za-z]+\s*\d+\s*ml',  # Liquid medicines
            r'\d+\s*x\s*\d+',         # Frequency patterns
            r'\d+\s*week[s]?',        # Duration patterns
            r'\d+\s*day[s]?',         # Duration patterns
        ]
    
    def enhance_for_handwriting(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Create multiple enhanced versions specifically for handwriting recognition
        """
        enhanced_images = []
        
        try:
            # Convert to PIL for easier manipulation
            if len(image.shape) == 3:
                pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            else:
                pil_image = Image.fromarray(image)
            
            # 1. High contrast version for dark handwriting
            enhancer = ImageEnhance.Contrast(pil_image)
            high_contrast = enhancer.enhance(2.5)
            enhanced_images.append(self._pil_to_cv2(high_contrast))
            
            # 2. Sharpened version for clearer edges
            sharpened = pil_image.filter(ImageFilter.SHARPEN)
            enhancer = ImageEnhance.Sharpness(sharpened)
            extra_sharp = enhancer.enhance(2.0)
            enhanced_images.append(self._pil_to_cv2(extra_sharp))
            
            # 3. Brightness adjusted for faded ink
            enhancer = ImageEnhance.Brightness(pil_image)
            brightened = enhancer.enhance(1.3)
            enhanced_images.append(self._pil_to_cv2(brightened))
            
            # 4. Morphological operations for handwriting
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Erosion to thicken thin strokes
            kernel = np.ones((2,2), np.uint8)
            eroded = cv2.erode(gray, kernel, iterations=1)
            enhanced_images.append(eroded)
            
            # 5. Adaptive threshold for varying lighting
            adaptive_thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            enhanced_images.append(adaptive_thresh)
            
            # 6. Bilateral filter to reduce noise while preserving edges
            bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
            enhanced_images.append(bilateral)
            
            # 7. Gaussian blur + threshold for smooth handwriting
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            enhanced_images.append(thresh)
            
            logger.info(f"Created {len(enhanced_images)} enhanced versions for handwriting")
            return enhanced_images
            
        except Exception as e:
            logger.error(f"Error in handwriting enhancement: {e}")
            return [image]
    
    def _pil_to_cv2(self, pil_image: Image.Image) -> np.ndarray:
        """Convert PIL image to OpenCV format"""
        if pil_image.mode == 'RGB':
            return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        else:
            return np.array(pil_image)
    
    def extract_handwritten_text(self, image: np.ndarray) -> Dict:
        """
        Extract text from handwritten prescription using specialized techniques
        """
        results = {
            'success': False,
            'text': '',
            'confidence': 0.0,
            'medications': [],
            'instructions': [],
            'method': 'handwriting_specialist'
        }
        
        try:
            # First try layout analysis if available
            layout_medications = []
            layout_instructions = []

            if self.layout_analyzer:
                logger.info("Using prescription layout analyzer")
                layout_result = self.layout_analyzer.analyze_prescription_layout(image)

                if layout_result.get('success'):
                    layout_medications = layout_result.get('medications', [])
                    layout_instructions = layout_result.get('instructions', [])
                    logger.info(f"Layout analyzer found {len(layout_medications)} medications")

            # Get enhanced versions for fallback OCR
            enhanced_images = self.enhance_for_handwriting(image)

            all_texts = []
            all_confidences = []

            # Try different Tesseract configurations for handwriting
            handwriting_configs = [
                '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,()/-+%',
                '--psm 8 --oem 3',
                '--psm 7 --oem 1',
                '--psm 6 --oem 1 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,()/-+%mg',
                '--psm 13 --oem 3',  # Raw line for handwriting
            ]
            
            for img_variant in enhanced_images:
                for config in handwriting_configs:
                    try:
                        # Extract text with confidence
                        data = pytesseract.image_to_data(
                            img_variant, 
                            config=config,
                            output_type=pytesseract.Output.DICT
                        )
                        
                        # Filter high confidence words
                        confident_words = []
                        confidences = []
                        
                        for i, conf in enumerate(data['conf']):
                            if conf > 30:  # Lower threshold for handwriting
                                word = data['text'][i].strip()
                                if len(word) > 1:  # Skip single characters
                                    confident_words.append(word)
                                    confidences.append(conf)
                        
                        if confident_words:
                            text = ' '.join(confident_words)
                            avg_conf = np.mean(confidences) if confidences else 0
                            
                            all_texts.append(text)
                            all_confidences.append(avg_conf)
                            
                    except Exception as e:
                        logger.warning(f"Tesseract config failed: {e}")
                        continue
            
            if all_texts:
                # Find the best result
                best_idx = np.argmax(all_confidences)
                best_text = all_texts[best_idx]
                best_confidence = all_confidences[best_idx]

                # Extract medications and instructions from OCR
                ocr_medications = self._extract_medications(best_text)
                ocr_instructions = self._extract_instructions(best_text)

                # Use specialized medication parser if available
                parser_medications = []
                if self.medication_parser:
                    parser_medications = self.medication_parser.parse_handwritten_medications(best_text)
                    logger.info(f"Specialized parser found {len(parser_medications)} medications")

                # Combine all results
                combined_medications = layout_medications + ocr_medications + parser_medications
                combined_instructions = layout_instructions + ocr_instructions

                # Remove duplicates and improve quality
                final_medications = self._merge_medication_results(combined_medications)
                final_instructions = list(set(combined_instructions))  # Remove duplicates

                results.update({
                    'success': True,
                    'text': best_text,
                    'confidence': best_confidence / 100.0,
                    'medications': final_medications,
                    'instructions': final_instructions,
                    'layout_analysis_used': bool(layout_medications),
                    'layout_medications_count': len(layout_medications),
                    'ocr_medications_count': len(ocr_medications),
                    'parser_medications_count': len(parser_medications)
                })

                logger.info(f"Handwriting extraction successful: {len(final_medications)} medications found (layout: {len(layout_medications)}, OCR: {len(ocr_medications)}, parser: {len(parser_medications)})")

            elif layout_medications:
                # Use layout analyzer results even if OCR failed
                results.update({
                    'success': True,
                    'text': 'Layout analysis only',
                    'confidence': 0.8,
                    'medications': layout_medications,
                    'instructions': layout_instructions,
                    'layout_analysis_used': True,
                    'layout_medications_count': len(layout_medications),
                    'ocr_medications_count': 0
                })

                logger.info(f"Using layout analysis only: {len(layout_medications)} medications found")
            
        except Exception as e:
            logger.error(f"Handwriting extraction failed: {e}")
        
        return results
    
    def _extract_medications(self, text: str) -> List[Dict]:
        """Extract medication information from text"""
        medications = []
        
        try:
            # Split text into lines and process each
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for medication patterns
                for pattern in self.medication_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        med_text = match.group()
                        
                        # Extract components
                        medication = {
                            'name': self._extract_med_name(med_text),
                            'dosage': self._extract_dosage(med_text),
                            'form': self._extract_form(med_text),
                            'raw_text': med_text,
                            'confidence': 0.8  # Base confidence for pattern matches
                        }
                        
                        if medication['name']:
                            medications.append(medication)
            
            # Also look for standalone medication names
            words = text.split()
            for i, word in enumerate(words):
                if len(word) > 3 and word.isalpha():
                    # Check if it might be a medication name
                    if self._looks_like_medication(word):
                        # Look for dosage in nearby words
                        dosage = self._find_nearby_dosage(words, i)
                        
                        medication = {
                            'name': word.title(),
                            'dosage': dosage,
                            'form': 'tablet',  # Default form
                            'raw_text': word,
                            'confidence': 0.7
                        }
                        medications.append(medication)
            
        except Exception as e:
            logger.error(f"Error extracting medications: {e}")
        
        return medications
    
    def _extract_instructions(self, text: str) -> List[str]:
        """Extract usage instructions from text"""
        instructions = []
        
        try:
            # Look for instruction patterns
            instruction_patterns = [
                r'\d+\s*x\s*\d+',  # Frequency like "2 x 3"
                r'\d+\s*times?\s*daily',
                r'\d+\s*week[s]?',
                r'\d+\s*day[s]?',
                r'apply\s+[^.]*',
                r'take\s+[^.]*',
                r'use\s+[^.]*'
            ]
            
            for pattern in instruction_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    instructions.append(match.group().strip())
            
        except Exception as e:
            logger.error(f"Error extracting instructions: {e}")
        
        return instructions
    
    def _extract_med_name(self, text: str) -> str:
        """Extract medication name from text"""
        # Remove dosage and form information
        name = re.sub(r'\d+\s*(mg|ml|gm)', '', text, flags=re.IGNORECASE)
        name = re.sub(r'(gel|cream|tablet|capsule|syrup)', '', name, flags=re.IGNORECASE)
        return name.strip().title()
    
    def _extract_dosage(self, text: str) -> str:
        """Extract dosage from text"""
        dosage_match = re.search(r'\d+\s*(mg|ml|gm)', text, re.IGNORECASE)
        return dosage_match.group() if dosage_match else ''
    
    def _extract_form(self, text: str) -> str:
        """Extract medication form from text"""
        form_match = re.search(r'(gel|cream|tablet|capsule|syrup)', text, re.IGNORECASE)
        return form_match.group().lower() if form_match else 'tablet'
    
    def _looks_like_medication(self, word: str) -> bool:
        """Check if a word looks like a medication name"""
        # Simple heuristics for medication names
        if len(word) < 4:
            return False
        
        # Common medication endings
        med_endings = ['in', 'ol', 'ide', 'ine', 'ate', 'ium']
        if any(word.lower().endswith(ending) for ending in med_endings):
            return True
        
        # Contains both consonants and vowels
        vowels = set('aeiou')
        consonants = set('bcdfghjklmnpqrstvwxyz')
        
        word_lower = word.lower()
        has_vowels = any(c in vowels for c in word_lower)
        has_consonants = any(c in consonants for c in word_lower)
        
        return has_vowels and has_consonants
    
    def _find_nearby_dosage(self, words: List[str], index: int) -> str:
        """Find dosage information near a medication name"""
        # Look in next 3 words
        for i in range(index + 1, min(index + 4, len(words))):
            word = words[i]
            if re.search(r'\d+\s*(mg|ml|gm)', word, re.IGNORECASE):
                return word
        
        return ''

    def _merge_medication_results(self, medications: List[Dict]) -> List[Dict]:
        """Merge and deduplicate medication results from different sources"""
        if not medications:
            return []

        # Group by similar names
        merged = {}

        for med in medications:
            name = med.get('name', '').lower().strip()
            if not name or len(name) < 2:
                continue

            # Check if this medication is similar to an existing one
            found_match = False
            for existing_name in list(merged.keys()):
                if self._are_medication_names_similar(name, existing_name):
                    # Merge the information, keeping the more complete one
                    existing_med = merged[existing_name]
                    merged_med = self._merge_medication_info(existing_med, med)

                    # Update with the better name (longer, more complete)
                    if len(med.get('name', '')) > len(existing_med.get('name', '')):
                        del merged[existing_name]
                        merged[name] = merged_med
                    else:
                        merged[existing_name] = merged_med

                    found_match = True
                    break

            if not found_match:
                merged[name] = med

        return list(merged.values())

    def _are_medication_names_similar(self, name1: str, name2: str) -> bool:
        """Check if two medication names are similar enough to be the same"""
        if not name1 or not name2:
            return False

        name1 = name1.lower().strip()
        name2 = name2.lower().strip()

        # Exact match
        if name1 == name2:
            return True

        # One contains the other
        if name1 in name2 or name2 in name1:
            return True

        # Similar length and characters (simple similarity)
        if len(name1) >= 4 and len(name2) >= 4:
            # Check if they share most characters
            common_chars = set(name1) & set(name2)
            if len(common_chars) >= min(len(set(name1)), len(set(name2))) * 0.7:
                return True

        return False

    def _merge_medication_info(self, med1: Dict, med2: Dict) -> Dict:
        """Merge information from two medication dictionaries"""
        merged = med1.copy()

        # Take the longer/more complete values
        for key in ['name', 'dosage', 'form', 'frequency', 'duration', 'instructions']:
            val1 = merged.get(key, '')
            val2 = med2.get(key, '')

            if len(val2) > len(val1):
                merged[key] = val2
            elif not val1 and val2:
                merged[key] = val2

        # Take the higher confidence
        conf1 = merged.get('confidence', 0)
        conf2 = med2.get('confidence', 0)
        merged['confidence'] = max(conf1, conf2)

        # Combine raw text
        raw1 = merged.get('raw_text', '')
        raw2 = med2.get('raw_text', '')
        if raw2 and raw2 not in raw1:
            merged['raw_text'] = f"{raw1} | {raw2}" if raw1 else raw2

        return merged
