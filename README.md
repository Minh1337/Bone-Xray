# 🦴 BoneScope · Hệ Thống Hỗ Trợ Phân Tích X-Quang U Xương

**Điểm tiếp quản Codex:** [START_HERE_NEXT_CODEX_VI.md](START_HERE_NEXT_CODEX_VI.md). Giai đoạn 11 đang tiếp tục theo yêu cầu sau ngày 29/10/2026; báo cáo, việc còn dở và bản sao lưu được ghi tại đó. Phạm vi hiện tại là **báo cáo học tập có tính thực nghiệm**, không cung cấp cho bác sĩ hoặc người bệnh.

> **Đồ án hệ thống hội thoại hỗ trợ phân tích ảnh X-quang u xương kết hợp mô hình học sâu và RAG.**  
> Suy luận ảnh (Swin + Cross-Attention Metadata) và truy xuất RAG chạy hoàn toàn cục bộ trên Windows 10/11 (GPU NVIDIA RTX/CUDA hoặc CPU); phần tạo bản nháp hội thoại kết nối tới Groq hoặc OpenAI (kèm cơ chế fallback mẫu máy chủ khi không có kết nối).

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
│   ├── conversation.py      # Routing hội thoại đa chủ đề và câu hỏi nối tiếp
│   ├── generation.py        # Transport Groq/OpenAI và tạo bản nháp
│   ├── demo_api.py          # API demo tra cứu/hội thoại local
│   ├── demo_web/             # Giao diện chatbot giáo dục
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
├── package.json              # Kiểm tra DESIGN.md bằng designmd
├── .env.example              # Mẫu cấu hình provider; không chứa secret
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

### Cách 3 — Chạy demo chatbot/RAG giáo dục

Demo chatbot dùng máy chủ FastAPI tại cổng `8765`, chỉ bind loopback. Trong
VS Code chọn cấu hình **`💬 BoneScope: Chatbot tra cứu tài liệu`** rồi bấm
**F5**, hoặc chạy:

```powershell
.\.venv\Scripts\python.exe -m uvicorn rag.demo_api:app --host 127.0.0.1 --port 8765
```

Mở `http://127.0.0.1:8765`. Không mở `rag\demo_web\index.html` bằng cách nhấp
đúp vì giao diện cần API. Muốn bật tạo bản nháp, sao chép `.env.example` thành
`.env` rồi điền key ở máy cá nhân; **không commit hoặc chia sẻ `.env`**. Mặc
định dùng Groq; có thể chọn OpenAI bằng `LLM_PROVIDER=openai`. Xem [hướng dẫn
chatbot](docs/guides/README_CHATBOT_UI_VI.md), [hướng dẫn hội thoại](docs/guides/CHATBOT_CONVERSATION_VI.md),
[thiết lập Groq](docs/guides/GROQ_CHATBOT_SETUP_VI.md) và [thiết lập OpenAI](docs/guides/OPENAI_CHATBOT_SETUP_VI.md).

Chatbot hỗ trợ hội thoại đa chủ đề, ngữ cảnh gần đây, chế độ **Trò chuyện +
tài liệu** và **Chỉ tra cứu tài liệu**, trích dẫn passage `[S1]`, `[S2]`, xuất
Markdown, sáng/tối và tạo cuộc trò chuyện mới. Lịch sử chỉ nằm trong bộ nhớ
tab; không có database hội thoại. Câu hỏi về xương vẫn phải qua retrieval cục
bộ. Câu trả lời từ model chỉ là **bản nháp chưa kiểm chứng**, không phải chẩn
đoán, không dùng cho ca bệnh/ảnh cá nhân và không phải bằng chứng nghiệm thu.

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

5. **Demo chatbot học tập local (kết hợp phân tích ca ảnh → RAG → hội thoại):**
   - Tra cứu 22 nguồn/794 đoạn với provenance, license và hash của passage.
   - Hỗ trợ nạp ảnh X-quang học tập kèm 22 trường metadata để chạy mô hình Swin + Cross-Attention cục bộ, đối chiếu bảng ánh xạ 10 nhãn (`rag/case_context.py`) sang kho nguồn, sinh giải thích học thuật có trích dẫn `[S1]`, `[S2]` và hỏi nối tiếp theo `case_id` do máy chủ quản lý.
   - Hội thoại đa chủ đề và hỏi nối tiếp; provider bản nháp là Groq hoặc OpenAI. Ảnh và metadata chỉ xử lý cục bộ; luôn trả `answer_ready: false`.

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

