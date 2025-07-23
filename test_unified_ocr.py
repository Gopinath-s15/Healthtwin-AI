#!/usr/bin/env python3
"""
Test the unified OCR pipeline directly
"""

import sys
import os
sys.path.append('app/ml_pipeline')

from unified_ocr_pipeline import UnifiedOCRPipeline
import cv2

def test_unified_ocr():
    """Test the unified OCR pipeline directly"""
    print("🧪 TESTING UNIFIED OCR PIPELINE")
    print("=" * 50)
    
    # Initialize the pipeline
    try:
        pipeline = UnifiedOCRPipeline()
        print("✅ UnifiedOCRPipeline initialized successfully")
        
        # Check available engines
        print(f"\n🔧 Available engines:")
        engines = {
            'printed_text': pipeline.printed_text_engine,
            'multilingual': pipeline.multilingual_engine,
            'handwriting': pipeline.handwriting_engine
        }

        for engine_name, engine in engines.items():
            if engine:
                print(f"   ✅ {engine_name}: Available")
            else:
                print(f"   ❌ {engine_name}: Not available")
        
        # Check processing modes
        print(f"\n📋 Processing modes:")
        for mode, engines in pipeline.processing_modes.items():
            print(f"   {mode}: {engines}")
        
        # Test with an image
        image_files = [f for f in os.listdir('.') if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if image_files:
            test_file = image_files[0]
            print(f"\n🖼️ Testing with: {test_file}")
            
            # Test standard mode (should include handwriting now)
            result = pipeline.process_prescription_comprehensive(test_file, mode='standard')
            
            print(f"\n📊 RESULTS:")
            print(f"   Success: {result.get('success')}")
            print(f"   Confidence: {result.get('confidence_score')}")
            print(f"   Method: {result.get('extraction_method')}")
            
            # Check if handwriting was used
            processing_info = result.get('processing_info', {})
            engines_used = processing_info.get('engines_used', [])
            print(f"   Engines used: {engines_used}")
            
            if 'handwriting' in engines_used:
                print(f"   ✅ Handwriting engine was used!")
            else:
                print(f"   ❌ Handwriting engine was NOT used")
            
            # Check handwriting results specifically
            handwriting_results = processing_info.get('handwriting_results', {})
            if handwriting_results:
                print(f"\n✍️ HANDWRITING RESULTS:")
                print(f"   Success: {handwriting_results.get('success')}")
                print(f"   Confidence: {handwriting_results.get('best_confidence')}")
                print(f"   Method: {handwriting_results.get('best_method')}")
                
                # Check for medications in handwriting results
                all_results = handwriting_results.get('all_results', [])
                total_medications = 0
                for result in all_results:
                    medications = result.get('medications', [])
                    total_medications += len(medications)
                
                print(f"   Total medications from handwriting: {total_medications}")
                
                if total_medications > 0:
                    print(f"   🎉 Handwriting recognition found medications!")
                else:
                    print(f"   ⚠️ Handwriting recognition didn't find medications")
        else:
            print(f"\n❌ No image files found for testing")
            
    except Exception as e:
        print(f"❌ Failed to initialize UnifiedOCRPipeline: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_unified_ocr()
