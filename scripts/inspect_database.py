#!/usr/bin/env python3
"""
Database inspection tool for HealthTwin AI
View and query SQLite database contents
"""
import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "healthtwin.db"
UPLOAD_DIR = "uploads"

def get_table_info(conn, table_name):
    """Get table structure"""
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({table_name})")
    columns = c.fetchall()
    return columns

def show_database_structure():
    """Display complete database structure"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get all tables
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        
        print("📊 DATABASE STRUCTURE")
        print("=" * 50)
        
        for table in tables:
            table_name = table[0]
            print(f"\n🗂️  Table: {table_name}")
            print("-" * 30)
            
            # Get column info
            columns = get_table_info(conn, table_name)
            for col in columns:
                col_id, name, data_type, not_null, default, pk = col
                pk_marker = " (PK)" if pk else ""
                null_marker = " NOT NULL" if not_null else ""
                default_marker = f" DEFAULT {default}" if default else ""
                print(f"  {name}: {data_type}{pk_marker}{null_marker}{default_marker}")
            
            # Get row count
            c.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = c.fetchone()[0]
            print(f"  📈 Rows: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")

def show_patients_data():
    """Display all patients"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM patients ORDER BY created_at DESC")
        patients = c.fetchall()
        
        print("\n👥 PATIENTS DATA")
        print("=" * 50)
        
        if not patients:
            print("No patients found")
            return
        
        for patient in patients:
            print(f"\n🏥 Patient ID: {patient['id']}")
            print(f"   Name: {patient['name']}")
            print(f"   Phone: {patient['phone']}")
            if 'created_at' in patient.keys():
                print(f"   Created: {patient['created_at']}")
            
            # Get timeline count for this patient
            c.execute("SELECT COUNT(*) FROM timeline WHERE patient_id = ?", (patient['id'],))
            timeline_count = c.fetchone()[0]
            print(f"   Timeline entries: {timeline_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing patients: {e}")

def show_timeline_data():
    """Display timeline entries with file status"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("""
            SELECT t.*, p.name as patient_name 
            FROM timeline t 
            LEFT JOIN patients p ON t.patient_id = p.id 
            ORDER BY t.created_at DESC
        """)
        entries = c.fetchall()
        
        print("\n📋 TIMELINE DATA")
        print("=" * 50)
        
        if not entries:
            print("No timeline entries found")
            return
        
        for entry in entries:
            print(f"\n📄 Entry ID: {entry['id']}")
            print(f"   Patient: {entry['patient_name']} ({entry['patient_id']})")
            print(f"   Doctor: {entry.get('doctor_name', 'N/A')}")
            print(f"   Diagnosis: {entry.get('diagnosis', 'N/A')}")
            print(f"   Medications: {entry.get('medications', 'N/A')}")
            print(f"   Created: {entry['created_at']}")
            
            # Check if prescription image exists
            if entry.get('prescription_img'):
                file_path = os.path.join(UPLOAD_DIR, entry['prescription_img'])
                file_status = "✅ EXISTS" if os.path.exists(file_path) else "❌ MISSING"
                file_size = ""
                if os.path.exists(file_path):
                    size_bytes = os.path.getsize(file_path)
                    file_size = f" ({size_bytes:,} bytes)"
                print(f"   Image: {entry['prescription_img']} {file_status}{file_size}")
            
            # Show OCR data if available
            if entry.get('extracted_text'):
                text_preview = entry['extracted_text'][:100] + "..." if len(entry['extracted_text']) > 100 else entry['extracted_text']
                print(f"   OCR Text: {text_preview}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing timeline: {e}")

def show_file_analysis():
    """Analyze uploaded files"""
    print("\n📁 FILE ANALYSIS")
    print("=" * 50)
    
    if not os.path.exists(UPLOAD_DIR):
        print("Uploads directory doesn't exist")
        return
    
    files = os.listdir(UPLOAD_DIR)
    if not files:
        print("No files in uploads directory")
        return
    
    total_size = 0
    file_types = {}
    
    for filename in files:
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            total_size += size
            
            # Get file extension
            ext = os.path.splitext(filename)[1].lower()
            file_types[ext] = file_types.get(ext, 0) + 1
            
            print(f"📎 {filename} ({size:,} bytes)")
    
    print(f"\n📊 Summary:")
    print(f"   Total files: {len(files)}")
    print(f"   Total size: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
    print(f"   File types: {dict(file_types)}")

def run_custom_query():
    """Run custom SQL query"""
    print("\n🔍 CUSTOM QUERY")
    print("=" * 50)
    print("Enter SQL query (or 'exit' to return):")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        while True:
            query = input("SQL> ").strip()
            if query.lower() == 'exit':
                break
            
            if not query:
                continue
            
            try:
                c.execute(query)
                
                if query.lower().startswith('select'):
                    results = c.fetchall()
                    if results:
                        # Print column headers
                        headers = list(results[0].keys())
                        print(" | ".join(headers))
                        print("-" * (len(" | ".join(headers))))
                        
                        # Print rows
                        for row in results:
                            print(" | ".join(str(row[col]) for col in headers))
                    else:
                        print("No results")
                else:
                    conn.commit()
                    print(f"Query executed. Rows affected: {c.rowcount}")
                    
            except Exception as e:
                print(f"Query error: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error in custom query: {e}")

def main():
    """Main inspection function"""
    print("HealthTwin AI - Database Inspector")
    print("=" * 40)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return
    
    while True:
        print("\nChoose an option:")
        print("1. Show database structure")
        print("2. Show patients data")
        print("3. Show timeline data")
        print("4. Show file analysis")
        print("5. Run custom query")
        print("6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == '1':
            show_database_structure()
        elif choice == '2':
            show_patients_data()
        elif choice == '3':
            show_timeline_data()
        elif choice == '4':
            show_file_analysis()
        elif choice == '5':
            run_custom_query()
        elif choice == '6':
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()