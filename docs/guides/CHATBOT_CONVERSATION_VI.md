# Hội thoại đa chủ đề & phân tích ca học tập cho BoneScope

Ảnh chat được giữ trong RAM của tab và gắn riêng với từng cuộc trò chuyện. Sau khi gửi, tệp rời khỏi ô soạn; các câu hỏi tiếp theo trong chat đó gọi lại `POST /api/image-chat` với ảnh và lịch sử gần đây. Có thể chuyển giữa các chat trong cùng tab mà không trộn ngữ cảnh ảnh. **Bỏ ảnh** chỉ hủy tệp đang chờ gửi; **Xóa ngữ cảnh** gỡ ảnh đã gửi khỏi chat hiện tại. Đóng hoặc tải lại tab sẽ xóa ảnh khỏi RAM; khi mở lại lịch sử cần đính kèm ảnh lại. Không ghi byte ảnh hoặc tên tệp vào SQLite. Luồng này nằm cạnh **nạp ảnh BTXRD theo mã + tự khớp 22 metadata qua SHA-256** và **phân tích ca học tập (Swin + Metadata → ánh xạ nhãn → RAG)**. Mọi phản hồi API tiếp tục giữ `answer_ready=false`.

## Cách dùng

1. Dừng phiên debug cũ bằng Shift+F5, chạy lại **💬 BoneScope: Chatbot tra cứu tài liệu** bằng F5.
2. Mở `http://127.0.0.1:8765`, Ctrl+F5 trong trình duyệt để tải mã giao diện mới.
3. Giữ chế độ **Trò chuyện + tài liệu** trong ô nhập. Chatbot có thể giải thích, viết/chỉnh nội dung, hỗ trợ lập trình và lập kế hoạch học tập.
4. Tiếp tục hỏi trong cùng tab: “giải thích dễ hiểu hơn”, “cho ví dụ”, “viết ngắn lại”, “trình bày bằng bảng”. Lịch sử gần đây được gửi kèm để hiểu bạn đang nói đến điều gì, và các lượt văn bản hoàn tất được lưu cục bộ trong `data/chat_history.db` (hỗ trợ mở lại, đổi tên và xóa ở thanh bên).
5. Với câu hỏi về xương, chatbot tra cứu kho tài liệu và hiển thị các nguồn thật `[S1]`, `[S2]`. Nếu kho tài liệu thiếu bằng chứng, chatbot nói rõ thay vì biến kiến thức model thành nguồn của dự án.
6. Chọn **Chỉ tra cứu tài liệu** để giới hạn trả lời theo kho nguồn, kể cả khi hỏi nối tiếp.
7. Bấm **Ảnh** cạnh ô nhập (hoặc dán `Ctrl+V` / kéo–thả tệp ảnh vào ô nhập) để gửi ảnh JPEG/PNG/WEBP (≤10 MiB) cho AI mô tả quan sát học tập. Sau phân tích, hệ thống tìm tối đa 4 đoạn trong kho BoneScope bằng câu hỏi và phần mô tả ảnh. Các nguồn hiện thành thẻ mở được để đọc nội dung, giấy phép và trang gốc; chúng chỉ là tài liệu tham khảo, không xác minh ảnh. Nếu không tìm được nguồn, kết quả ảnh vẫn được giữ và giao diện báo điều đó. Sau khi gửi, ô soạn được làm trống; ảnh vẫn làm ngữ cảnh của chat hiện tại và được gửi lại cùng lịch sử khi hỏi tiếp. Dùng **Xóa ngữ cảnh** để gỡ ảnh đã gửi; **Bỏ ảnh** chỉ hủy tệp mới đang chờ. Ngữ cảnh ảnh nằm riêng theo từng chat trong RAM của tab. Đóng/tải lại tab hoặc mở lịch sử ở tab mới sẽ cần đính kèm lại. Ảnh không lưu vào SQLite.
8. Bấm **Phân tích ca ảnh X-quang** (ở thanh bên, thẻ gợi ý hoặc nút **Ca ảnh · metadata** cạnh ô nhập) để nạp ảnh X-quang kèm đủ 22 trường metadata (có thể bấm trực tiếp các nút **Mẫu nhanh** như `IMG000002 · osteosarcoma`, `IMG000240 · osteochondroma`, nhập mã ảnh BTXRD như `IMG000001` để tự tải ảnh cục bộ và tự khớp 22 metadata qua SHA-256, hoặc nạp từ `cases.json`). Nếu ảnh tải lên không khớp SHA-256 trong BTXRD, hộp thoại cho phép bấm **Ảnh không khớp BTXRD · Hỏi AI về ảnh** để mô tả ảnh qua luồng vision hoặc tự nhập đủ 22 metadata ở bước 2. Máy chủ chạy mô hình Swin + Cross-Attention cục bộ, hiển thị Top-3 lớp dự đoán, đối chiếu bảng ánh xạ 10 nhãn (`rag/case_context.py`) và tự động tạo giải thích học thuật có nguồn (với 4 nhãn `direct`) hoặc tóm tắt giới hạn mẫu máy chủ (với các nhãn `unresolved`, `aggregate`, `no_tumor`). Đổi ảnh hoặc bấm **Xóa ca** sẽ xóa ngay ngữ cảnh ca cũ để tránh nhầm ca.

