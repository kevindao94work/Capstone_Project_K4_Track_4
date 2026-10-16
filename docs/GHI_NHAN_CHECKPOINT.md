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
- Commit/push: `0368cb5d184ee0fa4b2a95c75fdc688848a25987`; đã push `main`, sau
  `git fetch origin`, `HEAD` và `origin/main` cùng SHA.
- Minh chứng: `tests/test_sources.py`, `tests/test_landmarks.py`,
  `tests/test_cli_smoke.py`; model tải cục bộ, không commit.

### CP2 — EAR, head pose và kiểm thử hình học

- Thời điểm UTC: 2026-10-16 11:58 UTC.
- Trạng thái: PASS cho kiểm thử hình học tổng hợp; chưa đánh giá góc đầu trên
  người thật.
- Đã thay đổi: `src/vinfast_dms/geometry.py`, `tests/test_geometry.py`.
- Lệnh đã chạy: `ruff check --fix src tests` → 0 lỗi;
  `python -m compileall -q src scripts tests` → 0;
  `pytest -q tests/test_geometry.py` → 17 passed.
- Điều kiện chấp nhận: hai EAR tính từ pixel hóa landmark chuẩn hóa; kiểm tra
  missing, NaN/inf, mẫu số 0, EAR bất hợp lý và kích thước ảnh; PnP dùng sáu mốc
  nose/chin/eye corners/mouth corners, kiểm tra residual pixel; test tịnh tiến,
  scale, dấu yaw hai chiều, pitch/roll dựng sẵn và lỗi PnP. Mốc mắt đối chiếu với
  topology chính thức trong [MediaPipe face mesh connections](https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/python/solutions/face_mesh_connections.py)
  (các vùng mắt ở `FACEMESH_LEFT_EYE`, `FACEMESH_RIGHT_EYE`, mũi, cằm và môi).
- Phần chưa kiểm chứng: 3D reference points là hình mặt quy mô tùy ý; không phải
  hệ tọa độ mét, intrinsics vẫn là heuristic và test không chứng minh góc chính
  xác trên camera thật.
- Commit/push: `aeb83e3d008a3553086eb7a05794f06c699006e4`; đã push `main`, sau
  `git fetch origin`, `HEAD` và `origin/main` cùng SHA.
- Minh chứng: `tests/test_geometry.py` (17 fixture tổng hợp, chỉ là test thuật toán).

### CP3 — MVP temporal state machine và luồng headless

- Thời điểm UTC: 2026-10-16 12:04 UTC.
- Trạng thái: PASS cho unit/integration fixture; chưa có demo trên webcam hoặc
  video người thật.
- Đã thay đổi: `src/vinfast_dms/temporal.py`, `src/vinfast_dms/pipeline.py`,
  `src/vinfast_dms/overlay.py`, `src/vinfast_dms/cli.py`, `src/vinfast_dms/__main__.py`,
  cấu hình/lockfile có Pillow để vẽ tiếng Việt, các kiểm thử FSM/pipeline/overlay.
- Lệnh đã chạy: `ruff check .` → 0 lỗi;
  `python -m compileall -q src scripts tests` → 0;
  `pytest -q` → 49 passed; `python -m pip check` → sạch.
  CLI `python -m vinfast_dms --source <fixture-100-frames.avi> --headless --max-frames 100`
  chạy với model thật trên clip fixture đen 640×480 có 100 khung hình → exit 0,
  đã xử lý đủ 100, trạng thái cuối `KHÔNG XÁC ĐỊNH`.
- Điều kiện chấp nhận: chớp mắt tổng hợp 0,15 giây không cảnh báo; nhắm mắt kéo
  dài phát cảnh báo sau dwell theo thời gian ở 5/15/30/60 FPS và dãy timestamp
  không đều; mất mặt trả `UNKNOWN` và xóa trạng thái cũ; CLI `--help` chạy không
  mở camera; overlay có EAR/yaw/pitch/trạng thái/độ trễ.
- Phần chưa kiểm chứng: clip 100 khung chỉ là fixture trống để kiểm thử độ bền,
  không phải demo nhận diện hay benchmark hiệu năng; chưa mở cửa sổ tương tác hoặc
  webcam do quyền Camera chưa được cấp.
- Commit/push: `0dc6a7ed234a3ed8a0ec6b2992fe7bf67eb9441b`; đã push `main`, sau
  `git fetch origin`, `HEAD` và `origin/main` cùng SHA.
- Minh chứng: `tests/test_temporal.py`, `tests/test_pipeline.py`,
  `tests/test_overlay.py`, `tests/test_cli_smoke.py`.

### CP4 — Bất định, PnP và lọc nhiễu nâng cao

- Thời điểm UTC: 2026-10-16 12:06 UTC.
- Trạng thái: PASS cho cổng chất lượng, PnP và kiểm thử tổng hợp; chưa đánh giá
  chất lượng trên người thật.
- Đã thay đổi: `src/vinfast_dms/uncertainty.py`, pipeline/overlay và
  `tests/test_uncertainty.py`, `tests/test_pipeline.py`.
- Lệnh đã chạy: `python -m compileall -q src scripts tests` → 0;
  `ruff check .` → 0 lỗi; `pytest -q` → 64 passed;
  `python -m pip check` → sạch; CLI/model chạy lại fixture 100 khung → exit 0.
