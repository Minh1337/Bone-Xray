# Báo cáo Thực nghiệm Tích hợp Chatbot Đa Lượt, Phân loại X-quang + 22 Metadata & Phân tích Catalogue BTXRD (Giai đoạn 12 — Cập nhật 06/11/2026)

> **Phạm vi báo cáo:** Tài liệu này tổng hợp kiến trúc kỹ thuật, số liệu thống kê toàn bộ catalogue BTXRD (`3.746` ảnh), kết quả thực nghiệm phân tầng & ablation 22 trường metadata (`250` ảnh), phân tích hiệu chuẩn xác suất softmax (`ECE`, `MCE`, `Brier score`, `NLL`) cùng độ chính xác theo nhóm con (`view`/`center`/`region`/`status`), cơ chế ánh xạ 10 nhãn sang kho tài liệu RAG (`22` nguồn / `794` đoạn) và kết quả kiểm chứng phần mềm (`176 passed / 132 subtests passed`) phục vụ **báo cáo học tập có tính thực nghiệm** ([`STAGE11_USER_STATED_EDUCATIONAL_SCOPE_20261029.md`](../reference/STAGE11_USER_STATED_EDUCATIONAL_SCOPE_20261029.md)). Hệ thống **không** phải thiết bị y tế, **không** dùng để chẩn đoán/điều trị cho bác sĩ hay người bệnh, giữ `answer_ready = false` trên toàn bộ API và giữ nguyên **0/7 cổng nghiệm thu đóng (`OPEN`)** trong [`stage11_acceptance_gate_status_20261029.csv`](../reference/stage11_acceptance_gate_status_20261029.csv).

> **Cập nhật provider 09/11/2026:** báo cáo bên dưới phản ánh lần tích hợp cũ. Cấu hình hiện tại ưu tiên OpenRouter với model `:free`; Groq chỉ là dự phòng rate-limit khi bật và phải giữ tài khoản ở Free Plan. Xem [hướng dẫn provider hiện hành](../guides/OPENROUTER_CHATBOT_SETUP_VI.md).

## Cập nhật kiểm chứng 09/11/2026

Bản báo cáo chính dưới đây giữ nguyên số liệu và kết quả của mốc 06/11. Sau các thay đổi chatbot ngày 09/11, full regression offline hiện đạt **172 passed, 0 failed / 132 subtests passed**; provider traffic trong test được giả lập, không gọi API thật. Đã sửa `/api/config` thiếu import `os`, và chuyển kiểm tra phản hồi rỗng/incomplete vào nhánh fallback để yêu cầu đủ điều kiện có thể thử Qwen. Luồng ảnh giữ ảnh trong bộ nhớ tab theo hội thoại để hỏi tiếp, không ghi ảnh vào SQLite; sau phân tích, hệ thống tìm tối đa 4 đoạn RAG và gắn nhãn rõ là tài liệu đọc thêm.

Hiện dùng `openrouter/free` cho chat/RAG, `google/gemma-4-31b-it:free` cho ảnh và `qwen/qwen3.5-flash-02-23` làm fallback trả phí duy nhất sau timeout, rate limit, phản hồi incomplete hoặc rỗng. Với Gemma bị rate limit, thử OpenRouter Free Router một lần trước khi chuyển. Groq fallback mặc định tắt. Phản hồi Qwen được đánh dấu trong UI. **Browser smoke Chrome headless đã PASS với AI/retrieval giả lập và DB/profile tạm. Provider smoke riêng sau đó cũng PASS: chữ qua Free 3,343 giây, ảnh hình học qua Qwen 29,594 giây; một lượt trả phí và cost được phản hồi báo về $0,000248755 ([record](../reference/chatbot_provider_smoke_20261109.json)).** Lượt tiếp nối sửa retry mất ảnh sau lần lưu đầu, history ảnh vượt 8 tin/9.000 ký tự, tiêu đề chat, định dạng lịch sử và deadline UI. [Record 09/11](../reference/chatbot_browser_regression_20261109.json). G1–G7 vẫn OPEN, `answer_ready=false`; xem [báo cáo trạng thái hoàn thiện](PROJECT_COMPLETION_STATUS_20261109_VI.md).

---

