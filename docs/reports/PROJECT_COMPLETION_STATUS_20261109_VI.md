# Trạng thái hoàn thiện BoneScope — 09/11/2026

> **Cập nhật 21:57:** regression hiện đạt **202 passed / 132 subtests**; audit, replay 16/16, register QA và chatbot doctor đều PASS ([bản ghi](../reference/final_verification_20261109.json)). Đã có [báo cáo tổng kết đồ án](BAO_CAO_TONG_KET_DO_AN_BONESCOPE_20261109_VI.md) (Markdown + DOCX). Các số 172/176 bên dưới là mốc trước đó. Gate và giới hạn không đổi.

## Tóm tắt

Nguyên mẫu BoneScope phục vụ **học tập và nghiên cứu nội bộ** đã có các luồng chính: chatbot đa chủ đề, tra cứu RAG, lịch sử SQLite chỉ lưu chữ và nguồn, chat ảnh nhiều lượt trong tab, gợi ý tài liệu sau khi phân tích ảnh, và phân loại X-quang cục bộ khi có đủ metadata. Bộ regression offline hiện tại đạt **172 passed, 0 failed; 132 subtests passed**.

Chưa thể gọi toàn dự án là 100%. Theo checklist kỹ thuật bảy bước của Giai đoạn 11, sáu bước có artifact và bằng chứng triển khai hiện hành; bước 7 mới có cơ chế từ chối một số yêu cầu ngoài phạm vi, nhưng chưa có ngưỡng tin cậy được hiệu chỉnh bằng dữ liệu độc lập. Đây tương ứng **6/7 ≈ 86% độ bao phủ checklist kỹ thuật hẹp**, không phải phần trăm hoàn thành toàn dự án. Bảy gate G1–G7 vẫn `OPEN`; API vẫn trả `answer_ready=false`.

## Đã có và đã kiểm tra

