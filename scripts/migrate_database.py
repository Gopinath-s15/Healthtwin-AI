#!/usr/bin/env python3
"""
Database migration script for HealthTwin Backend
Migrates existing database to new enhanced schema
"""
import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = "healthtwin.db"
BACKUP_PATH = f"healthtwin_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

def backup_database():
    """Create a backup of the existing database"""
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print(f"✓ Database backed up to: {BACKUP_PATH}")
        return True
    return False

def get_existing_columns(conn, table_name):
    """Get existing columns in a table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [column[1] for column in cursor.fetchall()]

def migrate_patients_table(conn):
    """Migrate patients table to enhanced schema"""
    cursor = conn.cursor()
    existing_columns = get_existing_columns(conn, "patients")
    
    # Add missing columns to patients table
    new_columns = [
        ("password_hash", "TEXT"),
        ("date_of_birth", "DATE"),
        ("gender", "TEXT"),
        ("address", "TEXT"),
        ("emergency_contact", "TEXT"),
        ("blood_type", "TEXT"),
        ("allergies", "TEXT"),
        ("chronic_conditions", "TEXT"),
        ("preferred_language", "TEXT DEFAULT 'en'"),
        ("is_active", "BOOLEAN DEFAULT TRUE"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    ]
    
    for column_name, column_type in new_columns:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE patients ADD COLUMN {column_name} {column_type}")
                print(f"✓ Added column {column_name} to patients table")
            except sqlite3.OperationalError as e:
                print(f"⚠ Could not add column {column_name}: {e}")

def migrate_timeline_table(conn):
    """Migrate timeline table to enhanced schema"""
    cursor = conn.cursor()
    existing_columns = get_existing_columns(conn, "timeline")
    
    # Add missing columns to timeline table
    new_columns = [
        ("doctor_id", "TEXT"),
        ("entry_type", "TEXT DEFAULT 'prescription'"),
        ("doctor_name", "TEXT"),
        ("dosage_instructions", "TEXT"),
        ("extracted_text", "TEXT"),
        ("structured_data", "TEXT"),
        ("follow_up_date", "DATE"),
        ("notes", "TEXT"),
        ("ai_insights", "TEXT"),
        ("drug_interactions", "TEXT"),
        ("adherence_score", "REAL"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    ]
    
    for column_name, column_type in new_columns:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE timeline ADD COLUMN {column_name} {column_type}")
                print(f"✓ Added column {column_name} to timeline table")
            except sqlite3.OperationalError as e:
                print(f"⚠ Could not add column {column_name}: {e}")

def create_new_tables(conn):
    """Create new tables for enhanced features"""
    cursor = conn.cursor()
    
    # Create doctors table
    cursor.execute('''
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
    print("✓ Created/verified doctors table")
    
    # Create medications table
    cursor.execute('''
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
    print("✓ Created/verified medications table")
    
    # Create patient_medications table
    cursor.execute('''
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
    print("✓ Created/verified patient_medications table")
    
    # Create appointments table
    cursor.execute('''
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
    print("✓ Created/verified appointments table")
    
    # Create health_metrics table
    cursor.execute('''
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
    print("✓ Created/verified health_metrics table")
    
    # Create AI processing logs
    cursor.execute('''
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
    print("✓ Created/verified ai_processing_logs table")
    
    # Create communication logs
    cursor.execute('''
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
    print("✓ Created/verified communication_logs table")
    
    # Create user sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            user_type TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✓ Created/verified user_sessions table")

def main():
    """Main migration function"""
    print("HealthTwin Database Migration")
    print("=" * 40)
    
    # Backup existing database
    backup_created = backup_database()
    
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        print("\n📊 Migrating existing tables...")
        migrate_patients_table(conn)
        migrate_timeline_table(conn)
        
        print("\n🆕 Creating new tables...")
        create_new_tables(conn)
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        print("\n✅ Database migration completed successfully!")
        print(f"📁 Backup saved as: {BACKUP_PATH}")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        if backup_created:
            print(f"💾 You can restore from backup: {BACKUP_PATH}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
