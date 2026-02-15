# -*- coding: utf-8 -*-
"""
Module quản lý cơ sở dữ liệu SQLite cho ứng dụng Quản Lý Giờ Làm (Fixed Version).
Lưu trữ giờ làm (hỗ trợ nhiều ca/ngày), ngày nghỉ, và cài đặt người dùng.
"""

import sqlite3
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple, Union
import os
import sys

# Thiết lập UTF-8 encoding cho Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'
try:
    if sys.stdout and sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr and sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')
except:
    pass

# Đường dẫn database mặc định (sẽ được ghi đè bởi user-specific path)
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "work_hours.db")

def get_db_path() -> str:
    """Lấy đường dẫn database. Ưu tiên database của user nếu đã đăng nhập."""
    try:
        import streamlit as st
        if "user_db_path" in st.session_state and st.session_state["user_db_path"]:
            return st.session_state["user_db_path"]
    except:
        pass
    return DEFAULT_DB_PATH

# Alias cho tương thích
DB_PATH = DEFAULT_DB_PATH

# Cache đơn giản để tối ưu đọc database
_cache = {}
_cache_timeout = 5  # giây


def _get_cache(key):
    """Lấy dữ liệu từ cache nếu còn hiệu lực."""
    if key in _cache:
        data, timestamp = _cache[key]
        if (datetime.now() - timestamp).seconds < _cache_timeout:
            return data
    return None


def _set_cache(key, data):
    """Lưu dữ liệu vào cache."""
    _cache[key] = (data, datetime.now())


def clear_cache():
    """Xóa toàn bộ cache."""
    global _cache
    _cache = {}


def get_connection() -> sqlite3.Connection:
    """Tạo kết nối đến database."""
    db_path = get_db_path()
    # Đảm bảo thư mục tồn tại
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Cho phép truy cập cột theo tên
    return conn


def normalize_date(date_input: Union[date, str]) -> str:
    """Chuyển đổi date input thành ISO string cho database."""
    if isinstance(date_input, date):
        return date_input.isoformat()
    elif isinstance(date_input, str):
        return date_input
    else:
        raise ValueError(f"Invalid date type: {type(date_input)}")


