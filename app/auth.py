"""
Authentication and authorization module for HealthTwin Backend
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import sqlite3
import os

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "healthtwin-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token security
security = HTTPBearer()

class Token(BaseModel):
    access_token: str
    token_type: str
    user_type: str
    user_id: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    user_type: Optional[str] = None

class PatientLogin(BaseModel):
    patient_id: str
    password: str

class DoctorLogin(BaseModel):
    doctor_id: str
    password: str

class PatientCreate(BaseModel):
    phone: str
    name: Optional[str] = None
    password: str

class DoctorCreate(BaseModel):
    doctor_id: str
    name: str
    specialization: str
    license_number: str
    password: str

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Verify and decode JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("user_type")
        if user_id is None or user_type is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id, user_type=user_type)
    except JWTError:
        raise credentials_exception
    return token_data

def get_current_patient(token_data: TokenData = Depends(verify_token)) -> str:
    """Get current authenticated patient"""
    if token_data.user_type != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized as patient"
        )
    return token_data.user_id

def get_current_doctor(token_data: TokenData = Depends(verify_token)) -> str:
    """Get current authenticated doctor"""
    if token_data.user_type != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized as doctor"
        )
    return token_data.user_id

def get_current_user(token_data: TokenData = Depends(verify_token)) -> tuple:
    """Get current authenticated user (patient or doctor)"""
    return token_data.user_id, token_data.user_type

class AuthService:
    """Authentication service for managing users"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_auth_tables()
    
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_auth_tables(self):
        """Initialize authentication tables"""
        conn = self.get_db_connection()
        c = conn.cursor()

        # Check if password_hash column exists in patients table
        c.execute("PRAGMA table_info(patients)")
        columns = [column[1] for column in c.fetchall()]

        if 'password_hash' not in columns:
            try:
                c.execute('ALTER TABLE patients ADD COLUMN password_hash TEXT')
            except sqlite3.OperationalError:
                pass

        # Create doctors table
        c.execute('''
            CREATE TABLE IF NOT EXISTS doctors (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                specialization TEXT,
                license_number TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                hospital_affiliation TEXT,
                years_experience INTEGER,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create sessions table for token management
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                user_type TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
    
    def authenticate_patient(self, patient_id: str, password: str) -> Optional[dict]:
        """Authenticate a patient"""
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id, name, phone, password_hash FROM patients WHERE id = ?", (patient_id,))
        patient = c.fetchone()
        conn.close()
        
        if patient and patient['password_hash'] and verify_password(password, patient['password_hash']):
            return {
                "id": patient['id'],
                "name": patient['name'],
                "phone": patient['phone']
            }
        return None
    
    def authenticate_doctor(self, doctor_id: str, password: str) -> Optional[dict]:
        """Authenticate a doctor"""
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id, name, specialization, license_number FROM doctors WHERE id = ? AND is_active = TRUE", (doctor_id,))
        doctor = c.fetchone()
        
        if doctor:
            c.execute("SELECT password_hash FROM doctors WHERE id = ?", (doctor_id,))
            password_row = c.fetchone()
            conn.close()
            
            if password_row and verify_password(password, password_row['password_hash']):
                return {
                    "id": doctor['id'],
                    "name": doctor['name'],
                    "specialization": doctor['specialization'],
                    "license_number": doctor['license_number']
                }
        else:
            conn.close()
        return None
    
    def create_patient_with_password(self, phone: str, name: str, password: str) -> str:
        """Create a new patient with password"""
        import uuid
        patient_id = str(uuid.uuid4())
        password_hash = get_password_hash(password)
        
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute(
            "INSERT INTO patients (id, phone, name, password_hash) VALUES (?, ?, ?, ?)",
            (patient_id, phone, name, password_hash)
        )
        conn.commit()
        conn.close()
        return patient_id
    
    def create_doctor(self, doctor_data: DoctorCreate) -> str:
        """Create a new doctor"""
        password_hash = get_password_hash(doctor_data.password)
        
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute(
            "INSERT INTO doctors (id, name, specialization, license_number, password_hash) VALUES (?, ?, ?, ?, ?)",
            (doctor_data.doctor_id, doctor_data.name, doctor_data.specialization, 
             doctor_data.license_number, password_hash)
        )
        conn.commit()
        conn.close()
        return doctor_data.doctor_id
    
    def update_patient_password(self, patient_id: str, new_password: str) -> bool:
        """Update patient password"""
        password_hash = get_password_hash(new_password)
        
        conn = self.get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE patients SET password_hash = ? WHERE id = ?", (password_hash, patient_id))
        success = c.rowcount > 0
        conn.commit()
        conn.close()
        return success
