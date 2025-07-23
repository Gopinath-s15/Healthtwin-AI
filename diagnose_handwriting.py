#!/usr/bin/env python3
"""
Diagnostic script to analyze handwriting recognition issues
"""

import requests
import json
import cv2
import numpy as np
from PIL import Image
import pytesseract
import os

def diagnose_prescription_ocr():
    """Diagnose OCR issues with the prescription"""
    print("🔍 DIAGNOSING HANDWRITING OCR ISSUES")
    print("=" * 60)
    
    # Find prescription image
    image_files = [f for f in os.listdir('.') if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not image_files:
        print("❌ No image files found")
        return
    
    test_file = image_files[0]
    print(f"📁 Analyzing: {test_file}")
    
    try:
        # Load and analyze the image directly
        image = cv2.imread(test_file)
        if image is None:
            print(f"❌ Could not load image: {test_file}")
            return
        
        print(f"📐 Image dimensions: {image.shape}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Try basic OCR on the whole image
        print(f"\n🔤 BASIC OCR RESULTS:")
        print("-" * 40)
        
        try:
            full_text = pytesseract.image_to_string(gray, config='--psm 6 --oem 3')
            print(f"Full text extracted:")
            print(full_text[:500] + "..." if len(full_text) > 500 else full_text)
        except Exception as e:
            print(f"❌ Basic OCR failed: {e}")
        
        # Try different OCR configurations
        configs = [
            ('PSM 6 (Uniform block)', '--psm 6 --oem 3'),
            ('PSM 8 (Single word)', '--psm 8 --oem 3'),
            ('PSM 7 (Single line)', '--psm 7 --oem 3'),
            ('PSM 4 (Single column)', '--psm 4 --oem 3'),
            ('PSM 13 (Raw line)', '--psm 13 --oem 3'),
        ]
        
        print(f"\n🧪 TESTING DIFFERENT OCR CONFIGURATIONS:")
        print("-" * 50)
        
        for name, config in configs:
            try:
                text = pytesseract.image_to_string(gray, config=config)
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                print(f"\n{name}:")
                print(f"  Lines found: {len(lines)}")
                if lines:
                    print(f"  Sample: {lines[0][:50]}...")
            except Exception as e:
                print(f"  ❌ Failed: {e}")
        
        # Analyze image regions
        print(f"\n📊 ANALYZING IMAGE REGIONS:")
        print("-" * 40)
        
        height, width = gray.shape
        regions = {
            'Header (Top 25%)': gray[0:height//4, :],
            'Patient Info (25-50%)': gray[height//4:height//2, :],
            'Prescription Area (50-75%)': gray[height//2:3*height//4, :],
            'Footer (Bottom 25%)': gray[3*height//4:, :]
        }
        
        for region_name, region_img in regions.items():
            try:
                region_text = pytesseract.image_to_string(region_img, config='--psm 6 --oem 3')
                lines = [line.strip() for line in region_text.split('\n') if line.strip()]
                print(f"\n{region_name}:")
                print(f"  Lines: {len(lines)}")
                if lines:
                    for i, line in enumerate(lines[:3]):  # Show first 3 lines
                        print(f"    {i+1}. {line}")
            except Exception as e:
                print(f"  ❌ Failed: {e}")
        
        # Test API response
        print(f"\n🌐 TESTING API RESPONSE:")
        print("-" * 30)
        
        try:
            with open(test_file, 'rb') as f:
                response = requests.post(
                    'http://localhost:8000/patient/upload-prescription-enhanced',
                    files={'file': f}
                )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ API Success: {result.get('success')}")
                print(f"📊 Confidence: {result.get('confidence_score')}")
                
                medical_analysis = result.get('medical_analysis', {})
                if medical_analysis.get('success'):
                    structured = medical_analysis.get('structured_prescription', {})
                    medicines = structured.get('medicines', [])
                    
                    print(f"💊 Medicines found: {len(medicines)}")
                    for i, med in enumerate(medicines):
                        print(f"  {i+1}. {med.get('name', 'Unknown')} (conf: {med.get('confidence', 0):.2f})")
                
                # Check raw extracted text
                raw_text = result.get('raw_extracted_text', '')
                if raw_text:
                    print(f"\n📄 Raw extracted text (first 200 chars):")
                    print(f"  {raw_text[:200]}...")
                
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ API test failed: {e}")
        
        # Image enhancement analysis
        print(f"\n🎨 IMAGE ENHANCEMENT ANALYSIS:")
        print("-" * 40)
        
        # Try different image enhancements
        enhancements = {
            'Original': gray,
            'High Contrast': cv2.convertScaleAbs(gray, alpha=2.0, beta=0),
            'Gaussian Blur': cv2.GaussianBlur(gray, (3, 3), 0),
            'Bilateral Filter': cv2.bilateralFilter(gray, 9, 75, 75),
            'Adaptive Threshold': cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        }
        
        for name, enhanced_img in enhancements.items():
            try:
                text = pytesseract.image_to_string(enhanced_img, config='--psm 6 --oem 3')
                words = len([word for word in text.split() if len(word) > 2])
                print(f"  {name}: {words} meaningful words")
            except Exception as e:
                print(f"  {name}: Failed - {e}")
        
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")

def suggest_improvements():
    """Suggest specific improvements based on analysis"""
    print(f"\n💡 SPECIFIC IMPROVEMENT SUGGESTIONS:")
    print("=" * 50)
    
    suggestions = [
        "🔧 Implement region-specific OCR for prescription area",
        "📐 Add automatic image rotation and skew correction",
        "🎯 Use specialized handwriting recognition models",
        "📊 Implement confidence-based result merging",
        "🔍 Add pattern matching for common medication names",
        "📝 Implement context-aware medication extraction",
        "🧠 Add machine learning-based handwriting classification",
        "📈 Implement feedback loop for continuous improvement"
    ]
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. {suggestion}")

if __name__ == "__main__":
    diagnose_prescription_ocr()
    suggest_improvements()
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"  1. Focus on the prescription area (50-75% of image)")
    print(f"  2. Implement specialized handwriting patterns")
    print(f"  3. Use multiple OCR engines and merge results")
    print(f"  4. Add medical context validation")
    print(f"  5. Implement user feedback for improvement")
