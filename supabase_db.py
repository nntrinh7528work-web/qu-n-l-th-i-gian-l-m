# -*- coding: utf-8 -*-
"""
Module kết nối và thao tác với Supabase Database.
Thay thế SQLite để lưu trữ dữ liệu trên cloud.
"""

import streamlit as st
from supabase import create_client, Client
from datetime import datetime, date
from typing import List, Dict, Optional
import os

# ==================== SUPABASE CONNECTION ====================

# Cached client singleton
_cached_client = None
_client_initialized = False

def get_supabase_client() -> Optional[Client]:
    """Lấy Supabase client (cached singleton - tạo 1 lần dùng mãi)."""
    global _cached_client, _client_initialized
    
    # Return cached client nếu đã khởi tạo
    if _client_initialized:
        return _cached_client
    
    _client_initialized = True
    url = None
    key = None
    
    # Method 1: Streamlit secrets (check if key exists first)
    try:
        if hasattr(st, 'secrets'):
            if "SUPABASE_URL" in st.secrets:
                url = st.secrets["SUPABASE_URL"]
            if "SUPABASE_KEY" in st.secrets:
                key = st.secrets["SUPABASE_KEY"]
    except Exception:
        pass
    
    # Method 2: Environment variables (fallback)
    if not url:
        url = os.environ.get("SUPABASE_URL", "")
    if not key:
        key = os.environ.get("SUPABASE_KEY", "")
    
    # Create client if we have credentials
    if url and key:
        try:
            _cached_client = create_client(url, key)
        except Exception as e:
            print(f"Supabase client creation error: {e}")
            _cached_client = None
    
    return _cached_client


# Store last error for debugging
_last_supabase_error = None

def get_last_error() -> str:
    """Get last Supabase error for debugging."""
    global _last_supabase_error
    return _last_supabase_error or "No error"


def is_supabase_available() -> bool:
    """Kiểm tra xem Supabase có sẵn sàng không."""
    global _last_supabase_error
    try:
        client = get_supabase_client()
        if not client:
            _last_supabase_error = "Client is None - credentials missing"
            return False
        
        # Test connection with a simple query
        result = client.table('users').select('id').limit(1).execute()
        _last_supabase_error = None
        return True
    except Exception as e:
        _last_supabase_error = str(e)
        print(f"Supabase availability check failed: {e}")
    return False


# ==================== USERS ====================

def get_user_by_username(username: str) -> Optional[Dict]:
    """Lấy user theo username."""
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        result = client.table('users').select('*').eq('username', username.lower()).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None


def create_user(username: str, password_hash: str, display_name: str = "") -> Optional[Dict]:
    """Tạo user mới."""
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        data = {
            'username': username.lower(),
            'password_hash': password_hash,
            'display_name': display_name or username,
            'created_at': datetime.now().isoformat()
        }
        result = client.table('users').insert(data).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error creating user: {e}")
        return None


def update_user_last_login(user_id: int) -> bool:
    """Cập nhật thời gian đăng nhập cuối."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.table('users').update({
            'last_login': datetime.now().isoformat()
        }).eq('id', user_id).execute()
        return True
    except:
        return False


# ==================== JOBS ====================

def get_all_jobs(user_id: int) -> List[Dict]:
    """Lấy tất cả công việc của user."""
    client = get_supabase_client()
    if not client:
        return []
    
    try:
        result = client.table('jobs').select('*').eq('user_id', user_id).order('job_name').execute()
        return result.data or []
    except:
        return []


def add_job(user_id: int, job_name: str, hourly_rate: float, description: str = "", color: str = "#667eea") -> Optional[int]:
    """Thêm công việc mới."""
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        # Kiểm tra job đã tồn tại
        existing = client.table('jobs').select('id').eq('user_id', user_id).eq('job_name', job_name).execute()
        if existing.data:
            # Update existing
            client.table('jobs').update({
                'hourly_rate': hourly_rate,
                'description': description,
                'color': color
            }).eq('id', existing.data[0]['id']).execute()
            return existing.data[0]['id']
        
        # Create new
        result = client.table('jobs').insert({
            'user_id': user_id,
            'job_name': job_name,
            'hourly_rate': hourly_rate,
            'description': description,
            'color': color
        }).execute()
        
        if result.data:
            return result.data[0]['id']
        return None
    except Exception as e:
        print(f"Error adding job: {e}")
        return None


def update_job(job_id: int, job_name: str, hourly_rate: float, description: str = "", color: str = "#667eea") -> bool:
    """Cập nhật công việc."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.table('jobs').update({
            'job_name': job_name,
            'hourly_rate': hourly_rate,
            'description': description,
            'color': color
        }).eq('id', job_id).execute()
        return True
    except:
        return False


