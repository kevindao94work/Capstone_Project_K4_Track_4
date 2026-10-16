# Mô hình

Ứng dụng dùng MediaPipe Tasks Face Landmarker pretrained, không huấn luyện lại.
Tải gói `face_landmarker.task` từ liên kết Google Storage chính thức bằng
`python scripts/download_model.py`. Tệp mô hình không được commit; hãy xem giấy
phép và thông tin phiên bản trên trang mô hình chính thức trước khi phân phối.

SHA-256 của gói đã xác minh ngày 2026-10-16:
`64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff`. Có thể
truyền checksum để từ chối tệp khác:

```bash
python scripts/download_model.py --sha256 64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff
```

URL upstream có thành phần `latest`; nếu nội dung model đổi, cần xác minh và cập
nhật checksum có chủ ý.
