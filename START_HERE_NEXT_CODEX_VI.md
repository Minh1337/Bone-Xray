# Bàn giao BoneScope cho phiên Codex tiếp theo

## Mốc mới nhất 09/11/2026 (21:57) — Báo cáo tổng kết đồ án và xác minh lại

Người dùng yêu cầu hoàn thiện dự án nhanh nhất. Đã chạy lại toàn bộ kiểm chứng: regression **202 passed / 132 subtests** (1 cảnh báo Starlette, provider giả lập), audit PASS 22 nguồn/794 chunks, replay PASS 16/16, register QA PASS 24 tham chiếu/7 gate OPEN, `tools.chatbot_doctor` PASS 13/13, `node --check` PASS. Hash nền khớp handoff. Bản ghi: [final_verification_20261109.json](docs/reference/final_verification_20261109.json). Mọi ghi chú “chưa chạy pytest” bên dưới đã được thay bằng kết quả này.

Sản phẩm bàn giao học tập: [báo cáo tổng kết đồ án (Markdown)](docs/reports/BAO_CAO_TONG_KET_DO_AN_BONESCOPE_20261109_VI.md) và bản DOCX cùng tên, xuất bằng `.\.venv\Scripts\python.exe -m tools.export_report_docx <md> <docx>` (có test `tests/test_export_report_docx.py`). Các công cụ cục bộ đã có: `tools.chatbot_doctor`, `tools.run_chatbot`/`08_start_chatbot.bat`, `tools.calibrate_retrieval_threshold` (đang `AWAITING_LABELS`), `tools.preview_rag_source`.

Phần kỹ thuật tự làm được đã xong. Phần còn lại cần người ngoài: nhãn reviewer cho retrieval/entailment và ngưỡng bước 7, cohort ảnh ngoài có quyền, intended-use lock và chữ ký G1–G7. G1–G7 OPEN, `answer_ready=false`.

## Trạng thái đã xác minh 09/11/2026

Nguyên mẫu chatbot hiện có các luồng chat/RAG, lịch sử SQLite chỉ lưu văn bản và nguồn, chat ảnh nhiều lượt tạm trong tab, nguồn đọc thêm sau phân tích ảnh, và phân loại ảnh BTXRD cục bộ với khớp metadata theo SHA-256. Toàn bộ regression offline mới nhất đạt **172 passed / 132 subtests passed**; audit RAG PASS, replay 16/16 PASS, register QA 24 tham chiếu/15 cohort. Kiểm tra Chrome headless mới đã PASS với AI/retrieval giả lập và SQLite/profile tạm: thử lại đúng ảnh sau lần lưu đầu, nhiều lượt ảnh, chuyển chat, xóa ngữ cảnh, reload/mở/đổi tên/xóa lịch sử, mobile và chế độ tối. Xem [record kèm hash implementation](docs/reference/chatbot_browser_regression_20261109.json). Smoke provider thật sau đó PASS: chat Free 3,343 giây; ảnh hình học qua Qwen 29,594 giây, một lượt Qwen trả phí, cost các phản hồi báo về $0,000248755 ([record](docs/reference/chatbot_provider_smoke_20261109.json)); không dùng ảnh X-quang hay dữ liệu người dùng. Các sửa trước về fallback, `/api/config` và bundle audit/replay vẫn được giữ.

**Tiến độ:** sáu trên bảy bước checklist kỹ thuật Giai đoạn 11 có artifact (xấp xỉ 86% độ bao phủ checklist hẹp); bước 7 chưa có ngưỡng retrieval được hiệu chỉnh độc lập. G1–G7 vẫn `OPEN`, `answer_ready=false`; browser và provider smoke cơ bản đã hoàn tất; còn thiếu bộ đánh giá độc lập, reviewer và hiệu chỉnh retrieval. Xem [báo cáo tiến độ đầy đủ](docs/reports/PROJECT_COMPLETION_STATUS_20261109_VI.md).

Trước khi tiếp tục, giữ nguyên các thay đổi chưa commit, `.env`, cơ sở dữ liệu SQLite và dữ liệu người dùng. Người dùng đã cho phép tuyến Qwen dự phòng; smoke cơ bản dùng quyền này đã được ghi riêng. Regression vẫn dùng mock; chỉ gọi provider thật khi cần, với input thử nghiệm tối thiểu và đối chiếu cost ở OpenRouter Activity. Bản cập nhật này không thay thế các gate học thuật.

