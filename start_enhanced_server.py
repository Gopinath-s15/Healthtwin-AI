#!/usr/bin/env python3
"""
Startup script for HealthTwin AI Enhanced OCR Server
Handles import paths and dependency checking
"""
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are available"""
    required_deps = [
        ("cv2", "OpenCV"),
        ("PIL", "Pillow"),
        ("numpy", "NumPy"),
        ("paddleocr", "PaddleOCR"),
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn")
    ]
    
    optional_deps = [
        ("transformers", "Transformers (for handwriting recognition)"),
        ("torch", "PyTorch (for handwriting recognition)"),
        ("easyocr", "EasyOCR (for alternative handwriting recognition)"),
        ("langdetect", "Language Detection"),
        ("googletrans", "Google Translate"),
        ("spacy", "spaCy (for medical NLP)")
    ]
    
    missing_required = []
    missing_optional = []
    
    # Check required dependencies
    for module, name in required_deps:
        try:
            __import__(module)
            logger.info(f"✓ {name} available")
        except ImportError:
            missing_required.append(name)
            logger.error(f"✗ {name} missing (required)")
    
    # Check optional dependencies
    for module, name in optional_deps:
        try:
            __import__(module)
            logger.info(f"✓ {name} available")
        except ImportError:
            missing_optional.append(name)
            logger.warning(f"⚠ {name} missing (optional)")
    
    if missing_required:
        logger.error(f"Missing required dependencies: {', '.join(missing_required)}")
        logger.error("Please install missing dependencies and try again")
        return False
    
    if missing_optional:
        logger.warning(f"Missing optional dependencies: {', '.join(missing_optional)}")
        logger.warning("Some enhanced features may not be available")
    
    return True

def start_server():
    """Start the HealthTwin AI server"""
    try:
        # Add current directory to Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # Check dependencies
        if not check_dependencies():
            logger.error("Dependency check failed")
            return False
        
        # Change to app directory
        app_dir = os.path.join(current_dir, 'app')
        if not os.path.exists(app_dir):
            logger.error(f"App directory not found: {app_dir}")
            return False
        
        os.chdir(app_dir)
        sys.path.insert(0, app_dir)
        
        # Try to import the enhanced main application
        try:
            logger.info("Attempting to start enhanced OCR server...")
            import main
            
            logger.info("Enhanced OCR server starting...")
            logger.info("Features: Handwriting recognition, Multi-language support, Medical context processing")
            
        except Exception as e:
            logger.warning(f"Enhanced server failed to start: {e}")
            logger.info("Falling back to simple server...")
            
            try:
                import simple_main as main
                logger.info("Simple OCR server starting...")
                logger.info("Features: Basic OCR, Medical text extraction")
            except Exception as e2:
                logger.error(f"Simple server also failed: {e2}")
                return False
        
        # Start the server
        logger.info("Server will be available at: http://127.0.0.1:8000")
        logger.info("API documentation at: http://127.0.0.1:8000/docs")
        logger.info("Press Ctrl+C to stop the server")
        
        import uvicorn
        uvicorn.run(main.app, host="127.0.0.1", port=8000, reload=False)
        
        return True
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return True
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return False

def main():
    """Main function"""
    logger.info("HealthTwin AI Enhanced OCR Server")
    logger.info("=" * 50)
    
    success = start_server()
    
    if not success:
        logger.error("Failed to start server")
        logger.info("\nTroubleshooting:")
        logger.info("1. Make sure you're in the correct directory")
        logger.info("2. Install missing dependencies: pip install -r requirements.txt")
        logger.info("3. Try the basic server: cd app && python simple_main.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
