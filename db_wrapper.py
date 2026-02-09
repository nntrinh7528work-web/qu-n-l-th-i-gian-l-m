# -*- coding: utf-8 -*-
"""
Database Wrapper - Tự động chọn Supabase hoặc SQLite.
Import module này thay vì import trực tiếp database.py hoặc supabase_db.py
"""

import streamlit as st
from datetime import date
from typing import List, Dict, Optional, Union

# Thử import Supabase
try:
    import supabase_db
    _SUPABASE_MODULE_OK = True
except:
    _SUPABASE_MODULE_OK = False

# Import SQLite fallback
import database as sqlite_db


def _check_supabase() -> bool:
    """Kiểm tra Supabase có sẵn không (gọi mỗi lần)."""
    if not _SUPABASE_MODULE_OK:
        return False
    try:
        return supabase_db.is_supabase_available()
    except:
        return False

def _use_supabase() -> bool:
    """Alias for _check_supabase."""
    return _check_supabase()

def is_cloud_mode() -> bool:
    """Kiểm tra đang dùng cloud (Supabase) hay local (SQLite)."""
    return _check_supabase()


def _get_user_id() -> Optional[int]:
    """Lấy user_id từ session."""
    if "user_info" in st.session_state and st.session_state["user_info"]:
        return st.session_state["user_info"].get("id")
    return None


# ==================== JOBS ====================

def get_all_jobs() -> List[Dict]:
    """Lấy tất cả công việc."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.get_all_jobs(user_id)
        return []
    return sqlite_db.get_all_jobs()


def add_job(job_name: str, hourly_rate: float, description: str = "", color: str = "#667eea") -> Optional[int]:
    """Thêm công việc mới."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.add_job(user_id, job_name, hourly_rate, description, color)
        return None
    return sqlite_db.add_job(job_name, hourly_rate, description, color)


def update_job(job_id: int, job_name: str, hourly_rate: float, description: str = "", color: str = "#667eea") -> bool:
    """Cập nhật công việc."""
    if _check_supabase():
        return supabase_db.update_job(job_id, job_name, hourly_rate, description, color)
    return sqlite_db.update_job(job_id, job_name, hourly_rate, description, color)


def delete_job(job_id: int) -> bool:
    """Xóa công việc."""
    if _check_supabase():
        return supabase_db.delete_job(job_id)
    return sqlite_db.delete_job(job_id)


def get_job_by_id(job_id: int) -> Optional[Dict]:
    """Lấy thông tin công việc theo ID."""
    if _check_supabase():
        jobs = get_all_jobs()
        for job in jobs:
            if job['id'] == job_id:
                return job
        return None
    return sqlite_db.get_job_by_id(job_id)


# ==================== WORK SHIFTS (NEW CRUD) ====================

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
    if _check_supabase():
        # TODO: Implement Supabase version properly
        # Fallback to old add_work_shift for now if possible, or return None
        return None
    else:
        return sqlite_db.add_shift(
            work_date, job_id, start_time, end_time, 
            break_hours, total_hours, overtime_hours, notes
        )

def update_shift(shift_id: int, **kwargs) -> bool:
    """Cập nhật ca làm việc."""
    if _check_supabase():
        return False
    else:
        return sqlite_db.update_shift(shift_id, **kwargs)

def delete_shift(shift_id: int) -> bool:
    """Xóa ca làm việc."""
    if _check_supabase():
        return False
    else:
        return sqlite_db.delete_shift(shift_id)

def get_shift_by_id(shift_id: int) -> Optional[Dict]:
    """Lấy shift theo ID."""
    if _check_supabase():
        return None
    else:
        return sqlite_db.get_shift_by_id(shift_id)

# Aliases for legacy compatibility
add_work_shift = sqlite_db.add_work_shift
update_work_shift = sqlite_db.update_work_shift
delete_work_shift = sqlite_db.delete_work_shift


