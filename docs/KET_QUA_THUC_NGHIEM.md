# Kết quả thực nghiệm

**Tác giả:** Đào Gia Bảo — **MSSV:** 2A202602793.

## Dữ liệu thực đã đo

Đã chạy smoke test webcam, DMS live, benchmark 60 giây và một lượt kiểm tra tương
tác từng pha trên camera index 1 / AVFoundation. Webcam và pipeline xử lý frame
thật đã được xác minh. Lượt tương tác không lưu ảnh/video, nhưng cue và trạng thái
đầu ra chưa được gắn nhãn độc lập; các thống kê dưới đây là spot-check một người,
không phải phép đo accuracy hay kết luận an toàn.

| Đo lường trên dữ liệu người thật | Kết quả hiện tại | Lý do |
|---|---|---|
| Camera capture index 1 | PASS CP12 | AVFoundation, 640×480; 30 frame smoke; benchmark 60 giây đọc 1.797 frame, không có lỗi capture. Có một lần mở thiết bị thất bại thoáng qua trước các lượt chạy thành công. |
| DMS pipeline webcam | Chạy trên frame thật; nhận diện được quan sát, chưa đánh giá accuracy | Trong benchmark, face detector thấy mặt 1.458/1.797 frame; 1.452 frame qua quality gate landmark và 1.439 frame hợp lệ toàn pipeline. Hai lượt chạy 120 frame kết thúc sạch; trạng thái đầu ra thay đổi theo phiên. |
| Tốc độ nguồn camera | 29,94 FPS | Từ timestamp nguồn của 1.797 frame trong phiên benchmark. |
| Throughput webcam headless | 29,94 FPS | 1.797 frame / 60,011 giây; gồm chờ camera và xử lý, không gồm render cửa sổ. Đây là trung bình phiên, không phải median FPS. |
| Tốc độ xử lý riêng pipeline | 121,66 FPS năng lực tính toán | Số frame chia tổng `DMSPipeline.process` time; không phải tốc độ camera-to-display. |
| Processing latency | mean 8,22 ms; p50 8,64 ms; p95 10,90 ms | Đo quanh `DMSPipeline.process`; không tính chờ camera, hiển thị hoặc event-to-warning. |
| Tỷ lệ pipeline hợp lệ | 1.439/1.797 (80,08%) | 1.458 frame phát hiện mặt; 1.452 qua gate hình dạng/kích thước landmark; 1.439 qua quality gate tổng hợp. Đây là tỷ lệ theo frame, không phải precision. |
| Lượt tương tác theo tình huống | 8 pha hoàn tất; giảm sáng bỏ qua | 1.505 frame thuộc các pha đo; 3.009 lần đọc camera, 0 lỗi. Kết quả pha ở dưới; đây là spot-check theo cue, không có ground truth độc lập. |
| Số clip và số người có consent | N/A | Chưa lưu clip người thật; benchmark trực tiếp không lưu media. |
| Số frame/nhãn độc lập | N/A | Chưa có ground truth. |
| Confusion matrix, precision/recall/F1 | N/A | Không có cặp dự đoán–nhãn. |
| Coverage, UNKNOWN, false alarms/phút NORMAL | N/A | Chưa chạy benchmark có nhãn. |
| Source event onset delay | N/A | Chưa có sự kiện được gắn nhãn. |
| Camera-to-display latency | N/A | Benchmark headless, không đo thời điểm render. |
| Event-to-warning latency | N/A | Chưa có sự kiện được gắn nhãn độc lập. |
| So sánh baseline từng frame và temporal FSM | N/A | Chưa có dữ liệu chung để so sánh. |
| Ca lỗi quan sát và tái hiện | NOT DEMONSTRATED | Có tín hiệu ứng viên cần tái kiểm tra ở pha nhìn thẳng/quay trái; chưa đủ căn cứ gán nhãn lỗi hoặc root cause. Xem [phân tích ca lỗi](PHAN_TICH_CA_LOI.md). |

### Kết quả spot-check tương tác

Người tham gia xác nhận đã thực hiện mỗi hành vi sau cue “DO NOW” và chờ hết pha;
cửa sổ hiển thị hành động cần làm và thời lượng. Mỗi trạng thái dưới đây là nhãn do
mô hình dự đoán, không phải nhãn độc lập. Pha giảm sáng được người tham gia bỏ qua.
Các cửa sổ 5–7 giây không đủ để tính precision/recall/F1 hoặc false alarm rate ổn
định.

| Pha được yêu cầu | Frame | Pipeline hợp lệ | Trạng thái quan sát | Ghi chú |
|---|---:|---:|---|---|
| Nhìn thẳng, mắt mở | 181 | 171 | `DISTRACTED` 137, `NORMAL` 34, `UNKNOWN` 10 | Tín hiệu false-alarm ứng viên; pha tái kiểm tra cùng cue cho `NORMAL` 181/181 frame hợp lệ, 0 cảnh báo; bất thường đầu tiên không tái hiện. |
| Chớp mắt tự nhiên | 181 | 181 | `NORMAL` 181 | Không có frame cảnh báo trong pha. |
| Nhắm mắt 2 giây rồi mở | 210 | 210 | `EYES_CLOSED` 59, `NORMAL` 151 | 59 frame cảnh báo mắt nhắm; phù hợp một phần với thao tác được yêu cầu, chưa đo onset delay. |
| Quay trái, giữ rồi quay lại | 211 | 80 | `DISTRACTED` 13, `NORMAL` 67, `UNKNOWN` 131 | Có 126 frame `high_reprojection_error`; tín hiệu ứng viên về quality gate ở góc quay, chưa xác định root cause. |
| Quay phải, giữ rồi quay lại | 211 | 178 | `DISTRACTED` 20, `NORMAL` 158, `UNKNOWN` 33 | Có 31 frame `no_face`; không đủ nhãn độc lập để gọi là bỏ lỡ. |
| Ra khỏi khung rồi quay lại | 179 | 10 | `UNKNOWN` 169, `DISTRACTED` 9, `NORMAL` 1 | `UNKNOWN` chiếm đa số khi quan sát mặt không đủ; cảnh báo xuất hiện ở một số frame hợp lệ. |
| Che mắt rồi bỏ che | 181 | 161 | `EYES_CLOSED` 35, `NORMAL` 126, `UNKNOWN` 20 | Đầu ra phản ánh mắt nhắm trong một phần pha; hành vi che mắt không đồng nghĩa ground truth `UNKNOWN`. |
| Giảm sáng tùy chọn | 0 | 0 | Không đo | Người tham gia bỏ qua pha. |
| Phục hồi nhìn thẳng | 151 | 151 | `NORMAL` 151 | Không có cảnh báo trong pha. |

