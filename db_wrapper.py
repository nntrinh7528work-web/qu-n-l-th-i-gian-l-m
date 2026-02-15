# -*- coding: utf-8 -*-
"""
Database Wrapper - Tự động chọn Supabase (cloud) hoặc SQLite (local).
Khi có Supabase: dùng user_id mặc định (không cần login) để dữ liệu lưu lâu dài.
Khi không có Supabase: fallback sang SQLite.
"""

from datetime import date
from typing import List, Dict, Optional, Union
import database as sqlite_db

# Thử import Supabase
try:
    import supabase_db
    _SUPABASE_MODULE_OK = True
except Exception:
    _SUPABASE_MODULE_OK = False

# Default user ID khi không cần login
_DEFAULT_USER_ID = 1

# Cache trạng thái Supabase (tránh check liên tục)
_supabase_available = None


def _check_supabase() -> bool:
    """Kiểm tra Supabase có sẵn không (cache kết quả)."""
    global _supabase_available
    if _supabase_available is not None:
        return _supabase_available
    
    if not _SUPABASE_MODULE_OK:
        _supabase_available = False
        return False
    try:
        _supabase_available = supabase_db.is_supabase_available()
    except Exception:
        _supabase_available = False
    return _supabase_available


def _get_user_id() -> int:
    """Luôn trả về default user ID (không cần login)."""
    return _DEFAULT_USER_ID


def is_cloud_mode() -> bool:
    """Kiểm tra đang dùng cloud (Supabase) hay local (SQLite)."""
    return _check_supabase()


# ==================== SHIFT PRESETS ====================

def get_all_presets() -> List[Dict]:
    """Lấy tất cả khung giờ mẫu."""
    return sqlite_db.get_all_presets()


def add_preset(preset_name: str, start_time: str, end_time: str,
               break_hours: float, total_hours: float,
               job_id: int = None, emoji: str = "⏰") -> Optional[int]:
    """Thêm khung giờ mẫu mới."""
    return sqlite_db.add_preset(preset_name, start_time, end_time, break_hours, total_hours, job_id, emoji)


def update_preset(preset_id: int, **kwargs) -> bool:
    """Cập nhật khung giờ mẫu."""
    return sqlite_db.update_preset(preset_id, **kwargs)


def delete_preset(preset_id: int) -> bool:
    """Xóa khung giờ mẫu."""
    return sqlite_db.delete_preset(preset_id)


# ==================== JOBS ====================

def get_all_jobs() -> List[Dict]:
    """Lấy tất cả công việc."""
    if _check_supabase():
        try:
            result = supabase_db.get_all_jobs(_get_user_id())
            if result is not None:
                return result
        except Exception:
            pass
    return sqlite_db.get_all_jobs()


def add_job(job_name: str, hourly_rate: float, description: str = "", color: str = "#667eea") -> Optional[int]:
    """Thêm công việc mới."""
    if _check_supabase():
        try:
            result = supabase_db.add_job(_get_user_id(), job_name, hourly_rate, description, color)
            if result is not None:
                return result
        except Exception:
            pass
    return sqlite_db.add_job(job_name, hourly_rate, description, color)


def update_job(job_id: int, job_name: str, hourly_rate: float, description: str = "", color: str = "#667eea") -> bool:
    """Cập nhật công việc."""
    if _check_supabase():
        try:
            return supabase_db.update_job(job_id, job_name, hourly_rate, description, color)
        except Exception:
            pass
    return sqlite_db.update_job(job_id, job_name, hourly_rate, description, color)


def delete_job(job_id: int) -> bool:
    """Xóa công việc."""
    if _check_supabase():
        try:
            return supabase_db.delete_job(job_id)
        except Exception:
            pass
    return sqlite_db.delete_job(job_id)


