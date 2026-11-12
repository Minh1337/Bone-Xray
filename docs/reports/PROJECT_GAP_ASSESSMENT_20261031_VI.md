# BoneScope — Đối chiếu khoảng trống & trạng thái hoàn thiện theo mục tiêu đồ án

- **Ngày đối chiếu gốc:** 31/10/2026 (UTC+07)
- **Ngày cập nhật hoàn thiện kỹ thuật P1–P7:** 03/11/2026 (UTC+07)

Mục tiêu ghi trong README: **“Đồ án hệ thống hội thoại hỗ trợ phân tích ảnh X-quang u xương kết hợp mô hình học sâu và RAG.”** Phạm vi người dùng xác định: [báo cáo học tập có tính thực nghiệm](../reference/STAGE11_USER_STATED_EDUCATIONAL_SCOPE_20261029.md), không cung cấp cho bác sĩ/người bệnh. Yêu cầu hội thoại: trò chuyện đa chủ đề, dùng kho tài liệu khi hỏi về xương và tích hợp luồng phân tích ca ảnh học tập.

Mọi thay đổi kỹ thuật giữ nguyên `answer_ready=false`, không sửa nhãn dữ liệu, không ghi đè trọng số mô hình hay corpus/index đã khóa và giữ nguyên 7 acceptance gate ở trạng thái `OPEN`.

---

## 1. Bảng tổng hợp trạng thái P1–P7 sau đợt hoàn thiện 03/11/2026

