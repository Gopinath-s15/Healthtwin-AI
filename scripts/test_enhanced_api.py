#!/usr/bin/env python3
"""
Test script for Enhanced HealthTwin API with Authentication
"""
import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_patient_registration_with_auth():
    """Test patient registration with authentication"""
    print("Testing patient registration with authentication...")
    try:
        # Use a unique phone number with timestamp
        import time
        unique_phone = f"555{int(time.time()) % 10000:04d}"
        data = {
            "phone": unique_phone,
            "name": "Test Patient Auth",
            "password": "securepassword123"
        }
        response = requests.post(f"{BASE_URL}/auth/patient/register", json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_patient_login(patient_id, password):
    """Test patient login"""
    print(f"\nTesting patient login for {patient_id}...")
    try:
        data = {
            "patient_id": patient_id,
            "password": password
        }
        response = requests.post(f"{BASE_URL}/auth/patient/login", json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_doctor_registration():
    """Test doctor registration"""
    print("\nTesting doctor registration...")
    try:
        import time
        unique_id = f"DR{int(time.time()) % 10000:04d}"
        unique_license = f"LIC{int(time.time()) % 100000:05d}"
        data = {
            "doctor_id": unique_id,
            "name": "Dr. John Smith",
            "specialization": "Cardiology",
            "license_number": unique_license,
            "password": "doctorpassword123"
        }
        response = requests.post(f"{BASE_URL}/auth/doctor/register", json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_doctor_login(doctor_id, password):
    """Test doctor login"""
    print(f"\nTesting doctor login for {doctor_id}...")
    try:
        data = {
            "doctor_id": doctor_id,
            "password": password
        }
        response = requests.post(f"{BASE_URL}/auth/doctor/login", json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_authenticated_patient_profile(token):
    """Test getting patient profile with authentication"""
    print("\nTesting authenticated patient profile...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/patient/profile", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_authenticated_patient_timeline(token):
    """Test getting patient timeline with authentication"""
    print("\nTesting authenticated patient timeline...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/patient/timeline", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_doctor_patient_search(token):
    """Test doctor patient search"""
    print("\nTesting doctor patient search...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/doctor/patients", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_enhanced_health_check():
    """Test enhanced health check"""
    print("\nTesting enhanced health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("Testing Enhanced HealthTwin API with Authentication")
    print("=" * 60)
    
    results = {}
    
    # Test enhanced health check
    results["health_check"] = test_enhanced_health_check()
    
    # Test patient registration with auth
    patient_auth = test_patient_registration_with_auth()
    results["patient_registration"] = patient_auth is not None
    
    patient_token = None
    if patient_auth:
        # Test patient login
        patient_token = test_patient_login(patient_auth["user_id"], "securepassword123")
        results["patient_login"] = patient_token is not None
        
        if patient_token:
            # Test authenticated patient endpoints
            results["patient_profile"] = test_authenticated_patient_profile(patient_token)
            results["patient_timeline"] = test_authenticated_patient_timeline(patient_token)
    
    # Test doctor registration
    doctor_auth = test_doctor_registration()
    results["doctor_registration"] = doctor_auth is not None
    
    doctor_token = None
    if doctor_auth:
        # Test doctor login
        doctor_token = test_doctor_login(doctor_auth["user_id"], "doctorpassword123")
        results["doctor_login"] = doctor_token is not None
        
        if doctor_token:
            # Test doctor endpoints
            results["doctor_patient_search"] = test_doctor_patient_search(doctor_token)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary:")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{test_name:25} {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All enhanced authentication tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
