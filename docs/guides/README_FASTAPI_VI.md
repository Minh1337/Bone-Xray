# Bước 2: API dự đoán X-quang — 27/10/2026

Đây là gói bổ sung cho Bone_Xray_Local_Check đang chạy trên máy của bạn.
Không có trọng số trong ZIP. Dùng lại model/, inference.py, model_definition.py,
cases.json, test_images/ và .venv hiện tại. Không chạy lại 01_setup.bat.
Không thay nội dung các tệp mô hình và không training lại.

## 1. Chép gói vào đúng nơi

Giải nén ZIP, mở thư mục FastAPI_Addon, chép TOÀN BỘ NỘI DUNG bên trong vào:

`C:\Users\Admin\Desktop\Project\Checktest\Bone_Xray_Local_Check`

Sau khi chép, 04_setup_api.bat và xray_api.py phải nằm CÙNG CẤP với inference.py,
cases.json và thư mục .venv. Không đặt thêm một tầng FastAPI_Addon bên trong.
Gói bổ sung không chứa cases.json nên không ghi đè dữ liệu ba ca bạn đang dùng.

## 2. Cài phần API

Nhấp đúp 04_setup_api.bat. Script lưu danh sách phiên bản trước khi cài,
cài phần phụ thuộc API, kiểm tra xung đột pip và chạy 10 kiểm thử bằng mô hình giả.
Thư viện PyTorch, timm và bộ xử lý ảnh không nằm trong danh sách cài bổ sung.
Nếu có lỗi, dừng và gửi logs/api_setup.log; không tự xóa .venv.
Trong log kiểm thử có traceback 'Test failure' được tạo có chủ đích để kiểm tra
xử lý lỗi. Chỉ coi thành công khi cuối kiểm thử có OK và script báo API setup and tests passed.

## 3. Chạy API

Nhấp đúp 05_start_api.bat. Đợi 'Application startup complete'.
Giữ cửa sổ này mở. API chỉ lắng nghe trên máy hiện tại tại 127.0.0.1:8000.
Mô hình được nạp một lần. Một worker, không --reload, tránh nạp model nhiều lần.
CUDA được ưu tiên khi sẵn sàng. Có thể chạy bằng CPU từ CMD khi cần:

```bat
set XRAY_DEVICE=cpu
.venv\Scripts\python.exe -m uvicorn xray_api:app --host 127.0.0.1 --port 8000 --workers 1
```

Nếu cổng 8000 đang bận, dừng cửa sổ API cũ bằng Ctrl+C rồi chạy lại.
Nếu khởi động lỗi, gửi nội dung traceback trong cửa sổ. Không bỏ strict loading.

## 4. Kiểm tra tự động trước

Trong khi cửa sổ API vẫn mở, nhấp đúp 06_verify_api.bat.
Công cụ đọc cases.json hiện tại và ba ảnh trên máy, gửi chúng qua HTTP tới API.
Đối chiếu: mã SHA256 của model/config/mã suy luận, ảnh, metadata và điểm số 10 lớp.
Điểm tham chiếu là report.json của lượt chạy local thành công bạn đã gửi ngày 25/10.
Đổi đuôi tên ảnh đơn thuần không đổi hash. Lưu lại/nén lại ảnh sẽ đổi hash và bị báo lỗi.
Ngưỡng sai lệch tối đa 1e-4; nhãn top-1 phải khớp. Không tự tăng ngưỡng nếu kiểm tra lỗi.
Có thêm hai kiểm tra HTTP thật: thiếu metadata phải trả 422, ảnh hỏng phải trả 415.

Kết quả lưu trong api_results/<thời gian>/api_report.json và api_run_log.txt.
Gửi hai tệp này để kiểm tra bước API. Đạt khi status=API_LOCAL_PARITY_PASSED.
Đây là đối chiếu API với lượt local, KHÔNG phải xác minh khớp notebook.
Chưa biết ba ảnh thuộc train/val/test; không lấy 3/3 ca để công bố accuracy mới.

## 5. Thử thủ công bằng trình duyệt

