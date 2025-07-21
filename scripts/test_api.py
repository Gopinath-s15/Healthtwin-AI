#!/usr/bin/env python3
"""
Test script for HealthTwin API
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_root_endpoint():
    """Test the root endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"Root endpoint status: {response.status_code}")
        print(f"Root endpoint response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Root endpoint error: {e}")
        return False

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Health endpoint status: {response.status_code}")
        print(f"Health endpoint response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health endpoint error: {e}")
        return False

def test_register_patient():
    """Test patient registration"""
    try:
        data = {
            "phone": "1234567890",
            "name": "Test Patient"
        }
        response = requests.post(f"{BASE_URL}/register", json=data, timeout=5)
        print(f"Register endpoint status: {response.status_code}")
        print(f"Register endpoint response: {response.json()}")
        
        if response.status_code == 200:
            return response.json().get("healthtwin_id")
        return None
    except Exception as e:
        print(f"Register endpoint error: {e}")
        return None

def test_timeline_endpoint(patient_id):
    """Test timeline endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/timeline/{patient_id}", timeout=5)
        print(f"Timeline endpoint status: {response.status_code}")
        print(f"Timeline endpoint response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Timeline endpoint error: {e}")
        return False

def main():
    print("Testing HealthTwin API...")
    print("=" * 50)
    
    # Test basic endpoints
    root_ok = test_root_endpoint()
    print()
    
    health_ok = test_health_endpoint()
    print()
    
    # Test registration
    patient_id = test_register_patient()
    print()
    
    # Test timeline if registration worked
    if patient_id:
        timeline_ok = test_timeline_endpoint(patient_id)
        print()
    else:
        timeline_ok = False
    
    # Summary
    print("=" * 50)
    print("Test Results:")
    print(f"Root endpoint: {'✓' if root_ok else '✗'}")
    print(f"Health endpoint: {'✓' if health_ok else '✗'}")
    print(f"Register endpoint: {'✓' if patient_id else '✗'}")
    print(f"Timeline endpoint: {'✓' if timeline_ok else '✗'}")
    
    if all([root_ok, health_ok, patient_id, timeline_ok]):
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
