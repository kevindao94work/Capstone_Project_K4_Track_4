# VinFast Driver Monitoring System (DMS)

Prototype OpenCV và MediaPipe hỗ trợ quan sát tình trạng nhắm mắt kéo dài và quay
đầu/mất tập trung qua webcam hoặc video. Đây không phải hệ thống ADAS đạt chuẩn an
toàn, không đưa ra kết luận y khoa và không dùng khi lái xe thực tế.

**Tác giả duy nhất:** Đào Gia Bảo — **MSSV:** 2A202602793.

Bài làm cá nhân theo chỉ đạo; chưa chứng minh tuân thủ điều kiện nhóm của ban tổ
chức. Việc được chấp nhận hay không tùy giảng viên/VLearn. Không tạo cộng tác viên
hoặc lịch sử đóng góp giả. Codex không nộp VLearn thay tác giả; cần tự đăng nhập và
nộp URL repository public đúng tài khoản.

## Cài đặt

Yêu cầu macOS Apple Silicon, Python 3.11 hoặc 3.12 và máy chạy CPU. Từ thư mục gốc:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Tải model một lần bằng `python scripts/download_model.py`. File model được lưu
cục bộ, không theo dõi bằng Git. Kiểm tra môi trường bằng
`python scripts/check_environment.py`.

## Chạy

Chạy webcam hoặc video:

```bash
python -m vinfast_dms --source camera
python -m vinfast_dms --source data/private/consented_demo.mp4 --headless
```

Trên MacBook Pro M4 này, mặc định `--camera-index 1` là webcam tích hợp; OpenCV
dùng backend AVFoundation. Có thể chọn camera khác bằng `--camera-index N`. Thêm
`--max-frames 100` để giới hạn lượt chạy. CP12 đã đọc 30 frame thật từ index 1,
chạy DMS trên 120 frame headless và 120 frame có cửa sổ, đồng thời hoàn tất lượt
kiểm tra tương tác từng tình huống. Camera mở bằng AVFoundation và đã xử lý frame
thật; kết quả theo tình huống, giới hạn và số đo được ghi tại
[kết quả thực nghiệm](docs/KET_QUA_THUC_NGHIEM.md). Script kiểm tra nhanh chỉ chạy
khi tác giả chủ động gọi `python scripts/check_camera.py`; quyền webcam do macOS
quản lý tại **System Settings → Privacy & Security → Camera**.

Đo hiệu năng webcam mà không lưu ảnh, đặc trưng hay video:

```bash
python scripts/benchmark_camera.py --camera-index 1 --duration-seconds 30
```

Thêm `--output outputs/private/camera_benchmark.json` nếu muốn lưu riêng báo cáo
thống kê tổng hợp. Camera smoke test: `python scripts/check_camera.py --frames 30`.
Video và ảnh không được ghi mặc định. Log CSV chỉ tạo khi bật `--log-csv`; bỏ
đường dẫn để lưu tên tự sinh trong `outputs/private/`, hoặc chỉ định đường dẫn.
Ghi video overlay chỉ khi chủ động bật `--record-output`; mặc định cũng nằm trong
`outputs/private/`. Chỉ bật ghi hình khi đã có đồng ý phù hợp. So sánh replay:
`python scripts/replay.py --source data/private/consented_demo.mp4`.

Để chạy từng tình huống tương tác (cửa sổ chờ Space trước mỗi pha; `s` bỏ qua
giảm sáng tùy chọn, `q` dừng), dùng `python scripts/benchmark_camera.py
--camera-index 1 --interactive-scenarios --output outputs/private/camera_interactive.json`.
Báo cáo chỉ giữ số liệu tổng hợp, không lưu ảnh, frame, đặc trưng hay video.

Ví dụ chạy headless kèm log riêng tư:

```bash
python -m vinfast_dms --source data/private/consented_demo.mp4 --headless \
  --log-csv outputs/private/run.csv
```

## Kiểm tra kỹ thuật

```bash
python scripts/check_environment.py
python -m compileall -q src scripts tests
pytest -q
ruff check .
```

## Đối chiếu đề bài

Đề bài upstream mô tả capstone Track 4, demo tối đa 10 phút, ít
nhất hai trụ cột, một số đo, một ca lỗi và dữ liệu an toàn. Upstream giới thiệu
bảy trụ cột và sáu tiêu chí chấm trên 100 điểm. Hướng dẫn triển khai này mở rộng
phạm vi thành CP0–CP12 và khuyến nghị sáu trụ cột. Điều kiện làm cá nhân được ghi
minh bạch như chưa chứng minh tuân thủ yêu cầu đội; quyết định thuộc ban tổ chức.

## Tài liệu

- [Báo cáo kỹ thuật](docs/BAO_CAO_KY_THUAT.md)
- [Phương pháp đánh giá](docs/PHUONG_PHAP_DANH_GIA.md)
- [Kết quả thực nghiệm](docs/KET_QUA_THUC_NGHIEM.md)
- [Phân tích ca lỗi](docs/PHAN_TICH_CA_LOI.md)
- [Quyền riêng tư và giới hạn](docs/QUYEN_RIENG_TU_VA_GIOI_HAN.md)
- [Kịch bản demo 10 phút](docs/KICH_BAN_DEMO_10_PHUT.md)
- [Câu hỏi phản biện](docs/CAU_HOI_PHAN_BIEN.md)
- [Biên bản checkpoint](docs/GHI_NHAN_CHECKPOINT.md)
- [Checklist nộp bài](docs/CHECKLIST_NOP_BAI.md)

Tài liệu API: [MediaPipe Face Landmarker Python](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/python).
Nguồn đề và rubric: [K4 Track 4 Project Capstone](https://github.com/VinUni-AI20k/K4-Track4-ProjectCapstone).