## 1. Kiến trúc Tích hợp Tổng thể (`BoneScope Research Studio`)

Hệ thống kết hợp 4 luồng xử lý trong cùng một ứng dụng nghiên cứu cục bộ (`rag/demo_api.py`, `http://127.0.0.1:8765`):

1. **Luồng Phân loại Ca X-quang + 22 Metadata Cục bộ (`POST /api/case`, `POST /api/case/{case_id}/explain`):**
   - Nạp ảnh X-quang (upload tệp, kéo–thả, chọn nhanh 6 mẫu tiêu biểu `.btxrd-sample-chip`, hoặc nạp theo mã `IMG000001` từ `GET /api/reference-images/{image_id}`).
   - Tự động đối chiếu mã băm SHA-256 của byte ảnh với chỉ mục BTXRD cục bộ (`POST /api/case/metadata-match`) để điền chính xác 22 trường metadata; tự động chặn `9` nhóm ảnh trùng byte có metadata mâu thuẫn (`409 Conflict` / `ambiguous_metadata`).
   - Kiểm tra nghiêm ngặt quy tắc 22 trường metadata (`cases.check_demo_metadata()`: tuổi `0–120`, giới tính `M`/`F`, ít nhất `1/17` vị trí giải phẫu `== 1`, và đúng `1/3` tư thế chụp `frontal`/`lateral`/`oblique` `== 1`).
   - Chạy mô hình `Swin + MetadataMLP + Cross-Attention` (`model/best_model.pt`) trên máy cục bộ, lưu kết quả vào `CaseStore` trong RAM (`TTL = 30 phút`, tối đa `50` ca, không ghi ảnh/metadata ra đĩa) và ánh xạ qua bảng `LABEL_GUIDE`.
2. **Luồng Truy xuất RAG Có Trích dẫn & Hội thoại Đa lượt (`POST /api/query`):**
   - Kết hợp `BM25` + `Multilingual-E5-Small` (`794 × 384`) trên `22` nguồn tài liệu y khoa mở có kiểm tra giấy phép và mã băm SHA-256.
   - Hỗ trợ hỏi–đáp nối tiếp đa lượt (`rag/conversation.py`) có gắn ngữ cảnh ca đang mở (`case_id` do server quản lý; chỉ gửi Top-3 nhãn/điểm softmax và ghi chú ánh xạ tới nhà cung cấp AI, ẩn tuyệt đối ảnh, tuổi, giới tính, vị trí và tên tệp).
3. **Luồng Hỏi AI về Ảnh Đính Kèm (`POST /api/image-chat`):**
   - Hỗ trợ đính kèm ảnh JPEG/PNG/WEBP (`≤ 10 MiB`, `≤ 25 megapixel`, single-frame) bằng nút **Ảnh**, dán `Ctrl+V` hoặc kéo–thả vào khung nhập câu hỏi, hoặc chuyển tiếp từ ảnh không thuộc BTXRD.
   - Gửi ảnh dạng data URL tới model vision `google/gemma-4-31b-it:free`; khi dùng Qwen dự phòng, xử lý ảnh có thể phát sinh phí token. **Không lưu byte ảnh vào SQLite** (`image_not_stored = true`, `answer_ready = false`). UI giữ `File` ảnh tạm theo hội thoại trong tab để hỏi tiếp; mở lịch sử sau này cần gửi lại ảnh. Sau phân tích, backend tra cứu tối đa 4 đoạn nguồn liên quan; các đoạn này chỉ là tài liệu đọc thêm, không xác nhận dấu hiệu ảnh. Kiểm thử API offline mới nhất đạt trong [báo cáo 09/11](PROJECT_COMPLETION_STATUS_20261109_VI.md); Chrome headless đã kiểm tra luồng UI với fixture; provider đã có smoke cơ bản riêng bằng ảnh hình học; chưa kiểm tra chất lượng X-quang.
