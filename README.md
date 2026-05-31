# Hệ thống Mô phỏng Chuyển tiền Liên Ngân hàng (Giao thức 2-Phase Commit)

## Giới thiệu dự án
Đây là dự án mô phỏng giao thức Cam kết 2 Pha (2-Phase Commit - 2PC) trong Cơ sở dữ liệu phân tán. Hệ thống đóng vai trò là một Điều phối viên (Coordinator) quản lý giao dịch chuyển tiền giữa 2 ngân hàng độc lập (Bank A và Bank B) nhằm đảm bảo tính toàn vẹn dữ liệu.

## Cấu trúc hệ thống
* **Ngôn ngữ:** Python (Thư viện tích hợp: sqlite3, os, random, msvcrt).
* - 'main.py': Logic điều phối giao dịch.
  - 'func.py': Các hàm xử lý CSDL và logging.
  - 'log.txt': Nhật ký hệ thống.
* **Cơ sở dữ liệu:** SQLite (Hệ thống tự động sinh ra 2 file 'bank_a.db' và 'bank_b.db' đại diện cho 2 Node vật lý độc lập).
* **Nhật ký (Logging):** File 'log.txt' tự động lưu vết toàn bộ quá trình chuyển đổi trạng thái (INITIAL -> PREPARE -> READY -> COMMIT/CRASH).

## Hướng dẫn cài đặt và sử dụng
1. Tải file 'main.py' và 'func' về máy tính.
2. Mở Terminal / Command Prompt tại thư mục chứa file và chạy lệnh:
   python main.py
3. Hệ thống sẽ tự động khởi tạo cơ sở dữ liệu. Vui lòng làm theo hướng dẫn trên màn hình Terminal để thực hiện chuyển tiền.
4. Theo dõi kết quả: Kiểm tra file 'log.txt' hoặc dùng DB Browser để mở 'bank_a.db' và 'bank_b.db'.

## Kịch bản lỗi (Coordinator Crash) & Khả năng phục hồi
1. Mô phỏng lỗi: Khi chọn Kịch bản , hệ thống sẽ giả lập sự cố Điều phối viên bị sập nguồn (Crash):
   -Kịch bản 2 (Coordinator Crash at Ready): Điều phối viên sập nguồn ngay sau khi các Participant đã ở trạng thái READY. Dữ liệu tại hai ngân hàng bị "treo".
   -Kịch bản 3 (Partial Commit): Bank A đã hoàn tất COMMIT nhưng Bank B chưa thể thực hiện khởi tạo do không nhận được phản hồi.
   -Kịch bản 4 (Split-Brain/Illegal Commit): Phát hiện trạng thái không nhất quán (Bank A chưa chuyển trạng thái commit nhưng Bank B lạm quyền COMMIT). Hệ thống tự động kích hoạt trạng thái WARNING.
   -Kịch bản 5 (Abort-Commit Mismatch): Xung đột giữa trạng thái hủy (ABORT) của Bank A và hoàn tất (COMMIT) của Bank B.
2. Tự động phục hồi (Recovery): Khi khởi động lại chương trình (python main.py), hệ thống sẽ tự động quét giao dịch trong Tx_Logs, phát hiện giao dịch bị treo
   và thực hiện phục hồi động chuyển trạng thái để đồng bộ dữ liệu:
   -Quét trạng thái (State Scanning): Hệ thống quét bảng Tx_Logs trên cả hai Node (Bank A và Bank B) để tìm các giao dịch chưa kết thúc (đang ở trạng thái PREPARE, READY, hoặc WARNING).
   -Phân tích sự thống nhất (Consistency Check):
      + Nếu giao dịch ở READY trên cả hai node: Hệ thống tự động thực hiện COMMIT để đồng bộ.
      + Nếu phát hiện trạng thái WARNING (vi phạm giao thức): Hệ thống khóa giao dịch và đưa vào hàng đợi cần can thiệp thủ công, đảm bảo không tự ý thay đổi dữ liệu khi chưa rõ ràng.
   -Tự động cập nhật (Auto-Sync): Thực hiện lệnh COMMIT hoặc ROLLBACK đồng bộ dựa trên trạng thái đã ghi trong Log, đảm bảo dữ liệu quay về trạng thái nhất quán ACID.
