# Tài liệu dự án BoneScope

**Bắt đầu tại [trạng thái và bàn giao hiện tại](PROJECT_STATUS_VI.md).** Tài liệu đó ghi những phần đã làm, bằng chứng kiểm tra, giới hạn và việc cần thực hiện tiếp.

| Tài liệu | Nội dung |
| --- | --- |
| [README tiếng Việt](../README_VI.md) | Cài đặt, khởi động, sử dụng và kiểm thử trên máy mới |
| [Trạng thái dự án](PROJECT_STATUS_VI.md) | Điểm bàn giao, thay đổi gần đây, kiểm thử và thứ tự phát triển tiếp |
| [Tiếp tục giai đoạn 11](STAGE11_HANDOFF_VI.md) | Điểm dừng, ca trượt, kết quả cuối và lệnh tái lập cho AI tiếp quản |
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
| `reference/api_reference_local.json` | Dữ liệu tham chiếu cho `verify_api.py` |
| [Báo cáo tiến độ](reports/Bao_cao_tien_do.docx) | Báo cáo Word v1.7, snapshot 27/10/2026; dùng [trạng thái dự án](PROJECT_STATUS_VI.md) và [handoff Stage 11](STAGE11_HANDOFF_VI.md) cho snapshot mới hơn 29/10/2026 |
| [Báo cáo Giai đoạn 11 — 29/10/2026](reports/BAO_CAO_GIAI_DOAN_11_2026-10-29.md) | Snapshot có dẫn nguồn về bằng chứng kỹ thuật, giới hạn, 7 cổng nghiệm thu và runbook đóng cổng; không phải sign-off lâm sàng |
| [Tài liệu phát triển](reports/Tai_lieu_phat_trien_du_an.docx) | Tài liệu Word nền tảng của dự án |

Các đường dẫn lệnh trong tài liệu được hiểu từ thư mục gốc `BONESCOPE/`, trừ khi có ghi khác.

Trạng thái code gần nhất đã commit: `d1ef896` (policy routing và bàn giao Giai đoạn 11). Đọc [trạng thái dự án](PROJECT_STATUS_VI.md) để xem các xác minh mới hơn và thay đổi tài liệu đang thực hiện.
RAG đã có corpus/index/retrieval CLI và các phép đánh giá thử nghiệm; chatbot
chưa được triển khai, `answer_ready` vẫn luôn `false`, và giai đoạn 11 chưa
được nghiệm thu để dùng làm nền trả lời y khoa.

Sau mỗi thay đổi chức năng hoặc kết thúc một giai đoạn, cập nhật `PROJECT_STATUS_VI.md` với việc đã làm, lệnh/kết quả kiểm thử, giới hạn và bước tiếp theo; cập nhật Completion Note của giai đoạn tương ứng khi đủ tiêu chí trong lộ trình. Nếu thay đổi đường dẫn, API hoặc cách chạy, sửa cả hướng dẫn liên quan và README gốc trong cùng lượt thay đổi.
