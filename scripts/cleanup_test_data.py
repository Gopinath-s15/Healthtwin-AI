#!/usr/bin/env python3
"""
Cleanup script for HealthTwin AI test data
Removes test uploads and resets database for fresh start
"""
import os
import sqlite3
import shutil
from datetime import datetime
import glob

# Paths
UPLOAD_DIR = "uploads"
DB_PATH = "healthtwin.db"
BACKUP_DIR = "backups"

def create_backup():
    """Create backup before cleanup"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Backup database
    if os.path.exists(DB_PATH):
        backup_db = f"{BACKUP_DIR}/healthtwin_backup_{timestamp}.db"
        shutil.copy2(DB_PATH, backup_db)
        print(f"✓ Database backed up to: {backup_db}")
    
    # Backup uploads directory
    if os.path.exists(UPLOAD_DIR):
        backup_uploads = f"{BACKUP_DIR}/uploads_backup_{timestamp}"
        shutil.copytree(UPLOAD_DIR, backup_uploads)
        print(f"✓ Uploads backed up to: {backup_uploads}")

def clean_uploads_directory():
    """Remove all uploaded files"""
    if not os.path.exists(UPLOAD_DIR):
        print("✓ Uploads directory doesn't exist")
        return
    
    files = glob.glob(os.path.join(UPLOAD_DIR, "*"))
    if not files:
        print("✓ Uploads directory is already empty")
        return
    
    for file_path in files:
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"  Deleted: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"  Error deleting {file_path}: {e}")
    
    print(f"✓ Cleaned {len(files)} files from uploads directory")

def clean_test_database_entries():
    """Remove test entries from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get current counts
        c.execute("SELECT COUNT(*) FROM timeline")
        timeline_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM patients WHERE name LIKE '%Test%' OR name LIKE '%Upload%'")
        test_patients = c.fetchone()[0]
        
        print(f"Current database state:")
        print(f"  Timeline entries: {timeline_count}")
        print(f"  Test patients: {test_patients}")
        
        # Remove test timeline entries
        c.execute("""
            DELETE FROM timeline 
            WHERE patient_id IN (
                SELECT id FROM patients 
                WHERE name LIKE '%Test%' OR name LIKE '%Upload%'
            )
        """)
        deleted_timeline = c.rowcount
        
        # Remove test patients
        c.execute("DELETE FROM patients WHERE name LIKE '%Test%' OR name LIKE '%Upload%'")
        deleted_patients = c.rowcount
        
        # Remove orphaned timeline entries (files that no longer exist)
        c.execute("""
            DELETE FROM timeline 
            WHERE prescription_img IS NOT NULL 
            AND prescription_img != ''
        """)
        
        # Get remaining entries and check if files exist
        c.execute("SELECT id, prescription_img FROM timeline WHERE prescription_img IS NOT NULL")
        entries = c.fetchall()
        
        orphaned_entries = 0
        for entry_id, img_file in entries:
            file_path = os.path.join(UPLOAD_DIR, img_file)
            if not os.path.exists(file_path):
                c.execute("DELETE FROM timeline WHERE id = ?", (entry_id,))
                orphaned_entries += 1
        
        conn.commit()
        conn.close()
        
        print(f"✓ Cleaned database:")
        print(f"  Deleted {deleted_timeline} timeline entries")
        print(f"  Deleted {deleted_patients} test patients")
        print(f"  Deleted {orphaned_entries} orphaned entries")
        
    except Exception as e:
        print(f"❌ Database cleanup failed: {e}")

def main():
    """Main cleanup function"""
    print("HealthTwin AI - Test Data Cleanup")
    print("=" * 40)
    
    # Confirm cleanup
    response = input("This will delete all test data. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Cleanup cancelled")
        return
    
    # Create backups
    print("\n📦 Creating backups...")
    create_backup()
    
    # Clean uploads
    print("\n🗑️  Cleaning uploads directory...")
    clean_uploads_directory()
    
    # Clean database
    print("\n🗃️  Cleaning database...")
    clean_test_database_entries()
    
    print("\n✅ Cleanup completed successfully!")
    print("Your HealthTwin AI instance is now ready for fresh data.")

if __name__ == "__main__":
    main()