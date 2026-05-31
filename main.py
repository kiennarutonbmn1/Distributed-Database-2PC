from func import *

def main():
    # reset_tx_logs()
    khoi_tao_database_sach()


     
    while True: 
        kiem_tra_va_phuc_hoi_sau_crash()
        while True:
            print("\nCHỌN KỊCH BẢN CHẠY CHƯƠNG TRÌNH:")
            print("1. Chạy bình thường (Thành công hoàn toàn)")
            print("2. Mô phỏng CRASH khi cả 2 cùng ở trạng thái READY")
            print("3. Mô phỏng CRASH khi State Bank_A ở COMMIT mà State Bank_B chưa COMMIT)")
            print("4. Mô phỏng CRASH khi State Bank_A bị lỗi hệ thống mà State Bank_B chuyển sang  COMMIT)")
            print("5. Mô phỏng CRASH khi State Bank_A ở ABORT mà State Bank_B ở COMMIT)")
            chon_kb = input("Chọn kịch bản để chạy: ").strip()
            if chon_kb in ['1', '2', '3', '4', '5']: break

        stk_a, ten_a, so_du_a = nhap_tai_khoan_a()
        
        print("\n==================================================")
        print(" THÔNG TIN TÀI KHOẢN NGUỒN (NGÂN HÀNG A):")
        print(f" -> Số tài khoản: {stk_a}")
        print(f" -> Chủ tài khoản: {ten_a}")
        print(f" -> SỐ DƯ HIỆN TẠI : {so_du_a}$") 
        print("==================================================")
        
        try:
            stk_nhan = input("\nNhập số tài khoản đích đến (Bank B): ").strip()
        except KeyboardInterrupt:
            print("\n\nĐã nhận lệnh dừng từ người dùng. Đang thoát chương trình...")
            break 
        thong_tin_b = kiem_tra_tk_bank_b(stk_nhan)
        
        if not thong_tin_b:
            print("Số tài khoản không tồn tại ở Ngân hàng B! Giao dịch bị hủy.")
            input("\nNhấn Enter để quay lại màn hình chính...")
            continue
            
        ten_b, so_du_b_truoc = thong_tin_b
        print(f"Tìm thấy tài khoản đích: {ten_b}")

        if so_du_a <= 0:
            tx_id = f"TX_{random.randint(1000, 9999)}"
  
            with sqlite3.connect(DB_A_PATH) as conn_a:
                conn_a.execute("INSERT INTO Tx_Logs VALUES (?, ?, ?, ?, 'ABORT')", (tx_id, stk_a, stk_nhan, 0))
                ghi_log(f"[{tx_id}] Trạng thái: ABORT (Người dùng không đủ số dư để giao dịch)")
            with sqlite3.connect(DB_B_PATH) as conn_b:
                conn_b.execute("INSERT INTO Tx_Logs VALUES (?, ?, ?, ?, 'ABORT')", (tx_id, stk_a, stk_nhan, 0))
                ghi_log(f"[{tx_id}] Trạng thái: ABORT (Người dùng không đủ số dư để giao dịch)")
            
            print(f"\n[!] Lỗi: Số dư của bạn là {so_du_a}$. Không đủ điều kiện thực hiện giao dịch.")
            input("\nNhấn Enter để quay lại màn hình chính...")
            continue

        tx_id = f"TX_{random.randint(1000, 9999)}"
        ghi_log(f"--- KHỞI TẠO GIAO DỊCH MỚI: {tx_id} ---")
        
        with sqlite3.connect(DB_A_PATH) as conn_a:
            conn_a.execute("INSERT INTO Tx_Logs VALUES (?, ?, ?, ?, 'INITIAL')", (tx_id, stk_a , stk_nhan, 0))
            ghi_log(f"[{tx_id}] Trạng thái Bank_A: INITIAL ")
        with sqlite3.connect(DB_B_PATH) as conn_b:
            conn_b.execute("INSERT INTO Tx_Logs VALUES (?, ?, ?, ?, 'INITIAL')", (tx_id, stk_a, stk_nhan, 0))
            ghi_log(f"[{tx_id}] Trạng thái Bank_B: INITIAL ")
            

        print(f"\n[Thông báo] Số dư khả dụng của bạn là: {so_du_a}$")
        while True:
            chuoi_so_tien = input("Nhập số tiền cần chuyển: ").strip()
            try:
                so_tien_chuyen = float(chuoi_so_tien)
                if so_tien_chuyen <= 0 or so_tien_chuyen > so_du_a:
                    print("Số tiền nhập không hợp lệ hoặc vượt quá số dư! Vui lòng nhập lại!")
                else:
                    break
            except ValueError:
                print("Vui lòng chỉ nhập số hợp lệ!")
                

        with sqlite3.connect(DB_A_PATH) as conn_a:
            conn_a.execute("UPDATE Tx_Logs SET amount = ? WHERE tx_id = ?", (so_tien_chuyen, tx_id))
        with sqlite3.connect(DB_B_PATH) as conn_b:
            conn_b.execute("UPDATE Tx_Logs SET amount = ? WHERE tx_id = ?", (so_tien_chuyen, tx_id))
        
        #KB3
        if chon_kb == '3':
            with sqlite3.connect(DB_A_PATH) as conn_a:
                conn_a.execute("UPDATE Tx_Logs SET state = 'READY' WHERE tx_id = ?", (tx_id,))
                ghi_log(f"[{tx_id}] Trạng thái Bank_A: READY ")
            ghi_log(f"[{tx_id}] [LỖI] Bank_B không nhận được phản hồi.")
        #KB4
        elif chon_kb =='4':
            ghi_log(f"[{tx_id}] [LỖI]: Bank_A Gặp sự cố!")
            with sqlite3.connect(DB_B_PATH) as conn_b:
                conn_b.execute("UPDATE Accounts SET balance = balance + ? WHERE account_number = ?", (so_tien_chuyen, stk_nhan))
                conn_b.execute("UPDATE Tx_Logs SET state = 'COMMIT' WHERE tx_id = ?", (tx_id,))
                conn_b.commit()
                ghi_log(f"[{tx_id}] Bank_B: Cộng tiền thành công, chuyển STATE = 'COMMIT'.")
            
            
            input("Bank_A lỗi máy chủ vui lòng thử lại sau nhấn Enter để quay về menu chính...")
            continue
            
        else:
            with sqlite3.connect(DB_A_PATH) as conn_a:
                conn_a.execute("UPDATE Tx_Logs SET state = 'READY' WHERE tx_id = ?", (tx_id,))
                ghi_log(f"[{tx_id}] Trạng thái Bank_A: READY ")
            with sqlite3.connect(DB_B_PATH) as conn_b:
                conn_b.execute("UPDATE Tx_Logs SET state = 'READY' WHERE tx_id = ?", (tx_id,))
                ghi_log(f"[{tx_id}] Trạng thái Bank_B: READY ")

        print("\n[Hệ thống] Đã chuẩn bị xong (READY). Sẵn sàng xác nhận giao dịch.")


        while True:
            xac_nhan = input(f"\nBạn có chắc chắn muốn chuyển {so_tien_chuyen}$ tới tài khoản {stk_nhan} không? (yes/no): ").strip().lower()
            
            if xac_nhan == 'yes':
                print("\nGiao dịch đã được xác nhận và thực hiện.")
                break
            
            elif xac_nhan == 'no':
                with sqlite3.connect(DB_A_PATH) as conn_a:
                    conn_a.execute("UPDATE Tx_Logs SET state = 'ABORT' WHERE tx_id = ?", (tx_id,))
                    ghi_log(f"[{tx_id}] Trạng thái: ABORT (Người dùng hủy giao dịch)")
                if chon_kb == '5':
                    with sqlite3.connect(DB_B_PATH) as conn_b:
                        conn_b.execute("UPDATE Accounts SET balance = balance + ? WHERE account_number = ?", (so_tien_chuyen, stk_nhan))
                        conn_b.execute("UPDATE Tx_Logs SET state = 'COMMIT' WHERE tx_id = ?", (tx_id,))
                        conn_b.commit()
                    ghi_log(f"[{tx_id}] MÔ PHỎNG LỖI: Bank_B Trạng thái: COMMIT")
                else:
                    with sqlite3.connect(DB_B_PATH) as conn_b:
                        conn_b.execute("UPDATE Tx_Logs SET state = 'ABORT' WHERE tx_id = ?", (tx_id,))
                        conn_b.commit()
                    print("\nĐã hủy giao dịch thành công!")
                xac_nhan = 'abort_loop'
                break 
            
            else:
                print("Lựa chọn không hợp lệ! Vui lòng chỉ nhập 'yes' để xác nhận hoặc 'no' để hủy.")

        if xac_nhan == 'abort_loop':
            print("Đã hủy giao dịch.")
            input("\nNhấn Enter để quay lại màn hình chính...")
            continue


        if chon_kb == '2':
            input("\nNhấn Enter để tiếp tục")
            continue

        with sqlite3.connect(DB_A_PATH) as conn_a:
            conn_a.execute("UPDATE Accounts SET balance = balance - ? WHERE account_number = '111111'", (so_tien_chuyen,))
            conn_a.execute("UPDATE Tx_Logs SET state = 'COMMIT' WHERE tx_id = ?", (tx_id,))
            conn_a.commit()
            ghi_log(f"[{tx_id}] Bank_A: Trừ tiền thành công, chuyển STATE = 'COMMIT'.")

        if chon_kb == '3':
            ghi_log(f"[{tx_id}] LỖI: Không thể COMMIT ở B do thiếu trạng thái READY.")
        else:
            with sqlite3.connect(DB_B_PATH) as conn_b:
                conn_b.execute("UPDATE Accounts SET balance = balance + ? WHERE account_number = ?", (so_tien_chuyen, stk_nhan))
                conn_b.execute("UPDATE Tx_Logs SET state = 'COMMIT' WHERE tx_id = ?", (tx_id,))
                conn_b.commit()
                ghi_log(f"[{tx_id}] Bank_B: Cộng tiền thành công, chuyển STATE = 'COMMIT'.")

                print("\n==================================================")
                print(" GIAO DỊCH XỬ LÝ THÀNH CÔNG!")
                print("==================================================")
            


        input("\nNhấn Enter để tiếp tục giao dịch mới...")

if __name__ == "__main__":
    main()
    