4. **Luồng Lưu Lịch sử Hội thoại Văn bản Cục bộ (`rag/chat_history.py`, `/api/conversations*`):**
   - Lưu các lượt hỏi–đáp văn bản hoàn tất và 5 trường trích dẫn an toàn (`chunk_id`, `source_id`, `title`, `text`, `source_sha256`) vào `data/chat_history.db` (tối đa `500` cuộc trò chuyện, `2.000` tin nhắn/cuộc trò chuyện).
   - Chống phản hồi đến muộn gắn nhầm vào phiên mới, từ chối tạo lại hội thoại đã xóa (`409 Conflict`), và không tự động xóa ngầm lịch sử cũ khi chạm giới hạn.

---

## 2. Phân tích Định lượng Toàn bộ Catalogue BTXRD (`3.746` ảnh)

*Nguồn dữ liệu tái lập:* [`tools/analyze_btxrd_catalogue.py`](../../tools/analyze_btxrd_catalogue.py) → [`docs/reference/stage12_btxrd_catalogue_and_mapping_analysis_20261105.json`](../reference/stage12_btxrd_catalogue_and_mapping_analysis_20261105.json) (SHA-256 manifest: `e36be2de308e240c28c38e378416bbf789d6e251665ac66cc46dd62dbf19fe64`).

### 2.1. Tổng quan Catalogue & Kiểm tra Trùng lặp Byte (SHA-256)

| Chỉ số | Giá trị | Ghi chú kỹ thuật & xử lý trong BoneScope |
| --- | ---: | --- |
| Tổng số dòng trong `manifest.csv` | **3.746** | `100,0%` (`3.746/3.746`) đạt `metadata_status = ok` và tuân thủ quy tắc `≥1` vị trí giải phẫu & đúng `1` tư thế chụp |
| Số dòng có nhãn `ground_truth` đơn | **3.745** | `1` dòng (`IMG001276.jpeg`) có `ground_truth = null` trong manifest gốc |
| Số mã băm SHA-256 duy nhất | **3.725** | Có **21 cặp ảnh** (`42` dòng) chia sẻ cùng nội dung byte ảnh |
| Nhóm trùng byte có **metadata giống hệt** | **12 nhóm** (`24` ảnh) | Tự động điền 22 metadata bình thường (cùng tuổi, giới tính, vị trí, tư thế và nhãn) |
| Nhóm trùng byte có **metadata mâu thuẫn** | **9 nhóm** (`18` ảnh) | **Bị chặn tự điền** (`reason = "ambiguous_metadata"`, HTTP `409` trên `GET /api/reference-images/{id}`) |

**Danh sách 9 cặp ảnh trùng byte nhưng mâu thuẫn metadata bị chặn tự động:**
- `IMG000430.jpeg` ↔ `IMG000765.jpeg` (`osteochondroma` / `osteochondroma`, khác metadata)
- `IMG000591.jpeg` ↔ `IMG003456.jpeg` (`osteochondroma` / `no-tumor`, khác cả nhãn và metadata)
- `IMG000707.jpeg` ↔ `IMG003346.jpeg` (`osteochondroma` / `no-tumor`, khác cả nhãn và metadata)
- `IMG001721.jpeg` ↔ `IMG001799.jpeg` (`osteochondroma` / `osteochondroma`, khác metadata)
- `IMG001722.jpeg` ↔ `IMG001836.jpeg` (`osteochondroma` / `osteochondroma`, khác metadata)
- `IMG001733.jpeg` ↔ `IMG001766.jpeg` (`osteochondroma` / `osteochondroma`, khác metadata)
- `IMG001734.jpeg` ↔ `IMG001789.jpeg` (`osteochondroma` / `osteochondroma`, khác metadata)
- `IMG003668.jpeg` ↔ `IMG003686.jpeg` (`no-tumor` / `no-tumor`, khác metadata)
- `IMG003669.jpeg` ↔ `IMG003685.jpeg` (`no-tumor` / `no-tumor`, khác metadata)

### 2.2. Phân bố 10 Nhãn Checkpoint & Độ phủ Ánh xạ RAG (`LABEL_GUIDE`)

