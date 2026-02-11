# -*- coding: utf-8 -*-
"""
Ứng Dụng Quản Lý Giờ Làm
========================
Ứng dụng Streamlit để quản lý giờ làm việc, tính toán giờ làm thêm,
và tùy chỉnh lịch làm việc.

Tác giả: AI Assistant
Ngôn ngữ: Tiếng Việt
"""

# Thiết lập UTF-8 encoding cho Windows
import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, time, timedelta
import calendar
from io import BytesIO
import time as time_module  # For loading states

# Import các module nội bộ
import db_wrapper as db  # Tự động chọn Supabase hoặc SQLite
import database  # Direct access for low-level operations
import calculations as calc

# ==================== CẤU HÌNH TRANG ====================

st.set_page_config(
    page_title="Work Tracker Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== CSS TÙY CHỈNH (GEN Z STYLE) ====================
# Chỉ render CSS một lần để tăng hiệu suất
if "css_rendered" not in st.session_state:
    st.session_state.css_rendered = True
    
CSS_STYLES = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(to right, #FF0080, #FF8C00, #40E0D0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    .stat-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 24px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }

    .stat-card h3 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(45deg, #fff, #ccc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .stat-card p {
        margin-top: 5px;
        font-size: 1rem;
        font-weight: 600;
        opacity: 0.8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .result-box {
        background: #1E1E2E;
        border: 2px solid #3B82F6;
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.3);
    }
    
    .result-box h4 {
        color: #60A5FA;
        font-size: 1.2rem;
        text-transform: uppercase;
    }

    .stButton button {
        border-radius: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .cal-cell {
        border-radius: 16px;
        padding: 12px;
        text-align: center;
        margin: 4px;
    }
    
    .cal-cell.worked {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
        border: none;
        color: white;
    }
    
    .cal-cell.holiday {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
        border: none;
        color: white;
    }
    
    .cal-day-num {
        font-weight: 800;
        font-size: 1.2rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: rgba(255,255,255,0.05);
        padding: 10px;
        border-radius: 20px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        border-radius: 15px;
        font-weight: 700;
        font-size: 1rem;
        border: none !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #8B5CF6, #EC4899);
        color: white !important;
        box-shadow: 0 4px 15px rgba(236, 72, 153, 0.4);
    }
</style>
"""
st.markdown(CSS_STYLES, unsafe_allow_html=True)


# ==================== KHỞI TẠO DATABASE ====================
# Khởi tạo database trực tiếp, không cần đăng nhập
try:
    db.init_database()
    st.session_state.db_initialized = True
except Exception as e:
    # Log error nhưng không dừng app
    print(f"Database init warning: {e}")

# ==================== HEADER ====================

st.markdown('<h1 class="main-header">✨ Quản Lý Giờ Làm 🚀</h1>', unsafe_allow_html=True)

# ==================== DASHBOARD TỔNG QUAN ====================

# Hàm tính dashboard data với caching
# Giảm TTL xuống 60s để cập nhật nhanh hơn sau khi thay đổi
@st.cache_data(ttl=60, show_spinner=False)
def get_dashboard_data(month, year, today_str):
    """Lấy dữ liệu dashboard với caching."""
    month_start = date(year, month, 1)
    today = date.fromisoformat(today_str)
    
    # Lấy tất cả ca làm việc trong tháng
    all_shifts_month = db.get_shifts_by_range(month_start, today)
    all_jobs = db.get_all_jobs()
    job_map = {j['id']: j for j in all_jobs}
    
    # Tính tổng
    total_hours = 0
    total_salary = 0
    work_days = set()
    
    for shift in all_shifts_month:
        hours = shift.get('total_hours', 0)
        job_id = shift.get('job_id', 0)
        hourly_rate = job_map.get(job_id, {}).get('hourly_rate', 0)
        
        total_hours += hours
        total_salary += hours * hourly_rate
        work_days.add(shift.get('work_date'))
    
    return {
        'total_hours': total_hours,
        'total_salary': total_salary,
        'total_days': len(work_days)
    }

# Lấy dữ liệu tháng hiện tại
current_month = date.today().month
current_year = date.today().year

# Sử dụng cached function
dashboard_data = get_dashboard_data(current_month, current_year, date.today().isoformat())
total_hours_month = dashboard_data['total_hours']
total_salary_month = dashboard_data['total_salary']
total_days_month = dashboard_data['total_days']

# Hiển thị Dashboard
col_d1, col_d2, col_d3, col_d4 = st.columns(4)

with col_d1:
    st.markdown(f"""
    <div class="stat-card" style="background: linear-gradient(135deg, #FF0080 0%, #7928CA 100%);">
        <h3>📅 {total_days_month}</h3>
        <p>Ngày làm</p>
    </div>
    """, unsafe_allow_html=True)

with col_d2:
    st.markdown(f"""
    <div class="stat-card" style="background: linear-gradient(135deg, #4AF699 0%, #12B886 100%);">
        <h3>⏱️ {total_hours_month:.1f}h</h3>
        <p>Tổng giờ</p>
    </div>
    """, unsafe_allow_html=True)

with col_d3:
    st.markdown(f"""
    <div class="stat-card" style="background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);">
        <h3>💸 {total_salary_month:,.0f}</h3>
        <p>Lương (Yen)</p>
    </div>
    """, unsafe_allow_html=True)

with col_d4:
    avg_per_day = total_salary_month / total_days_month if total_days_month > 0 else 0
    st.markdown(f"""
    <div class="stat-card" style="background: linear-gradient(135deg, #00C6FB 0%, #005BEA 100%);">
        <h3>🔥 {avg_per_day:,.0f}</h3>
        <p>TB/ngày</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==================== TABS ====================

tab1, tab2, tab3, tab4 = st.tabs([
    "🎮 Nhập Giờ", 
    "📅 Lịch Làm", 
    "📈 Báo Cáo", 
    "⚙️ Cài Đặt"
])

# ==================== TAB 1: NHẬP GIỜ LÀM ====================

with tab1:
    st.header("🎮 Nhập Giờ Làm Việc")
    
    # ==================== QUICK ENTRY MODE ====================
    st.markdown("### ⚡ Nhập Nhanh")
    
    # Lấy danh sách công việc cho quick entry
    quick_jobs = db.get_all_jobs()
    quick_job_map = {j['id']: j for j in quick_jobs}
    
    if quick_jobs:
        quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
        
        # Lấy job đầu tiên làm mặc định
        default_job = quick_jobs[0] if quick_jobs else None
        
        with quick_col1:
            if st.button("☀️ Ca Sáng 8h\n(8:00-17:00)", use_container_width=True, key="quick_morning"):
                if default_job:
                    with st.spinner("Đang thêm ca sáng..."):
                        time_module.sleep(0.3)
                        shift_id = db.add_work_shift(
                            work_date=date.today(),
                            shift_name="Ca Sáng",
                            start_time="08:00",
                            end_time="17:00",
                            break_hours=1.0,
                            total_hours=8.0,
                            notes="Nhập Nhanh",
                            job_id=default_job['id']
                        )
                        if shift_id and shift_id > 0:
                            st.success("✅ Đã thêm ca sáng 8h thành công!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ Lỗi khi thêm ca sáng!")
        
        with quick_col2:
            if st.button("🌙 Ca Tối 8h\n(17:00-02:00)", use_container_width=True, key="quick_evening"):
                if default_job:
                    with st.spinner("Đang thêm ca tối..."):
                        time_module.sleep(0.3)
                        shift_id = db.add_work_shift(
                            work_date=date.today(),
                            shift_name="Ca Tối",
                            start_time="17:00",
                            end_time="02:00",
                            break_hours=1.0,
                            total_hours=8.0,
                            notes="Nhập Nhanh",
                            job_id=default_job['id']
                        )
                        if shift_id and shift_id > 0:
                            st.success("✅ Đã thêm ca tối 8h thành công!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ Lỗi khi thêm ca tối!")
        
        with quick_col3:
            if st.button("⏰ Part-time 4h\n(17:00-21:00)", use_container_width=True, key="quick_parttime"):
                if default_job:
                    with st.spinner("Đang thêm part-time..."):
                        time_module.sleep(0.3)
                        shift_id = db.add_work_shift(
                            work_date=date.today(),
                            shift_name="Part-time",
                            start_time="17:00",
                            end_time="21:00",
                            break_hours=0.0,
                            total_hours=4.0,
                            notes="Nhập Nhanh",
                            job_id=default_job['id']
                        )
                        if shift_id and shift_id > 0:
                            st.success("✅ Đã thêm part-time 4h thành công!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ Lỗi khi thêm part-time!")
        
        with quick_col4:
            if st.button("🔥 Full Day 10h\n(8:00-19:00)", use_container_width=True, key="quick_fullday"):
                if default_job:
                    with st.spinner("Đang thêm full day..."):
                        time_module.sleep(0.3)
                        shift_id = db.add_work_shift(
                            work_date=date.today(),
                            shift_name="Full Day",
                            start_time="08:00",
                            end_time="19:00",
                            break_hours=1.0,
                            total_hours=10.0,
                            notes="Nhập Nhanh",
                            job_id=default_job['id']
                        )
                        if shift_id and shift_id > 0:
                            st.success("✅ Đã thêm full day 10h thành công!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ Lỗi khi thêm full day!")
        
        st.caption(f"💡 Quick Entry sẽ log vào **{default_job['job_name']}** cho **hôm nay**")
    
    st.markdown("---")
    
    # ==================== NHẬP CHI TIẾT ====================
    st.markdown("### 📝 Nhập Chi Tiết")
    
    # Chọn ngày
    work_date = st.date_input(
        "📅 Chọn ngày làm việc:",
        value=date.today(),
        format="DD/MM/YYYY",
        key="main_work_date"
    )
    
    # Kiểm tra ngày nghỉ
    is_hol, hol_desc = db.is_holiday(work_date)
    if is_hol:
        st.warning(f"⚠️ Ngày này là ngày nghỉ: **{hol_desc}**")
    
    # Lấy các ca làm việc hiện có
    existing_shifts = db.get_shifts_by_date(work_date)
    standard_hours = db.get_standard_hours()
    total_hours_day = 0  # Khởi tạo biến
    
    # Hiển thị các ca đã có
    if existing_shifts:
        st.subheader(f"📌 Các Ca Làm Việc Ngày {work_date.strftime('%d/%m/%Y')}")
        
        # Tính tổng giờ và lương
        total_hours_day = sum(s['total_hours'] for s in existing_shifts)
        
        # Tính lương ước tính cho ngày này
        all_jobs = db.get_all_jobs()
        job_map = {j['id']: j for j in all_jobs}
        total_salary_day = 0
        
        for shift in existing_shifts:
            job_id = shift.get('job_id', 1)
            if job_id in job_map:
                hourly_rate = job_map[job_id]['hourly_rate']
                total_salary_day += shift['total_hours'] * hourly_rate
        
        # Hiển thị metrics
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("🎯 Số ca", f"{len(existing_shifts)} ca")
        with col_m2:
            st.metric("⌛ Tổng giờ", calc.format_hours(total_hours_day))
        with col_m3:
            st.metric("💝 Lương ngày", f"{total_salary_day:,.0f} Yen")
        
        st.markdown("---")
        
        # Hiển thị từng ca với thông tin lương
        for i, shift in enumerate(existing_shifts):
            job_id = shift.get('job_id', 1)
            job_name = job_map.get(job_id, {}).get('job_name', 'N/A')
            hourly_rate = job_map.get(job_id, {}).get('hourly_rate', 0)
            shift_salary = shift['total_hours'] * hourly_rate
            
            with st.expander(f"🌟 {shift['shift_name']} - {job_name} ({shift['total_hours']}h = {shift_salary:,.0f} Yen)", expanded=False):
                col_info, col_action = st.columns([3, 1])
                
                with col_info:
                    st.write(f"**Nơi làm:** {job_name}")
                    st.write(f"**Thời gian:** {shift['start_time']} - {shift['end_time']}")
                    st.write(f"**Nghỉ:** {shift['break_hours']} giờ")
                    st.write(f"**Tổng giờ:** {calc.format_hours(shift['total_hours'])}")
                    st.write(f"**Lương:** {shift_salary:,.0f} Yen ({hourly_rate:,.0f} Yen/h)")
                    if shift['notes']:
                        st.write(f"**Ghi chú:** {shift['notes']}")
                
                with col_action:
                    if st.button("🗑️ Xóa", key=f"del_shift_{shift['id']}", use_container_width=True):
                        if db.delete_work_shift(shift['id']):
                            st.success("Đã xóa ca!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("Lỗi khi xóa!")
        
        st.markdown("---")
    
    # Form thêm ca mới
    st.subheader("✨ Thêm Ca Làm Việc Mới")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Lấy danh sách công việc
        all_jobs = db.get_all_jobs()
        job_map = {j['id']: j for j in all_jobs}
        
        # Tạo danh sách hiển thị: Bệnh viện và Kombini trước, các công việc khác sau
        display_jobs = []
        
        # Tìm Bệnh viện và Kombini
        for name in ['Bệnh viện', 'Kombini']:
            for job in all_jobs:
                if job['job_name'] == name:
                    display_jobs.append(job)
                    break
        
        # Thêm các công việc khác (không phải Bệnh viện, Kombini, Công việc chính)
        for job in all_jobs:
            if job['job_name'] not in ['Bệnh viện', 'Kombini', 'Công việc chính', 'Công việc khác']:
                display_jobs.append(job)
        
        # Nếu không có job nào, dùng tất cả
        if not display_jobs:
            display_jobs = all_jobs
        
        # Chọn nơi làm việc bằng Radio Button
        if display_jobs:
            selected_job_id = st.radio(
                "🏠 Chọn Nơi Làm Việc:",
                options=[j['id'] for j in display_jobs],
                format_func=lambda x: f"{job_map[x]['job_name']} ({job_map[x]['hourly_rate']:,.0f}đ/h)",
                horizontal=True,
                key="job_radio"
            )
        else:
            selected_job_id = None
            st.warning("Chưa có công việc nào. Hãy thêm công việc bên dưới!")
        
        # Nút thêm công việc mới
        with st.expander("🌺 Thêm công việc mới"):
            new_name = st.text_input("Tên công việc:", key="new_job_name", placeholder="VD: Restaurant, Shop...")
            new_rate = st.number_input("Lương giờ (Yen):", min_value=0, value=1000, step=50, key="new_job_rate")
            
            if st.button("Thêm Công Việc", key="btn_add_job", type="primary"):
                if new_name and new_name.strip():
                    result = db.add_job(new_name.strip(), new_rate, "")
                    if result and result > 0:
                        st.success(f"Da them: {new_name} - {new_rate} Yen/h")
                        st.rerun()
                    else:
                        st.error("Loi khi them cong viec!")
                else:
                    st.warning("Vui long nhap ten cong viec!")
        
        # Tên ca
        shift_count = len(existing_shifts) + 1
        default_shift_names = ["Ca sáng", "Ca chiều", "Ca tối", "Ca đêm"]
        default_name = default_shift_names[min(shift_count - 1, len(default_shift_names) - 1)] if shift_count <= 4 else f"Ca {shift_count}"
        
        shift_name = st.text_input(
            "📛 Tên ca:",
            value=default_name,
            placeholder="Ví dụ: Ca sáng, Ca tối, Công việc 2..."
        )
        
        # Giờ bắt đầu
        col_start, col_end = st.columns(2)
        
        with col_start:
            # Đề xuất giờ bắt đầu dựa trên ca trước
            if existing_shifts:
                last_end = existing_shifts[-1]['end_time']
                h, m = map(int, last_end.split(':'))
                default_start = time(h, m)
            else:
                default_start = time(8, 0)
            
            start_time = st.time_input(
                "🌟 Giờ bắt đầu:",
                value=default_start,
                step=timedelta(minutes=15),
                key="new_shift_start"
            )
        
        with col_end:
            # Đề xuất giờ kết thúc
            default_end = time(17, 0) if not existing_shifts else time(0, 0)
            
            end_time = st.time_input(
                "🕔 Giờ kết thúc:",
                value=default_end,
                step=timedelta(minutes=15),
                key="new_shift_end",
                help="💡 Hỗ trợ ca qua đêm: ví dụ 22:00 - 06:00"
            )
        
        # Giờ nghỉ
        break_hours = st.number_input(
            "☕ Giờ nghỉ (giờ):",
            min_value=0.0,
            max_value=4.0,
            value=0.0 if existing_shifts else db.get_default_break_hours(),
            step=0.25,
            help="Để 0 nếu ca này không có nghỉ",
            key="new_shift_break"
        )
        
        # Ghi chú
        notes = st.text_input(
            "✏️ Ghi chú (tùy chọn):",
            placeholder="Ví dụ: Công việc A, dự án XYZ...",
            key="new_shift_notes"
        )
    
    with col2:
        st.subheader("👀 Xem Trước")
        
        # Chuyển đổi time sang string
        start_str = start_time.strftime("%H:%M")
        end_str = end_time.strftime("%H:%M")
        
        # Tính toán cho ca mới
        result = calc.calculate_full(start_str, end_str, break_hours, standard_hours)
        
        if result["success"]:
            # Tính tổng ngày nếu thêm ca này
            new_total_day = (total_hours_day if existing_shifts else 0) + result['total_hours']
            new_ot_day = max(0, new_total_day - standard_hours)
            
            # Hiển thị preview
            is_overnight = end_time <= start_time
            time_display = f"{start_str} - {end_str}" + (" 🌛" if is_overnight else "")
            
            # Tính lương ước tính
            job_rate = job_map.get(selected_job_id, {}).get('hourly_rate', 0) if selected_job_id else 0
            shift_salary = result['total_hours'] * job_rate
            
            st.markdown(f"""
            <div class="result-box">
                <h4>🌟 Ca: {shift_name}</h4>
                <p><strong>🌟 Thời gian:</strong> {time_display}</p>
                <p><strong>⌛ Giờ làm ca này:</strong> <span class="text-success" style="font-size: 1.3rem;">{calc.format_hours(result['total_hours'])}</span></p>
                <p><strong>💝 Lương ước tính:</strong> <span class="text-warning" style="font-size: 1.3rem;">{shift_salary:,.0f} Yen</span></p>
                <hr>
                <p><strong>📅 Tổng giờ ngày (sau khi thêm):</strong> <span style="font-size: 1.2rem;">{calc.format_hours(new_total_day)}</span></p>
            </div>
            """, unsafe_allow_html=True)
            
            # Nút thêm ca - có validation và loading state
            if st.button("✨ THÊM CA LÀM VIỆC", type="primary", use_container_width=True, key="add_shift_main"):
                # Validate form
                validation_errors = []
                
                # Validate shift name
                if not shift_name or shift_name.strip() == "":
                    validation_errors.append("❌ Tên ca không được để trống")
                elif len(shift_name) > 50:
                    validation_errors.append("❌ Tên ca không được quá 50 ký tự")
                
                # Validate job selection
                if not selected_job_id:
                    validation_errors.append("❌ Vui lòng chọn nơi làm việc")
                
                # Validate break hours
                if break_hours < 0:
                    validation_errors.append("❌ Giờ nghỉ không thể âm")
                elif break_hours >= result['total_hours'] + break_hours:
                    validation_errors.append("❌ Giờ nghỉ không thể lớn hơn tổng giờ làm")
                
                # Validate total hours > 0
                if result['total_hours'] <= 0:
                    validation_errors.append("❌ Tổng giờ làm phải lớn hơn 0")
                
                if validation_errors:
                    for error in validation_errors:
                        st.error(error)
                else:
                    # Xử lý thêm ca với loading state
                    with st.spinner("Đang thêm ca làm việc..."):
                        time_module.sleep(0.3)
                        shift_id = db.add_work_shift(
                            work_date=work_date,
                            shift_name=shift_name,
                            start_time=start_str,
                            end_time=end_str,
                            break_hours=break_hours,
                            total_hours=result['total_hours'],
                            notes=notes,
                            job_id=selected_job_id
                        )
                    
                    if shift_id and shift_id > 0:
                        st.success(f"🎉 Đã thêm {shift_name} thành công!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("😿 Lỗi khi thêm ca. Vui lòng thử lại!")
        else:
            st.markdown(f"""
            <div class="error-box">
                <p>{result['error_message']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Xóa tất cả ca của ngày
    if existing_shifts:
        st.markdown("---")
        
        # Hiển thị tổng kết ngày và nút hoàn thành
        st.subheader("🌈 Tổng Kết Ngày")
        
        col_summary1, col_summary2 = st.columns(2)
        
        with col_summary1:
            st.markdown(f"""
            <div class="result-box">
                <h4>📅 Ngày {work_date.strftime('%d/%m/%Y')}</h4>
                <p><strong>🎯 Số ca:</strong> {len(existing_shifts)} ca</p>
                <p><strong>⌛ Tổng giờ làm:</strong> <span class="text-success">{calc.format_hours(total_hours_day)}</span></p>
                <p><strong>💝 Tổng lương:</strong> <span class="text-warning">{total_salary_day:,.0f} Yen</span></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_summary2:
            # Chi tiết các ca với lương
            shifts_info = "<br>".join([
                f"• {s['shift_name']}: {s['total_hours']}h = {s['total_hours'] * job_map.get(s.get('job_id', 1), {}).get('hourly_rate', 0):,.0f} Yen"
                for s in existing_shifts
            ])
            st.markdown(f"""
            <div class="result-box" style="font-size: 0.9rem;">
                <h4>📌 Chi Tiết Các Ca</h4>
                {shifts_info}
            </div>
            """, unsafe_allow_html=True)
        
        # Nút Hoàn thành và Xóa
        col_complete, col_delete = st.columns([2, 1])
        
        with col_complete:
            if st.button("🎊 Hoàn Thành Nhập Liệu", type="primary", use_container_width=True):
                st.success(f"""
                🎊 **Đã hoàn thành nhập liệu cho ngày {work_date.strftime('%d/%m/%Y')}!**
                
                - 📅 Số ca: **{len(existing_shifts)} ca**
                - ⌛ Tổng giờ: **{calc.format_hours(total_hours_day)}**
                - 💝 Tổng lương: **{total_salary_day:,.0f} Yen**
                
                Bạn có thể xem trong tab **🗓️ Lịch Làm** để kiểm tra.
                """)
        
        with col_delete:
            if st.button("🗑️ Xóa Tất Cả", use_container_width=True):
                if db.delete_work_log(work_date):
                    st.success("🗑️ Đã xóa tất cả ca!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("😿 Lỗi khi xóa!")

# ==================== TAB 2: LỊCH LÀM ====================

with tab2:
    st.header("🗓️ Lịch Làm Việc")
    
    # Chọn tháng/năm
    col_month, col_year, col_view = st.columns([1, 1, 1])
    
    with col_month:
        selected_month = st.selectbox(
            "Tháng:",
            options=list(range(1, 13)),
            index=date.today().month - 1,
            format_func=lambda x: f"Tháng {x}"
        )
    
    with col_year:
        current_year = date.today().year
        selected_year = st.selectbox(
            "Năm:",
            options=list(range(current_year - 5, current_year + 2)),
            index=5  # Current year
        )
    
    with col_view:
        view_type = st.selectbox(
            "Kiểu xem:",
            options=["Lịch tháng", "Danh sách"]
        )
    
    # Lấy dữ liệu tháng
    try:
        work_logs = db.get_work_logs_by_month(selected_year, selected_month)
    except Exception as e:
        # Nếu lỗi (có thể do chưa init table mới), thử init lại
        # st.warning(f"Đang đồng bộ dữ liệu... ({e})")
        db.init_database()
        try:
            work_logs = db.get_work_logs_by_month(selected_year, selected_month)
        except Exception:
            work_logs = []
    holidays = db.get_holidays_by_year(selected_year)
    holiday_dates = [h['holiday_date'] for h in holidays]
    
    # Tạo dict để tra cứu nhanh
    log_dict = {log['work_date']: log for log in work_logs}
    
    if view_type == "Lịch tháng":
        # Tạo calendar view
        st.subheader(f"📅 Lịch Tháng {selected_month}/{selected_year}")
        
        # Lấy calendar của tháng
        cal = calendar.Calendar(firstweekday=0)  # Monday = 0
        month_days = list(cal.itermonthdays2(selected_year, selected_month))
        
        # Header ngày trong tuần
        weekdays = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"]
        cols = st.columns(7)
        for i, day_name in enumerate(weekdays):
            with cols[i]:
                st.markdown(f"**{day_name}**")
        
        # Hiển thị các tuần
        week = []
        for day, weekday in month_days:
            week.append((day, weekday))
            if len(week) == 7:
                cols = st.columns(7)
                for i, (d, wd) in enumerate(week):
                    with cols[i]:
                        if d == 0:
                            st.write("")
                        else:
                            day_date = date(selected_year, selected_month, d)
                            day_str = day_date.isoformat()
                            
                            # Xác định trạng thái ngày
                            if day_str in holiday_dates:
                                st.markdown(f"""
                                <div class="cal-cell holiday">
                                    <div class="cal-day-num">{d}</div>
                                    <div class="cal-day-info text-error">🌸 Nghỉ lễ</div>
                                </div>
                                """, unsafe_allow_html=True)
                            elif day_str in log_dict:
                                log = log_dict[day_str]
                                shift_count = log.get('shift_count', 1)
                                shift_label = f"({shift_count} ca)" if shift_count > 1 else ""
                                
                                st.markdown(f"""
                                <div class="cal-cell worked">
                                    <div class="cal-day-num">{d}</div>
                                    <div class="cal-day-info text-success">✿ {log['total_hours']}h</div>
                                    <div class="cal-day-info" style="font-size:0.65rem;">{shift_label}</div>
                                </div>
                                """, unsafe_allow_html=True)
                            elif wd >= 5:  # Weekend
                                st.markdown(f"""
                                <div class="cal-cell weekend">
                                    <div class="cal-day-num text-muted">{d}</div>
                                    <div class="cal-day-info text-muted">Cuối tuần</div>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div class="cal-cell empty">
                                    <div class="cal-day-num">{d}</div>
                                    <div class="cal-day-info text-muted">-</div>
                                </div>
                                """, unsafe_allow_html=True)
                week = []
        
        # Chú thích
        st.markdown("---")
        st.markdown("""
        **Chú thích:**
        - 🟢 Xanh lá: Ngày có làm việc
        - 🔴 Đỏ: Ngày nghỉ lễ
        - ⬜ Trắng: Chưa có dữ liệu
        """)
        
        # Tổng kết tháng cho Lịch tháng
        if work_logs:
            st.markdown("---")
            st.subheader("🌈 Tổng Kết Tháng")
            
            total_days = len(work_logs)
            total_hours = sum(log['total_hours'] for log in work_logs)
            avg_hours = total_hours / total_days if total_days > 0 else 0
            
            # Hiển thị metrics (không có OT)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    label="📅 Ngày Làm Việc",
                    value=f"{total_days} ngày"
                )
            with col2:
                st.metric(
                    label="⏱️ Tổng Giờ Làm",
                    value=calc.format_hours(total_hours)
                )
            with col3:
                st.metric(
                    label="📊 Trung Bình/Ngày",
                    value=calc.format_hours(avg_hours)
                )
        else:
            st.info("ℹ️ Chưa có dữ liệu giờ làm cho tháng này.")
    
    else:  # Danh sách
        st.subheader(f"📋 Danh Sách Giờ Làm Tháng {selected_month}/{selected_year}")
        
        if work_logs:
            # Tạo DataFrame
            df = pd.DataFrame(work_logs)
            
            # Format lại các cột
            df['work_date'] = pd.to_datetime(df['work_date']).dt.strftime('%d/%m/%Y')
            df['total_hours'] = df['total_hours'].apply(lambda x: f"{x} giờ")
            
            # Đổi tên cột (bỏ OT)
            df_display = df[['work_date', 'start_time', 'end_time', 'break_hours', 'total_hours', 'notes']].copy()
            df_display.columns = ['Ngày', 'Giờ bắt đầu', 'Giờ kết thúc', 'Nghỉ (h)', 'Tổng giờ', 'Ghi chú']
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Tổng kết tháng (không OT)
            st.markdown("---")
            total_days = len(work_logs)
            total_hours = sum(log['total_hours'] for log in work_logs)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📅 Số ngày làm việc", f"{total_days} ngày")
            with col2:
                st.metric("⌛ Tổng giờ làm", calc.format_hours(total_hours))
        else:
            st.info("ℹ️ Chưa có dữ liệu giờ làm cho tháng này.")
    
    # ==================== CHỈNH SỬA CA LÀM VIỆC ====================
    st.markdown("---")
    st.subheader("✏️ Chỉnh Sửa Ca Làm Việc")
    
    # Chọn ngày để chỉnh sửa
    col_edit_date, col_edit_info = st.columns([1, 2])
    
    with col_edit_date:
        # Tạo ngày mặc định trong tháng đang xem
        default_edit_date = date(selected_year, selected_month, min(date.today().day, 28))
        edit_date = st.date_input(
            "🗓️ Chọn ngày để xem/sửa:",
            value=default_edit_date,
            format="DD/MM/YYYY",
            key="calendar_edit_date"
        )
    
    with col_edit_info:
        # Lấy các ca làm việc của ngày đã chọn
        edit_shifts = db.get_shifts_by_date(edit_date)
        
        if edit_shifts:
            total_h = sum(s['total_hours'] for s in edit_shifts)
            st.success(f"🌟 Ngày {edit_date.strftime('%d/%m/%Y')}: {len(edit_shifts)} ca, {total_h:.1f} giờ")
        else:
            st.info(f"🌸 Ngày {edit_date.strftime('%d/%m/%Y')}: Chưa có ca làm việc")
    
    # Hiển thị và cho phép chỉnh sửa các ca
    if edit_shifts:
        all_jobs = db.get_all_jobs()
        job_options = {j['id']: f"{j['job_name']} ({j['hourly_rate']:,.0f} Yen/h)" for j in all_jobs}
        job_ids = list(job_options.keys())
        
        for i, shift in enumerate(edit_shifts):
            with st.expander(f"🌟 {shift['shift_name']} ({shift['start_time']} - {shift['end_time']})", expanded=False):
                col_e1, col_e2, col_e3 = st.columns(3)
                
                with col_e1:
                    # Chỉnh sửa thời gian bắt đầu
                    try:
                        start_parts = shift['start_time'].split(':')
                        default_start = time(int(start_parts[0]), int(start_parts[1]))
                    except:
                        default_start = time(9, 0)
                    
                    new_start = st.time_input(
                        "Giờ bắt đầu:",
                        value=default_start,
                        key=f"edit_start_{shift['id']}"
                    )
                
                with col_e2:
                    # Chỉnh sửa thời gian kết thúc
                    try:
                        end_parts = shift['end_time'].split(':')
                        default_end = time(int(end_parts[0]), int(end_parts[1]))
                    except:
                        default_end = time(17, 0)
                    
                    new_end = st.time_input(
                        "Giờ kết thúc:",
                        value=default_end,
                        key=f"edit_end_{shift['id']}"
                    )
                
                with col_e3:
                    # Chỉnh sửa giờ nghỉ
                    new_break = st.number_input(
                        "Giờ nghỉ:",
                        min_value=0.0,
                        max_value=4.0,
                        value=float(shift['break_hours']),
                        step=0.25,
                        key=f"edit_break_{shift['id']}"
                    )
                
                col_e4, col_e5 = st.columns(2)
                
                with col_e4:
                    # Chỉnh sửa công việc
                    current_job_id = shift.get('job_id', 1)
                    if current_job_id in job_ids:
                        default_idx = job_ids.index(current_job_id)
                    else:
                        default_idx = 0
                    
                    new_job = st.selectbox(
                        "Nơi làm việc:",
                        options=job_ids,
                        index=default_idx,
                        format_func=lambda x: job_options.get(x, "N/A"),
                        key=f"edit_job_{shift['id']}"
                    )
                
                with col_e5:
                    # Chỉnh sửa tên ca
                    new_shift_name = st.text_input(
                        "Tên ca:",
                        value=shift['shift_name'],
                        key=f"edit_name_{shift['id']}"
                    )
                
                # Ghi chú
                new_notes = st.text_input(
                    "Ghi chú:",
                    value=shift.get('notes', ''),
                    key=f"edit_notes_{shift['id']}"
                )
                
                # Tính giờ làm mới
                start_dt = datetime.combine(edit_date, new_start)
                end_dt = datetime.combine(edit_date, new_end)
                if new_end <= new_start:  # Ca đêm
                    end_dt += timedelta(days=1)
                new_total_hours = (end_dt - start_dt).total_seconds() / 3600 - new_break
                new_total_hours = max(0, new_total_hours)
                
                st.write(f"⌛ **Giờ làm mới:** {new_total_hours:.1f} giờ")
                
                # Nút Lưu và Xóa
                col_save, col_del = st.columns(2)
                
                with col_save:
                    if st.button("💖 Lưu Thay Đổi", key=f"save_shift_{shift['id']}", type="primary"):
                        # Validation
                        if not new_shift_name or new_shift_name.strip() == "":
                            st.error("❌ Tên ca không được để trống")
                        elif new_total_hours <= 0:
                            st.error("❌ Tổng giờ làm phải lớn hơn 0")
                        else:
                            with st.spinner("Đang lưu thay đổi..."):
                                time_module.sleep(0.3)
                                success = db.update_work_shift(
                                    shift_id=shift['id'],
                                    shift_name=new_shift_name,
                                    start_time=new_start.strftime('%H:%M'),
                                    end_time=new_end.strftime('%H:%M'),
                                    break_hours=new_break,
                                    total_hours=new_total_hours,
                                    notes=new_notes
                                )
                            if success:
                                st.success("🎉 Đã cập nhật ca làm việc!")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("😿 Lỗi khi cập nhật!")
                
                with col_del:
                    # Xác nhận xóa hai bước
                    confirm_key = f'confirm_delete_{shift["id"]}'
                    if st.session_state.get(confirm_key):
                        st.warning("⚠️ Nhấn lại để xác nhận xóa")
                        if st.button("❗ XÁC NHẬN XÓA", key=f"confirm_delete_shift_{shift['id']}", type="secondary"):
                            with st.spinner("Đang xóa..."):
                                time_module.sleep(0.3)
                                if db.delete_work_shift(shift['id']):
                                    st.success("🗑️ Đã xóa ca!")
                                    st.session_state[confirm_key] = False
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("😿 Lỗi khi xóa!")
                    else:
                        if st.button("🗑️ Xóa Ca Này", key=f"delete_shift_{shift['id']}"):
                            st.session_state[confirm_key] = True
                            st.rerun()
    
    # Nút thêm ca mới cho ngày đã chọn
    st.markdown("---")
    with st.expander(f"✨ Thêm ca mới cho ngày {edit_date.strftime('%d/%m/%Y')}"):
        all_jobs = db.get_all_jobs()
        job_map = {j['id']: j for j in all_jobs}
        
        col_add1, col_add2, col_add3 = st.columns(3)
        
        with col_add1:
            add_start = st.time_input("Giờ bắt đầu:", value=time(9, 0), key="add_shift_start")
        with col_add2:
            add_end = st.time_input("Giờ kết thúc:", value=time(17, 0), key="add_shift_end")
        with col_add3:
            add_break = st.number_input("Giờ nghỉ:", min_value=0.0, max_value=4.0, value=1.0, step=0.25, key="add_shift_break")
        
        col_add4, col_add5 = st.columns(2)
        
        with col_add4:
            add_job = st.selectbox(
                "Nơi làm việc:",
                options=[j['id'] for j in all_jobs],
                format_func=lambda x: f"{job_map[x]['job_name']} ({job_map[x]['hourly_rate']:,.0f} Yen/h)",
                key="add_shift_job"
            )
        with col_add5:
            add_name = st.text_input("Tên ca:", value="Ca làm", key="add_shift_name")
        
        add_notes = st.text_input("Ghi chú:", key="add_shift_notes")
        
        # Tính giờ làm
        add_start_dt = datetime.combine(edit_date, add_start)
        add_end_dt = datetime.combine(edit_date, add_end)
        if add_end <= add_start:
            add_end_dt += timedelta(days=1)
        add_total = max(0, (add_end_dt - add_start_dt).total_seconds() / 3600 - add_break)
        
        st.write(f"⌛ **Giờ làm:** {add_total:.1f} giờ | 💝 **Lương ước tính:** {add_total * job_map.get(add_job, {}).get('hourly_rate', 0):,.0f} Yen")
        
        if st.button("✨ THÊM CA", type="primary", key="add_new_shift_calendar"):
            # Validation
            validation_errors = []
            if not add_name or add_name.strip() == "":
                validation_errors.append("❌ Tên ca không được để trống")
            if add_total <= 0:
                validation_errors.append("❌ Tổng giờ làm phải lớn hơn 0")
            
            if validation_errors:
                for err in validation_errors:
                    st.error(err)
            else:
                with st.spinner("Đang thêm ca..."):
                    time_module.sleep(0.3)
                    shift_id = db.add_work_shift(
                        work_date=edit_date,
                        shift_name=add_name,
                        start_time=add_start.strftime('%H:%M'),
                        end_time=add_end.strftime('%H:%M'),
                        break_hours=add_break,
                        total_hours=add_total,
                        notes=add_notes,
                        job_id=add_job
                    )
                if shift_id and shift_id > 0:
                    st.success(f"🎉 Đã thêm ca làm việc cho ngày {edit_date.strftime('%d/%m/%Y')}!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("😿 Lỗi khi thêm ca!")

# ==================== TAB 3: BÁO CÁO ====================

with tab3:
    st.header("✨ Báo Cáo Giờ Làm")
    
    # Chọn khoảng thời gian
    st.subheader("📅 Chọn Khoảng Thời Gian")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Mặc định: đầu tháng hiện tại
        default_start = date.today().replace(day=1)
        report_start = st.date_input(
            "Từ ngày:",
            value=default_start,
            format="DD/MM/YYYY"
        )
    
    with col2:
        report_end = st.date_input(
            "Đến ngày:",
            value=date.today(),
            format="DD/MM/YYYY"
        )
    
    if report_start > report_end:
        st.error("❌ Ngày bắt đầu phải trước ngày kết thúc!")
    else:
        # Lấy dữ liệu
        report_logs = db.get_work_logs_by_range(report_start, report_end)
        standard_hours = db.get_standard_hours()
        
        if report_logs:
            # Tạo báo cáo
            report = calc.generate_report(report_logs, standard_hours)
            
            # Hiển thị thống kê (không có OT)
            st.subheader("✨ Thống Kê Tổng Quan")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "📅 Số Ngày Làm",
                    f"{report['total_days']} ngày"
                )
            
            with col2:
                st.metric(
                    "⏱️ Tổng Giờ Làm",
                    calc.format_hours(report['total_hours'])
                )
            
            with col3:
                st.metric(
                    "📊 Trung Bình/Ngày",
                    calc.format_hours(report['average_hours'])
                )
            
            st.markdown("---")
            
            # ==================== TÍNH LƯƠNG DỰ TÍNH ====================
            st.subheader("💰 Lương Dự Tính")
            
            # Lấy tất cả ca làm việc trong khoảng thời gian
            all_shifts = db.get_shifts_by_range(report_start, report_end)
            all_jobs = db.get_all_jobs()
            job_map = {j['id']: j for j in all_jobs}
            
            # Tính lương theo từng công việc
            job_salary_data = {}
            total_salary = 0
            
            for shift in all_shifts:
                job_id = shift.get('job_id', 0)
                hours = shift.get('total_hours', 0)
                
                if job_id in job_map:
                    job_info = job_map[job_id]
                    job_name = job_info['job_name']
                    hourly_rate = job_info['hourly_rate']
                else:
                    job_name = "Chưa phân loại"
                    hourly_rate = 0
                
                if job_name not in job_salary_data:
                    job_salary_data[job_name] = {
                        'hours': 0,
                        'salary': 0,
                        'hourly_rate': hourly_rate,
                        'shift_count': 0
                    }
                
                job_salary_data[job_name]['hours'] += hours
                job_salary_data[job_name]['salary'] += hours * hourly_rate
                job_salary_data[job_name]['shift_count'] += 1
                total_salary += hours * hourly_rate
            
            # Hiển thị tổng lương
            col_salary1, col_salary2 = st.columns([1, 2])
            
            with col_salary1:
                st.markdown(f"""
                <div class="stat-card" style="background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);">
                    <h3>💴 {total_salary:,.0f}</h3>
                    <p>Yen (Lương dự tính)</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_salary2:
                # Hiển thị chi tiết theo từng công việc
                if job_salary_data:
                    st.markdown("**📋 Chi tiết theo công việc:**")
                    for job_name, data in job_salary_data.items():
                        if data['salary'] > 0:
                            st.markdown(f"""
                            - **{job_name}**: {data['hours']:.1f}h × {data['hourly_rate']:,.0f} Yen = **{data['salary']:,.0f} Yen** ({data['shift_count']} ca)
                            """)
            
            st.markdown("---")
            
            # Biểu đồ giờ làm
            st.subheader("📈 Biểu Đồ Giờ Làm")
            
            df = pd.DataFrame(report_logs)
            df['work_date'] = pd.to_datetime(df['work_date'])
            
            # Biểu đồ cột đơn giản (chỉ tổng giờ, không phân chia OT)
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=df['work_date'],
                y=df['total_hours'],
                name='Giờ làm',
                marker_color='#22C55E'
            ))
            
            fig.update_layout(
                title='Giờ Làm Theo Ngày',
                xaxis_title='Ngày',
                yaxis_title='Số Giờ',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Xuất Excel
            st.subheader("📤 Xuất Báo Cáo")
            
            # Lấy tất cả shifts để tính lương
            export_shifts = db.get_shifts_by_range(report_start, report_end)
            all_jobs_export = db.get_all_jobs()
            job_map_export = {j['id']: j for j in all_jobs_export}
            
            # Chuẩn bị dữ liệu xuất với cột lương
            export_data = []
            total_salary_export = 0
            
            for shift in export_shifts:
                job_id = shift.get('job_id', 1)
                job_info = job_map_export.get(job_id, {'job_name': 'N/A', 'hourly_rate': 0})
                salary = shift['total_hours'] * job_info['hourly_rate']
                total_salary_export += salary
                
                export_data.append({
                    'Ngày': shift['work_date'],
                    'Ca làm': shift['shift_name'],
                    'Nơi làm': job_info['job_name'],
                    'Giờ BĐ': shift['start_time'],
                    'Giờ KT': shift['end_time'],
                    'Nghỉ (h)': shift['break_hours'],
                    'Tổng giờ': shift['total_hours'],
                    'Lương/h': job_info['hourly_rate'],
                    'Lương ca': salary,
                    'Ghi chú': shift.get('notes', '')
                })
            
            if export_data:
                df_export = pd.DataFrame(export_data)
                
                # Thêm dòng tổng kết
                summary_row = {
                    'Ngày': 'TỔNG CỘNG',
                    'Ca làm': '',
                    'Nơi làm': '',
                    'Giờ BĐ': '',
                    'Giờ KT': '',
                    'Nghỉ (h)': '',
                    'Tổng giờ': sum(s['total_hours'] for s in export_shifts),
                    'Lương/h': '',
                    'Lương ca': total_salary_export,
                    'Ghi chú': ''
                }
                df_export = pd.concat([df_export, pd.DataFrame([summary_row])], ignore_index=True)
                
                # Tạo file Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_export.to_excel(writer, sheet_name='Bao Cao Gio Lam', index=False)
                
                excel_data = output.getvalue()
                
                col_export1, col_export2 = st.columns(2)
                
                with col_export1:
                    st.download_button(
                        label="💾 Tải Excel",
                        data=excel_data,
                        file_name=f"bao_cao_{report_start.strftime('%d%m%Y')}_{report_end.strftime('%d%m%Y')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                with col_export2:
                    # Export CSV
                    csv_data = df_export.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📄 Tải CSV",
                        data=csv_data,
                        file_name=f"bao_cao_{report_start.strftime('%d%m%Y')}_{report_end.strftime('%d%m%Y')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                st.success(f"📊 Tổng lương trong kỳ: **{total_salary_export:,.0f} Yen**")
            
            # ==================== TÍNH LƯƠNG ====================
            st.markdown("---")
            st.subheader("💝 Tính Lương Theo Giờ")
            
            # Lấy tất cả shifts trong khoảng thời gian báo cáo
            shifts_data = db.get_shifts_by_range(report_start, report_end)
            
            if shifts_data:
                # Lấy danh sách công việc
                all_jobs = db.get_all_jobs()
                job_map = {j['id']: j for j in all_jobs}
                
                # Tính lương theo từng công việc
                job_salary = {}
                total_hours_all = 0
                total_salary_all = 0
                
                for shift in shifts_data:
                    job_id = shift.get('job_id') or 1
                    job_info = job_map.get(job_id, {'job_name': 'Chua phan loai', 'hourly_rate': 0})
                    job_name = job_info.get('job_name', 'Chua phan loai')
                    hourly_rate = job_info.get('hourly_rate', 0)
                    hours = shift['total_hours']
                    
                    if job_id not in job_salary:
                        job_salary[job_id] = {
                            'job_id': job_id,
                            'job_name': job_name,
                            'hourly_rate': hourly_rate,
                            'total_hours': 0,
                            'shift_count': 0,
                            'base_salary': 0
                        }
                    
                    job_salary[job_id]['total_hours'] += hours
                    job_salary[job_id]['shift_count'] += 1
                    job_salary[job_id]['base_salary'] += hours * hourly_rate
                    total_hours_all += hours
                    total_salary_all += hours * hourly_rate
                
                # Hiển thị tổng quan lương
                col_sal1, col_sal2, col_sal3 = st.columns(3)
                
                with col_sal1:
                    st.metric(
                        "💝 Tổng Lương",
                        f"{total_salary_all:,.0f} Yen"
                    )
                
                with col_sal2:
                    st.metric(
                        "⌛ Tổng Giờ",
                        f"{total_hours_all:.1f} giờ"
                    )
                
                with col_sal3:
                    avg_rate = total_salary_all / total_hours_all if total_hours_all > 0 else 0
                    st.metric(
                        "✨ TB Lương/Giờ",
                        f"{avg_rate:,.0f} Yen/h"
                    )
                
                # Chi tiết theo công việc
                if job_salary:
                    st.markdown("---")
                    st.markdown("**📌 Chi Tiết Lương Theo Công Việc:**")
                    
                    for job_id, job in job_salary.items():
                        with st.expander(f"🏠 {job['job_name']} - {job['total_hours']:.1f}h = {job['base_salary']:,.0f} Yen"):
                            col_j1, col_j2, col_j3 = st.columns(3)
                            with col_j1:
                                st.write(f"**Lương giờ:** {job['hourly_rate']:,.0f} Yen/h")
                            with col_j2:
                                st.write(f"**Số ca:** {job['shift_count']} ca")
                            with col_j3:
                                st.write(f"**Tổng giờ:** {job['total_hours']:.1f} giờ")
                            
                            st.markdown(f"**Tổng lương:** `{job['base_salary']:,.0f} Yen` = {job['total_hours']:.1f}h × {job['hourly_rate']:,.0f} Yen/h")
                    
                    # Biểu đồ phân bổ lương theo công việc
                    if len(job_salary) > 1:
                        fig_salary = px.pie(
                            values=[j['base_salary'] for j in job_salary.values()],
                            names=[j['job_name'] for j in job_salary.values()],
                            title='Phan Bo Luong Theo Cong Viec',
                            color_discrete_sequence=px.colors.qualitative.Pastel
                        )
                        st.plotly_chart(fig_salary, use_container_width=True)
                
                # Bảng tổng hợp lương
                st.markdown("---")
                st.markdown(f"""
                <div class="result-box" style="text-align: center;">
                    <h3>💝 TONG LUONG ({report_start.strftime('%d/%m')} - {report_end.strftime('%d/%m/%Y')})</h3>
                    <table style="width: 100%; margin-top: 1rem;">
                        <tr style="border-bottom: 2px solid #667eea;">
                            <td style="text-align: left; padding: 0.5rem; font-size: 1.2rem;"><strong>TONG CONG ({total_hours_all:.1f} gio)</strong></td>
                            <td style="text-align: right; padding: 0.5rem; font-size: 1.5rem; color: #22C55E;"><strong>{total_salary_all:,.0f} Yen</strong></td>
                        </tr>
                    </table>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("🌸 Chua co du lieu de tinh luong. Hay nhap gio lam truoc!")
                
        else:
            st.info("ℹ️ Không có dữ liệu trong khoảng thời gian này.")

# ==================== TAB 4: TÙY CHỈNH ====================

with tab4:
    st.header("⚙️ Cài Đặt")
    
    # Cài đặt giờ làm
    st.subheader("🌟 Cài Đặt Giờ Làm")
    
    col1, col2 = st.columns(2)
    
    with col1:
        current_standard = db.get_standard_hours()
        new_standard = st.number_input(
            "Giờ làm chuẩn (giờ/ngày):",
            min_value=1.0,
            max_value=12.0,
            value=current_standard,
            step=0.5,
            help="Số giờ làm việc tiêu chuẩn mỗi ngày. Giờ làm vượt quá sẽ tính là giờ làm thêm."
        )
        
        if st.button("💖 LƯU GIờ CHUẨN", key="save_standard"):
            with st.spinner("Đang lưu..."):
                time_module.sleep(0.3)
                if db.update_setting("standard_hours", str(new_standard)):
                    st.success(f"💫 Đã cập nhật giờ làm chuẩn: {new_standard} giờ")
                else:
                    st.error("😿 Lỗi khi lưu!")
    
    with col2:
        current_break = db.get_default_break_hours()
        new_break = st.number_input(
            "Giờ nghỉ mặc định (giờ):",
            min_value=0.0,
            max_value=3.0,
            value=current_break,
            step=0.25,
            help="Thời gian nghỉ trưa và nghỉ giải lao mặc định."
        )
        
        if st.button("💖 LƯU GIờ NGHỈ", key="save_break"):
            with st.spinner("Đang lưu..."):
                time_module.sleep(0.3)
                if db.update_setting("break_hours", str(new_break)):
                    st.success(f"💫 Đã cập nhật giờ nghỉ mặc định: {new_break} giờ")
                else:
                    st.error("😿 Lỗi khi lưu!")
    
    st.markdown("---")
    
    # ==================== QUẢN LÝ CÔNG VIỆC ====================
    st.subheader("🏠 Quản Lý Công Việc & Lương Giờ")
    
    col_job1, col_job2 = st.columns([1, 2])
    
    with col_job1:
        st.markdown("**🌺 Thêm Công Việc Mới**")
        
        settings_job_name = st.text_input(
            "Tên công việc:",
            placeholder="Ví dụ: Công việc A, Part-time B...",
            key="settings_new_job_name"
        )
        
        settings_hourly_rate = st.number_input(
            "Lương giờ (VNĐ):",
            min_value=0,
            max_value=1000000,
            value=50000,
            step=5000,
            key="settings_hourly_rate",
            help="Số tiền lương cho mỗi giờ làm việc"
        )
        
        settings_job_desc = st.text_input(
            "Mô tả (tùy chọn):",
            placeholder="Mô tả ngắn về công việc",
            key="settings_job_desc"
        )
        
        if st.button("🌺 THÊM CÔNG VIỆC", type="primary", key="settings_add_job"):
            if settings_job_name and settings_job_name.strip():
                if len(settings_job_name) > 50:
                    st.error("❌ Tên công việc không được quá 50 ký tự")
                elif settings_hourly_rate <= 0:
                    st.error("❌ Lương giờ phải lớn hơn 0")
                else:
                    with st.spinner("Đang thêm công việc..."):
                        time_module.sleep(0.3)
                        job_id = db.add_job(settings_job_name.strip(), settings_hourly_rate, settings_job_desc)
                        if job_id and job_id > 0:
                            st.success(f"✅ Đã thêm công việc: {settings_job_name}")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ Lỗi khi thêm công việc!")
            else:
                st.warning("⚠️ Vui lòng nhập tên công việc!")
    
    with col_job2:
        st.markdown("**📋 Danh Sách Công Việc**")
        
        jobs = db.get_all_jobs()
        
        if jobs:
            for job in jobs:
                with st.expander(f"🏠 {job['job_name']} - {job['hourly_rate']:,.0f} Yen/h"):
                    col_edit1, col_edit2 = st.columns([2, 1])
                    
                    with col_edit1:
                        # Chỉnh sửa tên công việc
                        updated_name = st.text_input(
                            "Tên công việc:",
                            value=job['job_name'],
                            key=f"name_{job['id']}"
                        )
                        
                        # Chỉnh sửa lương giờ
                        updated_rate = st.number_input(
                            f"Lương giờ (Yen/h):",
                            min_value=0,
                            max_value=1000000,
                            value=int(job['hourly_rate']),
                            step=100,
                            key=f"rate_{job['id']}"
                        )
                        
                        # Chỉnh sửa mô tả
                        updated_desc = st.text_input(
                            "Mô tả:",
                            value=job.get('description', ''),
                            key=f"desc_{job['id']}"
                        )
                        
                        if st.button("💖 Cập Nhật Công Việc", key=f"update_job_{job['id']}", type="primary"):
                            if db.update_job(job['id'], updated_name, updated_rate, updated_desc):
                                st.success("🎉 Đã cập nhật công việc!")
                                st.cache_data.clear()  # Clear cache để cập nhật dashboard
                                st.rerun()
                            else:
                                st.error("😿 Lỗi khi cập nhật!")
                    
                    with col_edit2:
                        st.write(f"**ID:** {job['id']}")
                        if job.get('description'):
                            st.write(f"**Mô tả:** {job['description']}")
                        
                        st.markdown("---")
                        st.markdown("**🗑️ Xóa Công Việc**")
                        
                        # Kiểm tra xem công việc có đang được sử dụng không
                        # Lấy số ca đang dùng công việc này (với xử lý lỗi)
                        count = 0
                        try:
                            conn = database.get_connection()
                            cursor = conn.cursor()
                            cursor.execute("SELECT COUNT(*) FROM work_shifts WHERE job_id = ?", (job['id'],))
                            count = cursor.fetchone()[0]
                            conn.close()
                        except Exception:
                            # Bảng work_shifts có thể chưa tồn tại - init lại database
                            try:
                                database.init_database()
                            except:
                                pass
                            count = 0
                        
                        if count > 0:
                            st.warning(f"⚠️ Có {count} ca đang dùng công việc này")
                            
                            # Checkbox xác nhận xóa
                            confirm_delete = st.checkbox(
                                f"Tôi xác nhận muốn xóa",
                                key=f"confirm_del_{job['id']}"
                            )
                            
                            if confirm_delete:
                                if st.button("🗑️ Xóa Công Việc", key=f"del_job_{job['id']}", type="secondary"):
                                    if db.delete_job(job['id']):
                                        st.success("🗑️ Đã xóa công việc!")
                                        st.rerun()
                                    else:
                                        st.error("😿 Lỗi khi xóa!")
                        else:
                            st.info("✅ Công việc này chưa được sử dụng")
                            if st.button("🗑️ Xóa Công Việc", key=f"del_job_{job['id']}", type="secondary"):
                                if db.delete_job(job['id']):
                                    st.success("🗑️ Đã xóa công việc!")
                                    st.rerun()
                                else:
                                    st.error("😿 Lỗi khi xóa!")
        else:
            st.info("🌸 Chưa có công việc nào. Hãy thêm công việc mới!")
    
    st.markdown("---")
    
    # Quản lý ngày nghỉ
    st.subheader("🌸 Quản Lý Ngày Nghỉ Lễ")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**➕ Thêm Ngày Nghỉ Mới**")
        
        new_holiday_date = st.date_input(
            "Chọn ngày:",
            value=date.today(),
            format="DD/MM/YYYY",
            key="new_holiday"
        )
        
        new_holiday_desc = st.text_input(
            "Mô tả:",
            placeholder="Ví dụ: Tết Nguyên Đán, 30/4, ..."
        )
        
        if st.button("➕ THÊM NGÀY NGHỈ", type="primary", key="add_holiday_btn"):
            if new_holiday_desc.strip():
                with st.spinner("Đang thêm ngày nghỉ..."):
                    time_module.sleep(0.3)
                    if db.add_holiday(new_holiday_date, new_holiday_desc.strip()):
                        st.success(f"🎉 Đã thêm ngày nghỉ: {new_holiday_date.strftime('%d/%m/%Y')} - {new_holiday_desc}")
                        st.rerun()
                    else:
                        st.error("😿 Lỗi khi thêm ngày nghỉ!")
            else:
                st.warning("⚠️ Vui lòng nhập mô tả cho ngày nghỉ!")
    
    with col2:
        st.markdown("**📋 Danh Sách Ngày Nghỉ**")
        
        holidays = db.get_all_holidays()
        
        if holidays:
            for holiday in holidays:
                hol_date = datetime.strptime(holiday['holiday_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
                col_info, col_delete = st.columns([4, 1])
                
                with col_info:
                    st.write(f"🎌 **{hol_date}** - {holiday['description']}")
                
                with col_delete:
                    if st.button("🗑️", key=f"del_{holiday['id']}", help="Xóa ngày nghỉ này"):
                        hol_date_obj = datetime.strptime(holiday['holiday_date'], '%Y-%m-%d').date()
                        if db.remove_holiday(hol_date_obj):
                            st.success("Đã xóa!")
                            st.rerun()
        else:
            st.info("ℹ️ Chưa có ngày nghỉ nào được thêm.")
        
        st.markdown("---")
        
        # Thêm nhanh ngày lễ Việt Nam
        st.markdown("**🇻🇳 Thêm Nhanh Ngày Lễ Việt Nam**")
        
        current_year = date.today().year
        vn_holidays = [
            (date(current_year, 1, 1), "Tết Dương Lịch"),
            (date(current_year, 4, 30), "Ngày Giải Phóng Miền Nam"),
            (date(current_year, 5, 1), "Ngày Quốc Tế Lao Động"),
            (date(current_year, 9, 2), "Ngày Quốc Khánh"),
        ]
        
        if st.button("🇻🇳 THÊM CÁC NGÀY LỄ CHÍNH NĂM " + str(current_year), key="add_vn_holidays"):
            with st.spinner("Đang thêm ngày lễ..."):
                time_module.sleep(0.3)
                added = 0
                for hol_date, hol_desc in vn_holidays:
                    if db.add_holiday(hol_date, hol_desc):
                        added += 1
                if added > 0:
                    st.success(f"🎉 Đã thêm {added} ngày lễ!")
                    st.rerun()
                else:
                    st.info("ℹ️ Các ngày lễ đã tồn tại trong hệ thống.")

# ==================== SIDEBAR ====================

with st.sidebar:
    st.markdown("### ✨ Thống Kê Nhanh")
    
    # Sử dụng cùng data với dashboard để đồng bộ
    # dashboard_data đã được tính ở phần đầu
    if total_days_month > 0:
        st.metric("📅 Tháng này", f"{total_days_month} ngày làm")
        st.metric("⏱️ Tổng giờ", calc.format_hours(total_hours_month))
        st.metric("💰 Tổng lương", f"{total_salary_month:,.0f} Yen")
        
        # Tính TB/ngày  
        avg_daily = total_salary_month / total_days_month if total_days_month > 0 else 0
        st.metric("📊 TB/ngày", f"{avg_daily:,.0f} Yen")
    else:
        st.info("📭 Chưa có dữ liệu tháng này")
    
    st.markdown("---")
    
    st.markdown("### 💌 Thông Tin")
    st.markdown("""
    **Quản Lý Giờ Làm** v1.0
    
    Ứng dụng giúp bạn:
    - 📝 Ghi nhận giờ làm hàng ngày
    - 🏠 Quản lý nhiều công việc
    - 💰 Tính lương theo giờ
    - 📅 Xem lịch làm việc
    - 📊 Tạo báo cáo chi tiết
    """)
    
    st.markdown("---")
    
    # Version info
    st.caption("© 2026 - Phát triển bởi AI")