def get_job_by_id(job_id: int) -> Optional[Dict]:
    """Lấy thông tin công việc theo ID."""
    if _check_supabase():
        try:
            jobs = supabase_db.get_all_jobs(_get_user_id())
            for job in jobs:
                if job['id'] == job_id:
                    return job
        except Exception:
            pass
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
    if _check_supabase():
        try:
            # Chuyển đổi date nếu cần
            if isinstance(work_date, str):
                work_date_obj = date.fromisoformat(work_date)
            else:
                work_date_obj = work_date
            
            result = supabase_db.add_work_shift(
                user_id=_get_user_id(),
                work_date=work_date_obj,
                shift_name="Ca làm",
                start_time=start_time,
                end_time=end_time,
                break_hours=break_hours,
                total_hours=total_hours,
                notes=notes,
                job_id=job_id
            )
            if result is not None:
                return result
        except Exception as e:
            print(f"Supabase add_shift error: {e}")
    return sqlite_db.add_shift(
        work_date, job_id, start_time, end_time,
        break_hours, total_hours, overtime_hours, notes
    )


def update_shift(shift_id: int, **kwargs) -> bool:
    """Cập nhật ca làm việc."""
    if _check_supabase():
        try:
            # Map kwargs to supabase_db.update_work_shift params
            return supabase_db.update_work_shift(
                shift_id=shift_id,
                shift_name=kwargs.get('shift_name', 'Ca làm'),
                start_time=kwargs.get('start_time', '09:00'),
                end_time=kwargs.get('end_time', '17:00'),
                break_hours=kwargs.get('break_hours', 1.0),
                total_hours=kwargs.get('total_hours', 8.0),
                notes=kwargs.get('notes', '')
            )
        except Exception:
            pass
    return sqlite_db.update_shift(shift_id, **kwargs)


def delete_shift(shift_id: int) -> bool:
    """Xóa ca làm việc."""
    if _check_supabase():
        try:
            return supabase_db.delete_work_shift(shift_id)
        except Exception:
            pass
    return sqlite_db.delete_shift(shift_id)


def get_shift_by_id(shift_id: int) -> Optional[Dict]:
    """Lấy shift theo ID."""
    # Supabase doesn't have a direct get_shift_by_id, use SQLite
    return sqlite_db.get_shift_by_id(shift_id)


def get_shifts_by_date(work_date: date) -> List[Dict]:
    """Lấy các ca làm việc theo ngày."""
    if _check_supabase():
        try:
            result = supabase_db.get_shifts_by_date(_get_user_id(), work_date)
            if result is not None:
                return result
        except Exception:
            pass
    return sqlite_db.get_shifts_by_date(work_date)


def get_shifts_by_range(start_date: date, end_date: date) -> List[Dict]:
    """Lấy các ca làm việc trong khoảng thời gian."""
    if _check_supabase():
        try:
            result = supabase_db.get_shifts_by_range(_get_user_id(), start_date, end_date)
            if result is not None:
                return result
        except Exception:
            pass
    return sqlite_db.get_shifts_by_range(start_date, end_date)


# Legacy aliases
def add_work_shift(work_date, shift_name, start_time, end_time, break_hours, total_hours, notes="", job_id=None):
    """Legacy wrapper for add_shift."""
    if job_id is None:
        all_jobs = get_all_jobs()
        if all_jobs:
            job_id = all_jobs[0]['id']
        else:
            return -1
    result = add_shift(work_date, job_id, start_time, end_time, break_hours, total_hours, 0.0, notes)
    return result if result is not None else -1


def update_work_shift(shift_id, shift_name, start_time, end_time, break_hours, total_hours, notes=""):
    """Legacy wrapper for update_shift."""
    return update_shift(shift_id, shift_name=shift_name, start_time=start_time, end_time=end_time,
                        break_hours=break_hours, total_hours=total_hours, notes=notes)


def delete_work_shift(shift_id):
    """Legacy wrapper for delete_shift."""
    return delete_shift(shift_id)


def get_daily_summary(work_date: date, standard_hours: float = 8.0) -> Dict:
    """Lấy tổng hợp giờ làm của một ngày."""
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


