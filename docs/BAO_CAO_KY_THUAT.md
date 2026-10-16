# Báo cáo kỹ thuật — VinFast Driver Monitoring System

**Tác giả duy nhất:** Đào Gia Bảo — **MSSV:** 2A202602793.

## Tóm tắt

Đây là prototype quan sát khuôn mặt qua webcam hoặc video, ước lượng tình trạng
mắt khép lâu và quay đầu kéo dài. Prototype dùng MediaPipe Face Landmarker dựng
sẵn, hình học EAR, `solvePnP`, bộ lọc theo thời gian và trạng thái `UNKNOWN` khi
đầu vào không đủ tin cậy. Mục đích là hỗ trợ minh họa cách một hệ thống hỗ trợ lái
có thể phản hồi; chưa phải hệ thống ADAS đạt chuẩn an toàn và không dùng khi lái xe
thực tế.

## Người dùng và vấn đề

Người dùng mục tiêu giả định là nhóm kỹ thuật hoặc nghiên cứu trải nghiệm lái xe
của VinFast, cùng người phụ trách đội xe cần khảo sát cảnh báo mệt mỏi/mất tập
trung. Vấn đề cần tìm hiểu là cách biểu diễn tín hiệu mắt và tư thế đầu từ camera
trong cabin, làm trơn theo thời gian và từ chối kết luận khi quan sát không đủ.
Chưa có phỏng vấn người dùng, tích hợp với xe VinFast hay bằng chứng về mức giảm
tai nạn; đây là giả thuyết sản phẩm cho prototype.

## Kiến trúc

```text
Webcam hoặc video
  → VideoSource, timestamp nguồn tăng đơn điệu
  → MediaPipe Tasks FaceLandmarker, tối đa 2 mặt
  → kiểm tra chất lượng / landmarks
  → EAR hai mắt + pose đầu solvePnP
  → EMA theo giây + hysteresis + dwell-time FSM
  → overlay tiếng Việt / CSV tùy chọn / recorder tùy chọn
  → annotate độc lập / evaluate / benchmark / replay
```

Mỗi frame được biểu diễn bằng mốc thời gian, landmark chuẩn hóa, hai EAR, yaw,
pitch và cờ chất lượng; các trường này đi qua dataclass có type hints, không được
ghép thành vector số học nếu thiếu dữ liệu. `UNKNOWN` có ưu tiên khi mất mặt,
nhiều mặt, landmark lỗi, PnP không đạt residual hoặc timestamp/gap lỗi. Pipeline
không dùng trạng thái cảnh báo cũ để suy luận qua frame không hợp lệ.

## Trụ cột kiến thức đã thể hiện

| Trụ cột | Vị trí và lựa chọn | Bằng chứng / giới hạn |
|---|---|---|
| Học | Dùng MediaPipe Face Landmarker pretrained; không fine-tune để giữ prototype nhẹ trên CPU. | `models/README.md`, model tải từ nguồn chính thức và checksum lưu trong log; không đo accuracy model riêng. |
| Hình học | EAR hai mắt và PnP từ sáu điểm mặt. | `src/vinfast_dms/geometry.py`, test bất biến và góc dựng sẵn; camera matrix và 3D mặt là heuristic chưa hiệu chuẩn. |
| Bất định | Quality gates, lý do lỗi cụ thể, `UNKNOWN` thay vì `NORMAL`. | `src/vinfast_dms/uncertainty.py`, `tests/test_uncertainty.py`; chưa đo coverage thật. |
| Thời gian | EMA có alpha phụ thuộc `dt`, hysteresis, dwell-time theo giây và reset khi gap. | `src/vinfast_dms/temporal.py`, test nhiều FPS và timestamp không đều; chưa đo trên webcam. |
| Dữ liệu và bằng chứng | CSV tùy chọn, replay, nhãn thủ công và batch benchmark. | `src/vinfast_dms/metrics.py`, `scripts/`; chưa có clip và kết quả thực nghiệm. |

## Thuật toán và cấu hình

EAR được tính theo công thức
`(‖p2-p6‖ + ‖p3-p5‖) / (2‖p1-p4‖)` cho từng mắt. Chỉ dùng trung bình nếu cả hai
mắt hợp lệ. Ngưỡng khởi tạo `ear_closed=0.21`, `ear_open=0.24`; yaw mất tập trung
khởi tạo `30°`; dwell nhắm mắt `1.2 s`, quay đầu `1.0 s`. Đây là ngưỡng demo có
trong `config/default.yaml`, chưa được hiệu chỉnh từ người dùng hoặc đánh giá độc
lập.

Pose dùng `cv2.solvePnP` trên mốc mũi, cằm, khóe mắt và khóe miệng. Tọa độ 3D có
quy mô tùy ý; ma trận nội tại ban đầu đặt tiêu cự bằng chiều rộng ảnh và méo bằng
không. Vì vậy yaw/pitch chỉ là ước lượng phục vụ demo, không phải góc chính xác,
tọa độ mét hay hướng nhìn (gaze). Hệ thống chưa tính PERCLOS chuẩn lâm sàng, ngáp,
hay chẩn đoán buồn ngủ.

