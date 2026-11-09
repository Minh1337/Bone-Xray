# Addendum: review câu trả lời do generator tạo

**Ngày:** 10/11/2026. **Trạng thái:** hướng dẫn bổ sung; chưa có reviewer hay nhãn độc lập.

Protocol [thẩm định retrieval hiện hành](STAGE11_INDEPENDENT_REVIEW_PROTOCOL_VI.md) được giữ nguyên theo hash trong register và tập trung vào quan hệ giữa câu hỏi với evidence trong corpus. Sau khi soạn protocol đó, BoneScope đã tích hợp generator OpenRouter vào chatbot học tập. Protocol retrieval vẫn hữu ích nhưng không tự xác nhận các câu trả lời được sinh.

Khi có reviewer và bộ dữ liệu được phép, review generator nên khóa trước model, prompt, corpus/index, policy, câu hỏi và phiên bản ứng dụng bằng hash. Reviewer chấm riêng từng claim đầu ra với exact source span: hỗ trợ trực tiếp/đầy đủ, hỗ trợ một phần, không hỗ trợ, mâu thuẫn; ghi polarity, điều kiện, qualifier và phạm vi nguồn bị thiếu hoặc bị đổi. Phân biệt nội dung tổng quát của model với claim gắn citation; tài liệu đọc thêm sau phân tích ảnh không được xem là xác nhận một quan sát trên ảnh. Không nâng citation do model tự gắn thành citation đã xác thực nếu hệ thống không xác minh mapping.

Các câu hỏi/đáp án và nhãn phải được khóa độc lập trước khi xem kết quả hệ thống; bất đồng cần adjudication, giữ nguyên từng nhãn gốc. Báo cáo số lượng theo population, khoảng bất định và trường hợp không đánh giá được; reviewer/owner phải quyết định tiêu chí và cỡ mẫu trước khi mở kết quả. Đây là đề cương review, không phải bằng chứng rằng các bước ấy đã diễn ra.

Hiện chưa có nhãn reviewer, adjudication, estimate entailment hoặc tiêu chí đã ký. Vì vậy claim-to-span, citation entailment và chất lượng generator vẫn `not evaluable`; G1–G7 OPEN, `answer_ready=false`. Xem thêm [quy trình vận hành và đánh giá](../guides/RESEARCH_WORKFLOW_VI.md).
