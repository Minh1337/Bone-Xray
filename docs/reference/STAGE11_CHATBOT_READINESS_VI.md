# Khi nào BoneScope có thể trở thành chatbot?

**Cập nhật 10/11/2026:** BoneScope hiện đã là chatbot học tập local có generator OpenRouter, hội thoại nhiều lượt, lịch sử SQLite text-only, Vision Chat trong phiên tab và retrieval nguồn. Mốc **“thêm generator” đã hoàn thành về tích hợp kỹ thuật**; Mốc 2 chưa được xác minh độc lập về claim-to-span/citation entailment, chất lượng, safety hoặc tính khái quát. Mốc 3 (phân tích ca/ảnh như sản phẩm) vẫn chưa đủ dữ liệu ngoài, reviewer hay nghiệm thu. Tiến độ/giới hạn hiện hành nằm trong [báo cáo hoàn thiện](../reports/PROJECT_COMPLETION_STATUS_20261109_VI.md) và [quy trình thực nghiệm](../guides/RESEARCH_WORKFLOW_VI.md); những snapshot ngày 03/11 bên dưới là lịch sử.

**Cập nhật mới nhất — 03/11/2026 (Đã hoàn thiện Nguyên mẫu Chatbot Học tập Tích hợp X-quang + Metadata + RAG Đa Lượt):**
- Trong phạm vi [báo cáo học tập thực nghiệm](STAGE11_USER_STATED_EDUCATIONAL_SCOPE_20261029.md), giao diện `rag.demo_api` (`http://127.0.0.1:8765`) đã được nâng cấp thành **chatbot tích hợp đa lượt**:
  1. **Hội thoại văn bản đa lượt có ngữ cảnh (`rag/conversation.py`, `rag/generation.py`):** viết lại câu hỏi nối tiếp độc lập, giữ trích dẫn `[S1]`, `[S2]` khớp đoạn nguồn, hỗ trợ 3 chế độ trả lời (`auto`, `extractive`, `llm`) và vẫn giữ `answer_ready = false`.
  2. **Phân tích ca ảnh X-quang + 22 metadata trực tiếp trong khung chat (`rag/case_context.py`, `POST /api/case`, `POST /api/case/{case_id}/explain`):** tái sử dụng `BestModelPredictor` (`model/best_model.pt`), lưu ngữ cảnh ca trong RAM (`CaseStore`, TTL 30 phút, không ghi ảnh/metadata xuống đĩa), ánh xạ minh bạch 10 nhãn checkpoint (`LABEL_GUIDE`: 4 nhãn `direct`, 3 nhãn `unresolved`, 2 nhãn `aggregate`, 1 nhãn `no_tumor`), và gắn `case_id` do server cấp cho các câu hỏi nối tiếp.
  3. **Kiểm chứng (`stage12_integrated_chatbot_verification_20261103.json`):** `162 passed / 132 subtests passed`, offline audit PASS, replay 16/16 PASS, structural QA 24/24 PASS. Cả 7 cổng nghiệm thu lâm sàng G1–G7 vẫn giữ `OPEN` vì đây là nguyên mẫu học tập thực nghiệm local, không phải thiết bị hay dịch vụ tư vấn y tế.

**Phạm vi đã được người dùng làm rõ:** đề tài là [báo cáo học tập thực nghiệm](STAGE11_USER_STATED_EDUCATIONAL_SCOPE_20261029.md), không cung cấp cho bác sĩ hay người bệnh. Với mục tiêu đó, bản tra cứu nội bộ bên dưới đã là một **demo giao diện hỏi–đáp về nguồn tài liệu**. Không cần đợi 7 gate lâm sàng mới có thể trình bày demo học tập. Các mốc chatbot sinh lời giải y khoa/đọc ca thực phía dưới chỉ là lộ trình giả định nếu sau này đổi mục đích, không phải yêu cầu hiện tại của đề tài.

## Bản tra cứu nội bộ đã hiện thực

Đã thêm `rag/demo_api.py` và `rag/demo_web/` làm giao diện hỏi–đáp **chỉ hiển thị đoạn nguồn**. API giới hạn Host vào localhost/127.0.0.1, từ chối Origin khác trang và fail-closed nếu status mâu thuẫn với số đoạn trả về. Chạy trong thư mục gốc:

