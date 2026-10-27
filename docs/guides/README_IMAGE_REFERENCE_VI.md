# Bộ ảnh tham chiếu X-quang

## Nguồn và phạm vi

Dự án bổ sung Giai đoạn 11A để quản lý một bộ ảnh X-quang có nhãn và nguồn gốc rõ. Nguồn được chọn là **BTXRD** trên Figshare chính thức, DOI `10.6084/m9.figshare.27865398.v1`, ghi giấy phép **CC BY 4.0**. Bài báo mô tả 3.746 ảnh, 1.879 ảnh xương không u và 1.867 ảnh có u. Trích dẫn: Yao et al., *Scientific Data* 12, 88 (2025), DOI `10.1038/s41597-024-04311-y`.

Trang Figshare cho biết archive `BTXRD.zip` có kích thước 840,474,929 byte; API Figshare trả MD5 `59132a5036d030580ccade8add8f13df`. Script kiểm tra cả hai trước khi giải nén. Ảnh gốc, manifest có metadata ca và bản giải nén được lưu dưới `data/external_datasets/BTXRD/`, đường dẫn này bị Git bỏ qua. Không commit archive/ảnh.

## Cách tạo catalogue

Archive đã được tải và xác minh. Cài dependency trước khi tái tạo catalogue:

```powershell
\.venv\Scripts\python.exe -m pip install -r requirements_rag.txt
.\.venv\Scripts\python.exe tools\prepare_btxrd_reference.py
```

Script xác minh checksum, giải nén an toàn, đọc CSV/XLSX, ghép từng dòng metadata với ảnh, tính SHA-256 ảnh và sinh `reference/manifest.csv` cùng `reference/summary.json`. Bản gốc trong `reference/source/` không bị biến đổi. Catalogue hiện có 3.746 ảnh và đủ 22 metadata hợp lệ; nhãn chuẩn hợp lệ cho 3.745 ảnh. Một ảnh `IMG001276.jpeg` có nhiều subtype cùng bật và được để trống nhãn để rà soát, không tự đoán. Có 21 nhóm exact-duplicate (42 ảnh), chưa tính perceptual duplicate.

Label map đầu ra thống nhất với 10 lớp của checkpoint: no-tumor; osteochondroma; multiple osteochondromas; simple bone cyst; giant cell tumor; osteofibroma; synovial osteochondroma; other bt; osteosarcoma; other mt. Metadata manifest theo 22 trường model yêu cầu và kèm center, license, DOI, attribution và hash.

## Hệ quy chiếu và tránh rò rỉ

Checkpoint đang có lưu đường dẫn huấn luyện BTXRD trong `model/config.json` và tên nguồn trong checkpoint config. Checkpoint chỉ có `split_signature`, không có danh sách image ID cho train/validation/test. Do đó mọi dòng BTXRD được gắn `partition=unassigned` và `independent_of_checkpoint_training=false`. Bộ này chỉ dùng phát triển/kiểm tra pipeline hoặc huấn luyện lại có split đã lưu; **không** dùng để tuyên bố hiệu năng độc lập của checkpoint hiện tại.

Phân bố nhãn hiện tại: no-tumor 1.879; osteochondroma 753; multiple osteochondromas 263; simple bone cyst 206; giant cell tumor 93; osteofibroma 44; synovial osteochondroma 50; other bt 115; osteosarcoma 297; other mt 45. Một ảnh có nhiều subtype cùng bật nên không được ép vào lớp nào. Mỗi dòng có SHA-256, nhưng hash trùng chỉ phát hiện ảnh giống byte; chưa phát hiện crop/resize/ảnh chụp lại.

Không chia ngẫu nhiên ảnh riêng lẻ khi chưa có patient/lesion IDs. Cần hash trùng ảnh, rà perceptual duplicates và giữ nhóm theo bệnh nhân/tổn thương/center nếu IDs có thể xác minh. Đánh giá tổng quát ảnh “chụp ngoài” cần bộ khác BTXRD, có quyền sử dụng và nhãn tham chiếu được chuyên gia xác nhận.

Inference dùng `val_transform.json` hiện tại để so khớp checkpoint; ảnh gốc không bị chuẩn hóa hoặc ghi đè trong catalogue. Báo cáo benchmark sau này cần ma trận nhầm lẫn, precision/recall/F1 theo lớp, macro-F1, top-1/top-3, calibration, kết quả theo center/view và số mẫu loại khỏi scoring. Softmax không được gọi là xác suất đã hiệu chuẩn.

## Trạng thái bàn giao

Archive đã xác minh: MD5 `59132a5036d030580ccade8add8f13df`, SHA-256 `e7c800c3b4e090262b160525a0765f9d93bcc53d639c03806a3ac47b0ded3373`. Phân bố nhãn/hash được lưu trong `data/external_datasets/BTXRD/reference/summary.json`; register được theo dõi trong `docs/reference/btxrd_source_register.json`. Handoff chi tiết tại [Giai đoạn 11](../STAGE11_HANDOFF_VI.md). Cho tới khi khôi phục split gốc hoặc có tập ngoài BTXRD độc lập, chưa công bố accuracy trên ảnh ngoài.