Các ghi chú bên dưới được ghi trước lần xác minh này; mọi câu “chưa chạy test/browser” đã được cập nhật bằng kết quả 172/172 và browser smoke ở phần trên. Provider thật đã được thử riêng với input tối thiểu như record phía trên. Trong lượt tiếp nối đã sửa retry làm mất ảnh, giới hạn history ảnh 8 tin/9.000 ký tự, tiêu đề chat dính thông báo ảnh, hiển thị Markdown khi mở lịch sử và deadline UI chat chữ 110 giây. Không cần tạo checkpoint ZIP mới cho các thay đổi nhỏ này; giữ mã nguồn, record và các hồ sơ bàn giao hiện hành.

## Cập nhật 09/11/2026 — OpenRouter Free trước, Qwen trả phí khi chậm/lỗi

Yêu cầu hiện bắt đầu bằng model OpenRouter Free đã cấu hình (`openrouter/free` cho chat/RAG; Gemma 4 Free cho ảnh). Người dùng cho phép một fallback trả phí duy nhất: `qwen/qwen3.5-flash-02-23`. Nếu model Free timeout sau 15 giây, rate limit hoặc trả bản nháp incomplete, hệ thống chuyển sang Qwen; với Gemma ảnh rate limit, còn thử `openrouter/free` một lần trước. Qwen được khóa allowlist trong `rag/generation.py`; `.env` đặt đúng model và ngưỡng 15 giây. UI ghi rõ Qwen trả phí khi model này tạo phản hồi. Sau lỗi Qwen incomplete, mã mới cấp tối thiểu 2.400 token đầu ra và giới hạn phần suy luận Qwen ở 512 token (OpenRouter tính token suy luận vào output); lỗi `finish_reason=length` nay nêu rõ trần token. Ảnh gửi sang Qwen được tính phí theo input usage; xem mức tiêu thụ trong OpenRouter Activity. Groq vẫn tắt (`GROQ_FALLBACK_ENABLED=false`). Không in giá trị API key.

Chưa chạy pytest, browser smoke hoặc gọi API thật sau chỉnh sửa reasoning budget Qwen; cần dừng và khởi động lại FastAPI để nạp mã mới. Không chạy kiểm thử hoặc API trả phí trong phiên này; chỉ kiểm tra cú pháp và diff. Xem [hướng dẫn provider](docs/guides/OPENROUTER_CHATBOT_SETUP_VI.md). G1–G7 vẫn OPEN và `answer_ready=false`.

## Cập nhật 09/11/2026 — Vision chat nhiều lượt (chưa xác minh)

Ô chat hiện giữ ảnh đã đính kèm trong biến trang và gửi lại ở câu hỏi tiếp theo; bấm **Bỏ ảnh** để quay về chat chữ/RAG, tạo chat mới hoặc mở hội thoại lưu sẽ xóa ảnh khỏi tab. SQLite tiếp tục chỉ nhận câu chữ khái quát, không có byte ảnh. Cần kiểm tra thủ công trong browser: gửi ảnh, hỏi tiếp không đính kèm lần nữa, xác nhận ảnh được giữ tới lúc bỏ; xác nhận chat mới và mở lịch sử bỏ ngữ cảnh ảnh. Chưa chạy test, kiểm tra cú pháp hay gọi provider thật cho thay đổi này. Xem hướng dẫn [CHATBOT_CONVERSATION_VI.md](docs/guides/CHATBOT_CONVERSATION_VI.md).

## Cập nhật tiếp theo 09/11/2026 — Giảm bịa giải phẫu khi phân tích ảnh

Người dùng báo vision chat mô tả sai ảnh BTXRD (IMG000012.jpeg: nhầm vùng chậu thành xương sườn/khớp háng thành khớp gối và khẳng định không có dấu hiệu bất thường). File local đã khớp SHA-256 duy nhất với manifest; metadata nguồn xác nhận frontal và pelvis/hip bone. `/api/image-chat` nay chỉ thêm vùng/tư thế khi khớp hash duy nhất, không gửi nhãn ground-truth, tuổi hay giới tính; UI tách rõ metadata dataset khỏi quan sát của AI. Prompt yêu cầu phân biệt quan sát với diễn giải, cấm kết luận “bình thường/không có tổn thương” khi thiếu căn cứ và yêu cầu nêu bất định. Vision model đặt cố định `google/gemma-4-31b-it:free`; chat chữ vẫn dùng `openrouter/free`. Chưa chạy test, browser hoặc gọi API sau thay đổi. Hướng dẫn [giao diện chatbot](docs/guides/README_CHATBOT_UI_VI.md); G1–G7 OPEN, `answer_ready=false`.

