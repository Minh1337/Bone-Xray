# BoneScope — Hướng dẫn cài đặt và sử dụng trên Windows

BoneScope là ứng dụng chạy cục bộ để phân tích ảnh X-quang u xương bằng mô hình
học sâu, quản lý ca bằng SQLite và thử nghiệm truy xuất tài liệu RAG. Đây là
phần mềm nghiên cứu; kết quả không thay thế chẩn đoán hoặc tư vấn y khoa.

## 1. Lấy mã nguồn

Cài Git và Python **3.11 64-bit**, sau đó chạy:

```powershell
git clone https://github.com/Minh1337/Bone-Xray.git
cd Bone-Xray
```

Model chính nằm trong `model/`. Nếu checkout chỉ có Git LFS pointer, cài Git
LFS rồi tải dữ liệu:

```powershell
git lfs install
git lfs pull
```

Không commit hoặc chia sẻ ảnh bệnh nhân, database runtime, log hay secret.

## 2. Cài môi trường

Nhấp đúp `01_setup.bat`. Script tạo `.venv`, cài PyTorch và dependency mô hình,
chạy kiểm tra cơ bản rồi tạo log trong `logs/`.

Tiếp theo nhấp đúp `04_setup_api.bat` để cài FastAPI và chạy test API.
Không copy `.venv` từ máy khác; hãy tạo lại trên từng máy để tránh lỗi đường dẫn,
Python và phần cứng.

## 3. Khởi động ứng dụng

Nhấp đúp `07_start_ui.bat`, sau đó mở:

```text
http://127.0.0.1:8000/
```

API có tài liệu tại `http://127.0.0.1:8000/docs`. Không chạy
`05_start_api.bat` đồng thời với `07_start_ui.bat` vì cả hai dùng cổng 8000.
Nếu cần chạy API riêng, dùng `05_start_api.bat`.

## 4. Phân tích và lưu ca

1. Chọn ảnh JPG, PNG, BMP hoặc TIFF, tối đa 30 MiB.
2. Nạp `cases.json` hoặc một object metadata JSON đủ 22 trường.
3. Bảo đảm ảnh và metadata thuộc cùng một ca; không tự đoán các trường còn thiếu.
4. Bấm **Phân tích ảnh** để xem Top-1, Top-3 và điểm của 10 lớp.
5. Bấm **Lưu ca vào lịch sử** nếu muốn lưu kết quả vào SQLite.

Các trang chính:

- `/`: phân tích ảnh và metadata.
- `/history`: lịch sử ca đã lưu, lọc và phân trang.
- `/dashboard`: thống kê ca, hiệu chỉnh, nhận xét và thiết bị.
- `/case/{id}`: chi tiết ca, nhận xét và hiệu chỉnh nhãn độc lập.

Database `data/bonescope.db` được tạo tại máy và bị Git bỏ qua. Máy mới sẽ không
có lịch sử từ máy cũ. Nếu cần chuyển lịch sử, dừng ứng dụng rồi sao lưu/copy
database riêng; không đưa dữ liệu bệnh nhân lên repository công khai.

## 5. Tạo chỉ mục RAG cục bộ

RAG hiện mới có corpus, embedding, retrieval, đánh giá và chính sách routing;
**chưa có chatbot và chưa được nghiệm thu để trả lời y khoa**.

Cài dependency và tạo index lần đầu:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements_rag.txt
.\.venv\Scripts\python.exe rag\build_index.py --download-model
.\.venv\Scripts\python.exe rag\evaluate.py
.\.venv\Scripts\python.exe rag\retrieval.py "Chordoma thường xuất hiện ở vùng nào?" --top-k 5
```

Corpus hiện gồm 439 đoạn từ 13 nguồn (12 trang NCI và 1 bài Open Orthopaedics
CC BY 4.0 có giới hạn phạm vi). Các thư mục
`rag\index\`, `rag\models\` và `rag\source_cache\` được tạo/tải tại máy và bị
Git bỏ qua. Lần sau chỉ cần chạy `rag\build_index.py` nếu model embedding đã có.

Hai tùy chọn thử nghiệm không bật mặc định:

```powershell
.\.venv\Scripts\python.exe rag\retrieval.py "..." --rerank-concepts
.\.venv\Scripts\python.exe rag\retrieval.py "..." --verify-evidence
```

`--rerank-concepts` cần kiểm định thêm trên tập độc lập. `--verify-evidence`
đang từ chối nhầm nhiều câu có đáp án nên không dùng cho người dùng cuối.
Cả hai chế độ vẫn trả `answer_ready: false`. Xem [hướng dẫn RAG](docs/README.md)
và [bàn giao giai đoạn 11](docs/STAGE11_HANDOFF_VI.md).

Catalogue ảnh tham chiếu BTXRD Figshare CC BY 4.0 đã được tải và tạo manifest,
nhưng đây cũng là nguồn huấn luyện của checkpoint hiện tại nên không dùng để
tuyên bố hiệu năng độc lập. Xem [hướng dẫn bộ ảnh](docs/guides/README_IMAGE_REFERENCE_VI.md)
và [trạng thái dự án](docs/PROJECT_STATUS_VI.md).

## 6. Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q
```

Kết quả xác nhận ngày 27/10/2026: **39 passed, 31 subtests passed**. Một cảnh báo
deprecated của Starlette không làm test thất bại.

## 7. Tài liệu và giới hạn

- [README tổng quan](README.md)
- [Trạng thái dự án](docs/PROJECT_STATUS_VI.md)
- [Lộ trình thực hiện](docs/LO_TRINH_THUC_HIEN_DU_AN_AI.md)
- [Hướng dẫn corpus RAG](docs/guides/README_RAG_CORPUS_VI.md)
- [Hướng dẫn index và retrieval](docs/guides/README_RAG_INDEX_VI.md)
- [Hệ quy chiếu ảnh X-quang](docs/guides/README_IMAGE_REFERENCE_VI.md)
- [Thiết kế kiểm tra bằng chứng](docs/reference/EVIDENCE_CHECK_DESIGN_VI.md)

Mô hình ảnh chưa được tuyên bố là có accuracy lâm sàng hoặc xác suất đã hiệu
chuẩn. RAG còn thiếu nguồn cho một số nhãn, chưa có chatbot, chưa có citation
generation và chưa được phép dùng để tự chẩn đoán hay đề xuất phác đồ.
