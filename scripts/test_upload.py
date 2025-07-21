#!/usr/bin/env python3
"""
Test file upload functionality
"""
import requests
import io
from PIL import Image
import sys

BASE_URL = "http://localhost:8000"

def create_test_image():
    """Create a simple test image"""
    # Create a simple 100x100 red image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def test_file_upload():
    """Test file upload functionality"""
    try:
        # First register a patient
        data = {
            "phone": "9876543210",
            "name": "Upload Test Patient"
        }
        response = requests.post(f"{BASE_URL}/register", json=data, timeout=5)
        if response.status_code != 200:
            print(f"Failed to register patient: {response.status_code}")
            return False
        
        patient_id = response.json().get("healthtwin_id")
        print(f"Registered patient: {patient_id}")
        
        # Create test image
        test_image = create_test_image()
        
        # Upload the image
        files = {
            'file': ('test_prescription.png', test_image, 'image/png')
        }
        params = {
            'patient_id': patient_id
        }
        
        response = requests.post(f"{BASE_URL}/upload-prescription", 
                               files=files, params=params, timeout=10)
        
        print(f"Upload status: {response.status_code}")
        print(f"Upload response: {response.json()}")
        
        if response.status_code == 200:
            # Test timeline to see if upload was recorded
            timeline_response = requests.get(f"{BASE_URL}/timeline/{patient_id}", timeout=5)
            print(f"Timeline after upload: {timeline_response.json()}")
            return True
        
        return False
        
    except Exception as e:
        print(f"Upload test error: {e}")
        return False

def main():
    print("Testing file upload functionality...")
    print("=" * 50)
    
    success = test_file_upload()
    
    print("=" * 50)
    if success:
        print("🎉 File upload test passed!")
        return 0
    else:
        print("❌ File upload test failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
