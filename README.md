# 🦴 BoneScope · Hệ Thống Hỗ Trợ Phân Tích X-Quang U Xương

> **Đồ án hệ thống hội thoại hỗ trợ phân tích ảnh X-quang u xương kết hợp mô hình học sâu và RAG.**  
> Thiết kế để chạy hoàn toàn cục bộ (offline/local) trên Windows 10/11, hỗ trợ tăng tốc GPU (NVIDIA RTX/CUDA) hoặc CPU.

---

## 📁 Cấu Trúc Dự Án (Đã Cập Nhật)

```
BONESCOPE/
├── .vscode/                 # Cấu hình chạy và debug trong VS Code
├── docs/                    # Roadmap, hướng dẫn, trạng thái và báo cáo
│   ├── PROJECT_STATUS_VI.md # Trạng thái và bằng chứng kiểm thử mới nhất
│   ├── STAGE11_HANDOFF_VI.md # Điểm bàn giao RAG giai đoạn 11
│   ├── guides/              # Hướng dẫn model, API, UI và RAG
│   ├── reference/           # Thiết kế và báo cáo đánh giá RAG/API
│   └── reports/             # Báo cáo Word
├── model/                   # Trọng số và cấu hình model
│   ├── best_model.pt        # Trọng số Swin + Cross-Attention
│   ├── config.json          # Tham số cấu hình model
│   ├── metadata_processor.joblib
│   └── val_transform.json
├── tools/                   # Công cụ cục bộ/installer (Git bỏ qua)
├── rag/                     # Corpus, retrieval và đánh giá RAG cục bộ
│   ├── data/                # Corpus, nguồn, gold evaluation và config
│   ├── build_corpus.py      # Tạo corpus từ các nguồn
│   ├── build_index.py       # Tạo embedding và vector index
│   ├── retrieval.py         # Hybrid retrieval và routing
│   ├── evaluate.py          # Đánh giá recall/MRR và câu ngoài phạm vi
│   ├── lexical.py           # Từ khóa, BM25 và hợp nhất thứ hạng
│   ├── policy.py            # Chính sách phạm vi và đủ nguồn
│   ├── evidence.py          # Thử nghiệm xếp hạng/độ phủ bằng chứng
│   ├── compare*.py          # Runner so sánh và báo cáo đánh giá
│   ├── tests/               # Kiểm thử corpus, retrieval và evidence
│   ├── index/               # Index tạo tại máy (Git bỏ qua)
│   ├── models/              # Model embedding (Git bỏ qua)
│   └── source_cache/        # HTML nguồn tải tại máy (Git bỏ qua)
├── xray_web/                # Frontend HTML/CSS/JavaScript
│   ├── index.html           # Phân tích ảnh và metadata
│   ├── history.html         # Lịch sử ca SQLite
│   ├── dashboard.html       # Thống kê và hiệu năng
│   ├── case_detail.html     # Chi tiết, nhận xét và hiệu chỉnh
│   ├── app.js               # Logic frontend
│   └── style.css            # Giao diện
├── tests/                   # Test validation và inference
├── api_tests/               # Test API và quản lý ca
├── ui_tests/                # Test route/UI
├── data/                    # SQLite runtime (Git bỏ qua)
├── logs/                    # Log runtime (Git bỏ qua)
├── results/                 # Kết quả offline (Git bỏ qua)
├── api_results/             # Kết quả verify API (Git bỏ qua)
├── test_images/             # Ảnh X-quang mẫu
├── 01_setup.bat             # Tạo venv và cài dependency model
├── 04_setup_api.bat         # Cài dependency FastAPI
├── 05_start_api.bat         # Chạy API tại cổng 8000
├── 06_verify_api.bat        # Kiểm tra API với model thật
├── 07_start_ui.bat          # Chạy UI và API
├── xray_ui.py               # Entrypoint UI + API + database
├── xray_api.py              # FastAPI suy luận model
├── case_api.py              # Endpoint ca, nhận xét, hiệu chỉnh
├── database.py              # SQLite và schema
├── inference.py             # Pipeline nạp model và suy luận
├── model_definition.py      # Kiến trúc Swin + Cross-Attention
├── validation.py            # Kiểm tra input và score
├── check_model.py           # Kiểm tra môi trường/model
├── verify_api.py             # Verify API parity
├── cases.json               # Metadata các ca mẫu
├── metadata_example.json     # Metadata mẫu cho API
├── requirements*.txt        # Dependency model, API và RAG
└── README*.md               # Hướng dẫn tổng quan tiếng Anh/Việt
```

Các thư mục đánh dấu **Git bỏ qua** sẽ được tạo lại sau khi cài đặt hoặc chạy
ứng dụng. Database và log không được chia sẻ tự động giữa các máy.

---

## 🚀 Hướng Dẫn Khởi Chạy

