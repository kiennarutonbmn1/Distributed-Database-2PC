import sqlite3
import os
import random
import msvcrt
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_A_PATH = os.path.join(BASE_DIR, 'bank_a.db')
DB_B_PATH = os.path.join(BASE_DIR, 'bank_b.db')
LOG_FILE_PATH = os.path.join(BASE_DIR, 'log.txt')

def ghi_log(thong_diep):
    """Hàm in thông báo ra Terminal đồng thời lưu vào file log.txt"""
    thoi_gian = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    noidung_log = f"[{thoi_gian}] {thong_diep}"
    
    print(thong_diep)
    
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
        cursor.execute("SELECT account_name, balance FROM Accounts WHERE account_number = '111111'")
        return cursor.fetchone()

def kiem_tra_tk_bank_b(stk_nhan):
    with sqlite3.connect(DB_B_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT account_name, balance FROM Accounts WHERE account_number = ?", (stk_nhan,))
        return cursor.fetchone()
    

def kiem_tra_va_phuc_hoi_sau_crash():
    print("\n[HỆ THỐNG] Đang kiểm tra tự động phục hồi sau sự cố...")
    ghi_log("\n[HỆ THỐNG] Đang kiểm tra tự động phục hồi sau sự cố...")
    tx_treo_a = []
    with sqlite3.connect(DB_A_PATH) as conn_a:
        cursor = conn_a.cursor()
        cursor.execute("SELECT tx_id, from_account, to_account, amount FROM Tx_Logs WHERE state = 'READY'")
        tx_treo_a = cursor.fetchall()

    if not tx_treo_a:
        print(" -> Không có giao dịch nào bị treo. Hệ thống an toàn.")
        return

    ghi_log(f"PHÁT HIỆN CÓ {len(tx_treo_a)} GIAO DỊCH BỊ TREO DO CRASH TRƯỚC ĐÓ!")

    print(f" -> PHÁT HIỆN CÓ {len(tx_treo_a)} GIAO DỊCH BỊ TREO!")
    
    for tx_id, from_acc, to_acc, amount in tx_treo_a:
        print(f"    [*] Đang tự động xử lý phục hồi động cho Giao dịch: {tx_id}")
        print(f"        [Thông tin log] Chuyển từ: {from_acc} -> Đến: {to_acc} | Số tiền: {amount}$")
        ghi_log(f"    [*] Đang tự động xử lý phục hồi động cho Giao dịch: {tx_id}")
        ghi_log(f"        [Thông tin log] Chuyển từ: {from_acc} -> Đến: {to_acc} | Số tiền: {amount}$")
        
        with sqlite3.connect(DB_B_PATH) as conn_b:
            cursor_b = conn_b.cursor()
            cursor_b.execute("SELECT state FROM Tx_Logs WHERE tx_id = ?", (tx_id,))
            res_b = cursor_b.fetchone()
            
        if res_b and res_b[0] == 'READY':

            with sqlite3.connect(DB_A_PATH) as conn_a:
                conn_a.execute("UPDATE Tx_Logs SET state = 'COMMIT' WHERE tx_id = ?", (tx_id,))
                conn_a.commit()
                ghi_log("[Bank_A] State: COMMIT")
            
            with sqlite3.connect(DB_B_PATH) as conn_b:
                conn_b.cursor().execute("UPDATE Accounts SET balance = balance + ? WHERE account_number = ?", (amount, to_acc))
                conn_b.cursor().execute("UPDATE Tx_Logs SET state = 'COMMIT' WHERE tx_id = ?", (tx_id,))
                conn_b.commit()
                ghi_log("[Bank_B] State: COMMIT")


def main():

    khoi_tao_database_sach()
    kiem_tra_va_phuc_hoi_sau_crash()
    print("==================================================")
    thong_tin_a = lay_thong_tin_tk_bank_a()
    if thong_tin_a is None:
        print("Lỗi: Không tìm thấy tài khoản Ngân hàng A trong Cơ sở dữ liệu!")
        return
    ten_a, so_du_a = thong_tin_a
    print(" THÔNG TIN TÀI KHOẢN NGUỒN (NGÂN HÀNG A):")
    print(f" -> Số tài khoản: 111111")
    print(f" -> Chủ tài khoản: {ten_a}")
    print(f" -> SỐ DƯ HIỆN TẠI : {so_du_a}$") 
    print("==================================================")
    
    while True:
        while True:
            stk_nhan = input("\n Nhập số tài khoản muốn chuyển cho ngân hàng B: ").strip()
            thong_tin_b = kiem_tra_tk_bank_b(stk_nhan)
            
            if thong_tin_b:
                ten_b, so_du_b_truoc = thong_tin_b
                print(f"Tìm thấy tài khoản đích: {ten_b}")
                break
            else:
                print("Số tài khoản không tồn tại ở Ngân hàng B!")

        print(f"\n[Thông báo] Số dư khả dụng của bạn là: {so_du_a}$")
        
        quay_lai_stk = False
        
        while True:
            print("Nhập số tiền cần chuyển (Hoặc ấn phím 0 để QUAY LẠI): ", end='', flush=True)
            
            phim = msvcrt.getch()
            
            if phim == b'0':
                print("0") 
                quay_lai_stk = True
                break
            
            ky_tu_dau = phim.decode('utf-8', errors='ignore')
            print(ky_tu_dau, end='', flush=True) 
            
            nhap_tiep = input() 
            chuoi_so_tien = ky_tu_dau + nhap_tiep
            
            try:
                so_tien_chuyen = float(chuoi_so_tien)
                
                if so_tien_chuyen <= 0 or so_tien_chuyen > so_du_a:
                    print(f"\nSố tiền nhập không hợp lệ! Phải lớn hơn 0 và nhỏ hơn hoặc bằng số dư hiện tại ({so_du_a}$).")
                    print("Vui lòng nhập lại!")
                else:
                    print(f"\nSố tiền {so_tien_chuyen}$ hợp lệ.")
                    break
            except ValueError:
                print("\nVui lòng chỉ nhập số ký tự số hợp lệ!")

        if quay_lai_stk:
            continue
            
        break
    
    print("\nCHỌN KỊCH BẢN CHẠY CHƯƠNG TRÌNH:")
    print("1. Chạy bình thường (Thành công hoàn toàn)")
    print("2. Mô phỏng CRASH (Sập nguồn ngay khi vừa READY)")
    chon_kb = input("Nhập lựa chọn (1 hoặc 2): ").strip()

    tx_id = f"TX_{random.randint(1000, 9999)}"
    ghi_log(f"\n--- BẮT ĐẦU TRANSACTION: {tx_id} ---")
    ghi_log("[Coordinator] State: INITIAL -> Đang khởi tạo giao dịch.")
    ghi_log("[Coordinator] Sent PREPARE to Bank_A and Bank_B")


    print(f"\n--- BẮT ĐẦU TRANSACTION: {tx_id} ---")
    
    # PHASE 1: PREPARE
    with sqlite3.connect(DB_A_PATH) as conn_a:
        cursor = conn_a.cursor()
        cursor.execute("UPDATE Accounts SET balance = balance - ? WHERE account_number = '111111'", (so_tien_chuyen,))

        cursor.execute("INSERT INTO Tx_Logs VALUES (?, ?, ?, ?, 'READY')", (tx_id, '111111', stk_nhan, so_tien_chuyen))
        conn_a.commit()
        ghi_log("[Bank_A] State: READY ")

    with sqlite3.connect(DB_B_PATH) as conn_b:
        cursor = conn_b.cursor()

        cursor.execute("INSERT INTO Tx_Logs VALUES (?, ?, ?, ?, 'READY')", (tx_id, '111111', stk_nhan, so_tien_chuyen))
        conn_b.commit()
        ghi_log("[Bank_B] State: READY")

    if chon_kb == '2':
        os._exit(0)

    # PHASE 2: COMMIT
    with sqlite3.connect(DB_A_PATH) as conn_a:
        cursor = conn_a.cursor()
        cursor.execute("UPDATE Tx_Logs SET state = 'COMMIT' WHERE tx_id = ?", (tx_id,))
        conn_a.commit()
        ghi_log("[Bank_A] State: COMMIT")

    with sqlite3.connect(DB_B_PATH) as conn_b:
        cursor = conn_b.cursor()
        cursor.execute("UPDATE Accounts SET balance = balance + ? WHERE account_number = ?", (so_tien_chuyen, stk_nhan))
        cursor.execute("UPDATE Tx_Logs SET state = 'COMMIT' WHERE tx_id = ?", (tx_id,))
        conn_b.commit()
        ghi_log(f"[Bank_B] State: COMMIT")

    _, so_du_a_sau = lay_thong_tin_tk_bank_a()
    _, so_du_b_sau = kiem_tra_tk_bank_b(stk_nhan)
    
    print("\n==================================================")
    print(" GIAO DỊCH XỬ LÝ THÀNH CÔNG - TỔNG KẾT SỐ DƯ MỚI")
    print("==================================================")
    print(f" Ngân hàng A ({ten_a}) : {so_du_a} -> {so_du_a_sau}$ (Đã trừ {so_tien_chuyen}$)")
    print(f" Ngân hàng B ({stk_nhan}) : {so_du_b_truoc} -> {so_du_b_sau}$ (Đã cộng {so_tien_chuyen}$)")
    print("==================================================")
    print("Hệ thống đã lưu cập nhật xuống file database thực tế.")

if __name__ == "__main__":
    main()