# 📌 Quản Lý Giờ Làm (Work Hours Tracker)

Ứng dụng quản lý giờ làm việc, tính toán giờ làm thêm, và tùy chỉnh lịch làm.
Phiên bản mới hỗ trợ **nhiều ca làm việc trong một ngày** và **phân loại công việc**.

## 🚀 Cài Đặt

### Yêu Cầu Hệ Thống
- Python 3.8 trở lên
- pip (trình quản lý package Python)

### Các Bước Cài Đặt

1. **Mở Terminal/Command Prompt** và di chuyển đến thư mục dự án:
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

## 🔄 Nâng Cấp Từ Bản Cũ

Nếu bạn đang dùng phiên bản cũ, vui lòng chạy lệnh sau để cập nhật dữ liệu:
```bash
python migration_script.py
```
Xem chi tiết tại [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md).

---

## 📖 Hướng Dẫn Sử Dụng

### Tab 1: 📝 Nhập Giờ Làm
- Chọn **Công việc** (Làm thêm, Chính thức, v.v.)
- Chọn ngày làm việc
- Nhập giờ bắt đầu và giờ kết thúc (Hỗ trợ ca qua đêm, ví dụ 22:00 hôm nay đến 06:00 hôm sau)
- Nhấn **"Lưu Ca Làm"**

### Tab 2: 📅 Lịch Làm
- Xem lịch làm việc trực quan theo tháng.
- Hiển thị ngày nghỉ, ngày có tăng ca.

### Tab 3: 📊 Báo Cáo
- Thống kê tổng giờ làm, tổng lương (ước tính).
- Tải báo cáo dạng Excel/CSV.

### Tab 4: ⚙️ Cài Đặt
- Quản lý danh sách **Công việc** (Thêm/Sửa/Xóa, đặt màu sắc, lương giờ).
- Cài đặt giờ làm chuẩn, giờ nghỉ.

---

## 📁 Cấu Trúc Thư Mục

```
quan_ly_gio_lam/
├── app.py                 # Ứng dụng chính (Streamlit UI)
├── database.py           # Core Database Logic (SQLite) - Đã fix lỗi
├── db_wrapper.py         # Wrapper (Switch giữa SQLite/Supabase)
├── calculations.py       # Logic tính toán giờ - Đã optimize
├── user_auth.py          # Xác thực người dùng
├── migration_script.py   # Script chuyển đổi dữ liệu
├── test_database.py      # Unit tests
├── requirements.txt      # Dependencies
└── README.md             # Tài liệu này
```

## 🐛 Fixes & Improvements
- Đã sửa lỗi "Table not found".
- Đã thêm chức năng quản lý nhiều Job.
- Đã tối ưu hóa tính toán ca đêm.

## 📞 Hỗ Trợ
Nếu gặp vấn đề, vui lòng kiểm tra file `CHANGELOG.md` hoặc chạy `test_database.py` để debug.