Bản hiện hành giữ một `Retriever`/embedding model trong tiến trình và tuần tự hóa các lượt truy xuất; sửa corpus/index/model/config cần khởi động lại dịch vụ và chạy lại audit. Smoke check trên máy này quan sát 14,39 giây cho lượt đầu và 0,05 giây cho lượt thứ hai, **không phải benchmark hiệu năng**. [Bản ghi v3](stage11_chat_demo_verification_20261029_v3.json) lưu hash và giới hạn.

```powershell
.\.venv\Scripts\python.exe -m rag.demo_api
```

Mở `http://127.0.0.1:8765` trên cùng máy. API `/api/query` dùng `rag.retrieval.retrieve()` có routing hiện hành, giới hạn câu hỏi 1.000 ký tự và top-5, không tải ảnh, không lưu lịch sử hoặc sinh câu trả lời. UI hiển thị ID đoạn, nguồn, giấy phép và SHA-256 văn bản; chỉ mở link `https://`. Giao diện là **research-only** và chỉ bind loopback theo lệnh chạy trên. Không nhập dữ liệu bệnh nhân vào bản thử nghiệm. [Bản ghi kiểm chứng mới](stage11_chat_demo_verification_20261029_v2.json) ghi regression, audit/replay, smoke check và hash khi chốt.

**Cập nhật 29/10/2026 — quyết định kỹ thuật, chưa phải phê duyệt triển khai.** Người dùng đã yêu cầu tiếp tục Giai đoạn 11 và hỏi mốc xây chatbot. Bản tra cứu nội bộ đã có giao diện riêng; chatbot diễn giải y khoa cho người dùng thực vẫn cần đánh giá. Cả 7 acceptance gate của Stage 11 hiện OPEN, `answer_ready=false`.

## Mốc 1 — bản thử nghiệm nội bộ về tài liệu: có thể bắt đầu trong Giai đoạn 11

`rag/retrieval.py` hiện nhận câu hỏi và trả về danh sách đoạn nguồn cùng metadata hoặc `insufficient_evidence`/`out_of_scope`. Giao diện tra cứu riêng đã xây như trên, không tổng hợp thành lời khuyên y khoa; giao diện phân loại ảnh `xray_web/index.html` vẫn chưa tích hợp chat. Bản thử nghiệm giới hạn ở câu hỏi giáo dục/kiểm tra phần mềm trên dữ liệu tổng hợp, chạy local, có chỉ dẫn rõ khi từ chối hoặc không đủ bằng chứng. Bản hiện hành không lưu từng lượt; muốn lập log đánh giá phải thiết kế riêng quyền/retention và ghi version/hash corpus, index, model, config, ID đoạn và trạng thái routing. API dùng `retrieve()`, không dùng raw `search()` để bỏ qua policy; không diễn giải score như xác suất lâm sàng.

**Kiểm chứng hiện tại:** API/UI trả đoạn cho `candidates_found`, trống cho `out_of_scope` và câu hỏi ảnh cá nhân; test fail-closed khi status không hợp lệ, hit xuất hiện sau khi từ chối hoặc status có nguồn nhưng không có đoạn. Đã chạy full regression **92 passed/132 subtests**. Audit PASS và replay 16/16 PASS của retrieval nền được chạy trước thay đổi cache ở demo; fingerprint retrieval/policy/corpus/config/index không đổi sau đó. Kiểm JS syntax ở bản giao diện hiện tại. Đây vẫn là prototype; cần đánh giá thêm các ca lỗi runtime/model/index và kiểm thử với người dùng trước bất kỳ bản phát hành nào. Không cần đợi đủ bảy chữ ký chỉ để phát triển prototype trên dữ liệu được phép trong môi trường nội bộ, nhưng phải tuân phạm vi do owner đặt ra và không dùng thông tin bệnh nhân chưa được phép. Không đổi `answer_ready=false`.

## Mốc 2 — chatbot tạo câu trả lời bằng ngôn ngữ tự nhiên: đã tích hợp, đang chờ đánh giá độc lập

