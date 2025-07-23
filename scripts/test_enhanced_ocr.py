"""
Test script for Enhanced OCR System
Tests handwriting recognition, multi-language support, and unified pipeline
"""
import requests
import json
import time
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
BASE_URL = "http://127.0.0.1:8000"
TEST_IMAGES_DIR = Path("test_images")

class EnhancedOCRTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.test_results = []
        
    def test_health_check(self):
        """Test health check endpoint"""
        logger.info("Testing health check endpoint...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                logger.info("Health check passed")
                logger.info(f"Available engines: {data.get('ocr_engines', {})}")
                logger.info(f"Features: {data.get('features', [])}")
                return True
            else:
                logger.error(f"Health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return False
    
    def test_ocr_capabilities(self):
        """Test OCR capabilities endpoint"""
        logger.info("Testing OCR capabilities endpoint...")
        try:
            response = requests.get(f"{self.base_url}/ocr/capabilities", timeout=10)
            if response.status_code == 200:
                data = response.json()
                logger.info("OCR capabilities retrieved successfully")
                logger.info(f"Available endpoints: {list(data.get('available_endpoints', {}).keys())}")
                logger.info(f"Processing modes: {list(data.get('processing_modes', {}).keys())}")
                return True
            else:
                logger.error(f"OCR capabilities failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"OCR capabilities error: {e}")
            return False
    
    def create_test_image(self, image_type="printed"):
        """Create a test prescription image"""
        from PIL import Image, ImageDraw, ImageFont
        import tempfile
        
        # Create a simple test prescription image
        width, height = 800, 600
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None
        
        if image_type == "printed":
            # Create printed text prescription
            text_lines = [
                "Dr. Rajesh Kumar",
                "MBBS, MD (Internal Medicine)",
                "City Hospital, Mumbai",
                "",
                "Patient: Amit Sharma",
                "Age: 35 years",
                "Date: 15/01/2024",
                "",
                "Rx:",
                "1. Paracetamol 500mg",
                "   Take 1 tablet twice daily after meals",
                "   For 5 days",
                "",
                "2. Azithromycin 250mg",
                "   Take 1 tablet once daily",
                "   For 3 days",
                "",
                "Follow up after 1 week"
            ]
            
            y_position = 50
            for line in text_lines:
                draw.text((50, y_position), line, fill='black', font=font)
                y_position += 25
                
        elif image_type == "multilingual":
            # Create mixed language prescription
            text_lines = [
                "Dr. Priya Patel",
                "MBBS, MD",
                "સિટી હોસ્પિટલ, અમદાવાદ",  # Gujarati
                "",
                "Patient: રાજેશ શાહ",  # Gujarati name
                "Age: 45 years",
                "Date: 15/01/2024",
                "",
                "Rx:",
                "1. Paracetamol 500mg",
                "   સવારે અને સાંજે ખાવાનું",  # Gujarati instructions
                "   ૫ દિવસ માટે",  # Gujarati duration
                "",
                "2. Amoxicillin 250mg",
                "   દિવસમાં ત્રણ વાર",  # Gujarati frequency
                "",
                "Follow up: ૧ અઠવાડિયા પછી"  # Gujarati follow-up
            ]
            
            y_position = 50
            for line in text_lines:
                draw.text((50, y_position), line, fill='black', font=font)
                y_position += 25
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        image.save(temp_file.name, 'PNG')
        return temp_file.name
    
    def test_legacy_ocr(self, image_path):
        """Test legacy OCR endpoint"""
        logger.info("Testing legacy OCR endpoint...")
        try:
            with open(image_path, 'rb') as f:
                files = {'file': ('test_prescription.png', f, 'image/png')}
                response = requests.post(
                    f"{self.base_url}/patient/upload-prescription",
                    files=files,
                    timeout=30
                )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("Legacy OCR test passed")
                logger.info(f"Confidence: {data.get('confidence_score', 0):.3f}")
                logger.info(f"Method: {data.get('extraction_method', 'Unknown')}")
                return data
            else:
                logger.error(f"Legacy OCR failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Legacy OCR error: {e}")
            return None
    
    def test_enhanced_ocr(self, image_path, mode="standard"):
        """Test enhanced OCR endpoint"""
        logger.info(f"Testing enhanced OCR endpoint (mode: {mode})...")
        try:
            with open(image_path, 'rb') as f:
                files = {'file': ('test_prescription.png', f, 'image/png')}
                params = {'processing_mode': mode}
                response = requests.post(
                    f"{self.base_url}/patient/upload-prescription-enhanced",
                    files=files,
                    params=params,
                    timeout=60
                )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("Enhanced OCR test passed")
                logger.info(f"Confidence: {data.get('confidence_score', 0):.3f}")
                logger.info(f"Processing mode: {data.get('processing_mode', 'Unknown')}")
                
                # Log enhanced features
                enhanced_features = data.get('enhanced_features', {})
                logger.info(f"Handwriting detected: {enhanced_features.get('handwriting_info', {}).get('handwriting_detected', False)}")
                logger.info(f"Multi-language detected: {enhanced_features.get('multilingual_info', {}).get('is_multilingual', False)}")
                logger.info(f"Engines used: {enhanced_features.get('engines_used', [])}")
                logger.info(f"Processing time: {enhanced_features.get('processing_time', 0):.2f}s")
                
                return data
            else:
                logger.error(f"Enhanced OCR failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Enhanced OCR error: {e}")
            return None
    
    def compare_results(self, legacy_result, enhanced_result):
        """Compare legacy and enhanced OCR results"""
        logger.info("Comparing OCR results...")
        
        if not legacy_result or not enhanced_result:
            logger.warning("Cannot compare - one or both results are missing")
            return
        
        # Compare confidence scores
        legacy_conf = legacy_result.get('confidence_score', 0)
        enhanced_conf = enhanced_result.get('confidence_score', 0)
        
        logger.info(f"Confidence comparison:")
        logger.info(f"  Legacy: {legacy_conf:.3f}")
        logger.info(f"  Enhanced: {enhanced_conf:.3f}")
        logger.info(f"  Improvement: {enhanced_conf - legacy_conf:.3f}")
        
        # Compare extracted medications
        legacy_meds = legacy_result.get('extracted_data', {}).get('medications', '')
        enhanced_meds = enhanced_result.get('prescription_data', {}).get('medications', '')
        
        logger.info(f"Medications comparison:")
        logger.info(f"  Legacy: {legacy_meds}")
        logger.info(f"  Enhanced: {enhanced_meds}")
        
        # Enhanced features
        enhanced_features = enhanced_result.get('enhanced_features', {})
        if enhanced_features:
            logger.info("Enhanced features detected:")
            for feature, info in enhanced_features.items():
                if isinstance(info, dict) and info:
                    logger.info(f"  {feature}: {info}")
    
    def run_comprehensive_test(self):
        """Run comprehensive test suite"""
        logger.info("Starting comprehensive OCR test suite...")
        
        # Test 1: Health check
        if not self.test_health_check():
            logger.error("Health check failed - aborting tests")
            return False
        
        # Test 2: OCR capabilities
        if not self.test_ocr_capabilities():
            logger.error("OCR capabilities check failed")
        
        # Test 3: Create test images and test OCR
        test_scenarios = [
            ("printed", "standard"),
            ("multilingual", "comprehensive")
        ]
        
        for image_type, processing_mode in test_scenarios:
            logger.info(f"\n--- Testing {image_type} prescription with {processing_mode} mode ---")
            
            # Create test image
            image_path = self.create_test_image(image_type)
            
            try:
                # Test legacy OCR
                legacy_result = self.test_legacy_ocr(image_path)
                
                # Test enhanced OCR
                enhanced_result = self.test_enhanced_ocr(image_path, processing_mode)
                
                # Compare results
                self.compare_results(legacy_result, enhanced_result)
                
                # Store results
                self.test_results.append({
                    'image_type': image_type,
                    'processing_mode': processing_mode,
                    'legacy_result': legacy_result,
                    'enhanced_result': enhanced_result
                })
                
            finally:
                # Cleanup test image
                try:
                    os.unlink(image_path)
                except:
                    pass
        
        # Test 4: Performance comparison
        self.analyze_performance()
        
        logger.info("Comprehensive test suite completed")
        return True
    
    def analyze_performance(self):
        """Analyze performance across all tests"""
        logger.info("\n--- Performance Analysis ---")
        
        if not self.test_results:
            logger.warning("No test results to analyze")
            return
        
        total_tests = len(self.test_results)
        successful_legacy = sum(1 for r in self.test_results if r['legacy_result'] and r['legacy_result'].get('success', False))
        successful_enhanced = sum(1 for r in self.test_results if r['enhanced_result'] and r['enhanced_result'].get('success', False))
        
        logger.info(f"Total tests: {total_tests}")
        logger.info(f"Legacy OCR success rate: {successful_legacy}/{total_tests} ({successful_legacy/total_tests*100:.1f}%)")
        logger.info(f"Enhanced OCR success rate: {successful_enhanced}/{total_tests} ({successful_enhanced/total_tests*100:.1f}%)")
        
        # Average confidence scores
        legacy_confidences = [r['legacy_result'].get('confidence_score', 0) for r in self.test_results if r['legacy_result']]
        enhanced_confidences = [r['enhanced_result'].get('confidence_score', 0) for r in self.test_results if r['enhanced_result']]
        
        if legacy_confidences:
            avg_legacy_conf = sum(legacy_confidences) / len(legacy_confidences)
            logger.info(f"Average legacy confidence: {avg_legacy_conf:.3f}")
        
        if enhanced_confidences:
            avg_enhanced_conf = sum(enhanced_confidences) / len(enhanced_confidences)
            logger.info(f"Average enhanced confidence: {avg_enhanced_conf:.3f}")
        
        # Processing times
        processing_times = []
        for result in self.test_results:
            if result['enhanced_result']:
                time_taken = result['enhanced_result'].get('enhanced_features', {}).get('processing_time', 0)
                if time_taken > 0:
                    processing_times.append(time_taken)
        
        if processing_times:
            avg_time = sum(processing_times) / len(processing_times)
            logger.info(f"Average processing time: {avg_time:.2f} seconds")

def main():
    """Main test function"""
    tester = EnhancedOCRTester()
    
    logger.info("Enhanced OCR Test Suite")
    logger.info("=" * 50)
    
    try:
        success = tester.run_comprehensive_test()
        if success:
            logger.info("\nAll tests completed successfully!")
        else:
            logger.error("\nSome tests failed!")
            
    except KeyboardInterrupt:
        logger.info("\nTest suite interrupted by user")
    except Exception as e:
        logger.error(f"\nTest suite failed with error: {e}")

if __name__ == "__main__":
    main()
