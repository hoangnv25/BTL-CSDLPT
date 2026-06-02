import os
import subprocess
import sys

# Đảm bảo in ký tự Unicode tiếng Việt không bị lỗi trên Terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def run_cmd(cmd, desc):
    print("\n" + "=" * 60)
    print(f" BƯỚC: {desc}")
    print("=" * 60)
    print(f"Đang thực thi: {cmd}\n")
    try:
        # Chạy command và stream output trực tiếp ra terminal
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                sys.stdout.write(line)
                sys.stdout.flush()
                
        process.wait()
        return process.returncode == 0
    except Exception as e:
        print(f"Lỗi hệ thống khi chạy lệnh: {e}")
        return False

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(base_dir)
    
    # Di chuyển thư mục làm việc về thư mục gốc dự án
    os.chdir(project_dir)
    
    k6_path = r'"C:\Program Files\k6\k6.exe"'
    
    cmd_centralized = f'{k6_path} run -e TARGET_NODE=main --summary-export=test/centralized_summary.json test/benchmark_product.js'
    cmd_distributed = f'{k6_path} run -e TARGET_NODE=auto --summary-export=test/distributed_summary.json test/benchmark_product.js'
    cmd_failover = f'{k6_path} run -e TARGET_NODE=auto --summary-export=test/distributed_failover_summary.json test/benchmark_product.js'
    
    node1_stopped = False
    
    try:
        # Khởi động lại backend để reset bộ nhớ và pool kết nối trước đợt test 1
        run_cmd("docker restart csdlpt_be", "Khởi động lại Backend (Làm sạch Connection Pool)")
        import time
        print("Đang chờ 3 giây để Backend khởi động xong...")
        time.sleep(3)
        
        # 1. Chạy test Tập trung (Centralized)
        run_cmd(cmd_centralized, "Chạy thử nghiệm Tập trung (Centralized)")
        
        # Khởi động lại backend để reset Circuit Breaker về ONLINE trước đợt test 2
        run_cmd("docker restart csdlpt_be", "Khởi động lại Backend (Reset Circuit Breaker về ONLINE)")
        print("Đang chờ 3 giây để Backend khởi động xong...")
        time.sleep(3)
        
        # 2. Chạy test Phân tán (Distributed)
        run_cmd(cmd_distributed, "Chạy thử nghiệm Phân tán (Distributed) - Các Node ONLINE")
        
        # 3. Tắt Node 1 để test Failover
        print("\n" + "=" * 60)
        print(" CHUẨN BỊ TEST FAILOVER: Tắt mysql_node1")
        print("=" * 60)
        if run_cmd("docker compose kill mysql_node1", "Khai tử lập tức Container mysql_node1 (Kill)"):
            node1_stopped = True
            
            import time
            print("\n>>> Đang chờ 2 giây để cổng kết nối đóng hoàn toàn...")
            time.sleep(2)
            
            # 4. Chạy test Failover
            run_cmd(cmd_failover, "Chạy thử nghiệm Phân tán khi sập 1 Node (Failover)")
        else:
            print("!!! Cảnh báo: Không thể tắt mysql_node1. Bỏ qua bước test Failover.")
            
    except KeyboardInterrupt:
        print("\n[HỦY BỎ] Người dùng hủy chạy test bằng phím bấm Ctrl+C.")
    finally:
        # 5. Khôi phục lại Node 1 luôn luôn chạy (kể cả khi lỗi hoặc bị hủy ngang)
        if node1_stopped:
            print("\n" + "=" * 60)
            print(" DỌN DẸP HỆ THỐNG: Khởi động lại mysql_node1")
            print("=" * 60)
            run_cmd("docker compose start mysql_node1", "Kích hoạt lại Container mysql_node1")
            
        # 6. Chạy so sánh kết quả tự động
        print("\n" + "=" * 60)
        print(" TỔNG HỢP VÀ SO SÁNH SỐ LIỆU")
        print("=" * 60)
        compare_script = os.path.join(base_dir, "compare.py")
        run_cmd(f'python "{compare_script}"', "Chạy so sánh kết quả")
        
        print("\n>>> HOÀN TẤT: Anh có thể xem kết quả so sánh chi tiết tại: test/comparison_result.md")

if __name__ == "__main__":
    main()
