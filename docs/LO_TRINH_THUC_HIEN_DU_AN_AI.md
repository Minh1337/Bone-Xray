# Lộ trình thực hiện BoneScope cho AI

> **Mục đích:** Tài liệu này là runbook dành cho các AI hoặc kỹ sư tiếp quản dự án
> BoneScope/Bone X-ray Local Check. Có thể đọc từ đầu đến cuối để dựng lại môi
> trường, kiểm tra mô hình, chạy API, chạy giao diện, xác minh dữ liệu và tiếp tục
> phát triển các phần RAG/LLM.
>
> **Nguyên tắc bắt buộc:** Sau khi hoàn thành **mỗi giai đoạn**, phải ghi một
> **Completion Note** theo mẫu ở cuối giai đoạn. Không được đánh dấu hoàn thành
> chỉ vì lệnh khởi chạy không báo lỗi; phải dựa trên tiêu chí nghiệm thu và lưu
> bằng chứng.

---

## 0. Tóm tắt dự án và trạng thái bàn giao

### 0.1. Mục tiêu sản phẩm

BoneScope là ứng dụng chạy cục bộ trên Windows để:

1. Nhận ảnh X-quang và 22 trường metadata.
2. Dùng mô hình học sâu Swin + Cross-Attention để phân loại 10 lớp u xương.
3. Trả về nhãn Top-1, Top-3, điểm số của toàn bộ 10 lớp, thiết bị và thời gian suy luận.
4. Lưu ca phân tích trong SQLite.
5. Cho phép xem lịch sử, chi tiết ca, thêm nhận xét và lưu nhãn hiệu chỉnh độc lập
   với dự đoán gốc.
6. Hiển thị dashboard thống kê.
7. Làm nền tảng cho kho tài liệu y khoa, tìm kiếm ngữ nghĩa RAG và chatbot tiếng Việt
   có trích dẫn nguồn ở giai đoạn sau.

### 0.2. Phạm vi hiện tại

- **Đã có:** pipeline suy luận cục bộ, kiểm tra model, API FastAPI, giao diện HTML/CSS/
  JavaScript, SQLite, lịch sử ca, nhận xét, hiệu chỉnh, dashboard, kiểm thử tự động
  và Git LFS cho model.
- **Đã xác minh kỹ thuật:** môi trường Python 3.11.9, PyTorch 2.6.0 + CUDA 12.4,
  RTX 3050 Laptop 4 GB, 3 ca mẫu chạy đạt kiểm tra lặp lại.
- **Chưa được tuyên bố:** notebook parity đầy đủ, accuracy lâm sàng, xác suất đã hiệu
  chuẩn, chẩn đoán y khoa, triển khai public có xác thực, RAG hoặc LLM.
- **Cần phát triển tiếp:** kho tài liệu y khoa, embeddings, vector index, chatbot,
  đánh giá toàn diện, bảo mật triển khai và tài liệu/slide bàn giao cuối.

### 0.3. Quy tắc an toàn và tính trung thực

1. Không đổi kiến trúc model, preprocessing, tên lớp hoặc strict loading để “làm cho
   chạy được” khi chưa có bằng chứng tương thích.
2. Không tự bịa metadata còn thiếu; phải lấy từ dòng dữ liệu gốc.
3. Không gọi các điểm softmax là xác suất bệnh đã hiệu chuẩn.
4. Không gọi kết quả kỹ thuật trên 3 ảnh là accuracy của toàn bộ dataset.
5. Không mở server này ra Internet bằng cách đổi host thành `0.0.0.0`.
6. Checkpoint và file joblib có thể chứa mã thực thi; chỉ nạp tệp đáng tin cậy.
7. Không commit database runtime, log, kết quả chạy, `.venv` hoặc secret.
8. Dữ liệu ảnh X-quang và thông tin bệnh nhân phải được xử lý như dữ liệu nhạy cảm.

### 0.4. Cấu trúc cần biết

