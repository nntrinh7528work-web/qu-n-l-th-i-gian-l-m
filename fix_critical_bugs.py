# -*- coding: utf-8 -*-
"""
FIX CRITICAL BUGS SCRIPT
Mục đích: Script sửa lỗi toàn diện và migrate dữ liệu an toàn.
Cách dùng: python fix_critical_bugs.py [optional_path_to_db]
"""

import sqlite3
import os
import sys
import shutil
from datetime import datetime

def backup_file(filepath):
    """Tạo backup file db."""
    if not os.path.exists(filepath):
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.{timestamp}.bak"
    print(f"📦 Đang tạo backup: {backup_path}")
    try:
        shutil.copy2(filepath, backup_path)
        return True
    except Exception as e:
        print(f"❌ Lỗi backup: {e}")
        return False

def check_structure(cursor):
    """Kiểm tra cấu trúc bảng."""
    issues = []
    
    # Check work_shifts
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='work_shifts'")
    if not cursor.fetchone():
        issues.append("MISSING_TABLE_WORK_SHIFTS")
    else:
        # Check columns
        cursor.execute("PRAGMA table_info(work_shifts)")
        cols = {col[1]: col for col in cursor.fetchall()}
        
        if 'job_id' not in cols:
            issues.append("MISSING_COLUMN_JOB_ID")
        if 'overtime_hours' not in cols:
            issues.append("MISSING_COLUMN_OVERTIME")
            
    # Check jobs
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
    if not cursor.fetchone():
        issues.append("MISSING_TABLE_JOBS")
        
    return issues

def apply_fixes(db_path):
    print(f"\n🛠️ Đang kiểm tra: {db_path}")
    
    # Backup trước
    backup_file(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    issues = check_structure(cursor)
    
    if not issues:
        print("✅ Database này ok, không cần sửa lỗi cấu trúc.")
    else:
        print(f"⚠️ Phát hiện vấn đề: {', '.join(issues)}")
        
        if "MISSING_TABLE_JOBS" in issues:
            print("   + Tạo bảng 'jobs'...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_name TEXT NOT NULL UNIQUE,
                    hourly_rate REAL NOT NULL DEFAULT 0.0,
                    description TEXT,
                    color TEXT DEFAULT '#667eea',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Add default jobs
            cursor.execute("""
                INSERT OR IGNORE INTO jobs (job_name, hourly_rate, color) 
                VALUES 
                ('Công việc chính', 1000, '#3B82F6'),
                ('Làm thêm', 1250, '#10B981')
            """)
            
        if "MISSING_TABLE_WORK_SHIFTS" in issues:
            print("   + Tạo bảng 'work_shifts'...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS work_shifts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_date TEXT NOT NULL,
                    shift_name TEXT DEFAULT 'Ca 1',
                    job_id INTEGER NOT NULL DEFAULT 1,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    break_hours REAL DEFAULT 1.0,
                    total_hours REAL NOT NULL,
                    overtime_hours REAL DEFAULT 0.0,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES jobs(id)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_shifts_date ON work_shifts(work_date);")
            
        if "MISSING_COLUMN_JOB_ID" in issues:
            print("   + Thêm cột 'job_id'...")
            cursor.execute("ALTER TABLE work_shifts ADD COLUMN job_id INTEGER DEFAULT 1")
            
        if "MISSING_COLUMN_OVERTIME" in issues:
            print("   + Thêm cột 'overtime_hours'...")
            cursor.execute("ALTER TABLE work_shifts ADD COLUMN overtime_hours REAL DEFAULT 0.0")
            
        conn.commit()
        print("✅ Đã sửa xong cấu trúc.")

    # Migration Check
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='work_logs'")
    if cursor.fetchone():
        cursor.execute("SELECT COUNT(*) FROM work_logs")
        log_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM work_shifts")
        shift_count = cursor.fetchone()[0]
        
        if log_count > 0 and shift_count == 0:
            print(f"\n🔄 Cần migrate {log_count} bản ghi từ work_logs sang work_shifts...")
            cursor.execute("PRAGMA table_info(work_logs)")
            cols = [c[1] for c in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM work_logs")
            logs = cursor.fetchall()
            
            migrated = 0
            for log in logs:
                d = dict(zip(cols, log))
                cursor.execute("""
                    INSERT INTO work_shifts 
                    (work_date, shift_name, job_id, start_time, end_time, break_hours, total_hours, overtime_hours, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    d['work_date'], 'Ca cũ', 1, 
                    d.get('start_time'), d.get('end_time'),
                    d.get('break_hours'), d.get('total_hours'),
                    d.get('overtime_hours'), d.get('notes')
                ))
                migrated += 1
            
            conn.commit()
            print(f"✅ Đã migrate xong {migrated} bản ghi.")
            
    conn.close()

def main():
    if len(sys.argv) > 1:
        # User provided a path
        path = sys.argv[1]
        if os.path.isdir(path):
            # Process dir
            for root, dirs, files in os.walk(path):
                for f in files:
                    if f.endswith(".db"):
                        apply_fixes(os.path.join(root, f))
        else:
            if os.path.exists(path):
                apply_fixes(path)
            else:
                print(f"❌ File không tồn tại: {path}")
    else:
        # Default scan
        print("🔍 Đang quét tìm database...")
        found = False
        
        # Check explicit files
        defaults = ["work_hours.db", "data/work_hours.db"]
        for d in defaults:
            if os.path.exists(d):
                apply_fixes(d)
                found = True
        
        # Scan folders
        for folder in ["data", "user_data"]:
            if os.path.exists(folder):
                for f in os.listdir(folder):
                    if f.endswith(".db"):
                        apply_fixes(os.path.join(folder, f))
                        found = True
        
        if not found:
            print("⚠️ Không tìm thấy database nào. Tạo mới 'work_hours.db'...")
            apply_fixes("work_hours.db")

if __name__ == "__main__":
    main()
