# -*- coding: utf-8 -*-
"""
Module quản lý cơ sở dữ liệu SQLite cho ứng dụng Quản Lý Giờ Làm.
Lưu trữ giờ làm (hỗ trợ nhiều ca/ngày), ngày nghỉ, và cài đặt người dùng.
"""

import sqlite3
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
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


def init_database() -> None:
    """Khởi tạo database và tạo các bảng nếu chưa tồn tại."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Bảng lưu giờ làm hàng ngày (giữ lại để tương thích ngược)
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
            work_date DATE NOT NULL,
            shift_name TEXT DEFAULT 'Ca 1',
            job_id INTEGER,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            break_hours REAL DEFAULT 0.0,
            total_hours REAL NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)
    
    # Kiểm tra và thêm cột job_id nếu chưa có (migration)
    cursor.execute("PRAGMA table_info(work_shifts)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'job_id' not in columns:
        cursor.execute("ALTER TABLE work_shifts ADD COLUMN job_id INTEGER")
    
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
    
    conn.commit()
    conn.close()


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
    # Lấy tổng giờ theo ngày
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
    
    # Thêm tiền OT (tính dựa trên lương trung bình các công việc)
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

def add_work_shift(
    work_date: date,
    shift_name: str,
    start_time: str,
    end_time: str,
    break_hours: float,
    total_hours: float,
    notes: str = "",
    job_id: int = None
) -> int:
    """
    Thêm một ca làm việc mới.
    
    Args:
        work_date: Ngày làm việc
        shift_name: Tên ca (ví dụ: "Ca sáng", "Ca tối")
        start_time: Giờ bắt đầu (HH:MM)
        end_time: Giờ kết thúc (HH:MM)
        break_hours: Số giờ nghỉ
        total_hours: Tổng giờ làm ca này
        notes: Ghi chú (tùy chọn)
        job_id: ID công việc (tùy chọn)
    
    Returns:
        ID của ca làm việc mới, -1 nếu lỗi
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO work_shifts 
                (work_date, shift_name, job_id, start_time, end_time, break_hours, total_hours, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (work_date.isoformat(), shift_name, job_id, start_time, end_time, 
              break_hours, total_hours, notes))
        
        shift_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return shift_id
    except Exception as e:
        print(f"Lỗi khi thêm ca làm việc: {e}")
        return -1


def update_work_shift(
    shift_id: int,
    shift_name: str,
    start_time: str,
    end_time: str,
    break_hours: float,
    total_hours: float,
    notes: str = ""
) -> bool:
    """Cập nhật một ca làm việc."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE work_shifts SET
                shift_name = ?,
                start_time = ?,
                end_time = ?,
                break_hours = ?,
                total_hours = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (shift_name, start_time, end_time, break_hours, total_hours, notes, shift_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Lỗi khi cập nhật ca làm việc: {e}")
        return False


def delete_work_shift(shift_id: int) -> bool:
    """Xóa một ca làm việc theo ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM work_shifts WHERE id = ?", (shift_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Lỗi khi xóa ca làm việc: {e}")
        return False


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
    
    Returns:
        Dict với total_hours, overtime_hours, shift_count, shifts
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


def get_daily_summaries_by_range(start_date: date, end_date: date, standard_hours: float = 8.0) -> List[Dict]:
    """
    Lấy tổng hợp giờ làm theo ngày trong khoảng thời gian.
    Gộp các ca trong cùng một ngày.
    """
    shifts = get_shifts_by_range(start_date, end_date)
    
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


# ==================== WORK LOGS (Tương thích ngược) ====================

