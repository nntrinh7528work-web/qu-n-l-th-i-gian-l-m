# -*- coding: utf-8 -*-
"""
Module tính toán giờ làm việc và giờ làm thêm.
Bao gồm các hàm validate và xử lý thời gian.
"""

from datetime import datetime, time, date, timedelta
from typing import Tuple, Optional, Dict, List
import pandas as pd

# Constants (Avoiding magic numbers)
DEFAULT_STANDARD_HOURS = 8.0
DEFAULT_BREAK_HOURS = 1.0
HOURS_PER_DAY = 24.0
MINUTES_PER_HOUR = 60.0

def parse_time(time_str: str) -> Optional[time]:
    """
    Chuyển đổi chuỗi thời gian thành đối tượng time.
    
    Args:
        time_str: Chuỗi thời gian định dạng "HH:MM"
    
    Returns:
        Đối tượng time hoặc None nếu không hợp lệ
    """
    try:
        return datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        return None


def time_to_hours(t: time) -> float:
    """
    Chuyển đổi time thành số giờ (float).
    
    Args:
        t: Đối tượng time
        
    Returns:
        Số giờ dạng float (VD: 1.5 giờ)
    """
    return t.hour + t.minute / MINUTES_PER_HOUR


def validate_time_input(start_time: str, end_time: str, allow_overnight: bool = True) -> Tuple[bool, str]:
    """
    Kiểm tra đầu vào thời gian có hợp lệ không.
    
    Args:
        start_time: Giờ bắt đầu (HH:MM)
        end_time: Giờ kết thúc (HH:MM)
        allow_overnight: Cho phép ca qua đêm (giờ kết thúc < giờ bắt đầu). 
                         Nếu True, start == end được hiểu là 24 giờ.
    
    Returns:
        Tuple (is_valid, error_message)
    """
    start = parse_time(start_time)
    end = parse_time(end_time)
    
    if start is None:
        return False, "❌ Giờ bắt đầu không hợp lệ. Vui lòng nhập theo định dạng HH:MM (ví dụ: 08:00)"
    
    if end is None:
        return False, "❌ Giờ kết thúc không hợp lệ. Vui lòng nhập theo định dạng HH:MM (ví dụ: 17:00)"
    
    # Nếu không cho phép ca qua đêm, thì start phải < end
    if not allow_overnight:
        if start >= end:
            return False, "❌ Giờ bắt đầu phải sớm hơn giờ kết thúc!"
    
    # Nếu cho phép ca qua đêm, mọi trường hợp đều hợp lệ về mặt logic
    # (start < end: ca thường, start > end: ca qua đêm, start == end: ca 24h)
    
    return True, ""


def calculate_work_hours(
    start_time: str, 
    end_time: str, 
    break_hours: float = DEFAULT_BREAK_HOURS
) -> Tuple[float, str]:
    """
    Tính tổng số giờ làm việc.
    Hỗ trợ ca qua đêm (ví dụ: 17:00 - 00:00 hoặc 22:00 - 06:00).
    Nếu start == end, được tính là 24 giờ.
    
    Args:
        start_time: Giờ bắt đầu (HH:MM)
        end_time: Giờ kết thúc (HH:MM)
        break_hours: Số giờ nghỉ (mặc định 1 giờ)
    
    Returns:
        Tuple (total_hours, error_message)
        total_hours = -1 nếu có lỗi
    """
    is_valid, error_msg = validate_time_input(start_time, end_time, allow_overnight=True)
    if not is_valid:
        return -1, error_msg
    
    start = parse_time(start_time)
    end = parse_time(end_time)
    
    # Tính tổng giờ làm
    start_hours = time_to_hours(start)
    end_hours = time_to_hours(end)
    
    # Xử lý ca qua đêm hoặc 24h (end_hours <= start_hours)
    if end_hours <= start_hours:
        # Ví dụ: 17:00 - 00:00 => 17 - 24 = 7 giờ
        # Ví dụ: 22:00 - 06:00 => 22 - 30 = 8 giờ
        # Ví dụ: 22:00 - 22:00 => 22 - 46 = 24 giờ
        end_hours += HOURS_PER_DAY
    
    total_hours = end_hours - start_hours - break_hours
    
    if total_hours < 0:
        return -1, f"❌ Tổng giờ làm ({total_hours + break_hours}h) nhỏ hơn giờ nghỉ ({break_hours}h). Vui lòng kiểm tra lại!"
    
    return round(total_hours, 2), ""