def get_daily_summaries_by_range(start_date: date, end_date: date, standard_hours: float = 8.0) -> List[Dict]:
    """Lấy tổng hợp giờ làm theo ngày trong khoảng thời gian."""
    shifts = get_shifts_by_range(start_date, end_date)
    
    if not shifts:
        return []
    
    # Gộp theo ngày
    daily_data = {}
    for shift in shifts:
        wd = shift['work_date']
        if wd not in daily_data:
            daily_data[wd] = {
                "work_date": wd,
                "total_hours": 0.0,
                "shift_count": 0,
                "shifts": [],
                "start_time": shift.get('start_time', ''),
                "end_time": shift.get('end_time', ''),
                "break_hours": 0.0,
                "notes": ""
            }
        
        daily_data[wd]["total_hours"] += shift['total_hours']
        daily_data[wd]["break_hours"] += shift.get('break_hours', 0)
        daily_data[wd]["shift_count"] += 1
        daily_data[wd]["shifts"].append(shift)
        daily_data[wd]["end_time"] = shift.get('end_time', '')
        
        if shift.get('notes'):
            if daily_data[wd]["notes"]:
                daily_data[wd]["notes"] += f"; {shift['notes']}"
            else:
                daily_data[wd]["notes"] = shift['notes']
    
    result = []
    for wd, data in daily_data.items():
        data["total_hours"] = round(data["total_hours"], 2)
        data["overtime_hours"] = round(max(0, data["total_hours"] - standard_hours), 2)
        result.append(data)
    
    result.sort(key=lambda x: x["work_date"])
    return result


def get_daily_summaries_by_month(year: int, month: int, standard_hours: float = 8.0) -> List[Dict]:
    """Lấy tổng hợp giờ làm theo ngày trong một tháng."""
    from datetime import timedelta
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    return get_daily_summaries_by_range(start_date, end_date, standard_hours)


# ==================== HOLIDAYS ====================

def add_holiday(holiday_date: date, description: str) -> bool:
    """Thêm ngày nghỉ."""
    if _check_supabase():
        try:
            return supabase_db.add_holiday(_get_user_id(), holiday_date, description)
        except Exception:
            pass
    return sqlite_db.add_holiday(holiday_date, description)


def remove_holiday(holiday_date: date) -> bool:
    """Xóa ngày nghỉ."""
    if _check_supabase():
        try:
            return supabase_db.remove_holiday(_get_user_id(), holiday_date)
        except Exception:
            pass
    return sqlite_db.remove_holiday(holiday_date)


def get_all_holidays() -> List[Dict]:
    """Lấy tất cả ngày nghỉ."""
    if _check_supabase():
        try:
            result = supabase_db.get_all_holidays(_get_user_id())
            if result is not None:
                return result
        except Exception:
            pass
    return sqlite_db.get_all_holidays()


def get_holidays_by_year(year: int) -> List[Dict]:
    """Lấy danh sách ngày nghỉ trong năm."""
    all_holidays = get_all_holidays()
    return [h for h in all_holidays if str(h.get('holiday_date', '')).startswith(str(year))]


def is_holiday(check_date: date) -> tuple:
    """Kiểm tra ngày nghỉ."""
    if _check_supabase():
        try:
            return supabase_db.is_holiday(_get_user_id(), check_date)
        except Exception:
            pass
    return sqlite_db.is_holiday(check_date)


# ==================== SETTINGS ====================

def get_setting(key: str) -> Optional[str]:
    """Lấy cài đặt."""
    if _check_supabase():
        try:
            result = supabase_db.get_setting(_get_user_id(), key)
            if result is not None:
                return result
        except Exception:
            pass
    return sqlite_db.get_setting(key)


def update_setting(key: str, value: str) -> bool:
    """Cập nhật cài đặt."""
    if _check_supabase():
        try:
            return supabase_db.update_setting(_get_user_id(), key, value)
        except Exception:
            pass
    return sqlite_db.update_setting(key, value)


