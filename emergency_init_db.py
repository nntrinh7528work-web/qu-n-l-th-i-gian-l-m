# -*- coding: utf-8 -*-
"""
Script khẩn cấp để init lại database và tạo bảng work_shifts.
"""
import os
import sys

# Thêm path hiện tại
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database

print("=== KHỞI TẠO LẠI DATABASE ===")
print(f"Database path: {database.get_db_path()}")

# Force init database
database.init_database()

print("✅ Đã khởi tạo lại database!")

# Kiểm tra các bảng
conn = database.get_connection()
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("\n📚 Các bảng trong database:")
for table in tables:
    print(f"  - {table[0]}")
    
# Kiểm tra cụ thể work_shifts
cursor.execute("PRAGMA table_info(work_shifts)")
columns = cursor.fetchall()

print("\n📋 Cột trong bảng work_shifts:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

conn.close()

print("\n✅ HOÀN TẤT!")