Ghi chú lịch sử: sau lỗi 429 ảnh, lần sửa trước đã thử model vision Free rồi `openrouter/free`, nâng output 2.400 tokens cho router ảnh và giới hạn prompt 350 từ. Cấu hình đó đã được mở rộng theo yêu cầu mới bằng fallback Qwen trả phí nêu trên; cần kiểm tra lại phản hồi và cost trên ảnh thử nghiệm sau khi khởi động lại.

## Cập nhật 05/11–06/11/2026 — nạp ảnh BTXRD theo mã, tự khớp SHA-256 metadata, Vision Chat, phân tích Calibration/Subgroup & đồng bộ giao diện Pro Obsidian

Trong hộp thoại ca ảnh đã thêm nạp ảnh cục bộ bằng mã `IMG000001` từ manifest BTXRD (`GET /api/reference-images/{image_id}`), 6 chip chọn nhanh mẫu BTXRD tiêu biểu (`.btxrd-sample-chip`) và đối chiếu SHA-256 (`POST /api/case/metadata-match`) để tự điền 22 trường metadata. 9 nhóm trùng byte nhưng metadata mâu thuẫn bị chặn tự điền (`409 Conflict` / `ambiguous_metadata`). Lịch sử SQLite (`rag/chat_history.py`) được siết chống phản hồi đến muộn, từ chối tạo lại hội thoại đã xóa và không tự xóa lượt cũ khi đạt giới hạn. Giao diện `rag/demo_web/graphite.css` đã được hoàn thiện đồng bộ cho các thành phần đính kèm ảnh (`#attach-image`, `.image-attachment`, dán `Ctrl+V` / kéo–thả ảnh vào khung chat) và hộp thoại nạp mã BTXRD (`.case-reference-picker`, `#case-reference-load`, `#case-image-match-note`, `#ask-ai-about-case-image`). Toàn suite đạt **176 passed / 132 subtests passed**; offline RAG audit PASS (`22 nguồn / 794 chunks`), deterministic replay PASS (`16/16`), register QA PASS (`24/24` tham chiếu khớp SHA-256); phân tích định lượng toàn bộ catalogue BTXRD (`tools/analyze_btxrd_catalogue.py` → [`stage12_btxrd_catalogue_and_mapping_analysis_20261105.json`](docs/reference/stage12_btxrd_catalogue_and_mapping_analysis_20261105.json): 3.746 ảnh, 3.725 SHA-256 duy nhất, 21 nhóm trùng byte gồm 9 nhóm mâu thuẫn metadata và 12 nhóm trùng metadata, phân bố Center 1/2/3 = 2.938/549/259, 3.745/3.746 dòng có nhãn `ground_truth`, 3.746/3.746 tuân thủ quy tắc ≥1 vị trí & đúng 1 tư thế chụp); phân tích hiệu chuẩn xác suất softmax & nhóm con trên 250 ảnh phân tầng (`tools/analyze_xray_calibration_and_subgroups.py` → [`stage12_xray_subgroup_and_calibration_20261106.json`](docs/reference/stage12_xray_subgroup_and_calibration_20261106.json): `10-bin ECE = 0.0367`, `Brier = 0.3334` khi đủ 22 metadata so với `ECE = 0.2075`, `Brier = 0.7616` khi xóa metadata về 0; phân rã theo `frontal`/`lateral`/`oblique`, `Center 1–3`, vùng giải phẫu và trạng thái ánh xạ RAG); smoke API, trình duyệt thật và kiểm thử tích hợp end-to-end với checkpoint `model/best_model.pt` xác nhận nạp ảnh BTXRD theo mã + khớp 22 metadata + suy luận Top-3 hoạt động trọn vẹn; image-chat và thông báo chờ 429 (`retry-after` / `x-ratelimit-reset-tokens`) đã được kiểm tra bằng provider giả lập và mock transport. Chưa gọi mạng tới tài khoản provider thật trong pytest. Xem [bản ghi tiếp nối 05/11](docs/reference/chatbot_image_reference_followup_20261105.md), [báo cáo thực nghiệm tổng hợp Giai đoạn 12](docs/reports/STAGE12_EXPERIMENTAL_CHATBOT_AND_BTXRD_REPORT_VI.md) và [manifest kiểm chứng tổng hợp 05/11](docs/reference/stage12_integrated_chatbot_verification_20261105.json). G1–G7 OPEN, `answer_ready=false`. Các checkpoint cũ không chứa working tree mới; giữ nguyên thay đổi chưa commit, `.env` và SQLite của người dùng.