Regression phần mềm gần nhất của chatbot/API: **58 passed**, một cảnh báo
deprecation Starlette. Chạy riêng:

```powershell
.\.venv\Scripts\python.exe -m pytest rag/tests/test_demo_api.py rag/tests/test_generation.py rag/tests/test_conversation.py -q
node --check rag/demo_web/app.js
```

Đây là regression code/UI, không phải xác nhận lâm sàng, kiểm định chất lượng
retrieval hay kiểm định độc lập. Regression Giai đoạn 11 gần nhất được ghi
trong [run record với code/data hashes](docs/reference/stage11_test_run_20261029_postdocs_full.json);
corpus hiện tại là 22 nguồn/794 chunk, audit provenance PASS và deterministic
replay PASS 16/16. Chưa có reviewer-labeled blind set hoặc citation-entailment
adjudication; Giai đoạn 11 chưa nghiệm thu, `answer_ready=false`.

---

## 📊 Tiến Độ Dự Án — Cập nhật 29/10/2026

### Mốc hoàn thiện tích hợp P1–P7 — 03/11/2026

- Đã hoàn thiện toàn bộ 7 hạng mục kỹ thuật trong [báo cáo đối chiếu P1–P7](docs/reports/PROJECT_GAP_ASSESSMENT_20261031_VI.md):
  - **P1/P3/P4/P6:** Tích hợp luồng **Ảnh + 22 Metadata → Dự đoán Swin + Cross-Attention cục bộ → Ánh xạ 10 nhãn (`LABEL_GUIDE`) → Tra cứu nguồn RAG → Giải thích học thuật & Hội thoại nối tiếp** trong `rag/case_context.py`, `rag/demo_api.py` và `rag/demo_web/`. Đổi hoặc xóa ảnh tự động xóa ngữ cảnh ca cũ (`case_id` trong RAM).
  - **P2/P5:** Bổ sung `tools/evaluate_xray_checkpoint.py` và hồ sơ thực nghiệm nội nguồn + ablation 250 ảnh phân tầng ([`stage11_xray_in_source_evaluation_20261103.json`](docs/reference/stage11_xray_in_source_evaluation_20261103.json)): có metadata thật đạt **Top-1 = 0,7760, Top-3 = 0,9400, Macro-F1 = 0,7759** (trung vị **25,2 ms/ảnh** trên RTX 3050); khi xóa vector metadata về 0, **Top-1 giảm xuống 0,4800 và Macro-F1 giảm xuống 0,4389** (đổi nhãn Top-1 ở 91/250 ảnh). Ghi rõ giới hạn: đây là số liệu nội nguồn BTXRD và ablation, không phải kiểm định độc lập.
  - **Kiểm thử tự động:** Full suite đạt **162 passed / 132 subtests** (gồm cả test tích hợp thật `tests/test_end_to_end_pipeline.py`), audit PASS, replay **16/16 PASS**, register QA **PASS**, 7 acceptance gates giữ `OPEN` và `answer_ready=false`.

### Mốc đồng bộ repository — 02/11/2026

- Đã chuẩn bị đồng bộ toàn bộ source, tài liệu và artifact dữ liệu hợp lệ trong
  workspace lên nhánh `main`.
- Các snapshot/patch sinh tự động trong `checkpoints/` được giữ cục bộ và bỏ qua
  bởi Git vì có file ZIP khoảng 133 MiB, vượt giới hạn 100 MB/file của GitHub.
- Trạng thái kỹ thuật sau lần đồng bộ: chatbot/API regression **58 passed**,
  corpus **22 nguồn/794 chunk**, audit PASS, replay **16/16**, bảy acceptance
  gates còn OPEN và `answer_ready=false`.

### Đã hoàn thành

