# Phân tích ca lỗi

**Tác giả:** Đào Gia Bảo — **MSSV:** 2A202602793.

## Trạng thái bằng chứng

**NOT DEMONSTRATED ở mức ca lỗi có root cause đã xác nhận.** CP12 đã có spot-check
trực tiếp trên người tham gia với cue được bắt đầu thủ công; người tham gia xác
nhận đã thực hiện từng hành vi sau cue và chờ hết pha. Tuy nhiên, lượt này không có
nhãn độc lập theo timestamp, không giữ frame/đặc trưng và chưa tái hiện ổn định một
lỗi. Bằng chứng ứng viên dưới đây được ghi riêng, không trình bày như kết luận
false positive/negative đã được chứng minh.

## Tín hiệu ứng viên trong spot-check CP12

- **Thiết lập:** camera tích hợp MacBook Pro M4, index 1, AVFoundation, 640×480;
  MediaPipe Face Landmarker và cấu hình mặc định. Cửa sổ hiển thị overlay/cue;
  báo cáo chỉ giữ số liệu tổng hợp. Tác giả là người tham gia duy nhất.
- **Pha nhìn thẳng, mắt mở:** người tham gia xác nhận làm theo cue; 181 frame,
  trong đó `DISTRACTED` 137, `NORMAL` 34, `UNKNOWN` 10; 171 frame qua quality
  gate, có 137 frame cảnh báo. Đây là tín hiệu false-alarm ứng viên.
- **Tái kiểm tra:** chạy lại riêng cùng cue trong 6,03 giây; 181/181 frame qua
  quality gate và đều `NORMAL`, không có cảnh báo. Lượt đầu không tái hiện; do đó
  không gọi đây là false alarm xác nhận và không suy đoán nguyên nhân.
- **Pha quay trái:** người tham gia xác nhận làm theo cue; 211 frame, với
  `DISTRACTED` 13, `NORMAL` 67 và `UNKNOWN` 131. Có 126 frame mang lý do
  `high_reprojection_error`, chỉ 80 frame hợp lệ toàn pipeline. Đây là tín hiệu
  ứng viên về giảm coverage khi quay trái. Báo cáo chỉ tổng hợp toàn pha 7 giây;
  không có timestamp riêng cho đoạn giữ đầu 2 giây nên chưa chứng minh chính xác
  một missed event.
- **Giới hạn nguyên nhân:** quality gate PnP loại nhiều quan sát trong pha quay
  trái là lý do được log. Chưa xác định vì ngưỡng residual, mapping/model điểm mặt,
  góc quay thực hay yếu tố khác; không điều chỉnh ngưỡng khi chưa có trace đủ chi
  tiết.

Các pha khác cũng là spot-check theo cue, không có nhãn độc lập. Pha giảm sáng được
bỏ qua; không đưa ra kết luận về ánh sáng yếu. Không có video hoặc ảnh được lưu.

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

**Kết luận hiện tại:** có bất thường ứng viên được quan sát trong pha nhìn thẳng,
nhưng không tái hiện; có tín hiệu quality-gate coverage thấp ở pha quay trái nhưng
chưa có mốc hành vi/dự đoán tường minh. Ca lỗi thật với ground truth độc lập,
root cause được xác định và mitigation được kiểm chứng vẫn **NOT DEMONSTRATED**;
CP8 chưa đạt.
