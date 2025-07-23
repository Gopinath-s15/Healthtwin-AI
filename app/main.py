from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.services.ocr_service import EnhancedPrescriptionOCR
    from app.ml_pipeline.unified_ocr_pipeline import UnifiedOCRPipeline
    from app.ml_pipeline.medical_context_processor import MedicalContextProcessor
except ImportError:
    # Fallback for direct execution
    from services.ocr_service import EnhancedPrescriptionOCR
    try:
        from ml_pipeline.unified_ocr_pipeline import UnifiedOCRPipeline
        from ml_pipeline.medical_context_processor import MedicalContextProcessor
    except ImportError:
        UnifiedOCRPipeline = None
        MedicalContextProcessor = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HealthTwin AI - Enhanced",
    description="AI-powered prescription processing with high-confidence OCR",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OCR services
ocr_service = EnhancedPrescriptionOCR()  # Legacy service for backward compatibility
unified_ocr_pipeline = None
medical_processor = None

# Initialize enhanced services with error handling
try:
    logger.info("Initializing enhanced OCR pipeline...")
    unified_ocr_pipeline = UnifiedOCRPipeline()
    medical_processor = MedicalContextProcessor()
    logger.info("Enhanced OCR pipeline initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize enhanced OCR pipeline: {e}")
    logger.info("Falling back to legacy OCR service")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HealthTwin AI - Enhanced Prescription Processing API",
        "version": "2.0.0",
        "features": ["Multi-engine OCR", "Medical NLP", "Safety validation"]
    }

@app.get("/health")
async def health_check():
    """Enhanced health check with new OCR capabilities"""
    health_status = {
        "status": "healthy",
        "service": "HealthTwin AI Enhanced v2.0",
        "ocr_engines": {
            "legacy_tesseract": True,
            "legacy_paddleocr": True,
            "unified_pipeline": unified_ocr_pipeline is not None,
            "handwriting_recognition": unified_ocr_pipeline is not None,
            "multilingual_ocr": unified_ocr_pipeline is not None,
            "medical_context_processor": medical_processor is not None
        },
        "features": [
            "Printed text OCR",
            "Handwriting recognition",
            "Multi-language support",
            "Medical context extraction",
            "Confidence validation",
            "Prescription type detection"
        ]
    }

    # Add detailed engine status if available
    if unified_ocr_pipeline:
        try:
            health_status["engine_details"] = {
                "handwriting_engine": unified_ocr_pipeline.handwriting_engine is not None,
                "multilingual_engine": unified_ocr_pipeline.multilingual_engine is not None,
                "printed_text_engine": unified_ocr_pipeline.printed_text_engine is not None,
                "processing_modes": ["fast", "standard", "comprehensive"]
            }
        except Exception as e:
            health_status["engine_details"] = {"error": str(e)}

    return health_status

