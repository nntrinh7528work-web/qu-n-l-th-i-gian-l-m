
import database as db
from datetime import date
import os

print(f"DB Path: {db.get_db_path()}")

try:
    print("Initializing database...")
    db.init_database()
    print("Database initialized.")
except Exception as e:
    print(f"Error init database: {e}")

try:
    print("Checking tables...")
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", [t[0] for t in tables])
    conn.close()
except Exception as e:
    print(f"Error checking tables: {e}")

try:
    print("Testing query...")
    start = date(2024, 1, 1)
    end = date(2024, 1, 31)
    shifts = db.get_shifts_by_range(start, end)
    print(f"Query successful. Found {len(shifts)} shifts.")
except Exception as e:
    print(f"Error querying: {e}")
    import traceback
    traceback.print_exc()