### Cách 1 — Chạy trong VSCode (Khuyến nghị khi phát triển)
1. Mở thư mục dự án bằng **VSCode**.
2. Nhấn phím **`F5`** (hoặc mở tab *Run and Debug* bên trái).
3. Chọn cấu hình: **`🌐 BoneScope: API + UI (dev)`**.
4. Mở trình duyệt web truy cập: **`http://127.0.0.1:8000/`**.

> **Mẹo:** Chế độ này có sẵn tính năng `--reload`, mỗi khi bạn sửa code HTML/CSS/Python, server sẽ tự động cập nhật ngay lập tức.

### Cách 2 — Chạy nhanh bằng file Batch (`.bat`)
- Nhấp đúp vào **`07_start_ui.bat`** để khởi chạy toàn bộ hệ thống.
- Khi màn hình hiện `Uvicorn running on http://127.0.0.1:8000`, mở trình duyệt để sử dụng.
- Dừng ứng dụng bằng tổ hợp phím **`Ctrl + C`**.

---

## 🌟 Các Tính Năng Hiện Có

1. **Phân tích X-quang u xương 10 lớp:**
   - Hỗ trợ tải ảnh định dạng JPG, PNG, BMP, TIFF (tối đa 30 MiB).
   - Kiểm tra chặt chẽ 22 trường metadata (tuổi, giới tính, 17 vị trí xương/khớp/chi, 3 hướng chụp).
   - Dự đoán Top-1, Top-3 và bảng điểm chi tiết cả 10 lớp u xương.

2. **Quản lý ca bệnh & Lưu trữ cục bộ (SQLite):**
   - Lưu trữ tức thì ca vừa phân tích với đầy đủ metadata, kết quả và mã băm SHA256.
   - Trang **Lịch sử** (`/history`): Tìm kiếm, lọc theo nhãn, xem lại kết quả cũ.
   - Trang **Chi tiết ca** (`/case/{id}`): Xem toàn diện ca bệnh.

3. **Ghi chú & Hiệu chỉnh chuyên gia:**
   - Cho phép thêm nhận xét lâm sàng cho từng ca.
   - Hiệu chỉnh nhãn độc lập: **Lưu riêng biệt, không ghi đè dự đoán gốc của mô hình** (đúng theo tài liệu đặc tả dự án).

4. **Dashboard thống kê thời gian thực (`/dashboard`):**
   - Tổng hợp số ca, phân bố các loại u xương đã phát hiện.
   - Thống kê tỷ lệ ca có hiệu chỉnh / nhận xét.
   - Đo lường tốc độ suy luận trung bình và thiết bị phần cứng (GPU/CPU).

---

## 🧪 Kiểm Thử Hệ Thống (Unit Tests)

Chạy tất cả bài kiểm tra tự động để đảm bảo hệ thống hoạt động chính xác:

```powershell
# Kích hoạt môi trường ảo
.\.venv\Scripts\Activate.ps1

# Kiểm tra dữ liệu đầu vào
python -m unittest discover -s tests -v

# Kiểm tra API & CSDL
python -m unittest discover -s api_tests -v

# Kiểm tra UI & Web Routes
python -m unittest discover -s ui_tests -v
```
Lệnh kiểm thử hiện tại:

```powershell
.\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q
```

Lần chạy ngày 27/10/2026 đạt **36 passed, 28 subtests passed** (một cảnh báo deprecated của Starlette).

---

## 📊 Tiến Độ Dự Án — Cập nhật 27/10/2026

### Đã hoàn thành

- Hoàn thiện pipeline phân tích ảnh X-quang 10 lớp bằng model cục bộ.
- Hoàn thiện API FastAPI, giao diện web, quản lý ca SQLite, lịch sử, nhận xét,
  hiệu chỉnh nhãn độc lập và dashboard.
- Hoàn thiện kho RAG gồm **13 nguồn (12 NCI và 1 CC BY 4.0) và 439 đoạn văn** có URL, section,
  thời điểm truy xuất và mã băm để truy vết citation.
- Hoàn thiện hybrid retrieval local, routing câu hỏi, đánh giá recall/MRR,
  concept rerank và các thử nghiệm kiểm tra evidence.
- Đồng bộ tài liệu cài đặt/chạy trên máy mới và cấu trúc repository.

### Kết quả kiểm thử gần nhất

- Toàn bộ test (27/10/2026): **36 passed, 28 subtests passed**.
- API parity với baseline local trên model thật: **3/3 ca đạt**, sai lệch score tối đa 0; metadata thiếu/ảnh hỏng bị từ chối đúng. Notebook parity chưa được xác minh.
- Hybrid retrieval mặc định: **8/10** câu regression đúng nguồn/mục,
  **6/8** câu V2 dev và **7/8** câu V2 test đúng đoạn.
