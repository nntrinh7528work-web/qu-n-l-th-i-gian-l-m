# -*- coding: utf-8 -*-
"""
QUICK FIX SCRIPT
Mục đích: Sửa ngay lỗi "no such table: work_shifts" mà không cần sửa code chính.
Cách dùng: python quick_fix.py
"""

import sqlite3
import os
import glob
from datetime import datetime

def fix_database_file(db_path):
    print(f"🔧 Đang xử lý: {db_path}...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Tạo bảng work_shifts nếu chưa có
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_shifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_date TEXT NOT NULL,
                shift_name TEXT DEFAULT 'Ca 1',
                job_id INTEGER DEFAULT 1,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                break_hours REAL DEFAULT 1.0,
                total_hours REAL NOT NULL,
                overtime_hours REAL DEFAULT 0.0,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Tạo bảng jobs nếu chưa có (để tránh lỗi foreign key giả lập)
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

        # 3. Tạo Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shifts_date ON work_shifts(work_date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shifts_job ON work_shifts(job_id);")
        
        # 4. Kiểm tra và thêm cột thiếu (nếu bảng đã tồn tại từ trước)
        cursor.execute("PRAGMA table_info(work_shifts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'job_id' not in columns:
            print("   - Thêm cột job_id...")
            cursor.execute("ALTER TABLE work_shifts ADD COLUMN job_id INTEGER DEFAULT 1")
            
        if 'overtime_hours' not in columns:
            print("   - Thêm cột overtime_hours...")
            cursor.execute("ALTER TABLE work_shifts ADD COLUMN overtime_hours REAL DEFAULT 0.0")

        conn.commit()
        
        # 5. Migrate dữ liệu từ work_logs (nếu có)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='work_logs'")
        if cursor.fetchone():
            print("   - Tìm thấy bảng work_logs, kiểm tra migration...")
            cursor.execute("SELECT * FROM work_logs")
            logs = cursor.fetchall()
            
            # Lấy columns của work_logs để map đúng
            cursor.execute("PRAGMA table_info(work_logs)")
            log_cols = [col[1] for col in cursor.fetchall()]
            
            count = 0
            for log in logs:
                log_dict = dict(zip(log_cols, log))
                w_date = log_dict['work_date']
                
                # Check exist
                cursor.execute("SELECT 1 FROM work_shifts WHERE work_date = ?", (w_date,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO work_shifts 
                        (work_date, shift_name, job_id, start_time, end_time, break_hours, total_hours, overtime_hours, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        w_date, 
                        'Ca Mặc định', 
                        1, 
                        log_dict.get('start_time', '08:00'),
                        log_dict.get('end_time', '17:00'),
                        log_dict.get('break_hours', 1.0),
                        log_dict.get('total_hours', 8.0),
                        log_dict.get('overtime_hours', 0.0),
                        log_dict.get('notes', '')
                    ))
                    count += 1
            
            if count > 0:
                print(f"   - Đã chuyển {count} bản ghi từ work_logs sang work_shifts.")
                conn.commit()
        
        conn.close()
        print("✅ Đã sửa xong file này!")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def main():
    print("=== WORK HOURS TRACKER QUICK FIX ===\n")
    
    # Quét file trong thư mục hiện tại
    db_files = glob.glob("*.db")
    
    # Quét thư mục data
    if os.path.exists("data"):
        db_files.extend(glob.glob("data/*.db"))
        
    # Quét thư mục user_data
    if os.path.exists("user_data"):
        db_files.extend(glob.glob("user_data/*.db"))
        
    if not db_files:
        # Nếu không tìm thấy file nào, tạo file mặc định
        print("⚠️ Không tìm thấy file database nào.")
        print("🔨 Tạo file mặc định 'work_hours.db'...")
        fix_database_file("work_hours.db")
    else:
        print(f"🔍 Tìm thấy {len(db_files)} file database.")
        for db in db_files:
            fix_database_file(db)
            
    print("\n✅ XONG! Hãy khởi động lại ứng dụng.")
    print("Run: streamlit run app.py")

if __name__ == "__main__":
    main()
