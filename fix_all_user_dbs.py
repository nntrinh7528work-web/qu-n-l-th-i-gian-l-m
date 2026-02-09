# -*- coding: utf-8 -*-
"""
Script để init TẤT CẢ user databases trong thư mục user_data.
"""
import os
import sys
import sqlite3

# Fix UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

USER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_data")

print("=== INIT ALL USER DATABASES ===")
print(f"User data directory: {USER_DATA_DIR}")

if not os.path.exists(USER_DATA_DIR):
    print("WARNING: user_data directory does not exist!")
    os.makedirs(USER_DATA_DIR)
    print("Created user_data directory")

# Find all .db files
db_files = [f for f in os.listdir(USER_DATA_DIR) if f.endswith('.db')]

print(f"\nFound {len(db_files)} database files:")
for db_file in db_files:
    print(f"  - {db_file}")

# Init each database
for db_file in db_files:
    db_path = os.path.join(USER_DATA_DIR, db_file)
    print(f"\nInitializing database: {db_file}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if work_shifts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='work_shifts'")
        if cursor.fetchone():
            print(f"  OK: work_shifts table already exists!")
        else:
            print(f"  WARNING: work_shifts table does not exist, creating...")
            
            # Create work_shifts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS work_shifts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_date TEXT NOT NULL,
                    shift_name TEXT DEFAULT 'Ca 1',
                    job_id INTEGER NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    break_hours REAL DEFAULT 1.0,
                    total_hours REAL NOT NULL,
                    overtime_hours REAL DEFAULT 0.0,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE RESTRICT
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_shifts_date ON work_shifts(work_date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_shifts_job ON work_shifts(job_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_shifts_date_job ON work_shifts(work_date, job_id);")
            
            conn.commit()
            print(f"  OK: Created work_shifts table!")
        
        conn.close()
    except Exception as e:
        print(f"  ERROR: {e}")

print("\nCOMPLETE!")