- Concept rerank thử nghiệm: **10/10** câu regression, **8/8** V2 dev,
  **8/8** V2 test và **9/10** V3 stress đúng đoạn.
- `--verify-evidence` chưa đạt vì từ chối nhầm nhiều câu có đáp án; không bật
  mặc định.
- API parity với model thật đã đạt trên 3 ca; notebook parity chưa được xác minh.

### Trạng thái hiện tại

**Giai đoạn 11 đang tiếp tục, chưa nghiệm thu để dùng làm nền trả lời y khoa.**
RAG hiện chỉ cung cấp retrieval/evaluation CLI; chưa có chatbot, API chat hoặc
giao diện hội thoại. Các chế độ evidence vẫn trả `answer_ready: false`.

### Việc cần làm tiếp theo

1. Kiểm định retrieval/rerank trên tập dữ liệu độc lập và bổ sung nguồn cho các
   nhãn còn thiếu như `simple bone cyst`, `osteofibroma` và
   `synovial osteochondroma`.
2. Khởi động ứng dụng và chạy `06_verify_api.bat`/`verify_api.py` với model thật.
3. Chỉ bắt đầu giai đoạn 12 sau khi có cơ chế đủ bằng chứng, citation và từ chối
   an toàn; sau đó mới xây chatbot tiếng Việt local.
4. Đánh giá toàn diện, bảo mật và đóng gói bàn giao ở giai đoạn 13.

Xem chi tiết tại [PROJECT_STATUS_VI.md](docs/PROJECT_STATUS_VI.md) và
[STAGE11_HANDOFF_VI.md](docs/STAGE11_HANDOFF_VI.md).

---

## 🗺️ Lộ Trình Phát Triển Tiếp Theo (Theo Tài Liệu Dự Án)

- [x] **Bước 1 — 4:** Kiểm kê mô hình, kiểm tra suy luận độc lập, API phân loại 10 lớp.
- [x] **Bước 5:** Quản lý ca bệnh, CSDL SQLite, Lịch sử, Nhận xét, Hiệu chỉnh & Dashboard.
- [x] **Giai đoạn 10:** Kho nguồn NCI và bộ câu hỏi tiếng Việt ban đầu.
- [ ] **Giai đoạn 11:** Đã có corpus 439 đoạn, hybrid retrieval v2, routing, rerank thử nghiệm và đánh giá evidence; chưa đạt để dùng làm nền trả lời y khoa.
- [x] **Giai đoạn 11A:** Đã tải và lập manifest BTXRD (3.746 ảnh, 10 lớp, 22 metadata, checksum và duplicate audit); do checkpoint hiện tại huấn luyện trên BTXRD nên chưa dùng làm kiểm định độc lập.
- [ ] **Giai đoạn 12:** Chatbot tiếng Việt có trích dẫn nguồn và kiểm thử an toàn.
- [ ] **Giai đoạn 13:** Đánh giá toàn diện, bảo mật và đóng gói bàn giao.

Kho nguồn RAG ban đầu gồm 12 trang NCI và bộ câu hỏi kiểm thử. Xem [hướng dẫn kho tài liệu](docs/guides/README_RAG_CORPUS_VI.md). Một số nhãn u lành tính còn thiếu nguồn chuyên biệt.

Để tiếp tục phát triển, đọc [trạng thái dự án và ghi chú bàn giao](docs/PROJECT_STATUS_VI.md) trước. Trang này tổng hợp các thay đổi đã làm, bằng chứng kiểm thử và việc còn mở.

Điểm tiếp tục hiện tại: [giai đoạn 11](docs/STAGE11_HANDOFF_VI.md). Từ vựng hybrid v2 đã giúp bộ dev riêng tìm 6/6 bằng chứng, nhưng chưa được kiểm định độc lập. Corpus hiện 439 đoạn; `answer_ready` vẫn luôn false. Chưa có chatbot.

Rerank thử nghiệm (`--rerank-concepts`) đạt 10/10 câu cũ, 8/8 trên V2 dev/test đã xem và 9/10 trên V3 stress; cần kiểm định độc lập. Bộ lọc `--verify-evidence` chặn nhầm nhiều câu có đáp án nên không bật mặc định. Cả hai chế độ vẫn trả `answer_ready: false`. Kết quả chi tiết và điểm tiếp tục nằm trong file bàn giao trên.

Tạo chỉ mục cục bộ: `python rag/build_index.py --download-model` (lần đầu), sau đó `python rag/build_index.py`; đo bằng `python rag/evaluate.py`. Xem [hướng dẫn truy xuất](docs/guides/README_RAG_INDEX_VI.md).

Khi lưu ca, API trả `prediction_id` sau `/predict`; giao diện gửi mã này tới `/cases` trong vòng 10 phút. Máy chủ lấy dữ liệu dự đoán đã giữ tạm và chỉ lưu một lần, tránh ghi điểm số do yêu cầu tự khai báo.
