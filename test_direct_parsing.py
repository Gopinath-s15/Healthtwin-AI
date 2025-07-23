#!/usr/bin/env python3
"""
Direct test of the handwritten medication parser
"""

import sys
import os
sys.path.append('app/ml_pipeline')

from handwritten_medication_parser import HandwrittenMedicationParser
import cv2
import pytesseract

def test_direct_parsing():
    """Test the medication parser directly"""
    print("🧪 TESTING HANDWRITTEN MEDICATION PARSER DIRECTLY")
    print("=" * 60)
    
    # Sample text from the prescription (based on our OCR analysis)
    sample_texts = [
        "Milly Ane plo. Ply",
        "Guh Bp 57 gel ec fA",
        "Dextt 16 i",
        "Bue © ae",
        "Dr. Arun Kumar Jacob",
        "Consultant Dermatologist & Aesthetic Physician",
        "Skin Disease Acne Dandruff Hair Fall",
        "Milly Ane gel rf",
        "Clotrimazole cream 1%",
        "Betamethasone gel 0.1%"
    ]
    
    # Initialize parser
    parser = HandwrittenMedicationParser()
    
    print("📝 Testing with sample texts:")
    print("-" * 40)
    
    all_medications = []
    
    for i, text in enumerate(sample_texts, 1):
        print(f"\n{i}. Testing: '{text}'")
        medications = parser.parse_handwritten_medications(text)
        
        if medications:
            print(f"   ✅ Found {len(medications)} medication(s):")
            for med in medications:
                print(f"      - {med.get('name', 'Unknown')} ({med.get('category', 'unknown')})")
                if med.get('form'):
                    print(f"        Form: {med['form']}")
                if med.get('dosage'):
                    print(f"        Dosage: {med['dosage']}")
                all_medications.append(med)
        else:
            print(f"   ❌ No medications found")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total medications found: {len(all_medications)}")
    
    if all_medications:
        print(f"\n💊 ALL MEDICATIONS:")
        for i, med in enumerate(all_medications, 1):
            print(f"   {i}. {med.get('name', 'Unknown')}")
            print(f"      Category: {med.get('category', 'unknown')}")
            print(f"      Form: {med.get('form', 'not specified')}")
            print(f"      Dosage: {med.get('dosage', 'not specified')}")
            print(f"      Confidence: {med.get('confidence', 0):.2f}")
            print()

def test_with_actual_image():
    """Test with the actual prescription image"""
    print("\n🖼️ TESTING WITH ACTUAL PRESCRIPTION IMAGE")
    print("=" * 50)
    
    # Find the prescription image
    image_files = [f for f in os.listdir('.') if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not image_files:
        print("❌ No image files found")
        return
    
    test_file = image_files[0]
    print(f"📁 Using: {test_file}")
    
    try:
        # Load image and extract text
        image = cv2.imread(test_file)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Extract text using different methods
        configs = [
            ('Basic OCR', '--psm 6 --oem 3'),
            ('Line OCR', '--psm 7 --oem 3'),
            ('Word OCR', '--psm 8 --oem 3'),
        ]
        
        parser = HandwrittenMedicationParser()
        
        for name, config in configs:
            print(f"\n🔍 {name}:")
            try:
                text = pytesseract.image_to_string(gray, config=config)
                medications = parser.parse_handwritten_medications(text)
                
                print(f"   Text length: {len(text)} characters")
                print(f"   Medications found: {len(medications)}")
                
                for med in medications:
                    print(f"      - {med.get('name', 'Unknown')} ({med.get('confidence', 0):.2f})")
                    
            except Exception as e:
                print(f"   ❌ Failed: {e}")
        
        # Test with prescription area only
        print(f"\n📐 TESTING PRESCRIPTION AREA ONLY:")
        height, width = gray.shape
        prescription_area = gray[height//2:3*height//4, :]  # Middle 25%
        
        try:
            area_text = pytesseract.image_to_string(prescription_area, config='--psm 6 --oem 3')
            print(f"   Prescription area text:")
            print(f"   '{area_text[:200]}...'")
            
            area_medications = parser.parse_handwritten_medications(area_text)
            print(f"   Medications in prescription area: {len(area_medications)}")
            
            for med in area_medications:
                print(f"      - {med.get('name', 'Unknown')} ({med.get('category', 'unknown')})")
                
        except Exception as e:
            print(f"   ❌ Area parsing failed: {e}")
            
    except Exception as e:
        print(f"❌ Image processing failed: {e}")

def test_medication_database():
    """Test the medication database matching"""
    print("\n🗃️ TESTING MEDICATION DATABASE")
    print("=" * 40)
    
    parser = HandwrittenMedicationParser()
    
    # Test words that should match medications
    test_words = [
        'milly',  # Should match mupirocin
        'dext',   # Should match betamethasone
        'guh',    # Might not match anything
        'clot',   # Should match clotrimazole
        'beta',   # Should match betamethasone
        'azee',   # Should match azithromycin
    ]
    
    print("🔍 Testing medication name matching:")
    for word in test_words:
        match = parser._find_medication_match(word)
        if match:
            med_name, med_info = match
            print(f"   '{word}' → {med_name} ({med_info.get('category', 'unknown')})")
        else:
            print(f"   '{word}' → No match")

if __name__ == "__main__":
    test_direct_parsing()
    test_with_actual_image()
    test_medication_database()
    
    print(f"\n🎯 CONCLUSION:")
    print(f"   If medications are found here but not in the API,")
    print(f"   the issue is in the integration, not the parser.")
