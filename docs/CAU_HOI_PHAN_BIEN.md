# Câu hỏi phản biện và trả lời gợi ý

**Tác giả:** Đào Gia Bảo — **MSSV:** 2A202602793.

1. **Vì sao dùng EAR?**
   EAR là tỷ lệ hình học giữa độ mở dọc và ngang của mỗi mắt. Cách tính nhẹ, dễ
   kiểm tra bằng test; ngưỡng của prototype cần hiệu chỉnh theo người và camera.
2. **Công thức EAR là gì?**
   `(‖p2-p6‖ + ‖p3-p5‖) / (2‖p1-p4‖)`. Tính riêng hai mắt và chỉ lấy trung bình
   khi cả hai hợp lệ; mẫu số gần 0 hoặc dữ liệu lỗi thì trạng thái không xác định.
3. **`solvePnP` cho biết góc chính xác không?**
   Không. Mô hình 3D và camera matrix hiện là heuristic chưa hiệu chuẩn. Tọa độ
   tịnh tiến không phải mét; yaw/pitch chỉ phục vụ minh họa.
4. **Vì sao FSM dùng giây thay vì số frame?**
   Thời lượng cảnh báo không nên thay đổi theo FPS. Dwell-time dùng timestamp
   nguồn, còn EMA điều chỉnh alpha theo khoảng thời gian giữa frame.
5. **Vì sao có `UNKNOWN`?**
   Mất mặt, nhiều mặt, landmark lỗi hoặc pose không đạt quality gate không đủ để
   kết luận bình thường. `UNKNOWN` giữ rõ sự thiếu bằng chứng.
6. **Nếu vừa nhắm mắt vừa quay đầu thì sao?**
   FSM ưu tiên nhắm mắt kéo dài khi cả hai dwell-time đã đạt. Nếu frame không hợp
   lệ, UNKNOWN được ưu tiên hơn mọi cảnh báo cũ.
7. **Chớp mắt có phát cảnh báo không?**
   Bộ lọc yêu cầu trạng thái kéo dài theo thời gian cấu hình; unit test kiểm tra
   chớp ngắn trên timestamp tổng hợp. Chưa đo hành vi trên người thật.
8. **Ngưỡng 0,21 EAR và 30° yaw lấy từ đâu?**
   Đây là giá trị khởi tạo thử trong YAML, không phải ngưỡng y khoa hay kết quả
   hiệu chỉnh. Cần đánh giá trên clip consent và nhãn độc lập trước khi thay đổi.
9. **Temporal FSM tốt hơn baseline chưa?**
   Chưa biết. Có công cụ chạy baseline threshold từng frame và temporal trên cùng
   log/nhãn; hiện thiếu dữ liệu nên chưa có kết luận so sánh.
10. **Accuracy hoặc FPS hiện tại là bao nhiêu?**
    Chưa có số liệu thực trên video người thật/webcam. 90 test là test kỹ thuật,
    không phải accuracy hoặc benchmark tốc độ.
11. **Prototype giữ hình ảnh thế nào?**
    Không ghi hình mặc định; video chỉ ghi khi người dùng bật tùy chọn. CSV cũng
    có thể nhạy cảm và được lưu trong outputs/private, không commit.
12. **Có thể dùng sản phẩm khi xe đang chạy không?**
    Không. Đây không phải ADAS, không có safety case/chứng nhận và cảnh báo giao
    diện chưa được kiểm tra nguy cơ gây xao nhãng.
13. **Impact 100 phút/ngày có phải kết quả?**
    Không. Đó là phép tính giả định 1.000 xe × 1 phút/xe/ngày × 10%; không xác
    nhận VinFast có số xe/đầu vào đó hoặc prototype tạo mức giảm ấy.
14. **Ca lỗi nào đã tìm được?**
    Chưa có failure thật được chứng minh. Mất mặt có thể được kiểm tra thành stress
    test; UNKNOWN đúng là fallback, không phải lỗi phân loại.
15. **Vì sao làm cá nhân khi đề yêu cầu nhóm?**
    Làm cá nhân theo chỉ đạo. Báo cáo công khai rằng chưa chứng minh đáp ứng điều
    kiện nhóm 3–5 người; việc chấp nhận tùy giảng viên/VLearn.