| Nhãn Checkpoint (`LABELS`) | Số ảnh BTXRD | Tỷ lệ (%) | Chế độ Ánh xạ (`LABEL_GUIDE`) | Hành vi của Chatbot khi Giải thích Ca (`POST /api/case/{id}/explain`) |
| --- | ---: | ---: | --- | --- |
| `no-tumor` | 1.879 | 50,16% | `no_tumor` | Trả về mẫu máy chủ giải thích nhãn không phát hiện khối u; không tự tra cứu bệnh |
| `osteochondroma` | 753 | 20,10% | `direct` | Tự động truy xuất RAG về *osteochondroma* và tổng hợp giải thích có trích dẫn `[S1]`, `[S2]` |
| `osteosarcoma` | 297 | 7,93% | `direct` | Tự động truy xuất RAG về *osteosarcoma* và tổng hợp giải thích có trích dẫn `[S1]`, `[S2]` |
| `multiple osteochondromas` | 263 | 7,02% | `unresolved` | Không tự gán vào *osteochondroma* đơn độc; hiển thị mẫu giải thích giới hạn và gợi ý chủ đề liên quan |
| `simple bone cyst` | 206 | 5,50% | `direct` | Tự động truy xuất RAG về *simple/unicameral bone cyst* và tổng hợp giải thích có trích dẫn |
| `other bt` | 115 | 3,07% | `aggregate` | Nhãn gộp u xương lành tính khác; giải thích theo mẫu máy chủ, không đoán bệnh cụ thể |
| `giant cell tumor` | 93 | 2,48% | `direct` | Tự động truy xuất RAG về *giant cell tumor of bone* và tổng hợp giải thích có trích dẫn |
| `synovial osteochondroma` | 50 | 1,33% | `unresolved` | Không tự đồng nhất với *synovial chondromatosis*; hiển thị mẫu giải thích giới hạn ánh xạ |
| `other mt` | 45 | 1,20% | `aggregate` | Nhãn gộp u xương ác tính khác; giải thích theo mẫu máy chủ, không đoán bệnh cụ thể |
| `osteofibroma` | 44 | 1,17% | `unresolved` | Không tự đồng nhất với *osteofibrous dysplasia*; hiển thị mẫu giải thích giới hạn ánh xạ |
| *(Chưa gán nhãn: `IMG001276.jpeg`)* | 1 | 0,03% | — | Vẫn có đủ 22 trường metadata hợp lệ trong manifest |
| **Tổng cộng** | **3.746** | **100,00%** | **4 nhóm (`direct`: 36,01%, `no_tumor`: 50,16%, `unresolved`: 9,53%, `aggregate`: 4,27%)** | **72,02% số ca có khối u (`1.349 / 1.866`) thuộc nhóm `direct` có nguồn RAG đối chiếu trực tiếp** |

### 2.3. Phân bố Nhân khẩu học, Trung tâm Thu thập, Vị trí Giải phẫu & Tư thế Chụp (`3.746` ảnh)

- **Độ tuổi (`age`):** nhỏ nhất `1,0` tuổi, phân vị thứ 25 (`Q25`) = `16,0`, trung vị (`median`) = `34,0`, trung bình (`mean`) = `35,29 ± 20,90` tuổi, phân vị thứ 75 (`Q75`) = `53,0`, lớn nhất `88,0` tuổi.
- **Giới tính (`gender`):** Nam (`M`) = `2.098` ảnh (`56,01%`), Nữ (`F`) = `1.648` ảnh (`43,99%`).
- **Trung tâm thu thập (`source_center`):**
  - `Center 1`: **2.938 ảnh (`78,43%`)** — đầy đủ cả 10 nhãn (`1.593 no-tumor`, `628 osteochondroma`, `215 osteosarcoma`, v.v.).
  - `Center 2`: **549 ảnh (`14,66%`)** — không có mẫu `osteofibroma` (`0`) và `other bt` (`0`).
  - `Center 3`: **259 ảnh (`6,91%`)** — tỷ lệ `no-tumor` rất thấp (`27/259 = 10,42%`), nhưng tập trung tỷ trọng lớn các nhãn hiếm/nhãn gộp như `other bt` (`43` ca, chiếm `37,39%` tổng số `other bt` toàn bộ dữ liệu), `multiple osteochondromas` (`49` ca) và `other mt` (`15` ca, chiếm `33,33%` tổng số `other mt`).
