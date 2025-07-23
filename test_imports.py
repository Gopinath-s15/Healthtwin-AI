#!/usr/bin/env python3
"""
Test imports to identify the issue
"""

import sys
import os
sys.path.append('app/ml_pipeline')

print("🧪 TESTING IMPORTS")
print("=" * 40)

# Test 1: Basic imports
try:
    import cv2
    print("✅ OpenCV imported successfully")
except ImportError as e:
    print(f"❌ OpenCV import failed: {e}")

try:
    import numpy as np
    print("✅ NumPy imported successfully")
except ImportError as e:
    print(f"❌ NumPy import failed: {e}")

try:
    import pytesseract
    print("✅ Pytesseract imported successfully")
except ImportError as e:
    print(f"❌ Pytesseract import failed: {e}")

try:
    from rapidfuzz import fuzz, process
    print("✅ RapidFuzz imported successfully")
except ImportError as e:
    print(f"❌ RapidFuzz import failed: {e}")

# Test 2: Medication parser
print(f"\n📦 TESTING MEDICATION PARSER:")
try:
    from handwritten_medication_parser import HandwrittenMedicationParser
    parser = HandwrittenMedicationParser()
    print("✅ HandwrittenMedicationParser imported and initialized successfully")
except ImportError as e:
    print(f"❌ HandwrittenMedicationParser import failed: {e}")
except Exception as e:
    print(f"❌ HandwrittenMedicationParser initialization failed: {e}")

# Test 3: Layout analyzer
print(f"\n📐 TESTING LAYOUT ANALYZER:")
try:
    from prescription_layout_analyzer import PrescriptionLayoutAnalyzer
    analyzer = PrescriptionLayoutAnalyzer()
    print("✅ PrescriptionLayoutAnalyzer imported and initialized successfully")
except ImportError as e:
    print(f"❌ PrescriptionLayoutAnalyzer import failed: {e}")
except Exception as e:
    print(f"❌ PrescriptionLayoutAnalyzer initialization failed: {e}")

# Test 4: Handwriting specialist
print(f"\n✍️ TESTING HANDWRITING SPECIALIST:")
try:
    from handwriting_specialist import HandwritingSpecialist
    specialist = HandwritingSpecialist()
    print("✅ HandwritingSpecialist imported and initialized successfully")
except ImportError as e:
    print(f"❌ HandwritingSpecialist import failed: {e}")
except Exception as e:
    print(f"❌ HandwritingSpecialist initialization failed: {e}")

# Test 5: Handwriting OCR engine
print(f"\n🔍 TESTING HANDWRITING OCR ENGINE:")
try:
    from handwriting_ocr import HandwritingRecognitionEngine
    engine = HandwritingRecognitionEngine()
    print("✅ HandwritingRecognitionEngine imported and initialized successfully")
except ImportError as e:
    print(f"❌ HandwritingRecognitionEngine import failed: {e}")
except Exception as e:
    print(f"❌ HandwritingRecognitionEngine initialization failed: {e}")

print(f"\n🎯 CONCLUSION:")
print(f"   If any component fails to import, that's the root cause")
print(f"   of the handwriting recognition not working in the API.")
