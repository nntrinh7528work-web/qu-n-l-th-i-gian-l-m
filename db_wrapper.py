# -*- coding: utf-8 -*-
"""
Database Wrapper - Tá»± Ä‘á»™ng chá»n Supabase hoáº·c SQLite.
Import module nÃ y thay vÃ¬ import trá»±c tiáº¿p database.py hoáº·c supabase_db.py
"""

import streamlit as st
from datetime import date
from typing import List, Dict, Optional

# Thá»­ import Supabase
try:
    import supabase_db
    _SUPABASE_MODULE_OK = True
except:
    _SUPABASE_MODULE_OK = False

# Import SQLite fallback
import database as sqlite_db


def _check_supabase() -> bool:
    """Kiá»ƒm tra Supabase cÃ³ sáºµn khÃ´ng (gá»i má»—i láº§n)."""
    if not _SUPABASE_MODULE_OK:
        return False
    try:
        return supabase_db.is_supabase_available()
    except:
        return False


def is_cloud_mode() -> bool:
    """Kiá»ƒm tra Ä‘ang dÃ¹ng cloud (Supabase) hay local (SQLite)."""
    return _check_supabase()


def _get_user_id() -> Optional[int]:
    """Láº¥y user_id tá»« session."""
    if "user_info" in st.session_state and st.session_state["user_info"]:
        return st.session_state["user_info"].get("id")
    return None


# ==================== JOBS ====================

def get_all_jobs() -> List[Dict]:
    """Láº¥y táº¥t cáº£ cÃ´ng viá»‡c."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.get_all_jobs(user_id)
        return []
    return sqlite_db.get_all_jobs()


def add_job(job_name: str, hourly_rate: float, description: str = "", color: str = "#667eea") -> Optional[int]:
    """ThÃªm cÃ´ng viá»‡c má»›i."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.add_job(user_id, job_name, hourly_rate, description, color)
        return None
    return sqlite_db.add_job(job_name, hourly_rate, description, color)


def update_job(job_id: int, job_name: str, hourly_rate: float, description: str = "", color: str = "#667eea") -> bool:
    """Cáº­p nháº­t cÃ´ng viá»‡c."""
    if _check_supabase():
        return supabase_db.update_job(job_id, job_name, hourly_rate, description, color)
    return sqlite_db.update_job(job_id, job_name, hourly_rate, description, color)


def delete_job(job_id: int) -> bool:
    """XÃ³a cÃ´ng viá»‡c."""
    if _check_supabase():
        return supabase_db.delete_job(job_id)
    return sqlite_db.delete_job(job_id)


def get_job_by_id(job_id: int) -> Optional[Dict]:
    """Láº¥y thÃ´ng tin cÃ´ng viá»‡c theo ID."""
    if _check_supabase():
        jobs = get_all_jobs()
        for job in jobs:
            if job['id'] == job_id:
                return job
        return None
    return sqlite_db.get_job_by_id(job_id)


# ==================== WORK SHIFTS ====================

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
    """ThÃªm ca lÃ m viá»‡c má»›i."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            result = supabase_db.add_work_shift(user_id, work_date, shift_name, start_time, end_time, break_hours, total_hours, notes, job_id)
            return result if result else -1
        return -1
    return sqlite_db.add_work_shift(work_date, shift_name, start_time, end_time, break_hours, total_hours, notes, job_id)


def update_work_shift(
    shift_id: int,
    shift_name: str,
    start_time: str,
    end_time: str,
    break_hours: float,
    total_hours: float,
    notes: str = ""
) -> bool:
    """Cáº­p nháº­t ca lÃ m viá»‡c."""
    if _check_supabase():
        return supabase_db.update_work_shift(shift_id, shift_name, start_time, end_time, break_hours, total_hours, notes)
    return sqlite_db.update_work_shift(shift_id, shift_name, start_time, end_time, break_hours, total_hours, notes)


def delete_work_shift(shift_id: int) -> bool:
    """XÃ³a ca lÃ m viá»‡c."""
    if _check_supabase():
        return supabase_db.delete_work_shift(shift_id)
    return sqlite_db.delete_work_shift(shift_id)


def get_shifts_by_date(work_date: date) -> List[Dict]:
    """Láº¥y cÃ¡c ca lÃ m viá»‡c theo ngÃ y."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.get_shifts_by_date(user_id, work_date)
        return []
    return sqlite_db.get_shifts_by_date(work_date)