```text
Bone_Xray_Local_Check/
├── .vscode/                 # cấu hình debug
├── docs/                    # tài liệu, roadmap, báo cáo
├── model/                   # checkpoint, config, preprocessing
├── test_images/             # ảnh mẫu
├── xray_web/                # frontend tĩnh
├── tests/                   # validation tests
├── api_tests/               # API và case-management tests
├── ui_tests/                # route/UI integration tests
├── check_model.py           # kiểm tra model offline
├── inference.py             # Predictor và preprocessing
├── model_definition.py      # kiến trúc model
├── validation.py            # validation cases và score comparison
├── xray_api.py              # FastAPI prediction service
├── case_api.py              # case/comment/correction/dashboard routes
├── database.py              # SQLite và schema
├── xray_ui.py               # ghép API, case routes và static UI
├── cases.json               # 3 ca mẫu có metadata
├── requirements.txt         # dependency model/inference
└── requirements_api.txt     # dependency API
```

### Completion Note — Giai đoạn 0

```text
[COMPLETION NOTE — GĐ0]
Ngày/giờ:
Người/AI thực hiện:
Commit hoặc phiên bản:
Đã xác nhận: mục tiêu, phạm vi, giới hạn và cấu trúc dự án.
Bằng chứng: đường dẫn/tên tệp hoặc kết quả lệnh.
Vấn đề còn lại:
Quyết định cho giai đoạn tiếp theo:
```

---

## 1. Chuẩn bị máy, quyền riêng tư và workspace

### Mục tiêu

Tạo một bản sao làm việc độc lập, giữ nguyên dữ liệu gốc và tránh đưa dữ liệu nhạy
cảm lên dịch vụ ngoài.

### Việc AI phải làm

1. Xác nhận hệ điều hành Windows 10/11 64-bit.
2. Xác nhận RAM, dung lượng ổ đĩa trống và GPU NVIDIA nếu có.
3. Mở đúng thư mục gốc `Bone_Xray_Local_Check`, không chạy bên trong file ZIP.
4. Kiểm tra thư mục `model/`, `test_images/`, `cases.json`, `requirements*.txt`.
5. Không xóa hoặc sửa `model/best_model.pt`, `metadata_processor.joblib`,
   `val_transform.json`, `config.json` nếu chưa có yêu cầu và bản sao lưu.
6. Kiểm tra `.gitignore` trước khi tạo file mới. Runtime database nằm ở
   `data/bonescope.db`; log nằm ở `logs/`; kết quả nằm ở `results/` và
   `api_results/`.
7. Nếu dữ liệu là dữ liệu bệnh nhân thật, thay thế bằng dữ liệu đã ẩn danh trước khi
   chia sẻ, commit hoặc đưa vào báo cáo.

### Kiểm tra tối thiểu

```powershell
Get-Location
Get-ChildItem
git status --short --branch
Get-ChildItem .\model
Get-ChildItem .\test_images
```

### Tiêu chí nghiệm thu

- Đang đứng đúng thư mục dự án.
- Model và ảnh mẫu có mặt hoặc đã ghi rõ tệp nào còn thiếu.
- Không có secret, token, dữ liệu bệnh nhân chưa ẩn danh trong file chuẩn bị commit.
- `git status` không cho thấy thay đổi ngoài phạm vi đã biết.

### Completion Note — Giai đoạn 1

```text
[COMPLETION NOTE — GĐ1]
Ngày/giờ:
Máy/OS/GPU/RAM:
Đường dẫn workspace:
Đã kiểm tra: model, ảnh mẫu, cases.json, .gitignore, dữ liệu nhạy cảm.
Bằng chứng:
Tệp còn thiếu hoặc rủi ro:
Trạng thái nghiệm thu: PASS / BLOCKED
```

---

## 2. Cài Python và môi trường ảo

### Mục tiêu

Tạo môi trường tái lập bằng Python 3.11 64-bit. Không dùng Python mới hơn một cách
tùy tiện vì model và dependency đã được kiểm tra trên Python 3.11.

### Chuẩn bị

1. Cài Python 3.11 64-bit và Python Launcher (`py`).
2. Bật tùy chọn `Add python.exe to PATH` nếu chính sách máy cho phép.
3. Đảm bảo có Internet trong lúc cài dependency và có vài GB dung lượng trống.
4. Với GPU, cài driver NVIDIA tương thích. Không cần cài CUDA Toolkit riêng cho
   bộ kiểm tra này; wheel PyTorch CUDA 12.4 cung cấp runtime cần thiết.

### Cài đặt chính thức

Chạy từ Explorer hoặc CMD:

```bat
01_setup.bat
```

Script thực hiện:

