"""
Enhanced OCR Engine with PaddleOCR-Indic support
Handles multilingual Indian prescriptions with better accuracy
"""
import cv2
import numpy as np
from PIL import Image
import paddleocr
import re
from typing import Dict, List, Tuple, Any
import logging

class EnhancedOCREngine:
    def __init__(self):
        """Initialize PaddleOCR with Indian language support"""
        self.ocr_engines = {
            'english': paddleocr.PaddleOCR(use_angle_cls=True, lang='en'),
            'hindi': paddleocr.PaddleOCR(use_angle_cls=True, lang='hi'),
            'tamil': paddleocr.PaddleOCR(use_angle_cls=True, lang='ta'),
            'telugu': paddleocr.PaddleOCR(use_angle_cls=True, lang='te'),
            'kannada': paddleocr.PaddleOCR(use_angle_cls=True, lang='kn'),
            'malayalam': paddleocr.PaddleOCR(use_angle_cls=True, lang='ml')
        }
        self.primary_engine = self.ocr_engines['english']
        
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Enhanced image preprocessing for better OCR"""
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Noise reduction
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # Adaptive thresholding for better text extraction
        binary = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Morphological operations to clean up
        kernel = np.ones((1,1), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def extract_text_multilingual(self, image_path: str) -> Dict[str, Any]:
        """Extract text using multiple OCR engines"""
        try:
            # Preprocess image
            processed_img = self.preprocess_image(image_path)
            
            results = {}
            confidence_scores = {}
            
            # Try English first (most medical prescriptions have English)
            eng_result = self.primary_engine.ocr(processed_img, cls=True)
            if eng_result and eng_result[0]:
                eng_text, eng_confidence = self._process_ocr_result(eng_result)
                results['english'] = eng_text
                confidence_scores['english'] = eng_confidence
            
            # Detect if regional language is present
            regional_lang = self._detect_regional_language(processed_img)
            if regional_lang and regional_lang in self.ocr_engines:
                regional_result = self.ocr_engines[regional_lang].ocr(processed_img, cls=True)
                if regional_result and regional_result[0]:
                    regional_text, regional_confidence = self._process_ocr_result(regional_result)
                    results[regional_lang] = regional_text
                    confidence_scores[regional_lang] = regional_confidence
            
            # Combine results intelligently
            combined_text = self._combine_multilingual_results(results)
            overall_confidence = max(confidence_scores.values()) if confidence_scores else 0.0
            
            return {
                'combined_text': combined_text,
                'language_results': results,
                'confidence_scores': confidence_scores,
                'overall_confidence': overall_confidence,
                'detected_languages': list(results.keys())
            }
            
        except Exception as e:
            logging.error(f"OCR extraction failed: {e}")
            return {
                'combined_text': '',
                'language_results': {},
                'confidence_scores': {},
                'overall_confidence': 0.0,
                'detected_languages': [],
                'error': str(e)
            }
    
    def _process_ocr_result(self, ocr_result: List) -> Tuple[str, float]:
        """Process PaddleOCR result and calculate confidence"""
        text_lines = []
        confidences = []
        
        for line in ocr_result[0]:
            if len(line) >= 2:
                text = line[1][0] if isinstance(line[1], tuple) else line[1]
                confidence = line[1][1] if isinstance(line[1], tuple) and len(line[1]) > 1 else 0.8
                
                text_lines.append(text)
                confidences.append(confidence)
        
        combined_text = '\n'.join(text_lines)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return combined_text, avg_confidence
    
    def _detect_regional_language(self, image: np.ndarray) -> str:
        """Detect regional Indian language in image"""
        # Simple heuristic - in production, use a language detection model
        # For now, try Hindi as it's most common
        return 'hindi'
    
    def _combine_multilingual_results(self, results: Dict[str, str]) -> str:
        """Intelligently combine multilingual OCR results"""
        if not results:
            return ""
        
        # Prioritize English for medical terms, combine with regional for names
        combined_lines = []
        
        if 'english' in results:
            eng_lines = results['english'].split('\n')
            combined_lines.extend(eng_lines)
        
        # Add unique lines from regional languages
        for lang, text in results.items():
            if lang != 'english':
                regional_lines = text.split('\n')
                for line in regional_lines:
                    if line.strip() and not any(self._similar_text(line, existing) for existing in combined_lines):
                        combined_lines.append(line)
        
        return '\n'.join(combined_lines)
    
    def _similar_text(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """Check if two text lines are similar"""
        # Simple similarity check - in production, use proper text similarity
        text1_clean = re.sub(r'[^\w\s]', '', text1.lower())
        text2_clean = re.sub(r'[^\w\s]', '', text2.lower())
        
        if not text1_clean or not text2_clean:
            return False
        
        # Jaccard similarity
        set1 = set(text1_clean.split())
        set2 = set(text2_clean.split())
        
        if not set1 or not set2:
            return False
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return (intersection / union) >= threshold