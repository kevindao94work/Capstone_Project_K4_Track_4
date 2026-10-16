# Kịch bản demo 10 phút

**Người trình bày duy nhất:** Đào Gia Bảo — **MSSV:** 2A202602793.

Kịch bản bám đúng 1 + 4 + 2 + 3 phút. Đã thử DMS live ở CP10 nhưng macOS báo
Terminal/Python chưa được cấp quyền Camera; chưa có frame webcam được xử lý. Chưa
có video người thật có consent trong repo; phần thao tác dưới đây là kế hoạch,
không phải tuyên bố đã diễn ra. Không dùng fixture đen làm video demo nhận diện.

## 0:00–1:00 — Bài toán và người dùng

“Em là Đào Gia Bảo, MSSV 2A202602793. Prototype này tìm hiểu cách quan sát dấu
hiệu nhắm mắt kéo dài và quay đầu qua camera cabin. Người dùng mục tiêu giả định
là nhóm kỹ thuật nghiên cứu trải nghiệm lái và đội xe của VinFast. Đây là demo
nghiên cứu, không phải hệ thống an toàn, không chẩn đoán buồn ngủ và không dùng
khi lái xe thật. Em sẽ chỉ kết luận điều gì có artifact kiểm chứng.”

## 1:00–5:00 — Demo 4 phút

### 1:00–1:40 — Khởi động

Sau khi đã cấp quyền Camera trong cài đặt macOS và tải model:

```bash
python -m vinfast_dms --source camera --camera-index 0
```

Cho xem khung landmark, EAR hai mắt, yaw/pitch, hợp lệ, FPS/độ trễ và trạng thái
tiếng Việt. Nếu quyền camera chưa được cấp, nói rõ trạng thái và chuyển sang video
đã được cho phép; không giả làm webcam trực tiếp.

### 1:40–2:20 — Nhìn thẳng và chớp mắt

Nhìn thẳng rồi chớp mắt tự nhiên. Giải thích một frame EAR thấp chưa đủ phát cảnh
báo; bộ lọc dùng thời gian và dwell. Chỉ mô tả hành vi nếu webcam hoạt động thật.

### 2:20–3:00 — Nhắm mắt duy trì

Trong demo mô phỏng khi đứng yên, nhắm mắt ngắn rồi mở lại; sau đó minh họa nhắm
mắt duy trì nếu an toàn. Chỉ ra ngưỡng cấu hình và thời gian giữ là giá trị thử,
không phải ngưỡng y khoa.

### 3:00–3:40 — Quay đầu và che mặt

Quay đầu sang bên trong lúc đứng yên, sau đó che mặt hoặc bước ra khỏi khung. Nếu
quality gate không đủ, giao diện phải hiện `KHÔNG XÁC ĐỊNH`, không dùng
`BÌNH THƯỜNG`. Nói rõ yaw không phải gaze.

### 3:40–5:00 — Video fallback

Chỉ khi có clip tự quay/được consent:

```bash
python -m vinfast_dms --source data/private/consented_demo.mp4 --headless
```

Ghi log riêng tư chỉ khi cần đo:

```bash
python -m vinfast_dms --source data/private/consented_demo.mp4 --headless \
  --log-csv outputs/private/demo.csv
```

Hiện tại chưa có clip fallback được chuẩn bị hoặc phép chạy demo trên người thật.
Nếu không có video đã được phép, dành thời gian này để chỉ cấu trúc luồng và gọi
đúng tên fixture kỹ thuật; không trình bày fixture là dữ liệu người thật.

## 5:00–7:00 — Trụ cột, số đo, ca lỗi và impact

- **Trụ cột:** pretrained Face Landmarker; hình học EAR/PnP; uncertainty với
  `UNKNOWN`; thời gian với EMA/dwell; log/replay/evaluation. Nêu test file tương
  ứng và giới hạn PnP chưa hiệu chuẩn.
- **Số đo:** hiện 92 test kỹ thuật đã pass theo kiểm định CP10; đây không phải metric
  thực nghiệm. Confusion matrix, event delay, latency, FPS và baseline chỉ được
  báo khi có video + nhãn thật.
- **Ca lỗi:** chưa có ca lỗi thực; mất mặt trả UNKNOWN là hành vi fallback đúng,
  không gọi là failure. Mở `docs/PHAN_TICH_CA_LOI.md` để nêu cách tìm failure thật.
- **Impact giả định:** với giả định 1.000 xe, 1 phút/xe/ngày và giảm 10%, phép nhân
  cho ra 100 phút/ngày. Tất cả đầu vào giả định; con số không phải tác động được
  đo hoặc tuyên bố của VinFast.

## 7:00–10:00 — Hỏi đáp

Mỗi câu trả lời ngắn, gắn với code hoặc log; nếu chưa có bằng chứng, trả lời
“chưa đo/chưa kiểm chứng”. Một tác giả duy nhất nên có thể giải thích toàn hệ thống,
nhưng điều đó không thay thế điều kiện nhóm 3–5 người của đề upstream.

Danh sách 12 câu gợi ý nằm trong [câu hỏi phản biện](CAU_HOI_PHAN_BIEN.md). Ưu
tiên câu EAR, PnP, temporal, UNKNOWN, baseline, consent và giới hạn sử dụng.

## Kiểm tra trước khi lên trình bày

1. Cấp quyền Camera macOS; tự chạy webcam trên đúng máy, rồi thử ánh sáng/che mặt.
2. Nếu có video, xác nhận consent, codec, đường dẫn và lệnh trước buổi demo.
3. Tải model từ `scripts/download_model.py`; kiểm tra môi trường bằng
   `scripts/check_environment.py`.
4. Đóng ứng dụng nặng, cắm nguồn, tắt thông báo và giữ video/log ở thư mục private.
5. Nếu live demo lỗi, nói rõ lỗi rồi chuyển sang video đã được phép; không khẳng
   định demo live hoặc clip dự phòng đã thử khi chưa thực hiện.
