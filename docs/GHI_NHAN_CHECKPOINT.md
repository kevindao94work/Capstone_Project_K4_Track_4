# Ghi nhận checkpoint

**Tác giả duy nhất:** Đào Gia Bảo — **MSSV:** 2A202602793.

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
- Commit/push: `cc46eb65a32862c3bfcab8ff103ab631724763c9`; đã push `main`, sau
  `git fetch origin`, `HEAD` và `origin/main` cùng SHA.
- Minh chứng: `tests/test_logging.py`, `tests/test_cli_smoke.py`,
  `scripts/replay.py`; cột runtime bị bỏ qua khi so sánh gồm `run_id`,
  `wall_time_utc`, `processing_ms`.

### CP7 — Nhãn độc lập và thực nghiệm định lượng

- Thời điểm UTC: 2026-10-16 12:16 UTC.
- Trạng thái: công cụ và metric fixture PASS; thực nghiệm video thật PENDING REAL
  DATA, chưa tự nhận CP7 thực nghiệm PASS.
- Đã thay đổi: `src/vinfast_dms/metrics.py`, `scripts/annotate_events.py`,
  `scripts/evaluate.py`, `scripts/benchmark.py`, `tests/test_metrics.py`,
  `tests/test_benchmark.py`. Manifest benchmark gồm cột `source,labels`; đường
  dẫn tương đối tính theo thư mục manifest. Báo cáo, prediction log mặc định
  trong `outputs/private/`.
- Lệnh đã chạy: `.venv/bin/ruff check .` → exit 0;
  `.venv/bin/python -m compileall -q src scripts tests` → exit 0;
  `.venv/bin/python -m pytest -q` → 89 passed;
  `.venv/bin/python -m pip check` → không có dependency lỗi;
  `scripts/check_environment.py` → Python 3.11.15 arm64, NumPy 2.2.6,
  OpenCV 4.14.0, MediaPipe 0.10.35, Tasks và solvePnP có sẵn; ba lệnh `--help`
  của annotate/evaluate/benchmark → exit 0.
- Điều kiện chấp nhận: fixture confusion matrix khớp chính xác; mẫu số 0 cho ra
  `N/A`; khoảng nhãn chồng lấp/thời gian không hợp lệ bị từ chối; không nhãn hoặc
  không có frame khớp cho ra `NOT EVALUATED`/exit 2. Có confusion matrix, precision,
  recall, F1, coverage, UNKNOWN riêng, false alarms/phút NORMAL, onset delay theo
  thời gian video, latency p50/p95, FPS nguồn/runtime, baseline threshold từng
  frame và temporal FSM. Benchmark ghi môi trường, hardware, config/model hash và
  giữ log riêng tư.
- Phần chưa kiểm chứng: chưa có clip thật được đồng ý, nhãn độc lập, metric thật,
  FPS trên người thật hoặc so sánh baseline thực nghiệm. Unit fixture chỉ kiểm
  tra code, không được xem là thực nghiệm hay công bố kết quả.
- Commit/push: `191cb68fa9046769dca7cad383657e97b08937b3`; đã push `main`, sau
  `git fetch origin`, `HEAD` và `origin/main` cùng SHA. CP7 vẫn PENDING REAL DATA,
  không nhận PASS thực nghiệm.
- Minh chứng: `tests/test_metrics.py`, `tests/test_benchmark.py`; không tạo hoặc
  xuất bản dữ liệu benchmark giả.

### CP8 — Một ca lỗi và nguyên nhân

- Thời điểm UTC: 2026-10-16 12:17 UTC.
- Trạng thái: NOT DEMONSTRATED; chưa có clip consent và nhãn độc lập để chứng minh
  ca lỗi thực.
- Đã thay đổi: `scripts/reproduce_failure.py` chạy lại clip từ đầu, lưu CSV riêng
  tư và trích cửa sổ thời gian có EAR/yaw/chất lượng/trạng thái; tùy chọn đối chiếu
  CSV nhãn độc lập. `docs/PHAN_TICH_CA_LOI.md` ghi rõ bằng chứng hiện có và quy
  trình tái hiện sau này.
