# 🛠️ HƯỚNG DẪN SỬA LỖI CHI TIẾT

## Bước 1: Chuẩn bị
1. Tải toàn bộ code mới nhất về.
2. Mở thư mục dự án trong VS Code hoặc Terminal.
3. **Quan trọng:** Copy file `work_hours.db` ra chỗ khác để backup.

## Bước 2: Sửa lỗi Database (Cách nhanh)
1. Chạy lệnh:
   ```bash
   python quick_fix.py
   ```
2. Đọc thông báo. Nếu thấy "✅ Đã sửa xong", chuyển sang Bước 4.

## Bước 3: Sửa lỗi Database (Cách thủ công - nếu Bước 2 thất bại)
1. Mở file `database.py`.
2. Tìm hàm `init_database`.
3. Thêm đoạn code tạo bảng `work_shifts`:
   ```python
   cursor.execute("""
       CREATE TABLE IF NOT EXISTS work_shifts (...)
   """)
   ```
   *(Xem chi tiết trong file patch_database.py)*
4. Lưu file.

## Bước 4: Cập nhật Logic
1. Copy các hàm từ `patch_database.py`.
2. Dán vào cuối file `database.py`.
3. Copy các hàm từ `patch_db_wrapper.py`.
4. Dán vào cuối file `db_wrapper.py`.

## Bước 5: Kiểm tra
1. Chạy lại ứng dụng:
   ```bash
   streamlit run app.py
   ```
2. Thử thêm một ca làm việc mới (VD: 22:00 -> 06:00).
3. Kiểm tra xem nó có hiện trên lịch không.

## 🆘 Troubleshooting
- **Lỗi "Table not found":** Chạy lại Bước 2.
- **Lỗi "Column not found":** Có thể bạn đang dùng DB cũ quá, hãy chạy `python fix_critical_bugs.py`.
- **Lỗi Logic:** Kiểm tra lại `calculations.py`.
