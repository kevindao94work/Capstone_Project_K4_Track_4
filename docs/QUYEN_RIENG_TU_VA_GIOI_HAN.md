# Quyền riêng tư và giới hạn

**Tác giả:** Đào Gia Bảo — **MSSV:** 2A202602793.

## Nguyên tắc sử dụng dữ liệu

- Chỉ quay người đã được thông báo và đồng ý; ưu tiên tác giả tự đóng vai.
- Không sử dụng video bệnh nhân, sinh viên hoặc người thứ ba không đồng ý.
- Chưa có video người thật được cấp quyền trong repo này; thư mục private trống
  dữ liệu theo dõi.
- Không bypass cơ chế quyền Camera của macOS. Người dùng cấp quyền tại
  **System Settings → Privacy & Security → Camera** rồi tự gọi CLI.
- Không dùng hình ảnh, gương mặt hoặc số đo để nhận diện danh tính, chẩn đoán y
  khoa, tuyển dụng, kỷ luật hay quyết định điều khiển xe.

## Ghi, lưu và chia sẻ

1. Ứng dụng không ghi video/ảnh mặc định.
2. `--log-csv` bật ghi số đo và trạng thái từng frame; CSV vẫn có dấu thời gian,
   có thể nhạy cảm. Không log vào thư mục public.
3. `--record-output` chủ động ghi video overlay và chỉ nên bật khi có consent.
4. `data/private/` và `outputs/private/` bị Git bỏ qua; video phổ biến, model
   binary và tệp bí mật cũng bị ignore. Kiểm tra `git status` trước khi push.
5. Giữ clip chỉ trong thời gian cần thiết; xóa thủ công khi không còn cần. Không
   có server upload hoặc xử lý cloud trong prototype.
6. Chỉ công bố artifact tổng hợp sau khi xác nhận không lộ hình ảnh, danh tính,
   đường dẫn nội bộ hay dữ liệu cá nhân.

## Giới hạn kỹ thuật

MediaPipe Face Landmarker là model dựng sẵn; không có huấn luyện hoặc đánh giá
trên bộ dữ liệu mục tiêu. Mốc 3D của PnP có quy mô tùy ý và camera intrinsics là
heuristic. EAR có thể thay đổi theo người, góc mặt, kính, ánh sáng và độ phân giải.
Yaw không đo hướng mắt/gaze. Ngưỡng chưa được hiệu chỉnh cá nhân và dwell-time
không chứng minh buồn ngủ.

Prototype không tính PERCLOS chuẩn lâm sàng, ngáp hoặc chỉ số y tế; không phải
thiết bị an toàn chức năng, không có safety case và không được dùng khi xe đang
chạy. `UNKNOWN` có nghĩa là quan sát không đủ, không có nghĩa là người lái bình
thường. Cảnh báo thị giác trên màn hình không được kiểm tra về nguy cơ gây xao
nhãng khi lái.

## Rủi ro cần đánh giá trước mọi ứng dụng thật

| Rủi ro | Cách xử lý hiện có | Phần còn thiếu |
|---|---|---|
| Mất landmark hoặc nhiều mặt | Quality gate đưa về `UNKNOWN`. | Đo coverage và kiểm tra khi lái trong cabin. |
| False negative nhắm mắt/quay đầu | Dwell state và log tùy chọn. | Nhãn độc lập, recall, phân tích failure thật. |
| False positive gây mệt vì cảnh báo | Hysteresis/dwell, cảnh báo hình ảnh. | False alarms/phút và nghiên cứu người dùng. |
| Sai lệch theo kính, da, ánh sáng, camera | Không kết luận khi quality gate thất bại. | Bộ dữ liệu đa dạng, consent, phân tích subgroup. |
| Rò rỉ dữ liệu gương mặt | Lưu cục bộ và ignore thư mục riêng tư. | Quy trình retention/access được phê duyệt nếu triển khai. |
| Hệ thống bị hiểu nhầm là ADAS/an toàn y tế | Cảnh báo trong README và giao diện. | Phê duyệt pháp lý, an toàn chức năng và xác nhận chuyên gia. |

Không có sự chứng thực, tích hợp hoặc triển khai của VinFast được khẳng định trong
báo cáo này.
