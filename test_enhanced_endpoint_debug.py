#!/usr/bin/env python3
"""
Debug test for the enhanced endpoint
"""

import requests
import os

def test_enhanced_endpoint():
    """Test the enhanced endpoint directly"""
    print("🧪 TESTING ENHANCED ENDPOINT DIRECTLY")
    print("=" * 50)
    
    # Find prescription image
    image_files = [f for f in os.listdir('.') if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not image_files:
        print("❌ No image files found")
        return
    
    test_file = image_files[0]
    print(f"📁 Testing with: {test_file}")
    
    url = "http://127.0.0.1:8000/patient/upload-prescription-enhanced"
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'image/jpeg')}
            data = {'processing_mode': 'standard'}
            
            print(f"🚀 Sending request to {url}")
            response = requests.post(url, files=files, data=data)
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📄 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success! Response keys: {list(result.keys())}")
                
                # Check if unified OCR pipeline was used
                extraction_method = result.get('extraction_method', 'Unknown')
                print(f"🔧 Extraction Method: {extraction_method}")
                
                # Check enhanced features
                enhanced_features = result.get('enhanced_features', {})
                print(f"🎯 Enhanced Features: {enhanced_features}")
                
                # Check medical analysis
                medical_analysis = result.get('medical_analysis', {})
                if medical_analysis:
                    structured = medical_analysis.get('structured_prescription', {})
                    medicines = structured.get('medicines', [])
                    print(f"💊 Medicines found: {len(medicines)}")
                    for i, med in enumerate(medicines, 1):
                        print(f"   {i}. {med.get('name', 'Unknown')} (source: {med.get('source', 'unknown')})")
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"📄 Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_enhanced_endpoint()
