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
    from app.services.pdf_processor import PDFProcessor
    from app.ml_pipeline.unified_ocr_pipeline import UnifiedOCRPipeline
    from app.ml_pipeline.medical_context_processor import MedicalContextProcessor
except ImportError:
    # Fallback for direct execution
    from services.ocr_service import EnhancedPrescriptionOCR
    from services.pdf_processor import PDFProcessor
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
pdf_processor = PDFProcessor()  # PDF processing service
unified_ocr_pipeline = None
medical_processor = None

# Initialize enhanced services with error handling
try:
    logger.info("🔧 Starting enhanced OCR pipeline initialization...")
    unified_ocr_pipeline = UnifiedOCRPipeline()
    logger.info("✅ Unified OCR pipeline created successfully")

    medical_processor = MedicalContextProcessor()
    logger.info("✅ Medical context processor created successfully")

    logger.info("🎉 Enhanced OCR pipeline initialized successfully")
    logger.info(f"📊 Pipeline status: unified_ocr_pipeline = {unified_ocr_pipeline is not None}")
except Exception as e:
    logger.error(f"❌ Failed to initialize enhanced OCR pipeline: {e}")
    logger.info("🔄 Falling back to legacy OCR service")
    import traceback
    traceback.print_exc()

# Helper functions for file processing
def validate_file_type(file: UploadFile) -> Dict[str, Any]:
    """
    Validate uploaded file type and return file info

    Args:
        file: FastAPI UploadFile object

    Returns:
        Dict with validation results
    """
    # Log file details for debugging
    logger.info(f"Validating file: {file.filename}, content_type: {file.content_type}")

    # Check if file has content type
    if not file.content_type:
        # Try to guess from filename
        if file.filename:
            filename_lower = file.filename.lower()
            if filename_lower.endswith('.pdf'):
                logger.info("Detected PDF from filename extension")
                if not pdf_processor.is_pdf_supported():
                    return {
                        "valid": False,
                        "error": "PDF processing not supported - missing dependencies",
                        "file_type": "pdf"
                    }
                return {
                    "valid": True,
                    "file_type": "pdf",
                    "content_type": "application/pdf"
                }
            elif any(filename_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']):
                logger.info("Detected image from filename extension")
                return {
                    "valid": True,
                    "file_type": "image",
                    "content_type": "image/unknown"
                }

        return {
            "valid": False,
            "error": "File type could not be determined",
            "file_type": None
        }

    # Check for image files
    if file.content_type.startswith('image/'):
        logger.info(f"Validated image file: {file.content_type}")
        return {
            "valid": True,
            "file_type": "image",
            "content_type": file.content_type
        }

    # Check for PDF files
    if file.content_type == 'application/pdf':
        logger.info(f"Validated PDF file: {file.content_type}")
        if not pdf_processor.is_pdf_supported():
            return {
                "valid": False,
                "error": "PDF processing not supported - missing dependencies",
                "file_type": "pdf"
            }
        return {
            "valid": True,
            "file_type": "pdf",
            "content_type": file.content_type
        }

    # Unsupported file type
    logger.warning(f"Unsupported file type: {file.content_type} for file: {file.filename}")
    return {
        "valid": False,
        "error": f"Unsupported file type: {file.content_type}. Please upload an image (JPG, PNG, etc.) or PDF file",
        "file_type": None
    }

def enhance_with_handwriting_specialist(image_path: str, ocr_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance OCR results with handwriting specialist when handwriting is detected
    """
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'ml_pipeline'))
        from app.ml_pipeline.handwriting_specialist import HandwritingSpecialist
        import cv2

        logger.info("Initializing handwriting specialist for enhancement")
        specialist = HandwritingSpecialist()

        # Load image
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Could not load image: {image_path}")
            return ocr_results

        # Extract handwritten medications
        specialist_result = specialist.extract_handwritten_text(image)

        if specialist_result.get('success'):
            specialist_medications = specialist_result.get('medications', [])
            specialist_instructions = specialist_result.get('instructions', [])

            logger.info(f"Handwriting specialist found {len(specialist_medications)} medications")

            if len(specialist_medications) > 0:
                # Enhance the medical analysis with handwriting specialist results
                medical_analysis = ocr_results.get('medical_analysis', {})
                if medical_analysis.get('success'):
                    structured_prescription = medical_analysis.get('structured_prescription', {})
                    existing_medicines = structured_prescription.get('medicines', [])
                    existing_instructions = structured_prescription.get('instructions', [])

                    # Convert specialist medications to the expected format
                    enhanced_medicines = []
                    for med in specialist_medications:
                        enhanced_med = {
                            'name': med.get('name', 'Unknown'),
                            'confidence': med.get('confidence', 0.8),
                            'category': med.get('category', 'unknown'),
                            'dosage': med.get('dosage', 'Not specified'),
                            'frequency': med.get('frequency', 'Not specified'),
                            'form': med.get('form', 'Not specified'),
                            'source': 'handwriting_specialist'
                        }
                        enhanced_medicines.append(enhanced_med)

                    # Merge with existing medicines (prioritize handwriting specialist)
                    all_medicines = enhanced_medicines + existing_medicines

                    # Remove duplicates (keep handwriting specialist results)
                    unique_medicines = {}
                    for med in all_medicines:
                        name_key = med['name'].lower()
                        if name_key not in unique_medicines or med.get('source') == 'handwriting_specialist':
                            unique_medicines[name_key] = med

                    final_medicines = list(unique_medicines.values())

                    # Update the results
                    structured_prescription['medicines'] = final_medicines
                    structured_prescription['instructions'] = list(set(existing_instructions + specialist_instructions))

                    medical_analysis['structured_prescription'] = structured_prescription
                    ocr_results['medical_analysis'] = medical_analysis

                    # Update extraction method
                    ocr_results['extraction_method'] = f"{ocr_results.get('extraction_method', 'Enhanced OCR')} + Handwriting Specialist"

                    # Update confidence if handwriting specialist is more confident
                    if specialist_result.get('confidence', 0) > ocr_results.get('confidence_score', 0):
                        ocr_results['confidence_score'] = specialist_result.get('confidence', 0.8)

                    logger.info(f"Enhanced results with {len(final_medicines)} total medications")

        return ocr_results

    except Exception as e:
        logger.error(f"Handwriting specialist enhancement failed: {e}")
        return ocr_results

def process_single_image_ocr(image_path: str, filename: str, processing_mode: str = "standard") -> Dict[str, Any]:
    """
    Process a single image file with OCR

    Args:
        image_path: Path to image file
        filename: Original filename
        processing_mode: OCR processing mode

    Returns:
        OCR results dictionary
    """
    try:
        logger.info(f"DEBUG: unified_ocr_pipeline = {unified_ocr_pipeline is not None}, processing_mode = {processing_mode}")

        if unified_ocr_pipeline and processing_mode != "legacy":
            # Use enhanced OCR pipeline
            logger.info(f"Processing with enhanced OCR: {filename} (mode: {processing_mode})")
            return unified_ocr_pipeline.process_prescription_comprehensive(image_path, processing_mode)
        else:
            # Use legacy OCR service with handwriting enhancement
            logger.info(f"Processing with legacy OCR + handwriting enhancement: {filename} (unified_ocr_pipeline available: {unified_ocr_pipeline is not None})")

            # Get legacy OCR results
            legacy_results = ocr_service.process_prescription(image_path)

            # Always try handwriting enhancement for better results
            try:
                logger.info("🔍 Attempting handwriting enhancement on legacy results")
                enhanced_results = enhance_with_handwriting_specialist(image_path, legacy_results)
                logger.info("✅ Handwriting enhancement completed")
                return enhanced_results
            except Exception as e:
                logger.warning(f"⚠️ Handwriting enhancement failed: {e}")
                return legacy_results
    except Exception as e:
        logger.error(f"OCR processing failed for {filename}: {e}")
        return {
            "success": False,
            "error": f"OCR processing failed: {str(e)}",
            "confidence": 0.0,
            "requires_review": True
        }

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
    Legacy prescription processing endpoint with PDF support (maintained for backward compatibility)
    """
    temp_paths = []
    try:
        # Validate file type
        file_validation = validate_file_type(file)
        if not file_validation["valid"]:
            raise HTTPException(status_code=400, detail=file_validation["error"])

        file_content = await file.read()
        file_type = file_validation["file_type"]

        # Check file size limits
        max_size = 50 * 1024 * 1024 if file_type == "pdf" else 10 * 1024 * 1024  # 50MB for PDF, 10MB for images
        if len(file_content) > max_size:
            raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {max_size // (1024*1024)}MB")

        # Process based on file type
        if file_type == "image":
            # Handle image files (existing logic)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(file_content)
                temp_paths.append(temp_file.name)

            logger.info(f"Processing image with legacy OCR: {file.filename}")
            ocr_results = process_single_image_ocr(temp_paths[0], file.filename, "legacy")

        elif file_type == "pdf":
            # Handle PDF files
            logger.info(f"Processing PDF with legacy OCR: {file.filename}")

            # Extract images from PDF
            pdf_result = pdf_processor.process_pdf_for_ocr(file_content, file.filename)
            if not pdf_result["success"]:
                raise HTTPException(status_code=400, detail=pdf_result["error"])

            temp_paths = pdf_result["temp_paths"]

            # Process each page and combine results
            all_results = []
            combined_text = []

            for i, temp_path in enumerate(temp_paths):
                page_results = process_single_image_ocr(temp_path, f"{file.filename}_page_{i+1}", "legacy")
                all_results.append(page_results)
                if page_results.get("raw_extracted_text"):
                    combined_text.append(f"Page {i+1}:\n{page_results['raw_extracted_text']}")

            # Combine results from all pages
            if all_results:
                # Use the best result or combine them
                best_result = max(all_results, key=lambda x: x.get("confidence", 0))
                ocr_results = best_result.copy()
                ocr_results["raw_extracted_text"] = "\n\n".join(combined_text)
                ocr_results["pdf_info"] = {
                    "total_pages": pdf_result["page_count"],
                    "processed_pages": len(all_results),
                    "page_results": all_results
                }
                ocr_results["extraction_method"] = f"Legacy OCR (PDF - {len(all_results)} pages)"
            else:
                ocr_results = {
                    "success": False,
                    "error": "No text could be extracted from PDF pages",
                    "confidence": 0.0,
                    "requires_review": True
                }

        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Cleanup temporary files
        for temp_path in temp_paths:
            try:
                os.unlink(temp_path)
            except:
                pass

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
        logger.error(f"Processing failed: {str(e)}")

        # Cleanup temporary files on error
        for temp_path in temp_paths:
            try:
                os.unlink(temp_path)
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
    Enhanced prescription processing with handwriting recognition, multi-language support, and PDF support
    """
    temp_paths = []
    try:
        # Validate file type
        file_validation = validate_file_type(file)
        if not file_validation["valid"]:
            raise HTTPException(status_code=400, detail=file_validation["error"])

        file_content = await file.read()
        file_type = file_validation["file_type"]

        # Check file size limits
        max_size = 50 * 1024 * 1024 if file_type == "pdf" else 10 * 1024 * 1024  # 50MB for PDF, 10MB for images
        if len(file_content) > max_size:
            raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {max_size // (1024*1024)}MB")

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

        # Process based on file type
        if file_type == "image":
            # Handle image files (existing logic)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(file_content)
                temp_paths.append(temp_file.name)

            logger.info(f"🔧 Processing image with enhanced OCR: {file.filename} (mode: {processing_mode})")
            logger.info(f"📁 Temp file path: {temp_paths[0]}")
            ocr_results = process_single_image_ocr(temp_paths[0], file.filename, processing_mode)
            logger.info(f"📊 OCR results received: {type(ocr_results)}, keys: {list(ocr_results.keys()) if isinstance(ocr_results, dict) else 'not dict'}")
            logger.info(f"🎯 About to check for handwriting enhancement...")

            # Apply handwriting specialist enhancement if handwriting is detected
            try:
                enhanced_features = ocr_results.get('enhanced_features', {})
                prescription_type = enhanced_features.get('prescription_type', {})
                handwriting_info = enhanced_features.get('handwriting_info', {})

                logger.info(f"🔍 Prescription type detection: {prescription_type}")
                logger.info(f"✍️ Handwriting info: {handwriting_info}")

                # More lenient condition for handwriting detection
                is_handwritten = (
                    prescription_type.get('type') == 'handwritten' or
                    handwriting_info.get('handwriting_detected', False) or
                    prescription_type.get('confidence', 0) > 0.5 or
                    handwriting_info.get('handwriting_confidence', 0) > 0.5 or
                    'handwritten' in str(prescription_type).lower()
                )

                logger.info(f"🎯 Handwriting detection result: {is_handwritten}")

                if is_handwritten:
                    logger.info("🚀 Handwriting detected, applying handwriting specialist enhancement")
                    ocr_results = enhance_with_handwriting_specialist(temp_paths[0], ocr_results)
                    logger.info("✅ Handwriting specialist enhancement completed")
                else:
                    logger.info("❌ No handwriting detected, skipping handwriting specialist enhancement")

            except Exception as e:
                logger.warning(f"⚠️ Handwriting specialist enhancement failed: {e}")
                import traceback
                traceback.print_exc()

        elif file_type == "pdf":
            # Handle PDF files
            logger.info(f"Processing PDF with enhanced OCR: {file.filename} (mode: {processing_mode})")

            # Extract images from PDF
            pdf_result = pdf_processor.process_pdf_for_ocr(file_content, file.filename)
            if not pdf_result["success"]:
                raise HTTPException(status_code=400, detail=pdf_result["error"])

            temp_paths = pdf_result["temp_paths"]

            # Process each page with enhanced OCR
            all_results = []
            combined_text = []
            best_confidence = 0.0

            for i, temp_path in enumerate(temp_paths):
                page_results = process_single_image_ocr(temp_path, f"{file.filename}_page_{i+1}", processing_mode)
                all_results.append(page_results)

                if page_results.get("raw_extracted_text"):
                    combined_text.append(f"Page {i+1}:\n{page_results['raw_extracted_text']}")

                # Track best confidence
                page_confidence = page_results.get("confidence", 0.0)
                if page_confidence > best_confidence:
                    best_confidence = page_confidence

            # Combine results from all pages
            if all_results:
                # Use the best result as base and enhance with combined data
                best_result = max(all_results, key=lambda x: x.get("confidence", 0))
                ocr_results = best_result.copy()

                # Update with combined information
                ocr_results["raw_extracted_text"] = "\n\n".join(combined_text)
                ocr_results["confidence"] = best_confidence
                ocr_results["pdf_info"] = {
                    "total_pages": pdf_result["page_count"],
                    "processed_pages": len(all_results),
                    "page_results": all_results,
                    "images_metadata": pdf_result["images_metadata"]
                }
                ocr_results["extraction_method"] = f"Enhanced OCR Pipeline (PDF - {len(all_results)} pages)"

                # Combine safety flags from all pages
                all_safety_flags = []
                for result in all_results:
                    all_safety_flags.extend(result.get("safety_flags", []))
                ocr_results["safety_flags"] = list(set(all_safety_flags))  # Remove duplicates

            else:
                ocr_results = {
                    "success": False,
                    "error": "No text could be extracted from PDF pages",
                    "confidence": 0.0,
                    "requires_review": True,
                    "pdf_info": {
                        "total_pages": pdf_result["page_count"],
                        "processed_pages": 0,
                        "page_results": []
                    }
                }

        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Process medical context if available
        medical_context = {}
        if medical_processor and ocr_results.get('success', False):
            try:
                medical_context = medical_processor.process_prescription_context(ocr_results)
            except Exception as e:
                logger.warning(f"Medical context processing failed: {e}")
                medical_context = {"error": str(e)}

        # Cleanup temporary files
        for temp_path in temp_paths:
            try:
                os.unlink(temp_path)
            except:
                pass

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

        # Cleanup temporary files on error
        for temp_path in temp_paths:
            try:
                os.unlink(temp_path)
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
            "supported_formats": ["JPG", "JPEG", "PNG", "BMP", "TIFF", "WebP", "PDF"],
            "max_file_size": "10 MB for images, 50 MB for PDFs",
            "recommended_resolution": "300 DPI or higher",
            "image_quality": "Clear, well-lit images with minimal blur",
            "pdf_support": {
                "available": pdf_processor.is_pdf_supported(),
                "max_pages": 10,
                "description": "Multi-page PDF support with automatic page extraction",
                "processing": "Each page processed individually and results combined"
            }
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
