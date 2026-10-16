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

FSM khởi tạo EMA từ sample hợp lệ đầu tiên; sample này chưa phát warning và không
được lưu làm tư thế neutral. Nếu yaw đầu tiên đã vượt ngưỡng, nó bắt đầu dwell; sau
1,0 giây liên tục mới phát `DISTRACTED`. Frame không hợp lệ chuyển `UNKNOWN` và
xóa dwell/EMA; khoảng thời gian lớn hơn `max_gap_s` cũng trả `UNKNOWN` rồi khởi
động lại. Test xác nhận startup pose không trở thành neutral calibration.

## Trụ cột kiến thức đã thể hiện

| Trụ cột | Vị trí và lựa chọn | Bằng chứng / giới hạn |
|---|---|---|
| Học | Dùng MediaPipe Face Landmarker pretrained; không fine-tune để giữ prototype nhẹ trên CPU. | `models/README.md`, model tải từ nguồn chính thức và checksum lưu trong log; không đo accuracy model riêng. |
| Hình học | EAR hai mắt và PnP từ sáu điểm canonical của MediaPipe. | `src/vinfast_dms/geometry.py`, test correspondence, basis, residual và dấu góc. 3D canonical đúng topology; camera matrix vẫn heuristic, chưa hiệu chuẩn vật lý. |
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

Pose dùng `cv2.solvePnP` với correspondence có thứ tự `(1, 152, 33, 263, 61, 291)`
giữa mũi, cằm, khóe mắt và khóe miệng. Sáu điểm 3D lấy từ
[MediaPipe canonical face model](https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model.obj);
trục canonical được đổi `(x,y,z) → (x,−y,−z)` để đưa +Y/+Z sang quy ước camera
OpenCV. Yaw output đổi dấu về quy ước semantic, dương là quay mũi về phía trái của
chủ thể. PnP dùng `SOLVEPNP_ITERATIVE`; residual là RMS khoảng cách Euclid 2D trên
sáu điểm. Gate giữ ở 12 px.

Camera mặc định giả định `fx=fy=width`, principal point tại tâm ảnh, méo bằng
không; chưa có intrinsic calibration bằng checkerboard. Tọa độ canonical theo
đơn vị của model, không phải số đo cá nhân hay vị trí thực trong xe. Do đó yaw và
pitch là ước lượng demo, không phải góc đã hiệu chuẩn, gaze hoặc hệ trục mét.
Không tính PERCLOS chuẩn lâm sàng, ngáp hoặc chẩn đoán buồn ngủ.

## Dữ liệu, quyền riêng tư và an toàn

Chưa có dataset video người thật được lưu với consent, nhãn thủ công hoặc media
công khai. Trong CP12–CP13, tác giả trực tiếp làm người tham gia cho webcam
spot-check theo cue; chỉ số tổng hợp không được xem là nhãn độc lập. Unit test dùng
mảng/landmark/video tổng hợp và chỉ xác nhận hợp đồng kỹ thuật. Ảnh/video không ghi
theo mặc định. CSV chỉ ghi khi bật `--log-csv`; video chỉ ghi khi bật
`--record-output`. `data/private/` và `outputs/private/` bị loại khỏi Git; model
`.task` cũng không commit. Không dùng dữ liệu bệnh nhân, sinh viên hoặc người bên
thứ ba không đồng ý.

Prototype không được kết nối điều khiển xe, phanh, vô lăng hoặc hệ thống khẩn cấp.
False negative có thể bỏ lỡ dấu hiệu cần quan sát; cảnh báo nhầm có thể gây mất
tin cậy. Không dùng riêng prototype để quyết định về tình trạng sức khỏe hay an
toàn của tài xế.

## Số đo và bằng chứng hiện có

CP12 benchmark 60 giây trên webcam index 1 đạt source/throughput headless 29,94 FPS,
pipeline capacity 121,66 FPS, latency mean/p50/p95 8,22/8,64/10,90 ms và
pipeline-valid 80,08%. CP13 đã đổi basis: pha nhìn thẳng 180/180 valid, 0 warning,
latency p50/p95 6,60/7,16 ms, reprojection median/p95 4,65/4,97 px. Pha quay lớn
vẫn mất một phần quan sát qua `no_face` hoặc residual cao. Các phiên cue đo
coverage và trạng thái quan sát, không có ground truth độc lập nên không báo
accuracy, false-alarm rate có nhãn hoặc event delay. Kết quả chi tiết ở
[kết quả thực nghiệm](KET_QUA_THUC_NGHIEM.md) và [phương pháp](PHUONG_PHAP_DANH_GIA.md).

Neutral yaw CP13 sau sửa có median +0,16°, p05–p95 −0,74°…+1,48°, thấp hơn nhiều
so với ngưỡng 30°. Không có evidence phiên này cần baseline neutral; calibration
tự động có thể che một tư thế quay đầu lúc khởi động. Vì vậy không thêm session
calibration cho bản này. Calibration người dùng chủ động chỉ nên xem xét nếu tập
dữ liệu có nhãn sau này chứng minh offset ổn định và lợi ích.

## Ca lỗi và giới hạn

CP13 tái hiện lỗi quy ước basis PnP bằng pitch nhìn thẳng −175,03°; đổi basis làm
pitch live thành +13,39° và synthetic neutral pitch gần 0°. Đó là ca lỗi hình học
đã có root cause/mitigation và phép đo lại. Góc lớn vẫn có `UNKNOWN`; riêng pha
quay phải còn warning trong recovery, chưa rõ do timing cue, pose outlier hay EMA.
Kịch bản che mặt/mất track trả `UNKNOWN` là hành vi bảo vệ khi không đủ quan sát,
không tự nó là lỗi phân loại. Quy trình tương lai được ghi ở
[phân tích ca lỗi](PHAN_TICH_CA_LOI.md). Tập hiện tại chưa cho phép ước lượng thiên
lệch do kính, ánh sáng, da, camera, khẩu trang, rung xe, góc lắp đặt hoặc khác biệt
giữa người dùng.

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
| Demo chạy được | 25 | 10 | Webcam và overlay chạy; chưa có clip consent dự phòng và chưa đánh giá nhận diện độc lập. |
| Độ hữu ích | 15 | 8 | Nhóm người dùng và vấn đề được nêu; chưa xác nhận nhu cầu với VinFast/đội xe. |
| Impact | 15 | 8 | Có phép tính giả định kèm rủi ro; chưa có đầu vào hoặc tác động thực tế. |
| Bằng chứng | 10 | 3 | Có synthetic geometry, webcam benchmark và ca basis PnP trước/sau; vẫn thiếu nhãn độc lập, accuracy và event latency. |
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
