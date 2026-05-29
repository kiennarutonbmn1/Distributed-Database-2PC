# Hệ thống Mô phỏng Chuyển tiền Liên Ngân hàng (Giao thức 2-Phase Commit)

## Giới thiệu dự án
Đây là dự án mô phỏng giao thức Cam kết 2 Pha (2-Phase Commit - 2PC) trong Cơ sở dữ liệu phân tán. Hệ thống đóng vai trò là một Điều phối viên (Coordinator) quản lý giao dịch chuyển tiền giữa 2 ngân hàng độc lập (Bank A và Bank B) nhằm đảm bảo tính toàn vẹn dữ liệu.

## Cấu trúc hệ thống
* **Ngôn ngữ:** Python (Thư viện tích hợp: sqlite3, os, random, msvcrt).
* **Cơ sở dữ liệu:** SQLite (Hệ thống tự động sinh ra 2 file 'bank_a.db' và 'bank_b.db' đại diện cho 2 Node vật lý độc lập).
* **Nhật ký (Logging):** File 'log.txt' tự động lưu vết toàn bộ quá trình chuyển đổi trạng thái (INITIAL -> PREPARE -> READY -> COMMIT/CRASH).

## Hướng dẫn cài đặt và sử dụng
1. Tải file 'main.py' về máy tính.
2. Mở Terminal / Command Prompt tại thư mục chứa file và chạy lệnh:
   python main.py
3. Hệ thống sẽ tự động khởi tạo cơ sở dữ liệu. Vui lòng làm theo hướng dẫn trên màn hình Terminal để thực hiện chuyển tiền.
## Kịch bản lỗi (Coordinator Crash) & Khả năng phục hồi
1. Mô phỏng lỗi: Khi chọn Kịch bản 2, hệ thống sẽ giả lập sự cố Điều phối viên bị sập nguồn (Crash) ngay sau pha PREPARE nhưng trước pha COMMIT.
2. Hiện tượng: Dữ liệu tại 2 Bank rơi vào trạng thái Nghẽn. Tiền bị khóa lại (Trạng thái READY) nhưng chưa được chuyển đi.
3. Tự động phục hồi (Recovery): Khi khởi động lại chương trình (python main.py), hệ thống sẽ tự động quét giao dịch trong Tx_Logs, phát hiện giao dịch bị treo
   và thực hiện phục hồi động chuyển trạng thái sang COMMIT để đồng bộ dữ liệu.
