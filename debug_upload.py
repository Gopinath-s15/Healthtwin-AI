#!/usr/bin/env python3
"""
Debug script to test the upload endpoint directly
"""

import requests
import json

def test_upload_with_image():
    """Test upload with an existing image"""
    
    # Try to find an existing image file
    import os
    image_files = []
    for ext in ['jpg', 'jpeg', 'png']:
        for file in os.listdir('.'):
            if file.lower().endswith(f'.{ext}'):
                image_files.append(file)
    
    if not image_files:
        print("No image files found in current directory")
        return False
    
    image_file = image_files[0]
    print(f"Testing upload with image: {image_file}")
    
    try:
        with open(image_file, 'rb') as f:
            files = {'file': (image_file, f, 'image/jpeg')}
            response = requests.post(
                'http://127.0.0.1:8000/patient/upload-prescription',
                files=files,
                timeout=30
            )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Image upload successful!")
            print(f"Success: {result.get('success')}")
            print(f"Message: {result.get('message')}")
            return True
        else:
            print(f"❌ Image upload failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing image upload: {e}")
        return False

def test_upload_with_pdf():
    """Test upload with PDF"""
    
    pdf_file = "test_prescription.pdf"
    if not os.path.exists(pdf_file):
        print(f"PDF file {pdf_file} not found")
        return False
    
    print(f"Testing upload with PDF: {pdf_file}")
    
    try:
        with open(pdf_file, 'rb') as f:
            files = {'file': (pdf_file, f, 'application/pdf')}
            response = requests.post(
                'http://127.0.0.1:8000/patient/upload-prescription',
                files=files,
                timeout=60
            )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ PDF upload successful!")
            print(f"Success: {result.get('success')}")
            print(f"Message: {result.get('message')}")
            return True
        else:
            print(f"❌ PDF upload failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing PDF upload: {e}")
        return False

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get('http://127.0.0.1:8000/health', timeout=10)
        print(f"Health Status Code: {response.status_code}")
        if response.status_code == 200:
            health = response.json()
            print("✅ Server is healthy")
            print(f"OCR Engines: {health.get('ocr_engines', {})}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking health: {e}")
        return False

if __name__ == "__main__":
    import os
    
    print("=" * 60)
    print("HealthTwin AI Upload Debug Test")
    print("=" * 60)
    
    # Test health first
    print("\n1. Testing server health...")
    if not test_health_endpoint():
        print("Server health check failed. Exiting.")
        exit(1)
    
    # Test image upload
    print("\n2. Testing image upload...")
    test_upload_with_image()
    
    # Test PDF upload
    print("\n3. Testing PDF upload...")
    test_upload_with_pdf()
    
    print("\n" + "=" * 60)
    print("Debug test completed")
    print("=" * 60)
