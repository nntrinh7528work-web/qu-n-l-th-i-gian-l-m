def add_shift(work_date, job_id, start_time, end_time, break_hours, total_hours, overtime_hours=0.0, notes=""):
    """Wrapper: Thêm ca làm việc."""
    if _check_supabase():
        # Fallback hoặc implement Supabase logic
        return None
    else:
        return sqlite_db.add_shift(work_date, job_id, start_time, end_time, 
                                   break_hours, total_hours, overtime_hours, notes)

def update_shift(shift_id, **kwargs):
    """Wrapper: Cập nhật ca làm việc."""
    if _check_supabase():
        return False
    else:
        return sqlite_db.update_shift(shift_id, **kwargs)

def delete_shift(shift_id):
    """Wrapper: Xóa ca làm việc."""
    if _check_supabase():
        return False
    else:
        return sqlite_db.delete_shift(shift_id)

def get_shift_by_id(shift_id):
    """Wrapper: Lấy shift theo ID."""
    if _check_supabase():
        return None
    else:
        return sqlite_db.get_shift_by_id(shift_id)

# Aliases for backward compatibility
add_work_shift = sqlite_db.add_work_shift
update_work_shift = sqlite_db.update_work_shift
delete_work_shift = sqlite_db.delete_work_shift