def get_shifts_by_range(start_date: date, end_date: date) -> List[Dict]:
    """Láº¥y cÃ¡c ca lÃ m viá»‡c trong khoáº£ng thá»i gian."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.get_shifts_by_range(user_id, start_date, end_date)
        return []
    return sqlite_db.get_shifts_by_range(start_date, end_date)


def get_shift_by_id(shift_id: int) -> Optional[Dict]:
    """Láº¥y thÃ´ng tin ca lÃ m viá»‡c theo ID."""
    return sqlite_db.get_shift_by_id(shift_id)


def get_daily_summary(work_date: date, standard_hours: float = 8.0) -> Dict:
    """Láº¥y tá»•ng há»£p giá» lÃ m cá»§a má»™t ngÃ y."""
    return sqlite_db.get_daily_summary(work_date, standard_hours)


def get_daily_summaries_by_range(start_date: date, end_date: date, standard_hours: float = 8.0) -> List[Dict]:
    """Láº¥y tá»•ng há»£p giá» lÃ m theo ngÃ y trong khoáº£ng thá»i gian."""
    return sqlite_db.get_daily_summaries_by_range(start_date, end_date, standard_hours)


def get_daily_summaries_by_month(year: int, month: int, standard_hours: float = 8.0) -> List[Dict]:
    """Láº¥y tá»•ng há»£p giá» lÃ m theo ngÃ y trong má»™t thÃ¡ng."""
    return sqlite_db.get_daily_summaries_by_month(year, month, standard_hours)


# ==================== HOLIDAYS ====================

def add_holiday(holiday_date: date, description: str) -> bool:
    """ThÃªm ngÃ y nghá»‰."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.add_holiday(user_id, holiday_date, description)
        return False
    return sqlite_db.add_holiday(holiday_date, description)


def remove_holiday(holiday_date: date) -> bool:
    """XÃ³a ngÃ y nghá»‰."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.remove_holiday(user_id, holiday_date)
        return False
    return sqlite_db.remove_holiday(holiday_date)


def get_all_holidays() -> List[Dict]:
    """Láº¥y táº¥t cáº£ ngÃ y nghá»‰."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.get_all_holidays(user_id)
        return []
    return sqlite_db.get_all_holidays()


def is_holiday(check_date: date) -> tuple:
    """Kiá»ƒm tra ngÃ y nghá»‰."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.is_holiday(user_id, check_date)
        return False, ""
    return sqlite_db.is_holiday(check_date)


# ==================== SETTINGS ====================

def get_setting(key: str) -> Optional[str]:
    """Láº¥y cÃ i Ä‘áº·t."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.get_setting(user_id, key)
        return None
    return sqlite_db.get_setting(key)


def update_setting(key: str, value: str) -> bool:
    """Cáº­p nháº­t cÃ i Ä‘áº·t."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.update_setting(user_id, key, value)
        return False
    return sqlite_db.update_setting(key, value)


def get_standard_hours() -> float:
    """Láº¥y sá»‘ giá» chuáº©n."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.get_standard_hours(user_id)
        return 8.0
    return sqlite_db.get_standard_hours()


def get_default_break_hours() -> float:
    """Láº¥y giá» nghá»‰ máº·c Ä‘á»‹nh."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            return supabase_db.get_default_break_hours(user_id)
        return 1.0
    return sqlite_db.get_default_break_hours()


def get_ot_rate() -> float:
    """Láº¥y há»‡ sá»‘ OT."""
    if _check_supabase():
        user_id = _get_user_id()
        if user_id:
            value = supabase_db.get_setting(user_id, 'ot_rate')
            return float(value) if value else 1.25
        return 1.25
    return sqlite_db.get_ot_rate()


# ==================== DATABASE INIT ====================

def init_database():
    """Khá»Ÿi táº¡o database."""
    # Supabase khÃ´ng cáº§n init (Ä‘Ã£ cÃ³ tables sáºµn)
    if not _check_supabase():
        sqlite_db.init_database()


def clear_cache():
    """XÃ³a cache."""
    sqlite_db.clear_cache()
