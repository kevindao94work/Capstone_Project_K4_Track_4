# Phương pháp đánh giá

**Tác giả:** Đào Gia Bảo — **MSSV:** 2A202602793.

## Tình trạng đánh giá

Chưa có video người thật được consent hoặc ground truth thủ công. Vì vậy không có
accuracy/F1/coverage/FPS webcam thực để báo cáo. Các lệnh dưới đây mô tả phương
pháp tái lập; chúng không khẳng định đã có dữ liệu hay kết quả.

## Chuẩn bị dữ liệu riêng tư

1. Tác giả tự quay clip MP4/AVI ngắn trong các đoạn: bình thường, chớp mắt, nhắm
   mắt duy trì, quay đầu duy trì, che mặt và quay lại nhìn thẳng. Chỉ quay người
   đã đồng ý; không dùng khi lái xe.
2. Ghi clip trong `data/private/`, không commit hoặc tải lên công khai.
3. Gắn nhãn từng khoảng bằng công cụ prompt:

   ```bash
   python scripts/annotate_events.py --output outputs/private/labels.csv \
     --annotator 'Đào Gia Bảo'
   ```

   Hoặc thêm khoảng tường minh:

   ```bash
   python scripts/annotate_events.py --output outputs/private/labels.csv \
     --start-s 0 --end-s 5 --label NORMAL --notes 'xem lại bằng video'
   ```

   Đoạn nhãn dùng `[start_s, end_s)`, phải hữu hạn, không âm, dương và không
   chồng lấp. Người gắn nhãn tự xem lại video; nhãn không được sinh từ output của
   mô hình. `UNKNOWN` dành cho đoạn mà người gắn nhãn cũng không thể xác định.
4. Dùng clip khác nhau cho điều chỉnh ngưỡng và đánh giá cuối nếu có đủ dữ liệu.
   Nếu chỉ một người/clip, ghi rõ giới hạn này; không ngoại suy sang tài xế khác.

## Chạy dự đoán và đánh giá

Tạo log riêng tư trên toàn clip:

```bash
python -m vinfast_dms --source data/private/consented_demo.mp4 --headless \
  --log-csv outputs/private/predictions.csv
```

Tính metric và instant baseline dùng cùng frame/nhãn:

```bash
python scripts/evaluate.py --predictions outputs/private/predictions.csv \
  --labels outputs/private/labels.csv --output outputs/private/evaluation.json
```

Để benchmark nhiều clip, tạo `manifest.csv` trong thư mục riêng tư với header
`source,labels`; mỗi đường dẫn tương đối tính từ thư mục manifest:

```csv
source,labels
consented_a.mp4,labels_a.csv
consented_b.mp4,labels_b.csv
```

Sau đó chạy `python scripts/benchmark.py --manifest data/private/manifest.csv`.
Mỗi clip cần có nhãn độc lập khớp với thời gian nguồn video. Script lưu prediction
log và JSON trong `outputs/private/benchmark/`, ghi phần cứng/phần mềm, model
checksum, config hash và metric từng clip. Không đưa artifact có dữ liệu cá nhân
lên repo công khai.

## Định nghĩa metric

- **Confusion matrix:** frame trong đoạn nhãn được gán trạng thái thật theo thời
  gian video. Trạng thái thật `UNKNOWN` được đếm riêng; ma trận phân loại gồm ba
  lớp thật đã biết và bốn cột dự đoán kể cả dự đoán `UNKNOWN`.
- **Precision/recall/F1:** tính riêng `EYES_CLOSED` và `DISTRACTED`; không có mẫu
  số thì trả `N/A`, không quy thành 0 hay 100%.
- **Coverage:** tỷ lệ frame có ground truth đã biết mà mô hình cũng không trả
  `UNKNOWN`. Frame ground truth `UNKNOWN` được thống kê riêng và không làm đổi mẫu
  số coverage.
- **False alarms/minute NORMAL:** số lần trạng thái cảnh báo bắt đầu trong frame
  được gắn nhãn `NORMAL`, chia thời lượng NORMAL được quan sát (phút). Nếu không có
  thời lượng NORMAL thì `N/A`.
- **Event onset delay:** với từng segment nhắm mắt/quay đầu, lấy thời gian nguồn
  đến dự đoán cùng lớp đầu tiên trừ thời điểm bắt đầu segment. Segment không phát
  hiện được tính vào số sự kiện bỏ lỡ. Đây là delay trong clip, không dùng đồng hồ
  tốc độ chạy.
- **Latency p50/p95:** percentile tuyến tính nội suy của `processing_ms` trên
  toàn bộ frame log. Đây là thời gian xử lý từng vòng đo trong phần mềm, chưa tính
  độ trễ camera, màn hình hoặc cảnh báo.
- **FPS nguồn:** `(số mốc thời gian nguồn phân biệt − 1) / (mốc cuối − mốc đầu)`
  trên toàn log.
- **FPS runtime:** tính cùng công thức trên `wall_time_utc` của log; phụ thuộc máy
  và điều kiện chạy. Không lấy FPS fixture làm kết quả benchmark người thật.
- **Baseline:** instant threshold trên cùng EAR/yaw và guard chất lượng, không
  dùng EMA/dwell temporal. Mọi so sánh lấy cùng clip, frame và ground truth; chỉ
  gọi temporal tốt hơn nếu số liệu thực chứng minh điều đó.

## Tái lập và diễn giải

Lưu riêng clip, CSV nhãn, CSV dự đoán, JSON đánh giá, config, model SHA-256 và môi
trường. Đọc lại các timestamp ở mép segment vì khoảng nhãn kết thúc là exclusive.
Đừng tuning trên cùng clip rồi trình bày như tập test độc lập.

Ngưỡng `ear_closed=0.21`, `yaw=30°` là giá trị khởi tạo thử nghiệm. Một người và
một webcam không đại diện khác biệt về kính, ánh sáng, da, camera, vị trí lắp, rung
xe, khẩu trang hoặc cách ngồi. Báo cáo một lần đo chỉ mô tả clip cụ thể đã gắn
nhãn, không chứng minh độ an toàn hoặc hiệu quả với tài xế ngoài đời.