## Checkpoint mới nhất — 03/11/2026: Hoàn thiện Chatbot Tích hợp Ảnh X-quang + Metadata + RAG Đa Lượt (Giai đoạn 12 — Phạm vi Học tập Thực nghiệm)

Theo yêu cầu của người dùng hoàn thiện một chatbot thống nhất có thể **phân tích hình ảnh khung xương thực tế kèm 22 metadata và trả lời hội thoại đa lượt**, toàn bộ 7 hạng mục kỹ thuật (`P1`–`P7`) trong [Đánh giá khoảng trống 31/10/2026](docs/reports/PROJECT_GAP_ASSESSMENT_20261031_VI.md) đã được triển khai, kiểm thử và ghi nhận tại [bản ghi kiểm chứng tích hợp](docs/reference/stage12_integrated_chatbot_verification_20261103.json):

1. **Tích hợp X-ray + 22 Metadata vào Chatbot (`rag/case_context.py`, `rag/demo_api.py`, `rag/demo_web/`, `xray_api.py`):**
   - Dùng chung hàm `parse_metadata()` và `predict_upload()` giữa `xray_api.py` và `rag/demo_api.py` (kiểm tra định dạng ảnh, dung lượng ≤ 30 MiB, ≤ 25 triệu pixel, single-frame, 22 trường metadata hợp lệ: ít nhất 1/17 vị trí giải phẫu `== 1` và đúng 1/3 góc chụp `frontal`/`lateral`/`oblique` `== 1`).
   - `CaseStore` giữ ngữ cảnh ca trong RAM (`CASE_TTL_SECONDS = 1800`, tối đa 50 ca), không lưu ảnh hoặc metadata ra ổ đĩa, cấp `case_id` do server sở hữu (client không gửi điểm số).
   - Bảng `LABEL_GUIDE` ánh xạ minh bạch đủ **10 nhãn checkpoint** sang kho tri thức RAG:
     - `direct` (`osteochondroma`, `simple bone cyst`, `giant cell tumor`, `osteosarcoma`): tự động truy xuất tài liệu RAG cho khái niệm bệnh học tương ứng.
     - `unresolved` (`osteofibroma`, `synovial osteochondroma`, `multiple osteochondromas`): không tự động gán tương đương sang `osteofibrous dysplasia` / `synovial chondromatosis` / `osteochondroma` đơn độc; chỉ gợi ý chủ đề học thuật liên quan nếu người dùng tự chọn tìm hiểu.
     - `aggregate` (`other bt`, `other mt`) và `no_tumor` (`no-tumor`): giải thích theo mẫu cố định, không tự truy xuất bệnh cụ thể.
   - `llm_context(record)` tối thiểu hóa dữ liệu khi gọi LLM ngoài (chỉ gửi Top-3 nhãn/softmax, trạng thái ánh xạ và giới hạn; không gửi ảnh, tên tệp, tuổi, giới tính, vị trí giải phẫu hay mã băm).
   - Giao diện web `http://127.0.0.1:8765` hỗ trợ hộp thoại tải ảnh X-quang + 22 metadata (hoặc nạp nhanh từ `cases.json`), banner ca đang gắn ở đầu khung chat, nút giải thích ca tức thì (`POST /api/case/{case_id}/explain`), hỏi–đáp nối tiếp đa lượt (`POST /api/query` kèm `case_id`), tự động dọn `case_id` cũ khi đổi/xóa ca (`DELETE /api/case/{case_id}`) và xuất lịch sử Markdown kèm tóm tắt ca.
2. **Thực nghiệm định lượng & Ablation Cross-Attention Metadata (`tools/evaluate_xray_checkpoint.py`, [bản ghi JSON](docs/reference/stage11_xray_in_source_evaluation_20261103.json)):**
   - Đánh giá in-source có phân tầng trên **250 ảnh BTXRD** (25 ảnh × 10 lớp, `seed=20261031`, RTX 3050 Laptop GPU):
     - **Đủ 22 metadata thực:** Top-1 Accuracy = **0.7760** (194/250), Top-3 Accuracy = **0.9400** (235/250), Macro-F1 = **0.7759**, trung vị độ trễ = **25.2 ms/ảnh**.
     - **Ablation xóa metadata về 0 (`zeroed_metadata`):** Top-1 giảm còn **0.4800** (-29.6 điểm %), Top-3 giảm còn **0.7200** (-22.0 điểm %), Macro-F1 giảm còn **0.4389**, và **91/250 ảnh (36.4%) đổi nhãn dự đoán Top-1** (Recall của `no-tumor` và `synovial osteochondroma` sụp về `0.0`).
   - *Lưu ý provenance:* `model/metadata_processor.joblib` ghi nhận `n_samples_seen_ = 2616` (~69.8% của 3.746 dòng BTXRD) và BTXRD công khai không có cột `patient_id` để khôi phục `split_signature`, nên mọi số liệu trên BTXRD là **đánh giá nội nguồn & ablation kỹ thuật**, không phải kiểm định độc lập bên ngoài.
