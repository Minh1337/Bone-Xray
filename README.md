# 🦴 BoneScope · Hệ Thống Hỗ Trợ Phân Tích X-Quang U Xương

> **Đồ án hệ thống hội thoại hỗ trợ phân tích ảnh X-quang u xương kết hợp mô hình học sâu và RAG.**  
> Thiết kế để chạy hoàn toàn cục bộ (offline/local) trên Windows 10/11, hỗ trợ tăng tốc GPU (NVIDIA RTX/CUDA) hoặc CPU.

---

## 📁 Cấu Trúc Dự Án (Đã Tinh Gọn & Chuẩn Hóa)

```
Bone_Xray_Local_Check/
├── .vscode/                 # Cấu hình môi trường & Debug trong VSCode
│   ├── launch.json          # 3 profile chạy (F5): UI+API, Chỉ API, Check Model
│   └── settings.json        # Tự động chọn venv Python 3.11
├── docs/                    # Tài liệu đặc tả & báo cáo dự án
│   ├── README_VI.md         # Hướng dẫn kiểm tra mô hình ban đầu
│   ├── README_FASTAPI_VI.md # Tài liệu API FastAPI
│   ├── README_UI_VI.md      # Tài liệu giao diện web
│   ├── LO_TRINH_THUC_HIEN_DU_AN_AI.md # Runbook chi tiết cho AI tiếp quản
│   ├── Bao_cao_tien_do.docx # Báo cáo tiến độ theo chương
│   └── Tai_lieu_phat_trien_du_an.docx # Tài liệu roadmap & lộ trình 4 tuần
├── tools/                   # Bộ công cụ & installer
│   └── python-3.11.9-amd64.exe # Bộ cài Python 3.11 64-bit
├── data/                    # Cơ sở dữ liệu ứng dụng
│   └── bonescope.db         # SQLite CSDL: lưu ca, nhận xét, hiệu chỉnh nhãn
├── model/                   # Trọng số & cấu hình mô hình Deep Learning
│   ├── best_model.pt        # Trọng số Swin + Cross-Attention (138 MB)
│   ├── config.json          # Tham số cấu hình mô hình
│   ├── metadata_processor.joblib # Bộ tiền xử lý 22 trường metadata
│   └── val_transform.json   # Cấu hình biến đổi ảnh Albumentations
├── test_images/             # Ảnh X-quang mẫu thử nghiệm (IMG000001 -> 03)
├── xray_web/                # Giao diện web ứng dụng BoneScope
│   ├── index.html           # Trang phân tích ảnh & nhập thông tin
│   ├── history.html         # Trang lịch sử ca đã lưu
│   ├── dashboard.html       # Trang thống kê & dashboard hiệu năng
│   ├── case_detail.html     # Trang chi tiết ca, nhận xét & hiệu chỉnh
│   ├── app.js               # Logic điều khiển frontend
│   └── style.css            # Giao diện y tế hiện đại
├── tests/                   # Kiểm thử logic xác thực metadata & ảnh
├── api_tests/               # Kiểm thử API endpoints (/predict, /cases, /dashboard)
├── ui_tests/                # Kiểm thử UI routes & tích hợp
├── logs/                    # Nhật ký hoạt động hệ thống
├── results/                 # Kết quả các đợt chạy kiểm tra offline
├── api_results/             # Kết quả xác minh tính toàn vẹn API
│
├── xray_ui.py               # Main Web Entrypoint (kết nối API + UI + Database)
├── xray_api.py              # Core FastAPI app (suy luận mô hình)
├── case_api.py              # API quản lý ca bệnh, nhận xét, hiệu chỉnh
├── database.py              # Module quản lý CSDL SQLite
├── inference.py             # Pipeline nạp mô hình & suy luận
├── model_definition.py      # Kiến trúc mạng Swin + Cross-Attention
├── validation.py            # Quy tắc kiểm tra tính hợp lệ dữ liệu
├── check_model.py           # Script kiểm tra môi trường & tính toán SHA256
├── cases.json               # Dữ liệu 3 ca mẫu chuẩn
├── requirements.txt         # Thư viện Python cho mô hình (torch, timm, ...)
└── requirements_api.txt     # Thư viện cho API (fastapi, uvicorn, ...)
```

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
*(Hiện tại 100% các bài test đều PASS).*

---

## 🗺️ Lộ Trình Phát Triển Tiếp Theo (Theo Tài Liệu Dự Án)

- [x] **Bước 1 — 4:** Kiểm kê mô hình, kiểm tra suy luận độc lập, API phân loại 10 lớp.
- [x] **Bước 5:** Quản lý ca bệnh, CSDL SQLite, Lịch sử, Nhận xét, Hiệu chỉnh & Dashboard.
- [ ] **Bước 6:** Xây dựng kho tài liệu y khoa u xương (10–20 tài liệu chuẩn, chia đoạn chunk).
- [ ] **Bước 7:** Hệ thống nhúng (Embeddings) & Chỉ mục vector tìm kiếm ngữ nghĩa RAG.
- [ ] **Bước 8:** Chatbot hội thoại thông minh tiếng Việt có trích dẫn nguồn tài liệu.
- [ ] **Bước 9 — 11:** Đánh giá toàn diện, tài liệu bàn giao & slide báo cáo bảo vệ đồ án.
