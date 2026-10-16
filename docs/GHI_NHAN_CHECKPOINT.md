# Ghi nhận checkpoint

Các trạng thái dưới đây chỉ phản ánh lệnh và dữ liệu đã thực sự kiểm tra. Webcam,
video người thật, metric thực nghiệm và tình trạng nộp VLearn không được suy diễn
từ unit test.

### CP0 — Khảo sát repo, môi trường, bảo mật và Git

- Thời điểm UTC: 2026-10-16 11:53 UTC.
- Trạng thái: PASS cho khảo sát, môi trường và nền tảng repo.
- Đã thay đổi: `README.md`, `pyproject.toml`, `requirements.txt`, `.gitignore`,
  `.python-version`, `config/default.yaml`, `src/vinfast_dms/config.py`,
  `scripts/check_environment.py`, `tests/test_config.py`, README dữ liệu/model/
  outputs và thư mục `docs/`.
- Lệnh đã chạy: `python -m compileall -q src scripts tests` → 0;
  `python -m pytest -q` → 3 passed;
  `ruff check .` → 0 lỗi;
  `python -m pip check` → không có dependency lỗi;
  `python scripts/check_environment.py` → Python 3.11.15 arm64, NumPy 2.2.6,
  OpenCV 4.14.0, MediaPipe 0.10.35, FaceLandmarker Tasks và `solvePnP` có sẵn;
  `git diff --check` → 0.
- Điều kiện chấp nhận: remote `origin` trùng URL clone
  `https://github.com/kevindao94work/Capstone_Project_K4_Track_4.git`; nhánh local
  `main`; remote ban đầu chưa có nhánh; venv `.venv` bị bỏ qua bởi Git; cấu hình
  đọc và kiểm tra được; thông tin tác giả và điều kiện bài cá nhân được ghi rõ.
- Đối chiếu đề bài upstream: trang chính thức mô tả 2 giờ build, demo 10 phút,
  ít nhất hai trụ cột, một số đo, một ca lỗi, dữ liệu an toàn; có bảy trụ cột và
  sáu tiêu chí chấm trên 100 điểm. Hướng dẫn người dùng mở rộng thành CP0–CP10,
  đề xuất sáu trụ cột và yêu cầu làm cá nhân. Upstream nhấn mạnh làm theo đội và
  hỏi đáp các thành viên; bài cá nhân chưa chứng minh đáp ứng yêu cầu đội.
- Phần chưa kiểm chứng: chưa xin quyền mở webcam; chưa có clip có consent, nhãn,
  đo thực nghiệm hay ca lỗi quan sát thật. Đây không ngăn CP0.
- Commit/push: `261ee9a5056178e7ac943528292376c52abf5c3b`; đã push `main`, sau
  `git fetch origin`, `HEAD` và `origin/main` cùng SHA.
- Minh chứng: `.venv` cục bộ (không theo dõi), `pyproject.toml`,
  `requirements.txt`, `config/default.yaml`.

### CP1 — Video sources và MediaPipe landmark adapter

- Thời điểm UTC: 2026-10-16 11:56 UTC.
- Trạng thái: PASS cho nguồn video, bộ chuyển MediaPipe Tasks và kiểm thử tích hợp
  trên khung hình tổng hợp; BLOCKED-QUYỀN cho webcam (chưa mở camera).
- Đã thay đổi: `src/vinfast_dms/sources.py`, `src/vinfast_dms/landmarks.py`,
  `scripts/download_model.py`, `scripts/check_camera.py`, cùng các kiểm thử nguồn,
  landmark và trợ giúp CLI.
- Lệnh đã chạy: `python -m compileall -q src scripts tests` → 0;
  `pytest -q` → 11 passed;
  `ruff check src scripts tests` → 0 lỗi. Tích hợp model chạy trên mảng đen tổng
  hợp 640×480 với `detect_for_video` → 0 mặt, `reason=no_face`, exit 0.
- Điều kiện chấp nhận: model khởi tạo được; mốc thời gian video tăng đơn điệu;
  clip codec MJPG tạo trong thư mục tạm đọc hết và giải phóng nguồn; video không
  tồn tại báo lỗi dễ hiểu; ảnh BGR đổi đúng kiểu cho MediaPipe; không yêu cầu nhận
  diện khuôn mặt trong fixture tổng hợp.
- Model: nguồn gói Google Storage chính thức từ trang MediaPipe; SHA-256 cục bộ
  `64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff`. File nằm
  trong `models/` và bị Git bỏ qua.
- Phần chưa kiểm chứng: chưa đọc 30 khung webcam do chưa cấp quyền; không có clip
  người thật. Tích hợp model trên ảnh tổng hợp không phải kết quả nhận diện người.
- Commit/push: SHA sẽ được đối chiếu ngay sau commit CP1 và ghi ở checkpoint kế.
- Minh chứng: `tests/test_sources.py`, `tests/test_landmarks.py`,
  `tests/test_cli_smoke.py`; model tải cục bộ, không commit.
