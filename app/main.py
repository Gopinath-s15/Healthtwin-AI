from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer
from datetime import timedelta

from pydantic import BaseModel, field_validator
from typing import Optional, List
import uuid
import sqlite3
import os
import mimetypes
from pathlib import Path

# Import our custom modules
from .auth import (
    AuthService, Token, PatientLogin, DoctorLogin, PatientCreate, DoctorCreate,
    create_access_token, get_current_patient, get_current_doctor, get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from .database import DatabaseManager
from .ocr_service import PrescriptionOCR

app = FastAPI(title="HealthTwin AI API", version="2.0.0", description="Enhanced HealthTwin Backend with AI-powered features")

# Configure CORS with specific origins for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"]
)

# Create uploads directory and mount static files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

DB_PATH = "healthtwin.db"

# Initialize services
db_manager = DatabaseManager(DB_PATH)
auth_service = AuthService(DB_PATH)
ocr_service = PrescriptionOCR()

# Allowed file types for prescription uploads
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Default prescription data for demo purposes
DEFAULT_PRESCRIPTIONS = [
    {
        "id": "default-1",
        "doctor_name": "Dr. Sarah Johnson",
        "diagnosis": "Hypertension",
        "medications": "Lisinopril 10mg, Amlodipine 5mg",
        "prescription_img": "default-prescription-1.jpg",
        "created_at": "2024-01-15 10:30:00",
        "notes": "Monitor blood pressure daily. Follow up in 4 weeks.",
        "entry_type": "prescription"
    },
    {
        "id": "default-2", 
        "doctor_name": "Dr. Michael Chen",
        "diagnosis": "Type 2 Diabetes",
        "medications": "Metformin 500mg, Glipizide 5mg",
        "prescription_img": "default-prescription-2.jpg",
        "created_at": "2024-01-10 14:15:00",
        "notes": "Check blood sugar levels twice daily. Diet modification recommended.",
        "entry_type": "prescription"
    },
    {
        "id": "default-3",
        "doctor_name": "Dr. Emily Rodriguez", 
        "diagnosis": "Seasonal Allergies",
        "medications": "Cetirizine 10mg, Fluticasone nasal spray",
        "prescription_img": "default-prescription-3.jpg",
        "created_at": "2024-01-05 09:45:00",
        "notes": "Take antihistamine daily during allergy season. Use nasal spray as needed.",
        "entry_type": "prescription"
    }
]

def get_default_prescriptions():
    """Get default prescription data for demo purposes"""
    return DEFAULT_PRESCRIPTIONS.copy()

def has_user_prescriptions(patient_id: str) -> bool:
    """Check if patient has any uploaded prescriptions"""
    try:
        conn = db_manager.get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM timeline WHERE patient_id = ?", (patient_id,))
        count = c.fetchone()[0]
        conn.close()
        return count > 0
    except:
        return False

# Legacy database functions (keeping for compatibility)
def get_db_connection():
    """Get database connection with proper error handling (legacy)"""
    return db_manager.get_connection()

def patient_exists(patient_id: str) -> bool:
    """Check if patient exists (legacy)"""
    return db_manager.patient_exists(patient_id)

# Legacy PatientRegister model (keeping for backward compatibility)
class PatientRegister(BaseModel):
    phone: str
    name: Optional[str] = None

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Phone number is required')
        # Basic phone validation - adjust regex as needed
        import re
        if not re.match(r'^[\d\s\-\+\(\)]+$', v.strip()):
            raise ValueError('Invalid phone number format')
        return v.strip()

class DoctorTimelineEntry(BaseModel):
    patient_id: str
    diagnosis: str
    medications: str
    dosage_instructions: Optional[str] = None
    follow_up_date: Optional[str] = None
    notes: Optional[str] = None

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file type and size"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Check MIME type
    mime_type, _ = mimetypes.guess_type(file.filename)
    if not mime_type or not mime_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/auth/patient/register", response_model=Token)
