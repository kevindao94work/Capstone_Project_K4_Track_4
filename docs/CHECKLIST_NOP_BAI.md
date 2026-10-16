# Checklist nộp bài

**Tác giả duy nhất:** Đào Gia Bảo — **MSSV:** 2A202602793.

Các mục `CHƯA KIỂM CHỨNG` cần được giữ nguyên trạng thái khi chưa có bằng chứng.

| # | Hạng mục | Trạng thái | Bằng chứng / thao tác cần làm |
|---:|---|---|---|
| 1 | Cài đặt, test, lint, compile và secret/privacy scan | PASS CP13 | Python 3.11.15: 121 test pass, Ruff, compileall, pip check, environment check và validator pass; validator rà 58 file tracked. |
| 2 | Repository public, origin đúng và commit remote khớp | PASS các checkpoint CP13 | [Repository public](https://github.com/kevindao94work/Capstone_Project_K4_Track_4); từng checkpoint CP13 đã push và SHA local/remote khớp; xác nhận lại sau commit tài liệu cuối. |
| 3 | Tên, MSSV và tác giả duy nhất thống nhất | PASS theo tài liệu hiện có | README và báo cáo ghi Đào Gia Bảo / 2A202602793; không teammate giả. |
| 4 | Webcam trên máy demo đã chạy thật | PASS capture; spot-check có giới hạn | CP13: index 1 / AVFoundation 640×480; 0 lỗi đọc ở các phiên cue. Lượt CLI cuối cho thấy cùng camera MacBook được ánh xạ index 0; smoke và DMS CLI 30 frame pass tại index 0. Kiểm tra index trước demo. |
| 5 | Video fallback người thật có consent và được phép công bố | CHƯA CÓ | Chưa có clip; không dùng fixture tổng hợp làm video demo người thật. |
| 6 | Ít nhất hai trụ cột có code và kiểm thử | PASS kỹ thuật | EAR/PnP, uncertainty, temporal FSM; PnP có kiểm thử canonical correspondence, basis và yaw sign; xem `BAO_CAO_KY_THUAT.md`. |
| 7 | Hiệu năng webcam / metric trên dữ liệu có nhãn độc lập | FPS/latency đã đo; accuracy có nhãn CHƯA CÓ | Bộ đánh giá hỗ trợ precision/recall/F1, confusion matrix, false alarms/phút NORMAL, event delay, coverage và abstention. Chưa có consent clip/nhãn độc lập nên metric thực nghiệm vẫn pending. |
| 8 | Một ca lỗi thật có input, mốc, dự đoán, root cause | PASS lỗi basis PnP; giới hạn quay đầu còn lại | Pitch frontal gần −175° trước sửa, do lệch basis MediaPipe/OpenCV; sau đổi basis pitch +13,39° và live yaw hai hướng đúng dấu. Vẫn có frame `UNKNOWN` ở góc lớn và warning trong recovery; không tuyên bố hết lỗi. Xem `PHAN_TICH_CA_LOI.md`. |
| 9 | Privacy, impact, trình bày và nộp VLearn | Một phần | Webcam aggregate ở `outputs/private/` không commit; không lưu media. Impact chỉ giả định; script 1+4+2+3 có sẵn. Tác giả tự đăng nhập VLearn và nộp URL public nếu được chấp nhận. |

## Lệnh kiểm tra / chạy

```bash
python scripts/check_environment.py
python -m compileall -q src scripts tests
pytest -q
ruff check .
python -m vinfast_dms --source camera --camera-index 0
```

Index webcam mặc định là 1 trên MacBook này; dùng `scripts/check_camera.py` để
smoke-test. Chạy video bằng đường dẫn private chỉ khi có consent; không commit raw
clip hoặc CSV cá nhân. Nộp trên VLearn chưa được thực hiện.

## Ràng buộc hành chính

Đề upstream yêu cầu nhóm 3–5 người và mỗi thành viên tự nộp VLearn. Bài này theo
chỉ đạo cá nhân; chưa chứng minh tuân thủ điều kiện nhóm. Quyết định thuộc giảng
viên/VLearn. Không tạo collaborator hoặc đóng góp giả.
