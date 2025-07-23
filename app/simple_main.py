"""
Simplified main application that works with basic dependencies only
Falls back gracefully when enhanced OCR dependencies are not available
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import enhanced services, fall back to basic if not available
try:
    from services.ocr_service import EnhancedPrescriptionOCR
    ENHANCED_OCR_AVAILABLE = True
    logger.info("Enhanced OCR service available")
except ImportError as e:
    logger.warning(f"Enhanced OCR not available: {e}")
    ENHANCED_OCR_AVAILABLE = False

# Try to import the unified pipeline for advanced features
UNIFIED_PIPELINE_AVAILABLE = False
unified_ocr_pipeline = None

try:
    from ml_pipeline.unified_ocr_pipeline import UnifiedOCRPipeline
    from ml_pipeline.medical_context_processor import MedicalContextProcessor

    # Try to initialize
    unified_ocr_pipeline = UnifiedOCRPipeline()
    medical_processor = MedicalContextProcessor()
    UNIFIED_PIPELINE_AVAILABLE = True
    logger.info("Unified OCR pipeline available - Enhanced features enabled!")

except Exception as e:
    logger.warning(f"Unified OCR pipeline not available: {e}")
    logger.info("Enhanced features will be limited to basic OCR improvements")
    unified_ocr_pipeline = None
    medical_processor = None
    # Create a basic OCR fallback
    import pytesseract
    from PIL import Image
    
    class BasicOCR:
        def process_prescription(self, image_path: str) -> Dict[str, Any]:
            try:
                image = Image.open(image_path)
                text = pytesseract.image_to_string(image, lang='eng')
                return {
                    "success": True,
                    "confidence": 0.7,
                    "confidence_level": "Medium",
                    "extraction_method": "Basic Tesseract",
                    "requires_review": True,
                    "safety_flags": [],
                    "raw_extracted_text": text,
                    "doctor_name": "Not extracted",
                    "patient_name": "Not extracted",
                    "clinic_name": "Not extracted",
                    "medications": "Not extracted",
                    "diagnosis": "Not extracted",
                    "prescription_date": "Not extracted",
                    "instructions": "Not extracted",
                    "patient_details": "Not extracted",
                    "follow_up": "Not extracted"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "confidence": 0.0,
                    "confidence_level": "Failed"
                }

app = FastAPI(
    title="HealthTwin AI - Basic",
    description="AI-powered prescription processing (Basic Mode)",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OCR service
if ENHANCED_OCR_AVAILABLE:
    ocr_service = EnhancedPrescriptionOCR()
else:
    ocr_service = BasicOCR()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HealthTwin AI - Basic Prescription Processing API",
        "version": "1.0.0",
        "mode": "Enhanced" if ENHANCED_OCR_AVAILABLE else "Basic",
        "features": ["OCR", "Medical text extraction"] if ENHANCED_OCR_AVAILABLE else ["Basic OCR"]
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "HealthTwin AI Enhanced",
        "ocr_available": True,
        "enhanced_basic_ocr": ENHANCED_OCR_AVAILABLE,
        "unified_pipeline": UNIFIED_PIPELINE_AVAILABLE,
        "mode": "Full Enhanced" if UNIFIED_PIPELINE_AVAILABLE else ("Enhanced Basic" if ENHANCED_OCR_AVAILABLE else "Basic"),
        "available_endpoints": {
            "/patient/upload-prescription": "Basic OCR processing",
            "/patient/upload-prescription-enhanced": "Enhanced processing (with fallback)"
        },
        "features": {
            "basic_ocr": True,
            "enhanced_tesseract": ENHANCED_OCR_AVAILABLE,
            "handwriting_recognition": UNIFIED_PIPELINE_AVAILABLE,
            "multilingual_support": UNIFIED_PIPELINE_AVAILABLE,
            "medical_context_processing": UNIFIED_PIPELINE_AVAILABLE
        }
    }

@app.post("/patient/upload-prescription")
async def upload_prescription(file: UploadFile = File(...)):
    """
    Basic prescription processing
    """
    try:
        # Validate file
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Save temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        logger.info(f"Processing prescription: {file.filename}")
        
        # OCR processing
        ocr_results = ocr_service.process_prescription(temp_file_path)
        
        # Cleanup
        os.unlink(temp_file_path)
        
        # Determine response based on confidence
        confidence_score = ocr_results.get("confidence", 0.0)
        success = ocr_results.get("success", False)
        
        if confidence_score < 0.4:
            status_message = "Low confidence extraction. Manual review required."
        elif confidence_score < 0.7:
            status_message = "Medium confidence extraction. Please verify results."
        else:
            status_message = "Extraction completed successfully."
        
        response_data = {
            "success": success,
            "message": status_message,
            "filename": file.filename,
            "confidence_score": confidence_score,
            "confidence_level": ocr_results.get("confidence_level", "Unknown"),
            "extraction_method": ocr_results.get("extraction_method", "Basic OCR"),
            "requires_review": ocr_results.get("requires_review", True),
            "enhanced_features_available": ENHANCED_OCR_AVAILABLE,
            "prescription_data": {
                "doctor_name": ocr_results.get("doctor_name", "Not found"),
                "patient_name": ocr_results.get("patient_name", "Not found"),
                "clinic_name": ocr_results.get("clinic_name", "Not found"),
                "medications": ocr_results.get("medications", "Not extracted"),
                "diagnosis": ocr_results.get("diagnosis", "Not found"),
                "prescription_date": ocr_results.get("prescription_date", "Not found"),
                "instructions": ocr_results.get("instructions", "Follow doctor's advice"),
                "patient_details": ocr_results.get("patient_details", "Not found"),
                "follow_up": ocr_results.get("follow_up", "As advised")
            },
            "raw_text": ocr_results.get("raw_extracted_text", "")
        }
        
        if not ENHANCED_OCR_AVAILABLE:
            response_data["note"] = "Running in basic mode. Install enhanced dependencies for handwriting recognition and multi-language support."
        
        logger.info(f"OCR completed: {confidence_score:.3f} confidence")
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Processing error: {str(e)}",
                "confidence_score": 0.0,
                "confidence_level": "Failed",
                "requires_review": True,
                "prescription_data": {
                    "doctor_name": "Processing failed",
                    "patient_name": "Processing failed",
                    "clinic_name": "Processing failed",
                    "medications": "Processing failed",
                    "diagnosis": "Processing failed",
                    "prescription_date": "Processing failed",
                    "instructions": "Processing failed",
                    "patient_details": "Processing failed",
                    "follow_up": "Processing failed"
                }
            }
        )

@app.get("/patient/timeline")
async def get_patient_timeline():
    """
    Get patient medical timeline (demo version)
    """
    timeline_data = [
        {
            "id": 1,
            "date": "2024-01-15",
            "type": "prescription",
            "doctor": "Dr. Rajesh Kumar",
            "medications": ["Paracetamol 500mg", "Azithromycin 250mg"],
            "diagnosis": "Viral fever",
            "notes": "Take rest, drink plenty of fluids"
        },
        {
            "id": 2,
            "date": "2024-01-10",
            "type": "checkup",
            "doctor": "Dr. Priya Sharma",
            "medications": [],
            "diagnosis": "Routine checkup",
            "notes": "All vitals normal"
        }
    ]
    
    return {
        "success": True,
        "timeline": timeline_data,
        "total_entries": len(timeline_data)
    }

# Additional endpoints for compatibility
@app.post("/register")
async def register_patient():
    """Demo registration endpoint"""
    return {
        "healthtwin_id": "demo-patient-123",
        "message": "Demo registration for testing"
    }

@app.post("/patient/upload-prescription-enhanced")
async def upload_prescription_enhanced(
    file: UploadFile = File(...),
    processing_mode: str = "standard"
):
    """
    Enhanced prescription processing (if available)
    """
    if not UNIFIED_PIPELINE_AVAILABLE:
        # Fallback to enhanced basic processing
        logger.info("Using enhanced basic processing (unified pipeline not available)")

        try:
            # Validate file
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="Invalid file type")

            file_content = await file.read()
            if len(file_content) > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="File too large")

            # Save temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            logger.info(f"Processing with enhanced basic OCR: {file.filename}")

            # Use the enhanced OCR service
            ocr_results = ocr_service.process_prescription(temp_file_path)

            # Cleanup
            os.unlink(temp_file_path)

            # Enhanced response format
            response_data = {
                "success": ocr_results.get("success", True),
                "message": "Enhanced basic processing completed",
                "filename": file.filename,
                "processing_mode": processing_mode,
                "confidence_score": ocr_results.get("confidence", 0.7),
                "confidence_level": ocr_results.get("confidence_level", "Medium"),
                "extraction_method": "Enhanced Basic OCR",
                "requires_review": ocr_results.get("requires_review", True),

                "prescription_data": {
                    "doctor_name": ocr_results.get("doctor_name", "Not found"),
                    "patient_name": ocr_results.get("patient_name", "Not found"),
                    "clinic_name": ocr_results.get("clinic_name", "Not found"),
                    "medications": ocr_results.get("medications", "Not extracted"),
                    "diagnosis": ocr_results.get("diagnosis", "Not found"),
                    "prescription_date": ocr_results.get("prescription_date", "Not found"),
                    "instructions": ocr_results.get("instructions", "Follow doctor's advice"),
                    "patient_details": ocr_results.get("patient_details", "Not found"),
                    "follow_up": ocr_results.get("follow_up", "As advised")
                },

                "enhanced_features": {
                    "handwriting_info": {
                        "handwriting_detected": False,
                        "note": "Handwriting recognition not available - install torch and transformers"
                    },
                    "multilingual_info": {
                        "detected_languages": ["en"],
                        "is_multilingual": False,
                        "note": "Multi-language support limited - install additional ML dependencies"
                    },
                    "prescription_type": {
                        "type": "printed",
                        "confidence": 0.8,
                        "note": "Basic type detection only"
                    }
                },

                "raw_data": {
                    "combined_text": ocr_results.get("raw_extracted_text", "")
                },

                "processing_notes": [
                    f"Processed using Enhanced Basic OCR (mode: {processing_mode})",
                    "For full enhanced features, install: torch, transformers, easyocr",
                    "Current capabilities: Advanced Tesseract processing, Medical term extraction"
                ]
            }

            return JSONResponse(content=response_data)

        except Exception as e:
            logger.error(f"Enhanced basic processing failed: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Enhanced processing error: {str(e)}",
                    "note": "Unified pipeline not available"
                }
            )

    else:
        # Use the full unified pipeline
        try:
            # Validate file
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="Invalid file type")

            file_content = await file.read()
            if len(file_content) > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="File too large")

            # Save temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            logger.info(f"Processing with full unified pipeline: {file.filename}")

            # Use unified pipeline
            ocr_results = unified_ocr_pipeline.process_prescription_comprehensive(temp_file_path, processing_mode)

            # Process medical context if available
            if medical_processor and ocr_results.get('success', False):
                try:
                    medical_context = medical_processor.process_prescription_context(ocr_results)
                    ocr_results['medical_analysis'] = medical_context
                except Exception as e:
                    logger.warning(f"Medical context processing failed: {e}")

            # Cleanup
            os.unlink(temp_file_path)

            return JSONResponse(content=ocr_results)

        except Exception as e:
            logger.error(f"Unified pipeline processing failed: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": f"Unified pipeline error: {str(e)}"
                }
            )

@app.post("/upload-prescription")
async def upload_prescription_legacy(file: UploadFile = File(...)):
    """Legacy upload endpoint"""
    return await upload_prescription(file)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting HealthTwin AI server...")
    logger.info(f"Mode: {'Enhanced' if ENHANCED_OCR_AVAILABLE else 'Basic'}")
    logger.info("Server will be available at: http://127.0.0.1:8000")
    logger.info("API documentation at: http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