def calculate_overtime(
    total_hours: float, 
    standard_hours: float = DEFAULT_STANDARD_HOURS
) -> float:
    """
    Tính giờ làm thêm.
    
    Args:
        total_hours: Tổng giờ làm thực tế
        standard_hours: Giờ làm chuẩn (mặc định 8 giờ)
    
    Returns:
        Số giờ làm thêm (0 nếu không có OT)
    """
    overtime = total_hours - standard_hours
    return round(max(0, overtime), 2)


def calculate_full(
    start_time: str,
    end_time: str,
    break_hours: float = DEFAULT_BREAK_HOURS,
    standard_hours: float = DEFAULT_STANDARD_HOURS
) -> Dict:
    """
    Tính toán đầy đủ giờ làm và giờ làm thêm.
    
    Args:
        start_time: Giờ bắt đầu
        end_time: Giờ kết thúc
        break_hours: Giờ nghỉ
        standard_hours: Giờ chuẩn
        
    Returns:
        Dict với các key: success, total_hours, overtime_hours, error_message
    """
    result = {
        "success": False,
        "total_hours": 0.0,
        "overtime_hours": 0.0,
        "error_message": ""
    }
    
    total_hours, error = calculate_work_hours(start_time, end_time, break_hours)
    
    if total_hours < 0:
        result["error_message"] = error
        return result
    
    overtime = calculate_overtime(total_hours, standard_hours)
    
    result["success"] = True
    result["total_hours"] = total_hours
    result["overtime_hours"] = overtime
    
    return result


def format_hours(hours: float) -> str:
    """
    Format số giờ thành chuỗi dễ đọc.
    
    Args:
        hours: Số giờ (float)
    
    Returns:
        Chuỗi định dạng "X giờ Y phút" hoặc "X giờ"
    """
    h = int(hours)
    m = int((hours - h) * MINUTES_PER_HOUR)
    
    if m == 0:
        return f"{h} giờ"
    return f"{h} giờ {m} phút"


def generate_report(work_logs: List[Dict], standard_hours: float = DEFAULT_STANDARD_HOURS) -> Dict:
    """
    Tạo báo cáo từ danh sách giờ làm.
    
    Args:
        work_logs: Danh sách dict chứa thông tin giờ làm
        standard_hours: Giờ làm chuẩn
    
    Returns:
        Dict chứa thống kê báo cáo
    """
    if not work_logs:
        return {
            "total_days": 0,
            "total_hours": 0.0,
            "total_overtime": 0.0,
            "average_hours": 0.0,
            "days_with_overtime": 0,
            "max_overtime_day": None,
            "max_overtime_hours": 0.0
        }
    
    df = pd.DataFrame(work_logs)
    
    # Ensure columns exist to avoid KeyError
    if 'total_hours' not in df.columns:
        df['total_hours'] = 0.0
    if 'overtime_hours' not in df.columns:
        df['overtime_hours'] = 0.0
    
    total_days = len(df)
    total_hours = df['total_hours'].sum()
    total_overtime = df['overtime_hours'].sum()
    average_hours = total_hours / total_days if total_days > 0 else 0
    days_with_overtime = len(df[df['overtime_hours'] > 0])
    
    # Ngày có OT nhiều nhất
    max_idx = df['overtime_hours'].idxmax()
    # Check if there is any overtime at all
    if df.loc[max_idx, 'overtime_hours'] > 0:
        max_overtime_day = df.loc[max_idx, 'work_date']
        max_overtime_hours = df['overtime_hours'].max()
    else:
        max_overtime_day = None
        max_overtime_hours = 0.0
    
    return {
        "total_days": total_days,
        "total_hours": round(total_hours, 2),
        "total_overtime": round(total_overtime, 2),
        "average_hours": round(average_hours, 2),
        "days_with_overtime": days_with_overtime,
        "max_overtime_day": max_overtime_day,
        "max_overtime_hours": round(max_overtime_hours, 2)
    }


def get_week_dates(target_date: date) -> Tuple[date, date]:
    """
    Lấy ngày đầu tuần và cuối tuần (Thứ 2 - Chủ Nhật).
    
    Args:
        target_date: Ngày cần lấy tuần
        
    Returns:
        Tuple (monday, sunday)
    """
    monday = target_date - timedelta(days=target_date.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def get_month_dates(year: int, month: int) -> Tuple[date, date]:
    """
    Lấy ngày đầu tháng và cuối tháng.
    
    Args:
        year: Năm
        month: Tháng
        
    Returns:
        Tuple (first_day, last_day)
    """
    first_day = date(year, month, 1)
    
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    
    last_day = next_month - timedelta(days=1)
    
    return first_day, last_day
