import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class EnhancedPrescriptionOCR:
    def __init__(self):
        self.confidence_threshold = 0.6
        
    def preprocess_image(self, image_path: str) -> List[np.ndarray]:
        """Enhanced preprocessing with multiple variants"""
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError("Could not load image")
            
            variants = []
            
            # Original grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            variants.append(gray)
            
            # High contrast
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            variants.append(enhanced)
            
            # Denoised
            denoised = cv2.fastNlMeansDenoising(gray)
            variants.append(denoised)
            
            # Thresholded
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            variants.append(thresh)
            
            # Morphological operations
            kernel = np.ones((2,2), np.uint8)
            morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            variants.append(morph)
            
            return variants
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            # Fallback to simple grayscale
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            return [img] if img is not None else []
    
    def extract_text_with_tesseract(self, image: np.ndarray) -> str:
        """Extract text using Tesseract with multiple configs"""
        try:
            configs = [
                '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,:-/ ',
                '--psm 4',
                '--psm 3',
                '--psm 1'
            ]
            
            best_text = ""
            max_confidence = 0
            
            for config in configs:
                try:
                    text = pytesseract.image_to_string(image, config=config)
                    if len(text.strip()) > len(best_text.strip()):
                        best_text = text
                except:
                    continue
            
            return best_text.strip()
            
        except Exception as e:
            logger.error(f"Tesseract extraction failed: {e}")
            return ""
    
    def extract_medical_info(self, text: str) -> Dict[str, str]:
        """Enhanced medical information extraction"""
        if not text or len(text.strip()) < 10:
            return {}
        
        text_lower = text.lower()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        result = {}
        
        # Doctor name patterns
        doctor_patterns = [
            r'dr\.?\s+([a-z\s\.]+)',
            r'doctor\s+([a-z\s\.]+)',
            r'physician\s+([a-z\s\.]+)',
            r'consultant\s+([a-z\s\.]+)'
        ]
        
        for pattern in doctor_patterns:
            match = re.search(pattern, text_lower)
            if match:
                result['doctor_name'] = match.group(1).strip().title()
                break
        
        # Clinic/Hospital patterns
        clinic_patterns = [
            r'(hospital|clinic|medical center|healthcare|nursing home)[\s\w]*',
            r'([a-z\s]+(?:hospital|clinic|medical center))',
            r'([a-z\s]+(?:healthcare|medical))'
        ]
        
        for pattern in clinic_patterns:
            match = re.search(pattern, text_lower)
            if match:
                result['clinic_name'] = match.group(0).strip().title()
                break
        
        # Date patterns
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{2,4})',
            r'date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text_lower)
            if match:
                result['prescription_date'] = match.group(1)
                break
        
        # Medication patterns
        medication_keywords = ['tab', 'tablet', 'capsule', 'syrup', 'injection', 'mg', 'ml', 'drops']
        medications = []
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in medication_keywords):
                # Clean and format medication
                med = re.sub(r'^\d+\.?\s*', '', line)  # Remove numbering
                if len(med.strip()) > 3:
                    medications.append(med.strip())
        
        if medications:
            result['medications'] = ', '.join(medications[:5])  # Limit to 5 medications
        
        # Diagnosis patterns
        diagnosis_keywords = ['diagnosis', 'condition', 'disease', 'infection', 'syndrome', 'disorder']
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in diagnosis_keywords):
                # Extract diagnosis
                diag = re.sub(r'diagnosis[:\s]*', '', line, flags=re.IGNORECASE)
                if len(diag.strip()) > 3:
                    result['diagnosis'] = diag.strip()
                    break
        
        # Patient name (usually at top)
        if lines:
            first_few_lines = lines[:3]
            for line in first_few_lines:
                # Skip lines with doctor/clinic info
                if not any(word in line.lower() for word in ['dr', 'doctor', 'clinic', 'hospital']):
                    # Check if it looks like a name
                    if re.match(r'^[a-zA-Z\s\.]{3,30}$', line.strip()):
                        result['patient_name'] = line.strip().title()
                        break
        
        return result
    
    def process_prescription(self, image_path: str) -> Dict[str, Any]:
        """Main processing function with enhanced extraction"""
        try:
            logger.info(f"Processing prescription: {image_path}")
            
            # Preprocess image variants
            image_variants = self.preprocess_image(image_path)
            
            if not image_variants:
                return self._create_error_response("Could not preprocess image")
            
            # Extract text from all variants
            all_texts = []
            for i, variant in enumerate(image_variants):
                text = self.extract_text_with_tesseract(variant)
                if text:
                    all_texts.append(text)
                    logger.info(f"Variant {i+1} extracted {len(text)} characters")
            
            if not all_texts:
                return self._create_error_response("No text extracted from image")
            
            # Combine and analyze all extracted texts
            combined_text = '\n'.join(all_texts)
            best_text = max(all_texts, key=len)  # Use longest extraction as primary
            
            logger.info(f"Best extraction: {len(best_text)} characters")
            logger.info(f"Sample text: {best_text[:200]}...")
            
            # Extract medical information
            medical_info = self.extract_medical_info(best_text)
            
            # Calculate confidence based on extracted fields
            confidence_score = self._calculate_confidence(medical_info, best_text)
            
            # Prepare response
            response = {
                "success": True,
                "confidence": confidence_score,
                "confidence_level": self._get_confidence_level(confidence_score),
                "extraction_method": f"Enhanced Tesseract ({len(image_variants)} variants)",
                "requires_review": confidence_score < 0.7,
                "safety_flags": [],
                "raw_extracted_text": best_text,
                **medical_info
            }
            
            # Add defaults for missing fields
            defaults = {
                "doctor_name": "Not clearly visible",
                "patient_name": "Not clearly visible", 
                "clinic_name": "Not found",
                "medications": "Not clearly visible",
                "diagnosis": "Not clearly specified",
                "prescription_date": "Not found",
                "instructions": "Follow doctor's advice",
                "patient_details": "Not found",
                "follow_up": "As advised"
            }
            
            for key, default_value in defaults.items():
                if key not in response:
                    response[key] = default_value
            
            logger.info(f"Processing completed with {confidence_score:.2f} confidence")
            return response
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return self._create_error_response(f"Processing error: {str(e)}")
    
    def _calculate_confidence(self, medical_info: Dict[str, str], text: str) -> float:
        """Calculate confidence based on extracted information"""
        score = 0.0
        
        # Base score for having text
        if text and len(text.strip()) > 50:
            score += 0.3
        
        # Score for each extracted field
        field_scores = {
            'doctor_name': 0.2,
            'medications': 0.3,
            'clinic_name': 0.1,
            'diagnosis': 0.2,
            'prescription_date': 0.1,
            'patient_name': 0.1
        }
        
        for field, weight in field_scores.items():
            if field in medical_info and medical_info[field]:
                score += weight
        
        # Bonus for medical keywords
        medical_keywords = ['tablet', 'mg', 'doctor', 'prescription', 'diagnosis']
        keyword_count = sum(1 for keyword in medical_keywords if keyword in text.lower())
        score += min(keyword_count * 0.05, 0.2)
        
        return min(score, 1.0)
    
    def _get_confidence_level(self, score: float) -> str:
        """Convert confidence score to level"""
        if score >= 0.8:
            return "High"
        elif score >= 0.5:
            return "Medium"
        else:
            return "Low"
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "success": False,
            "confidence": 0.0,
            "confidence_level": "Failed",
            "extraction_method": "Error",
            "requires_review": True,
            "safety_flags": ["Processing Error"],
            "raw_extracted_text": error_message,
            "doctor_name": "Processing failed",
            "patient_name": "Processing failed",
            "clinic_name": "Processing failed", 
            "medications": "Processing failed",
            "diagnosis": "Processing failed",
            "prescription_date": "Processing failed",
            "instructions": "Processing failed",
            "patient_details": "Processing failed",
            "follow_up": "Processing failed"
        }

