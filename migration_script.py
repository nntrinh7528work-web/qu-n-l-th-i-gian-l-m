# -*- coding: utf-8 -*-
"""
Migration Script for Work Hours Tracker.
Migrates data from legacy 'work_logs' table to new 'work_shifts' table.
"""

import sqlite3
import os
import sys
from datetime import datetime

# Import database path logic
try:
    import database
except ImportError:
    print("❌ Cannot import database.py. Please run this script from the project root.")
    sys.exit(1)

def migrate_database(db_path):
    """Migrate data for a specific database file."""
    if not os.path.exists(db_path):
        print(f"⚠️ Database file not found: {db_path}")
        return

    print(f"\n🔄 Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Ensure work_shifts table exists (it should, but just in case)
        # We rely on database.init_database() usually, but let's be safe
        cursor.execute("PRAGMA table_info(work_logs)")
        if not cursor.fetchall():
            print("ℹ️ Table 'work_logs' does not exist. Nothing to migrate.")
            conn.close()
            return

        cursor.execute("PRAGMA table_info(work_shifts)")
        if not cursor.fetchall():
            print("❌ Table 'work_shifts' does not exist. Please run the app fully once to initialize DB schema.")
            conn.close()
            return
            
        # 2. Get all data from work_logs
        cursor.execute("SELECT * FROM work_logs")
        logs = cursor.fetchall()
        
        if not logs:
            print("ℹ️ No data in 'work_logs' to migrate.")
            conn.close()
            return
            
        print(f"found {len(logs)} records in work_logs.")
        
        # 3. Get default job_id (Create one if not exists)
        cursor.execute("SELECT id FROM jobs LIMIT 1")
        job_row = cursor.fetchone()
        if job_row:
            default_job_id = job_row['id']
        else:
            print("Constructor default job...")
            cursor.execute("INSERT INTO jobs (job_name, hourly_rate) VALUES (?, ?)", ('Default Job', 1000.0))
            default_job_id = cursor.lastrowid
            
        migrated_count = 0
        skipped_count = 0
        
        # 4. Migrate each log to work_shifts
        for log in logs:
            work_date = log['work_date']
            
            # Check if this date already exists in work_shifts
            cursor.execute("SELECT id FROM work_shifts WHERE work_date = ?", (work_date,))
            if cursor.fetchone():
                skipped_count += 1
                continue
            
            # Map fields
            # work_logs: id, work_date, start_time, end_time, break_hours, total_hours, overtime_hours, notes, ...
            # work_shifts: id, work_date, shift_name, job_id, start_time, end_time, break_hours, total_hours, ...
            
            try:
                cursor.execute("""
                    INSERT INTO work_shifts 
                    (work_date, shift_name, job_id, start_time, end_time, 
                     break_hours, total_hours, overtime_hours, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log['work_date'],
                    'Ca Mặc định',
                    default_job_id,
                    log['start_time'],
                    log['end_time'],
                    log['break_hours'],
                    log['total_hours'],
                    log['overtime_hours'],
                    log['notes'],
                    log['created_at']
                ))
                migrated_count += 1
            except Exception as e:
                print(f"❌ Error migrating record {work_date}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Migration complete for {db_path}")
        print(f"   - Migrated: {migrated_count}")
        print(f"   - Skipped (Already existed): {skipped_count}")
        
    except Exception as e:
        print(f"❌ Critical error migrating {db_path}: {e}")

if __name__ == "__main__":
    # 1. Migrate default database
    default_db = database.DEFAULT_DB_PATH
    migrate_database(default_db)
    
    # 2. Check for other .db files in user_data or current dir
    print("\n🔍 Scanning for other database files...")
    
    # Check current directory
    for file in os.listdir("."):
        if file.endswith(".db") and file != "work_hours.db":
            migrate_database(os.path.abspath(file))
            
    # Check data directory if exists
    if os.path.exists("data"):
        for file in os.listdir("data"):
            if file.endswith(".db"):
                migrate_database(os.path.join("data", file))
                
    # Check user_data directory
    if os.path.exists("user_data"):
        for file in os.listdir("user_data"):
            if file.endswith(".db"):
                migrate_database(os.path.join("user_data", file))
                
    print("\n🎉 All done!")
