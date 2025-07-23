"""
Unified OCR Pipeline for Enhanced Prescription Processing
Combines printed text OCR, handwriting recognition, and multi-language processing
"""
import cv2
import numpy as np
from PIL import Image
import logging
from typing import Dict, List, Tuple, Any, Optional
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# Import our custom OCR engines with error handling
import sys
import os

# Add parent directories to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

HandwritingRecognitionEngine = None
MultilingualOCREngine = None
EnhancedPrescriptionOCR = None

try:
    from handwriting_ocr import HandwritingRecognitionEngine
    logger.info("Handwriting OCR engine imported successfully")
except ImportError as e:
    logger.warning(f"Could not import handwriting OCR: {e}")

try:
    from multilingual_ocr import MultilingualOCREngine
    logger.info("Multilingual OCR engine imported successfully")
except ImportError as e:
    logger.warning(f"Could not import multilingual OCR: {e}")

try:
    from services.ocr_service import EnhancedPrescriptionOCR
    logger.info("Enhanced prescription OCR imported successfully")
except ImportError as e:
    logger.warning(f"Could not import enhanced prescription OCR: {e}")

logger = logging.getLogger(__name__)

class UnifiedOCRPipeline:
    def __init__(self):
        """Initialize the unified OCR pipeline with all engines"""
        logger.info("Initializing Unified OCR Pipeline...")
        
        # Initialize individual engines
        self.handwriting_engine = None
        self.multilingual_engine = None
        self.printed_text_engine = None
        
        self._init_engines()
        
        # Configuration
        self.confidence_thresholds = {
            'high': 0.8,
            'medium': 0.5,
            'low': 0.3
        }
        
        # Processing modes (temporarily disable multilingual due to compatibility issues)
        self.processing_modes = {
            'fast': ['printed_text'],
            'standard': ['printed_text', 'handwriting'],
            'comprehensive': ['printed_text', 'handwriting']
        }
    
    def _init_engines(self):
        """Initialize all OCR engines"""
        try:
            # Initialize printed text OCR engine
            if EnhancedPrescriptionOCR is not None:
                logger.info("Loading printed text OCR engine...")
                self.printed_text_engine = EnhancedPrescriptionOCR()
                logger.info("Printed text OCR engine loaded successfully")
            else:
                logger.warning("Enhanced prescription OCR not available")
                self.printed_text_engine = None

            # Initialize multilingual OCR engine
            if MultilingualOCREngine is not None:
                logger.info("Loading multilingual OCR engine...")
                self.multilingual_engine = MultilingualOCREngine()
                logger.info("Multilingual OCR engine loaded successfully")
            else:
                logger.warning("Multilingual OCR engine not available")
                self.multilingual_engine = None

            # Initialize handwriting recognition engine
            if HandwritingRecognitionEngine is not None:
                logger.info("Loading handwriting recognition engine...")
                self.handwriting_engine = HandwritingRecognitionEngine()
                logger.info("Handwriting recognition engine loaded successfully")
            else:
                logger.warning("Handwriting recognition engine not available")
                self.handwriting_engine = None

            # Check if at least one engine is available
            if not any([self.printed_text_engine, self.multilingual_engine, self.handwriting_engine]):
                raise Exception("No OCR engines could be initialized")

            logger.info("OCR engine initialization completed")

        except Exception as e:
            logger.error(f"Failed to initialize OCR engines: {e}")
            raise
    
    def detect_prescription_type(self, image_path: str) -> Dict[str, Any]:
        """Detect the type of prescription (printed, handwritten, mixed)"""
        try:
            # Read and analyze image
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                return {'type': 'unknown', 'confidence': 0.0, 'features': {}}
            
            features = {}
            
            # Analyze image characteristics
            # 1. Edge density (handwritten text typically has more irregular edges)
            edges = cv2.Canny(img, 50, 150)
            edge_density = np.sum(edges > 0) / (img.shape[0] * img.shape[1])
            features['edge_density'] = edge_density
            
            # 2. Text line regularity (printed text has more regular lines)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            line_regularity = self._calculate_line_regularity(contours, img.shape)
            features['line_regularity'] = line_regularity
            
            # 3. Character uniformity (printed text has more uniform character sizes)
            char_uniformity = self._calculate_character_uniformity(contours)
            features['character_uniformity'] = char_uniformity
            
            # 4. Stroke thickness variation (handwritten text has more variation)
            stroke_variation = self._calculate_stroke_variation(img)
            features['stroke_variation'] = stroke_variation
            
            # Determine prescription type based on features
            prescription_type, confidence = self._classify_prescription_type(features)
            
            return {
                'type': prescription_type,
                'confidence': confidence,
                'features': features,
                'recommended_engines': self._get_recommended_engines(prescription_type)
            }
            
        except Exception as e:
            logger.error(f"Prescription type detection failed: {e}")
            return {
                'type': 'mixed',
                'confidence': 0.5,
                'features': {},
                'recommended_engines': ['printed_text', 'multilingual', 'handwriting']
            }
    
    def _calculate_line_regularity(self, contours: List, image_shape: Tuple) -> float:
        """Calculate regularity of text lines"""
        if not contours:
            return 0.0
        
        # Get bounding rectangles for contours
        rects = [cv2.boundingRect(contour) for contour in contours if cv2.contourArea(contour) > 50]
        
        if len(rects) < 3:
            return 0.5
        
        # Calculate y-coordinate variance (regular lines have low variance)
        y_coords = [rect[1] for rect in rects]
        y_variance = np.var(y_coords)
        
        # Normalize by image height
        normalized_variance = y_variance / (image_shape[0] ** 2)
        
        # Convert to regularity score (lower variance = higher regularity)
        regularity = max(0, 1 - normalized_variance * 1000)
        
        return min(regularity, 1.0)
    
    def _calculate_character_uniformity(self, contours: List) -> float:
        """Calculate uniformity of character sizes"""
        if not contours:
            return 0.0
        
        # Get areas of contours
        areas = [cv2.contourArea(contour) for contour in contours if cv2.contourArea(contour) > 20]
        
        if len(areas) < 5:
            return 0.5
        
        # Calculate coefficient of variation
        mean_area = np.mean(areas)
        std_area = np.std(areas)
        
        if mean_area == 0:
            return 0.0
        
        cv = std_area / mean_area
        
        # Convert to uniformity score (lower CV = higher uniformity)
        uniformity = max(0, 1 - cv)
        
        return min(uniformity, 1.0)
    
    def _calculate_stroke_variation(self, image: np.ndarray) -> float:
        """Calculate stroke thickness variation"""
        try:
            # Apply morphological operations to analyze stroke thickness
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            
            # Erosion and dilation to analyze stroke thickness
            eroded = cv2.erode(image, kernel, iterations=1)
            dilated = cv2.dilate(image, kernel, iterations=1)
            
            # Calculate thickness variation
            thickness_map = dilated - eroded
            variation = np.std(thickness_map[thickness_map > 0])
            
            # Normalize
            normalized_variation = variation / 255.0
            
            return min(normalized_variation, 1.0)
            
        except Exception:
            return 0.5
    
    def _classify_prescription_type(self, features: Dict[str, float]) -> Tuple[str, float]:
        """Classify prescription type based on features"""
        # Scoring thresholds
        printed_score = 0
        handwritten_score = 0
        
        # Line regularity (higher = more likely printed)
        line_reg = features.get('line_regularity', 0.5)
        if line_reg > 0.7:
            printed_score += 2
        elif line_reg < 0.3:
            handwritten_score += 2
        
        # Character uniformity (higher = more likely printed)
        char_unif = features.get('character_uniformity', 0.5)
        if char_unif > 0.7:
            printed_score += 2
        elif char_unif < 0.3:
            handwritten_score += 2
        
        # Stroke variation (higher = more likely handwritten)
        stroke_var = features.get('stroke_variation', 0.5)
        if stroke_var > 0.6:
            handwritten_score += 1
        elif stroke_var < 0.2:
            printed_score += 1
        
        # Edge density (moderate = printed, high = handwritten)
        edge_density = features.get('edge_density', 0.1)
        if 0.05 < edge_density < 0.15:
            printed_score += 1
        elif edge_density > 0.2:
            handwritten_score += 1
        
        # Determine type and confidence
        if printed_score > handwritten_score + 1:
            return 'printed', min(0.9, 0.6 + (printed_score - handwritten_score) * 0.1)
        elif handwritten_score > printed_score + 1:
            return 'handwritten', min(0.9, 0.6 + (handwritten_score - printed_score) * 0.1)
        else:
            return 'mixed', 0.7
    
    def _get_recommended_engines(self, prescription_type: str) -> List[str]:
        """Get recommended OCR engines based on prescription type"""
        if prescription_type == 'printed':
            return ['printed_text', 'multilingual']
        elif prescription_type == 'handwritten':
            return ['handwriting', 'multilingual']
        else:  # mixed
            return ['printed_text', 'multilingual', 'handwriting']
    
    def process_prescription_comprehensive(self, image_path: str, mode: str = 'standard') -> Dict[str, Any]:
        """Process prescription using comprehensive OCR pipeline"""
        start_time = time.time()
        
        try:
            logger.info(f"Starting comprehensive OCR processing: {image_path}")
            
            # Step 1: Detect prescription type
            type_detection = self.detect_prescription_type(image_path)
            logger.info(f"Detected prescription type: {type_detection['type']} (confidence: {type_detection['confidence']:.2f})")
            
            # Step 2: Determine which engines to use
            if mode in self.processing_modes:
                engines_to_use = self.processing_modes[mode]
            else:
                engines_to_use = type_detection['recommended_engines']

            logger.info(f"Engines to use: {engines_to_use}")
            logger.info(f"Available engines: printed_text={bool(self.printed_text_engine)}, multilingual={bool(self.multilingual_engine)}, handwriting={bool(self.handwriting_engine)}")
            
            # Step 3: Process with multiple engines in parallel
            results = {}
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_engine = {}
                
                if 'printed_text' in engines_to_use and self.printed_text_engine:
                    logger.info("Starting printed_text engine")
                    future = executor.submit(self.printed_text_engine.process_prescription, image_path)
                    future_to_engine[future] = 'printed_text'

                if 'multilingual' in engines_to_use and self.multilingual_engine:
                    logger.info("Starting multilingual engine")
                    try:
                        future = executor.submit(self.multilingual_engine.extract_multilingual_text, image_path)
                        future_to_engine[future] = 'multilingual'
                    except Exception as e:
                        logger.warning(f"Failed to start multilingual engine: {e}")
                        # Continue without multilingual engine

                if 'handwriting' in engines_to_use and self.handwriting_engine:
                    logger.info("Starting handwriting engine")
                    future = executor.submit(self.handwriting_engine.process_handwritten_prescription, image_path)
                    future_to_engine[future] = 'handwriting'
                
                # Collect results
                for future in as_completed(future_to_engine):
                    engine_name = future_to_engine[future]
                    try:
                        result = future.result(timeout=30)  # 30 second timeout per engine
                        results[engine_name] = result
                        logger.info(f"Completed {engine_name} processing")
                    except Exception as e:
                        logger.error(f"Engine {engine_name} failed: {e}")
                        results[engine_name] = {'success': False, 'error': str(e)}

                # Ensure we have at least handwriting results if available
                if 'handwriting' not in results and 'handwriting' in engines_to_use and self.handwriting_engine:
                    logger.info("Handwriting engine not in results, running directly...")
                    try:
                        handwriting_result = self.handwriting_engine.process_handwritten_prescription(image_path)
                        results['handwriting'] = handwriting_result
                        logger.info("Direct handwriting processing completed")
                    except Exception as e:
                        logger.error(f"Direct handwriting processing failed: {e}")
                        results['handwriting'] = {'success': False, 'error': str(e)}
            
            # Step 4: Fuse results intelligently
            fused_result = self._fuse_ocr_results(results, type_detection)
            
            # Step 5: Add metadata
            processing_time = time.time() - start_time
            fused_result.update({
                'processing_metadata': {
                    'processing_time_seconds': processing_time,
                    'engines_used': list(results.keys()),
                    'prescription_type': type_detection,
                    'processing_mode': mode,
                    'timestamp': time.time()
                }
            })
            
            logger.info(f"Comprehensive OCR completed in {processing_time:.2f} seconds")
            return fused_result
            
        except Exception as e:
            logger.error(f"Comprehensive OCR processing failed: {e}")
            return self._create_error_response(f"Processing failed: {str(e)}")
    
    def _fuse_ocr_results(self, results: Dict[str, Any], type_detection: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently fuse results from multiple OCR engines"""
        try:
            # Initialize fused result
            fused = {
                'success': False,
                'confidence': 0.0,
                'confidence_level': 'Low',
                'extraction_method': 'Unified Pipeline',
                'requires_review': True,
                'safety_flags': [],
                'raw_extracted_text': '',
                'engine_results': results
            }
            
            # Collect successful results
            successful_results = {k: v for k, v in results.items() if v.get('success', False)}
            
            if not successful_results:
                fused['error'] = 'All OCR engines failed'
                return fused
            
            # Determine primary result based on prescription type and confidence
            primary_result = self._select_primary_result(successful_results, type_detection)
            
            if primary_result:
                # Copy primary result fields
                for key in ['doctor_name', 'patient_name', 'clinic_name', 'medications', 
                           'diagnosis', 'prescription_date', 'instructions', 'patient_details', 'follow_up']:
                    fused[key] = primary_result.get(key, 'Not found')
                
                # Combine text from all engines
                all_texts = []
                for engine, result in successful_results.items():
                    if 'raw_extracted_text' in result:
                        all_texts.append(f"[{engine.upper()}]\n{result['raw_extracted_text']}")
                    elif 'combined_text' in result:
                        all_texts.append(f"[{engine.upper()}]\n{result['combined_text']}")
                    elif 'best_text' in result:
                        all_texts.append(f"[{engine.upper()}]\n{result['best_text']}")
                
                fused['raw_extracted_text'] = '\n\n'.join(all_texts)
                
                # Calculate overall confidence
                confidences = [r.get('confidence', 0) for r in successful_results.values()]
                fused['confidence'] = max(confidences) if confidences else 0.0
                
                # Add multilingual information if available
                if 'multilingual' in successful_results:
                    ml_result = successful_results['multilingual']
                    fused['multilingual_info'] = {
                        'detected_languages': ml_result.get('detected_languages', []),
                        'is_multilingual': ml_result.get('is_multilingual', False),
                        'translated_text': ml_result.get('translated_text', {})
                    }
                
                # Add handwriting information if available
                if 'handwriting' in successful_results:
                    hw_result = successful_results['handwriting']
                    fused['handwriting_info'] = {
                        'handwriting_detected': hw_result.get('handwriting_detected', False),
                        'best_method': hw_result.get('best_method', ''),
                        'handwriting_confidence': hw_result.get('best_confidence', 0.0)
                    }
                
                fused['success'] = True
                fused['confidence_level'] = self._get_confidence_level(fused['confidence'])
                fused['requires_review'] = fused['confidence'] < 0.7
            
            return fused
            
        except Exception as e:
            logger.error(f"Result fusion failed: {e}")
            return self._create_error_response(f"Result fusion error: {str(e)}")
    
    def _select_primary_result(self, results: Dict[str, Any], type_detection: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Select the primary result based on prescription type and confidence"""
        if not results:
            return None
        
        prescription_type = type_detection.get('type', 'mixed')
        
        # Priority order based on prescription type
        if prescription_type == 'handwritten':
            priority_order = ['handwriting', 'multilingual', 'printed_text']
        elif prescription_type == 'printed':
            priority_order = ['printed_text', 'multilingual', 'handwriting']
        else:  # mixed
            priority_order = ['multilingual', 'printed_text', 'handwriting']
        
        # Select best result based on priority and confidence
        best_result = None
        best_score = 0
        
        for engine in priority_order:
            if engine in results:
                result = results[engine]
                confidence = result.get('confidence', 0)
                
                # Boost score based on priority
                priority_boost = (len(priority_order) - priority_order.index(engine)) * 0.1
                score = confidence + priority_boost
                
                if score > best_score:
                    best_score = score
                    best_result = result
        
        return best_result
    
    def _get_confidence_level(self, score: float) -> str:
        """Convert confidence score to level"""
        if score >= self.confidence_thresholds['high']:
            return "High"
        elif score >= self.confidence_thresholds['medium']:
            return "Medium"
        else:
            return "Low"
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'success': False,
            'confidence': 0.0,
            'confidence_level': 'Failed',
            'extraction_method': 'Unified Pipeline',
            'requires_review': True,
            'safety_flags': ['Processing Error'],
            'raw_extracted_text': error_message,
            'error': error_message,
            'engine_results': {},
            'processing_metadata': {
                'processing_time_seconds': 0,
                'engines_used': [],
                'prescription_type': {'type': 'unknown', 'confidence': 0.0},
                'processing_mode': 'error',
                'timestamp': time.time()
            }
        }