- **Kho RAG:** 22 nguồn có provenance, 794 đoạn, index `794 × 384`; audit hiện hành ngày 09/11 đạt PASS, 0 lỗi ([record](../reference/stage11_integrity_audit_20261109_cureus_v1.json)). Replay bundle `cureus_abcrouting_v1` đạt **16/16**, không mismatch ([record](../reference/stage11_replay_20261109_cureus_v1.json)). Kiểm tra register đạt **24 tham chiếu**, 15 cohort, 7 gate vẫn OPEN. Lệnh mặc định audit/replay đã được đổi về bundle hiện hành; bundle `personal_image_jats_wrapper_v7` chỉ còn là lịch sử.
- **Chatbot:** trả lời hội thoại đa lượt, dùng lịch sử hiện tại để hiểu câu hỏi; câu hỏi về xương được định tuyến qua kho tài liệu và trả các đoạn nguồn. Chat tổng quát không giả tạo citation.
- **Lịch sử:** SQLite giữ văn bản hỏi–đáp và trường nguồn cho phép; ảnh không được ghi vào DB. Có tạo/mở/đổi tên/xóa hội thoại và giới hạn dữ liệu có kiểm soát.
- **Chat ảnh:** ảnh JPEG/PNG/WEBP được xác thực, giữ tạm trong bộ nhớ tab theo hội thoại và gửi lại cho câu hỏi tiếp nối. Mở lịch sử sau này cần đính kèm lại ảnh. Sau phân tích, ứng dụng tìm tối đa 4 đoạn RAG liên quan; giao diện nêu rõ đây là tài liệu đọc thêm, không xác minh dấu hiệu trên ảnh.
- **Metadata ảnh:** chỉ tự gắn metadata khi byte ảnh khớp SHA-256 chính xác và không mơ hồ với manifest BTXRD. Ảnh trùng byte nhưng metadata mâu thuẫn bị chặn. Nếu không khớp, prompt cấm đoán metadata hoặc nhãn bệnh từ tên tệp.
- **Phân loại cục bộ:** mô hình Swin + metadata dùng được trong hộp thoại ca học tập. Catalogue BTXRD có 3.746 ảnh; đánh giá 250 ảnh và ablation hiện có là **in-source**, không phải holdout độc lập.
- **Nhà cung cấp:** chat/RAG thử OpenRouter Free trước; ảnh thử Gemma Free. Sau timeout 15 giây, rate limit, phản hồi incomplete hoặc rỗng, code chuyển sang đúng model Qwen đã khóa. Gemma ảnh gặp rate limit còn thử Free Router một lần. Groq chỉ là fallback tùy chọn và đang tắt theo `.env.example`. Qwen là model trả phí; giá và phương thức được OpenRouter niêm yết tại [trang model Qwen](https://openrouter.ai/qwen/qwen3.5-flash-20260224/pricing) và [API Chat Completions](https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request?explorer=true). Giá có thể thay đổi; ảnh cũng có thể tạo chi phí đầu vào khi được gửi tới Qwen.

## Công việc đã làm trong lượt hoàn thiện này

1. Sửa ranh giới fallback để phản hồi bị cắt, rỗng cũng được nhận diện trước khi trả về; nếu đủ điều kiện, ứng dụng thử tuyến dự phòng thay vì hiện bản nháp thiếu.
2. Sửa lỗi thiếu `import os` khiến `/api/config` có thể lỗi khi đọc trạng thái fallback Groq.
3. Chuyển các kiểm thử nhà cung cấp cũ sang cấu hình OpenRouter và schema Chat Completions hiện tại; thêm kiểm tra mock cho fallback Qwen, fallback Groq chỉ khi bật rõ ràng, ảnh gửi dạng data URL và retrieval tài liệu sau phân tích.
4. Sửa default audit/replay vì trước đó trỏ nhầm bundle lịch sử (`personal_image_jats_wrapper_v7`); giờ cả hai lệnh mặc định chọn bundle `cureus_abcrouting_v1` và có kiểm thử giữ hợp đồng này.
5. Chạy toàn bộ lệnh regression offline:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest api_tests rag\tests tests ui_tests -q
   ```

   Kết quả: **172 passed, 0 failed, 132 subtests passed**, một cảnh báo deprecation của Starlette. Kiểm thử dùng mock transport; không gửi request đến OpenRouter/Groq và không dùng token API.

## Tiếp nối: kiểm chứng trình duyệt và sửa luồng ảnh

Đã bổ sung `ui_tests/test_chatbot_browser.py` chạy Chrome headless với profile, ảnh hình học và SQLite tạm. AI và retrieval được giả lập; HTTP/DOM và persistence dùng ứng dụng thật. Test tái hiện lỗi retry mất ảnh sau khi key draft chuyển thành ID hội thoại đã lưu. Sau sửa, test đạt cả hỏi nhiều lượt, đổi chat/quay lại, xóa ngữ cảnh, reload cần đính kèm lại, lưu/mở/đổi tên/xóa chat và giữ nguồn. Đã đồng bộ history ảnh với giới hạn 8 tin/9.000 ký tự của API, sửa tiêu đề dính thông báo ảnh, giữ Markdown an toàn khi mở lịch sử và tiếp tục phân biệt tài liệu đọc thêm với citation chứng minh ảnh. Deadline UI chữ đổi thành 110 giây để nhận phản hồi từ API có deadline 105 giây; ảnh vẫn chờ tối đa 90 giây.

Ở 320×568 và 390×844, không tràn ngang, composer nằm trong chiều rộng màn hình và sidebar mobile quản lý `inert` đúng; chế độ tối được giữ sau reload. Không ghi nhận JavaScript exception trong kịch bản. Kiểm tra không đo chất lượng mô tả X-quang hoặc mức liên quan/entailment của nguồn và không thay cho đánh giá UI trực quan thủ công.

[Bản ghi máy đọc được](../reference/chatbot_browser_regression_20261109.json) lưu kết quả **172 passed / 132 subtests**, hash mã nguồn và xác nhận năm hash nền vẫn khớp handoff. `node --check rag/demo_web/app.js` và `git diff --check` đều đạt. Hướng dẫn UI/hội thoại đã đồng bộ Free → Qwen trả phí dự phòng.

## Kiểm tra provider thật — đã hoàn tất smoke cơ bản

Theo quyền dùng Qwen dự phòng đã được người dùng cấp, đã gọi tuyến hiện hành bằng một câu chữ rất ngắn và một PNG hình học tự tạo; không gửi ảnh X-quang, lịch sử người dùng hoặc dữ liệu từ SQLite. `plan_turn` trả nhánh chat qua `openrouter/free` trong **3,343 giây**. Ảnh gặp 429 ở Gemma Free, tuyến Free Router không có HTTP response được ghi trước fallback, rồi Qwen trả nội dung không rỗng trong tổng **29,594 giây**. Bốn HTTP attempts gồm **một attempt Qwen trả phí**, tổng cost do các phản hồi thành công báo về **$0,000248755**. Request bị timeout có thể có usage phía server không được trả về; OpenRouter Activity là nơi đối chiếu chi phí.

[Record provider thật](../reference/chatbot_provider_smoke_20261109.json) lưu model, thời gian, usage, SHA-256 ảnh và cách tái tạo input; không chứa key hoặc nội dung hội thoại thật. Đây là kiểm tra kết nối/chuyển tuyến và phản hồi không rỗng, chưa chấm độ đúng mô tả hình học, chất lượng X-quang, citation entailment hay SLA. Regression 172/132 ở trên vẫn là offline; live smoke được chạy riêng sau đó.

## Những gì còn thiếu trước khi có thể gọi dự án hoàn tất

### Sử dụng bản mới trên VS Code

Dừng phiên cũ bằng Shift+F5, chạy lại cấu hình chatbot bằng F5 rồi Ctrl+F5 trong trình duyệt để nạp JavaScript mới. Browser smoke và provider smoke cơ bản đã có record; chất lượng nghiên cứu cần đánh giá theo các mục dưới đây.

### Cần bằng chứng hoặc quyết định độc lập

- Chưa có bộ ảnh ngoài BTXRD được cấp quyền, giữ tách theo bệnh nhân/lesion và có reference standard do chuyên gia xác lập. Không có danh sách patient IDs hoặc split history đầy đủ cho checkpoint hiện tại.
- Chưa có reviewer độc lập chấm retrieval relevance, claim-to-source support, citation entailment và câu trả lời sinh.
- Chưa có dữ liệu phù hợp để hiệu chỉnh ngưỡng `insufficient_evidence` cho retrieval. Không chọn ngưỡng từ các bộ dev/test đã xem.
- Chưa có chữ ký reviewer, quyết định intended-use chính thức hoặc hồ sơ đóng các gate G1–G7. Không tự đặt dấu ký, đóng gate hay đổi `answer_ready`.
- Chưa có kiểm thử bảo mật/riêng tư độc lập. Đóng gói phát hành và VPS là bước triển khai sau khi xác định phạm vi; nguyên mẫu hiện chạy local.

## Tiến độ có thể báo cáo

| Phạm vi | Trạng thái |
| --- | --- |
| Regression phần mềm offline | 172/172 passed; 132 subtests passed |
| Checklist pipeline kỹ thuật Giai đoạn 11 | 6/7 bước có artifact; khoảng 86% độ bao phủ hẹp; bước 7 chưa hiệu chỉnh ngưỡng độc lập |
| Chatbot học tập và luồng ảnh | Chức năng chính đã tích hợp; mock/API, Chrome headless và provider smoke cơ bản PASS; chưa đánh giá độc lập chất lượng X-quang/nguồn |
| Gate nghiệm thu G1–G7 | 0/7 đóng, đều `OPEN` |
| Kết luận toàn dự án | Chưa đạt 100%; chưa có mẫu số hợp lệ để quy ra một tỷ lệ tổng thể |

**Hạn chế sử dụng:** chatbot và mô hình ảnh là bản thử nghiệm học tập. Kết quả AI có thể sai, nguồn đọc thêm không xác nhận quan sát ảnh, và mô hình phân loại không được dùng để chẩn đoán hay quyết định điều trị.
