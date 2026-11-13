# Checklist nghiệm thu BoneScope — phạm vi đồ án học tập

**Phiên bản:** 13/11/2026

**Phạm vi:** demo local cho báo cáo học tập/thực nghiệm; không dùng cho bác sĩ, người bệnh hoặc quyết định y khoa.

Checklist này giúp người dùng và người hướng dẫn nghiệm thu các luồng phần mềm có thể trình diễn. Nó không phải xác nhận độ chính xác y khoa, kiểm định độc lập, giấy phép dữ liệu, phê duyệt bảo mật/pháp quy hay đóng các gate G1–G7.

## 1. Kết quả kiểm tra đã có

| Hạng mục | Bằng chứng hiện hành | Kết luận cho nghiệm thu demo |
|---|---|---|
| Regression phần mềm | Chạy lại 13/11: 216 passed, 0 failed, 1 skipped; 227 subtests passed | PASS_WITH_ENVIRONMENT_SKIP; xem [record báo cáo 13/11](../reference/project_report_verification_20261113.json) |
| API phân loại ảnh | 3/3 ca parity; hash model khớp; metadata thiếu và ảnh hỏng bị từ chối | PASS theo record; đây là parity kỹ thuật, không phải đánh giá độ đúng y khoa |
| RAG audit và replay | 22 nguồn/794 chunks, 0 source cache thiếu; replay 16/16, không mismatch | PASS về provenance/cấu trúc/tái lập, không chấm entailment |
| Chatbot doctor | Chạy lại 12/11: 13/13 kiểm tra cấu hình local đạt | PASS; chỉ kiểm tra cục bộ, không gọi provider |
| DOCX report | Exporter 2/2 test đạt; bản 13/11 được xuất PDF bằng Word và xem từng trang | PASS bố cục chín trang; renderer chuẩn thiếu LibreOffice trên máy này |
| Browser smoke | 13/11: 1 bài đạt khi chạy riêng ngoài sandbox với Chrome, SQLite tạm, ảnh tổng hợp và AI giả lập | Đã xác nhận ảnh hiện trong tin nhắn, lịch sử, đổi tên, xóa và giao diện di động |
| Acceptance gate | G1–G7: 7 OPEN, 0 CLOSED; answer_ready=false | Giữ nguyên; checklist demo này không thay thế gate |

**Rà soát bổ sung 12/11:** bộ regression trong sandbox đạt 213 bài, 1 bài bị bỏ qua vì tiến trình GPU của Chrome dừng trước khi mở ứng dụng. Bài Chrome chạy riêng ngoài sandbox đạt 1/1. Chatbot doctor đạt 13/13, kiểm tra cấu trúc Giai đoạn 11 đạt, RAG audit đạt (22 nguồn, 794 đoạn), replay khớp 16/16 và kiểm tra checkpoint bằng CPU đạt 3/3 ca mẫu. Đã sửa mã thoát của hai launcher X-quang và bổ sung quy tắc Git bỏ qua tệp SQLite journal, WAL và SHM.

**Cập nhật 13/11:** kiểm tra lại mã hiện hành đạt 216 bài, 1 skip, 227 subtests; Chrome riêng đạt 1/1. Audit nguồn và replay 16/16 đạt; 7 gate vẫn OPEN. Các số của 12/11 ở trên là snapshot lịch sử.

## 2. Kiểm tra trực tiếp trước buổi nghiệm thu

Chạy tại PowerShell trong thư mục gốc dự án:

~~~powershell
.\.venv\Scripts\python.exe -m tools.chatbot_doctor
.\.venv\Scripts\python.exe -m tools.run_chatbot
~~~

Mở http://127.0.0.1:8765. Giữ terminal đang chạy để xem lỗi và dừng server bằng Ctrl+C. Không đổi host thành 0.0.0.0 hoặc mở cổng ra mạng công cộng.

