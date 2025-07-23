"""
Enhanced Handwriting Recognition Engine for Medical Prescriptions
Supports handwritten text extraction using TrOCR and EasyOCR
"""
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import re
from typing import Dict, List, Tuple, Any, Optional
import logging
import warnings

# Enhanced image processing imports
try:
    from skimage import exposure, filters, morphology
    from scipy import ndimage
    ADVANCED_PROCESSING_AVAILABLE = True
    logging.info("Advanced image processing libraries available")
except ImportError:
    ADVANCED_PROCESSING_AVAILABLE = False
    logging.warning("Advanced image processing libraries not available - using basic preprocessing")

# Try to import ML dependencies, fall back gracefully if not available
try:
    import torch
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    TORCH_AVAILABLE = True
    logging.info("PyTorch and Transformers available for handwriting recognition")
except ImportError as e:
    TORCH_AVAILABLE = False
    logging.warning(f"PyTorch/Transformers not available - handwriting recognition will be limited: {e}")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
    logging.info("EasyOCR available for alternative handwriting recognition")
except ImportError as e:
    EASYOCR_AVAILABLE = False
    logging.warning(f"EasyOCR not available - alternative handwriting recognition will be limited: {e}")

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Import handwriting specialist
try:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from handwriting_specialist import HandwritingSpecialist
    HANDWRITING_SPECIALIST_AVAILABLE = True
    logging.info("Handwriting specialist available")
except ImportError as e:
    HANDWRITING_SPECIALIST_AVAILABLE = False
    logging.warning(f"Handwriting specialist not available: {e}")

logger = logging.getLogger(__name__)

