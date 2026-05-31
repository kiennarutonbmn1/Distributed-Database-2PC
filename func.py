import sqlite3
import os
import random
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_A_PATH = os.path.join(BASE_DIR, 'bank_a.db')
DB_B_PATH = os.path.join(BASE_DIR, 'bank_b.db')
LOG_FILE_PATH = os.path.join(BASE_DIR, 'log.txt')

def nhap_tai_khoan_a():
    while True:
        stk_nhap = input("\nNhập số tài khoản ngân hàng A: ").strip()
        
        with sqlite3.connect(DB_A_PATH) as conn:
            cursor = conn.execute("SELECT * FROM Accounts WHERE account_number = ?", (stk_nhap,))
            tk = cursor.fetchone()
            
            if tk:
                return tk
            else:
                print("Tài khoản không tồn tại!")
                chon = input("Bạn có muốn tạo tài khoản mới không? (yes/no): ").strip().lower()
                if chon == 'yes':
                    ten_moi = input("Nhập tên chủ tài khoản: ")
                    so_du_moi = float(input("Nhập số dư khởi tạo: "))
                    with sqlite3.connect(DB_A_PATH) as conn_tao:
                        conn_tao.execute("INSERT INTO Accounts VALUES (?, ?, ?)", (stk_nhap, ten_moi, so_du_moi))
                        conn_tao.commit()
                    print("Tạo tài khoản thành công!")
                    return (stk_nhap, ten_moi, so_du_moi)
                else:
                    print("Vui lòng nhập lại số tài khoản khác.")


def reset_tx_logs():
    for db_path in [DB_A_PATH, DB_B_PATH]:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Tx_Logs")
            conn.commit()
            conn.close()
            print(f"Đã xóa sạch log trong: {db_path}")
        except Exception as e:
            print(f"Lỗi khi xóa log tại {db_path}: {e}")

def ghi_log(thong_diep):
    thoi_gian = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    noidung_log = f"[{thoi_gian}] {thong_diep}"
    
    with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
        f.write(noidung_log + "\n")

def khoi_tao_database_sach():
    with sqlite3.connect(DB_A_PATH) as conn_a:
        cursor = conn_a.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Accounts (
                            account_number TEXT PRIMARY KEY, account_name TEXT, balance REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Tx_Logs (
                            tx_id TEXT PRIMARY KEY, from_account TEXT, to_account TEXT, amount REAL, state TEXT)''')
        cursor.execute("INSERT OR IGNORE INTO Accounts VALUES ('111111', 'Nguyen Van A', 1000.0)")
        cursor.execute("INSERT OR IGNORE INTO Accounts VALUES ('222222', 'Nguyen Van B', 0.0)")
        cursor.execute("INSERT OR IGNORE INTO Accounts VALUES ('333333', 'Nguyen Van C', 20.0)")
        conn_a.commit()

    with sqlite3.connect(DB_B_PATH) as conn_b:
        cursor = conn_b.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Accounts (
                            account_number TEXT PRIMARY KEY, account_name TEXT, balance REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Tx_Logs (
                            tx_id TEXT PRIMARY KEY, from_account TEXT, to_account TEXT, amount REAL, state TEXT)''')
        cursor.execute("INSERT OR IGNORE INTO Accounts VALUES ('222222', 'Tran Thi B', 500.0)")
        cursor.execute("INSERT OR IGNORE INTO Accounts VALUES ('333333', 'Tran Thi C', 700.0)")
        conn_b.commit()

