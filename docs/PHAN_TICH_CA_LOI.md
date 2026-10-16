# Phân tích ca lỗi

**Tác giả:** Đào Gia Bảo — **MSSV:** 2A202602793.

## CP13.5 — lỗi quy ước basis PnP đã tái hiện và sửa

**Điều kiện tái hiện:** webcam tích hợp MacBook Pro M4, index 1, AVFoundation,
640×480; sáu correspondence canonical MediaPipe; chỉ giữ thống kê aggregate.
Trong lượt nhìn thẳng trước sửa basis, 180/180 pose hợp lệ nhưng pitch median là
−175,03° trong khi yaw median gần 0° (+0,63°), residual median 3,86 px. Điều này
cho thấy `solvePnP` tìm được projection khớp nhưng góc được diễn giải trong basis
không cùng chiều với camera.

**Root cause được xác nhận:** model canonical dùng +Y lên và +Z hướng ra phía mũi;
OpenCV camera dùng +Y xuống và +Z hướng rời camera. Đưa nguyên tọa độ model thẳng
vào PnP làm tư thế nhìn thẳng biểu diễn gần một nửa vòng quay quanh X. Mảng 3D hiện
được đổi bằng phép quay 180° quanh X `(x, y, z) → (x, −y, −z)`; dấu yaw được đổi về
quy ước semantic (+ quay về phía trái của chủ thể). Thay đổi được kiểm tra bằng
pose dựng sẵn, residual gần 0, pitch trung tính gần 0 và hai hướng yaw. Ngưỡng
reprojection **không đổi**, vẫn 12 px.

**Lặp lại trên webcam:** sau sửa, pha nhìn thẳng cho pitch median +13,39°, yaw
median +0,16° (p05–p95: −0,74° đến +1,48°), residual median/p95 4,65/4,97 px;
180/180 frame `NORMAL`, không warning. Trong hold quay trái, yaw median +39,81°;
quay phải −36,28°. Dấu phù hợp với quy ước cue đã dùng. Một lượt ngắn sau đó giữ
chớp mắt 180/180 frame `NORMAL` và nhận `EYES_CLOSED` trong 33/60 frame hold nhắm
mắt; recovery trở lại `NORMAL` 120/120 frame. Đây là đối chiếu trước/sau có số đo
thật, nhưng không có nhãn sự kiện độc lập và không chứng minh accuracy.

**Giới hạn còn lại:** quay trái có 9/60 frame hold `UNKNOWN` do residual vượt gate;
reprojection p95 trên cả hold là 1.201 px vì một outlier 1.203 px. Quay phải có
20/59 frame hold `no_face`; 39 frame còn pose, yaw median −36,28°. Quality gate
đang từ chối residual lớn thay vì buộc thành `NORMAL`. Trong recovery sau quay phải,
52/120 frame vẫn `DISTRACTED`, dù yaw median pha là +4,10° và p05 −36,93°. Chỉ
aggregate không phân biệt được người tham gia còn quay ở đầu recovery, outlier pose
hay thời gian EMA/hysteresis; không tuyên bố đã sửa độ trễ hồi phục. Đây là giới
hạn gần nhất còn được xác minh của CP13.

Ở cùng lượt, hold quay trái có yaw median +39,81° nhưng 51 frame valid đều ở
`NORMAL`; hold quay phải chỉ có 8/39 frame valid là `DISTRACTED`. Đây là đầu ra
đáng điều tra vì ngưỡng yaw cấu hình là 30°, nhưng không có chuỗi yaw/EMA/dwell từng
frame để biết các sample trên ngưỡng có liên tục đủ 1,0 giây hay bị ngắt bởi
quality reset. Vì vậy không hạ dwell, đổi ngưỡng hoặc gọi là false negative đã
xác nhận từ aggregate cue.

Tài liệu hình học tham chiếu [MediaPipe canonical face model](https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model.obj),
[MediaPipe Face Geometry](https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/face_mesh.md)
và [OpenCV solvePnP](https://docs.opencv.org/4.10.0/d5/d1f/calib3d_solvePnP.html).

## Trạng thái bằng chứng

CP13 đã tái hiện và sửa **lỗi hình học quy ước basis** ở trên bằng phép đo trước/sau
và synthetic test. Các cue live không có nhãn độc lập theo timestamp, nên những
trạng thái theo hành vi không được dùng để kết luận phân loại sai hoặc đúng. CP12
được giữ lại dưới đây làm lịch sử và đối chứng có giới hạn.

## Tín hiệu ứng viên trong spot-check CP12 (lịch sử)

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

**Kết luận:** lỗi basis hình học CP13 có root cause và mitigation đã được đo lại;
coverage thấp ở góc quay lớn và warning còn tiếp diễn vào recovery vẫn là giới hạn
chưa được khắc phục. CP12 false warning nhìn thẳng không tái hiện ở CP13. Không có
ground truth độc lập để kết luận accuracy hoặc event latency, nhưng CP13 đã đáp ứng
ca lỗi kỹ thuật có số đo trước/sau.
