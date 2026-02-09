def add_shift(
    work_date,
    job_id,
    start_time,
    end_time,
    break_hours,
    total_hours,
    overtime_hours=0.0,
    notes=""
):
    """Thêm ca làm việc mới (Patch)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Convert date to string
        if hasattr(work_date, 'isoformat'):
            work_date = work_date.isoformat()
            
        cursor.execute("""
            INSERT INTO work_shifts 
            (work_date, job_id, start_time, end_time, break_hours, 
             total_hours, overtime_hours, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (work_date, job_id, start_time, end_time, 
              break_hours, total_hours, overtime_hours, notes))
        
        shift_id = cursor.lastrowid
        conn.commit()
        conn.close()
        _sync_to_github()
        return shift_id
    except Exception as e:
        print(f"Error in add_shift: {e}")
        return None

def update_shift(shift_id, **kwargs):
    """Cập nhật ca làm việc (Patch)."""
    try:
        if not kwargs:
            return False
            
        conn = get_connection()
        cursor = conn.cursor()
        
        fields = []
        values = []
        allowed = ['work_date', 'job_id', 'start_time', 'end_time', 
                  'break_hours', 'total_hours', 'overtime_hours', 'notes', 'shift_name']
                  
        for k, v in kwargs.items():
            if k in allowed:
                if k == 'work_date' and hasattr(v, 'isoformat'):
                    v = v.isoformat()
                fields.append(f"{k} = ?")
                values.append(v)
                
        if not fields:
            conn.close()
            return False
            
        values.append(shift_id)
        fields.append("updated_at = CURRENT_TIMESTAMP")
        
        sql = f"UPDATE work_shifts SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(sql, values)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        _sync_to_github()
        return success
    except Exception as e:
        print(f"Error: {e}")
        return False

def delete_shift(shift_id):
    """Xóa ca làm việc (Patch)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM work_shifts WHERE id = ?", (shift_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        _sync_to_github()
        return success
    except Exception as e:
        print(f"Error: {e}")
        return False

def get_shift_by_id(shift_id):
    """Lấy thông tin 1 shift (Patch)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM work_shifts WHERE id = ?", (shift_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None

def get_shifts_by_range(start_date, end_date):
    """Lấy shifts trong khoảng thời gian có error handling (Patch)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        s_date = start_date.isoformat() if hasattr(start_date, 'isoformat') else start_date
        e_date = end_date.isoformat() if hasattr(end_date, 'isoformat') else end_date
        
        cursor.execute("""
            SELECT * FROM work_shifts 
            WHERE work_date BETWEEN ? AND ?
            ORDER BY work_date ASC, start_time ASC
        """, (s_date, e_date))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error: {e}")
        return []

# === Add to init_database ===
# Copy đoạn dưới vào cuối hàm init_database()
"""
    # Create work_shifts table
    cursor.execute('''
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
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    ''')
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_shifts_date ON work_shifts(work_date);")
"""
