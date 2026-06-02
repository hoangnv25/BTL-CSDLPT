import os
import json
import sys

# Đảm bảo in ký tự Unicode tiếng Việt không bị lỗi trên Terminal Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def load_summary(filepath):
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Lỗi khi đọc file {filepath}: {e}")
        return None

def extract_metrics(summary_data):
    if not summary_data:
        return {
            "total_reqs": "N/A",
            "throughput": "N/A",
            "avg_latency": "N/A",
            "p90_latency": "N/A",
            "p95_latency": "N/A",
            "error_rate": "N/A",
            "raw": {
                "count": 0, "rate": 0, "avg": 0, "p90": 0, "p95": 0, "err": 0
            }
        }
    
    metrics = summary_data.get("metrics", {})
    
    # Số request (http_reqs)
    reqs_metric = metrics.get("http_reqs", {})
    reqs_values = reqs_metric.get("values", reqs_metric)
    total_reqs = reqs_values.get("count", 0)
    throughput_val = reqs_values.get("rate", 0)
    throughput = f"{throughput_val:.2f} req/s" if throughput_val > 0 else "N/A"
        
    # Độ trễ (http_req_duration)
    duration_metric = metrics.get("http_req_duration", {})
    duration_values = duration_metric.get("values", duration_metric)
    avg_latency_val = duration_values.get("avg", 0)
    p90_latency_val = duration_values.get("p(90)", duration_values.get("p90", 0))
    p95_latency_val = duration_values.get("p(95)", duration_values.get("p95", 0))
    
    avg_latency = f"{avg_latency_val:.2f} ms" if avg_latency_val > 0 else "N/A"
    p90_latency = f"{p90_latency_val:.2f} ms" if p90_latency_val > 0 else "N/A"
    p95_latency = f"{p95_latency_val:.2f} ms" if p95_latency_val > 0 else "N/A"
        
    # Tỷ lệ lỗi (http_req_failed)
    failed_metric = metrics.get("http_req_failed", {})
    failed_values = failed_metric.get("values", failed_metric)
    error_rate_val = failed_values.get("rate", 0)
    if "rate" not in failed_values and "fails" in failed_values and "passes" in failed_values:
        total = failed_values.get("passes", 0) + failed_values.get("fails", 0)
        error_rate_val = failed_values.get("passes", 0) / total if total > 0 else 0
    error_rate = f"{error_rate_val * 100:.2f}%" if (error_rate_val > 0 or "rate" in failed_values or "passes" in failed_values) else "0.00%"
        
    return {
        "total_reqs": total_reqs,
        "throughput": throughput,
        "avg_latency": avg_latency,
        "p90_latency": p90_latency,
        "p95_latency": p95_latency,
        "error_rate": error_rate,
        "raw": {
            "count": total_reqs,
            "rate": round(throughput_val, 2),
            "avg": round(avg_latency_val, 2),
            "p90": round(p90_latency_val, 2),
            "p95": round(p95_latency_val, 2),
            "err": round(error_rate_val * 100, 2)
        }
    }

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    centralized_path = os.path.join(base_dir, "centralized_summary.json")
    distributed_path = os.path.join(base_dir, "distributed_summary.json")
    failover_path = os.path.join(base_dir, "distributed_failover_summary.json")
    
    c_data = load_summary(centralized_path)
    d_data = load_summary(distributed_path)
    f_data = load_summary(failover_path)
    
    c_metrics = extract_metrics(c_data)
    d_metrics = extract_metrics(d_data)
    f_metrics = extract_metrics(f_data)
    
    # 1. In bảng Markdown ra terminal và lưu file comparison_result.md
    markdown_table = f"""# Bảng Kết Quả So Sánh Hiệu Năng

| Chỉ số | Tập trung (Centralized) | Phân tán (Distributed) | Phân tán khi sập 1 Node (Failover) |
| :--- | :---: | :---: | :---: |
| **Tổng số Request** | {c_metrics['total_reqs']} | {d_metrics['total_reqs']} | {f_metrics['total_reqs']} |
| **Throughput (Tốc độ xử lý)** | {c_metrics['throughput']} | {d_metrics['throughput']} | {f_metrics['throughput']} |
| **Độ trễ trung bình (Avg Latency)** | {c_metrics['avg_latency']} | {d_metrics['avg_latency']} | {f_metrics['avg_latency']} |
| **Độ trễ phân vị P90** | {c_metrics['p90_latency']} | {d_metrics['p90_latency']} | {f_metrics['p90_latency']} |
| **Độ trễ phân vị P95** | {c_metrics['p95_latency']} | {d_metrics['p95_latency']} | {f_metrics['p95_latency']} |
| **Tỷ lệ lỗi (Error %)** | {c_metrics['error_rate']} | {d_metrics['error_rate']} | {f_metrics['error_rate']} |
| **Trạng thái hoạt động** | {("Bình thường" if c_data else "Chưa chạy test")} | {("Bình thường" if d_data else "Chưa chạy test")} | {("Tự phục hồi (Auto-recovered)" if f_data else "Chưa chạy test")} |
"""
    
    print("\n" + "="*50)
    print(" KẾT QUẢ SO SÁNH HIỆU NĂNG ")
    print("="*50)
    print(markdown_table)
    print("="*50)
    
    result_path = os.path.join(base_dir, "comparison_result.md")
    try:
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(markdown_table)
        print(f"Đã lưu bảng so sánh Markdown vào: {result_path}")
    except Exception as e:
        print(f"Không thể ghi file kết quả MD: {e}")

if __name__ == "__main__":
    main()
