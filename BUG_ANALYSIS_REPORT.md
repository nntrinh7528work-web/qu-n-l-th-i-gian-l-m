# 🐞 BUG ANALYSIS REPORT

## 🚨 Critical Issues

### 1. `sqlite3.OperationalError: no such table: work_shifts`
- **Nguyên nhân:** Bảng `work_shifts` được gọi trong queries nhưng chưa bao giờ được tạo trong hàm `init_database()`.
- **Tác động:** App crash ngay lập tức khi mở Dashboard hoặc Lịch.
- **Giải pháp:** Thêm câu lệnh `CREATE TABLE` vào `database.py`.

### 2. Thiếu hàm `add_shift` / `update_shift` (CRUD)
- **Nguyên nhân:** Chỉ có code đọc dữ liệu, code ghi dữ liệu bị thiếu hoặc dùng tên cũ (`save_work_log`).
- **Tác động:** Không thể thêm ca làm việc mới với cấu trúc dữ liệu mới (Job ID, Overtime).
- **Giải pháp:** Implement đầy đủ CRUD functions.

### 3. Dữ liệu không nhất quán (Work Logs vs Work Shifts)
- **Nguyên nhân:** App đang cố gắng duy trì 2 bảng song song mà không có migration strategy rõ ràng.
- **Tác động:** Dữ liệu cũ không hiện trên giao diện mới.
- **Giải pháp:** Viết script migration check và chuyển đổi dữ liệu 1 lần.

## ⚠️ High Priority Issues

### 4. Logic tính giờ qua đêm bị sai
- **Vấn đề:** Các ca làm như 22:00 -> 06:00 thường bị tính âm hoặc sai số giờ.
- **Giải pháp:** Cập nhật hàm `calculate_work_hours` để xử lý `end_time < start_time` bằng cách cộng thêm 24h.

### 5. Validate Input yếu
- **Vấn đề:** Không check `job_id` có tồn tại hay không trước khi insert.
- **Tác động:** Gây lỗi Foreign Key hoặc dữ liệu rác.
- **Giải pháp:** Thêm validation check.

### 6. Hardcoded Paths & Magic Numbers
- **Vấn đề:** Đường dẫn DB, các hệ số (8h, 1h) được hardcode rải rác.
- **Giải pháp:** Gom về Constants hoặc Config.

## 📝 Fix Strategy

1. **Immediate Fix (Quick Fix):** Chạy script `quick_fix.py` để vá lỗi thiếu bảng ngay lập tức (Hotfix).
2. **Codebase Update:** Cập nhật `database.py` và `db_wrapper.py` với các bản vá (Patch) để hỗ trợ tính năng lâu dài.
3. **Data Migration:** Chạy `fix_critical_bugs.py` để đảm bảo user cũ không mất dữ liệu.