1. Kiểm tra Python 3.11 và tiến trình 64-bit.
2. Tạo `.venv` nếu chưa tồn tại.
3. Nâng pip.
4. Cài `torch==2.6.0` và `torchvision==0.21.0` từ index CUDA 12.4.
5. Cài `requirements.txt`.
6. Chạy `pip check`.
7. Lưu phiên bản vào `logs/installed_versions.txt`.
8. Chạy test trong `tests/`.

### Các dependency chính

| Nhóm | Gói/phiên bản |
|---|---|
| Deep learning | `torch==2.6.0`, `torchvision==0.21.0` (`cu124`) |
| Model/ảnh | `timm==1.0.15`, `albumentations==2.0.8`, `Pillow==11.1.0`, `opencv-python-headless==4.11.0.86` |
| Dữ liệu | `numpy==1.26.4`, `pandas==2.2.3`, `scikit-learn==1.6.1`, `joblib==1.4.2` |
| Hệ thống | `psutil==7.0.0` |

### Chẩn đoán lỗi

- Cài lỗi: chỉ đọc `logs/setup.log`, không xóa `.venv` ngay.
- `py -3.11` không tồn tại: cài Python 3.11 64-bit hoặc sửa PATH.
- `pip check` lỗi: ghi nguyên văn lỗi và phiên bản; không tự nâng/hạ version.
- GPU không nhận: kiểm tra driver, `torch.cuda.is_available()` và log; thử CPU ở
  giai đoạn riêng, không kết luận model hỏng.

### Tiêu chí nghiệm thu

- Có `.venv\Scripts\python.exe`.
- `01_setup.bat` báo `Setup complete`.
- `logs/setup.log` không có lỗi cài đặt.
- `pip check` đạt.
- `tests` đạt.

### Completion Note — Giai đoạn 2

```text
[COMPLETION NOTE — GĐ2]
Ngày/giờ:
Python:
PyTorch/torchvision:
CUDA/GPU:
Kết quả 01_setup.bat:
Kết quả pip check:
Kết quả tests:
Bằng chứng: logs/setup.log, logs/installed_versions.txt và output test.
Vấn đề còn lại:
```

---

## 3. Chuẩn bị model, preprocessing và dữ liệu ca

### Mục tiêu

Bảo đảm checkpoint, kiến trúc, processor, transform, config, ảnh và metadata khớp
với nhau trước khi suy luận.

### Tệp bắt buộc

- `model/best_model.pt`: checkpoint chính, khoảng 138 MB.
- `model/config.json`: cấu hình model.
- `model/metadata_processor.joblib`: processor cho 22 trường metadata.
- `model/val_transform.json`: transform validation.
- `model_definition.py`: kiến trúc `HierarchicalSwinCrossAttnLocalHeads`.
- `inference.py`: loader và predictor.
- `test_images/IMG000001.jpg` đến `IMG000003.jpg`.
- `cases.json`: danh sách ca và metadata.

### 22 trường metadata

`age`, `gender`, `hand`, `ulna`, `radius`, `humerus`, `foot`, `tibia`, `fibula`,
`femur`, `hip bone`, `ankle-joint`, `knee-joint`, `hip-joint`, `elbow-joint`,
`shoulder-joint`, `upper limb`, `lower limb`, `pelvis`, `frontal`, `lateral`,
`oblique`.

- `age` phải là số.
- `gender` phải là `M` hoặc `F`.
- 20 trường còn lại phải giữ đúng 0/1 từ dữ liệu nguồn.
- Không suy ra metadata từ tên file hoặc hình ảnh.
- `true_label` là nhãn tham chiếu, không gửi vào model như input.
- `expected_top1` và `expected_scores` chỉ là giá trị đối chiếu nếu có.

### 10 lớp đầu ra

1. `no-tumor`
2. `osteochondroma`
3. `multiple osteochondromas`
4. `simple bone cyst`
5. `giant cell tumor`
6. `osteofibroma`
7. `synovial osteochondroma`
8. `other bt`
9. `osteosarcoma`
10. `other mt`

### Tiêu chí nghiệm thu

- Checkpoint mở được với `weights_only=False` chỉ khi tệp đáng tin cậy.
- Model khởi tạo đúng config và strict state loading.
- Số trường metadata, tên trường và tên lớp khớp.
- Mỗi ảnh được gắn đúng metadata.
- Không sửa preprocessing chỉ để vượt qua lỗi.

### Completion Note — Giai đoạn 3