def get_shifts_by_date(work_date: date) -> List[Dict]:
    """Lấy các ca làm việc theo ngày."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.get_shifts_by_date(user_id, work_date)
        return []
    return sqlite_db.get_shifts_by_date(work_date)


def get_shifts_by_range(start_date: date, end_date: date) -> List[Dict]:
    """Lấy các ca làm việc trong khoảng thời gian."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.get_shifts_by_range(user_id, start_date, end_date)
        return []
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
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.add_holiday(user_id, holiday_date, description)
        return False
    return sqlite_db.add_holiday(holiday_date, description)


def remove_holiday(holiday_date: date) -> bool:
    """Xóa ngày nghỉ."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.remove_holiday(user_id, holiday_date)
        return False
    return sqlite_db.remove_holiday(holiday_date)


def get_all_holidays() -> List[Dict]:
    """Lấy tất cả ngày nghỉ."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.get_all_holidays(user_id)
        return []
    return sqlite_db.get_all_holidays()


def get_holidays_by_year(year: int) -> List[Dict]:
    """Lấy danh sách ngày nghỉ trong năm."""
    if _check_supabase():
        # Lấy tất cả và lọc (tạm thời)
        all_holidays = get_all_holidays()
        return [h for h in all_holidays if str(h.get('holiday_date', '')).startswith(str(year))]
    return sqlite_db.get_holidays_by_year(year)


def is_holiday(check_date: date) -> tuple:
    """Kiểm tra ngày nghỉ."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.is_holiday(user_id, check_date)
        return False, ""
    return sqlite_db.is_holiday(check_date)


# ==================== SETTINGS ====================

def get_setting(key: str) -> Optional[str]:
    """Lấy cài đặt."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.get_setting(user_id, key)
        return None
    return sqlite_db.get_setting(key)


def update_setting(key: str, value: str) -> bool:
    """Cập nhật cài đặt."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.update_setting(user_id, key, value)
        return False
    return sqlite_db.update_setting(key, value)


def get_standard_hours() -> float:
    """Lấy số giờ chuẩn."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.get_standard_hours(user_id)
        return 8.0
    return sqlite_db.get_standard_hours()


def get_default_break_hours() -> float:
    """Lấy giờ nghỉ mặc định."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.get_default_break_hours(user_id)
        return 1.0
    return sqlite_db.get_default_break_hours()


def get_ot_rate() -> float:
    """Lấy hệ số OT."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            value = supabase_db.get_setting(user_id, 'ot_rate')
            return float(value) if value else 1.25
        return 1.25
    return sqlite_db.get_ot_rate()


# ==================== DATABASE INIT ====================

def init_database():
    """Khởi tạo database."""
    # Supabase không cần init (đã có tables sẵn)
    if not _check_supabase():
        sqlite_db.init_database()


def clear_cache():
    """Xóa cache."""
    sqlite_db.clear_cache()


# ==================== COMPATIBILITY ====================

def get_work_logs_by_month(year: int, month: int) -> List[Dict]:
    """Compatibility wrapper for get_work_logs_by_month."""
    if _check_supabase():
        # Map to daily summaries
        return get_daily_summaries_by_month(year, month)
    return sqlite_db.get_work_logs_by_month(year, month)


def get_work_logs_by_range(start_date: date, end_date: date) -> List[Dict]:
    """Compatibility wrapper for get_work_logs_by_range."""
    if _check_supabase():
        return get_daily_summaries_by_range(start_date, end_date)
    return sqlite_db.get_work_logs_by_range(start_date, end_date)


def delete_work_log(work_date: date) -> bool:
    """Delete all work logs/shifts for a date."""
    if _check_supabase():
        # Delete all shifts for this date
        shifts = get_shifts_by_date(work_date)
        if not shifts:
            return True # Nothing to delete
            
        success = True
        for shift in shifts:
            if not delete_work_shift(shift['id']):
                success = False
        return success
    return sqlite_db.delete_work_log(work_date)