- Lệnh đã chạy: `.venv/bin/ruff check .` → exit 0;
  `.venv/bin/python -m compileall -q src scripts tests` → exit 0;
  `.venv/bin/python -m pytest -q` → 90 passed;
  `python scripts/reproduce_failure.py --help` → exit 0;
  `git diff --check` → exit 0.
- Điều kiện chấp nhận: công cụ không kết luận root cause chỉ từ log; nếu không có
  nhãn độc lập, thông báo rõ rằng cửa sổ dự đoán không chứng minh failure. Kịch
  bản occlusion/mất mặt được giữ là stress test; `UNKNOWN` đúng không bị gọi nhầm
  là lỗi dự đoán.
- Phần chưa kiểm chứng: không có clip ID, thời điểm sự kiện thật, nhãn mong đợi,
  dự đoán lỗi, số đo liên quan hoặc root cause đã quan sát; chưa có regression test
  của lỗi đã sửa.
- Commit/push: `570f75e914320aa594a2ce5453f15ee0593b1830`; đã push `main`, sau
  `git fetch origin`, `HEAD` và `origin/main` cùng SHA.
- Minh chứng: `docs/PHAN_TICH_CA_LOI.md`, `scripts/reproduce_failure.py`;
  không ghi hình hoặc tạo failure giả.

### CP9 — Báo cáo, impact, kịch bản thuyết trình tiếng Việt

- Thời điểm UTC: 2026-10-16 12:20 UTC.
- Trạng thái: PASS cho tài liệu và kịch bản; số đo thực/ca lỗi vẫn thiếu và được
  ghi N/A hoặc NOT DEMONSTRATED.
- Đã thay đổi: `docs/BAO_CAO_KY_THUAT.md`, `docs/PHUONG_PHAP_DANH_GIA.md`,
  `docs/KET_QUA_THUC_NGHIEM.md`, `docs/PHAN_TICH_CA_LOI.md`,
  `docs/QUYEN_RIENG_TU_VA_GIOI_HAN.md`, `docs/KICH_BAN_DEMO_10_PHUT.md`,
  `docs/CAU_HOI_PHAN_BIEN.md`, `docs/CHECKLIST_NOP_BAI.md`, README và tác giả
  trong biên bản.
- Lệnh đã chạy: `.venv/bin/python -m compileall -q src scripts tests` → exit 0;
  `.venv/bin/ruff check .` → exit 0; `.venv/bin/python -m pytest -q` → 90 passed;
  `.venv/bin/python -m pip check` → sạch; rà placeholder → không có kết quả; rà
  liên kết Markdown tương đối → tất cả tồn tại; `git diff --check` → exit 0.
- Điều kiện chấp nhận: kịch bản đúng 1+4+2+3 phút, gồm 12 câu hỏi; report có sáu
  tiêu chí rubric chính thức, tự chấm sơ bộ 54/100 và căn cứ/thiếu; impact 100
  phút/ngày được ghi rõ là giả định; kết quả thật được tách khỏi test kỹ thuật và
  kịch bản giả định. Tất cả tài liệu ghi tác giả duy nhất và MSSV.
- Phần chưa kiểm chứng: chưa diễn tập; chưa có webcam/video người thật, metric
  thực hoặc failure thật; tự chấm không phải điểm giám khảo. Bài cá nhân chưa
  chứng minh điều kiện nhóm và VLearn chưa nộp.
- Commit/push: `96705644b8ab8924da18c555e78badec7e96a2df`; đã push `main`, sau
  `git fetch origin`, `HEAD` và `origin/main` cùng SHA.
- Minh chứng: tám tài liệu CP9 trong `docs/`, liên kết trong `README.md`; rà soát
  README và tài liệu không tìm thấy placeholder.

### CP10 — Kiểm thử cuối và phát hành repo

- Thời điểm UTC: 2026-10-16 12:27 UTC.
- Trạng thái: PASS cho cài đặt sạch, tests/lint/compile, model reproducibility,
  video smoke, privacy scan, GitHub public visibility và đồng bộ; BLOCKED-QUYỀN
  cho webcam vì macOS báo camera chưa được cấp quyền.