```text
[COMPLETION NOTE — GĐ3]
Ngày/giờ:
Checkpoint/config/processor/transform:
SHA256 các tệp quan trọng:
Số ảnh và mapping ảnh-ca:
Số trường metadata:
Danh sách lớp:
Đã xác nhận strict loading/preprocessing: Có/Không
Bằng chứng:
Rủi ro hoặc dữ liệu chưa xác minh:
```

---

## 4. Chạy kiểm tra model offline

### Mục tiêu

Đo khả năng nạp model, tính nhất quán kết quả, tài nguyên và thời gian suy luận;
không gọi API, không training lại, không sửa trọng số.

### GPU

```bat
02_run_check.bat
```

Mặc định script gọi:

```text
check_model.py --device auto
```

Chương trình kiểm tra input, tính SHA256, nạp model, kiểm tra config/metadata, chạy
warm-up một lần rồi đo ba lần cho từng ảnh. Batch suy luận là 1. Thời gian đo gồm
đọc ảnh, preprocessing và predict nhưng không gồm thời gian nạp model.

### CPU fallback

```bat
03_run_cpu.bat
```

Chỉ dùng CPU khi cần so sánh hoặc GPU không khả dụng. Không dùng CPU để kết luận
GPU không tương thích nếu chưa đọc log.

### Đọc kết quả

Mỗi lượt tạo thư mục mới trong `results/`:

- `report.json`: môi trường, SHA256, kết quả, timing, RAM/VRAM, lỗi.
- `predictions.csv`: bảng tóm tắt nếu chạy đến bước dự đoán.
- `run_log.txt`: log ngắn.
- `logs/last_run_console.txt`: output console gần nhất.

### Ý nghĩa trạng thái

- `TECHNICAL_CHECK_PASSED`: model nạp được và kiểm tra kỹ thuật đạt.
- `repeat_pass`: kết quả lặp lại ổn định trong ngưỡng.
- `notebook_comparison: NOT_PROVIDED`: chưa có notebook parity.
- `TOP1_ONLY`: mới đối chiếu nhãn Top-1.
- `SCORES_CHECKED`: đã đối chiếu score với tolerance; không tự nới tolerance.
- `true_label` đúng không đồng nghĩa model đạt accuracy lâm sàng.

### Bằng chứng tham chiếu hiện có

Lượt chạy đã ghi nhận:

- Python 3.11.9, Windows 10, RTX 3050 Laptop 4 GB.
- `cuda_available: true`, PyTorch CUDA 12.4.
- `case_001`: Top-1 `other mt`, score khoảng 0.68349.
- `case_002`: Top-1 `osteosarcoma`, score khoảng 0.95007.
- `case_003`: Top-1 `osteosarcoma`, score khoảng 0.94649.
- Cả ba có `repeat_pass: true`.

Đây là kiểm tra kỹ thuật trên ba ca, không phải công bố accuracy dataset.

### Tiêu chí nghiệm thu

- `report.json` tồn tại và đọc được.
- Không có lỗi nạp model hoặc lỗi input.
- Có thông tin thiết bị, version và SHA256.
- Ba lượt đo lặp lại trong ngưỡng.
- Mọi sai khác với notebook phải được ghi là chưa xác minh, không tự bỏ qua.

### Completion Note — Giai đoạn 4

```text
[COMPLETION NOTE — GĐ4]
Ngày/giờ:
Thiết bị chạy:
Thư mục results:
Trạng thái report:
Kết quả từng ca (Top-1/true_label/repeat_pass):
Load time và median inference:
Notebook parity:
SHA256 đã lưu:
Bằng chứng:
Lỗi hoặc giới hạn:
```

---

## 5. Cài và xác minh FastAPI

### Mục tiêu

Đóng gói predictor thành API local, bảo toàn kết quả so với chạy offline.

### Cài dependency

Sau khi giai đoạn model đạt:

```bat
04_setup_api.bat
```

Script lưu trước/sau cài đặt, cài `requirements_api.txt`, chạy `pip check` và test
trong `api_tests/`.

### Khởi chạy API

```bat
05_start_api.bat
```

API lắng nghe `127.0.0.1:8000`, một worker, không `--reload`, nạp model một lần.
Swagger: `http://127.0.0.1:8000/docs`.

### Các endpoint cốt lõi