| Hạng mục | Khoảng trống ghi nhận ngày 31/10 | Phần đã hoàn thiện ngày 03/11 | Artifact / Bằng chứng tái lập | Giới hạn còn phải nêu trung thực trong báo cáo |
| --- | --- | --- | --- | --- |
| **P1 — Luồng ảnh → dự đoán → tài liệu → hội thoại** | Giao diện ảnh tách khỏi chatbot; chatbot chưa nhận kết quả dự đoán ca ảnh. | Đã tích hợp trọn vẹn trong `rag/case_context.py`, `rag/demo_api.py` và `rag/demo_web/`: nạp ảnh + 22 metadata → chạy `Predictor` cục bộ → lưu `CaseStore` trong RAM với `case_id` do máy chủ cấp → tự động tra cứu nguồn (với nhãn `direct`) và sinh giải thích 3 phần → hỏi nối tiếp theo `case_id` → đổi/xóa ảnh tự động xóa ngữ cảnh ca cũ. | `rag/case_context.py`, `rag/demo_api.py`, `rag/demo_web/`, `rag/tests/test_case_context.py`, `tests/test_end_to_end_pipeline.py` | Ảnh và 22 metadata chỉ xử lý cục bộ; trợ lý AI không nhìn thấy pixel ảnh mà chỉ đọc Top-3 nhãn/điểm softmax và đoạn nguồn. Điểm softmax không phải xác suất mắc bệnh. |
| **P2 — Đánh giá thực nghiệm mô hình ảnh** | Mới có kiểm tra 3 ảnh mẫu (`cases.json`); thiếu bảng confusion matrix, macro-F1, per-class P/R/F1 và ablation trên mẫu lớn. | Đã xây `tools/evaluate_xray_checkpoint.py` và chạy đánh giá phân tầng 250 ảnh (25 ảnh × 10 lớp, seed `20261031`) trên GPU RTX 3050: **Top-1 = 0,7760, Top-3 = 0,9400, Macro-F1 = 0,7759**, thời gian suy luận trung vị **25,2 ms/ảnh**. Kèm thí nghiệm ablation tắt metadata (đặt vector 22 chiều = 0): **Top-1 giảm từ 0,7760 xuống 0,4800, Macro-F1 giảm từ 0,7759 xuống 0,4389**, làm đổi dự đoán Top-1 ở **91/250 ảnh (36,4%)** (trong đó `no-tumor` và `synovial osteochondroma` tụt recall về 0,0 khi mất metadata). | `tools/evaluate_xray_checkpoint.py`, `docs/reference/stage11_xray_in_source_evaluation_20261103.json`, `tests/test_xray_evaluator.py` | BTXRD là tập nguồn huấn luyện của checkpoint (`n_samples_seen_ = 2616` ≈ 69,8% bộ BTXRD) và danh sách ID train/val/test gốc không được lưu trong checkpoint. Do đó số liệu trên là **đánh giá nội nguồn (in-source) và chứng minh vai trò của nhánh Cross-Attention metadata**, KHÔNG phải kiểm định độc lập (external/held-out test). |
| **P3 — Hợp đồng đầu vào và phạm vi “đọc ảnh”** | Cần làm rõ 22 trường bắt buộc, chặn form trống và nói rõ mô hình chỉ phân loại 10 lớp. | Đã bổ sung kiểm tra `check_demo_metadata` (dựa trên quy luật kiểm chứng ở cả 3.746 dòng BTXRD: đủ 22 trường, ≥1 vị trí giải phẫu = 1 và đúng 1 tư thế chụp `frontal`/`lateral`/`oblique` = 1) và giao diện nhập/nạp JSON thuận tiện trong hộp thoại phân tích ca. | `bonescope/xray_api.py` (`parse_metadata`, `predict_upload`), `rag/case_context.py` (`check_demo_metadata`), `rag/demo_web/index.html` | Đầu ra của mô hình chỉ là phân loại 10 nhãn cấp ảnh (image-level classification); không khoanh vùng (bounding box/segmentation) hay mô tả dấu hiệu X-quang chi tiết từ pixel. |
| **P4 — Liên kết nhãn với nguồn & đánh giá giải thích** | Cần bảng ánh xạ rõ 10 nhãn của checkpoint sang kho nguồn, tránh đồng nhất nhãn chưa rõ (`osteofibroma`, `synovial osteochondroma`) hoặc nhãn gộp (`other bt`, `other mt`). | Đã khóa bảng `LABEL_GUIDE` cho đủ 10 nhãn đồng bộ với `rag/data/retrieval_config.json`: 4 nhãn `direct` (`osteochondroma`, `simple bone cyst`, `giant cell tumor`, `osteosarcoma`) được tra cứu tự động; 3 nhãn `unresolved` (`osteofibroma`, `synovial osteochondroma`, `multiple osteochondromas`), 2 nhãn `aggregate` (`other bt`, `other mt`) và `no-tumor` không tự động tra cứu nguồn mà trả lời bằng mẫu máy chủ xác định kèm gợi ý khái niệm liên quan chưa kiểm chứng. | `rag/case_context.py` (`LABEL_GUIDE`, `template_explanation`), `rag/tests/test_case_context.py` | Bảng ánh xạ là thiết kế kỹ thuật bảo thủ để chống suy diễn quá đà, chưa có adjudication thuật ngữ của bác sĩ chuyên khoa chẩn đoán hình ảnh/giải phẫu bệnh. |
| **P5 — Tái lập và đối chiếu nguồn huấn luyện** | Cần ghi rõ thông tin khôi phục được từ checkpoint và `metadata_processor.joblib`. | Đã trích xuất và lưu tự động trong `checkpoint_provenance_audit`: `best_epoch = 41`, `best_val_mAP = 0.686125`, `best_threshold = 0.15`, `split_signature = d812e544...`, `seed = 2018`, `group_column = patient_id`, `val_ratio = 0.15`, `test_ratio = 0.15` và `metadata_processor` (`age` scaler `n_samples_seen_ = 2616`, `mean = 35.3528`, `std = 20.7671`, `median_fill = 35.0`). | `docs/reference/stage11_xray_in_source_evaluation_20261103.json` | Danh sách ID ảnh từng tập train/val/test và cột `patient_id` gốc không có trong bản phát hành BTXRD công khai trên Figshare nên không thể tái tạo chính xác tập test gốc chỉ từ archive công khai. |
| **P6 — Demo và kiểm thử toàn chuỗi** | Cần phép thử toàn chuỗi từ ảnh + metadata hợp lệ đến dự đoán, truy xuất tài liệu và hội thoại, gồm cả các ca lỗi. | Đã thêm 12 bài kiểm tra đơn vị/API trong `rag/tests/test_case_context.py`, 2 bài kiểm tra evaluator trong `tests/test_xray_evaluator.py` và bài kiểm tra tích hợp thật `tests/test_end_to_end_pipeline.py` chạy trực tiếp `model/best_model.pt` + `rag.retrieval.Retriever` trên `case_002` (`osteosarcoma`) và `case_001` (`other mt`). | `rag/tests/test_case_context.py`, `tests/test_end_to_end_pipeline.py`, `tests/test_xray_evaluator.py` | Các bài kiểm tra tự động dùng mock cho tầng gọi mạng Groq/OpenAI để đảm bảo chạy lại offline 100% và không lộ API key. |
| **P7 — Báo cáo và bàn giao đúng phiên bản hiện tại** | Một số chỗ trong README còn mô tả “chưa nhận ảnh/ca bệnh” hoặc “offline hoàn toàn”. | Đã cập nhật `README.md`, `README_VI.md`, `docs/guides/CHATBOT_CONVERSATION_VI.md` và tài liệu này để phản ánh chính xác kiến trúc lai: **mô hình ảnh Swin + Metadata và truy xuất RAG chạy cục bộ (offline), kết hợp tạo bản nháp/hội thoại qua Groq hoặc OpenAI (online, có fallback mẫu máy chủ khi không có mạng/key)**. | `README.md`, `README_VI.md`, `docs/guides/CHATBOT_CONVERSATION_VI.md`, `docs/reports/PROJECT_GAP_ASSESSMENT_20261031_VI.md` | 7 cổng nghiệm thu G1–G7 của hồ sơ Giai đoạn 11 vẫn giữ `OPEN` và `answer_ready=false`. |

