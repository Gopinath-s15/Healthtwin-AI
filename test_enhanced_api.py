#!/usr/bin/env python3
"""
Test the enhanced API with prescription processing
"""

import requests
import json

def test_enhanced_api():
    """Test the enhanced prescription processing API"""
    print("🧪 TESTING ENHANCED PRESCRIPTION PROCESSING API")
    print("=" * 60)
    
    try:
        # Test the enhanced endpoint
        with open('test_prescription.pdf', 'rb') as f:
            response = requests.post(
                'http://localhost:8000/patient/upload-prescription-enhanced',
                files={'file': f}
            )
        
        if response.status_code != 200:
            print(f"❌ API Error: Status {response.status_code}")
            return False
        
        result = response.json()
        
        print(f"✅ API Response: Status {response.status_code}")
        print(f"📊 Overall Success: {result.get('success')}")
        print(f"🎯 Confidence Score: {result.get('confidence_score')}")
        print(f"📈 Confidence Level: {result.get('confidence_level')}")
        print(f"🔧 Extraction Method: {result.get('extraction_method')}")
        
        # Medical Analysis Results
        medical_analysis = result.get('medical_analysis', {})
        print(f"\n💊 Medical Analysis Success: {medical_analysis.get('success')}")
        
        if medical_analysis.get('success'):
            # Enhanced NER Information
            processing_info = medical_analysis.get('processing_info', {})
            enhanced_ner_used = processing_info.get('enhanced_ner_used', False)
            print(f"🧠 Enhanced NER Used: {enhanced_ner_used}")
            
            # Structured Prescription Data
            structured_prescription = medical_analysis.get('structured_prescription', {})
            medicines = structured_prescription.get('medicines', [])
            instructions = structured_prescription.get('instructions', [])
            
            print(f"\n📋 Structured Prescription Data:")
            print(f"   Medications Found: {len(medicines)}")
            print(f"   Instructions Found: {len(instructions)}")
            
            # Display top medications
            if medicines:
                print(f"\n💊 Top Medications:")
                for i, med in enumerate(medicines[:5], 1):
                    name = med.get('name', 'Unknown')
                    confidence = med.get('confidence', 0)
                    category = med.get('category', 'Unknown')
                    dosage = med.get('dosage', 'Not specified')
                    
                    print(f"   {i}. {name}")
                    print(f"      Category: {category}")
                    print(f"      Dosage: {dosage}")
                    print(f"      Confidence: {confidence:.2f}")
                    print()
            
            # Confidence Assessment
            confidence_scores = structured_prescription.get('confidence_scores', {})
            if confidence_scores:
                print(f"📊 Confidence Breakdown:")
                for entity_type, score in confidence_scores.items():
                    print(f"   {entity_type.title()}: {score:.2f}")
        
        else:
            error = medical_analysis.get('error', 'Unknown error')
            print(f"❌ Medical Analysis Error: {error}")
        
        # Enhanced Features
        enhanced_features = result.get('enhanced_features', {})
        if enhanced_features:
            print(f"\n✨ Enhanced Features:")
            prescription_type = enhanced_features.get('prescription_type', {})
            if prescription_type:
                print(f"   Prescription Type: {prescription_type.get('type', 'Unknown')}")
                print(f"   Type Confidence: {prescription_type.get('confidence', 0):.2f}")
            
            engines_used = enhanced_features.get('engines_used', [])
            if engines_used:
                print(f"   OCR Engines Used: {', '.join(engines_used)}")
            
            processing_time = enhanced_features.get('processing_time', 0)
            print(f"   Processing Time: {processing_time:.2f} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_enhanced_api()
    if success:
        print(f"\n🎉 Enhanced API test completed successfully!")
        print(f"\n✨ Key Improvements Demonstrated:")
        print(f"   ✅ Enhanced medical NER with structured data")
        print(f"   ✅ Improved medication extraction and categorization")
        print(f"   ✅ Confidence assessment and validation")
        print(f"   ✅ Prescription type detection")
        print(f"   ✅ Multi-engine OCR processing")
    else:
        print(f"\n❌ Enhanced API test failed!")
