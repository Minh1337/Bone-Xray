# Hội thoại đa chủ đề & phân tích ca học tập cho BoneScope

Cập nhật 03/11/2026: bổ sung **luồng phân tích ca ảnh X-quang học tập (Swin + 22 Metadata → ánh xạ nhãn → RAG → hội thoại)** bên cạnh chế độ **trò chuyện đa chủ đề, dùng kho tài liệu khi hỏi về xương**. Không thay đổi dữ liệu corpus, trọng số mô hình hoặc 7 acceptance gate của Giai đoạn 11. Mọi phản hồi API tiếp tục giữ `answer_ready=false`.

## Cách dùng

1. Dừng phiên debug cũ bằng Shift+F5, chạy lại **💬 BoneScope: Chatbot tra cứu tài liệu** bằng F5.
2. Mở `http://127.0.0.1:8765`, Ctrl+F5 trong trình duyệt để tải mã giao diện mới.
3. Giữ chế độ **Trò chuyện + tài liệu** trong ô nhập. Chatbot có thể giải thích, viết/chỉnh nội dung, hỗ trợ lập trình và lập kế hoạch học tập.
4. Tiếp tục hỏi trong cùng tab: “giải thích dễ hiểu hơn”, “cho ví dụ”, “viết ngắn lại”, “trình bày bằng bảng”. Lịch sử gần đây được gửi kèm để hiểu bạn đang nói đến điều gì.
5. Với câu hỏi về xương, chatbot tra cứu kho tài liệu và hiển thị các nguồn thật `[S1]`, `[S2]`. Nếu kho tài liệu thiếu bằng chứng, chatbot nói rõ thay vì biến kiến thức model thành nguồn của dự án.
6. Chọn **Chỉ tra cứu tài liệu** để giới hạn trả lời theo kho nguồn, kể cả khi hỏi nối tiếp.
7. Bấm **Phân tích ca ảnh X-quang** (ở thanh bên, thẻ gợi ý hoặc nút **Ca ảnh** cạnh ô nhập) để nạp ảnh X-quang kèm đủ 22 trường metadata (hoặc nạp từ `cases.json`). Máy chủ chạy mô hình Swin + Cross-Attention cục bộ, hiển thị Top-3 lớp dự đoán, đối chiếu bảng ánh xạ 10 nhãn (`rag/case_context.py`) và tự động tạo giải thích học thuật có nguồn (với 4 nhãn `direct`) hoặc tóm tắt giới hạn mẫu máy chủ (với các nhãn `unresolved`, `aggregate`, `no_tumor`). Đổi ảnh hoặc bấm **Xóa ca** sẽ xóa ngay ngữ cảnh ca cũ để tránh nhầm ca.

Phản hồi chung có nhãn **Groq · trò chuyện · kiến thức chung** (hoặc OpenAI theo cấu hình); phản hồi dựa trên tài liệu có nhãn **bản nháp chưa kiểm chứng** và các thẻ nguồn. “Kiến thức chung” không có nghĩa là đã kiểm tra tính đúng bằng tài liệu hoặc Internet.

## Chuỗi câu hỏi để thử

**Nhớ ngữ cảnh cá nhân giả lập:**

1. “Mình tên An và mới bắt đầu học Python.”
2. “Mình tên gì và đang học gì?”
3. “Lập lịch học trong 3 ngày, mỗi ngày 30 phút.”
4. “Rút gọn lịch đó thành bảng.”

**Tra cứu và hỏi nối tiếp:**

1. “Tài liệu nói gì về osteochondroma?”
2. “Giải thích dễ hiểu hơn giúp mình.”
3. “Tóm tắt thành 3 ý và giữ mã nguồn tham khảo.”
4. “Đổi chủ đề: giải thích vòng lặp for trong Python.”

**Phân tích ca ảnh học tập + hỏi nối tiếp:**

1. Bấm **Phân tích ca ảnh X-quang**, nạp `cases.json`, chọn `case_002` và ảnh `test_images/IMG000002.jpg`, đánh dấu xác nhận rồi bấm **Chạy mô hình & giải thích**.
2. Quan sát thẻ tóm tắt Top-3 của mô hình cục bộ và bản giải thích học thuật có trích dẫn `[S1]`, `[S2]`.
3. Hỏi nối tiếp: “Giải thích ý nghĩa điểm Top-1 của ca đang mở và vì sao điểm softmax không phải xác suất mắc bệnh?”
4. Bấm **Đổi ảnh / ca khác** hoặc **Xóa ca** để kiểm tra việc xóa ngữ cảnh ca cũ.

**Xóa ngữ cảnh:** bấm “Cuộc trò chuyện mới”, rồi hỏi “Mình tên gì?”. Chatbot không nên biết tên nếu bạn chưa nói trong cuộc trò chuyện mới.

## Bộ nhớ và giới hạn