- Hoàn thiện pipeline phân tích ảnh X-quang 10 lớp bằng model cục bộ.
- Hoàn thiện API FastAPI, giao diện web, quản lý ca SQLite, lịch sử, nhận xét,
  hiệu chỉnh nhãn độc lập và dashboard.
- Mở rộng kho RAG lên **22 nguồn/794 đoạn**: 13 mục NCI và 9 nguồn ngoài NCI; provenance/license/scope được ghi theo nguồn. G4 đã sàng lọc 15 leads; C12–C15 chưa đủ điều kiện đánh giá ảnh. C15 IIEST là bộ hỗn hợp 217 ảnh với 69 cancer-labelled, chưa xác minh package/quyền/reference standard/overlap. Xem [cohort register](docs/reference/stage11_external_cohort_screening_register_20261029.csv), [C14 screen](docs/reference/stage11_frontiers_11case_cohort_screen_20261029.json) và [C15 screen](docs/reference/stage11_iiest_69case_cohort_screen_20261029.json).
  Mỗi chunk mang nguồn, license, scope, section và hash.
- Hoàn thiện hybrid retrieval local, routing câu hỏi, đánh giá recall/MRR,
  concept rerank và các thử nghiệm kiểm tra evidence.
- Thêm demo tra cứu tài liệu học tập local tại `rag/demo_api.py` và
  `rag/demo_web/`: chỉ bind loopback, có provenance/citation cho passage,
  từ chối câu hỏi ngoài phạm vi hoặc cần ảnh, không lưu lịch sử và không dùng
  để chẩn đoán.
- Thêm hội thoại đa chủ đề và hội thoại đa lượt trong `rag/conversation.py`,
  tầng Groq/OpenAI trong `rag/generation.py`, chế độ `auto`/`documents`,
  giới hạn lịch sử và deadline. Đây là transport/tạo bản nháp có kiểm soát,
  không phải answer generator đã nghiệm thu.
- Thêm giao diện chatbot responsive, xuất Markdown, nguồn có thể mở, theme
  sáng/tối, retry/stop/new conversation và tài liệu thiết lập provider. UI
  không gọi Gemini; provider hiện tại là Groq (mặc định) hoặc OpenAI.
- Đồng bộ tài liệu cài đặt/chạy trên máy mới và cấu trúc repository.

### Kết quả đo gần nhất và trạng thái kiểm thử

- Full suite mới nhất được ghi nhận: **92 passed/132 subtests**, một cảnh báo deprecation Starlette. Đây là regression phần mềm, không phải kiểm định retrieval độc lập hay lâm sàng. Xem [run record với code/data hashes](docs/reference/stage11_test_run_20261029_postdocs_full.json) và [record lịch sử](docs/reference/stage11_test_run_20261028.json).
- API parity với baseline local trên model thật: **3/3 ca đạt**, sai lệch score tối đa 0; metadata thiếu/ảnh hỏng bị từ chối đúng. Notebook parity chưa được xác minh.
- Audit integrity/provenance offline hiện tại: **PASS**, 22 nguồn/794 đoạn, index `794 × 384`; deterministic replay **16/16 PASS**. Đây không phải
  xác nhận y khoa hay citation entailment.
- Historical v8 expansion dev (22 dương/3 âm, agent-authored/đã xem) đạt Recall@5 22/22 trước corpus growth; không phải holdout. Corpus growth làm metric đổi trên một số report. Sau đó, ABC route được thử trên dev riêng đã xem: Recall@5 0.955→1.000, MRR 0.644→0.689, abstention âm 3/3; kết quả in-sample, xem [experiment record](docs/reference/stage11_cureus_abc_route_dev_experiment_20261029.json).
- Historical V2 regression đã xem đạt hybrid Recall@5 8/8, MRR 0.733 sau route chondrosarcoma đã chỉnh theo lỗi đã thấy; concept rerank cũng đạt 8/8, MRR 0.938. Các số này là lịch sử/in-sample; corpus growth sau đó làm một số V2 report đổi metric. Rerank vẫn opt-in vì dev giảm 22/22→19/22.
- Policy image-routing dev: abstain đúng lý do **51/51**; 16 false negative định tuyến ảnh cá nhân phát hiện qua nhiều vòng đã được sửa, 5/5 probe cá nhân mới abstain và 2/2 câu giáo dục đối chứng vẫn qua policy. Bộ tự soạn/in-sample, không đại diện; API retrieval chỉ nhận văn bản, chưa kiểm tra metadata hay pixel ảnh đính kèm. Xem [report và provenance](docs/reference/stage11_policy_rerun_20261029_personal_image_jats_wrapper_v7/image_routing_dev.json).
- Historical v8 `--verify-evidence` chưa đạt: abstain nhầm 21/22 câu dương trên dev và 8/8 trên
  V2 đã xem; negative abstention lần lượt 3/3 và 6/6. Không bật mặc định.

