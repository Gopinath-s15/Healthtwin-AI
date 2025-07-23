#!/usr/bin/env python3
"""
Direct test of the handwriting recognition engine
"""

import sys
import os
sys.path.append('app/ml_pipeline')

from handwriting_ocr import HandwritingRecognitionEngine
import cv2

def test_handwriting_engine_direct():
    """Test the handwriting engine directly"""
    print("🧪 TESTING HANDWRITING ENGINE DIRECTLY")
    print("=" * 50)
    
    # Find prescription image
    image_files = [f for f in os.listdir('.') if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not image_files:
        print("❌ No image files found")
        return
    
    test_file = image_files[0]
    print(f"📁 Testing with: {test_file}")
    
    try:
        # Initialize handwriting engine
        print("🔧 Initializing handwriting engine...")
        engine = HandwritingRecognitionEngine()
        print("✅ Handwriting engine initialized successfully")
        
        # Test direct processing
        print(f"\n🖼️ Processing {test_file}...")
        result = engine.process_handwritten_prescription(test_file)
        
        print(f"\n📊 RESULTS:")
        print(f"   Success: {result.get('success')}")
        print(f"   Best confidence: {result.get('best_confidence')}")
        print(f"   Best method: {result.get('best_method')}")
        print(f"   Combined text length: {len(result.get('combined_text', ''))}")
        
        # Check all results
        all_results = result.get('all_results', [])
        print(f"   Total result variants: {len(all_results)}")
        
        total_medications = 0
        for i, res in enumerate(all_results):
            medications = res.get('medications', [])
            instructions = res.get('instructions', [])
            method = res.get('method', 'unknown')
            
            print(f"\n   Variant {i+1} ({method}):")
            print(f"      Medications: {len(medications)}")
            print(f"      Instructions: {len(instructions)}")
            
            if medications:
                for j, med in enumerate(medications):
                    print(f"         {j+1}. {med.get('name', 'Unknown')} (conf: {med.get('confidence', 0):.2f})")
                    if med.get('form'):
                        print(f"            Form: {med['form']}")
                    if med.get('dosage'):
                        print(f"            Dosage: {med['dosage']}")
            
            total_medications += len(medications)
        
        print(f"\n🎯 SUMMARY:")
        print(f"   Total medications found: {total_medications}")
        
        if total_medications > 0:
            print(f"   🎉 SUCCESS! Handwriting recognition found medications!")
        else:
            print(f"   ⚠️ No medications found - need to improve recognition")
            
            # Show some raw text for debugging
            combined_text = result.get('combined_text', '')
            if combined_text:
                print(f"\n📄 Raw text sample (first 200 chars):")
                print(f"   '{combined_text[:200]}...'")
        
        return result
        
    except Exception as e:
        print(f"❌ Handwriting engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_handwriting_specialist_direct():
    """Test the handwriting specialist directly"""
    print(f"\n✍️ TESTING HANDWRITING SPECIALIST DIRECTLY")
    print("=" * 50)
    
    try:
        from handwriting_specialist import HandwritingSpecialist
        
        # Find prescription image
        image_files = [f for f in os.listdir('.') if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not image_files:
            print("❌ No image files found")
            return
        
        test_file = image_files[0]
        print(f"📁 Testing with: {test_file}")
        
        # Load image
        image = cv2.imread(test_file)
        if image is None:
            print(f"❌ Could not load image: {test_file}")
            return
        
        print(f"📐 Image shape: {image.shape}")
        
        # Initialize specialist
        specialist = HandwritingSpecialist()
        print("✅ Handwriting specialist initialized")
        
        # Test extraction
        result = specialist.extract_handwritten_text(image)
        
        print(f"\n📊 SPECIALIST RESULTS:")
        print(f"   Success: {result.get('success')}")
        print(f"   Confidence: {result.get('confidence'):.2f}")
        print(f"   Text length: {len(result.get('text', ''))}")
        print(f"   Medications: {len(result.get('medications', []))}")
        print(f"   Instructions: {len(result.get('instructions', []))}")
        
        # Show medications
        medications = result.get('medications', [])
        if medications:
            print(f"\n💊 MEDICATIONS FOUND:")
            for i, med in enumerate(medications, 1):
                print(f"   {i}. {med.get('name', 'Unknown')}")
                print(f"      Confidence: {med.get('confidence', 0):.2f}")
                print(f"      Category: {med.get('category', 'unknown')}")
                if med.get('form'):
                    print(f"      Form: {med['form']}")
                if med.get('dosage'):
                    print(f"      Dosage: {med['dosage']}")
                print()
        
        # Show some text for debugging
        text = result.get('text', '')
        if text:
            print(f"\n📄 Extracted text sample:")
            print(f"   '{text[:300]}...'")
        
        return result
        
    except Exception as e:
        print(f"❌ Handwriting specialist test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test both approaches
    engine_result = test_handwriting_engine_direct()
    specialist_result = test_handwriting_specialist_direct()
    
    print(f"\n🎯 FINAL COMPARISON:")
    if engine_result and specialist_result:
        engine_meds = len(engine_result.get('all_results', [{}])[0].get('medications', []))
        specialist_meds = len(specialist_result.get('medications', []))
        
        print(f"   Engine medications: {engine_meds}")
        print(f"   Specialist medications: {specialist_meds}")
        
        if specialist_meds > engine_meds:
            print(f"   🏆 Specialist performed better!")
        elif engine_meds > specialist_meds:
            print(f"   🏆 Engine performed better!")
        else:
            print(f"   🤝 Both performed equally")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. If specialist works but engine doesn't, fix engine integration")
    print(f"   2. If both work but API doesn't, fix API integration")
    print(f"   3. If neither works, improve OCR preprocessing")
    print(f"   4. Add more medication patterns to the parser")