- **Tư thế chụp (`VIEW_FIELDS`, tổng = `3.746`):** `frontal` = `2.181` (`58,22%`), `lateral` = `1.269` (`33,88%`), `oblique` = `296` (`7,90%`).
- **Vị trí giải phẫu phổ biến nhất (`SITE_FIELDS`):** `lower limb` (`2.406`), `upper limb` (`1.124`), `tibia` (`630`), `femur` (`592`), `fibula` (`259`), `humerus` (`235`), `pelvis` (`216`), `hand` (`97`), `foot` (`93`), `radius` (`73`), `hip bone` (`69`), `ulna` (`62`), `knee-joint` (`37`), `shoulder-joint` (`12`), `elbow-joint` (`5`), `ankle-joint` (`4`), `hip-joint` (`3`).

---

## 3. Kết quả Thực nghiệm Phân tầng 250 Ảnh & Ablation Cross-Attention Metadata

*Nguồn dữ liệu tái lập:* [`tools/evaluate_xray_checkpoint.py`](../../tools/evaluate_xray_checkpoint.py) → [`docs/reference/stage11_xray_in_source_evaluation_20261103.json`](../reference/stage11_xray_in_source_evaluation_20261103.json) (`250` ảnh phân tầng = `25` ảnh × `10` lớp, `seed = 20261031`, chạy trên NVIDIA GeForce RTX 3050 Laptop GPU, độ trễ trung vị `25,2 ms/ảnh`).

> **Cảnh báo nguồn gốc dữ liệu (Provenance):** Checkpoint `model/best_model.pt` được huấn luyện trên BTXRD (`n_samples_seen_ = 2.616` trong `metadata_processor.joblib`, tương đương `~69,8%` bộ dữ liệu) và không lưu danh sách ID của tập train/val/test. Do đó, bảng dưới đây là **đánh giá nội nguồn & thực nghiệm ablation kỹ thuật (in-source evaluation & metadata ablation)** để chứng minh vai trò của nhánh `MetadataMLP + Cross-Attention`, **không phải** độ chính xác kiểm định độc lập bên ngoài.

### 3.1. So sánh Tổng thể: Đủ 22 Metadata Thực so với Ablation Xóa Metadata về 0

| Chế độ Thực nghiệm | Top-1 Accuracy | Top-3 Accuracy | Macro-F1 | Số ca đổi dự đoán Top-1 |
| --- | ---: | ---: | ---: | ---: |
| **Có đủ 22 Metadata thực (`with_true_metadata`)** | **0,7760** (`194/250`) | **0,9400** (`235/250`) | **0,7759** | — (Mốc tham chiếu) |
| **Xóa 22 Metadata về 0 (`ablation_with_zeroed_metadata`)** | **0,4800** (`120/250`) | **0,7200** (`180/250`) | **0,4389** | **91 / 250 ca (`36,40%`)** |
| **Độ sụt giảm khi thiếu Metadata ($\Delta$)** | **$-0,2960$ (`-29,60%`)** | **$-0,2200$ (`-22,00%`)** | **$-0,3370$** | **Sụp đổ hoàn toàn ở `no-tumor` và `synovial osteochondroma`** |

### 3.2. Kết quả Chi tiết theo Từng Lớp (`25` ảnh/lớp)