Pha tái kiểm tra “nhìn thẳng, mắt mở” hoàn tất 181 frame/6,03 giây, tất cả qua
quality gate và đều `NORMAL`, không cảnh báo; 0/604 lần đọc webcam thất bại trong
phiên đó. Không thể kết luận nguyên nhân lần đầu có 137 frame `DISTRACTED` vì
không lưu frame hoặc đặc trưng theo thời gian. File aggregate cục bộ
`outputs/private/camera_interactive_cp12.json` và
`outputs/private/camera_normal_repro_cp12.json` không được commit; không chứa
frame, ảnh, đặc trưng hay timestamp từng frame.

## Kiểm thử kỹ thuật đã chạy

CP12 kiểm định trong môi trường `.venv` Python 3.11.15: `.venv/bin/python -m
pytest -q` → **105 passed**; `.venv/bin/ruff check .`, `compileall`, `pip check`,
`scripts/check_environment.py` và `scripts/validate_submission.py
--allow-dirty --skip-sync` đều exit 0. Video AVI đen tổng hợp 30 frame được chạy
qua `scripts/replay.py --runs 2 --max-frames 30` → hai chữ ký replay trùng nhau.
Fixture nằm trong thư mục tạm và được xóa sau lượt chạy; đây là kiểm thử hồi quy,
không phải dữ liệu nhận diện người.

Tại CP8, `.venv/bin/python -m pytest -q` cho 90 passed. CP10 dựng venv Python 3.11
mới, cài `pip install -e '.[dev]'`, rồi chạy `.venv/bin/python -m pytest -q` tương
đương trong venv sạch: **92 passed**. RUFF, `compileall`, `pip check` và
`scripts/check_environment.py` cũng thành công trong môi trường sạch. Test gồm
hình học dựng sẵn, timestamp, FSM theo thời gian, lỗi quality, CSV/replay, manifest
và exact confusion matrix trên fixture. Đây là kiểm chứng hợp đồng code; không phải
độ chính xác nhận diện, FPS webcam hay số liệu an toàn.

Model MediaPipe Tasks chạy trên clip đen tổng hợp 100 frame trước đó và 30 frame
trong smoke CP10; đều trả `UNKNOWN` vì không có mặt. Thử codec/replay cũng dùng
clip tổng hợp trong thư mục tạm. Smoke CP10 xử lý 30 frame, tạo 30 dòng CSV, rồi
replay 2 lượt có chữ ký giống nhau. Các bước này xác nhận luồng không crash và
file có thể đọc lại, không đánh giá khả năng nhận diện người.

Benchmark 60 giây CP12 dùng camera index 1, AVFoundation, 640×480, model SHA-256
`64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff`, Python 3.11.15,
OpenCV 4.14.0 và MediaPipe 0.10.35. Báo cáo aggregate ở
`outputs/private/camera_benchmark_cp12_retry.json` (không commit). Lượt tương tác
aggregate ở `outputs/private/camera_interactive_cp12.json` (không commit). Một lần
chạy benchmark ban đầu không có mặt được nhận diện; lượt retry có mặt trong 81,14%
frame. Chỉ số trên mô tả các phiên trên thiết bị/cấu hình này; phải đo lại ở điều
kiện demo đại diện.

## Mốc chấp nhận kỹ thuật và giả định

- Throughput webcam headless 29,94 FPS và pipeline capacity 121,66 FPS là trung
  bình/aggregate của một phiên. Chưa đo median FPS theo cửa sổ hoặc độ trễ hiển thị;
  vì vậy chưa kết luận đạt mục tiêu guide **12 FPS trung vị ở 640×480**.
- EAR/yaw thresholds trong `config/default.yaml` là cấu hình demo ban đầu, chưa
  fit hoặc xác nhận bởi tập dữ liệu.
- Ví dụ impact 1.000 xe × 1 phút giả định × 10% giả định = 100 phút/ngày là phép
  tính kịch bản giả định, không phải dữ liệu thực hay tuyên bố của VinFast.

## Kết luận có thể rút ra

Hiện webcam capture, phát hiện landmark, quality gate và các nhánh trạng thái đã
được thực thi trên người tham gia trong spot-check. Quan sát này cho thấy hành vi
phụ thuộc pha và còn các trường hợp `UNKNOWN`/`DISTRACTED` cần xem lại; không thay
thế video được consent và gắn nhãn độc lập. Chưa có bằng chứng để kết luận accuracy,
false alarm rate, event delay, mục tiêu FPS trung vị, giảm cảnh báo sai hoặc tác
động cho VinFast. Cách mở rộng đánh giá được mô tả tại [phương pháp đánh giá](PHUONG_PHAP_DANH_GIA.md).
