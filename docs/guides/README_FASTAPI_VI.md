# FastAPI — BoneScope hiện tại

API được chạy cục bộ từ thư mục gốc `BONESCOPE/`. Đây không còn là gói
`FastAPI_Addon` tách rời; mã API, model và dữ liệu mẫu nằm cùng repository.

## Cài đặt

Sau khi chạy `01_setup.bat`, chạy `04_setup_api.bat` để cài:

- FastAPI và Starlette
- Uvicorn
- multipart và HTTP client phục vụ API/test

Script cũng chạy test API và ghi log vào `logs/api_setup.log`.

## Khởi động

Chạy:

```text
05_start_api.bat
```

Sau khi thấy `Application startup complete`, mở
`http://127.0.0.1:8000/docs`. API chỉ lắng nghe trên máy hiện tại, dùng một
worker và nạp model một lần. Không chạy đồng thời `05_start_api.bat` và
`07_start_ui.bat` vì cùng dùng cổng 8000.

Có thể ép chạy CPU từ CMD:

```bat
set XRAY_DEVICE=cpu
.venv\Scripts\python.exe -m uvicorn xray_api:app --host 127.0.0.1 --port 8000 --workers 1
```

## Endpoint chính

- `GET /health`: trạng thái model và thiết bị.
- `GET /metadata-schema`: 22 trường metadata và 10 tên lớp.
- `POST /predict`: nhận ảnh và metadata, trả Top-1, Top-3, toàn bộ điểm,
  thiết bị, thời gian suy luận và `prediction_id`.
- `POST /cases`: lưu ca dựa trên `prediction_id` do server cấp; không nhận
  điểm số tự khai từ trình duyệt.
- `GET /cases`, `GET /cases/{id}`, `DELETE /cases/{id}`: lịch sử SQLite.
- Các endpoint nhận xét, hiệu chỉnh và dashboard nằm trong `case_api.py`.

`prediction_id` chỉ được giữ trong bộ nhớ của một tiến trình, hết hạn sau
10 phút và không dùng chung giữa nhiều worker. Đây là giới hạn thiết kế local,
không phải kho trạng thái bền vững cho triển khai production.

## Kiểm tra API

Khi server đang chạy, có thể chạy:

```text
06_verify_api.bat
```

Kết quả được ghi vào `api_results/`, thư mục này bị Git bỏ qua. Nếu không có
server, verify sẽ thất bại rõ ràng; cần khởi động API trước, không coi đó là
kết quả parity.

Chạy test tự động không cần server:

```powershell
.\.venv\Scripts\python.exe -m pytest api_tests -q
```

Test dùng predictor giả để kiểm tra contract và lỗi API; cần chạy
`06_verify_api.bat` để đối chiếu model thật.

## Giới hạn an toàn

API kiểm tra định dạng/giải mã ảnh, giới hạn kích thước, metadata dư/thiếu,
ảnh hỏng và yêu cầu cạnh tranh. Điểm softmax không phải xác suất bệnh đã hiệu
chuẩn. Không đổi host thành `0.0.0.0`, không public API demo này và không gửi
ảnh hoặc metadata bệnh nhân lên dịch vụ ngoài.