Generator đã được tích hợp trong `rag/generation.py`; retrieval vẫn trả **candidate passages**, không tự xác nhận rằng chúng hỗ trợ câu trả lời được sinh. Để nâng chất lượng claim, mỗi câu trả lời cần được review theo từng claim với exact source span/citation, provenance và phiên bản nguồn; chấm polarity, điều kiện, qualifier và phạm vi. Strict lexical filter vẫn là thử nghiệm opt-in, không đo entailment và không thay thế review độc lập. Hướng dẫn ghi nhãn mới nằm ở [addendum review generator](STAGE11_GENERATOR_REVIEW_ADDENDUM_20261110.md).

Trước khi đưa ra claim rằng generator đáng tin cậy hoặc mở rộng người dùng/phạm vi, cần đánh giá mù độc lập và adjudication (G2), claim-to-span support/entailment và false acceptance/refusal (G3), safety scenarios và controls (G5), privacy/security theo deployment (G6), cùng quyết định G1/G7 theo mục đích và jurisdiction. Hiện chưa có nhãn/reviewer độc lập hay sign-off cho các tiêu chí đó. Không lấy metric dev đã xem làm tỷ lệ an toàn. Khi đổi prompt/model/corpus, khóa version và đánh giá lại theo protocol tương ứng.

## Mốc 3 — chatbot trả lời về ca bệnh hoặc ảnh X-quang thực: chỉ sau nghiệm thu chức năng tích hợp

Classifier ảnh hiện trả nhãn và softmax; chưa có kiểm định độc lập phù hợp cho việc diễn giải ca thực hoặc liên kết ảnh với lời giải thích chatbot. Cần làm rõ quyền ảnh và độc lập của cohort, reference standard, patient-level split/overlap và đánh giá external phù hợp (G4); thêm hazard phân nhánh ảnh + RAG + generator (G5), data flow/retention/access control (G6), intended use và regulatory pathway (G1/G7). Đủ các artifact/code/test không thay cho quyết định của reviewer có thẩm quyền. **Hiện chưa có mốc ngày có thể cam kết cho Mốc 2 hoặc 3** vì thiếu reviewer, blind labels, cohort đủ quyền và sign-off.

| Tính năng | Có thể làm khi nào | Trạng thái hiện tại |
| --- | --- | --- |
| Tra cứu theo lượt hỏi, hiển thị passage/citation như một màn hình chat nội bộ | Trong Stage 11 | Bản local research-only đã chạy và qua smoke check; chưa có đánh giá độc lập |
| Tạo câu trả lời văn bản về kiến thức chung | Generator đã tích hợp cho demo học tập; trước khi nâng claim chất lượng cần review claim-to-span, retrieval, safety/privacy và đánh giá theo scope | Đã có generator; chưa có đánh giá độc lập về entailment/chất lượng hoặc sign-off |
| Trả lời về ảnh/ca người bệnh và dùng ngoài nghiên cứu nội bộ | Sau khi đủ bằng chứng, quyền, đánh giá và phê duyệt cho chức năng tích hợp trong jurisdiction đích | 0/7 gate đóng; không đủ điều kiện |

## Việc gần nhất có ích

1. Owner chọn và ghi rõ Mốc 1 là prototype local, tập người thử và dữ liệu được phép; nếu muốn sản phẩm y khoa, khóa intended use riêng cho Mốc 2/3 (G1).
2. Xây UI/API tra cứu có provenance và abstention, kiểm thử policy bằng trường hợp dương/âm và failure paths. Không đặt tên output `answer` hoặc bật `answer_ready` khi chỉ có candidates.
3. Song song, giao protocol G2/G3 cho reviewer độc lập để thu nhãn thật; mốc này quyết định khi nào có thể bắt đầu đánh giá generator, thay vì đo bằng phần trăm chuẩn bị workspace.

Nguồn trạng thái: [intended-use draft](STAGE11_INTENDED_USE_DRAFT_FOR_OWNER_REVIEW_20261029.md), [gate register](stage11_acceptance_gate_status_20261029.csv), [blocker matrix](STAGE11_GATE_CLOSURE_BLOCKERS_VI.md), [execution plan](../STAGE11_EXECUTION_PLAN_VI.md), `rag/retrieval.py`, `xray_web/index.html`.
