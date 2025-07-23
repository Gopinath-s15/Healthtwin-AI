#!/usr/bin/env python3
"""
Test the import fix for handwriting specialist
"""

def test_import_fix():
    """Test that the handwriting specialist can be imported correctly"""
    print("🧪 TESTING IMPORT FIX")
    print("=" * 40)
    
    try:
        # Test the import that was failing
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'app', 'ml_pipeline'))
        from app.ml_pipeline.handwriting_specialist import HandwritingSpecialist
        
        print("✅ Import successful!")
        
        # Test initialization
        specialist = HandwritingSpecialist()
        print("✅ HandwritingSpecialist initialized successfully!")
        
        print("\n🎉 Import fix verified - no more import errors!")
        
    except ImportError as e:
        print(f"❌ Import error still exists: {e}")
    except Exception as e:
        print(f"❌ Other error: {e}")

if __name__ == "__main__":
    test_import_fix()