## Dữ liệu, quyền riêng tư và an toàn

Hiện không có dữ liệu người thật, clip được consent, nhãn thủ công hay media công
khai. Unit test dùng mảng/landmark/video tổng hợp và chỉ xác nhận hành vi kỹ thuật.
Ảnh/video không ghi theo mặc định. CSV chỉ ghi khi bật `--log-csv`; video chỉ ghi
khi bật `--record-output`. `data/private/` và `outputs/private/` bị loại khỏi Git;
model `.task` cũng không commit. Không dùng dữ liệu bệnh nhân, sinh viên hoặc người
bên thứ ba không đồng ý.

Prototype không được kết nối điều khiển xe, phanh, vô lăng hoặc hệ thống khẩn cấp.
False negative có thể bỏ lỡ dấu hiệu cần quan sát; cảnh báo nhầm có thể gây mất
tin cậy. Không dùng riêng prototype để quyết định về tình trạng sức khỏe hay an
toàn của tài xế.

## Số đo và bằng chứng hiện có

Tại CP9, `.venv/bin/python -m pytest -q` có 90 passed; ở CP10, clean install
Python 3.11 có **92 passed**, ruff, compileall và `pip check` đều qua. Đây là
kiểm chứng code, không phải độ chính xác hoặc tốc độ ngoài thực địa. Chưa có
benchmark trên video người thật, FPS webcam, latency thực, số false alarm, event
delay hay so sánh baseline có nhãn. Xem [kết quả thực nghiệm](KET_QUA_THUC_NGHIEM.md)
và [phương pháp](PHUONG_PHAP_DANH_GIA.md).

## Ca lỗi và giới hạn

Chưa có ca lỗi thật nào được tái hiện. Kịch bản che mặt/mất track trả `UNKNOWN` là
stress test, không phải lỗi khi đó là trạng thái đúng. Quy trình tương lai được ghi
ở [phân tích ca lỗi](PHAN_TICH_CA_LOI.md). Tập hiện tại chưa cho phép ước lượng
thiên lệch do kính, ánh sáng, da, camera, khẩu trang, rung xe, góc lắp đặt hoặc
khác biệt giữa người dùng.

## Impact giả định và tự đánh giá rubric

Phép tính minh họa giả định: `phút chú ý tiềm năng/ngày = số xe × phút mất chú ý
giả định mỗi xe/ngày × tỷ lệ giảm giả định`. Với 1.000 xe, 1 phút/xe/ngày và mức
giảm giả định 10%, kết quả số học là 100 phút/ngày. Đây chỉ là kịch bản toán học
để kiểm tra độ lớn; mọi đầu vào đều giả định, không phải tác động thực tế, hiệu
quả DMS hay dự báo an toàn của VinFast.

Rubric sáu tiêu chí dưới đây theo [trang đề chính thức](https://github.com/VinUni-AI20k/K4-Track4-ProjectCapstone/blob/main/index.html).
API Face Landmarker tham chiếu [tài liệu MediaPipe Tasks](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/python).
Điểm tự chấm sơ bộ chỉ là
ước lượng cá nhân dựa trên artifact hiện có; giám khảo quyết định điểm cuối.

| Tiêu chí chính thức | Trọng số | Tự chấm sơ bộ | Căn cứ và khoảng trống |
|---|---:|---:|---|
| Vận dụng kiến thức đã học | 25 | 20 | EAR, PnP, uncertainty, temporal có test; chưa có hiệu chuẩn hoặc dữ liệu thật. |
| Demo chạy được | 25 | 10 | CLI video/headless và fixture chạy; webcam chưa kiểm tra, chưa có clip người thật dự phòng. |
| Độ hữu ích | 15 | 8 | Nhóm người dùng và vấn đề được nêu; chưa xác nhận nhu cầu với VinFast/đội xe. |
| Impact | 15 | 8 | Có phép tính giả định kèm rủi ro; chưa có đầu vào hoặc tác động thực tế. |
| Bằng chứng | 10 | 3 | 90 test kỹ thuật có thể chạy lại; thiếu số đo thực và ca lỗi thật. |
| Trình bày và hỏi đáp | 10 | 5 | Có kịch bản và câu hỏi; chưa diễn tập/đánh giá, tiêu chí upstream giả định team. |
| **Tổng tự chấm sơ bộ** | **100** | **54** | Không phải điểm do ban tổ chức xác nhận. |

Đề upstream yêu cầu nhóm 3–5 người và đặt Q&A cho mọi thành viên. Bài làm này
theo chỉ đạo là một tác giả duy nhất, chưa chứng minh tuân thủ điều kiện nhóm; khả
năng được chấp nhận thuộc giảng viên/VLearn. Tác giả cần tự nộp URL repository
public trên VLearn.

## Kết luận

Prototype và bộ công cụ kiểm tra đã được triển khai; mức sẵn sàng thực nghiệm
ngoài đời chưa được chứng minh. Bước cần thiết tiếp theo là xin consent, quay
clip do tác giả đóng vai, gắn nhãn độc lập, chạy đánh giá và tái hiện một ca sai
thực trước khi rút kết luận về độ chính xác hoặc lợi ích.