def get_standard_hours() -> float:
    """Lấy số giờ chuẩn."""
    if _check_supabase():
        try:
            return supabase_db.get_standard_hours(_get_user_id())
        except Exception:
            pass
    return sqlite_db.get_standard_hours()


def get_default_break_hours() -> float:
    """Lấy giờ nghỉ mặc định."""
    if _check_supabase():
        try:
            return supabase_db.get_default_break_hours(_get_user_id())
        except Exception:
            pass
    return sqlite_db.get_default_break_hours()


def get_ot_rate() -> float:
    """Lấy hệ số OT."""
    if _check_supabase():
        try:
            value = supabase_db.get_setting(_get_user_id(), 'ot_rate')
            return float(value) if value else 1.25
        except Exception:
            pass
    return sqlite_db.get_ot_rate()


# ==================== DATABASE INIT ====================

def init_database():
    """Khởi tạo database."""
    # Luôn init SQLite (cho fallback)
    try:
        sqlite_db.init_database()
    except Exception as e:
        print(f"SQLite init warning: {e}")
    
    # Init dữ liệu mặc định trên Supabase nếu có
    if _check_supabase():
        try:
            supabase_db.init_user_default_data(_get_user_id())
        except Exception as e:
            print(f"Supabase init warning: {e}")


def clear_cache():
    """Xóa cache."""
    sqlite_db.clear_cache()


# ==================== SALARY ====================

def calculate_salary_by_month(year: int, month: int) -> Dict:
    """Tính lương theo tháng, phân chia theo từng công việc."""
    from datetime import timedelta
    
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    # Lấy shifts từ nguồn dữ liệu đúng (Supabase hoặc SQLite)
    shifts = get_shifts_by_range(start_date, end_date)
    all_jobs = get_all_jobs()
    
    # Build job lookup
    job_lookup = {j['id']: j for j in all_jobs}
    
    standard_hours = get_standard_hours()
    ot_rate_val = get_ot_rate()
    
    job_salary = {}
    total_hours_all = 0
    total_salary_all = 0
    
    for shift in shifts:
        job_id = shift.get('job_id') or 0
        job_info = job_lookup.get(job_id, {})
        job_name = job_info.get('job_name') or shift.get('job_name') or 'Chưa phân loại'
        hourly_rate = job_info.get('hourly_rate') or shift.get('hourly_rate') or 0
        color = job_info.get('color') or shift.get('color') or '#667eea'
        hours = shift.get('total_hours', 0)
        
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
    
    # Tính OT theo ngày
    daily_hours = {}
    for shift in shifts:
        day = shift['work_date']
        if day not in daily_hours:
            daily_hours[day] = 0
        daily_hours[day] += shift.get('total_hours', 0)
    
    total_ot_hours = 0
    for day, hours in daily_hours.items():
        if hours > standard_hours:
            total_ot_hours += hours - standard_hours
    
    for job_id, data in job_salary.items():
        total_salary_all += data['base_salary']
    
    if total_hours_all > 0 and total_salary_all > 0:
        avg_hourly_rate = total_salary_all / total_hours_all
        ot_bonus = total_ot_hours * avg_hourly_rate * (ot_rate_val - 1)
    else:
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
        'ot_rate': ot_rate_val
    }


# ==================== COMPATIBILITY ====================

def get_work_logs_by_month(year: int, month: int) -> List[Dict]:
    """Compatibility wrapper."""
    return get_daily_summaries_by_month(year, month)


def get_work_logs_by_range(start_date: date, end_date: date) -> List[Dict]:
    """Compatibility wrapper."""
    return get_daily_summaries_by_range(start_date, end_date)


def delete_work_log(work_date: date) -> bool:
    """Delete all work logs/shifts for a date."""
    shifts = get_shifts_by_date(work_date)
    if not shifts:
        return True
    
    success = True
    for shift in shifts:
        if not delete_shift(shift['id']):
            success = False
    return success