---

## 2. Tóm tắt số liệu thực nghiệm mô hình ảnh để đưa vào báo cáo học tập (P2 & P5)

Nguồn dữ liệu: `docs/reference/stage11_xray_in_source_evaluation_20261103.json` (tái lập bằng `.\.venv\Scripts\python.exe tools\evaluate_xray_checkpoint.py --per-class 25`).

### 2.1. So sánh tổng thể & Ablation nhánh Metadata Cross-Attention (250 ảnh phân tầng, 25 ảnh/lớp)

| Cấu hình suy luận | Top-1 Accuracy | Top-3 Accuracy | Macro-F1 | Số ảnh đổi nhãn Top-1 | Thời gian suy luận trung vị (RTX 3050) |
| --- | --- | --- | --- | --- | --- |
| **Đầy đủ: Ảnh + 22 trường Metadata thật** | **0,7760** (194/250) | **0,9400** (235/250) | **0,7759** | — (baseline) | **25,2 ms / ảnh** (p95: 27,0 ms) |
| **Ablation: Ảnh + Vector Metadata = 0** | **0,4800** (120/250) | **0,7200** (180/250) | **0,4389** | **91 / 250 (36,4%)** | Cùng lượt chạy |

**Nhận xét khoa học cho báo cáo:**
1. **Vai trò quyết định của Metadata + Cross-Attention:** Khi xóa thông tin metadata (đặt vector 22 chiều về 0 sau chuẩn hóa), Top-1 giảm mạnh **29,6 điểm phần trăm** (từ 77,6% xuống 48,0%) và Macro-F1 giảm **33,7 điểm phần trăm** (từ 0,7759 xuống 0,4389). Đặc biệt, lớp `no-tumor` (F1 từ 1,000 xuống 0,000) và `synovial osteochondroma` (F1 từ 0,9583 xuống 0,000) bị sụp đổ hoàn toàn khi thiếu thông tin vị trí xương/khớp và hướng chụp, chứng minh mô hình đã học sự phụ thuộc chặt chẽ giữa đặc trưng hình ảnh Swin và token metadata qua cổng Cross-Attention.
2. **Lý do kỹ thuật bắt buộc kiểm tra 22 trường đầu vào (P3):** Kết quả ablation giải thích trực tiếp vì sao hệ thống không được phép tự động điền 0 khi người dùng bỏ trống metadata—việc điền 0 làm sai lệch phân bố đầu vào của `MetadataMLP` và làm đổi nhãn Top-1 ở 36,4% số ca.
3. **Giới hạn phương pháp luận:** Vì checkpoint được huấn luyện trên BTXRD (`n_samples_seen_ = 2616` trên 3.746 ảnh) và không lưu danh sách ID của tập test gốc, mẫu 250 ảnh phân tầng chứa cả ảnh thuộc tập train và val/test. Trong báo cáo đồ án, bảng này được trình bày là **kiểm tra thực nghiệm nội nguồn và phân tích đóng góp thành phần (ablation study)**, không gọi là độ chính xác kiểm định độc lập.