def delete_job(job_id: int) -> bool:
    """Xóa công việc."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.table('jobs').delete().eq('id', job_id).execute()
        return True
    except:
        return False


# ==================== WORK SHIFTS ====================

def add_work_shift(
    user_id: int,
    work_date: date,
    shift_name: str,
    start_time: str,
    end_time: str,
    break_hours: float,
    total_hours: float,
    notes: str = "",
    job_id: int = None
) -> Optional[int]:
    """Thêm ca làm việc mới."""
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        result = client.table('work_shifts').insert({
            'user_id': user_id,
            'work_date': work_date.isoformat(),
            'shift_name': shift_name,
            'job_id': job_id,
            'start_time': start_time,
            'end_time': end_time,
            'break_hours': break_hours,
            'total_hours': total_hours,
            'notes': notes
        }).execute()
        
        if result.data:
            return result.data[0]['id']
        return None
    except Exception as e:
        print(f"Error adding shift: {e}")
        return None


def update_work_shift(
    shift_id: int,
    shift_name: str,
    start_time: str,
    end_time: str,
    break_hours: float,
    total_hours: float,
    notes: str = ""
) -> bool:
    """Cập nhật ca làm việc."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.table('work_shifts').update({
            'shift_name': shift_name,
            'start_time': start_time,
            'end_time': end_time,
            'break_hours': break_hours,
            'total_hours': total_hours,
            'notes': notes
        }).eq('id', shift_id).execute()
        return True
    except:
        return False


def delete_work_shift(shift_id: int) -> bool:
    """Xóa ca làm việc."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.table('work_shifts').delete().eq('id', shift_id).execute()
        return True
    except:
        return False


def get_shifts_by_date(user_id: int, work_date: date) -> List[Dict]:
    """Lấy các ca làm việc theo ngày."""
    client = get_supabase_client()
    if not client:
        return []
    
    try:
        result = client.table('work_shifts').select('*').eq('user_id', user_id).eq('work_date', work_date.isoformat()).order('start_time').execute()
        return result.data or []
    except:
        return []


def get_shifts_by_range(user_id: int, start_date: date, end_date: date) -> List[Dict]:
    """Lấy các ca làm việc trong khoảng thời gian."""
    client = get_supabase_client()
    if not client:
        return []
    
    try:
        result = client.table('work_shifts').select('*').eq('user_id', user_id).gte('work_date', start_date.isoformat()).lte('work_date', end_date.isoformat()).order('work_date').order('start_time').execute()
        return result.data or []
    except:
        return []


# ==================== HOLIDAYS ====================

def add_holiday(user_id: int, holiday_date: date, description: str) -> bool:
    """Thêm ngày nghỉ."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        # Upsert
        client.table('holidays').upsert({
            'user_id': user_id,
            'holiday_date': holiday_date.isoformat(),
            'description': description
        }, on_conflict='user_id,holiday_date').execute()
        return True
    except:
        return False


def remove_holiday(user_id: int, holiday_date: date) -> bool:
    """Xóa ngày nghỉ."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.table('holidays').delete().eq('user_id', user_id).eq('holiday_date', holiday_date.isoformat()).execute()
        return True
    except:
        return False


def get_all_holidays(user_id: int) -> List[Dict]:
    """Lấy tất cả ngày nghỉ."""
    client = get_supabase_client()
    if not client:
        return []
    
    try:
        result = client.table('holidays').select('*').eq('user_id', user_id).order('holiday_date').execute()
        return result.data or []
    except:
        return []


def is_holiday(user_id: int, check_date: date) -> tuple:
    """Kiểm tra ngày nghỉ."""
    client = get_supabase_client()
    if not client:
        return False, ""
    
    try:
        result = client.table('holidays').select('description').eq('user_id', user_id).eq('holiday_date', check_date.isoformat()).execute()
        if result.data:
            return True, result.data[0]['description']
        return False, ""
    except:
        return False, ""


# ==================== SETTINGS ====================

def get_setting(user_id: int, key: str) -> Optional[str]:
    """Lấy cài đặt."""
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        result = client.table('settings').select('value').eq('user_id', user_id).eq('key', key).execute()
        if result.data:
            return result.data[0]['value']
        return None
    except:
        return None


def update_setting(user_id: int, key: str, value: str) -> bool:
    """Cập nhật cài đặt."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.table('settings').upsert({
            'user_id': user_id,
            'key': key,
            'value': value
        }, on_conflict='user_id,key').execute()
        return True
    except:
        return False


