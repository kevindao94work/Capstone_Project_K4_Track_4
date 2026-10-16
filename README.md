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

Tải model một lần bằng `python scripts/download_model.py` sau khi CP1 được triển
khai. File model được lưu cục bộ, không theo dõi bằng Git.

## Chạy

Lệnh demo webcam và video sẽ được bổ sung cùng CLI ở CP1–CP5. Quyền webcam do
macOS quản lý; cấp quyền trong **System Settings → Privacy & Security → Camera**.
Video và ảnh không được ghi mặc định. Log CSV chỉ tạo khi bật `--log-csv` và nằm
trong `outputs/private/`.

## Kiểm tra kỹ thuật

```bash
python scripts/check_environment.py
python -m compileall -q src scripts tests
pytest -q
ruff check .
```

## Đối chiếu đề bài

Đề bài upstream mô tả capstone Track 4, 2 giờ xây dựng, demo tối đa 10 phút, ít
nhất hai trụ cột, một số đo, một ca lỗi và dữ liệu an toàn. Upstream giới thiệu
bảy trụ cột và sáu tiêu chí chấm trên 100 điểm. Hướng dẫn triển khai này mở rộng
phạm vi thành CP0–CP10 và khuyến nghị sáu trụ cột. Điều kiện làm cá nhân được ghi
minh bạch như chưa chứng minh tuân thủ yêu cầu đội; quyết định thuộc ban tổ chức.

## Tài liệu

- [Báo cáo kỹ thuật](docs/BAO_CAO_KY_THUAT.md)
- [Phương pháp đánh giá](docs/PHUONG_PHAP_DANH_GIA.md)
- [Kết quả thực nghiệm](docs/KET_QUA_THUC_NGHIEM.md)
- [Quyền riêng tư và giới hạn](docs/QUYEN_RIENG_TU_VA_GIOI_HAN.md)
- [Checklist nộp bài](docs/CHECKLIST_NOP_BAI.md)
