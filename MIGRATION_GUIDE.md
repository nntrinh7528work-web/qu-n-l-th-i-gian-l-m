# 🔄 Guide Migration (Hướng Dẫn Nâng Cấp)

Nếu bạn đang sử dụng phiên bản cũ của ứng dụng và muốn nâng cấp lên phiên bản mới nhất (có hỗ trợ nhiều ca làm việc/ngày), vui lòng làm theo hướng dẫn sau để không bị mất dữ liệu.

## ⚠️ Lưu Ý Quan Trọng
- **Sao lưu dữ liệu**: Trước khi làm bất cứ điều gì, hãy copy file `work_hours.db` ra một nơi an toàn.
- **Không xóa file DB cũ**: Script sẽ đọc dữ liệu từ file cũ và ghi vào bảng mới.

## 🛠️ Các Bước Thực Hiện

### Bước 1: Cập nhật Code
Tải về toàn bộ source code mới nhất (bao gồm `migration_script.py`, `database.py`, `app.py`...).

### Bước 2: Chạy Script Migration
Mở terminal tại thư mục dự án và chạy lệnh sau:

```bash
python migration_script.py
```

Script sẽ tự động:
1. Tìm file `work_hours.db`.
2. Kiểm tra dữ liệu trong bảng cũ (`work_logs`).
3. Chuyển đổi và copy dữ liệu sang bảng mới (`work_shifts`).
4. Gán tất cả dữ liệu cũ vào một "Công việc mặc định".

### Bước 3: Kiểm Tra
Sau khi chạy script xong:
1. Mở ứng dụng: `streamlit run app.py`
2. Vào tab "Lịch Làm" hoặc "Báo Cáo".
3. Kiểm tra xem dữ liệu cũ có hiển thị đầy đủ không.

### ❓ Câu Hỏi Thường Gặp

**Q: Tôi có bị mất dữ liệu cũ không?**  
A: Không. Dữ liệu cũ vẫn nằm trong bảng `work_logs` (chúng tôi không xóa nó). Ứng dụng mới sẽ ưu tiên đọc từ bảng `work_shifts`.

**Q: Tôi có nhiều file database (ví dụ: `user1.db`, `user2.db`)?**  
A: Script migration đã được thiết kế để quét và migrate tất cả các file `.db` trong thư mục `data/` và `user_data/`.

**Q: Nếu gặp lỗi khi chạy script?**  
A: Hãy chụp ảnh màn hình lỗi và gửi cho bộ phận kỹ thuật. Bạn có thể khôi phục lại file `.db` đã sao lưu ở bước đầu.