async def register_patient_with_auth(patient_data: PatientCreate):
    """Register a new patient with authentication"""
    try:
        # Check if phone already exists
        conn = db_manager.get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM patients WHERE phone = ?", (patient_data.phone,))
        existing = c.fetchone()
        conn.close()

        if existing:
            raise HTTPException(status_code=400, detail="Phone number already registered")

        # Create patient with password
        patient_id = auth_service.create_patient_with_password(
            patient_data.phone, patient_data.name, patient_data.password
        )

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": patient_id, "user_type": "patient"},
            expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_type": "patient",
            "user_id": patient_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/auth/patient/login", response_model=Token)
async def login_patient(login_data: PatientLogin):
    """Authenticate patient login"""
    patient = auth_service.authenticate_patient(login_data.patient_id, login_data.password)

    if not patient:
        raise HTTPException(
            status_code=401,
            detail="Invalid patient ID or password"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": patient["id"], "user_type": "patient"},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "patient",
        "user_id": patient["id"]
    }

@app.post("/auth/doctor/register", response_model=Token)
async def register_doctor(doctor_data: DoctorCreate):
    """Register a new doctor"""
    try:
        # Check if doctor ID or license already exists
        conn = db_manager.get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM doctors WHERE id = ? OR license_number = ?",
                 (doctor_data.doctor_id, doctor_data.license_number))
        existing = c.fetchone()
        conn.close()

        if existing:
            raise HTTPException(status_code=400, detail="Doctor ID or license number already exists")

        # Create doctor
        doctor_id = auth_service.create_doctor(doctor_data)

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": doctor_id, "user_type": "doctor"},
            expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_type": "doctor",
            "user_id": doctor_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Doctor registration failed: {str(e)}")

@app.post("/auth/doctor/login", response_model=Token)
async def login_doctor(login_data: DoctorLogin):
    """Authenticate doctor login"""
    doctor = auth_service.authenticate_doctor(login_data.doctor_id, login_data.password)

    if not doctor:
        raise HTTPException(
            status_code=401,
            detail="Invalid doctor ID or password"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": doctor["id"], "user_type": "doctor"},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "doctor",
        "user_id": doctor["id"]
    }

# ============================================================================
# LEGACY ENDPOINTS
# ============================================================================

