#!/usr/bin/env python3
"""
Test the enhanced handwriting recognition on the specific prescription image
"""

import requests
import json
import os
from PIL import Image
import numpy as np

def test_handwriting_prescription():
    """Test handwriting recognition on the prescription image"""
    print("🧪 TESTING ENHANCED HANDWRITING PRESCRIPTION PROCESSING")
    print("=" * 70)
    
    # Check if we have a prescription image to test
    image_files = [f for f in os.listdir('.') if f.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf'))]
    
    if not image_files:
        print("❌ No image files found in current directory")
        print("Please add a prescription image file (PNG, JPG, JPEG, or PDF)")
        return False
    
    print(f"📁 Found image files: {image_files}")
    
    # Use the first image file found
    test_file = image_files[0]
    print(f"🔍 Testing with: {test_file}")
    
    try:
        # Test the enhanced endpoint
        with open(test_file, 'rb') as f:
            response = requests.post(
                'http://localhost:8000/patient/upload-prescription-enhanced',
                files={'file': f}
            )
        
        if response.status_code != 200:
            print(f"❌ API Error: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        
        print(f"✅ API Response: Status {response.status_code}")
        print(f"📊 Overall Success: {result.get('success')}")
        print(f"🎯 Confidence Score: {result.get('confidence_score')}")
        print(f"🔧 Extraction Method: {result.get('extraction_method')}")
        
        # Check if handwriting was detected
        enhanced_features = result.get('enhanced_features', {})
        if enhanced_features:
            prescription_type = enhanced_features.get('prescription_type', {})
            if prescription_type.get('type') == 'handwritten':
                print(f"✍️ HANDWRITTEN PRESCRIPTION DETECTED!")
                print(f"   Handwriting Confidence: {prescription_type.get('confidence', 0):.2f}")
        
        # Medical Analysis Results
        medical_analysis = result.get('medical_analysis', {})
        print(f"\n💊 Medical Analysis Success: {medical_analysis.get('success')}")
        
        if medical_analysis.get('success'):
            structured_prescription = medical_analysis.get('structured_prescription', {})
            medicines = structured_prescription.get('medicines', [])
            instructions = structured_prescription.get('instructions', [])
            
            print(f"\n📋 EXTRACTED PRESCRIPTION DATA:")
            print(f"   Medications Found: {len(medicines)}")
            print(f"   Instructions Found: {len(instructions)}")
            
            # Display medications with details
            if medicines:
                print(f"\n💊 MEDICATIONS EXTRACTED:")
                for i, med in enumerate(medicines, 1):
                    name = med.get('name', 'Unknown')
                    confidence = med.get('confidence', 0)
                    category = med.get('category', 'Unknown')
                    dosage = med.get('dosage', 'Not specified')
                    frequency = med.get('frequency', 'Not specified')
                    
                    print(f"   {i}. {name}")
                    print(f"      📊 Confidence: {confidence:.2f}")
                    print(f"      🏷️ Category: {category}")
                    print(f"      💊 Dosage: {dosage}")
                    print(f"      ⏰ Frequency: {frequency}")
                    print()
            else:
                print(f"\n❌ NO MEDICATIONS CLEARLY EXTRACTED")
                print(f"   This indicates the handwriting recognition needs improvement")
            
            # Display instructions
            if instructions:
                print(f"\n📝 INSTRUCTIONS EXTRACTED:")
                for i, instruction in enumerate(instructions, 1):
                    print(f"   {i}. {instruction}")
            
            # Show raw extracted text for debugging
            raw_text = result.get('raw_extracted_text', '')
            if raw_text:
                print(f"\n📄 RAW EXTRACTED TEXT:")
                print(f"   {raw_text[:200]}...")  # First 200 characters
        
        else:
            error = medical_analysis.get('error', 'Unknown error')
            print(f"❌ Medical Analysis Error: {error}")
        
        # Processing details
        processing_info = medical_analysis.get('processing_info', {})
        if processing_info:
            print(f"\n🔧 PROCESSING DETAILS:")
            print(f"   Enhanced NER Used: {processing_info.get('enhanced_ner_used', False)}")
            print(f"   Processing Time: {processing_info.get('processing_time', 0):.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def analyze_prescription_quality():
    """Analyze the quality of prescription extraction"""
    print(f"\n🔍 PRESCRIPTION QUALITY ANALYSIS")
    print("=" * 50)
    
    # Expected elements in a typical prescription
    expected_elements = [
        "Doctor name",
        "Clinic/Hospital name", 
        "Patient name",
        "Date",
        "Medications with dosages",
        "Usage instructions",
        "Duration/frequency"
    ]
    
    print("📋 Elements that should be extracted from a prescription:")
    for i, element in enumerate(expected_elements, 1):
        print(f"   {i}. {element}")
    
    print(f"\n💡 IMPROVEMENT SUGGESTIONS:")
    print(f"   ✅ Use high-resolution images (300+ DPI)")
    print(f"   ✅ Ensure good lighting and contrast")
    print(f"   ✅ Avoid shadows and reflections")
    print(f"   ✅ Keep the prescription flat and straight")
    print(f"   ✅ Include the entire prescription in the image")

if __name__ == "__main__":
    success = test_handwriting_prescription()
    
    if success:
        print(f"\n🎉 Handwriting prescription test completed!")
        analyze_prescription_quality()
        
        print(f"\n🚀 NEXT STEPS FOR IMPROVEMENT:")
        print(f"   1. 📸 Test with higher quality images")
        print(f"   2. 🔧 Fine-tune handwriting recognition parameters")
        print(f"   3. 📚 Expand medical terminology database")
        print(f"   4. 🧠 Improve pattern recognition for handwritten text")
        print(f"   5. 🔄 Add feedback loop for continuous improvement")
    else:
        print(f"\n❌ Handwriting prescription test failed!")
        print(f"   Please check server status and try again")
