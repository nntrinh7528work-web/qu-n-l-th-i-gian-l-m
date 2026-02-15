# -*- coding: utf-8 -*-
"""
Database Wrapper - Luôn sử dụng SQLite trực tiếp (không cần đăng nhập).
Import module này thay vì import trực tiếp database.py
"""

from datetime import date
from typing import List, Dict, Optional, Union

# Import SQLite module
import database as sqlite_db


def is_cloud_mode() -> bool:
    """Luôn trả về False vì không dùng Supabase khi không có login."""
    return False


# ==================== JOBS ====================

def get_all_jobs() -> List[Dict]:
    """Lấy tất cả công việc."""
    return sqlite_db.get_all_jobs()


def add_job(job_name: str, hourly_rate: float, description: str = "", color: str = "#667eea") -> Optional[int]:
    """Thêm công việc mới."""
    return sqlite_db.add_job(job_name, hourly_rate, description, color)


def update_job(job_id: int, job_name: str, hourly_rate: float, description: str = "", color: str = "#667eea") -> bool:
    """Cập nhật công việc."""
    return sqlite_db.update_job(job_id, job_name, hourly_rate, description, color)


def delete_job(job_id: int) -> bool:
    """Xóa công việc."""
    return sqlite_db.delete_job(job_id)


def get_job_by_id(job_id: int) -> Optional[Dict]:
    """Lấy thông tin công việc theo ID."""
    return sqlite_db.get_job_by_id(job_id)


# ==================== WORK SHIFTS ====================

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
    return sqlite_db.add_shift(
        work_date, job_id, start_time, end_time,
        break_hours, total_hours, overtime_hours, notes
    )

def update_shift(shift_id: int, **kwargs) -> bool:
    """Cập nhật ca làm việc."""
    return sqlite_db.update_shift(shift_id, **kwargs)

def delete_shift(shift_id: int) -> bool:
    """Xóa ca làm việc."""
    return sqlite_db.delete_shift(shift_id)

def get_shift_by_id(shift_id: int) -> Optional[Dict]:
    """Lấy shift theo ID."""
    return sqlite_db.get_shift_by_id(shift_id)

# Aliases for legacy compatibility
add_work_shift = sqlite_db.add_work_shift
update_work_shift = sqlite_db.update_work_shift
delete_work_shift = sqlite_db.delete_work_shift


def get_shifts_by_date(work_date: date) -> List[Dict]:
    """Lấy các ca làm việc theo ngày."""
    return sqlite_db.get_shifts_by_date(work_date)


def get_shifts_by_range(start_date: date, end_date: date) -> List[Dict]:
    """Lấy các ca làm việc trong khoảng thời gian."""
    return sqlite_db.get_shifts_by_range(start_date, end_date)


def get_daily_summary(work_date: date, standard_hours: float = 8.0) -> Dict:
    """Lấy tổng hợp giờ làm của một ngày."""
    return sqlite_db.get_daily_summary(work_date, standard_hours)


def get_daily_summaries_by_range(start_date: date, end_date: date, standard_hours: float = 8.0) -> List[Dict]:
    """Lấy tổng hợp giờ làm theo ngày trong khoảng thời gian."""
    return sqlite_db.get_daily_summaries_by_range(start_date, end_date, standard_hours)


def get_daily_summaries_by_month(year: int, month: int, standard_hours: float = 8.0) -> List[Dict]:
    """Lấy tổng hợp giờ làm theo ngày trong một tháng."""
    return sqlite_db.get_daily_summaries_by_month(year, month, standard_hours)


# ==================== HOLIDAYS ====================

def add_holiday(holiday_date: date, description: str) -> bool:
    """Thêm ngày nghỉ."""
    return sqlite_db.add_holiday(holiday_date, description)


def remove_holiday(holiday_date: date) -> bool:
    """Xóa ngày nghỉ."""
    return sqlite_db.remove_holiday(holiday_date)


def get_all_holidays() -> List[Dict]:
    """Lấy tất cả ngày nghỉ."""
    return sqlite_db.get_all_holidays()


def get_holidays_by_year(year: int) -> List[Dict]:
    """Lấy danh sách ngày nghỉ trong năm."""
    return sqlite_db.get_holidays_by_year(year)


def is_holiday(check_date: date) -> tuple:
    """Kiểm tra ngày nghỉ."""
    return sqlite_db.is_holiday(check_date)


# ==================== SETTINGS ====================

def get_setting(key: str) -> Optional[str]:
    """Lấy cài đặt."""
    return sqlite_db.get_setting(key)


def update_setting(key: str, value: str) -> bool:
    """Cập nhật cài đặt."""
    return sqlite_db.update_setting(key, value)


def get_standard_hours() -> float:
    """Lấy số giờ chuẩn."""
    return sqlite_db.get_standard_hours()


def get_default_break_hours() -> float:
    """Lấy giờ nghỉ mặc định."""
    return sqlite_db.get_default_break_hours()


def get_ot_rate() -> float:
    """Lấy hệ số OT."""
    return sqlite_db.get_ot_rate()


# ==================== DATABASE INIT ====================

def init_database():
    """Khởi tạo database."""
    try:
        sqlite_db.init_database()
    except Exception as e:
        print(f"SQLite init warning: {e}")


def clear_cache():
    """Xóa cache."""
    sqlite_db.clear_cache()


# ==================== COMPATIBILITY ====================

def get_work_logs_by_month(year: int, month: int) -> List[Dict]:
    """Compatibility wrapper for get_work_logs_by_month."""
    return sqlite_db.get_work_logs_by_month(year, month)


def get_work_logs_by_range(start_date: date, end_date: date) -> List[Dict]:
    """Compatibility wrapper for get_work_logs_by_range."""
    return sqlite_db.get_work_logs_by_range(start_date, end_date)


def delete_work_log(work_date: date) -> bool:
    """Delete all work logs/shifts for a date."""
    return sqlite_db.delete_work_log(work_date)
