# Tài liệu dự án BoneScope

**Giai đoạn 11 đã được tiếp tục sau lần tạm dừng 29/10/2026:** bắt đầu tại [bàn giao cho Codex tiếp theo](../START_HERE_NEXT_CODEX_VI.md), gồm trạng thái hiện hành, việc còn mở, lệnh xác minh và backup source/model/data. [Bảng đối chiếu đề tài học tập](reference/STAGE11_EDUCATIONAL_COMPLETION_MATRIX_20261029.md) tách 7 bước kỹ thuật khỏi gate triển khai lâm sàng.

**Bắt đầu tại [trạng thái và bàn giao hiện tại](PROJECT_STATUS_VI.md).** Tài liệu đó ghi những phần đã làm, bằng chứng kiểm tra, giới hạn và việc cần thực hiện tiếp.

## Trạng thái hiện hành

BoneScope hiện là nguyên mẫu nghiên cứu giáo dục chạy cục bộ, gồm pipeline phân loại X-quang, Research Studio, hội thoại RAG và chatbot ảnh nhiều lượt. Bản kiểm chứng gần nhất ghi nhận `209 passed`, audit RAG `22 nguồn / 794 chunks`, replay xác định `16/16`, và chatbot doctor `13/13`. Đây là kiểm thử phần mềm và tính toàn vẹn artifact; không phải kiểm định lâm sàng hoặc đánh giá độc lập.

`answer_ready=false`, ngưỡng retrieval vẫn `AWAITING_LABELS`, và cả 7 acceptance gates vẫn `OPEN`. Không sử dụng hệ thống để chẩn đoán, triage, theo dõi hoặc điều trị.

Để chạy nhanh trên máy mới, đọc [README tiếng Anh](../README.md) hoặc [README tiếng Việt](../README_VI.md). Để tiếp quản công việc kỹ thuật, đọc [trạng thái dự án](PROJECT_STATUS_VI.md), [quy trình nghiên cứu](guides/RESEARCH_WORKFLOW_VI.md) và [bản bàn giao](../START_HERE_NEXT_CODEX_VI.md).

| Tài liệu | Nội dung |
| --- | --- |
| [README tiếng Việt](../README_VI.md) | Cài đặt, khởi động, sử dụng và kiểm thử trên máy mới |
| [Trạng thái dự án](PROJECT_STATUS_VI.md) | Điểm bàn giao, thay đổi gần đây, kiểm thử và thứ tự phát triển tiếp |
| [Tiếp tục giai đoạn 11](STAGE11_HANDOFF_VI.md) | Điểm dừng, ca trượt, kết quả cuối và lệnh tái lập cho AI tiếp quản |
| [Mốc và bản tra cứu chatbot nội bộ](reference/STAGE11_CHATBOT_READINESS_VI.md) | Cách chạy prototype local và điều kiện cho chatbot tạo câu trả lời |
| [Phạm vi học tập do người dùng xác định](reference/STAGE11_USER_STATED_EDUCATIONAL_SCOPE_20261029.md) | Mục tiêu báo cáo thực nghiệm, giới hạn dùng và quyết định intended-use còn cần khóa |
| [Hồ sơ review Stage 11](reference/STAGE11_REVIEWER_PACKET_VI.md) | 7 acceptance gates, intended-use, independent review và trạng thái open |
| [Sàng lọc phạm vi quy định và quản lý AI](reference/STAGE11_REGULATORY_APPLICABILITY_REVIEW_VI.md) | Nguồn FDA/IMDRF/NIST cập nhật, phân biệt draft/final và checklist chuyển giao theo chức năng; không phải phân loại pháp lý |
| [Crosswalk reporting guideline AI/y tế (trọng tâm STARD-AI)](reference/STAGE11_STARD_AI_REPORTING_CROSSWALK_VI.md) | Chọn checklist theo study aim/design, gồm diagnostic accuracy, LLM, trial theo nhóm tuổi/AI và disclosure GAMER; không dùng thay benchmark RAG retrieval-only |
| [CSV checklist STARD-AI trắng](reference/stage11_stard_ai_reporting_checklist_template_20261029.csv) | 40 mục/48 dòng phản hồi (+header = 49 dòng); CC BY accepted-manuscript wording, có attribution, chưa điền |
| [Intended-use lock template](reference/STAGE11_INTENDED_USE_LOCK_TEMPLATE_VI.md) | Xác nhận phạm vi theo chức năng trước safety/privacy/regulatory review |
| [Safety hazard-analysis guide](reference/STAGE11_SAFETY_REVIEW_GUIDE_VI.md) | Hazard/use-error prompts, control verification và residual-risk sign-off |
| [Privacy/security closeout worksheet](reference/STAGE11_PRIVACY_SECURITY_GATE_TEMPLATE_VI.md) | Bằng chứng, owner, gap, quyết định và chữ ký theo data-governance scope |
| [Lộ trình thực hiện](LO_TRINH_THUC_HIEN_DU_AN_AI.md) | Tiêu chí và mẫu Completion Note cho từng giai đoạn |
| [Hướng dẫn kiểm tra model](guides/README_VI.md) | Môi trường Windows và kiểm tra suy luận |
| [Hướng dẫn API](guides/README_FASTAPI_VI.md) | API phân loại ảnh |
| [Hướng dẫn UI](guides/README_UI_VI.md) | Giao diện ứng dụng |
| [Kho nguồn RAG](guides/README_RAG_CORPUS_VI.md) | Thu thập, chia đoạn và quản lý nguồn |
| [Chỉ mục RAG](guides/README_RAG_INDEX_VI.md) | Embedding, truy xuất và kết quả đánh giá |
| `reference/api_reference_local.json` | Dữ liệu tham chiếu cho `python -m bonescope.verify_api` |
| [Báo cáo tiến độ](reports/Bao_cao_tien_do.docx) | Báo cáo Word lịch sử, snapshot 27/10/2026; không phải trạng thái hiện hành |
| [Báo cáo Giai đoạn 11 — 29/10/2026](reports/BAO_CAO_GIAI_DOAN_11_2026-10-29.md) | Snapshot có dẫn nguồn về bằng chứng kỹ thuật, giới hạn, 7 cổng nghiệm thu và runbook đóng cổng; không phải sign-off lâm sàng |

Các đường dẫn lệnh trong tài liệu được hiểu từ thư mục gốc `BONESCOPE/`, trừ khi có ghi khác.

Các file trong `docs/reference/` mang ngày và phiên bản vì lưu bằng chứng lịch sử,
record hash và kết quả tái lập. Không xóa hoặc gộp các record này chỉ để giảm số
file nếu chưa cập nhật các liên kết, manifest và báo cáo phụ thuộc vào chúng.

Sau mỗi thay đổi chức năng hoặc kết thúc một giai đoạn, cập nhật `PROJECT_STATUS_VI.md` với việc đã làm, lệnh/kết quả kiểm thử, giới hạn và bước tiếp theo; cập nhật Completion Note của giai đoạn tương ứng khi đủ tiêu chí trong lộ trình. Nếu thay đổi đường dẫn, API hoặc cách chạy, sửa cả hướng dẫn liên quan và README gốc trong cùng lượt thay đổi.