| Nhãn (`support = 25`) | Precision (Đủ Meta) | Recall (Đủ Meta) | F1 (Đủ Meta) | Precision (Zero Meta) | Recall (Zero Meta) | F1 (Zero Meta) | Nhận xét tác động của Cross-Attention Metadata |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `no-tumor` | 1,0000 | 1,0000 | **1,0000** | 0,0000 | 0,0000 | **0,0000** | Khi mất metadata, `25/25` ca `no-tumor` bị đoán nhầm thành u xương (`15` ca sang `osteochondroma`) |
| `synovial osteochondroma` | 1,0000 | 0,9200 | **0,9583** | 0,0000 | 0,0000 | **0,0000** | Phụ thuộc mạnh vào vị trí khớp; khi mất metadata, Recall tụt từ `92%` về `0%` |
| `multiple osteochondromas` | 0,8889 | 0,9600 | **0,9231** | 0,8000 | 0,6400 | **0,7111** | Recall giảm từ `96%` xuống `64%` (nhầm sang `osteochondroma` đơn độc) |
| `osteosarcoma` | 0,9091 | 0,8000 | **0,8511** | 0,8182 | 0,7200 | **0,7660** | Giữ được đặc trưng hình ảnh ác tính tốt hơn nhưng F1 vẫn giảm `8,51` điểm % |
| `simple bone cyst` | 0,7241 | 0,8400 | **0,7778** | 0,4857 | 0,6800 | **0,5667** | Precision giảm mạnh từ `72,41%` xuống `48,57%` khi thiếu tuổi và vị trí xương dài |
| `giant cell tumor` | 0,8500 | 0,6800 | **0,7556** | 0,7778 | 0,2800 | **0,4118** | Recall giảm từ `68%` xuống `28%` khi thiếu thông tin độ tuổi trưởng thành và đầu xương |
| `other mt` | 0,7500 | 0,6000 | **0,6667** | 0,4615 | 0,4800 | **0,4706** | F1 giảm `19,61` điểm % khi mất ngữ cảnh metadata |
| `osteochondroma` | 0,5000 | 0,9600 | **0,6575** | 0,2963 | 0,9600 | **0,4528** | Khi xóa metadata, mô hình thiên lệch dự đoán `osteochondroma` (`FP` tăng từ `24` lên `57`) |
| `osteofibroma` | 0,8571 | 0,4800 | **0,6154** | 0,7500 | 0,4800 | **0,5854** | Thường gặp ở xương chày (`tibia`); hay bị nhầm với `osteochondroma` trên ảnh đơn thuần |
| `other bt` | 0,5909 | 0,5200 | **0,5532** | 0,3415 | 0,5600 | **0,4242** | Precision giảm từ `59,09%` xuống `34,15%` |

> **Ý nghĩa thực tiễn cho thiết kế UI/API:** Kết quả ablation giải thích vì sao giao diện BoneScope **bắt buộc kiểm tra đủ 22 trường metadata** (hoặc tự khớp qua SHA-256 BTXRD) trước khi gọi bộ phân loại Swin, đồng thời tuyệt đối **không tự điền `0` cho các thông tin chưa biết** của ảnh ngoại lai mà hướng người dùng sang luồng mô tả trực quan (`POST /api/image-chat`).

### 3.3. Phân tích Hiệu chuẩn Xác suất Softmax (`Calibration`) & Kết quả Theo Nhóm Con (`Subgroup Breakdown`)

*Nguồn dữ liệu tái lập:* [`tools/analyze_xray_calibration_and_subgroups.py`](../../tools/analyze_xray_calibration_and_subgroups.py) → [`docs/reference/stage12_xray_subgroup_and_calibration_20261106.json`](../reference/stage12_xray_subgroup_and_calibration_20261106.json) (`250` ảnh phân tầng, `seed = 20261031`).

#### A. Hiệu chuẩn điểm Softmax Top-1 (Đủ 22 Metadata so với Ablation Zero Metadata)

| Chỉ số Hiệu chuẩn (`Calibration Metric`) | Đủ 22 Metadata Thực | Xóa 22 Metadata về 0 (`Ablation`) | Diễn giải Kỹ thuật & Ý nghĩa An toàn |
| --- | ---: | ---: | --- |
| **Top-1 Accuracy** | **0,7760** (`77,60%`) | **0,4800** (`48,00%`) | Giảm `29,60` điểm % khi mất metadata |
| **Điểm Softmax Top-1 Trung bình (Toàn bộ 250 ca)** | **0,7892** (`78,92%`) | **0,6875** (`68,75%`) | Dù mất metadata làm sai hơn một nửa số ca, điểm tự tin trung bình vẫn ở mức cao (`68,75%`) |
| **Điểm Softmax Top-1 trên các ca ĐOÁN ĐÚNG** | **0,8439** (`84,39%`) | **0,7451** (`74,51%`) | Phân tách độ tự tin tốt hơn khi có đủ metadata |
| **Điểm Softmax Top-1 trên các ca ĐOÁN SAI** | **0,5996** (`59,96%`) | **0,6345** (`63,45%`) | Ngay cả khi đoán sai, mô hình vẫn xuất điểm Top-1 trung bình `~60–63%` |
| **Độ lệch tự tin quá mức (`Mean Conf - Accuracy`)** | **+0,0132** (`+1,32%`) | **+0,2075** (`+20,75%`) | Khi thiếu metadata, mô hình rơi vào trạng thái **tự tin quá mức nghiêm trọng (`+20,75%`)** |
| **Expected Calibration Error (`10-bin ECE`)** | **0,0367** (`3,67%`) | **0,2075** (`20,75%`) | Sai số hiệu chuẩn tăng gấp **5,65 lần** khi thiếu metadata |
| **Maximum Calibration Error (`10-bin MCE`)** | **0,0671** (`6,71%`) | **0,3461** (`34,61%`) | Ở bin `(0.9, 1.0]` khi xóa metadata (`58` ca), độ tự tin TB là `96,68%` nhưng độ chính xác thực nghiệm chỉ đạt `62,07%` |
| **Multi-class Brier Score** *(nhỏ hơn là tốt hơn)* | **0,3334** | **0,7616** | Sai số toàn phương trung bình trên 10 lớp tăng gấp `2,28` lần khi xóa metadata |
| **Negative Log-Likelihood (`NLL`)** | **0,7295** | **2,7223** | Phạt nặng các dự đoán sai có xác suất cao ở chế độ xóa metadata |

