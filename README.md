# 📌 Quản Lý Giờ Làm (Work Hours Tracker)

Ứng dụng quản lý giờ làm việc, tính toán giờ làm thêm, và tùy chỉnh lịch làm.
Hỗ trợ **nhiều ca làm việc trong một ngày** và **phân loại công việc**.

## 🚀 Cài Đặt

### Yêu Cầu Hệ Thống
- Python 3.8 trở lên
- pip (trình quản lý package Python)

### Các Bước Cài Đặt

1. **Di chuyển đến thư mục dự án**:
   ```bash
   cd quan_ly_gio_lam
   ```

2. **Cài đặt các thư viện cần thiết**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Chạy ứng dụng**:
   ```bash
   streamlit run app.py
   ```

4. **Truy cập ứng dụng**: Mở trình duyệt và vào địa chỉ: `http://localhost:8501`

---

## 📖 Hướng Dẫn Sử Dụng

### Tab 1: 📝 Nhập Giờ Làm
- **Quick Entry**: Nhanh chóng log các ca làm việc phổ biến (Ca sáng, Ca tối, Part-time, Full day)
- **Nhập chi tiết**: Chọn công việc, ngày, giờ bắt đầu/kết thúc
- Hỗ trợ **ca qua đêm** (ví dụ: 22:00 hôm nay đến 06:00 hôm sau)

### Tab 2: 📅 Lịch Làm
- Xem lịch làm việc trực quan theo tháng
- Hiển thị ngày nghỉ, ngày có tăng ca
- Màu sắc phân biệt theo loại công việc

### Tab 3: 📊 Báo Cáo
- Thống kê tổng giờ làm, tổng lương theo từng công việc
- Biểu đồ trực quan
- Tải báo cáo dạng Excel

### Tab 4: ⚙️ Cài Đặt
- Quản lý danh sách **Công việc** (Thêm/Sửa/Xóa, đặt màu sắc, lương giờ)
- Cài đặt giờ làm chuẩn, giờ nghỉ mặc định
- Quản lý ngày nghỉ lễ

---

## 📁 Cấu Trúc Thư Mục

```
quan_ly_gio_lam/
├── app.py                 # Ứng dụng chính (Streamlit UI)
├── database.py            # Core Database Logic (SQLite)
├── db_wrapper.py          # Wrapper (Switch giữa SQLite/Supabase)
├── calculations.py        # Logic tính toán giờ làm
├── user_auth.py           # Xác thực người dùng
├── supabase_db.py         # Supabase integration (optional)
├── github_sync.py         # GitHub sync (optional)
├── requirements.txt       # Dependencies
├── work_hours.db          # Database file (tự động tạo)
├── user_data/             # Thư mục chứa database của từng user
└── .streamlit/            # Streamlit config
```

## 💾 Dữ Liệu

- Dữ liệu được lưu trong file SQLite (`work_hours.db`)
- Mỗi user có database riêng trong thư mục `user_data/`
- Để sao lưu, copy các file `.db`

## 🛠️ Khắc Phục Sự Cố

### Lỗi "Module not found"
```bash
pip install streamlit pandas plotly openpyxl supabase extra-streamlit-components
```

### Lỗi khi mở trình duyệt
```bash
streamlit run app.py --server.port 8502
```

### Kiểm tra database
```bash
python -c "import database; database.init_database(); print('OK')"
```

---

**Phiên bản:** 2.0  
**Ngôn ngữ:** Tiếng Việt  
**Nền tảng:** Web (Streamlit)