- `GET /health`: trạng thái sẵn sàng, device, model hash.
- `GET /metadata-schema`: 22 trường và danh sách lớp.
- `POST /predict`: multipart file + metadata JSON.
- `POST /cases`: lưu ca thông qua case router khi chạy UI app.
- `GET /cases`, `GET /cases/{id}`, `DELETE /cases/{id}`.
- `POST/GET /cases/{id}/comments`.
- `POST /cases/{id}/corrections`.
- `GET /dashboard/stats`.

### Ràng buộc API phải giữ

- Ảnh tối đa 30 MiB và 25 triệu pixel.
- Nhận JPEG/PNG/BMP/TIFF; giải mã ảnh thực tế, không tin MIME đơn thuần.
- Metadata phải đủ, không dư, không null và đúng kiểu.
- Ảnh hỏng: 415; input/metadata sai: 422; quá lớn: 413; bận: 429;
  model chưa sẵn sàng: 503.
- Ảnh tạm phải được dọn sau request thành công và thất bại.
- API chỉ local; không tự thêm auth hoặc public binding mà chưa có thiết kế.

### Xác minh parity

```bat
06_verify_api.bat
```

Script gửi các ca và ảnh hiện tại tới API, đối chiếu SHA256, metadata và score với
report offline. Kết quả phải đạt `API_LOCAL_PARITY_PASSED`, với sai lệch tối đa
`1e-4` và Top-1 khớp.

### Tiêu chí nghiệm thu

- `04_setup_api.bat` báo pass.
- `GET /health` trả trạng thái ready.
- `06_verify_api.bat` đạt parity.
- Kiểm tra lỗi thiếu metadata và ảnh hỏng trả đúng status.
- Không còn file tạm rác sau request.

### Completion Note — Giai đoạn 5

```text
[COMPLETION NOTE — GĐ5]
Ngày/giờ:
API commit/version:
Kết quả setup API:
Kết quả unit/API tests:
Health response:
Parity status:
HTTP negative tests:
Bằng chứng: logs/api_setup.log, api_results/<timestamp>/.
Lỗi/giới hạn:
```

---

## 6. Chạy giao diện web local

### Mục tiêu

Cho người dùng chọn ảnh, nạp metadata, gửi dự đoán và đọc kết quả mà không mở
`index.html` trực tiếp từ file system.

### Khởi chạy

Không chạy đồng thời `05_start_api.bat` và `07_start_ui.bat` vì cùng dùng cổng 8000.
Dừng API cũ bằng `Ctrl+C`, sau đó:

```bat
07_start_ui.bat
```

Mở `http://127.0.0.1:8000/`.

### Luồng sử dụng

1. Nạp `cases.json` hoặc object metadata đúng ca.
2. Chọn case.
3. Chọn đúng ảnh tương ứng.
4. Xác nhận ảnh và metadata cùng ca.
5. Bấm phân tích.
6. Kiểm tra Top-1, Top-3, bảng 10 lớp, device và thời gian.
7. Có thể tải JSON kết quả.
8. Khi đổi ảnh/ca, kết quả cũ và xác nhận cũ phải bị xóa.

### Kiểm thử UI

`07_start_ui.bat` chạy route tests trong `ui_tests/` trước khi khởi động uvicorn.
UI phải xử lý mất kết nối, HTTP 429, thiếu trường, chọn nhầm ảnh/ca và trạng thái
đang xử lý mà không hiển thị dự đoán giả.

### Tiêu chí nghiệm thu

- Route `/`, `/history`, `/dashboard`, `/case/{id}` trả đúng HTML.
- Ba ca mẫu gửi được đến API thật.
- Kết quả hiển thị khớp API, không có dữ liệu hard-code.
- UI không gửi `true_label` vào predictor.
- Không dùng CDN hoặc API key cho luồng local hiện tại.
- Độ rộng mobile khoảng 390 px không bị tràn ngang.

### Completion Note — Giai đoạn 6

```text
[COMPLETION NOTE — GĐ6]
Ngày/giờ:
URL đã kiểm tra:
Kết quả route tests:
Ca đã thử:
Top-1/Top-3 đã đối chiếu:
Negative UI tests:
Desktop/mobile:
Bằng chứng: console output, ảnh chụp hoặc file JSON tải xuống.
Vấn đề còn lại:
```

---

## 7. Hoàn thiện SQLite và quản lý ca

### Mục tiêu

Lưu lịch sử phân tích cục bộ, nhận xét và hiệu chỉnh có thể truy xuất nhưng không
ghi đè dự đoán gốc.

### Schema và nguyên tắc