def save_work_log(
    work_date: date,
    start_time: str,
    end_time: str,
    break_hours: float,
    total_hours: float,
    overtime_hours: float,
    notes: str = ""
) -> bool:
    """
    Lưu hoặc cập nhật giờ làm cho một ngày (tương thích ngược).
    Phương thức này sẽ tạo/cập nhật cả work_logs và work_shifts.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Lưu vào work_logs (tương thích ngược)
        cursor.execute("""
            INSERT INTO work_logs 
                (work_date, start_time, end_time, break_hours, total_hours, overtime_hours, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(work_date) DO UPDATE SET
                start_time = excluded.start_time,
                end_time = excluded.end_time,
                break_hours = excluded.break_hours,
                total_hours = excluded.total_hours,
                overtime_hours = excluded.overtime_hours,
                notes = excluded.notes,
                updated_at = CURRENT_TIMESTAMP
        """, (work_date.isoformat(), start_time, end_time, break_hours, 
              total_hours, overtime_hours, notes))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Lỗi khi lưu giờ làm: {e}")
        return False


def get_work_log(work_date: date) -> Optional[Dict]:
    """Lấy giờ làm của một ngày cụ thể (ưu tiên từ work_shifts nếu có)."""
    # Kiểm tra work_shifts trước
    shifts = get_shifts_by_date(work_date)
    if shifts:
        standard_hours = get_standard_hours()
        summary = get_daily_summary(work_date, standard_hours)
        return {
            "work_date": work_date.isoformat(),
            "start_time": shifts[0]['start_time'],
            "end_time": shifts[-1]['end_time'],
            "break_hours": sum(s['break_hours'] for s in shifts),
            "total_hours": summary['total_hours'],
            "overtime_hours": summary['overtime_hours'],
            "notes": "; ".join(s['notes'] for s in shifts if s['notes']),
            "shift_count": len(shifts),
            "shifts": shifts
        }
    
    # Fallback: Lấy từ work_logs
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM work_logs WHERE work_date = ?
    """, (work_date.isoformat(),))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        result = dict(row)
        result['shift_count'] = 1
        result['shifts'] = []
        return result
    return None


def get_work_logs_by_range(start_date: date, end_date: date) -> List[Dict]:
    """Lấy danh sách giờ làm trong khoảng thời gian (kết hợp cả 2 bảng)."""
    standard_hours = get_standard_hours()
    
    # Lấy từ work_shifts (ưu tiên)
    daily_summaries = get_daily_summaries_by_range(start_date, end_date, standard_hours)
    shift_dates = {s['work_date'] for s in daily_summaries}
    
    # Lấy từ work_logs cho các ngày chưa có trong shifts
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM work_logs 
        WHERE work_date BETWEEN ? AND ?
        ORDER BY work_date ASC
    """, (start_date.isoformat(), end_date.isoformat()))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Thêm các ngày từ work_logs chưa có trong shifts
    for row in rows:
        if row['work_date'] not in shift_dates:
            log_dict = dict(row)
            log_dict['shift_count'] = 1
            daily_summaries.append(log_dict)
    
    # Sắp xếp lại
    daily_summaries.sort(key=lambda x: x['work_date'])
    return daily_summaries


def get_work_logs_by_month(year: int, month: int) -> List[Dict]:
    """Lấy danh sách giờ làm trong một tháng."""
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    from datetime import timedelta
    end_date = end_date - timedelta(days=1)
    
    return get_work_logs_by_range(start_date, end_date)


def delete_work_log(work_date: date) -> bool:
    """Xóa giờ làm của một ngày (cả work_logs và work_shifts)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Xóa từ work_logs
        cursor.execute("DELETE FROM work_logs WHERE work_date = ?", 
                      (work_date.isoformat(),))
        
        # Xóa từ work_shifts
        cursor.execute("DELETE FROM work_shifts WHERE work_date = ?", 
                      (work_date.isoformat(),))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Lỗi khi xóa giờ làm: {e}")
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


def get_all_settings() -> Dict[str, str]:
    """Lấy tất cả cài đặt."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    
    return {row['key']: row['value'] for row in rows}


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


# Note: Database khởi tạo được gọi trong app.py sau khi user đăng nhập
# để đảm bảo sử dụng đúng database path của user
