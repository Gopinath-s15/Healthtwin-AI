#!/usr/bin/env python3
"""
Basic setup test
"""

def test_imports():
    """Test basic imports"""
    try:
        print("Testing cv2...")
        import cv2
        print("✅ cv2 imported")
        
        print("Testing PIL...")
        from PIL import Image
        print("✅ PIL imported")
        
        print("Testing numpy...")
        import numpy as np
        print("✅ numpy imported")
        
        print("Testing dataset manager...")
        from app.ml_pipeline.dataset_manager import DatasetManager
        dm = DatasetManager()
        print("✅ DatasetManager imported")
        
        print("Testing handwriting specialist...")
        from app.ml_pipeline.handwriting_specialist import HandwritingSpecialist
        hs = HandwritingSpecialist()
        print("✅ HandwritingSpecialist imported")
        
        print("\n🎉 All basic imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_imports()