def get_standard_hours(user_id: int) -> float:
    """Lấy số giờ chuẩn."""
    value = get_setting(user_id, 'standard_hours')
    return float(value) if value else 8.0


def get_default_break_hours(user_id: int) -> float:
    """Lấy giờ nghỉ mặc định."""
    value = get_setting(user_id, 'break_hours')
    return float(value) if value else 1.0


# ==================== SHIFT PRESETS ====================

def get_all_presets(user_id: int) -> List[Dict]:
    """Lấy tất cả khung giờ mẫu của user."""
    client = get_supabase_client()
    if not client:
        return []
    
    try:
        result = client.table('shift_presets').select('*').eq('user_id', user_id).order('sort_order').execute()
        return result.data or []
    except:
        return []


def add_preset(user_id: int, preset_name: str, start_time: str, end_time: str,
               break_hours: float, total_hours: float,
               job_id: int = None, emoji: str = "⏰", sort_order: int = 0) -> Optional[int]:
    """Thêm khung giờ mẫu mới."""
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        data = {
            'user_id': user_id,
            'preset_name': preset_name,
            'start_time': start_time,
            'end_time': end_time,
            'break_hours': break_hours,
            'total_hours': total_hours,
            'emoji': emoji,
            'sort_order': sort_order
        }
        if job_id is not None:
            data['job_id'] = job_id
        
        result = client.table('shift_presets').insert(data).execute()
        if result.data:
            return result.data[0]['id']
        return None
    except Exception as e:
        print(f"Error adding preset: {e}")
        return None


def update_preset(user_id: int, preset_id: int, **kwargs) -> bool:
    """Cập nhật khung giờ mẫu."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        update_data = {}
        allowed_fields = ['preset_name', 'start_time', 'end_time', 'break_hours', 
                          'total_hours', 'job_id', 'emoji', 'sort_order']
        for key, value in kwargs.items():
            if key in allowed_fields:
                update_data[key] = value
        
        if update_data:
            client.table('shift_presets').update(update_data).eq('id', preset_id).eq('user_id', user_id).execute()
        return True
    except:
        return False


def delete_preset(user_id: int, preset_id: int) -> bool:
    """Xóa khung giờ mẫu."""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.table('shift_presets').delete().eq('id', preset_id).eq('user_id', user_id).execute()
        return True
    except:
        return False


# ==================== INIT DEFAULT DATA ====================

def init_user_default_data(user_id: int):
    """Khởi tạo dữ liệu mặc định cho user mới."""
    client = get_supabase_client()
    if not client:
        return
    
    try:
        # Kiểm tra đã có jobs chưa
        existing_jobs = get_all_jobs(user_id)
        if not existing_jobs:
            # Thêm jobs mặc định
            add_job(user_id, "Bệnh viện", 1200, "Công việc chính", "#10B981")
            add_job(user_id, "Kombini", 1100, "Công việc phụ", "#3B82F6")
        
        # Thêm settings mặc định
        if not get_setting(user_id, 'standard_hours'):
            update_setting(user_id, 'standard_hours', '8.0')
        if not get_setting(user_id, 'break_hours'):
            update_setting(user_id, 'break_hours', '1.0')
        if not get_setting(user_id, 'ot_rate'):
            update_setting(user_id, 'ot_rate', '1.25')
        
        # Thêm presets mặc định nếu chưa có
        existing_presets = get_all_presets(user_id)
        if not existing_presets:
            default_presets = [
                ('Ca Sáng 8h', '08:00', '17:00', 1.0, 8.0, '☀️', 1),
                ('Ca Tối 8h', '17:00', '02:00', 1.0, 8.0, '🌙', 2),
                ('Part-time 4h', '09:00', '13:00', 0.0, 4.0, '⏰', 3),
                ('Full Day 10h', '07:00', '18:00', 1.0, 10.0, '🔥', 4),
            ]
            for name, start, end, brk, total, emoji, order in default_presets:
                add_preset(user_id, name, start, end, brk, total, emoji=emoji, sort_order=order)
    except:
        pass
