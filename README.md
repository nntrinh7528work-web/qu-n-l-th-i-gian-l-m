# 📌 Quản Lý Giờ Làm

Ứng dụng quản lý giờ làm việc, tính toán giờ làm thêm, và tùy chỉnh lịch làm.

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

4. **Truy cập ứng dụng**: Mở trình duyệt và vào địa chỉ:
   ```
   http://localhost:8501
   ```

## 📖 Hướng Dẫn Sử Dụng

### Tab 1: 📝 Nhập Giờ Làm
- Chọn ngày làm việc
- Nhập giờ bắt đầu và giờ kết thúc
- Điều chỉnh giờ nghỉ nếu cần
- Thêm ghi chú (tùy chọn)
- Nhấn **"Lưu Giờ Làm"** để lưu

### Tab 2: 📅 Lịch Làm
- Chọn tháng/năm để xem
- Xem lịch theo dạng **Lịch tháng** hoặc **Danh sách**
- Màu sắc chú thích:
  - 🟢 Xanh: Làm đủ giờ
  - 🟡 Vàng: Có làm thêm (OT)
  - 🔴 Đỏ: Ngày nghỉ lễ

### Tab 3: 📊 Báo Cáo
- Chọn khoảng thời gian cần báo cáo
- Xem thống kê tổng quan
- Xem biểu đồ trực quan
- **Tải xuống file Excel** để lưu trữ hoặc in

### Tab 4: ⚙️ Tùy Chỉnh
- Thay đổi **giờ làm chuẩn** (mặc định: 8 giờ)
- Thay đổi **giờ nghỉ mặc định** (mặc định: 1 giờ)
- Quản lý **ngày nghỉ lễ**:
  - Thêm ngày nghỉ mới
  - Xóa ngày nghỉ
  - Thêm nhanh các ngày lễ Việt Nam

## 📁 Cấu Trúc Thư Mục

```
quan_ly_gio_lam/
├── app.py              # Ứng dụng chính
├── database.py         # Quản lý cơ sở dữ liệu SQLite
├── calculations.py     # Các hàm tính toán thời gian
├── requirements.txt    # Danh sách thư viện cần thiết
├── README.md           # Tài liệu hướng dẫn
└── work_hours.db       # Cơ sở dữ liệu (tự động tạo khi chạy)
```

## 💾 Dữ Liệu

- Dữ liệu được lưu trong file `work_hours.db` (SQLite)
- File này được tạo tự động khi chạy ứng dụng lần đầu
- Để sao lưu dữ liệu, chỉ cần copy file `work_hours.db`

## 🛠️ Khắc Phục Sự Cố

### Lỗi "Module not found"
```bash
pip install streamlit pandas plotly openpyxl
```

### Lỗi khi mở trình duyệt
- Kiểm tra xem port 8501 có bị chiếm không
- Thử chạy với port khác:
  ```bash
  streamlit run app.py --server.port 8502
  ```

### Dữ liệu không hiển thị
- Kiểm tra file `work_hours.db` có tồn tại không
- Thử xóa file `work_hours.db` và chạy lại (dữ liệu sẽ bị mất)

## 📞 Hỗ Trợ

Nếu gặp vấn đề, hãy kiểm tra:
1. Python version: `python --version`
2. Pip version: `pip --version`
3. Các thư viện đã cài: `pip list`

---

**Phiên bản:** 1.0  
**Ngôn ngữ:** Tiếng Việt  
**Nền tảng:** Web (Streamlit)