def lay_thong_tin_tk_bank_a():
    with sqlite3.connect(DB_A_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT account_number, account_name, balance FROM Accounts WHERE account_number = '111111'")
        return cursor.fetchone()

def kiem_tra_tk_bank_b(stk_nhan):
    with sqlite3.connect(DB_B_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT account_name, balance FROM Accounts WHERE account_number = ?", (stk_nhan,))
        return cursor.fetchone()

def kiem_tra_va_phuc_hoi_sau_crash():
    ghi_log("[HỆ THỐNG] Đang chạy quét phục hồi sự cố...")
    try:
        with sqlite3.connect(DB_A_PATH) as conn_a:
            tx_list = conn_a.execute("SELECT tx_id, from_account, to_account, amount, state FROM Tx_Logs").fetchall()

        if not tx_list:
            return

        for tx_id, from_acc, to_acc, amount, state_a in tx_list:
            with sqlite3.connect(DB_B_PATH) as conn_b:
                res_b = conn_b.execute("SELECT state FROM Tx_Logs WHERE tx_id = ?", (tx_id,)).fetchone()
                state_b = res_b[0] if res_b else "NOT_FOUND"

            # Bỏ qua các giao dịch đã hoàn tất hợp lệ
            if state_a == 'COMMIT' and state_b == 'COMMIT':
                continue
            if state_a == 'ABORT' and state_b == 'ABORT':
                continue

            ghi_log(f"[*] Phát hiện mâu thuẫn/treo tại giao dịch: {tx_id} (Bank_A: {state_a}, Bank_B: {state_b})")

            # 1. Kịch bản 2: Cả 2 đều READY -> Ép COMMIT toàn cục
            if state_a == 'READY' and state_b == 'READY':

                with sqlite3.connect(DB_A_PATH) as conn_a2:

                    conn_a2.execute("UPDATE Tx_Logs SET state = 'COMMIT' WHERE tx_id = ?", (tx_id,))

                    ghi_log(f"[{tx_id}] Trạng thái Bank_A: READY -> COMMIT")    

                with sqlite3.connect(DB_B_PATH) as conn_b2:

                    conn_b2.execute("UPDATE Accounts SET balance = balance + ? WHERE account_number = ?", (amount, to_acc))

                    conn_b2.execute("UPDATE Tx_Logs SET state = 'COMMIT' WHERE tx_id = ?", (tx_id,))

                    ghi_log(f"[{tx_id}] Trạng thái Bank_B: READY -> COMMIT")

                ghi_log(f"Đã xử lý giao dịch [{tx_id}] thành công")

            # 5 kịch bản 6: bên ngân hàng B hủy giao dịch thực hiện hoàn tiền
            elif state_b == 'ABORT' and state_a != 'ABORT':
                ghi_log(f"[{tx_id}] Phát hiện Bank B đã ABORT. Đang thực hiện hoàn tiền cho Bank A...")  
                with sqlite3.connect(DB_A_PATH) as conn_a_fix:
                    conn_a_fix.execute("UPDATE Accounts SET balance = balance + ? WHERE account_number = ?", (amount, from_acc))
                    conn_a_fix.execute("UPDATE Tx_Logs SET state = 'ABORT' WHERE tx_id = ?", (tx_id,))
                    conn_a_fix.commit()
                ghi_log(f"[{tx_id}] Phục hồi thành công: Đã hoàn tiền {amount}$ vào tài khoản {from_acc} và chuyển Bank A sang ABORT.")

            # 2. Kịch bản 3: A đã COMMIT, B chưa -> Ép B COMMIT theo A
            elif state_a == 'COMMIT' and state_b != 'COMMIT':
                ghi_log(f"[{tx_id}] Trạng thái Bank_A: COMMIT") 
                with sqlite3.connect(DB_B_PATH) as conn_b2:
                    conn_b2.execute("UPDATE Accounts SET balance = balance + ? WHERE account_number = ?", (amount, to_acc))
                    conn_b2.execute("UPDATE Tx_Logs SET state = 'COMMIT' WHERE tx_id = ?", (tx_id,))
                    ghi_log(f"[{tx_id}] Trạng thái Bank_B: READY -> COMMIT") 
                ghi_log(f"Đã xử lý giao dịch [{tx_id}] thành công")

            # 3. Kịch bản 5: A đã ABORT, nhưng B lại COMMIT/READY/INITIAL -> Ép B Rollback bù trừ
            elif state_a == 'ABORT' and state_b in ['INITIAL', 'READY', 'COMMIT']:
                ghi_log(f"[{tx_id}] Trạng thái Bank_A: ABORT")
                with sqlite3.connect(DB_B_PATH) as conn_b2:
                    if state_b == 'COMMIT':
                        conn_b2.execute("UPDATE Accounts SET balance = balance - ? WHERE account_number = ?", (amount, to_acc))
                        ghi_log(f"[{tx_id}] [HỆ THỐNG] Đã thu hồi {amount}$ từ tài khoản {to_acc} do giao dịch bị hủy từ bên chuyển.")
                    conn_b2.execute("UPDATE Tx_Logs SET state = 'ABORT' WHERE tx_id = ?", (tx_id,))
                    ghi_log(f"[{tx_id}] Trạng thái Bank_B: --> ABORT")

            # 4. Kịch bản 4: A đang INITIAL nhưng B lạm quyền COMMIT -> Cảnh báo xử lý giao dịch thủ công thủ công đưa về trạng thái cảnh báo
            elif state_a == 'INITIAL' and state_b == 'COMMIT':
                with sqlite3.connect(DB_B_PATH) as conn_b:
                    conn_b.execute("UPDATE Tx_Logs SET state = 'WARNING' WHERE tx_id = ?", (tx_id,))
                    conn_b.commit()
                    ghi_log(f"[{tx_id}] Trạng thái Bank_A: --> WARNING")
                    
                with sqlite3.connect(DB_A_PATH) as conn_a:
                    conn_a.execute("UPDATE Tx_Logs SET state = 'WARNING' WHERE tx_id = ?", (tx_id,))
                    conn_a.commit()
                    ghi_log(f"[{tx_id}] Trạng thái Bank_B: --> WARNING")
                ghi_log(f"[{tx_id}] CHUYỂN TRẠNG THÁI SANG: WARNING (Cần can thiệp thủ công)")


            elif state_a == 'INITIAL' and state_b == 'INITIAL':
                ghi_log(f"[{tx_id}] Dọn dẹp giao dịch INITIAL bị bỏ  -> Hủy (ABORT)")
                with sqlite3.connect(DB_A_PATH) as conn_a2:
                    conn_a2.execute("UPDATE Tx_Logs SET state = 'ABORT' WHERE tx_id = ?", (tx_id,))
                with sqlite3.connect(DB_B_PATH) as conn_b2:
                    conn_b2.execute("UPDATE Tx_Logs SET state = 'ABORT' WHERE tx_id = ?", (tx_id,))

    except sqlite3.Error as e:
        ghi_log(f"Lỗi khi phục hồi dữ liệu: {e}")