def init_database() -> None:
    """Khởi tạo database và tạo các bảng nếu chưa tồn tại."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Bảng lưu giờ làm hàng ngày (giữ lại để tương thích ngược & migration)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_date DATE NOT NULL UNIQUE,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            break_hours REAL DEFAULT 1.0,
            total_hours REAL NOT NULL,
            overtime_hours REAL DEFAULT 0.0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Bảng lưu công việc và lương giờ
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
    
    # Bảng mới: Lưu các ca làm việc (hỗ trợ nhiều ca/ngày)
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

    # Tạo indexes để tăng performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_shifts_date ON work_shifts(work_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_shifts_job ON work_shifts(job_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_shifts_date_job ON work_shifts(work_date, job_id);")
    
    # Kiểm tra cột (Migration cho database cũ)
    cursor.execute("PRAGMA table_info(work_shifts)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'job_id' not in columns:
        cursor.execute("ALTER TABLE work_shifts ADD COLUMN job_id INTEGER DEFAULT 1")
    if 'overtime_hours' not in columns:
        cursor.execute("ALTER TABLE work_shifts ADD COLUMN overtime_hours REAL DEFAULT 0.0")

    # Bảng lưu khung giờ mẫu (shift presets)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shift_presets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            preset_name TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            break_hours REAL DEFAULT 0.0,
            total_hours REAL NOT NULL,
            job_id INTEGER,
            emoji TEXT DEFAULT '⏰',
            sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL
        )
    """)

    # Bảng lưu ngày nghỉ lễ
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            holiday_date DATE NOT NULL UNIQUE,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Bảng lưu cài đặt
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Thêm cài đặt mặc định nếu chưa có
    default_settings = [
        ("standard_hours", "8.0"),
        ("break_hours", "1.0"),
        ("ot_rate", "1.5"),  # Hệ số lương OT
    ]
    
    for key, value in default_settings:
        cursor.execute("""
            INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
        """, (key, value))
    
    # Thêm công việc mặc định nếu chưa có
    cursor.execute("SELECT COUNT(*) FROM jobs")
    if cursor.fetchone()[0] == 0:
        default_jobs = [
            ('Bệnh viện', 1200, 'Làm việc tại bệnh viện', '#EF4444'),
            ('Kombini', 1100, 'Làm việc tại cửa hàng tiện lợi', '#3B82F6'),
            ('Công việc khác', 1000, 'Các công việc khác', '#6B7280')
        ]
        
        for name, rate, desc, color in default_jobs:
            cursor.execute("""
                INSERT INTO jobs (job_name, hourly_rate, description, color) 
                VALUES (?, ?, ?, ?)
            """, (name, rate, desc, color))
    
    # Thêm khung giờ mẫu mặc định nếu chưa có
    cursor.execute("SELECT COUNT(*) FROM shift_presets")
    if cursor.fetchone()[0] == 0:
        default_presets = [
            ('Ca Sáng 8h', '08:00', '17:00', 1.0, 8.0, '☀️', 1),
            ('Ca Tối 8h', '17:00', '02:00', 1.0, 8.0, '🌙', 2),
            ('Part-time 4h', '17:00', '21:00', 0.0, 4.0, '⏰', 3),
            ('Full Day 10h', '08:00', '19:00', 1.0, 10.0, '🔥', 4),
        ]
        
        for name, start, end, brk, total, emoji, order in default_presets:
            cursor.execute("""
                INSERT INTO shift_presets (preset_name, start_time, end_time, break_hours, total_hours, emoji, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, start, end, brk, total, emoji, order))
    
    conn.commit()
    conn.close()


# Cờ để kiểm soát việc sync (tránh sync quá nhiều)
ENABLE_SYNC = False # Tắt tạm thời do yêu cầu sửa lỗi

def _sync_to_github():
    """Đồng bộ database của user hiện tại lên GitHub (Placeholder)."""
    # TODO: Implement actual sync logic properly later
    pass


# ==================== SHIFT PRESETS (Khung giờ mẫu) ====================

def get_all_presets() -> List[Dict]:
    """Lấy tất cả khung giờ mẫu."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM shift_presets ORDER BY sort_order ASC, id ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception:
        return []


def add_preset(preset_name: str, start_time: str, end_time: str, 
               break_hours: float, total_hours: float, 
               job_id: int = None, emoji: str = "⏰") -> Optional[int]:
    """Thêm khung giờ mẫu mới."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Lấy sort_order tiếp theo
        cursor.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 FROM shift_presets")
        next_order = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO shift_presets (preset_name, start_time, end_time, break_hours, total_hours, job_id, emoji, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (preset_name, start_time, end_time, break_hours, total_hours, job_id, emoji, next_order))
        
        preset_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return preset_id
    except Exception as e:
        print(f"Error adding preset: {e}")
        return None


def update_preset(preset_id: int, **kwargs) -> bool:
    """Cập nhật khung giờ mẫu."""
    try:
        if not kwargs:
            return False
        
        conn = get_connection()
        cursor = conn.cursor()
        
        fields = []
        values = []
        allowed = ['preset_name', 'start_time', 'end_time', 'break_hours', 
                    'total_hours', 'job_id', 'emoji', 'sort_order']
        
        for key, value in kwargs.items():
            if key in allowed:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            conn.close()
            return False
        
        values.append(preset_id)
        cursor.execute(f"UPDATE shift_presets SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        print(f"Error updating preset: {e}")
        return False


def delete_preset(preset_id: int) -> bool:
    """Xóa khung giờ mẫu."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM shift_presets WHERE id = ?", (preset_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        print(f"Error deleting preset: {e}")
        return False


# ==================== JOBS (Công việc và lương giờ) ====================

def add_job(job_name: str, hourly_rate: float, description: str = "", color: str = "#667eea") -> int:
    """Thêm công việc mới. Nếu đã tồn tại, trả về ID của job đó."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Kiểm tra xem job đã tồn tại chưa
        cursor.execute("SELECT id FROM jobs WHERE job_name = ?", (job_name,))
        existing = cursor.fetchone()
        
        if existing:
            # Nếu đã tồn tại, cập nhật lương và trả về ID
            cursor.execute("""
                UPDATE jobs SET hourly_rate = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE job_name = ?
            """, (hourly_rate, description, job_name))
            conn.commit()
            conn.close()
            clear_cache()
            _sync_to_github()
            return existing[0]
        
        # Thêm mới nếu chưa tồn tại
        cursor.execute("""
            INSERT INTO jobs (job_name, hourly_rate, description, color)
            VALUES (?, ?, ?, ?)
        """, (job_name, hourly_rate, description, color))
        
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        clear_cache()
        _sync_to_github()
        return job_id
    except Exception:
        return -1


def update_job(job_id: int, job_name: str, hourly_rate: float, description: str = "", color: str = "#667eea") -> bool:
    """Cập nhật thông tin công việc."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE jobs SET
                job_name = ?,
                hourly_rate = ?,
                description = ?,
                color = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (job_name, hourly_rate, description, color, job_id))
        
        conn.commit()
        conn.close()
        clear_cache()  # Xóa cache khi cập nhật
        _sync_to_github()
        return True
    except Exception:
        return False


def delete_job(job_id: int) -> bool:
    """Xóa công việc."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        
        conn.commit()
        conn.close()
        clear_cache()  # Xóa cache khi xóa
        _sync_to_github()
        return True
    except Exception:
        return False


def get_all_jobs() -> List[Dict]:
    """Lấy tất cả công việc (có cache)."""
    cached = _get_cache('all_jobs')
    if cached is not None:
        return cached
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM jobs ORDER BY job_name ASC")
    rows = cursor.fetchall()
    conn.close()
    
    result = [dict(row) for row in rows]
    _set_cache('all_jobs', result)
    return result


def get_job_by_id(job_id: int) -> Optional[Dict]:
    """Lấy thông tin một công việc."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_ot_rate() -> float:
    """Lấy hệ số lương OT."""
    value = get_setting("ot_rate")
    return float(value) if value else 1.5


def calculate_salary_by_month(year: int, month: int) -> Dict:
    """
    Tính lương theo tháng, phân chia theo từng công việc.
    
    Returns:
        Dict với thông tin lương theo từng công việc và tổng lương
    """
    from datetime import timedelta
    
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Lấy tất cả ca làm việc trong tháng với thông tin công việc
    cursor.execute("""
        SELECT 
            ws.*, 
            j.job_name, 
            j.hourly_rate,
            j.color
        FROM work_shifts ws
        LEFT JOIN jobs j ON ws.job_id = j.id
        WHERE ws.work_date BETWEEN ? AND ?
        ORDER BY ws.work_date ASC
    """, (start_date.isoformat(), end_date.isoformat()))
    
    shifts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Lấy cài đặt
    standard_hours = get_standard_hours()
    ot_rate = get_ot_rate()
    
    # Tính theo từng công việc
    job_salary = {}
    total_hours_all = 0
    total_salary_all = 0
    
    for shift in shifts:
        job_id = shift.get('job_id') or 0
        job_name = shift.get('job_name') or 'Chưa phân loại'
        hourly_rate = shift.get('hourly_rate') or 0
        color = shift.get('color') or '#667eea'
        hours = shift['total_hours']
        
        if job_id not in job_salary:
            job_salary[job_id] = {
                'job_id': job_id,
                'job_name': job_name,
                'hourly_rate': hourly_rate,
                'color': color,
                'total_hours': 0,
                'shift_count': 0,
                'base_salary': 0
            }
        
        job_salary[job_id]['total_hours'] += hours
        job_salary[job_id]['shift_count'] += 1
        job_salary[job_id]['base_salary'] += hours * hourly_rate
        total_hours_all += hours
    
    # Tính OT (tính theo tổng giờ ngày, không theo từng ca)
    daily_hours = {}
    for shift in shifts:
        day = shift['work_date']
        if day not in daily_hours:
            daily_hours[day] = 0
        daily_hours[day] += shift['total_hours']
    
    total_ot_hours = 0
    for day, hours in daily_hours.items():
        if hours > standard_hours:
            total_ot_hours += hours - standard_hours
    
    # Tính tổng lương
    for job_id, data in job_salary.items():
        total_salary_all += data['base_salary']
    
    # Thêm tiền OT
    if total_hours_all > 0 and total_salary_all > 0:
        avg_hourly_rate = total_salary_all / total_hours_all
        ot_bonus = total_ot_hours * avg_hourly_rate * (ot_rate - 1)  # Phần thưởng OT
    else:
        avg_hourly_rate = 0
        ot_bonus = 0
    
    return {
        'year': year,
        'month': month,
        'jobs': list(job_salary.values()),
        'total_hours': round(total_hours_all, 2),
        'total_ot_hours': round(total_ot_hours, 2),
        'total_days': len(daily_hours),
        'base_salary': round(total_salary_all, 0),
        'ot_bonus': round(ot_bonus, 0),
        'total_salary': round(total_salary_all + ot_bonus, 0),
        'ot_rate': ot_rate
    }


# ==================== WORK SHIFTS (Nhiều ca/ngày) ====================

def add_shift(
    work_date: Union[date, str],
    job_id: int,
    start_time: str,
    end_time: str,
    break_hours: float,
    total_hours: float,
    overtime_hours: float = 0.0,
    notes: str = ""
) -> Optional[int]:
    """Thêm ca làm việc mới."""
    try:
        # Validate job_id exists
        job = get_job_by_id(job_id)
        if not job:
            raise ValueError(f"Job ID {job_id} không tồn tại!")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        work_date_str = normalize_date(work_date)
        
        cursor.execute("""
            INSERT INTO work_shifts 
            (work_date, job_id, start_time, end_time, break_hours, 
             total_hours, overtime_hours, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (work_date_str, job_id, start_time, end_time, 
              break_hours, total_hours, overtime_hours, notes))
        
        shift_id = cursor.lastrowid
        conn.commit()
        conn.close()
        _sync_to_github()
        
        return shift_id
    except Exception as e:
        print(f"Error in add_shift: {e}")
        return None

# Alias for backward compatibility
add_work_shift_alias = add_shift 
def add_work_shift(work_date, shift_name, start_time, end_time, break_hours, total_hours, notes="", job_id=None):
    """Legacy wrapper for add_shift."""
    if job_id is None:
        # Default fallback job if not provided
        all_jobs = get_all_jobs()
        if all_jobs:
            job_id = all_jobs[0]['id']
        else:
            return -1
    res = add_shift(work_date, job_id, start_time, end_time, break_hours, total_hours, 0.0, notes)
    return res if res is not None else -1

def update_shift(shift_id: int, **kwargs) -> bool:
    """Cập nhật ca làm việc."""
    try:
        if not kwargs:
            return False
        
        conn = get_connection()
        cursor = conn.cursor()
        
        fields = []
        values = []
        allowed_fields = ['work_date', 'job_id', 'start_time', 'end_time', 
                         'break_hours', 'total_hours', 'overtime_hours', 'notes', 'shift_name']
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                if key == 'work_date':
                    value = normalize_date(value)
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            conn.close()
            return False
        
        values.append(shift_id)
        # Update updated_at automatically
        fields.append("updated_at = CURRENT_TIMESTAMP")
        
        query = f"UPDATE work_shifts SET {', '.join(fields)} WHERE id = ?"
        
        cursor.execute(query, values)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        _sync_to_github()
        
        return success
    except Exception as e:
        print(f"Error in update_shift: {e}")
        return False

# Alias for backward compatibility
def update_work_shift(shift_id, shift_name, start_time, end_time, break_hours, total_hours, notes=""):
    return update_shift(shift_id, shift_name=shift_name, start_time=start_time, end_time=end_time,
                        break_hours=break_hours, total_hours=total_hours, notes=notes)

def delete_shift(shift_id: int) -> bool:
    """Xóa ca làm việc."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM work_shifts WHERE id = ?", (shift_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        _sync_to_github()
        return success
    except Exception as e:
        print(f"Error in delete_shift: {e}")
        return False

# Alias for backward compatibility
delete_work_shift = delete_shift

def get_shifts_by_date(work_date: date) -> List[Dict]:
    """Lấy tất cả ca làm việc của một ngày."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM work_shifts 
        WHERE work_date = ?
        ORDER BY start_time ASC
    """, (work_date.isoformat(),))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_shift_by_id(shift_id: int) -> Optional[Dict]:
    """Lấy thông tin một ca làm việc theo ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM work_shifts WHERE id = ?", (shift_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_daily_summary(work_date: date, standard_hours: float = 8.0) -> Dict:
    """
    Lấy tổng hợp giờ làm của một ngày (tất cả các ca).
    """
    shifts = get_shifts_by_date(work_date)
    
    if not shifts:
        return {
            "work_date": work_date.isoformat(),
            "total_hours": 0.0,
            "overtime_hours": 0.0,
            "shift_count": 0,
            "shifts": []
        }
    
    total_hours = sum(s['total_hours'] for s in shifts)
    overtime_hours = max(0, total_hours - standard_hours)
    
    return {
        "work_date": work_date.isoformat(),
        "total_hours": round(total_hours, 2),
        "overtime_hours": round(overtime_hours, 2),
        "shift_count": len(shifts),
        "shifts": shifts
    }


def get_shifts_by_range(start_date: date, end_date: date) -> List[Dict]:
    """Lấy tất cả ca làm việc trong khoảng thời gian."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM work_shifts 
            WHERE work_date BETWEEN ? AND ?
            ORDER BY work_date ASC, start_time ASC
        """, (start_date.isoformat(), end_date.isoformat()))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error in get_shifts_by_range: {e}")
        return []


def get_daily_summaries_by_range(start_date: date, end_date: date, standard_hours: float = 8.0) -> List[Dict]:
    """
    Lấy tổng hợp giờ làm theo ngày trong khoảng thời gian.
    Gộp các ca trong cùng một ngày.
    """
    try:
        shifts = get_shifts_by_range(start_date, end_date)
        
        if not shifts:
            return []
        
        # Gộp theo ngày
        daily_data = {}
        for shift in shifts:
            work_date = shift['work_date']
            if work_date not in daily_data:
                daily_data[work_date] = {
                    "work_date": work_date,
                    "total_hours": 0.0,
                    "shift_count": 0,
                    "shifts": [],
                    "start_time": shift['start_time'],  # Ca đầu tiên
                    "end_time": shift['end_time'],
                    "break_hours": 0.0,
                    "notes": ""
                }
            
            daily_data[work_date]["total_hours"] += shift['total_hours']
            daily_data[work_date]["break_hours"] += shift['break_hours']
            daily_data[work_date]["shift_count"] += 1
            daily_data[work_date]["shifts"].append(shift)
            daily_data[work_date]["end_time"] = shift['end_time']  # Ca cuối cùng
            
            # Gộp notes
            if shift['notes']:
                if daily_data[work_date]["notes"]:
                    daily_data[work_date]["notes"] += f"; {shift['notes']}"
                else:
                    daily_data[work_date]["notes"] = shift['notes']
        
        # Tính overtime cho mỗi ngày
        result = []
        for work_date, data in daily_data.items():
            data["total_hours"] = round(data["total_hours"], 2)
            data["overtime_hours"] = round(max(0, data["total_hours"] - standard_hours), 2)
            result.append(data)
        
        # Sắp xếp theo ngày
        result.sort(key=lambda x: x["work_date"])
        return result
    except Exception as e:
        print(f"Error in get_daily_summaries_by_range: {e}")
        return []


def get_daily_summaries_by_month(year: int, month: int, standard_hours: float = 8.0) -> List[Dict]:
    """Lấy tổng hợp giờ làm theo ngày trong một tháng."""
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    from datetime import timedelta
    end_date = end_date - timedelta(days=1)
    
    return get_daily_summaries_by_range(start_date, end_date, standard_hours)


# ==================== WORK LOGS (Backward Compatibility) ====================

def get_work_logs_by_range(start_date: date, end_date: date) -> List[Dict]:
    """Lấy danh sách giờ làm trong khoảng thời gian (kết hợp cả 2 bảng)."""
    # Chỉ dùng work_shifts vì đã migrate
    return get_daily_summaries_by_range(start_date, end_date)

def get_work_logs_by_month(year: int, month: int) -> List[Dict]:
    """Lấy danh sách giờ làm trong một tháng."""
    return get_daily_summaries_by_month(year, month)

def delete_work_log(work_date: date) -> bool:
    """Xóa giờ làm của một ngày."""
    try:
        shifts = get_shifts_by_date(work_date)
        for shift in shifts:
            delete_shift(shift['id'])
        
        # Cleanup legacy table too
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM work_logs WHERE work_date = ?", (work_date.isoformat(),))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


# ==================== HOLIDAYS ====================

def add_holiday(holiday_date: date, description: str) -> bool:
    """Thêm ngày nghỉ lễ."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO holidays (holiday_date, description)
            VALUES (?, ?)
        """, (holiday_date.isoformat(), description))
        
        conn.commit()
        conn.close()
        _sync_to_github()
        return True
    except Exception as e:
        print(f"Lỗi khi thêm ngày nghỉ: {e}")
        return False


def remove_holiday(holiday_date: date) -> bool:
    """Xóa ngày nghỉ lễ."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM holidays WHERE holiday_date = ?", 
                      (holiday_date.isoformat(),))
        
        conn.commit()
        conn.close()
        _sync_to_github()
        return True
    except Exception as e:
        print(f"Lỗi khi xóa ngày nghỉ: {e}")
        return False


def get_all_holidays() -> List[Dict]:
    """Lấy tất cả ngày nghỉ lễ."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM holidays ORDER BY holiday_date ASC")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_holidays_by_year(year: int) -> List[Dict]:
    """Lấy ngày nghỉ lễ trong một năm."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM holidays 
        WHERE strftime('%Y', holiday_date) = ?
        ORDER BY holiday_date ASC
    """, (str(year),))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def is_holiday(check_date: date) -> Tuple[bool, str]:
    """Kiểm tra xem một ngày có phải ngày nghỉ không."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT description FROM holidays WHERE holiday_date = ?
    """, (check_date.isoformat(),))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return True, row['description']
    return False, ""


# ==================== SETTINGS ====================

def get_setting(key: str) -> Optional[str]:
    """Lấy giá trị một cài đặt."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row['value']
    return None


def update_setting(key: str, value: str) -> bool:
    """Cập nhật một cài đặt."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET 
            value = excluded.value,
            updated_at = CURRENT_TIMESTAMP
        """, (key, value))
        
        conn.commit()
        conn.close()
        _sync_to_github()
        return True
    except Exception as e:
        print(f"Lỗi khi cập nhật cài đặt: {e}")
        return False


def get_standard_hours() -> float:
    """Lấy số giờ làm chuẩn."""
    value = get_setting("standard_hours")
    return float(value) if value else 8.0


def get_default_break_hours() -> float:
    """Lấy số giờ nghỉ mặc định."""
    value = get_setting("break_hours")
    return float(value) if value else 1.0