- Chỉ các lượt hoàn tất mới được gửi lại làm lịch sử; lỗi, yêu cầu bị hủy và trạng thái đang chờ không được dùng làm trí nhớ.
- Tối đa 12 tin nhắn, tương đương khoảng 6 lượt hỏi đáp gần đây; mỗi tin tối đa 3.000 ký tự, tổng tối đa 12.000 ký tự. Nội dung cũ/dài hơn được cắt khỏi ngữ cảnh gửi đi.
- Lịch sử và ca ảnh đang mở chỉ nằm trong bộ nhớ tạm (RAM máy chủ tối đa 30 phút cho `case_id`, không ghi đĩa; lịch sử chat nằm trong tab trình duyệt). Tải lại trang/đóng tab sẽ mất; xuất Markdown để tự lưu khi cần.
- “Cuộc trò chuyện mới” xóa trí nhớ phía trình duyệt, xóa `case_id` đang mở trên máy chủ và bỏ qua kết quả cũ đến muộn.
- Không tự học/cập nhật trọng số model từ cuộc trò chuyện. Hành vi được cải thiện bằng lịch sử, hướng dẫn và công cụ tìm nguồn. Chất lượng vẫn phụ thuộc model, quota và độ dài ngữ cảnh.
- Chưa có công cụ tìm Internet theo thời gian thực, mở tệp tùy ý của người dùng hoặc tự chạy code. Khi phân tích ca học tập, ảnh và 22 trường metadata chỉ xử lý cục bộ trên máy này; nhà cung cấp AI chỉ nhận Top-3 nhãn/điểm softmax và ghi chú ánh xạ nhãn do máy chủ quản lý (`case_id`), không nhận ảnh, tuổi/giới tính/vị trí hay tên tệp.
- Câu hỏi yêu cầu đọc trực tiếp hình ảnh/ca bệnh cá nhân, kê liều thuốc và các guard có sẵn vẫn được chặn trước khi đưa vào luồng hội thoại chung.

## Cách triển khai

- `rag/case_context.py`: quản lý `CaseStore` trong bộ nhớ (TTL 30 phút, tối đa 50 ca), kiểm tra quy tắc metadata BTXRD (đủ 22 trường, ≥1 vị trí giải phẫu, đúng 1 tư thế chụp), bảng `LABEL_GUIDE` ánh xạ 10 nhãn của checkpoint (`direct`, `unresolved`, `aggregate`, `no_tumor`), tạo `llm_context` tối thiểu và `template_explanation` xác định khi không tự động tra cứu hoặc khi LLM lỗi.
- `rag/conversation.py`: hướng dẫn trò chuyện và công cụ `search_bone_documents`; model viết lại câu hỏi nối tiếp thành câu hỏi độc lập, có nhận `case_context` do máy chủ gắn kèm khi đang mở ca.
- `rag/generation.py`: transport chung cho Groq/OpenAI; prompt bản nháp dùng lịch sử và `case_context` (nếu có) nhưng chỉ trích dẫn các passages ở lượt hiện tại.
- `rag/demo_api.py`: cung cấp `/api/case`, `/api/case/{case_id}`, `/api/case/{case_id}/explain` và `/api/query` (nhận `question`, `history`, `mode` và `case_id` tùy chọn). Điểm số dự đoán luôn lấy từ `CaseStore` phía máy chủ, không nhận điểm tự khai từ trình duyệt.
- Tổng deadline máy chủ 85 giây; giới hạn riêng retrieval 45 giây, model mặc định 35 giây; trình duyệt chờ tối đa 90 giây. Lượt bị chậm vẫn có nút dừng chờ.
- `rag/demo_web/app.js`: hộp thoại nạp ảnh + 22 trường metadata (hỗ trợ nạp `cases.json`), thanh trạng thái ca đang mở, xuất hội thoại kèm thông tin ca, đổi chế độ, gửi ngữ cảnh và reset trí nhớ.

Groq chưa giữ trạng thái hội thoại thay ứng dụng; việc gửi lịch sử theo từng yêu cầu được thực hiện theo [hướng dẫn multi-turn của Groq](https://console.groq.com/docs/responses-api). Key/provider tiếp tục theo [hướng dẫn Groq](GROQ_CHATBOT_SETUP_VI.md).

## Kiểm tra

Lệnh tái lập không gọi API ngoài:

```powershell
.\.venv\Scripts\python.exe -m pytest rag/tests/test_case_context.py rag/tests/test_demo_api.py rag/tests/test_generation.py rag/tests/test_conversation.py tests/test_end_to_end_pipeline.py -q
node --check rag/demo_web/app.js
```

Kết quả hiện tại: **71 bài kiểm tra đạt** (gồm 70 bài unit/API cho hội thoại + ca ảnh và 1 bài tích hợp toàn chuỗi với checkpoint `model/best_model.pt` thật và `rag.retrieval.Retriever` thật).
