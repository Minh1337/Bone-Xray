# Hội thoại đa chủ đề cho BoneScope

Cập nhật 31/10/2026 theo lựa chọn của người dùng: **trò chuyện đa chủ đề, dùng kho tài liệu khi hỏi về xương**. Đây là phần chatbot; không thay đổi tiến độ, dữ liệu hoặc acceptance gate của Giai đoạn 11. Mọi phản hồi API tiếp tục giữ `answer_ready=false`.

## Cách dùng

1. Dừng phiên debug cũ bằng Shift+F5, chạy lại **💬 BoneScope: Chatbot tra cứu tài liệu** bằng F5.
2. Mở `http://127.0.0.1:8765`, Ctrl+F5 trong trình duyệt để tải mã giao diện mới.
3. Giữ chế độ **Trò chuyện + tài liệu** trong ô nhập. Chatbot có thể giải thích, viết/chỉnh nội dung, hỗ trợ lập trình và lập kế hoạch học tập.
4. Tiếp tục hỏi trong cùng tab: “giải thích dễ hiểu hơn”, “cho ví dụ”, “viết ngắn lại”, “trình bày bằng bảng”. Lịch sử gần đây được gửi kèm để hiểu bạn đang nói đến điều gì.
5. Với câu hỏi về xương, chatbot tra cứu kho tài liệu và hiển thị các nguồn thật `[S1]`, `[S2]`. Nếu kho tài liệu thiếu bằng chứng, chatbot nói rõ thay vì biến kiến thức model thành nguồn của dự án.
6. Chọn **Chỉ tra cứu tài liệu** để giới hạn trả lời theo kho nguồn, kể cả khi hỏi nối tiếp.

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

**Xóa ngữ cảnh:** bấm “Cuộc trò chuyện mới”, rồi hỏi “Mình tên gì?”. Chatbot không nên biết tên nếu bạn chưa nói trong cuộc trò chuyện mới.

## Bộ nhớ và giới hạn

- Chỉ các lượt hoàn tất mới được gửi lại làm lịch sử; lỗi, yêu cầu bị hủy và trạng thái đang chờ không được dùng làm trí nhớ.
- Tối đa 12 tin nhắn, tương đương khoảng 6 lượt hỏi đáp gần đây; mỗi tin tối đa 3.000 ký tự, tổng tối đa 12.000 ký tự. Nội dung cũ/dài hơn được cắt khỏi ngữ cảnh gửi đi.
- Lịch sử nằm trong bộ nhớ tab, không có cơ sở dữ liệu hoặc ghi hội thoại vào máy chủ. Tải lại trang/đóng tab sẽ mất; xuất Markdown để tự lưu khi cần. Nhà cung cấp AI nhận lịch sử gần đây cùng câu hỏi.
- “Cuộc trò chuyện mới” xóa trí nhớ phía trình duyệt và bỏ qua kết quả cũ đến muộn.
- Không tự học/cập nhật trọng số model từ cuộc trò chuyện. Hành vi được cải thiện bằng lịch sử, hướng dẫn và công cụ tìm nguồn. Chất lượng vẫn phụ thuộc model, quota và độ dài ngữ cảnh.
- Chưa có công cụ tìm Internet theo thời gian thực, mở tệp của người dùng, chạy code hoặc đọc ảnh. Chatbot được hướng dẫn nói rõ các giới hạn này khi liên quan.
- Câu hỏi về ảnh/ca bệnh cá nhân, liều thuốc và các guard có sẵn vẫn được chặn trước khi đưa vào luồng hội thoại chung.

## Cách triển khai

- `rag/conversation.py`: hướng dẫn trò chuyện và công cụ `search_bone_documents`; model viết lại câu hỏi nối tiếp thành câu hỏi độc lập. Công cụ chỉ tìm nguồn cục bộ; không có thực thi shell hay công cụ truy cập máy tính.
- `rag/generation.py`: transport chung cho Groq/OpenAI; prompt bản nháp dùng lịch sử để hiểu câu hỏi nhưng chỉ trích dẫn các passages ở lượt hiện tại.
- `rag/demo_api.py`: nhận `question`, `history` và `mode`. `history` chỉ nhận vai trò `user`/`assistant`, giới hạn kích thước; không nhận system prompt từ client. `mode=auto` cho hội thoại đa chủ đề; khi không truyền mode, API vẫn mặc định `documents` để tương thích các client cũ.
- Câu hỏi xương được policy nhận diện rõ sẽ đi thẳng vào retrieval, tránh một lượt gọi lập kế hoạch không cần thiết. Câu hỏi chung/câu nối tiếp dùng model để trả lời hoặc yêu cầu công cụ tra cứu. Một lượt có tra cứu sau bước lập kế hoạch có thể dùng hai lần gọi model và tiêu tốn quota hơn trò chuyện đơn giản.
- Tổng deadline máy chủ 85 giây; giới hạn riêng retrieval 45 giây, model mặc định 35 giây; trình duyệt chờ tối đa 90 giây. Lượt bị chậm vẫn có nút dừng chờ.
- `rag/demo_web/app.js`: lịch sử riêng với bản xuất hội thoại; đổi chế độ, gửi ngữ cảnh, hiển thị rõ cơ sở phản hồi và reset trí nhớ.

Groq chưa giữ trạng thái hội thoại thay ứng dụng; việc gửi lịch sử theo từng yêu cầu được thực hiện theo [hướng dẫn multi-turn của Groq](https://console.groq.com/docs/responses-api). Key/provider tiếp tục theo [hướng dẫn Groq](GROQ_CHATBOT_SETUP_VI.md).

## Kiểm tra

Lệnh tái lập không gọi API ngoài:

```powershell
.\.venv\Scripts\python.exe -m pytest rag/tests/test_demo_api.py rag/tests/test_generation.py rag/tests/test_conversation.py -q
node --check rag/demo_web/app.js
```

Kết quả hiện tại: **58 bài kiểm tra đạt**. Kiểm tra gồm: giữ ngữ cảnh trong payload, trả lời chung không tải retrieval, chuyển câu hỏi nối tiếp thành query độc lập, buộc tra cứu khi cần, từ chối tool/arguments không hợp lệ, giữ nguồn và `answer_ready=false`, từ chối history quá dài/role system, deadline cả bước hội thoại, hồi quy Groq/OpenAI.

Chrome headless đã kiểm tra chế độ mặc định, gửi lịch sử hỏi đáp, nguồn có thể mở, thử lại không dùng tin lỗi làm ngữ cảnh, tạo cuộc trò chuyện mới xóa trí nhớ, chuyển sang chỉ tài liệu và bố cục điện thoại 390px. Không có lỗi JavaScript. Ảnh: `.stitch/designs/chatbot-conversation-desktop.png`, `chatbot-conversation-mobile.png`.

Đã chạy **hai phép thử Groq thật** với dữ liệu giả lập: (1) nhắc lại đúng tên An và chủ đề học Python từ lịch sử; (2) yêu cầu “giải thích dễ hiểu hơn” sau osteochondroma trả về lệnh tra cứu có chủ đề osteochondroma đầy đủ. Đây là kiểm tra tích hợp nhỏ, không phải benchmark chất lượng, kiểm định y khoa hoặc bảo đảm mọi câu hỏi đều đúng. Không ghi key hoặc nguyên văn phản hồi của người dùng vào báo cáo.
