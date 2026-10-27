# Giao diện web BoneScope

Giao diện HTML/CSS/JavaScript được phục vụ cùng FastAPI từ repository hiện tại.
Không cần Node.js, API key hay CDN để chạy phần giao diện local.

## Khởi động

1. Chạy `01_setup.bat` và `04_setup_api.bat` một lần trên máy mới.
2. Chạy `07_start_ui.bat`.
3. Mở `http://127.0.0.1:8000/`.

Không mở trực tiếp các file HTML bằng Explorer. Không chạy `05_start_api.bat`
đồng thời với `07_start_ui.bat`; nếu cần chạy API riêng, dùng `05_start_api.bat`
và không mở UI ở cổng 8000 cùng lúc.

## Các trang

- `/`: chọn ảnh, nạp metadata JSON, xem Top-1/Top-3 và điểm của 10 lớp.
- `/history`: xem, lọc, phân trang và xóa ca đã lưu trong SQLite.
- `/dashboard`: xem tổng số ca, hiệu chỉnh, nhận xét, phân bố nhãn và thiết bị.
- `/case/{id}`: xem chi tiết, thêm nhận xét và lưu nhãn hiệu chỉnh độc lập.

RAG hiện chưa có chatbot hoặc khung hội thoại trong giao diện. Pipeline RAG chỉ
được chạy bằng CLI và vẫn trả `answer_ready: false`.

## Quy trình phân tích

1. Chọn ảnh JPG, PNG, BMP hoặc TIFF, tối đa 30 MiB.
2. Nạp `cases.json` hoặc object metadata đủ 22 trường.
3. Xác nhận ảnh và metadata là cùng một ca.
4. Bấm **Phân tích ảnh**.
5. Bấm **Lưu ca vào lịch sử** nếu muốn ghi kết quả vào SQLite.

Khi đổi ảnh hoặc metadata, kết quả cũ và ô xác nhận được xóa để tránh nhầm ca.
Dữ liệu hiển thị lấy từ phản hồi API; giao diện không tự suy diễn nhãn hoặc điểm.

## Kiểm thử

Test route/UI không cần mở server:

```powershell
.\.venv\Scripts\python.exe -m pytest ui_tests -q
```

Test toàn bộ repository:

```powershell
.\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q
```

Kết quả gần nhất của toàn bộ suite là **36 passed, 14 subtests passed**. Việc
chạy với model thật trên máy mới cần thêm bước kiểm tra API bằng `06_verify_api.bat`.

## Giới hạn

Giao diện chỉ chạy local, không có xác thực người dùng và không phù hợp để
public Internet. Điểm mô hình không phải chẩn đoán hoặc xác suất bệnh đã hiệu
chuẩn. SQLite, log và kết quả runtime nằm ngoài Git; lịch sử không tự đồng bộ
giữa các máy.