3. **Trạng thái kiểm chứng & ranh giới an toàn:**
   - Toàn bộ test suite (`api_tests`, `rag/tests`, `tests`, `ui_tests`): **162 passed, 132 subtests passed**.
   - Offline provenance audit (`cureus_abcrouting_v1`): **PASS** (`22 nguồn / 794 chunks`, `errors: []`).
   - Deterministic replay (`cureus_abcrouting_v1`): **PASS 16/16**.
   - Structural register QA (`tools.verify_stage11_registers`): **PASS** (24/24 artifact hashes khớp, 15 cohort leads, **7/7 cổng G1–G7 giữ `OPEN`**, `answer_ready = false`).

### Bổ sung kiểm chứng SQLite — 03/11/2026

Sau bản ghi tích hợp ở trên, luồng lịch sử chat SQLite được kiểm tra riêng: **49 kiểm thử liên quan đạt**, cùng browser smoke test gửi câu hỏi qua giao diện, lưu câu trả lời/nguồn, tải lại trang, mở lại và xóa. Đã dừng rồi khởi động lại tiến trình FastAPI trên cùng DB tạm và xác nhận câu trả lời/nguồn vẫn đọc được. Bản trả lời AI được giả lập; không gọi provider. Mọi kiểm thử dùng DB tạm và bản ghi thử đã xóa; DB thật của người dùng không bị đụng tới. Xem [bản ghi xác minh SQLite](docs/reference/chat_history_sqlite_verification_20261103.json).

Đã đổi khởi tạo schema sang FastAPI lifespan, chuẩn hóa khoảng trắng đầu/cuối trong service lưu, thêm kiểm thử SQLite và `conftest.py` để cô lập DB cho toàn bộ pytest. Bản ghi này bổ sung riêng, và toàn bộ hash mới đã được cập nhật trong manifest kiểm chứng tổng hợp [`docs/reference/stage12_integrated_chatbot_verification_20261105.json`](docs/reference/stage12_integrated_chatbot_verification_20261105.json) (đồng thời đồng bộ [`stage12_integrated_chatbot_verification_20261103.json`](docs/reference/stage12_integrated_chatbot_verification_20261103.json)); kiểm tra tự động không gọi Groq/OpenAI thật.

### Rà soát retrieval và bằng chứng — 03/11/2026

Đã đối chiếu read-only 16 report của bundle `cureus_abcrouting_v1` với hash dataset/corpus/config/index/evaluator/policy hiện hành; không có mismatch. Bộ stress song ngữ 20 câu đã xem cho exact-gold recall@5 **8/10 câu dương**, MRR **0,633**, negative abstention **10/10**; hai câu dương vẫn có candidate nhưng gold chunk đã gán không nằm trong top-5. Với câu hỏi dấu hiệu Ewing, một hit top-5 có câu tóm tắt liên quan nhưng độ hỗ trợ cần người chấm xác nhận; câu hỏi các loại sinh thiết không lấy được đoạn gold trong top-5. Vì vậy không thể coi exact-gold miss nào cũng là không có passage tương đương; cần reviewer xác lập evidence alternatives/groups. Bộ OFD dev có 5 câu dương/2 âm, recall@5 **5/5**, MRR **0,70**, nhưng câu hỏi và gold lấy từ nguồn vừa ingest. Đây là regression/dev agent-authored, không phải đánh giá mù.

Strict `EvidenceVerifier` dựa trên độ phủ từ vựng, không đo entailment: trên V2 test đã xem chặn nhầm **7/7** câu dương; OFD dev chặn nhầm **3/5**. Vì vậy tiếp tục để opt-in/tắt mặc định và không chỉnh threshold/ontology từ các bộ đã xem. Còn thiếu reviewer độc lập chấm claim-span ↔ passage (relevance, direct support, polarity, qualifiers, context), cũng như đánh giá câu trả lời do generator tạo. Dùng protocol và reviewer packet hiện có; không tạo gold mới từ chính test đã xem rồi gọi là độc lập. Tham khảo [thiết kế evidence checker](docs/reference/EVIDENCE_CHECK_DESIGN_VI.md), [bundle manifest](docs/reference/stage11_policy_rerun_20261029_cureus_abcrouting_v1/manifest.json) và [reviewer packet](docs/reference/STAGE11_REVIEWER_PACKET_VI.md).

