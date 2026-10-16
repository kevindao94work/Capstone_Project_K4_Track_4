# Checklist nộp bài

**Tác giả duy nhất:** Đào Gia Bảo — **MSSV:** 2A202602793.

Các mục `CHƯA KIỂM CHỨNG` cần được giữ nguyên trạng thái khi chưa có bằng chứng.

| # | Hạng mục | Trạng thái | Bằng chứng / thao tác cần làm |
|---:|---|---|---|
| 1 | Cài đặt, test, lint, compile và secret/privacy scan | PASS CP10 | Cài mới Python 3.11, 92 test pass; validator quét file tracked, placeholder và ignore. |
| 2 | Repository public, origin đúng và commit remote khớp | PASS sau push CP10 | [Repository public](https://github.com/kevindao94work/Capstone_Project_K4_Track_4); SHA sẽ được xác nhận trong biên bản CP10. |
| 3 | Tên, MSSV và tác giả duy nhất thống nhất | PASS theo tài liệu hiện có | README và báo cáo ghi Đào Gia Bảo / 2A202602793; không teammate giả. |
| 4 | Webcam trên máy demo đã chạy thật | BLOCKED-QUYỀN | Đã thử DMS; macOS báo chưa cấp Camera cho Terminal/Python. Bật quyền tại Privacy & Security → Camera rồi thử lại. |
| 5 | Video fallback người thật có consent và được phép công bố | CHƯA CÓ | Chưa có clip; không dùng fixture tổng hợp làm video demo người thật. |
| 6 | Ít nhất hai trụ cột có code và kiểm thử | PASS kỹ thuật | EAR/PnP, uncertainty, temporal FSM; xem `BAO_CAO_KY_THUAT.md`. |
| 7 | Metric trên video thật có nhãn độc lập | CHƯA CÓ | Cần clip do tác giả quay, consent, label CSV, prediction log và báo cáo. |
| 8 | Một ca lỗi thật có input, mốc, dự đoán, root cause | NOT DEMONSTRATED | Chưa có failure thật; xem `PHAN_TICH_CA_LOI.md`. |
| 9 | Privacy, impact, trình bày và nộp VLearn | Một phần | Media private bị ignore; impact chỉ giả định; script 1+4+2+3 có sẵn. Tác giả tự đăng nhập VLearn và nộp URL public nếu được chấp nhận. |

## Lệnh kiểm tra / chạy

```bash
python scripts/check_environment.py
python -m compileall -q src scripts tests
pytest -q
ruff check .
python -m vinfast_dms --source camera --camera-index 0
```

Chỉ chạy lệnh webcam sau khi tác giả đã cấp quyền Camera. Chạy video bằng đường
dẫn private chỉ khi có consent; không commit raw clip hoặc CSV cá nhân. Nộp trên
VLearn chưa được thực hiện.

## Ràng buộc hành chính

Đề upstream yêu cầu nhóm 3–5 người và mỗi thành viên tự nộp VLearn. Bài này theo
chỉ đạo cá nhân; chưa chứng minh tuân thủ điều kiện nhóm. Quyết định thuộc giảng
viên/VLearn. Không tạo collaborator hoặc đóng góp giả.