### Trạng thái hiện tại

**Giai đoạn 11 đang tiếp tục, chưa nghiệm thu để dùng làm nền trả lời y khoa.**
Đã có demo tra cứu tài liệu học tập local gồm API và giao diện chatbot đa lượt;
demo chỉ phục vụ research/education, không nhận ảnh hoặc ca bệnh, không lưu
lịch sử phía máy chủ và không thay thế đánh giá độc lập. Tầng sinh câu trả lời
Groq/OpenAI chỉ tạo bản nháp; các đường demo vẫn trả `answer_ready: false`.

### Việc cần làm tiếp theo

1. Người rà soát chuyên môn độc lập xác nhận answerability, acceptable evidence,
   span, citation entailment và ngưỡng pass; dùng [quy trình thẩm định](docs/reference/STAGE11_INDEPENDENT_REVIEW_PROTOCOL_VI.md).
2. Đóng băng một tập mù mới và đo false acceptance/refusal, retrieval, routing,
   citation và bất đồng reviewer; không tune trên kết quả mù.
3. Với kiểm định ảnh G4, chưa có cohort đủ điều kiện: register hiện có 15 leads, cần quyền ảnh/data-use, reference standard, manifest bệnh nhân/ảnh và audit overlap trước mọi external test. C12 TCIA sai modality/disease/endpoint; C13 Gitto chưa có ảnh trong Zenodo; C14 Frontiers thiếu nhóm âm và license; C15 IIEST là bộ ảnh hỗn hợp, chưa rõ package/quyền/reference standard/overlap. Không tải hoặc dùng chúng làm evaluation. Xem [cohort register](docs/reference/stage11_external_cohort_screening_register_20261029.csv), [C15 screen](docs/reference/stage11_iiest_69case_cohort_screen_20261029.json) và [due diligence](docs/reference/STAGE11_EXTERNAL_COHORT_DUE_DILIGENCE_VI.md).
4. Hoàn thiện kiểm thử tích hợp provider, xử lý quota/timeout và kiểm tra UI
   trong môi trường không có key; không ghi key hoặc dữ liệu người dùng vào
   log, report hay commit.
5. Chỉ xem xét giai đoạn 12 sau khi cổng evidence và rà soát độc lập được nghiệm thu.
6. Hoàn thành đánh giá toàn diện, bảo mật và đóng gói bàn giao ở giai đoạn 13.

Xem chi tiết tại [PROJECT_STATUS_VI.md](docs/PROJECT_STATUS_VI.md), [báo cáo Giai đoạn 11 ngày 29/10/2026](docs/reports/BAO_CAO_GIAI_DOAN_11_2026-10-29.md), [STAGE11_HANDOFF_VI.md](docs/STAGE11_HANDOFF_VI.md), [reviewer packet](docs/reference/STAGE11_REVIEWER_PACKET_VI.md), [intended-use lock template](docs/reference/STAGE11_INTENDED_USE_LOCK_TEMPLATE_VI.md), [safety hazard-analysis guide](docs/reference/STAGE11_SAFETY_REVIEW_GUIDE_VI.md), [privacy/security closeout worksheet](docs/reference/STAGE11_PRIVACY_SECURITY_GATE_TEMPLATE_VI.md), [online evidence/regulatory review](docs/reference/stage11_online_evidence_review_20261028.md) và [static privacy/security review](docs/reference/STAGE11_LOCAL_PRIVACY_SECURITY_REVIEW_20261029.md).

---

## 🗺️ Lộ Trình Phát Triển Tiếp Theo (Theo Tài Liệu Dự Án)