### Luồng nhập ảnh chatbot — 03/11–05/11/2026

Đã chỉnh giao diện ô chat để đính kèm JPEG/PNG/WEBP và gửi câu hỏi cùng ảnh tới vision model theo provider; ảnh không lưu vào SQLite, chỉ ghi câu hỏi dạng tổng quát/câu trả lời. Trong hộp thoại Swin, backend đối chiếu hash ảnh với BTXRD manifest và trả metadata chỉ khi SHA-256 khớp chính xác (hoặc nạp theo mã `IMG000001`); ảnh unmatched có nút chuyển sang vision chat. Luồng vision mô tả ảnh, không tuyên bố nhãn u xương đã được kiểm định; không gửi ảnh bệnh nhân thật. Tùy chọn `.env`: `GROQ_VISION_MODEL=qwen/qwen3.8-27b`, `OPENAI_VISION_MODEL=gpt-5.4-mini`. Dữ liệu BTXRD đã có sẵn tại `data/external_datasets/BTXRD/` và archive hash khớp summary. Đã xác minh qua bộ kiểm thử tự động (**176 passed / 132 subtests**) và browser smoke local; chưa gọi mạng tới tài khoản provider thật trong pytest. G1–G7 OPEN, `answer_ready=false`.

Sau phản hồi 429 của Groq, luồng vision được giảm lịch sử gửi kèm (4 lượt × tối đa 800 ký tự), giới hạn output 1.200 tokens và dùng reasoning `none` cho Qwen để giảm token. Backend đọc `retry-after` hoặc `x-ratelimit-reset-tokens` để hướng dẫn thời gian chờ; không tự retry. Đã kiểm chứng tự động qua mock transport (`test_generate_image_answer_sends_data_url_and_reports_rate_limit_wait`).

---

**Phạm vi mới nhất do người dùng nêu:** [đề tài báo cáo học tập thực nghiệm](docs/reference/STAGE11_USER_STATED_EDUCATIONAL_SCOPE_20261029.md), không cung cấp cho bác sĩ hoặc người bệnh. Ưu tiên retrieval/provenance/demo và báo cáo nghiên cứu; [bảng đối chiếu 7 bước kỹ thuật](docs/reference/STAGE11_EDUCATIONAL_COMPLETION_MATRIX_20261029.md) tách tiến độ đồ án khỏi gate lâm sàng. [QA register có thể chạy lại](tools/verify_stage11_registers.py) với [record v6](docs/reference/stage11_gate_cohort_register_qa_20261029_v6.json) kiểm 24 tham chiếu, không thay ký duyệt.

**Thăm dò bước 7 mới nhất:** [score overlap record](docs/reference/stage11_similarity_overlap_probe_20261029.json) trên 28 câu đã xem cho thấy không thể chọn một ngưỡng dense cosine đơn để giữ trọn 17 câu dương và loại trọn 11 câu âm. Chạy lại bằng `.\.venv\Scripts\python.exe -m tools.probe_stage11_similarity --output docs/reference/stage11_similarity_overlap_probe_rerun.json` nếu cần; khi tái chạy không ghi đè artifact lịch sử, chọn tên record mới. Không sửa retrieval threshold mặc định từ bộ này.

**Cập nhật tiếp nối 29/10/2026:** người dùng đã yêu cầu tiếp tục Giai đoạn 11 sau điểm dừng bên dưới và hỏi khi nào xây chatbot. Xem [mốc chatbot và điều kiện](docs/reference/STAGE11_CHATBOT_READINESS_VI.md). Archive `20261029_pause_handoff` là snapshot tại điểm dừng; các thay đổi sau đó phải được kiểm tra trong working tree và checkpoint mới. Những câu “chưa nhận yêu cầu tiếp tục” phía dưới là lịch sử tại thời điểm lưu, không còn ngăn việc làm theo yêu cầu tiếp nối.

**Điểm dừng: 29/10/2026 (UTC+07). Người dùng yêu cầu lưu toàn bộ tiến trình và tạm ngưng goal.** Không chạy tiếp nghiên cứu, tuning hoặc triển khai Giai đoạn 11 khi chưa nhận yêu cầu tiếp tục. Hồ sơ trong thư mục dự án đủ để tiếp quản mà không cần lịch sử cuộc chat; trạng thái goal trong ứng dụng không tự chuyển sang chat mới.

