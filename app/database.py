"""
Database utilities and models for HealthTwin Backend
"""
import sqlite3
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

class DatabaseManager:
    """Database manager for HealthTwin application"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize all database tables"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Enhanced patients table
        c.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                id TEXT PRIMARY KEY,
                phone TEXT NOT NULL UNIQUE,
                name TEXT,
                password_hash TEXT,
                date_of_birth DATE,
                gender TEXT,
                address TEXT,
                emergency_contact TEXT,
                blood_type TEXT,
                allergies TEXT,
                chronic_conditions TEXT,
                preferred_language TEXT DEFAULT 'en',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Doctors table
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Enhanced timeline table
        c.execute('''
            CREATE TABLE IF NOT EXISTS timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                doctor_id TEXT,
                entry_type TEXT DEFAULT 'prescription',
                doctor_name TEXT,
                diagnosis TEXT,
                medications TEXT,
                dosage_instructions TEXT,
                prescription_img TEXT,
                extracted_text TEXT,
                structured_data TEXT,
                follow_up_date DATE,
                notes TEXT,
                ai_insights TEXT,
                drug_interactions TEXT,
                adherence_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id),
                FOREIGN KEY (doctor_id) REFERENCES doctors (id)
            )
        ''')
        
        # Medications table for drug interaction checking
        c.execute('''
            CREATE TABLE IF NOT EXISTS medications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                generic_name TEXT,
                drug_class TEXT,
                common_dosages TEXT,
                contraindications TEXT,
                side_effects TEXT,
                interactions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Patient medications (current prescriptions)
        c.execute('''
            CREATE TABLE IF NOT EXISTS patient_medications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                medication_name TEXT NOT NULL,
                dosage TEXT,
                frequency TEXT,
                start_date DATE,
                end_date DATE,
                prescribed_by TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                adherence_tracking BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        ''')
        
        # Appointments table
        c.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                doctor_id TEXT NOT NULL,
                appointment_date TIMESTAMP NOT NULL,
                appointment_type TEXT,
                status TEXT DEFAULT 'scheduled',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id),
                FOREIGN KEY (doctor_id) REFERENCES doctors (id)
            )
        ''')
        
        # Health metrics table
        c.execute('''
            CREATE TABLE IF NOT EXISTS health_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                recorded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        ''')
        
        # AI processing logs
        c.execute('''
            CREATE TABLE IF NOT EXISTS ai_processing_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timeline_id INTEGER,
                processing_type TEXT NOT NULL,
                input_data TEXT,
                output_data TEXT,
                confidence_score REAL,
                processing_time REAL,
                status TEXT DEFAULT 'completed',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (timeline_id) REFERENCES timeline (id)
            )
        ''')
        
        # Communication logs
        c.execute('''
            CREATE TABLE IF NOT EXISTS communication_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                communication_type TEXT NOT NULL,
                recipient TEXT,
                message_content TEXT,
                language TEXT,
                status TEXT DEFAULT 'sent',
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        ''')
        
        # User sessions for authentication
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
    
    def patient_exists(self, patient_id: str) -> bool:
        """Check if patient exists"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT 1 FROM patients WHERE id = ? AND is_active = TRUE", (patient_id,))
        result = c.fetchone()
        conn.close()
        return result is not None
    
    def doctor_exists(self, doctor_id: str) -> bool:
        """Check if doctor exists"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT 1 FROM doctors WHERE id = ? AND is_active = TRUE", (doctor_id,))
        result = c.fetchone()
        conn.close()
        return result is not None
    
    def get_patient_info(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get patient information"""
        conn = self.get_connection()
        c = conn.cursor()

        # Get available columns first
        c.execute("PRAGMA table_info(patients)")
        available_columns = [col[1] for col in c.fetchall()]

        # Build query with only available columns
        base_columns = ['id', 'phone', 'name']
        optional_columns = ['date_of_birth', 'gender', 'address', 'emergency_contact',
                          'blood_type', 'allergies', 'chronic_conditions', 'preferred_language', 'created_at']

        columns_to_select = base_columns + [col for col in optional_columns if col in available_columns]

        query = f"""
            SELECT {', '.join(columns_to_select)}
            FROM patients
            WHERE id = ? AND (is_active IS NULL OR is_active = TRUE)
        """

        c.execute(query, (patient_id,))
        patient = c.fetchone()
        conn.close()

        if patient:
            return dict(patient)
        return None
    
    def get_doctor_info(self, doctor_id: str) -> Optional[Dict[str, Any]]:
        """Get doctor information"""
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT id, name, specialization, license_number, phone, email,
                   hospital_affiliation, years_experience, created_at
            FROM doctors 
            WHERE id = ? AND is_active = TRUE
        """, (doctor_id,))
        doctor = c.fetchone()
        conn.close()
        
        if doctor:
            return dict(doctor)
        return None
    
    def search_patients_by_doctor(self, doctor_id: str, search_term: str = None) -> List[Dict[str, Any]]:
        """Search patients accessible to a doctor"""
        conn = self.get_connection()
        c = conn.cursor()

        # Get available columns first
        c.execute("PRAGMA table_info(patients)")
        available_columns = [col[1] for col in c.fetchall()]

        # Build column list with available columns
        base_columns = ['id', 'name', 'phone']
        optional_columns = ['created_at']
        columns_to_select = base_columns + [col for col in optional_columns if col in available_columns]

        # Check if doctor_id column exists in timeline
        c.execute("PRAGMA table_info(timeline)")
        timeline_columns = [col[1] for col in c.fetchall()]
        has_doctor_id = 'doctor_id' in timeline_columns

        if has_doctor_id:
            # First check if any patients exist for this doctor
            c.execute("SELECT COUNT(*) FROM timeline WHERE doctor_id = ?", (doctor_id,))
            count = c.fetchone()[0]
        else:
            count = 0

        if count == 0:
            # Return all patients if doctor hasn't treated anyone yet (for demo purposes)
            if search_term:
                query = f"""
                    SELECT {', '.join(columns_to_select)}
                    FROM patients
                    WHERE (is_active IS NULL OR is_active = TRUE)
                    AND (name LIKE ? OR phone LIKE ? OR id LIKE ?)
                    ORDER BY name
                    LIMIT 10
                """
                c.execute(query, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            else:
                query = f"""
                    SELECT {', '.join(columns_to_select)}
                    FROM patients
                    WHERE (is_active IS NULL OR is_active = TRUE)
                    ORDER BY name
                    LIMIT 10
                """
                c.execute(query)
        else:
            # Return patients this doctor has treated
            if search_term:
                query = f"""
                    SELECT DISTINCT p.{', p.'.join(columns_to_select)}
                    FROM patients p
                    JOIN timeline t ON p.id = t.patient_id
                    WHERE t.doctor_id = ? AND (p.is_active IS NULL OR p.is_active = TRUE)
                    AND (p.name LIKE ? OR p.phone LIKE ? OR p.id LIKE ?)
                    ORDER BY p.name
                """
                c.execute(query, (doctor_id, f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            else:
                query = f"""
                    SELECT DISTINCT p.{', p.'.join(columns_to_select)}
                    FROM patients p
                    JOIN timeline t ON p.id = t.patient_id
                    WHERE t.doctor_id = ? AND (p.is_active IS NULL OR p.is_active = TRUE)
                    ORDER BY p.name
                """
                c.execute(query, (doctor_id,))

        patients = c.fetchall()
        conn.close()

        return [dict(patient) for patient in patients]
    
    def get_patient_timeline(self, patient_id: str, doctor_id: str = None) -> List[Dict[str, Any]]:
        """Get patient timeline with optional doctor filtering"""
        conn = self.get_connection()
        c = conn.cursor()

        # Get available columns first
        c.execute("PRAGMA table_info(timeline)")
        available_columns = [col[1] for col in c.fetchall()]

        # Build query with only available columns
        base_columns = ['id', 'patient_id', 'diagnosis', 'medications', 'prescription_img', 'created_at']
        optional_columns = ['doctor_id', 'doctor_name', 'dosage_instructions', 'extracted_text',
                          'follow_up_date', 'notes', 'ai_insights', 'drug_interactions',
                          'adherence_score', 'updated_at', 'doctor', 'entry_type']

        columns_to_select = [col for col in (base_columns + optional_columns) if col in available_columns]

        if doctor_id and 'doctor_id' in available_columns:
            # Doctor can only see entries they created or general entries
            query = f"""
                SELECT {', '.join(columns_to_select)}
                FROM timeline
                WHERE patient_id = ? AND (doctor_id = ? OR doctor_id IS NULL)
                ORDER BY created_at DESC
            """
            c.execute(query, (patient_id, doctor_id))
        else:
            # Patient can see all their entries
            query = f"""
                SELECT {', '.join(columns_to_select)}
                FROM timeline
                WHERE patient_id = ?
                ORDER BY created_at DESC
            """
            c.execute(query, (patient_id,))

        timeline = c.fetchall()
        conn.close()

        return [dict(entry) for entry in timeline]
    
    def add_timeline_entry(self, patient_id: str, doctor_id: str = None, **kwargs) -> int:
        """Add a new timeline entry"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Build dynamic insert query
        fields = ['patient_id']
        values = [patient_id]
        placeholders = ['?']
        
        if doctor_id:
            fields.append('doctor_id')
            values.append(doctor_id)
            placeholders.append('?')
        
        for field, value in kwargs.items():
            if value is not None:
                fields.append(field)
                values.append(value)
                placeholders.append('?')
        
        query = f"""
            INSERT INTO timeline ({', '.join(fields)})
            VALUES ({', '.join(placeholders)})
        """
        
        c.execute(query, values)
        timeline_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return timeline_id