`database.py` sử dụng `data/bonescope.db`, SQLite WAL và foreign keys. Các nhóm dữ
liệu chính:

- `cases`: filename, hash ảnh, metadata, scores, top1, timing, device, model hash,
  API version và true label.
- `comments`: nội dung nhận xét theo case.
- `corrections`: nhãn hiệu chỉnh và lý do, độc lập với output model.

Database được khởi tạo khi `xray_ui.py` import app. Runtime DB không commit vào Git.

### Luồng phải kiểm tra

1. Lưu một prediction thành case.
2. Liệt kê cases có pagination và lọc label.
3. Mở chi tiết case, gồm comments/corrections.
4. Thêm và đọc comment.
5. Thêm correction với label hợp lệ.
6. Từ chối label correction không hợp lệ.
7. Xóa case và xác nhận dữ liệu con được xử lý theo schema.
8. Đọc dashboard stats.

### Tiêu chí nghiệm thu

- `api_tests/test_case_api.py` đạt.
- Dự đoán gốc không bị thay đổi sau correction.
- Case không tồn tại trả 404.
- `limit` 1–200, `offset` không âm.
- Nội dung comment/correction có giới hạn độ dài.
- Database tự tạo được trong thư mục `data/`.

### Completion Note — Giai đoạn 7

```text
[COMPLETION NOTE — GĐ7]
Ngày/giờ:
Database path:
Schema/tables:
CRUD case:
Comments:
Corrections:
Dashboard:
Kết quả api_tests/test_case_api.py:
Bằng chứng:
```

---

## 8. Chạy toàn bộ kiểm thử và kiểm tra hồi quy

### Mục tiêu

Đảm bảo thay đổi mới không phá inference, API, case management hoặc UI.

### Bộ lệnh kiểm thử

```powershell
.\.venv\Scripts\Activate.ps1
python -m unittest discover -s tests -v
python -m unittest discover -s api_tests -v
python -m unittest discover -s ui_tests -v
python -m compileall -q .
```

Không đưa `.venv`, `data`, `logs`, `results` vào compile/test thủ công nếu không cần.

### Kiểm tra bổ sung

- `git diff --check`.
- `git status --short`.
- `git check-ignore` cho `.venv`, database, log, kết quả.
- Kiểm tra mọi endpoint có lỗi rõ ràng, không catch rộng rồi trả thành công giả.
- Nếu sửa model/inference, chạy lại giai đoạn 4 và 5; không chỉ chạy unit tests.

### Tiêu chí nghiệm thu

- Tất cả test suites đạt.
- Không có syntax error.
- Không có file runtime bị stage ngoài ý muốn.
- Có log test và commit hash.

### Completion Note — Giai đoạn 8

```text
[COMPLETION NOTE — GĐ8]
Ngày/giờ:
Test command:
Kết quả tests:
Compile/syntax:
git diff --check:
Kiểm tra ignore:
Regression risk:
Bằng chứng:
```

---

## 9. Xác minh Git, Git LFS và bàn giao phiên bản

### Mục tiêu

Bảo đảm source code và model có thể được clone lại, nhưng không đưa runtime artifact
hoặc secret vào repository.

### Quy trình

1. Đọc `git status`.
2. Kiểm tra remote và branch.
3. Kiểm tra `model/*.pt` được Git LFS track qua `.gitattributes`.
4. Không commit `.venv`, `data/*.db`, logs, results, API keys.
5. Ghi commit có nội dung ngắn, rõ.
6. Push branch `main`.
7. Clone thử vào thư mục tạm nếu cần; chạy LFS pull và đọc README.
8. Ghi link commit/repository vào Completion Note.

### Tiêu chí nghiệm thu

- `git lfs ls-files` hiển thị `model/best_model.pt`.
- `git status` sạch sau push.
- Remote branch trỏ đúng commit.
- README hướng dẫn đúng với các batch file hiện tại.

### Completion Note — Giai đoạn 9

```text
[COMPLETION NOTE — GĐ9]
Ngày/giờ:
Branch/commit:
Remote:
Git LFS model:
Files excluded:
Clone/pull verification:
Repository URL:
```

---

## 10. Xây kho tài liệu y khoa cho RAG (giai đoạn tiếp theo)

> Giai đoạn này **chưa được coi là hoàn thành** trong bản hiện tại.

### Mục tiêu

