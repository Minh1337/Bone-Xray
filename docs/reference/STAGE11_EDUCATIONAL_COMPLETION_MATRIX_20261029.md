# Giai đoạn 11 theo mục tiêu báo cáo học tập thực nghiệm

**Ngày đối chiếu:** 29/10/2026. [Phạm vi người dùng xác định](STAGE11_USER_STATED_EDUCATIONAL_SCOPE_20261029.md): đề tài học tập, không cung cấp cho bác sĩ hoặc người bệnh. Bảng này đối chiếu đúng bảy bước kỹ thuật trong [lộ trình Giai đoạn 11](../LO_TRINH_THUC_HIEN_DU_AN_AI.md); trạng thái triển khai không phải bằng chứng về độ đúng y khoa.

| Bước lộ trình | Kết quả có thể trình bày trong đồ án | Giới hạn còn phải nêu |
| --- | --- | --- |
| 1. Chunk và metadata | Đã có corpus text-only 22 nguồn/794 chunks, source lock, URL/section/license và text hash; [audit](stage11_integrity_audit_20261029_cureus_abcrouting_v1.json) PASS. | Hash/provenance không xác nhận một đoạn thực sự hỗ trợ claim. |
| 2. Embedding có phiên bản | `intfloat/multilingual-e5-small`, revision và hash model/assets trong index manifest và [audit](stage11_integrity_audit_20261029_cureus_abcrouting_v1.json). | Tái lập artifact không đồng nghĩa tái lập tuyệt đối trên mọi môi trường phần cứng/phần mềm. |
| 3. Vector gắn chunk/source/model | Index NumPy 794×384, manifest chứa chunk IDs, model revision và hash corpus/source lock/vectors. | Đây là bộ chỉ mục của corpus văn bản hiện hành, không phải bằng chứng kiểm định lâm sàng. |
| 4. Build lại index | `rag.build_index` có quy trình build và kiểm cấu trúc/hash; [deterministic replay](stage11_replay_20261029_cureus_abcrouting_v1.json) PASS 16/16 report, không mismatch preflight. | Replay xác minh các artifact/report đã ghi; không phải phép thử mù mới hoặc xác nhận mọi bước download nguồn còn truy cập được. |
| 5. Retrieval evaluator | `rag.evaluate` tính Recall@k, MRR, abstention và các chẩn đoán; bundle hiện hành có 16 report. | Câu hỏi/nhãn dev đã xem hoặc do agent soạn; metric chỉ là thực nghiệm trong mẫu, không dùng làm accuracy y khoa. |
| 6. Câu hỏi dễ/khó/mơ hồ/ngoài phạm vi | Evaluation datasets và policy regression bao gồm câu dương, âm, ngoài phạm vi, yêu cầu diễn giải ảnh/cá nhân; full suite 94 passed/132 subtests theo [record](stage11_educational_scope_verification_20261029.json). | Độ bao phủ tình huống và nhãn chưa được reviewer độc lập khóa/đánh giá; không suy ra tính khái quát. |
| 7. Không đủ nguồn/score thấp | `retrieve()` có `out_of_scope` và `insufficient_evidence`; `min_score` tùy chọn lọc hit thấp, UI demo chỉ hiển thị candidates và giữ `answer_ready=false`. | **Chưa có ngưỡng similarity mặc định được hiệu chỉnh/kiểm định**. Một hit còn lại chỉ là candidate, không phải xác nhận đủ bằng chứng. Đây là phần chưa hoàn chỉnh theo nghĩa mạnh của bước 7. |

**Kết luận kỹ thuật cho báo cáo:** Có thể trình bày pipeline RAG, số liệu thực nghiệm và [demo tra cứu local](STAGE11_CHATBOT_READINESS_VI.md) ngay bây giờ, với các giới hạn trên. Bước 7 còn cần protocol/nhãn phù hợp nếu muốn khẳng định cơ chế từ chối theo ngưỡng; không đặt ngưỡng tùy tiện để biến mục này thành “đạt”. Chưa có LLM sinh câu trả lời học thuật. [Bảy gate trong register](stage11_acceptance_gate_status_20261029.csv) vẫn OPEN và theo dõi claims/triển khai vượt phạm vi demo; **0/7 không phải phần trăm hoàn thành đồ án học tập**. Không tự đánh dấu gate CLOSED/N/A hoặc đổi `answer_ready`.

### Thăm dò ngưỡng similarity trên bộ đã xem

Chạy lại với tên record mới, ví dụ `.\.venv\Scripts\python.exe -m tools.probe_stage11_similarity --output docs/reference/stage11_similarity_overlap_probe_rerun.json`. [Record có hash đầu vào và 28 quan sát](stage11_similarity_overlap_probe_20261029.json) ghi 17 câu dự kiến có candidates và 11 câu dự kiến từ chối. Điểm cosine dense top-1 thấp nhất của nhóm dương là **0,8003**; cao nhất của nhóm âm là **0,9087**. Hai miền điểm chồng nhau, nên **không tồn tại một ngưỡng đơn toàn cục** vừa giữ tất cả 17 câu dương vừa loại tất cả 11 câu âm trong chính bộ này. Policy hiện từ chối được một số câu âm bằng routing độc lập với score. Đây là bộ do agent soạn, đã xem và có split `test` cũng đã xem; kết quả chỉ giải thích vì sao không đặt ngưỡng mặc định từ dữ liệu hiện tại, không phải phép hiệu chỉnh hay đánh giá độc lập.