Mở http://127.0.0.1:8000/docs (giao diện Swagger có thể cần Internet để tải JS/CSS).
- GET /health -> Try it out -> Execute: trạng thái ready, thiết bị và mã mô hình.
- POST /predict -> Try it out:
  - file: chọn IMG000001.jpg trong test_images.
  - metadata: mở metadata_example.json, sao chép toàn bộ object {...} vào ô này.
  - Execute.
  - Response 200 có top1, top3, scores, device, prediction_seconds, model_sha256.

metadata_example.json CHỈ dành cho IMG000001. Không dùng cùng metadata cho ảnh khác.
Với ảnh 2/3, sao chép riêng object metadata tương ứng từ cases.json,
không dán toàn bộ danh sách ca. Không truyền true_label, tumor hay cột nhãn bệnh vào metadata.
GET /metadata-schema liệt kê 22 trường và tên lớp.
Tệp và metadata dùng multipart/form-data; metadata là chuỗi JSON trong một form field.

## 6. Hành vi và giới hạn

- Xử lý một lượt dự đoán tại một thời điểm; yêu cầu đang cạnh tranh trả 429 để thử lại.
- Ảnh tối đa 30 MiB, 25 triệu pixel, một khung; kiểm tra giải mã ảnh thực, không chỉ MIME.
- Nhận JPEG/PNG/BMP/TIFF; không xử lý DICOM/PDF.
- Metadata đủ 22 trường; từ chối dư trường, null, nhị phân ngoài 0/1 hoặc tuổi sai kiểu.
- Giữ nguyên tiền xử lý gốc CLAHE -> 448x448 -> Normalize -> tensor.
- Ảnh tạm được xóa sau yêu cầu. Chưa có lưu lịch sử/database hay giao diện sản phẩm.
- prediction_seconds gồm tiền xử lý + dự đoán trong Predictor, không gồm upload,
  xác minh ảnh, nạp model hoặc toàn bộ HTTP round trip.
- Không gửi ảnh ra ngoài và không gọi API LLM. Swagger tải tài nguyên giao diện từ CDN.
- Điểm số không phải xác suất bệnh đã hiệu chuẩn. Kiểm tra ảnh hợp lệ không nhận biết
  chắc chắn đó là ảnh X-quang u xương phù hợp với phạm vi mô hình.
- Bản này chỉ dùng local: chưa có xác thực, giới hạn body trước parser hoặc cấu hình
  bảo vệ cho triển khai công khai. Không đổi host thành 0.0.0.0 để public bản demo này.

Mã lỗi: 413 quá lớn, 415 định dạng/ảnh hỏng, 422 metadata hoặc thiếu đầu vào,
429 đang bận, 500 lỗi suy luận, 503 mô hình chưa sẵn sàng.

## 7. Kiểm thử đã thực hiện khi soạn gói

10 kiểm thử API đạt trên Linux/Python 3.12 với TestClient và Predictor giả:
luồng thành công + một lần nạp, health/schema, metadata sai/thiếu/dư,
JSON sai/trùng khóa, ảnh rỗng/hỏng/sai đuôi, giới hạn byte/pixel,
dọn ảnh tạm sau lỗi và phục hồi, yêu cầu cạnh tranh, lỗi lúc khởi động.
Predictor giả chỉ tồn tại trong api_tests, không có lựa chọn chạy model giả trên API thật.
Chưa chạy Windows, trọng số thật, CUDA hoặc đối chiếu HTTP trên máy người dùng.
Môi trường API đã cài và pip check thành công trong môi trường kiểm thử.
Các dependency API chính được ghim; phụ thuộc gián tiếp ghi trong logs/after_api_install.txt
trên máy người dùng. Không khẳng định đây là phiên bản mới nhất của các thư viện.

Tài liệu tham khảo: https://fastapi.tiangolo.com/tutorial/request-forms-and-files/
https://fastapi.tiangolo.com/tutorial/testing/

## Sau khi đạt

Giữ report API. Tiếp theo xây giao diện tải ảnh/metadata và hiển thị top-3,
rồi lưu ca vào SQLite. Nhà cung cấp LLM và RAG sẽ xử lý ở bước sau.