Phản hồi mang nhãn provider/model thực tế: **OpenRouter · Free**, **Qwen3.5 Flash · trả phí dự phòng**, hoặc **Groq · dự phòng Free** khi được bật. Phản hồi dựa trên tài liệu có nhãn **bản nháp chưa kiểm chứng** và các thẻ nguồn. “Kiến thức chung” không có nghĩa là đã kiểm tra tính đúng bằng tài liệu hoặc Internet.

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
- Lịch sử hội thoại văn bản được lưu cục bộ trong SQLite (`data/chat_history.db`, chỉ giữ văn bản câu hỏi/trả lời và 5 trường trích dẫn an toàn `chunk_id`, `source_id`, `title`, `text`, `source_sha256`; tuyệt đối không lưu byte ảnh, tuổi/giới tính/vị trí hay tên tệp ảnh). Ca ảnh đang mở (`case_id`) nằm trong RAM server tối đa 30 phút; ảnh chat nằm tạm trong bộ nhớ tab, được phân vùng theo ID cuộc trò chuyện và có thể xóa bằng **Xóa ngữ cảnh**. Khi đóng/tải lại tab, dữ liệu ảnh tạm biến mất.
- “Cuộc trò chuyện mới” tạo phiên mới trên trình duyệt, xóa `case_id` đang mở trên máy chủ và bỏ qua kết quả cũ đến muộn; các cuộc trò chuyện đã lưu vẫn có thể mở lại hoặc xóa thủ công ở mục **Đã lưu trên máy** (tối đa 500 cuộc trò chuyện, 2.000 tin nhắn/cuộc trò chuyện, không tự động xóa ngầm lịch sử cũ khi đầy).
- Không tự học/cập nhật trọng số model từ cuộc trò chuyện. Hành vi được cải thiện bằng lịch sử, hướng dẫn và công cụ tìm nguồn. Chất lượng vẫn phụ thuộc model, quota và độ dài ngữ cảnh.
- Chưa có công cụ tìm Internet theo thời gian thực, mở tệp tùy ý của người dùng hoặc tự chạy code. Khi phân tích ca học tập, ảnh và 22 trường metadata chỉ xử lý cục bộ trên máy này; nhà cung cấp AI chỉ nhận Top-3 nhãn/điểm softmax và ghi chú ánh xạ nhãn do máy chủ quản lý (`case_id`), không nhận ảnh, tuổi/giới tính/vị trí hay tên tệp.
- Câu hỏi yêu cầu đọc trực tiếp hình ảnh/ca bệnh cá nhân, kê liều thuốc và các guard có sẵn vẫn được chặn trước khi đưa vào luồng hội thoại chung.

## Cách triển khai

