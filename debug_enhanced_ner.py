#!/usr/bin/env python3
"""
Debug script for Enhanced Medical NER
"""

import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_enhanced_ner():
    """Debug the enhanced medical NER system step by step"""
    print("🔍 DEBUGGING ENHANCED MEDICAL NER")
    print("=" * 60)
    
    try:
        from app.ml_pipeline.enhanced_medical_ner import EnhancedMedicalNER
        
        # Initialize enhanced NER
        print("1. Initializing Enhanced Medical NER...")
        ner = EnhancedMedicalNER()
        print("✅ Enhanced NER initialized successfully")
        
        # Test text
        test_text = "Dr. Smith Clinic. Patient: John Doe. Rx: 1. Paracetamol 650mg BD x 5 days 2. Amoxicillin 500mg TID x 7 days 3. Omeprazole 20mg OD before meals x 14 days. Follow up after 1 week."
        
        print(f"\n2. Testing basic entity extraction...")
        print(f"Input text: {test_text[:100]}...")
        
        # Test basic entity extraction
        try:
            entities = ner.extract_medical_entities(test_text)
            print(f"✅ Basic entity extraction successful")
            print(f"   Entities type: {type(entities)}")
            print(f"   Entities keys: {entities.keys() if isinstance(entities, dict) else 'Not a dict'}")
            
            for entity_type, entity_list in entities.items():
                if entity_type != 'confidence_scores' and entity_list:
                    print(f"   {entity_type}: {len(entity_list)} found")
                    if entity_list:
                        first_entity = entity_list[0]
                        print(f"     First entity type: {type(first_entity)}")
                        print(f"     First entity: {first_entity}")
        
        except Exception as e:
            print(f"❌ Basic entity extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print(f"\n3. Testing structured prescription data extraction...")
        
        # Test structured data extraction
        try:
            structured_data = ner.extract_structured_prescription_data(test_text)
            print(f"✅ Structured data extraction successful")
            print(f"   Structured data type: {type(structured_data)}")
            print(f"   Structured data keys: {structured_data.keys() if isinstance(structured_data, dict) else 'Not a dict'}")
            
            medications = structured_data.get('medications', [])
            print(f"   Medications: {len(medications)} found")
            if medications:
                first_med = medications[0]
                print(f"     First medication type: {type(first_med)}")
                print(f"     First medication: {first_med}")
        
        except Exception as e:
            print(f"❌ Structured data extraction failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print(f"\n4. Testing medical context processor integration...")
        
        try:
            from app.ml_pipeline.medical_context_processor import MedicalContextProcessor
            
            processor = MedicalContextProcessor()
            print(f"✅ Medical context processor initialized")
            print(f"   Enhanced NER available: {processor.enhanced_ner is not None}")
            
            # Test OCR results format
            sample_ocr_results = {
                'success': True,
                'raw_extracted_text': test_text,
                'confidence_score': 0.85,
                'multilingual_info': {},
                'handwriting_info': {}
            }
            
            print(f"   Testing with sample OCR results...")
            result = processor.process_prescription_context(sample_ocr_results)
            
            print(f"✅ Medical context processing successful")
            print(f"   Result type: {type(result)}")
            print(f"   Result success: {result.get('success', False)}")
            
            if result.get('success', False):
                structured_prescription = result.get('structured_prescription', {})
                print(f"   Structured prescription keys: {structured_prescription.keys()}")
                
                medicines = structured_prescription.get('medicines', [])
                print(f"   Medicines found: {len(medicines)}")
                
                return True
            else:
                print(f"❌ Medical context processing returned failure: {result.get('error', 'Unknown error')}")
                return False
        
        except Exception as e:
            print(f"❌ Medical context processor integration failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_enhanced_ner()
    print(f"\n🎯 Debug Result: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