@app.post("/register")
async def register_patient(data: PatientRegister):
    """Register a new patient (legacy endpoint - no password)"""
    try:
        patient_id = str(uuid.uuid4())
        conn = db_manager.get_connection()
        c = conn.cursor()

        # Check if phone already exists
        c.execute("SELECT id FROM patients WHERE phone = ?", (data.phone,))
        existing = c.fetchone()
        if existing:
            conn.close()
            raise HTTPException(status_code=400, detail="Phone number already registered")

        c.execute("INSERT INTO patients (id, phone, name) VALUES (?, ?, ?)",
                 (patient_id, data.phone, data.name))
        conn.commit()
        conn.close()

        return {"healthtwin_id": patient_id, "message": "Patient registered successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

# ============================================================================
# FILE UPLOAD ENDPOINTS
# ============================================================================

@app.post("/patient/upload-prescription")
async def upload_prescription_authenticated(
    file: UploadFile = File(...),
    current_patient: str = Depends(get_current_patient)
):
    """Upload prescription image (authenticated patient)"""
    try:
        # Validate file
        validate_file(file)

        # Check file size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")

        # Generate unique filename
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Process with OCR
        try:
            ocr_results = ocr_service.process_prescription(file_path)
            
            # Store in database with OCR results
            timeline_id = db_manager.add_timeline_entry(
                patient_id=current_patient,
                entry_type="prescription",
                doctor_name=ocr_results.get("doctor_name", "Self-uploaded"),
                diagnosis=ocr_results.get("diagnosis", "Pending AI analysis"),
                medications=ocr_results.get("medications", "Pending AI extraction"),
                prescription_img=unique_filename,
                extracted_text=ocr_results.get("raw_extracted_text", ""),
                notes=f"""
Clinic: {ocr_results.get('clinic_name', 'Not found')}
Doctor: {ocr_results.get('doctor_name', 'Not clearly visible')}
Patient: {ocr_results.get('patient_name', 'Not clearly visible')}
Patient Details: {ocr_results.get('patient_details', 'N/A')}
Prescription Date: {ocr_results.get('prescription_date', 'Not found')}
Instructions: {ocr_results.get('instructions', 'Follow doctor advice')}
Follow-up: {ocr_results.get('follow_up', 'As advised')}
OCR Confidence: {ocr_results.get('confidence', 'Medium')}
                """.strip(),
                ai_insights=f"OCR Processing completed with {ocr_results.get('confidence', 'medium')} confidence"
            )
            
        except Exception as ocr_error:
            print(f"OCR Processing failed: {ocr_error}")
            # Fallback to basic entry
            timeline_id = db_manager.add_timeline_entry(
                patient_id=current_patient,
                entry_type="prescription",
                doctor_name="Self-uploaded",
                diagnosis="OCR processing failed",
                medications="Manual review required",
                prescription_img=unique_filename,
                notes="OCR processing encountered an error. Manual review recommended."
            )

        return {
            "status": "success",
            "timeline_id": timeline_id,
            "file": unique_filename,
            "message": "Prescription uploaded and processed successfully",
            "ocr_results": ocr_results if 'ocr_results' in locals() else None
        }

    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if database operation fails
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/upload-prescription")
async def upload_prescription_legacy(
    patient_id: str = Query(..., description="Patient ID"),
    file: UploadFile = File(...)
):
    """Upload prescription image for a patient (legacy endpoint)"""
    try:
        # Validate patient exists
        if not db_manager.patient_exists(patient_id):
            raise HTTPException(status_code=404, detail="Patient not found")

        # Validate file
        validate_file(file)

        # Check file size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")

        # Generate unique filename
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Store in database with better default values
        timeline_id = db_manager.add_timeline_entry(
            patient_id=patient_id,
            entry_type="prescription",
            doctor_name="Self-uploaded",
            diagnosis="Pending AI analysis",
            medications="Pending AI extraction",
            prescription_img=unique_filename,
            notes="Patient uploaded prescription - AI analysis in progress"
        )

        return {
            "status": "success",
            "timeline_id": timeline_id,
            "file": unique_filename,
            "message": "Prescription uploaded successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if database operation fails
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# ============================================================================
# DOCTOR ENDPOINTS
# ============================================================================

@app.post("/doctor/patient/{patient_id}/timeline")
async def add_doctor_timeline_entry(
    patient_id: str,
    entry_data: DoctorTimelineEntry,
    current_doctor: str = Depends(get_current_doctor)
):
    """Add a new medical entry to patient timeline"""
    try:
        if not db_manager.patient_exists(patient_id):
            raise HTTPException(status_code=404, detail="Patient not found")

        # Get doctor info
        doctor_info = db_manager.get_doctor_info(current_doctor)
        if not doctor_info:
            raise HTTPException(status_code=404, detail="Doctor not found")

        # Add timeline entry
        timeline_id = db_manager.add_timeline_entry(
            patient_id=patient_id,
            doctor_id=current_doctor,
            entry_type="medical_entry",
            doctor_name=doctor_info["name"],
            diagnosis=entry_data.diagnosis,
            medications=entry_data.medications,
            dosage_instructions=entry_data.dosage_instructions,
            follow_up_date=entry_data.follow_up_date,
            notes=entry_data.notes
        )

        return {
            "status": "success",
            "timeline_id": timeline_id,
            "message": "Medical entry added successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add entry: {str(e)}")

# ============================================================================
# TIMELINE ENDPOINTS
# ============================================================================

@app.get("/patient/timeline")
async def get_patient_own_timeline(current_patient: str = Depends(get_current_patient)):
    """Get patient's own complete timeline with default data if empty"""
    try:
        timeline = db_manager.get_patient_timeline(current_patient)
        patient_info = db_manager.get_patient_info(current_patient)

        # If no user prescriptions exist, return default data
        if not timeline:
            default_prescriptions = get_default_prescriptions()
            return {
                "patient": patient_info,
                "timeline": default_prescriptions,
                "is_default_data": True,
                "message": "Showing sample prescriptions. Upload your own to get started!"
            }

        return {
            "patient": patient_info,
            "timeline": timeline,
            "is_default_data": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve timeline: {str(e)}")

@app.get("/timeline/{patient_id}")
async def get_timeline_legacy(patient_id: str):
    """Get medical timeline for a patient (legacy endpoint) with default data"""
    try:
        # Validate patient exists
        if not db_manager.patient_exists(patient_id):
            raise HTTPException(status_code=404, detail="Patient not found")

        timeline = db_manager.get_patient_timeline(patient_id)

        # If no user prescriptions exist, return default data
        if not timeline:
            default_prescriptions = get_default_prescriptions()
            # Convert to legacy format
            legacy_timeline = []
            for entry in default_prescriptions:
                legacy_entry = {
                    "doctor": entry.get("doctor_name", "Unknown"),
                    "diagnosis": entry.get("diagnosis", ""),
                    "medications": entry.get("medications", ""),
                    "img": entry.get("prescription_img", ""),
                    "created_at": entry.get("created_at", "")
                }
                legacy_timeline.append(legacy_entry)

            return {
                "timeline": legacy_timeline,
                "is_default_data": True,
                "message": "Showing sample prescriptions. Upload your own to get started!"
            }

        # Convert user data to legacy format
        legacy_timeline = []
        for entry in timeline:
            legacy_entry = {
                "doctor": entry.get("doctor_name", "Unknown"),
                "diagnosis": entry.get("diagnosis", ""),
                "medications": entry.get("medications", ""),
                "img": entry.get("prescription_img", ""),
                "created_at": entry.get("created_at", "")
            }
            legacy_timeline.append(legacy_entry)

        return {
            "timeline": legacy_timeline,
            "is_default_data": False
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve timeline: {str(e)}")

@app.get("/patient/timeline/status")
async def get_timeline_status(current_patient: str = Depends(get_current_patient)):
    """Get timeline status (whether showing default or user data)"""
    try:
        has_user_data = has_user_prescriptions(current_patient)
        return {
            "has_user_data": has_user_data,
            "is_showing_default": not has_user_data,
            "total_entries": len(db_manager.get_patient_timeline(current_patient)) if has_user_data else len(DEFAULT_PRESCRIPTIONS)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

# ============================================================================
# USER PROFILE ENDPOINTS
# ============================================================================

@app.get("/patient/profile")
async def get_patient_profile(current_patient: str = Depends(get_current_patient)):
    """Get current patient's profile"""
    try:
        patient_info = db_manager.get_patient_info(current_patient)
        if not patient_info:
            raise HTTPException(status_code=404, detail="Patient not found")

        # Remove sensitive information
        patient_info.pop('password_hash', None)
        return {"patient": patient_info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")

@app.get("/doctor/profile")
async def get_doctor_profile(current_doctor: str = Depends(get_current_doctor)):
    """Get current doctor's profile"""
    try:
        doctor_info = db_manager.get_doctor_info(current_doctor)
        if not doctor_info:
            raise HTTPException(status_code=404, detail="Doctor not found")

        return {"doctor": doctor_info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")

# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "HealthTwin AI API is running", "version": "2.0.0", "features": ["authentication", "ai-processing", "multi-language"]}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test database connection
        conn = db_manager.get_connection()
        conn.close()
        db_status = "healthy"
    except:
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "database": db_status,
        "uploads_dir": "exists" if os.path.exists(UPLOAD_DIR) else "missing",
        "auth_service": "active",
        "version": "2.0.0"
    }
