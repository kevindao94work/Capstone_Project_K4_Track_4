# Phân tích ca lỗi

**Tác giả:** Đào Gia Bảo — **MSSV:** 2A202602793.

## Trạng thái bằng chứng

**NOT DEMONSTRATED.** Hiện chưa có video người thật được đồng ý, nhãn độc lập,
clip ID, mốc thời gian hay log dự đoán để khẳng định một lỗi quan sát thật. Vì vậy
tài liệu này không nêu EAR, yaw, trạng thái dự đoán hoặc nguyên nhân gốc của một
ca lỗi giả định như thể đã đo được.

Kiểm thử mất mặt và đầu vào bất hợp lệ trong `tests/test_uncertainty.py` là kiểm
thử hành vi an toàn tổng hợp. Trạng thái `UNKNOWN` đúng khi che mặt/mất track là
stress test có kiểm soát, không phải false prediction. Fixture video đen dùng
trước đó chỉ kiểm tra độ bền luồng video.

## Quy trình tái hiện khi có clip được phép

1. Tự quay clip với consent trong điều kiện cụ thể; lưu ở `data/private/`. Ghi
   lại camera, ánh sáng, khoảng cách và khoảng thời gian cần xem. Không đưa clip
   lên Git.
2. Tự gắn nhãn `NORMAL`, `EYES_CLOSED`, `DISTRACTED` hoặc `UNKNOWN` độc lập với
   dự đoán bằng `scripts/annotate_events.py`; xem lại mốc sự kiện trước khi đánh
   giá.
3. Chạy `python scripts/reproduce_failure.py --source data/private/clip.mp4
   --time-s 12.5 --window-s 4 --labels outputs/private/labels.csv`. Công cụ chạy
   lại model trên toàn clip rồi lưu log và các frame quanh mốc yêu cầu trong
   `outputs/private/failures/`.
4. So sánh nhãn, `state`, `quality_valid`, `quality_reason`, EAR và yaw từng
   frame. Ghi clip ID nội bộ, mốc, trạng thái mong đợi/thực tế, số đo trích từ log,
   nguyên nhân được hỗ trợ bởi log, cách giảm rủi ro và regression test nếu đã sửa.

Sai khác nhãn và trạng thái cần được người đánh giá xác nhận; script chỉ tái chạy
và trích cửa sổ, không tự kết luận root cause. `UNKNOWN` phải được phân tích riêng,
không ép thành `NORMAL`. Log CSV và báo cáo chỉ nên giữ cục bộ vì có thể chứa dấu
thời gian và đặc trưng cá nhân.

## Kế hoạch tình huống cần kiểm tra

Khi có dữ liệu được phép, ưu tiên một tình huống cụ thể như backlight làm landmark
không ổn định, kính làm sai vị trí mắt, quay đầu gây reprojection error cao, hoặc
cảnh báo false positive sau blink. Nếu model trả về chất lượng không hợp lệ thì
kiểm tra việc `UNKNOWN` có an toàn hay không trước khi xem đó là lỗi phân loại.
Chỉ gọi một tình huống là ca lỗi khi log và nhãn độc lập chứng minh hệ thống đưa ra
trạng thái sai hoặc bỏ lỡ một sự kiện cần phát hiện.

**Kết luận hiện tại:** chưa có ca lỗi thực để tái hiện; CP8 chưa được chứng minh.