- Điều kiện chấp nhận: reason code tách riêng cho không có mặt, nhiều mặt, lỗi
  inference, frame sai, landmark sai hình dạng/NaN/ngoài khung, mặt nhỏ, thiếu
  mắt, EAR bất hợp lý, solvePnP thất bại, residual cao, timestamp lỗi và gap;
  14 kiểm thử bất định/hình học và pipeline bao gồm ít nhất tám tình huống lỗi.
  Mất mặt hoặc gap trả `UNKNOWN`, reset dwell/EMA và không giữ cảnh báo cũ.
- Phần chưa kiểm chứng: ngưỡng diện tích mặt và residual là heuristic; chưa đo
  blur/brightness và không tạo confidence giả; pose chưa hiệu chuẩn theo camera.
  Video 100 khung là clip trống tổng hợp, không đại diện người thật.
- Commit/push: `20512cec29cae33faf88cc1743758bde25d74c7b`; đã push `main`, sau
  `git fetch origin`, `HEAD` và `origin/main` cùng SHA.
- Minh chứng: `tests/test_uncertainty.py`, `tests/test_pipeline.py`,
  `tests/test_temporal.py`, `tests/test_geometry.py`.

### CP5 — Giao diện OpenCV và live demo

- Thời điểm UTC: 2026-10-16 12:08 UTC.
- Trạng thái: PASS cho UI/fallback video và kiểm thử phím bằng nguồn giả;
  BLOCKED-QUYỀN cho webcam thật vì chưa nhận được quyền Camera macOS.
- Đã thay đổi: `scripts/check_camera.py` (kiểm tra theo số frame hoặc thời lượng),
  `src/vinfast_dms/cli.py` (đóng cửa sổ an toàn khi display lỗi),
  `tests/test_cli_live.py`, `tests/test_cli_smoke.py`.
- Lệnh đã chạy: `python -m compileall -q src scripts tests` → 0;
  `ruff check .` → 0 lỗi; `pytest -q` → 67 passed;
  `python -m pip check` → sạch; `python -m vinfast_dms --help` và
  `python scripts/check_camera.py --help` → exit 0. Video fixture đen 640×480,
  100 khung, chạy headless với model → exit 0, trạng thái cuối `KHÔNG XÁC ĐỊNH`.
- Điều kiện chấp nhận: phím `q` thoát và lỗi mở cửa sổ chuyển sang headless được
  kiểm tra bằng nguồn giả; `r` đặt lại session, `h` hiện trợ giúp; CLI có các
  ngưỡng, lựa chọn mirror, độ trễ/FPS và trạng thái tiếng Việt. Không ghi media.
- Phần chưa kiểm chứng: chưa chạy cửa sổ tương tác hoặc webcam; chưa đo FPS thật.
  `python scripts/check_camera.py --duration-seconds 60` sẽ kiểm tra 1 phút sau
  khi có quyền Camera; script chỉ đọc frame trong bộ nhớ và không ghi hình.
- Commit/push: `dc4d9b4c0428f148cfe22743d1125287ddc4e43b`; đã push `main`, sau `git fetch origin`, `HEAD` và `origin/main` cùng SHA.
- Minh chứng: `tests/test_cli_live.py`, `tests/test_cli_smoke.py`,
  `tests/test_overlay.py`; video fixture được tạo và xóa trong thư mục tạm.

### CP6 — Logger, recorder theo lựa chọn và replay

- Thời điểm UTC: 2026-10-16 12:10 UTC.
- Trạng thái: PASS cho CSV, replay và codec với fixture tổng hợp; không ghi hoặc
  công bố media người thật.
- Đã thay đổi: `src/vinfast_dms/logging_utils.py`, `src/vinfast_dms/cli.py`,
  `scripts/replay.py`, `tests/test_logging.py`, trợ giúp CLI.
- Lệnh đã chạy: `python -m compileall -q src scripts tests` → 0;
  `ruff check .` → 0 lỗi; `pytest -q` → 76 passed;
  `python -m pip check` → sạch. CLI chạy clip đen 10 khung với
  `--log-csv` và `--record-output` trong thư mục tạm → exit 0, CSV có 10 dòng,
  AVI có 10 khung và dữ liệu; `python scripts/replay.py` chạy 2 lượt, 10 khung,
  chữ ký dự đoán giống nhau ngoài ID/thời gian máy.
- Điều kiện chấp nhận: CSV schema version 1 có đầy đủ nguồn, thời gian nguồn,
  thời gian UTC, độ trễ, EAR, yaw/pitch, chất lượng, trạng thái, cảnh báo, hash
  cấu hình, phiên bản/hash model; giá trị thiếu là ô rỗng. Chỉ ghi khi bật flag;
  tên tự sinh nằm trong `outputs/private/`. Recorder dùng overlay và báo lỗi
  codec; fixture AVI roundtrip thành công, output hỏng/empty bị xóa.
- Phần chưa kiểm chứng: chưa replay clip cá nhân có consent; chưa ghi video người
  thật. Những tệp fixture đều ở thư mục tạm và đã bị xóa khi kết thúc.
- Commit/push: SHA sẽ được ghi và đối chiếu ở CP7.
- Minh chứng: `tests/test_logging.py`, `tests/test_cli_smoke.py`,
  `scripts/replay.py`; cột runtime bị bỏ qua khi so sánh gồm `run_id`,
  `wall_time_utc`, `processing_ms`.
