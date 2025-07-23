"""
Setup script for Enhanced OCR System
Installs dependencies and downloads required models
"""
import subprocess
import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(command, description=""):
    """Run a command and handle errors"""
    logger.info(f"Running: {description or command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {command}")
        logger.error(f"Error: {e.stderr}")
        return False

def install_dependencies():
    """Install Python dependencies"""
    logger.info("Installing Python dependencies...")
    
    # Install basic requirements
    if not run_command("pip install -r requirements.txt", "Installing basic requirements"):
        logger.error("Failed to install basic requirements")
        return False
    
    # Install additional dependencies that might not be in requirements.txt
    additional_deps = [
        "torch>=2.0.0",
        "torchvision>=0.15.0", 
        "transformers>=4.35.0",
        "easyocr>=1.7.0",
        "langdetect>=1.0.9",
        "googletrans==4.0.0rc1",
        "albumentations>=1.3.0"
    ]
    
    for dep in additional_deps:
        logger.info(f"Installing {dep}...")
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            logger.warning(f"Failed to install {dep} - continuing anyway")
    
    return True

def download_spacy_models():
    """Download spaCy language models"""
    logger.info("Downloading spaCy models...")
    
    models = ["en_core_web_sm"]
    
    for model in models:
        logger.info(f"Downloading spaCy model: {model}")
        if not run_command(f"python -m spacy download {model}", f"Downloading {model}"):
            logger.warning(f"Failed to download {model} - some features may not work")
    
    return True

def setup_model_cache():
    """Setup model cache directories"""
    logger.info("Setting up model cache directories...")
    
    cache_dirs = [
        Path.home() / ".cache" / "huggingface" / "transformers",
        Path.home() / ".cache" / "torch" / "hub",
        Path.home() / ".paddleocr"
    ]
    
    for cache_dir in cache_dirs:
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created cache directory: {cache_dir}")
        except Exception as e:
            logger.warning(f"Failed to create cache directory {cache_dir}: {e}")
    
    return True

def test_imports():
    """Test if all required modules can be imported"""
    logger.info("Testing module imports...")
    
    test_modules = [
        ("cv2", "OpenCV"),
        ("PIL", "Pillow"),
        ("numpy", "NumPy"),
        ("paddleocr", "PaddleOCR"),
        ("transformers", "Transformers"),
        ("torch", "PyTorch"),
        ("easyocr", "EasyOCR"),
        ("spacy", "spaCy"),
        ("langdetect", "Language Detection"),
        ("googletrans", "Google Translate")
    ]
    
    failed_imports = []
    
    for module_name, display_name in test_modules:
        try:
            __import__(module_name)
            logger.info(f"✓ {display_name} imported successfully")
        except ImportError as e:
            logger.error(f"✗ Failed to import {display_name}: {e}")
            failed_imports.append(display_name)
    
    if failed_imports:
        logger.error(f"Failed to import: {', '.join(failed_imports)}")
        logger.error("Some features may not work properly")
        return False
    else:
        logger.info("All modules imported successfully!")
        return True

def download_models():
    """Download required ML models"""
    logger.info("Downloading required ML models...")
    
    try:
        # Test TrOCR model download
        logger.info("Testing TrOCR model download...")
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel
        
        model_name = "microsoft/trocr-base-handwritten"
        logger.info(f"Downloading {model_name}...")
        
        processor = TrOCRProcessor.from_pretrained(model_name)
        model = VisionEncoderDecoderModel.from_pretrained(model_name)
        
        logger.info("TrOCR model downloaded successfully")
        
    except Exception as e:
        logger.error(f"Failed to download TrOCR model: {e}")
        logger.warning("Handwriting recognition may not work")
    
    try:
        # Test PaddleOCR initialization
        logger.info("Testing PaddleOCR initialization...")
        import paddleocr
        
        # Initialize with English (updated parameters)
        ocr = paddleocr.PaddleOCR(use_angle_cls=True, lang='en')
        logger.info("PaddleOCR English model loaded successfully")

        # Test with Hindi
        ocr_hi = paddleocr.PaddleOCR(use_angle_cls=True, lang='hi')
        logger.info("PaddleOCR Hindi model loaded successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize PaddleOCR: {e}")
        logger.warning("Multi-language OCR may not work")
    
    try:
        # Test EasyOCR initialization
        logger.info("Testing EasyOCR initialization...")
        import easyocr
        
        reader = easyocr.Reader(['en'], gpu=False)
        logger.info("EasyOCR initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize EasyOCR: {e}")
        logger.warning("Alternative OCR engine may not work")

def create_test_environment():
    """Create test environment and files"""
    logger.info("Creating test environment...")
    
    # Create test directories
    test_dirs = ["test_images", "test_results", "logs"]
    
    for test_dir in test_dirs:
        try:
            Path(test_dir).mkdir(exist_ok=True)
            logger.info(f"Created directory: {test_dir}")
        except Exception as e:
            logger.warning(f"Failed to create directory {test_dir}: {e}")
    
    # Create a simple test configuration
    config = {
        "ocr_settings": {
            "confidence_threshold": 0.6,
            "processing_timeout": 30,
            "max_file_size_mb": 10
        },
        "model_settings": {
            "trocr_model": "microsoft/trocr-base-handwritten",
            "paddleocr_languages": ["en", "hi", "ta", "te", "kn", "ml"],
            "easyocr_languages": ["en", "hi", "ta", "te", "kn", "ml"]
        }
    }
    
    try:
        import json
        with open("enhanced_ocr_config.json", "w") as f:
            json.dump(config, f, indent=2)
        logger.info("Created configuration file: enhanced_ocr_config.json")
    except Exception as e:
        logger.warning(f"Failed to create configuration file: {e}")

def main():
    """Main setup function"""
    logger.info("Enhanced OCR Setup Script")
    logger.info("=" * 50)
    
    steps = [
        ("Installing dependencies", install_dependencies),
        ("Downloading spaCy models", download_spacy_models),
        ("Setting up model cache", setup_model_cache),
        ("Testing imports", test_imports),
        ("Downloading ML models", download_models),
        ("Creating test environment", create_test_environment)
    ]
    
    failed_steps = []
    
    for step_name, step_function in steps:
        logger.info(f"\n--- {step_name} ---")
        try:
            if not step_function():
                failed_steps.append(step_name)
        except Exception as e:
            logger.error(f"Step '{step_name}' failed with error: {e}")
            failed_steps.append(step_name)
    
    logger.info("\n" + "=" * 50)
    logger.info("Setup Summary")
    logger.info("=" * 50)
    
    if failed_steps:
        logger.warning(f"Setup completed with {len(failed_steps)} failed steps:")
        for step in failed_steps:
            logger.warning(f"  - {step}")
        logger.warning("Some features may not work properly")
    else:
        logger.info("Setup completed successfully!")
        logger.info("All features should be available")
    
    logger.info("\nNext steps:")
    logger.info("1. Start the backend server: python app/main.py")
    logger.info("2. Test the enhanced OCR: python scripts/test_enhanced_ocr.py")
    logger.info("3. Check API documentation at: http://127.0.0.1:8000/docs")

if __name__ == "__main__":
    main()