| # | Thao tác nghiệm thu | Kết quả mong đợi | Đạt |
|---:|---|---|:---:|
| 1 | Tạo cuộc trò chuyện mới, gửi “Xin chào” | Chatbot phản hồi như hội thoại; không buộc truy xuất tài liệu cho lời chào | ☐ |
| 2 | Chọn **Tra cứu cục bộ** hoặc bấm **Tra cứu osteochondroma** ở màn hình chào | Hiện thẻ đoạn nguồn sau khi chỉ mục đã được dựng. Có thể mở đoạn và liên kết gốc mà không cần API key | ☐ |
| 3 | Hỏi về điều trị hoặc kết luận cho một bệnh nhân cụ thể | Chatbot không đưa ra quyết định y khoa; hiển thị giới hạn phù hợp | ☐ |
| 4 | Lưu cuộc trò chuyện, tải lại trang rồi mở lịch sử | Nội dung chữ và nguồn còn; có thể đổi tên và xóa hội thoại | ☐ |
| 5 | Đính kèm ảnh tổng hợp hoặc ảnh có quyền sử dụng, hỏi mô tả rồi hỏi tiếp | Ảnh hiện trực tiếp trong tin nhắn và mở lớn được; lượt sau giữ ngữ cảnh ảnh trong cùng tab; ảnh được gỡ khỏi ô soạn sau khi gửi | ☐ |
| 6 | Tạo chat mới sau khi chat ảnh | Chat mới không thừa hưởng ngữ cảnh ảnh; xóa/ngắt ngữ cảnh ảnh có hiệu lực | ☐ |
| 7 | Mở lại chat ảnh sau khi tải lại trang | Lịch sử chữ/nguồn vẫn có; ứng dụng yêu cầu đính kèm lại ảnh | ☐ |
| 8 | Chạy luồng phân loại ảnh (nếu trình bày) | Chỉ dùng ảnh được phép; metadata không được đoán cho ảnh lạ; kết quả/điểm số được giới thiệu là đầu ra mô hình thực nghiệm | ☐ |
| 9 | Kiểm tra provider và dữ liệu gửi đi | Không hiển thị API key; người trình bày biết ảnh chat có thể được gửi tới provider đã cấu hình | ☐ |

Nếu cần chạy regression trước buổi nghiệm thu:

~~~powershell
.\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q
~~~

Browser smoke riêng:

~~~powershell
.\.venv\Scripts\python.exe -m pytest ui_tests/test_chatbot_browser.py -q -rs
~~~

Nếu smoke bị skip do trình duyệt/DevTools, ghi rõ là **chưa kiểm tra được trong môi trường đó**. Không đổi skip thành PASS; có thể thực hiện checklist UI thủ công phía trên bằng dữ liệu tổng hợp.

## 3. Phạm vi được nghiệm thu

Có thể nghiệm thu **nguyên mẫu phần mềm học tập chạy local** nếu các thao tác trực tiếp ở mục 2 đạt và báo cáo trình bày các giới hạn. Không dùng kết quả này để tuyên bố:

- mô hình đã được đánh giá độc lập hoặc tổng quát hóa sang cơ sở khác;
- chatbot luôn trích đúng bằng chứng hoặc đã qua chấm entailment độc lập;
- ảnh BTXRD được phép phân phối lại ở cấp từng ảnh;
- hệ thống phù hợp sử dụng lâm sàng, chạy public/VPS, hoặc an toàn cho dữ liệu bệnh nhân.

Các việc trên được ghi là **tạm hoãn/ngoài phạm vi demo** cho tới khi có cohort được phép, nhãn và adjudication phù hợp, hồ sơ quyền dữ liệu, đánh giá triển khai và tiêu chí được owner chốt. G1–G7 vẫn OPEN; answer_ready=false.

## 4. Biên bản nghiệm thu

| Trường | Điền khi nghiệm thu |
|---|---|
| Người nghiệm thu / vai trò |  |
| Ngày và môi trường chạy |  |
| Phiên bản/commit được trình bày |  |
| Các mục không đạt hoặc chưa chạy |  |
| Quyết định | ☐ Đạt trong phạm vi demo học tập ☐ Cần sửa trước khi nghiệm thu |
| Ghi chú |  |

Không điền chữ ký hoặc quyết định thay cho người nghiệm thu.
