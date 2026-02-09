# 📄 CHANGELOG

## [Unreleased]

### 🐛 Bug Fixes
- **Critical**: Đã thêm bảng `work_shifts` vào database schema để sửa lỗi "no such table: work_shifts".
- **Critical**: Thêm chức năng CRUD (Create, Read, Update, Delete) cho `work_shifts`.
- **Logic**: Sửa lỗi tính toán sai giờ làm cho ca qua đêm (ví dụ 22:00 -> 06:00).
- **Validation**: Thêm kiểm tra `job_id` hợp lệ trước khi lưu ca làm việc.
- **Error Handling**: Thêm try-except block cho tất cả các thao tác database.
- **Performance**: Thêm indexes cho bảng `work_shifts` để tăng tốc độ truy vấn.

### ⚡ Improvements
- **Refactor**: Loại bỏ "magic numbers" trong `calculations.py`, thay bằng constants.
- **Structure**: Tách biệt rõ ràng logic database wrapper cho SQLite và Supabase.
- **Testing**: Thêm unit tests (`test_database.py`) để kiểm tra tính đúng đắn của code.
- **Migration**: Thêm script `migration_script.py` để chuyển dữ liệu từ bảng cũ sang bảng mới.

### 📝 Documentation
- Cập nhật `README.md`.
- Thêm `MIGRATION_GUIDE.md` hướng dẫn nâng cấp.

---

## [1.0] - 2023-10-xx
- Initial Release.