## Đọc theo thứ tự

1. [Báo cáo Giai đoạn 11 hiện hành](docs/reports/BAO_CAO_GIAI_DOAN_11_2026-10-29.md) và [tiến độ](docs/STAGE11_PROGRESS_2026-10-29.md).
2. [Trạng thái bàn giao dạng JSON](docs/reference/stage11_pause_handoff_20261029.json), gồm Git HEAD, hash đầu vào, hồ sơ kiểm chứng, lệnh và danh sách việc còn mở.
3. [Kế hoạch thực thi](docs/STAGE11_EXECUTION_PLAN_VI.md), [blocker theo 7 gate](docs/reference/STAGE11_GATE_CLOSURE_BLOCKERS_VI.md) và [register nghiệm thu](docs/reference/stage11_acceptance_gate_status_20261029.csv).
4. [Handoff kỹ thuật](docs/STAGE11_HANDOFF_VI.md) và [reviewer packet](docs/reference/STAGE11_REVIEWER_PACKET_VI.md) khi cần chi tiết. Các đoạn v8, continuation_v2 và số liệu cũ là lịch sử; bundle hiện hành là `cureus_abcrouting_v1`.

## Trạng thái tại điểm dừng

- Chuẩn bị workspace **khoảng 85%**, là ước lượng quản lý, không phải tỷ lệ hoàn thành toàn bộ Giai đoạn 11. **Nghiệm thu 0/7 cổng (0%)**, tất cả OPEN; `answer_ready=false`.
- Corpus **22 nguồn / 794 chunks**, index **794×384**, model embedding `intfloat/multilingual-e5-small` với revision/hash trong index manifest. Bundle hiện hành: `docs/reference/stage11_policy_rerun_20261029_cureus_abcrouting_v1`.
- Regression gần nhất đã ghi: **87 passed / 132 subtests**, một cảnh báo Starlette; offline audit PASS; deterministic replay PASS **16/16**, không preflight mismatch. Lượt lưu/tạm dừng chỉ kiểm tra bảo toàn dữ liệu và hash, không chạy lại hay nâng mức bằng chứng của các kết quả đó.
- Đã lưu: nguồn có license/provenance, corpus/index, retrieval/routing, dev experiments, evidence diagnostics, evaluator, regression/audit/replay, biểu mẫu review và báo cáo. Strict evidence filter vẫn opt-in/tắt mặc định; lexical coverage không chứng minh entailment. Chưa có answer generator được nghiệm thu.
- G4 có **15 leads**, chưa cohort nào đủ điều kiện external evaluation. BTXRD nằm trong nguồn huấn luyện khai báo của checkpoint; thiếu split/patient mapping và rights-chain upstream. Không dùng BTXRD như external test của model hiện tại.
- Báo cáo Markdown ngày 29/10 là bản hiện hành; các DOCX cũ là snapshot lịch sử, chưa được cập nhật/kiểm tra bố cục lại.

## Các việc phải tiếp tục sau khi người dùng cho chạy lại

| Cổng | Công việc còn thiếu | Vai trò/bằng chứng cần có |
| --- | --- | --- |
| G1 | Khóa intended use theo từng chức năng, deployment và jurisdiction | Owner và reviewer liên quan ký scope thực tế; bản draft hiện tại chưa có hiệu lực |
| G2 | Freeze rubric/sampling trước khi xem labels; thu nhãn mù và adjudication | Reviewer lâm sàng độc lập, sampling manifest, nhãn thật, adjudication và release có chữ ký |
| G3 | Đánh giá support/entailment theo claim-span, polarity, qualifiers, context; đo false accept/refusal | Nhãn độc lập và adjudication; không thay bằng strict lexical checker |
| G4 | Làm rõ quyền từng ảnh, reference standard, patient-level manifest và overlap với checkpoint/pretraining | Custodian/rights holder/cohort auditor; chưa có cohort được cleared, không tự liên hệ bên ngoài |
| G5 | Hazard/use-error analysis theo intended use; verify controls và residual risk | Safety lead/reviewer ký; các prompt sơ bộ chưa phải safety approval |
| G6 | Xác minh deployment/data-flow, access control, retention/deletion, DB/WAL/backup và incident response | Privacy/security reviewer và owner ký; filename minimization chỉ là một kiểm soát nhỏ |
| G7 | Đọc đầy đủ nguồn pháp lý theo chức năng/jurisdiction/ngày vận hành, ghi applicability và pathway | Reviewer regulatory/counsel đủ thẩm quyền; source register chưa phải legal opinion |

