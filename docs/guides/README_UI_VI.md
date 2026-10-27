# Bước 3 — Giao diện phân tích X-quang

Gói bổ sung chạy trên Windows với API đã đạt API_LOCAL_PARITY_PASSED.
Không cần cài Node.js, không cần API key, không chạy LLM. Không cần cài thêm thư viện Python.
Giao diện dùng HTML/CSS/JavaScript và được phục vụ cùng API, không dùng CDN.

## 1. Sao chép đúng nơi

Giải nén ZIP, mở UI_Addon rồi chép toàn bộ nội dung bên trong vào:
`C:\Users\Admin\Desktop\Project\Checktest\Bone_Xray_Local_Check`

Các tệp/thư mục thêm: xray_ui.py, 07_start_ui.bat, xray_web/, ui_tests/ và README này.
Giữ nguyên xray_api.py, .venv, model/, cases.json, test_images/ và toàn bộ kết quả cũ.

## 2. Khởi động

1. Ở cửa sổ API cũ đang chạy bằng 05_start_api.bat, nhấn Ctrl+C để dừng.
2. Nhấp đúp 07_start_ui.bat. Kiểm thử route sẽ chạy, sau đó mô hình thật được nạp.
3. Khi có 'Application startup complete', mở http://127.0.0.1:8000/.
4. Giữ cửa sổ này mở. Từ nay dùng 07_start_ui.bat khi muốn mở cả giao diện và API.

Không chạy 05 và 07 đồng thời vì cả hai dùng cổng 8000.
Không mở index.html trực tiếp bằng File Explorer. Giao diện phải được mở qua địa chỉ HTTP.
Nếu trang báo Not Found, bạn có thể vẫn đang chạy máy chủ cũ (05); dừng nó và dùng 07.
Nếu báo cổng đã dùng, kiểm tra và dừng cửa sổ máy chủ cũ, không tùy ý kết thúc tiến trình khác.

## 3. Chạy ba ca đã kiểm chứng

1. Ở phần 'Thông tin đi kèm', chọn tệp cases.json bằng nút Nạp metadata JSON.
2. Chọn case_001 trong danh sách ca. Biểu mẫu sẽ có tuổi 48, giới tính F, hip bone=1,
   pelvis=1, frontal=1 và các trường nhị phân còn lại 0.
3. Chọn ảnh IMG000001.jpg tương ứng trong test_images. Đuôi jpg và jpeg được coi tương
   đương khi so tên; nội dung ảnh vẫn cần do bạn xác nhận đúng ca.
4. Đánh dấu xác nhận ảnh và metadata cùng ca, bấm Phân tích ảnh.
5. Kiểm tra top-1 other mt, điểm khoảng 68,35%; bấm Tải kết quả JSON.
6. Chọn case_002, thay ảnh bằng IMG000002.jpg, xác nhận rồi phân tích. Mong đợi osteosarcoma ~95,01%.
7. Chọn case_003, thay ảnh bằng IMG000003.jpg, xác nhận rồi phân tích. Mong đợi osteosarcoma ~94,65%.

Mỗi lần thay ảnh/metadata, kết quả cũ và ô xác nhận bị xóa để tránh nhầm ca.
File kết quả JSON gồm tên ảnh, metadata thực sự đã gửi và toàn bộ phản hồi API.
Gửi ba tệp kết quả này và ảnh chụp giao diện để kiểm tra bước UI.
Các điểm trên chỉ là tham chiếu từ lượt API của bạn, không phải dữ liệu được điền sẵn vào giao diện.
Mọi kết quả hiển thị đều lấy từ POST /predict.

## 4. Nhập ca mới thủ công

Chọn Làm mới trước khi nhập ca mới. Điền tuổi, giới tính và 20 trường nhị phân.
Không để trống các trường, không tự điền 0 khi không biết.
Có thể nạp object metadata riêng (đủ 22 khóa), một object ca, hoặc danh sách ca từ cases.json.
Khi nạp danh sách ca, chỉ metadata được gửi tới mô hình; true_label và expected_scores không được gửi.
Nếu metadata đã nạp gắn với tên ảnh khác, giao diện yêu cầu chọn lại đúng ảnh.
Không tự suy ra nhóm xương/khớp/chi từ ảnh hoặc tên tệp.

## 5. Kiểm tra trước khi xác nhận hoàn thành

- Trang hiển thị Đã kết nối và GPU.
- Ba ca trả kết quả như bảng tham chiếu trên, có thể tải JSON.
- Thay tuổi hoặc ảnh: kết quả cũ biến mất, phải xác nhận lại.
- Thử thiếu một trường: biểu mẫu yêu cầu bổ sung.
- Thử chọn nhầm ca/ảnh: báo tên ảnh mong đợi, không gửi yêu cầu.
- Dừng máy chủ rồi thử Phân tích: có thông báo lỗi kết nối, không hiển thị dự đoán giả.
- Khi máy chủ đang chạy bằng 07, vẫn có thể chạy 06_verify_api.bat để kiểm tra API như cũ.

Ảnh TIFF có thể không xem trước được trong trình duyệt; API vẫn kiểm tra tệp.
Tệp ảnh hỏng có thể được chọn nhưng sẽ bị API từ chối. UI không thể xác minh ảnh ngoài phạm vi
u xương bằng cách chỉ kiểm tra định dạng. Điểm softmax không phải xác suất bệnh đã hiệu chuẩn.

## 6. Phạm vi hiện tại

Đã có: xem trước, nạp JSON, nhập metadata, gửi ảnh, top-3, bảng 10 lớp, tải kết quả,
trạng thái kết nối, trạng thái đang xử lý và xử lý lỗi.
Chưa có: lịch sử SQLite, lưu ảnh lâu dài, hiệu chỉnh, dashboard, LLM/RAG.
Trang làm mới sẽ mất dữ liệu chưa tải. Không dùng localStorage để giữ ảnh hoặc metadata.
Giao diện chỉ chạy local; không mở public server. Mã mô hình và API không thay đổi.
Thời gian hiển thị là prediction_seconds từ API, không phải tổng thời gian chờ của người dùng.
Không tự gắn nhãn kết quả 'tốt' hoặc 'chắc chắn' theo một ngưỡng điểm tùy ý.

Sau khi xác minh UI, bước tiếp theo là lưu lịch sử ca và nhận xét bằng SQLite.

## Kiểm thử trước khi giao

Đã kiểm tra route giao diện cùng API bằng TestClient (mô hình giả), kiểm tra cú pháp JavaScript,
và chạy kiểm thử trình duyệt Chromium trên Linux với API dùng mô hình giả:
nạp cases.json, điền đủ 20 trường nhị phân, chọn ảnh JPG với tên tham chiếu JPEG,
gửi ảnh, hiển thị kết quả và 10 điểm số, tải JSON, xóa kết quả cũ khi đổi dữ liệu,
chặn ảnh/ca khác tên, hiển thị lỗi 429, làm mới biểu mẫu, trạng thái mất kết nối.
Đã xem bố cục desktop và mobile; không phát hiện tràn ngang ở độ rộng 390 px.
Chưa chạy giao diện với trọng số thật trên Windows. Ba ca bạn chạy ở bước 3 là kiểm tra
tích hợp cần thiết. Không có mô hình giả hoặc dữ liệu dự đoán giả trong mã giao diện.