### 2.2. Kết quả chi tiết theo từng lớp (với Metadata thật, 25 ảnh/lớp)

| Nhãn checkpoint (`flat_labels`) | Trạng thái ánh xạ RAG (`LABEL_GUIDE`) | Precision | Recall | F1-score | Support |
| --- | --- | --- | --- | --- | --- |
| `no-tumor` | `no_tumor` (không tra cứu bệnh) | 1,0000 | 1,0000 | 1,0000 | 25 |
| `synovial osteochondroma` | `unresolved` (gợi ý học tập: *synovial chondromatosis*) | 1,0000 | 0,9200 | 0,9583 | 25 |
| `multiple osteochondromas` | `unresolved` (gợi ý học tập: *osteochondroma*) | 0,8889 | 0,9600 | 0,9231 | 25 |
| `osteosarcoma` | `direct` (tra cứu tự động kho nguồn) | 0,9091 | 0,8000 | 0,8511 | 25 |
| `simple bone cyst` | `direct` (tra cứu tự động kho nguồn) | 0,7241 | 0,8400 | 0,7778 | 25 |
| `giant cell tumor` | `direct` (tra cứu tự động kho nguồn) | 0,8500 | 0,6800 | 0,7556 | 25 |
| `other mt` | `aggregate` (nhóm u ác gộp, không tự tra cứu) | 0,7500 | 0,6000 | 0,6667 | 25 |
| `osteochondroma` | `direct` (tra cứu tự động kho nguồn) | 0,5000 | 0,9600 | 0,6575 | 25 |
| `osteofibroma` | `unresolved` (gợi ý học tập: *osteofibrous dysplasia*) | 0,8571 | 0,4800 | 0,6154 | 25 |
| `other bt` | `aggregate` (nhóm u lành gộp, không tự tra cứu) | 0,5909 | 0,5200 | 0,5532 | 25 |

---

## 3. Căn cứ và lệnh kiểm chứng toàn dự án

```powershell
# 1. Toàn bộ bài kiểm thử tự động (API, RAG, Chatbot, Case Context, Evaluator, E2E thật)
.\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q

# 2. Kiểm tra cú pháp JavaScript giao diện
node --check rag/demo_web/app.js
node --check xray_web/app.js

# 3. Kiểm tra tính toàn vẹn kho nguồn/index và deterministic replay (16/16)
.\.venv\Scripts\python.exe -m rag.audit --report-dir docs/reference/stage11_policy_rerun_20261029_cureus_abcrouting_v1 --output $env:TEMP\bs_audit.json
.\.venv\Scripts\python.exe -m rag.replay_reports --bundle docs/reference/stage11_policy_rerun_20261029_cureus_abcrouting_v1 --output $env:TEMP\bs_replay.json

# 4. Kiểm tra tính toàn vẹn thanh ghi 7 cổng G1–G7 và 15 cohort leads
.\.venv\Scripts\python.exe -m tools.verify_stage11_registers
```