> **Chứng minh thực nghiệm cho cảnh báo giao diện:** Ngay cả khi có đủ 22 metadata, các ca dự đoán sai vẫn có điểm softmax Top-1 trung bình tới **59,96%**, và ở nhóm `no-tumor` khi thiếu metadata, mô hình dự đoán sai `25/25` ca thành u xương với điểm tự tin trung bình **72,65%**. Đây là bằng chứng định lượng trực tiếp giải thích vì sao `rag/case_context.py` và giao diện `rag/demo_web/app.js` luôn gắn nhãn kết quả mô hình là **“điểm tương đối chưa hiệu chuẩn, không phải xác suất lâm sàng”**.

#### B. Độ chính xác và Hiệu chuẩn theo Tư thế chụp, Trung tâm, Vùng giải phẫu & Chế độ ánh xạ RAG (`250` ảnh)

| Nhóm phân tích (`Subgroup`) | Số ca (`n`) | Top-1 Acc (Đủ Meta) | Top-3 Acc (Đủ Meta) | Weighted-F1 (Đủ Meta) | Mean Top-1 Conf (Đủ Meta) | ECE 10-bin (Đủ Meta) | Brier Score (Đủ Meta) | Top-1 Acc (Zero Meta) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Tư thế chụp: `frontal` (Thẳng)** | 146 | **0,7740** | 0,9315 | 0,7732 | 0,7804 | 0,0664 | 0,3378 | 0,4863 |
| **Tư thế chụp: `lateral` (Nghiêng)** | 88 | **0,7841** | 0,9545 | 0,7802 | 0,8021 | 0,0797 | 0,3282 | 0,4773 |
| **Tư thế chụp: `oblique` (Chếch)** | 16 | **0,7500** | 0,9375 | 0,7438 | 0,7984 | 0,1327 | 0,3215 | 0,4375 |
| **Trung tâm: `Center 1`** | 173 | **0,8208** | 0,9595 | 0,8179 | 0,8293 | 0,0503 | 0,2899 | 0,4566 |
| **Trung tâm: `Center 2`** | 39 | **0,6923** | 0,8974 | 0,6883 | 0,7355 | 0,1469 | 0,4136 | 0,4359 |
| **Trung tâm: `Center 3`** | 38 | **0,6579** | 0,8947 | 0,6347 | 0,6616 | 0,1601 | 0,4493 | 0,6316 |
| **Vùng giải phẫu: `lower limb` (Chi dưới)** | 165 | **0,8000** | 0,9636 | 0,8016 | 0,8088 | 0,0624 | 0,3113 | 0,5091 |
| **Vùng giải phẫu: `pelvis` (Khung chậu)** | 28 | **0,7500** | 0,9286 | 0,7507 | 0,7367 | 0,0610 | 0,3229 | 0,5357 |
| **Vùng giải phẫu: `upper limb` (Chi trên)** | 57 | **0,7193** | 0,8772 | 0,7152 | 0,7581 | 0,0777 | 0,4024 | 0,3684 |
| **Ánh xạ RAG: `no_tumor` (`1` lớp)** | 25 | **1,0000** | 1,0000 | 1,0000 | 1,0000 | 0,0000 | 0,0000 | 0,0000 |
| **Ánh xạ RAG: `direct` (`4` lớp có nguồn)** | 100 | **0,8200** | 0,9600 | 0,8511 | 0,7921 | 0,0717 | 0,2720 | 0,6600 |
| **Ánh xạ RAG: `unresolved` (`3` lớp)** | 75 | **0,7867** | 0,9467 | 0,8622 | 0,8281 | 0,1226 | 0,3092 | 0,3733 |
| **Ánh xạ RAG: `aggregate` (`other bt`/`mt`)** | 50 | **0,5600** | 0,8600 | 0,7000 | 0,6196 | 0,1608 | 0,6592 | 0,5200 |

