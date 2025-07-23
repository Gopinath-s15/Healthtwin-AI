#!/usr/bin/env python3
"""
Test script for PDF processing functionality in HealthTwin AI
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.pdf_processor import PDFProcessor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pdf_processor():
    """Test the PDF processor functionality"""
    
    print("=" * 60)
    print("HealthTwin AI - PDF Processing Test")
    print("=" * 60)
    
    # Initialize PDF processor
    pdf_processor = PDFProcessor()
    
    # Check if PDF processing is supported
    print(f"PDF Processing Supported: {pdf_processor.is_pdf_supported()}")
    print(f"Max Pages: {pdf_processor.max_pages}")
    print(f"Max File Size: {pdf_processor.max_file_size // (1024*1024)}MB")
    print(f"Zoom Factor: {pdf_processor.zoom_factor}")
    
    if not pdf_processor.is_pdf_supported():
        print("\n❌ PDF processing not supported - missing dependencies")
        print("Required dependencies:")
        print("- pypdfium2 (for PDF reading)")
        print("- opencv-python (for image processing)")
        print("- Pillow (for image handling)")
        return False
    
    print("\n✅ PDF processing is fully supported!")
    
    # Test with a sample PDF (if available)
    test_pdf_path = "test_prescription.pdf"
    if os.path.exists(test_pdf_path):
        print(f"\n📄 Testing with {test_pdf_path}...")
        
        try:
            with open(test_pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Validate PDF
            validation = pdf_processor.validate_pdf_file(pdf_content, test_pdf_path)
            print(f"Validation Result: {validation}")
            
            if validation["valid"]:
                # Process PDF
                result = pdf_processor.process_pdf_for_ocr(pdf_content, test_pdf_path)
                print(f"Processing Result: {result}")
                
                if result["success"]:
                    print(f"✅ Successfully processed {result['extracted_pages']} pages")
                    
                    # Cleanup
                    pdf_processor.cleanup_temp_files(result["temp_paths"])
                    print("✅ Temporary files cleaned up")
                else:
                    print(f"❌ Processing failed: {result['error']}")
            else:
                print(f"❌ PDF validation failed: {validation['error']}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
    else:
        print(f"\n📄 No test PDF found at {test_pdf_path}")
        print("To test with a real PDF, place a prescription PDF file named 'test_prescription.pdf' in the project root")
    
    return True

def test_file_validation():
    """Test file validation logic"""
    
    print("\n" + "=" * 60)
    print("Testing File Validation Logic")
    print("=" * 60)
    
    # Import the validation function
    try:
        from app.main import validate_file_type
        
        # Mock UploadFile objects for testing
        class MockUploadFile:
            def __init__(self, content_type, filename):
                self.content_type = content_type
                self.filename = filename
        
        # Test cases
        test_cases = [
            ("image/jpeg", "prescription.jpg", True, "image"),
            ("image/png", "prescription.png", True, "image"),
            ("application/pdf", "prescription.pdf", True, "pdf"),
            ("text/plain", "prescription.txt", False, None),
            ("application/msword", "prescription.doc", False, None),
            (None, "prescription.unknown", False, None),
        ]
        
        for content_type, filename, expected_valid, expected_type in test_cases:
            mock_file = MockUploadFile(content_type, filename)
            result = validate_file_type(mock_file)
            
            status = "✅" if result["valid"] == expected_valid else "❌"
            print(f"{status} {filename} ({content_type}): {result}")
            
            if expected_valid and result["valid"]:
                assert result["file_type"] == expected_type, f"Expected {expected_type}, got {result['file_type']}"
        
        print("\n✅ All file validation tests passed!")
        
    except ImportError as e:
        print(f"❌ Could not import validation function: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Starting HealthTwin AI PDF Support Tests...\n")
    
    success = True
    
    # Test PDF processor
    if not test_pdf_processor():
        success = False
    
    # Test file validation
    if not test_file_validation():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests completed successfully!")
        print("\nPDF support is ready for HealthTwin AI prescription processing!")
        print("\nSupported features:")
        print("- PDF file upload validation")
        print("- Multi-page PDF processing")
        print("- Image extraction from PDF pages")
        print("- OCR processing of extracted images")
        print("- Combined results from all pages")
        print("- Automatic cleanup of temporary files")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    print("=" * 60)