- Đã thay đổi: `scripts/validate_submission.py`, kiểm thử help/validator trong
  `tests/test_benchmark.py`, checklist, kết quả cuối và kịch bản demo. Venv sạch
  được tạo ngoài repo bằng Python 3.11; `pip install -e '.[dev]'` thành công.
- Lệnh đã chạy: trong venv sạch, `pytest -q` → 92 passed, `ruff check .`,
  `compileall`, `pip check` và `scripts/check_environment.py` đều exit 0. Model
  được tải lại từ Google Storage với SHA-256 khớp
  `64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff`. Video
  fixture trống 30 frame được DMS xử lý, tạo 30 dòng CSV và trạng thái cuối
  `KHÔNG XÁC ĐỊNH`; replay 2 lượt/30 frame tái lập. Một lần gọi smoke harness đầu
  thiếu biến môi trường cho đường dẫn fixture; đã chạy lại với path tường minh và
  smoke thành công. Validator pre-commit → mọi kiểm tra PASS. Sau commit,
  `scripts/validate_submission.py` → mọi mục PASS, rà 56 tracked files, worktree
  sạch và `main` local = `origin/main` tại SHA dưới đây. Public repository `origin`
  mở được ở GitHub.
- Camera: đã thử chạy DMS live headless; macOS/OpenCV trả “not authorized to
  capture video”, source báo không mở được webcam, exit 2 sau khoảng 1.8 giây.
  Không xử lý frame webcam và không lưu ảnh, video hay CSV. Phải bật quyền cho
  ứng dụng Terminal/Python tại **System Settings → Privacy & Security → Camera**
  rồi mới chạy lại.
- Điều kiện chấp nhận: cài mới và test sạch thành công; model checksum tái lập;
  video fixture chỉ xác nhận luồng kỹ thuật, không được xem là accuracy; rà file
  Git tracked, secret, media, model và đường dẫn ignore; xác nhận repo public.
- Phần chưa kiểm chứng: webcam demo, video fallback người thật, metric thật, FPS
  mục tiêu 12, ca lỗi thật và VLearn. Vì thiếu dữ liệu, không tạo tag `v1.0.0`.
- Commit/push: `fa4cf632f2ba68b6d2f69c152fd1dff47d39f2c7`, commit
  `chore: hoan thien capstone va kiem dinh cuoi`; đã push `main`, fetch xác nhận
  `HEAD` = `origin/main` = SHA này. `origin` giữ nguyên; không force-push.
- Minh chứng: `scripts/validate_submission.py`, `docs/CHECKLIST_NOP_BAI.md`,
  `docs/KET_QUA_THUC_NGHIEM.md`; fixture và venv sạch đều ở thư mục tạm.

### CP11 — Thử lại quyền webcam sau khi tác giả bật Camera

- Thời điểm UTC: 2026-10-16 12:33 UTC.
- Trạng thái: BLOCKED-QUYỀN. Tác giả xác nhận đã bật quyền Camera; lượt DMS live
  vẫn bị macOS/OpenCV từ chối trước khi đọc được frame.
- Lệnh: chạy DMS camera source ở chế độ headless, không bật CSV hoặc ghi video,
  giới hạn tiến trình tối đa 60 giây. OpenCV trả `not authorized to capture video`
  và `camera failed to properly initialize`; CLI báo không mở được webcam.
- Kết quả: thoát mã 2 sau 4,3 giây; 0 frame xử lý. Không lưu ảnh, video hay CSV.
  Đây là lỗi quyền/mở thiết bị, không phải kết quả đánh giá nhận diện.
- Tiếp theo: khởi động lại terminal/app được cấp quyền Camera rồi chạy lại. Nếu
  vẫn lỗi, kiểm tra đúng ứng dụng đã bật trong **System Settings → Privacy &
  Security → Camera**. Các metric trên người và FPS thật vẫn chưa có.

### CP12 — Webcam tích hợp, spot-check tương tác và kiểm định cuối