Tạo tập tài liệu đáng tin cậy về u xương, phân loại, dấu hiệu hình ảnh, giới hạn
chẩn đoán và hướng dẫn chuyển tuyến; không biến chatbot thành công cụ tự chẩn đoán.

### Quy trình đề xuất

1. Xác định nguồn được phép sử dụng và giấy phép.
2. Thu thập 10–20 tài liệu có tác giả, năm, URL/DOI hoặc mã nguồn.
3. Lưu metadata nguồn: title, authors, publisher, date, license, URL, checksum.
4. Chuyển tài liệu sang text có kiểm soát; giữ bảng và chú thích quan trọng.
5. Chia chunk theo tiêu đề/ngữ nghĩa, không cắt giữa điều kiện lâm sàng.
6. Gắn `source_id`, trang/section, thời điểm truy xuất và phiên bản chunk.
7. Tạo bộ câu hỏi kiểm thử có đáp án và nguồn mong đợi.
8. Không đưa dữ liệu bệnh nhân thật vào kho tài liệu.

### Tiêu chí nghiệm thu

- Mỗi chunk truy ngược được về tài liệu và vị trí.
- Không có nguồn không rõ xuất xứ.
- Có bộ câu hỏi kiểm tra citation/faithfulness.
- Có chính sách cập nhật và loại bỏ tài liệu cũ.

### Completion Note — Giai đoạn 10

```text
[COMPLETION NOTE — GĐ10]
Ngày/giờ:
Số tài liệu:
Nguồn/giấy phép:
Pipeline trích xuất/chunk:
Metadata/citation:
Bộ câu hỏi kiểm thử:
Rủi ro pháp lý/y khoa:
Trạng thái: PASS / BLOCKED
```

---

## 11. Embeddings và chỉ mục vector

> Giai đoạn này **chưa được coi là hoàn thành** trong bản hiện tại.

### Mục tiêu

Cho phép tìm các đoạn tài liệu liên quan theo câu hỏi tiếng Việt/Anh mà vẫn bảo toàn
nguồn trích dẫn.

### Thiết kế cần chốt trước khi code

- Model embedding chạy local hay dịch vụ ngoài.
- Kích thước vector, model version và checksum.
- Vector store local, format persistence và backup.
- Top-k, similarity threshold, filter theo nguồn/phiên bản.
- Cách xử lý truy vấn không có bằng chứng phù hợp.
- Chi phí và rủi ro gửi dữ liệu ra ngoài.

### Quy trình

1. Chuẩn hóa chunk và metadata.
2. Tạo embedding deterministic theo phiên bản model.
3. Lưu vector cùng chunk ID, source ID và model version.
4. Build index từ đầu có thể lặp lại.
5. Viết retrieval evaluator: recall@k, MRR hoặc metric phù hợp.
6. Test câu hỏi dễ, khó, mơ hồ và ngoài phạm vi.
7. Từ chối hoặc trả lời “không đủ nguồn” khi similarity thấp.

### Completion Note — Giai đoạn 11

```text
[COMPLETION NOTE — GĐ11]
Ngày/giờ:
Embedding model/version:
Vector store:
Index version/checksum:
Top-k/threshold:
Kết quả retrieval evaluation:
Truy xuất citation có thể tái lập: Có/Không
Vấn đề:
```

---

## 12. Chatbot tiếng Việt có RAG và citation

> Giai đoạn này **chưa được coi là hoàn thành** trong bản hiện tại.

### Mục tiêu

Trả lời câu hỏi bằng tiếng Việt dựa trên các đoạn đã truy xuất, luôn hiển thị nguồn
và phân biệt rõ hỗ trợ nghiên cứu với chẩn đoán y khoa.

### Luồng xử lý

1. Nhận câu hỏi.
2. Kiểm tra prompt injection và nội dung nhạy cảm.
3. Xác định câu hỏi có liên quan phạm vi u xương hay không.
4. Retrieve chunks.
5. Nếu không đủ bằng chứng, từ chối khẳng định và yêu cầu nguồn/bác sĩ.
6. Sinh câu trả lời chỉ dựa trên context đã truy xuất.
7. Gắn citation tới source/section/page.
8. Ghi log tối thiểu, không lưu dữ liệu bệnh nhân nếu không cần.
9. Trả disclaimer phù hợp; không đưa ra phác đồ cá nhân hóa.

### Kiểm thử bắt buộc