G1 là dependency cần xử lý trước; G2/G3 cần người độc lập. Không tạo thêm tài liệu trùng lặp để thay cho bằng chứng thiếu. Nếu cải thiện code/retrieval, dùng dev riêng có provenance, không tune trên tập test đã xem hoặc blind set; cập nhật audit/replay/regression và báo cáo sau thay đổi. Nguồn online mới phải được kiểm tra lại ở primary/official source; lưu ngày, license, payload/hash và giới hạn. Không tự nâng `answer_ready` hoặc đổi gate thành CLOSED.

## Lệnh đối chiếu khi được yêu cầu tiếp tục

Chạy tại thư mục gốc của dự án. Trên máy hiện tại dùng Python trong `.venv`; Python hệ thống không đủ dependencies cho RAG. Khi chuyển máy, dựng lại môi trường theo README/requirements và đối chiếu [bản ghi phiên bản môi trường](docs/reference/stage11_environment_at_pause_20261029.json); `.venv` không nằm trong backup.

```powershell
git status --short
git log -3 --oneline
python -X utf8 checkpoints/20261029_pause_handoff/verify_resume_bundle.py
.\.venv\Scripts\python.exe -m rag.audit --output docs/reference/stage11_integrity_audit_YYYYMMDD_cureus_v1.json
.\.venv\Scripts\python.exe -m rag.replay_reports --output docs/reference/stage11_replay_YYYYMMDD_cureus_v1.json
.\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q
```

Các lệnh audit/replay mặc định hiện trỏ tới bundle đang dùng `cureus_abcrouting_v1`; record lịch sử `personal_image_jats_wrapper_v7` không còn được chọn làm mặc định. Dùng tên file ngày mới cho kết quả để không ghi đè record trước đó. Trước mọi rebuild, kiểm hash của corpus, config, source lock, index và model với JSON bàn giao; nếu khác, ghi nguyên nhân rồi tạo record mới, giữ nguyên record lịch sử. Trên chat Codex mới, chỉ tạo goal mới nếu người dùng yêu cầu; goal cũ được tạm ngưng trong chat hiện tại.

## Bản lưu để chuyển phiên/máy

Thư mục [checkpoints/20261029_pause_handoff](checkpoints/20261029_pause_handoff) gồm:

- `project_snapshot.zip` và `manifest.json`: source, tài liệu, test, model do Git theo dõi, cấu hình, corpus và source cache; SHA-256 từng file do checkpoint utility ghi.
- `assets_runtime.zip` và `assets_runtime_manifest.json`: index, model embedding, BTXRD đang có, kết quả/API artifacts, logs và bản SQLite nhất quán của dữ liệu runtime cục bộ. Đây là lưu trữ nội bộ, không phát hành lại dữ liệu hay xác nhận quyền tái sử dụng.
- `repository.bundle`: lịch sử và refs Git hiện có; thay đổi chưa commit nằm trong snapshot/patch, không nằm trong bundle Git.
- `bundle_manifest.json` và `verify_resume_bundle.py`: hash các thành phần và kiểm tra nội dung archive. SHA-256 của archive được lưu bên ngoài archive để tránh tự tham chiếu.

Giữ nguyên workspace hiện tại là cách tiếp quản nhanh nhất. Nếu chuyển máy, chép **toàn bộ thư mục checkpoint trên**, xác minh bằng script, rồi giải nén source và assets vào **thư mục mới** giữ nguyên relative paths. Nếu cần lịch sử Git, clone `repository.bundle` trước, rồi chép nội dung snapshot/patch lên checkout; đọc manifest để nhận biết thay đổi chưa commit. Không giải nén đè lên một checkout có công việc chưa sao lưu. Bộ ảnh/model/runtime được giữ cục bộ; không cần tải lại để khôi phục nội dung đã lưu. Môi trường Python, driver/CUDA, ứng dụng Codex và credentials phải thiết lập riêng; backup không chứa `.git` trực tiếp, `.venv`, installer/cache hệ thống hoặc các checkpoint cũ.

## Câu lệnh có thể gửi cho Codex khác

> Đọc AGENTS.md và START_HERE_NEXT_CODEX_VI.md trong dự án BONESCOPE. Tôi cho phép tiếp tục Giai đoạn 11 từ điểm tạm dừng ngày 29/10/2026. Đối chiếu hash và trạng thái thực tế trước khi sửa; tiếp tục các việc trong kế hoạch và blocker matrix, giữ answer_ready=false và không tự đóng gate/chứng nhận review độc lập. Lưu mọi thay đổi và bằng chứng vào dự án.