- Thời điểm UTC: 2026-10-16 13:14 UTC.
- Trạng thái: PASS cho chọn/capture camera index 1, xử lý pipeline live, benchmark
  hiệu năng aggregate, spot-check theo cue và hồi quy video tổng hợp. Chưa chứng
  minh accuracy/false alarms có nhãn độc lập, ca lỗi có root cause xác nhận hoặc
  mục tiêu 12 FPS trung vị.
- Đã thay đổi: `src/vinfast_dms/sources.py` ưu tiên AVFoundation trên macOS, mặc
  định index 1, fallback backend, đếm lỗi đọc và giải phóng resource; CLI/checker
  dùng index 1 mặc định. `PipelineResult` phân biệt mặt được detector thấy với
  landmark qua quality gate. `scripts/benchmark_camera.py` đo webcam headless,
  cue tương tác từng pha và cho phép lặp pha chọn lọc; chỉ xuất aggregate. Tests,
  README, báo cáo, checklist, kịch bản demo và phân tích lỗi được cập nhật.
- Lệnh đã chạy: `scripts/check_camera.py --frames 30` → 30 frame thật, PASS;
  DMS live headless và cửa sổ xử lý 120 frame mỗi lượt, thoát sạch. Benchmark 60 s
  → 1.797 frame, AVFoundation 640×480, 0/1.797 lỗi đọc, nguồn 29,94 FPS, headless
  throughput 29,94 FPS, pipeline capacity 121,66 FPS, latency mean/p50/p95 là
  8,22/8,64/10,90 ms; 1.458/1.797 frame phát hiện mặt và 1.439/1.797 frame
  pipeline-valid. Kiểm tra tương tác hoàn tất 8 pha bắt buộc, bỏ qua pha giảm sáng;
  1.505 frame trong các pha, 0/3.009 lần đọc webcam lỗi. Pha nhắm mắt có 59 frame
  `EYES_CLOSED`; pha nhìn thẳng lần đầu có 137/181 `DISTRACTED` nhưng lượt lặp có
  181/181 `NORMAL`, 0 cảnh báo; pha quay trái có 131/211 `UNKNOWN`, log 126
  `high_reprojection_error`. Đây là quan sát theo cue, không phải metric có nhãn
  độc lập.
- QA CP12: `.venv/bin/python -m pytest -q` → **105 passed**; `ruff check .`,
  `compileall`, `pip check`, `scripts/check_environment.py` thành công. AVI đen tổng
  hợp 30 frame trong thư mục tạm: replay 2 lượt, chữ ký dự đoán giống nhau.
  `scripts/validate_submission.py --allow-dirty --skip-sync` qua; rà 58 file
  tracked sau stage, không media/private/model/secret; author và liên kết đúng.
- Điều kiện chấp nhận: webcam index 1 capture frame và pipeline chạy; cửa sổ
  overlay/cue hiển thị; blink/nhắm mắt, cảnh báo theo thời gian, mất mặt/che mặt và
  `UNKNOWN` được quan sát; capture lỗi có test cleanup. Một lần mở camera thất bại
  thoáng qua trước đó, retry thành công; các lượt đo CP12 sau đó không lỗi đọc.
- Phần chưa kiểm chứng: pha giảm sáng đã bỏ qua; chưa có video được lưu với consent
  và nhãn độc lập, precision/recall/F1, false alarms/phút, event-to-warning,
  camera-to-display, median FPS theo cửa sổ, baseline có nhãn hoặc ca lỗi tái hiện
  ổn định kèm root cause/mitigation. Các báo cáo ghi rõ các giới hạn này.
- Commit/push: CP12 được commit lên `main`, push tới `origin` hiện có; sau fetch,
  SHA local khớp remote-tracking `origin/main`. Không rewrite lịch sử hoặc force-push.
- Minh chứng: `outputs/private/camera_benchmark_cp12_retry.json`,
  `outputs/private/camera_interactive_cp12.json` và
  `outputs/private/camera_normal_repro_cp12.json` chỉ chứa aggregate, bị ignore và
  không commit; replay fixture nằm trong thư mục tạm.
