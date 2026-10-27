# Tài liệu dự án BoneScope

**Bắt đầu tại [trạng thái và bàn giao hiện tại](PROJECT_STATUS_VI.md).** Tài liệu đó ghi những phần đã làm, bằng chứng kiểm tra, giới hạn và việc cần thực hiện tiếp.

| Tài liệu | Nội dung |
| --- | --- |
| [Trạng thái dự án](PROJECT_STATUS_VI.md) | Điểm bàn giao, thay đổi gần đây, kiểm thử và thứ tự phát triển tiếp |
| [Tiếp tục giai đoạn 11](STAGE11_HANDOFF_VI.md) | Điểm dừng, ca trượt, kết quả cuối và lệnh tái lập cho AI tiếp quản |
| [Lộ trình thực hiện](LO_TRINH_THUC_HIEN_DU_AN_AI.md) | Tiêu chí và mẫu Completion Note cho từng giai đoạn |
| [Hướng dẫn kiểm tra model](guides/README_VI.md) | Môi trường Windows và kiểm tra suy luận |
| [Hướng dẫn API](guides/README_FASTAPI_VI.md) | API phân loại ảnh |
| [Hướng dẫn UI](guides/README_UI_VI.md) | Giao diện ứng dụng |
| [Kho nguồn RAG](guides/README_RAG_CORPUS_VI.md) | Thu thập, chia đoạn và quản lý nguồn |
| [Chỉ mục RAG](guides/README_RAG_INDEX_VI.md) | Embedding, truy xuất và kết quả đánh giá |
| `reference/api_reference_local.json` | Dữ liệu tham chiếu cho `verify_api.py` |
| [Báo cáo tiến độ](reports/Bao_cao_tien_do.docx) | Báo cáo Word bản 1.3, gồm Completion Note giai đoạn 10–11, kết quả rerank/lọc thử nghiệm và điểm tiếp tục |
| [Tài liệu phát triển](reports/Tai_lieu_phat_trien_du_an.docx) | Tài liệu Word nền tảng của dự án |

Các đường dẫn lệnh trong tài liệu được hiểu từ thư mục gốc `BONESCOPE/`, trừ khi có ghi khác.

Sau mỗi thay đổi chức năng hoặc kết thúc một giai đoạn, cập nhật `PROJECT_STATUS_VI.md` với việc đã làm, lệnh/kết quả kiểm thử, giới hạn và bước tiếp theo; cập nhật Completion Note của giai đoạn tương ứng khi đủ tiêu chí trong lộ trình. Nếu thay đổi đường dẫn, API hoặc cách chạy, sửa cả hướng dẫn liên quan và README gốc trong cùng lượt thay đổi.