- [x] **Bước 1 — 4:** Kiểm kê mô hình, kiểm tra suy luận độc lập, API phân loại 10 lớp.
- [x] **Bước 5:** Quản lý ca bệnh, CSDL SQLite, Lịch sử, Nhận xét, Hiệu chỉnh & Dashboard.
- [x] **Giai đoạn 10:** Kho nguồn NCI và bộ câu hỏi tiếng Việt ban đầu.
- [ ] **Giai đoạn 11:** Corpus 794 đoạn/22 nguồn, hybrid retrieval, source routing/preferences, evidence evaluator, audit/replay và regression; chưa nghiệm thu vì thiếu reviewer độc lập, tập mù, citation-entailment review và sign-off G1–G7.
- [x] **Giai đoạn 11A:** Đã tải và lập manifest BTXRD (3.746 ảnh, 10 lớp, 22 metadata, checksum và duplicate audit); do checkpoint hiện tại huấn luyện trên BTXRD nên chưa dùng làm kiểm định độc lập.
- [ ] **Giai đoạn 12:** Chatbot tiếng Việt có trích dẫn nguồn và kiểm thử an toàn.
  Đã có prototype hội thoại Groq/OpenAI cho mục tiêu học tập; chưa có
  acceptance, đánh giá an toàn, blind set hoặc sign-off.
- [ ] **Giai đoạn 13:** Đánh giá toàn diện, bảo mật và đóng gói bàn giao.

Kho nguồn RAG ban đầu gồm 12 trang NCI và bộ câu hỏi kiểm thử. Xem [hướng dẫn kho tài liệu](docs/guides/README_RAG_CORPUS_VI.md). Một số nhãn u lành tính còn thiếu nguồn chuyên biệt.

Để tiếp tục phát triển, đọc [trạng thái dự án và ghi chú bàn giao](docs/PROJECT_STATUS_VI.md) trước. Trang này tổng hợp các thay đổi đã làm, bằng chứng kiểm thử và việc còn mở.

Điểm tiếp tục hiện tại: [Giai đoạn 11 handoff](docs/STAGE11_HANDOFF_VI.md) và [progress note](docs/STAGE11_PROGRESS_2026-10-29.md). Corpus hiện 794 đoạn/22 nguồn; audit PASS, replay 16/16. Dev/V2 đã xem, không phải kiểm định độc lập. G4 đã rà soát 15 cohort candidates; chưa có cohort đủ điều kiện. [C14](docs/reference/stage11_frontiers_11case_cohort_screen_20261029.json) · [C15](docs/reference/stage11_iiest_69case_cohort_screen_20261029.json). Bảy acceptance gates còn OPEN; `answer_ready=false`; đã có demo tra cứu tài liệu local nhưng chưa có chatbot được nghiệm thu. Xem [online evidence review](docs/reference/stage11_online_evidence_review_20261028.md) và [mốc chatbot](docs/reference/STAGE11_CHATBOT_READINESS_VI.md).

Rerank thử nghiệm (`--rerank-concepts`) cho kết quả khác nhau theo tập: giảm dev từ 22/22 xuống 19/22; trên V2 đã xem, hybrid và rerank đều 8/8 (MRR 0,733 và 0,938). Giữ opt-in vì route V2 đã được tune theo p13 và dev giảm. Bộ lọc `--verify-evidence` chặn nhầm nhiều câu có đáp án nên không bật mặc định. Mọi chế độ vẫn trả `answer_ready: false`. Kết quả chi tiết và điểm tiếp tục nằm trong file bàn giao trên.

Tạo chỉ mục cục bộ: `python rag/build_index.py --download-model` (lần đầu), sau đó `python rag/build_index.py`; đo bằng `python rag/evaluate.py`. Xem [hướng dẫn truy xuất](docs/guides/README_RAG_INDEX_VI.md).

Khi lưu ca, API trả `prediction_id` sau `/predict`; giao diện gửi mã này tới `/cases` trong vòng 10 phút. Máy chủ lấy dữ liệu dự đoán đã giữ tạm và chỉ lưu một lần, tránh ghi điểm số do yêu cầu tự khai báo.
