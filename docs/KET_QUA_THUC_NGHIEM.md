# Kết quả thực nghiệm

**Tác giả:** Đào Gia Bảo — **MSSV:** 2A202602793.

## Dữ liệu thực đã đo

**CHƯA CÓ SỐ LIỆU.** Chưa có clip người thật do tác giả tự quay với consent, nhãn
độc lập, webcam được phép mở hoặc log benchmark trên người. Do đó chưa có precision,
recall, F1, coverage, false alarms/phút, event delay, FPS hoặc latency thực để đưa
vào bảng. Không lấy fixture tổng hợp làm metric thực nghiệm.

| Đo lường trên dữ liệu người thật | Kết quả hiện tại | Lý do |
|---|---|---|
| Số clip và số người có consent | N/A | Chưa ghi nhận clip. |
| Số frame/nhãn độc lập | N/A | Chưa có ground truth. |
| Webcam trên MacBook Pro M4 | BLOCKED-QUYỀN | Sau khi tác giả bật Camera permission và thử lại, OpenCV vẫn báo `not authorized to capture video`; tiến trình thoát mã 2 sau 4,3 giây, 0 frame được xử lý. |
| Confusion matrix, precision/recall/F1 | N/A | Không có cặp dự đoán–nhãn. |
| Coverage, UNKNOWN, false alarms/phút NORMAL | N/A | Chưa chạy benchmark có nhãn. |
| Source event onset delay | N/A | Chưa có sự kiện được gắn nhãn. |
| Processing latency p50/p95 và runtime FPS | N/A | Chưa chạy video người thật/webcam; không suy ra từ test tự động. |
| So sánh baseline từng frame và temporal FSM | N/A | Chưa có dữ liệu chung để so sánh. |
| Ca lỗi quan sát và tái hiện | NOT DEMONSTRATED | Xem [phân tích ca lỗi](PHAN_TICH_CA_LOI.md). |

## Kiểm thử kỹ thuật đã chạy

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

## Mốc chấp nhận kỹ thuật và giả định

- Mục tiêu guide **12 FPS trung vị ở 640×480 trên Mac M4** chưa đo; trạng thái
  `CHƯA KIỂM CHỨNG`, không phải kết quả.
- EAR/yaw thresholds trong `config/default.yaml` là cấu hình demo ban đầu, chưa
  fit hoặc xác nhận bởi tập dữ liệu.
- Ví dụ impact 1.000 xe × 1 phút giả định × 10% giả định = 100 phút/ngày là phép
  tính kịch bản giả định, không phải dữ liệu thực hay tuyên bố của VinFast.

## Kết luận có thể rút ra

Hiện có bằng chứng unit/integration fixture cho các nhánh kỹ thuật và công cụ
đánh giá. Chưa có bằng chứng để kết luận prototype nhận diện tốt trên người, đạt
mục tiêu hiệu năng, giảm cảnh báo sai, hoặc tạo tác động cho VinFast. Sau khi có
clip consent, cách tái lập được mô tả tại [phương pháp đánh giá](PHUONG_PHAP_DANH_GIA.md);
chỉ đưa bảng số liệu vào đây khi artifact nguồn đã tồn tại và có thể kiểm tra.