- Câu hỏi có nguồn rõ.
- Câu hỏi không có nguồn.
- Câu hỏi ngoài phạm vi.
- Prompt injection.
- Câu hỏi yêu cầu chẩn đoán chắc chắn.
- Câu hỏi chứa thông tin định danh bệnh nhân.
- Citation sai hoặc thiếu.

### Tiêu chí nghiệm thu

- Citation không được bịa.
- Câu trả lời không khẳng định chẩn đoán chỉ từ một ảnh/model score.
- Có fallback rõ ràng khi retrieval thấp.
- Có test regression cho prompt injection và privacy.

### Completion Note — Giai đoạn 12

```text
[COMPLETION NOTE — GĐ12]
Ngày/giờ:
LLM/provider:
RAG index:
Citation tests:
Safety/privacy tests:
Out-of-scope fallback:
Đánh giá của người có chuyên môn:
Trạng thái: PASS / BLOCKED
```

---

## 13. Đánh giá toàn diện, bảo mật và đóng gói cuối

### Mục tiêu

Chuyển từ bản demo local sang bản bàn giao có bằng chứng, giới hạn và hướng dẫn rõ.

### Đánh giá model

- Xác minh notebook parity trên cùng checkpoint, preprocessing và metadata.
- Tạo train/validation/test split rõ ràng, tránh leakage.
- Báo cáo accuracy, macro-F1, balanced accuracy, confusion matrix, Top-k và calibration
  nếu phù hợp.
- Phân tích theo lớp, giới tính, tuổi, vị trí và hướng chụp khi dữ liệu cho phép.
- Không dùng 3 ảnh mẫu làm benchmark đại diện.

### Bảo mật API

Nếu triển khai ngoài máy cá nhân, phải thiết kế lại trước khi public:

- authentication/authorization;
- giới hạn request body trước parser;
- rate limiting;
- CORS và trusted hosts;
- quản lý secret;
- audit log không lộ dữ liệu;
- xóa file tạm;
- phân quyền database;
- TLS/reverse proxy;
- backup và khôi phục.

### Đóng gói

1. Chốt version source/model/index.
2. Chạy clean install trên máy hoặc thư mục mới.
3. Chạy đầy đủ test và smoke test.
4. Tạo release note với known limitations.
5. Cập nhật README tiếng Việt/Anh.
6. Bàn giao report, log nghiệm thu, checksum và hướng dẫn khôi phục.

### Completion Note — Giai đoạn 13

```text
[COMPLETION NOTE — GĐ13]
Ngày/giờ:
Model evaluation:
Notebook parity:
Security review:
Clean-install verification:
Release/source/model/index version:
Known limitations:
Tài liệu bàn giao:
Người duyệt:
Trạng thái phát hành: PASS / BLOCKED
```

---

## Phụ lục A — Checklist nhanh cho AI tiếp quản

### Trước khi sửa code

- [ ] Đọc file này và README liên quan.
- [ ] Xác định đang ở giai đoạn nào.
- [ ] Đọc test hiện có trước khi sửa.
- [ ] Ghi baseline test nếu thay đổi behavior.
- [ ] Không sửa checkpoint hoặc nới validation để né lỗi.

### Sau khi sửa code

- [ ] Chạy test nhỏ nhất bao phủ thay đổi.
- [ ] Nếu sửa inference/model: chạy lại offline check và API parity.
- [ ] Kiểm tra lỗi rõ ràng, không fallback thành công giả.
- [ ] Kiểm tra file runtime/secret không bị stage.
- [ ] Cập nhật tài liệu liên quan.
- [ ] Ghi Completion Note của giai đoạn.

### Khi gặp lỗi

1. Ghi lệnh, môi trường, traceback và file log.
2. Phân loại lỗi: môi trường, input, model, API, UI, database hay dữ liệu.
3. Không xóa log hoặc kết quả cũ trước khi sao lưu bằng chứng.
4. Thử phương án ít thay đổi nhất.
5. Nếu không đủ thông tin, đánh dấu `BLOCKED` và nêu chính xác dữ liệu cần bổ sung.

## Phụ lục B — Mẫu note tối giản dùng trong commit/issue

```text
[COMPLETION NOTE — GĐX]
- Ngày/giờ:
- Phạm vi:
- Lệnh đã chạy:
- Kết quả:
- Bằng chứng:
- Thay đổi source:
- Giới hạn/known issue:
- Quyết định tiếp theo:
```