- `rag/case_context.py`: quản lý `CaseStore` trong bộ nhớ (TTL 30 phút, tối đa 50 ca), kiểm tra quy tắc metadata BTXRD (đủ 22 trường, ≥1 vị trí giải phẫu, đúng 1 tư thế chụp), bảng `LABEL_GUIDE` ánh xạ 10 nhãn của checkpoint (`direct`, `unresolved`, `aggregate`, `no_tumor`), tạo `llm_context` tối thiểu và `template_explanation` xác định khi không tự động tra cứu hoặc khi LLM lỗi.
- `rag/conversation.py`: hướng dẫn trò chuyện và công cụ `search_bone_documents`; model viết lại câu hỏi nối tiếp thành câu hỏi độc lập, có nhận `case_context` do máy chủ gắn kèm khi đang mở ca.
- `rag/generation.py`: OpenRouter Free trước, Qwen trả phí khi model Free timeout, rate limit, trả rỗng hoặc incomplete; Groq chỉ là fallback tùy chọn. `generate_image_answer` yêu cầu tiếng Việt, tách quan sát khỏi giả thuyết, kiểm tra độ chắc của vùng chụp/ký hiệu R-L/chồng hình và cấm tự tạo nhãn/điểm. Vision không nhận các đoạn RAG ở lượt này; ứng dụng hiển thị riêng tài liệu liên quan, không xem chúng là bằng chứng ảnh. Prompt bản nháp thường dùng lịch sử và `case_context` (nếu có), chỉ trích dẫn passages ở lượt hiện tại.
- `rag/demo_api.py`: cung cấp `/api/case`, `/api/case/{case_id}`, `/api/case/{case_id}/explain`, `/api/query` và `/api/image-chat`. Luồng ảnh chạy vision trước, sau đó truy xuất tối đa 4 đoạn tài liệu theo câu hỏi và mô tả ảnh; lỗi retrieval không làm mất phản hồi ảnh. Điểm số dự đoán luôn lấy từ `CaseStore` phía máy chủ, không nhận điểm tự khai từ trình duyệt.
- Deadline máy chủ: chat chữ 105 giây; chat ảnh 85 giây (gồm retrieval ảnh tối đa 25 giây). Trình duyệt chờ chat chữ 110 giây và chat ảnh 90 giây để nhận kịp phản hồi hoặc lỗi từ máy chủ. Lượt bị chậm vẫn có nút dừng chờ. Lịch sử gửi lên API ảnh tối đa 8 tin nhắn/9.000 ký tự; chat chữ tối đa 12 tin nhắn/12.000 ký tự. Đây là ngữ cảnh gần đây, không phải toàn bộ lịch sử dài hạn được đưa vào model.
- `rag/demo_web/app.js`: hộp thoại nạp ảnh + 22 trường metadata (hỗ trợ nạp `cases.json`), thanh trạng thái ca đang mở, xuất hội thoại kèm thông tin ca, đổi chế độ, gửi ngữ cảnh và reset trí nhớ.

Lịch sử được gửi kèm theo từng yêu cầu, không dựa vào trạng thái lưu từ nhà cung cấp. Key và cách chuyển tuyến xem [hướng dẫn OpenRouter Free và Qwen dự phòng](OPENROUTER_CHATBOT_SETUP_VI.md).

## Kiểm tra

Lệnh tái lập không gọi API ngoài:

```powershell
.\.venv\Scripts\python.exe -m pytest rag/tests/test_case_context.py rag/tests/test_chat_history.py rag/tests/test_demo_api.py rag/tests/test_generation.py rag/tests/test_conversation.py tests/test_end_to_end_pipeline.py -q
node --check rag/demo_web/app.js
```

Kết quả toàn suite mới nhất ngày 09/11: **172 passed / 132 subtests**. Kiểm tra Chrome headless nằm trong `ui_tests/test_chatbot_browser.py`, dùng DB/profile tạm và AI giả lập; xác nhận thử lại giữ ảnh sau lần lưu đầu, hỏi nhiều lượt không vượt hợp đồng API, đổi chat không trộn ảnh, reload chỉ giữ văn bản/nguồn, đổi tên/xóa chat và mobile. Xem [bản ghi kiểm chứng](../reference/chatbot_browser_regression_20261109.json). Các regression này không tiêu token API. Lượt [smoke provider riêng](../reference/chatbot_provider_smoke_20261109.json) sau đó đã PASS: chữ Free 3,343 giây; ảnh hình học qua Qwen 29,594 giây; một lượt Qwen trả phí, cost phản hồi báo về $0,000248755. Smoke chỉ xác nhận kết nối và chuyển tuyến; chưa chấm chất lượng X-quang hoặc nguồn.