@app.post("/patient/upload-prescription")
async def upload_prescription(file: UploadFile = File(...)):
    """
    Legacy prescription processing endpoint (maintained for backward compatibility)
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

        logger.info(f"Processing with legacy OCR: {file.filename}")

        # Legacy OCR processing
        ocr_results = ocr_service.process_prescription(temp_file_path)

        # Cleanup
        os.unlink(temp_file_path)

        # Determine response based on confidence and safety
        confidence_score = ocr_results.get("confidence", 0.0)
        requires_review = ocr_results.get("requires_review", True)
        safety_flags = ocr_results.get("safety_flags", [])

        if confidence_score < 0.4:
            status_message = "Low confidence extraction. Manual review required."
            success = False
        elif confidence_score < 0.7 or safety_flags:
            status_message = "Medium confidence extraction. Please verify results."
            success = True
        else:
            status_message = "High confidence extraction completed successfully."
            success = True
        
        response_data = {
            "success": success,
            "message": status_message,
            "filename": file.filename,
            "confidence_score": confidence_score,
            "confidence_level": ocr_results.get("confidence_level", "Unknown"),
            "extraction_method": ocr_results.get("extraction_method", "Enhanced OCR"),
            "requires_review": requires_review,
            "safety_flags": safety_flags,
            "extracted_data": {
                "raw_text": ocr_results.get("raw_extracted_text", ""),
                "doctor_name": ocr_results.get("doctor_name", "Not found"),
                "patient_name": ocr_results.get("patient_name", "Not found"),
                "clinic_name": ocr_results.get("clinic_name", "Not found"),
                "medications": ocr_results.get("medications", "Not extracted"),
                "diagnosis": ocr_results.get("diagnosis", "Not found"),
                "prescription_date": ocr_results.get("prescription_date", "Not found"),
                "instructions": ocr_results.get("instructions", "Follow doctor's advice"),
                "patient_details": ocr_results.get("patient_details", "Not found"),
                "follow_up": ocr_results.get("follow_up", "As advised")
            }
        }
        
        logger.info(f"Enhanced OCR completed: {confidence_score:.3f} confidence, {len(safety_flags)} flags")
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced processing failed: {str(e)}")
        
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
                "safety_flags": ["Processing Error"],
                "extracted_data": {
                    "raw_text": "Processing failed",
                    "doctor_name": "Processing failed"
                }
            }
        )

@app.post("/patient/upload-prescription-enhanced")
async def upload_prescription_enhanced(
    file: UploadFile = File(...),
    processing_mode: str = Query("standard", description="Processing mode: fast, standard, or comprehensive")
):
    """
    Enhanced prescription processing with handwriting recognition and multi-language support
    """
    try:
        # Validate file
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Invalid file type")

        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large")

        # Check if enhanced pipeline is available
        if not unified_ocr_pipeline:
            raise HTTPException(
                status_code=503,
                detail="Enhanced OCR pipeline not available. Please use /patient/upload-prescription endpoint."
            )

        # Validate processing mode
        valid_modes = ["fast", "standard", "comprehensive"]
        if processing_mode not in valid_modes:
            processing_mode = "standard"

        # Save temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        logger.info(f"Processing with enhanced OCR pipeline: {file.filename} (mode: {processing_mode})")

        # Enhanced OCR processing
        ocr_results = unified_ocr_pipeline.process_prescription_comprehensive(temp_file_path, processing_mode)

        # Process medical context if available
        medical_context = {}
        if medical_processor and ocr_results.get('success', False):
            try:
                medical_context = medical_processor.process_prescription_context(ocr_results)
            except Exception as e:
                logger.warning(f"Medical context processing failed: {e}")
                medical_context = {"error": str(e)}

        # Cleanup
        os.unlink(temp_file_path)

        # Determine response based on confidence and safety
        confidence_score = ocr_results.get("confidence", 0.0)
        requires_review = ocr_results.get("requires_review", True)
        safety_flags = ocr_results.get("safety_flags", [])

        if confidence_score < 0.4:
            status_message = "Low confidence extraction. Manual review required."
            success = False
        elif confidence_score < 0.7 or safety_flags:
            status_message = "Medium confidence extraction. Please verify results."
            success = True
        else:
            status_message = "High confidence extraction completed successfully."
            success = True

        # Prepare enhanced response
        response_data = {
            "success": success,
            "message": status_message,
            "filename": file.filename,
            "processing_mode": processing_mode,
            "confidence_score": confidence_score,
            "confidence_level": ocr_results.get("confidence_level", "Unknown"),
            "extraction_method": "Enhanced OCR Pipeline",
            "requires_review": requires_review,
            "safety_flags": safety_flags,

            # Basic prescription data
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

            # Enhanced features
            "enhanced_features": {
                "handwriting_info": ocr_results.get("handwriting_info", {}),
                "multilingual_info": ocr_results.get("multilingual_info", {}),
                "prescription_type": ocr_results.get("processing_metadata", {}).get("prescription_type", {}),
                "engines_used": ocr_results.get("processing_metadata", {}).get("engines_used", []),
                "processing_time": ocr_results.get("processing_metadata", {}).get("processing_time_seconds", 0)
            },

            # Medical context analysis
            "medical_analysis": medical_context,

            # Raw data
            "raw_data": {
                "combined_text": ocr_results.get("raw_extracted_text", ""),
                "engine_results": ocr_results.get("engine_results", {})
            },

            "processing_notes": [
                f"Processed using Enhanced OCR Pipeline (mode: {processing_mode})",
                f"Confidence level: {ocr_results.get('confidence_level', 'Unknown')}",
                f"Review required: {'Yes' if requires_review else 'No'}",
                f"Handwriting detected: {'Yes' if ocr_results.get('handwriting_info', {}).get('handwriting_detected', False) else 'No'}",
                f"Multi-language detected: {'Yes' if ocr_results.get('multilingual_info', {}).get('is_multilingual', False) else 'No'}"
            ]
        }

        logger.info(f"Enhanced OCR completed: {confidence_score:.3f} confidence, {processing_mode} mode")
        return JSONResponse(content=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced processing failed: {str(e)}")

        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Enhanced processing error: {str(e)}",
                "confidence_score": 0.0,
                "confidence_level": "Failed",
                "requires_review": True,
                "safety_flags": ["Processing Error"],
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
                },
                "enhanced_features": {},
                "medical_analysis": {},
                "raw_data": {"combined_text": "Processing failed"},
                "processing_notes": [f"Enhanced processing failed: {str(e)}"]
            }
        )

@app.get("/ocr/capabilities")
async def get_ocr_capabilities():
    """
    Get information about available OCR capabilities and features
    """
    capabilities = {
        "available_endpoints": {
            "/patient/upload-prescription": {
                "description": "Legacy OCR endpoint using Tesseract",
                "features": ["Printed text recognition", "Basic medical term extraction"],
                "supported_languages": ["English"],
                "processing_modes": ["standard"]
            },
            "/patient/upload-prescription-enhanced": {
                "description": "Enhanced OCR endpoint with advanced features",
                "features": [
                    "Printed text recognition",
                    "Handwriting recognition",
                    "Multi-language support",
                    "Medical context extraction",
                    "Prescription type detection"
                ],
                "supported_languages": ["English", "Hindi", "Tamil", "Telugu", "Kannada", "Malayalam"],
                "processing_modes": ["fast", "standard", "comprehensive"],
                "available": unified_ocr_pipeline is not None
            }
        },
        "processing_modes": {
            "fast": {
                "description": "Quick processing using printed text OCR only",
                "engines": ["printed_text"],
                "estimated_time": "2-5 seconds"
            },
            "standard": {
                "description": "Balanced processing with printed text and multi-language support",
                "engines": ["printed_text", "multilingual"],
                "estimated_time": "5-10 seconds"
            },
            "comprehensive": {
                "description": "Full processing with all available engines",
                "engines": ["printed_text", "multilingual", "handwriting"],
                "estimated_time": "10-20 seconds"
            }
        },
        "supported_features": {
            "handwriting_recognition": {
                "available": unified_ocr_pipeline is not None,
                "description": "Recognition of handwritten text in medical prescriptions",
                "models": ["TrOCR", "EasyOCR"]
            },
            "multilingual_support": {
                "available": unified_ocr_pipeline is not None,
                "description": "Support for mixed-language prescriptions",
                "languages": ["English", "Hindi", "Tamil", "Telugu", "Kannada", "Malayalam"],
                "features": ["Language detection", "Text translation", "Script recognition"]
            },
            "medical_context_extraction": {
                "available": medical_processor is not None,
                "description": "Extraction and structuring of medical information",
                "features": ["Medicine name recognition", "Dosage extraction", "Instruction parsing"]
            },
            "prescription_type_detection": {
                "available": unified_ocr_pipeline is not None,
                "description": "Automatic detection of prescription type",
                "types": ["printed", "handwritten", "mixed"]
            }
        },
        "file_requirements": {
            "supported_formats": ["JPG", "JPEG", "PNG", "BMP", "TIFF", "WebP"],
            "max_file_size": "10 MB",
            "recommended_resolution": "300 DPI or higher",
            "image_quality": "Clear, well-lit images with minimal blur"
        }
    }

    return capabilities

@app.get("/patient/timeline")
async def get_patient_timeline():
    """
    Get patient medical timeline (hackathon demo version)
    """
    try:
        # Mock timeline data for hackathon demonstration
        timeline_data = [
            {
                "id": 1,
                "date": "2024-01-15",
                "type": "prescription",
                "doctor": "Dr. Smith",
                "medications": ["Amoxicillin 500mg", "Paracetamol 650mg"],
                "diagnosis": "Upper respiratory infection",
                "confidence": "High",
                "status": "completed"
            },
            {
                "id": 2,
                "date": "2024-01-10", 
                "type": "checkup",
                "doctor": "Dr. Johnson",
                "notes": "Regular health checkup - all vitals normal",
                "confidence": "High",
                "status": "completed"
            },
            {
                "id": 3,
                "date": "2024-01-05",
                "type": "prescription",
                "doctor": "Dr. Patel",
                "medications": ["Cetirizine 10mg"],
                "diagnosis": "Seasonal allergies",
                "confidence": "Medium",
                "status": "completed"
            }
        ]
        
        logger.info("Timeline data retrieved successfully")
        
        return {
            "success": True,
            "timeline": timeline_data,
            "total_records": len(timeline_data),
            "message": "Timeline retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Timeline retrieval failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "timeline": [],
                "total_records": 0,
                "message": f"Failed to retrieve timeline: {str(e)}"
            }
        )

# Legacy endpoint for backward compatibility
@app.get("/timeline/{patient_id}")
async def get_timeline_legacy(patient_id: str):
    """Legacy timeline endpoint for backward compatibility"""
    return await get_patient_timeline()

# Additional endpoints for completeness
@app.post("/register")
async def register_patient_legacy():
    """Legacy registration endpoint"""
    return {
        "healthtwin_id": "demo-patient-123",
        "message": "Demo registration for hackathon"
    }

@app.post("/upload-prescription")
async def upload_prescription_legacy(file: UploadFile = File(...)):
    """Legacy upload endpoint"""
    return await upload_prescription(file)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