class HandwritingRecognitionEngine:
    def __init__(self):
        """Initialize handwriting recognition models"""
        if TORCH_AVAILABLE:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Initialize handwriting specialist
        if HANDWRITING_SPECIALIST_AVAILABLE:
            self.handwriting_specialist = HandwritingSpecialist()
            logger.info("Handwriting specialist initialized successfully")
        else:
            self.handwriting_specialist = None
            logger.warning("Handwriting specialist not available")

        if TORCH_AVAILABLE:
            logger.info(f"Using device: {self.device}")
        else:
            self.device = "cpu"
            logger.warning("PyTorch not available - TrOCR disabled, using Tesseract-based handwriting recognition")

        # Initialize TrOCR for handwritten text
        self.trocr_processor = None
        self.trocr_model = None
        if TORCH_AVAILABLE:
            self._init_trocr()

        # Initialize EasyOCR for additional handwriting support
        self.easyocr_reader = None
        if EASYOCR_AVAILABLE:
            self._init_easyocr()

        # Medical terms dictionary for context-aware recognition
        self.medical_terms = self._load_medical_terms()
        
    def _init_trocr(self):
        """Initialize TrOCR model for handwriting recognition"""
        if not TORCH_AVAILABLE:
            logger.warning("TrOCR not available - PyTorch/Transformers not installed")
            return

        try:
            logger.info("Loading enhanced TrOCR model for handwriting recognition...")

            # Try to use the latest handwritten text model
            model_candidates = [
                "microsoft/trocr-large-handwritten",  # Best quality
                "microsoft/trocr-base-handwritten",   # Fallback
            ]

            for model_name in model_candidates:
                try:
                    logger.info(f"Attempting to load {model_name}...")
                    self.trocr_processor = TrOCRProcessor.from_pretrained(model_name)
                    self.trocr_model = VisionEncoderDecoderModel.from_pretrained(model_name)
                    self.trocr_model.to(self.device)
                    self.trocr_model.eval()
                    logger.info(f"TrOCR model loaded successfully: {model_name}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to load {model_name}: {e}")
                    continue

            if self.trocr_model is None:
                logger.error("Failed to load any TrOCR model")

        except Exception as e:
            logger.error(f"Failed to initialize TrOCR: {e}")
            self.trocr_processor = None
            self.trocr_model = None
    
    def _init_easyocr(self):
        """Initialize EasyOCR for additional handwriting support"""
        if not EASYOCR_AVAILABLE:
            logger.warning("EasyOCR not available - package not installed")
            return

        try:
            logger.info("Loading EasyOCR for handwriting recognition...")
            # Support English and common Indian languages
            self.easyocr_reader = easyocr.Reader(['en', 'hi', 'ta', 'te', 'kn', 'ml'])
            logger.info("EasyOCR loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load EasyOCR: {e}")
            self.easyocr_reader = None
    
    def _load_medical_terms(self) -> List[str]:
        """Load common medical terms for context-aware recognition"""
        return [
            # Common medicine types
            'tablet', 'capsule', 'syrup', 'injection', 'drops', 'cream', 'ointment',
            'suspension', 'powder', 'gel', 'lotion', 'spray',
            
            # Common dosage terms
            'mg', 'ml', 'gm', 'mcg', 'iu', 'units', 'dose', 'twice', 'thrice',
            'daily', 'morning', 'evening', 'night', 'before', 'after', 'meals',
            'empty', 'stomach', 'bedtime', 'hourly',
            
            # Common medicine names (abbreviated list)
            'paracetamol', 'ibuprofen', 'aspirin', 'amoxicillin', 'azithromycin',
            'metformin', 'atorvastatin', 'omeprazole', 'pantoprazole', 'ranitidine',
            'cetirizine', 'loratadine', 'prednisolone', 'dexamethasone',
            
            # Medical instructions
            'take', 'apply', 'use', 'continue', 'stop', 'reduce', 'increase',
            'as', 'needed', 'required', 'directed', 'prescribed'
        ]
    
    def preprocess_for_handwriting(self, image_path: str) -> List[np.ndarray]:
        """Enhanced preprocessing specifically for handwritten text"""
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            variants = []
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            variants.append(gray)
            
            # Enhance contrast for handwriting
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            variants.append(enhanced)
            
            # Gaussian blur to smooth handwriting
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            variants.append(blurred)
            
            # Adaptive thresholding for handwriting
            adaptive_thresh = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 15, 10
            )
            variants.append(adaptive_thresh)
            
            # Morphological operations to connect broken characters
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
            morph = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
            variants.append(morph)
            
            # Skew correction for handwritten text
            corrected = self._correct_skew(gray)
            if corrected is not None:
                variants.append(corrected)

            # Add advanced preprocessing variants if available
            if ADVANCED_PROCESSING_AVAILABLE:
                advanced_variants = self._create_advanced_preprocessing_variants(gray)
                variants.extend(advanced_variants)

            # Limit to reasonable number of variants for performance
            return variants[:10]
            
        except Exception as e:
            logger.error(f"Handwriting preprocessing failed: {e}")
            return []

    def _create_advanced_preprocessing_variants(self, gray: np.ndarray) -> List[np.ndarray]:
        """Create advanced preprocessing variants using scikit-image for better handwriting recognition"""
        variants = []

        try:
            # Variant 1: Gamma correction for better contrast
            gamma_corrected = exposure.adjust_gamma(gray, gamma=1.2)
            variants.append(gamma_corrected.astype(np.uint8))

            # Variant 2: Unsharp masking for text sharpening
            blurred = filters.gaussian(gray, sigma=1.0)
            unsharp = gray + 0.6 * (gray - blurred)
            unsharp = np.clip(unsharp, 0, 255).astype(np.uint8)
            variants.append(unsharp)

            # Variant 3: Top-hat transform for text enhancement
            selem = morphology.disk(2)
            tophat = morphology.white_tophat(gray, selem)
            variants.append(tophat)

            # Variant 4: Adaptive histogram equalization
            equalized = exposure.equalize_adapthist(gray, clip_limit=0.03)
            variants.append((equalized * 255).astype(np.uint8))

        except Exception as e:
            logger.warning(f"Failed to create advanced preprocessing variants: {e}")

        return variants

    def _correct_skew(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Correct skew in handwritten text"""
        try:
            # Find contours
            contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
            
            # Find the largest contour (likely the main text area)
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Get minimum area rectangle
            rect = cv2.minAreaRect(largest_contour)
            angle = rect[2]
            
            # Correct angle
            if angle < -45:
                angle = 90 + angle
            
            # Rotate image
            if abs(angle) > 1:  # Only rotate if significant skew
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                return rotated
            
            return image
            
        except Exception as e:
            logger.error(f"Skew correction failed: {e}")
            return None
    
    def extract_handwritten_text_trocr(self, image: np.ndarray) -> Tuple[str, float]:
        """Extract handwritten text using TrOCR"""
        try:
            if self.trocr_processor is None or self.trocr_model is None:
                return "", 0.0
            
            # Convert numpy array to PIL Image
            if len(image.shape) == 3:
                pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            else:
                pil_image = Image.fromarray(image).convert('RGB')
            
            # Process with TrOCR
            pixel_values = self.trocr_processor(pil_image, return_tensors="pt").pixel_values.to(self.device)
            
            with torch.no_grad():
                generated_ids = self.trocr_model.generate(pixel_values, max_length=100)
                generated_text = self.trocr_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # Calculate confidence based on text quality
            confidence = self._calculate_text_confidence(generated_text)
            
            return generated_text.strip(), confidence
            
        except Exception as e:
            logger.error(f"TrOCR extraction failed: {e}")
            return "", 0.0
    
    def extract_handwritten_text_easyocr(self, image: np.ndarray) -> Tuple[str, float]:
        """Extract handwritten text using EasyOCR"""
        try:
            if self.easyocr_reader is None:
                return "", 0.0
            
            # EasyOCR expects image in BGR format
            if len(image.shape) == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            
            # Extract text with confidence scores
            results = self.easyocr_reader.readtext(image, detail=1)
            
            if not results:
                return "", 0.0
            
            # Combine all detected text
            text_parts = []
            confidences = []
            
            for (bbox, text, confidence) in results:
                if confidence > 0.3:  # Filter low confidence detections
                    text_parts.append(text)
                    confidences.append(confidence)
            
            combined_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return combined_text.strip(), avg_confidence
            
        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            return "", 0.0
    
    def _calculate_text_confidence(self, text: str) -> float:
        """Calculate confidence score for extracted text"""
        if not text or len(text.strip()) < 2:
            return 0.0
        
        score = 0.0
        
        # Base score for having text
        score += 0.3
        
        # Score for medical terms
        text_lower = text.lower()
        medical_matches = sum(1 for term in self.medical_terms if term in text_lower)
        score += min(medical_matches * 0.1, 0.4)
        
        # Score for proper formatting (numbers, letters)
        if re.search(r'\d+', text):  # Contains numbers (dosage)
            score += 0.1
        if re.search(r'[a-zA-Z]{3,}', text):  # Contains words
            score += 0.2
        
        return min(score, 1.0)
    
    def process_handwritten_prescription(self, image_path: str) -> Dict[str, Any]:
        """Main function to process handwritten prescription"""
        try:
            logger.info(f"Processing handwritten prescription: {image_path}")
            
            # Preprocess image for handwriting
            image_variants = self.preprocess_for_handwriting(image_path)
            
            if not image_variants:
                return self._create_error_response("Could not preprocess image for handwriting")
            
            # Extract text using multiple methods
            all_results = []
            
            for i, variant in enumerate(image_variants):
                # Try Handwriting Specialist first (most specialized)
                if self.handwriting_specialist:
                    logger.info(f"Using handwriting specialist for variant {i+1}")
                    specialist_result = self.handwriting_specialist.extract_handwritten_text(variant)
                    logger.info(f"Handwriting specialist result: success={specialist_result['success']}, medications={len(specialist_result.get('medications', []))}")
                    if specialist_result['success']:
                        all_results.append({
                            'method': f'HandwritingSpecialist_variant_{i+1}',
                            'text': specialist_result['text'],
                            'confidence': specialist_result['confidence'],
                            'medications': specialist_result.get('medications', []),
                            'instructions': specialist_result.get('instructions', [])
                        })
                else:
                    logger.warning("Handwriting specialist not available for processing")

                # Try TrOCR
                trocr_text, trocr_conf = self.extract_handwritten_text_trocr(variant)
                if trocr_text:
                    all_results.append({
                        'method': f'TrOCR_variant_{i+1}',
                        'text': trocr_text,
                        'confidence': trocr_conf
                    })

                # Try EasyOCR
                easyocr_text, easyocr_conf = self.extract_handwritten_text_easyocr(variant)
                if easyocr_text:
                    all_results.append({
                        'method': f'EasyOCR_variant_{i+1}',
                        'text': easyocr_text,
                        'confidence': easyocr_conf
                    })
            
            if not all_results:
                return self._create_error_response("No handwritten text extracted")
            
            # Select best result
            best_result = max(all_results, key=lambda x: x['confidence'])
            
            # Combine and clean results
            combined_text = self._combine_handwriting_results(all_results)
            
            return {
                'success': True,
                'handwriting_detected': True,
                'best_method': best_result['method'],
                'best_text': best_result['text'],
                'best_confidence': best_result['confidence'],
                'combined_text': combined_text,
                'all_results': all_results,
                'total_variants_processed': len(image_variants)
            }
            
        except Exception as e:
            logger.error(f"Handwriting processing failed: {e}")
            return self._create_error_response(f"Handwriting processing error: {str(e)}")
    
    def _combine_handwriting_results(self, results: List[Dict]) -> str:
        """Intelligently combine handwriting recognition results"""
        if not results:
            return ""
        
        # Group by confidence levels
        high_conf = [r for r in results if r['confidence'] > 0.7]
        med_conf = [r for r in results if 0.4 <= r['confidence'] <= 0.7]
        
        # Prefer high confidence results
        if high_conf:
            return max(high_conf, key=lambda x: x['confidence'])['text']
        elif med_conf:
            return max(med_conf, key=lambda x: x['confidence'])['text']
        else:
            return max(results, key=lambda x: x['confidence'])['text']
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response for handwriting recognition"""
        return {
            'success': False,
            'handwriting_detected': False,
            'error': error_message,
            'best_method': 'None',
            'best_text': '',
            'best_confidence': 0.0,
            'combined_text': '',
            'all_results': [],
            'total_variants_processed': 0
        }
