# Phương pháp đánh giá

**Tác giả:** Đào Gia Bảo — **MSSV:** 2A202602793.

## Tình trạng đánh giá

Chưa có video được lưu với consent hoặc ground truth thủ công. Đã có benchmark
webcam trực tiếp và spot-check tương tác có ranh giới transition/hold/recovery;
có thể báo cáo capture, latency, trạng thái, chất lượng, residual và coverage
quan sát theo cue. Chưa có accuracy/F1, false-alarm rate hoặc event latency trên
nhãn độc lập.

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

Đo hiệu năng xử lý trực tiếp mà không lưu frame hoặc đặc trưng. Index 1 đã được
dùng ở các phiên CP13; lần kiểm tra CLI cuối cùng macOS ánh xạ camera tích hợp sang
index 0. Chạy `scripts/check_camera.py --camera-index N --frames 30` để chọn index
đang hoạt động:

```bash
python scripts/benchmark_camera.py --camera-index 1 --duration-seconds 60 \
  --output outputs/private/camera_benchmark.json
```

JSON chỉ chứa số frame, tốc độ, latency, tỷ lệ landmark hợp lệ, trạng thái tổng hợp,
thông số môi trường và hash model/config. Mặc định không ghi JSON; kết quả chỉ in
ra terminal. Lệnh này không gắn nhãn hành vi và không sinh precision/recall/F1.

Để thực hiện từng cue khi người tham gia sẵn sàng, chạy:

```bash
python scripts/benchmark_camera.py --camera-index 1 --interactive-scenarios \
  --output outputs/private/camera_interactive.json
```

Cửa sổ chờ Space trước mỗi tình huống; người tham gia làm theo dải cue riêng dưới
HUD. Mỗi tình huống tách transition, hold, recovery theo offset từ Space; JSON lưu
frame đầu/cuối, timestamp nguồn đầu/cuối và khoảng offset quan sát của mỗi
subphase. `s` bỏ qua pha giảm sáng tùy chọn, `q` dừng. Đây là spot-check theo cue,
không có nhãn độc lập; không dùng tính accuracy/F1. Chỉ lưu aggregate trong
`outputs/private/`, không lưu frame, ảnh, đặc trưng, timestamp từng frame hay video.

## Định nghĩa metric

- **Confusion matrix:** frame trong đoạn nhãn được gán trạng thái thật theo thời
  gian video. Trạng thái thật `UNKNOWN` được đếm riêng; ma trận phân loại gồm ba
  lớp thật đã biết và bốn cột dự đoán kể cả dự đoán `UNKNOWN`.
- **Precision/recall/F1:** tính từng lớp ground truth đã biết (`NORMAL`,
  `EYES_CLOSED`, `DISTRACTED`); `UNKNOWN` là trạng thái abstention, không được gộp
  như lớp cảnh báo. Không có mẫu số thì trả `N/A`, không quy thành 0 hay 100%.
- **Accuracy all-known:** đúng / toàn bộ frame ground truth đã biết; dự đoán
  `UNKNOWN` tính là không đúng.
- **Accuracy when covered:** đúng / frame ground truth đã biết mà prediction không
  `UNKNOWN`; luôn đọc cùng coverage và abstention rate.
- **Coverage/abstention:** coverage là tỷ lệ frame ground truth đã biết có dự đoán
  khác `UNKNOWN`; abstention rate trên known labels là phần bù coverage. Báo thêm
  tỷ lệ `UNKNOWN` trên mọi frame được gắn nhãn và số frame ground truth `UNKNOWN`.
- **False alarms/minute NORMAL:** số lần trạng thái cảnh báo bắt đầu bên trong mỗi
  đoạn `NORMAL` được gắn nhãn, chia tổng thời lượng NORMAL được quan sát (phút).
  Trạng thái trước một đoạn không nối onset vào đoạn kế tiếp. Nếu không có thời
  lượng NORMAL thì `N/A`.
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
- **Tốc độ nguồn camera:** `(số frame − 1) / (timestamp nguồn cuối − timestamp
  nguồn đầu)` trong phiên webcam.
- **Năng lực xử lý riêng pipeline:** số frame xử lý chia tổng
  `DMSPipeline.process` time; loại thời gian chờ camera và render.
- **Throughput headless:** số frame chia thời gian chạy wall-clock; gồm chờ
  capture và xử lý, không gồm render. Đây là throughput trung bình của phiên,
  không phải median FPS theo cửa sổ. Các số này không phải độ trễ
  camera-to-display.
- **Tỷ lệ landmark hợp lệ:** số frame có landmark đạt kiểm tra hình dạng/kích cỡ
  chia frame đã xử lý. Tỷ lệ pipeline hợp lệ chặt hơn, vì còn yêu cầu EAR và PnP
  qua quality gate.
- **Capture failure rate:** số lần `read()` thất bại chia số lần gọi `read()` trong
  phiên; không đo mất frame nội bộ của driver nếu OpenCV không báo lỗi.
- **Camera-to-display:** không đo trong benchmark headless. Event-to-warning chỉ đo
  trên segment có mốc bắt đầu được gắn nhãn độc lập.
- **Baseline:** instant threshold trên cùng EAR/yaw và guard chất lượng, không
  dùng EMA/dwell temporal. Mọi so sánh lấy cùng clip, frame và ground truth; chỉ
  gọi temporal tốt hơn nếu số liệu thực chứng minh điều đó.

## Tái lập và diễn giải

Lưu riêng clip, CSV nhãn, CSV dự đoán, JSON đánh giá, config, model SHA-256 và môi
trường. Đọc lại các timestamp ở mép segment vì khoảng nhãn kết thúc là exclusive.
Đừng tuning trên cùng clip rồi trình bày như tập test độc lập. Báo cáo CP13 live
không có independent labels; mọi accuracy, precision/recall/F1, false alarms/phút
và event-to-warning latency phải để `N/A` cho đến khi có nhãn độc lập.

Ngưỡng `ear_closed=0.21`, `yaw=30°` là giá trị khởi tạo thử nghiệm. Một người và
một webcam không đại diện khác biệt về kính, ánh sáng, da, camera, vị trí lắp, rung
xe, khẩu trang hoặc cách ngồi. Báo cáo một lần đo chỉ mô tả clip cụ thể đã gắn
nhãn, không chứng minh độ an toàn hoặc hiệu quả với tài xế ngoài đời.