- **Nhận xét theo trung tâm (`Center 1–3`):** Độ chính xác giảm từ `Center 1` (`82,08%`) xuống `Center 2` (`69,23%`) và `Center 3` (`65,79%`). Nguyên nhân chính là `Center 1` chiếm `78,43%` bộ dữ liệu gốc, trong khi `Center 3` tập trung tỷ lệ lớn các ca nhãn gộp khó phân biệt (`other bt`, `other mt`).
- **Nhận xét theo chế độ ánh xạ RAG (`LABEL_GUIDE`):** Nhóm 4 lớp có nguồn RAG đối chiếu trực tiếp (`direct`: *osteochondroma*, *osteosarcoma*, *simple bone cyst*, *giant cell tumor*) đạt **Top-1 = 82,00%** và **Top-3 = 96,00%**, trong khi nhóm nhãn gộp (`aggregate`: `other bt`, `other mt`) chỉ đạt **Top-1 = 56,00%** (Brier score `0,6592`). Điều này củng cố quyết định thiết kế của `rag/case_context.py`: tự động truy xuất tài liệu có trích dẫn cho nhóm `direct`, nhưng dùng mẫu giải thích thận trọng cố định của máy chủ cho nhóm `aggregate` và `unresolved`.

---

## 4. Tổng hợp Kiểm chứng Phần mềm & Toàn vẹn Hồ sơ (Mốc 06/11/2026)

*Hồ sơ máy đọc được:* [`docs/reference/stage12_integrated_chatbot_verification_20261105.json`](../reference/stage12_integrated_chatbot_verification_20261105.json).

1. **Bộ kiểm thử tự động (`.\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q`):**
   - **176 passed, 132 subtests passed, 0 failed** (gồm kiểm thử API phân loại X-quang, kiểm thử hội thoại & định tuyến RAG, kiểm thử SQLite chat history, kiểm thử mock transport vision + 429 rate-limit wait header, kiểm thử DOM/route UI, kiểm thử phân tích catalogue/hiệu chuẩn xác suất, và kiểm thử tích hợp end-to-end với checkpoint `model/best_model.pt` thật + ảnh BTXRD thật).
2. **Kiểm tra cú pháp JavaScript (`node --check rag/demo_web/app.js`):** **PASS**.
3. **Kiểm toán Provenance Kho nguồn RAG (`.\.venv\Scripts\python.exe -m rag.audit --report-dir docs/reference/stage11_policy_rerun_20261029_cureus_abcrouting_v1`):**
   - **PASS** (`22` nguồn, `794` đoạn văn bản, vector index `794 × 384`, `10` tập đánh giá, `0` lỗi).
4. **Tái lập Tất định 16 Báo cáo Đánh giá (`.\.venv\Scripts\python.exe -m rag.replay_reports --bundle docs/reference/stage11_policy_rerun_20261029_cureus_abcrouting_v1`):**
   - **PASS** (`16/16` báo cáo khớp tuyệt đối, `0` preflight mismatch).
5. **Kiểm tra Toàn vẹn Register G1–G7 & G4 Cohort (`.\.venv\Scripts\python.exe -m tools.verify_stage11_registers`):**
   - **PASS** (`24/24` tệp tham chiếu khớp SHA-256, `15` ứng viên cohort được ghi nhận đầy đủ, **0/7 cổng nghiệm thu đóng (`OPEN`)**, `answer_ready = false`).
