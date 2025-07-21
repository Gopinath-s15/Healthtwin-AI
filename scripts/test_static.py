#!/usr/bin/env python3
"""
Test static file serving
"""
import requests

BASE_URL = "http://localhost:8000"

def test_static_file():
    """Test static file serving"""
    try:
        # Use the filename from the previous upload test
        filename = "c1c5fead-1a02-4152-93c0-987bb24a1b14.png"
        response = requests.get(f"{BASE_URL}/uploads/{filename}", timeout=5)
        
        print(f"Static file status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Content-Length: {len(response.content)} bytes")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Static file test error: {e}")
        return False

if __name__ == "__main__":
    print("Testing static file serving...")
    print("=" * 50)
    
    success = test_static_file()
    
    print("=" * 50)
    if success:
        print("🎉 Static file test passed!")
    else:
        print("❌ Static file test failed!")
