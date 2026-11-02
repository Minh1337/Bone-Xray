# Kết nối chatbot BoneScope với OpenAI API

Cập nhật: 31/10/2026. Luồng tạo bản nháp đã chuyển từ Gemini sang OpenAI Responses API. Tài liệu và mô hình retrieval của Giai đoạn 11 không thay đổi; kết quả tiếp tục mang `answer_ready=false`.

Cập nhật tiếp theo: dự án đã hỗ trợ thêm Groq và workspace đang chọn `LLM_PROVIDER=groq`. Để dùng hướng dẫn OpenAI bên dưới, đổi sang `LLM_PROVIDER=openai` rồi khởi động lại. Xem [hướng dẫn Groq](GROQ_CHATBOT_SETUP_VI.md) nếu muốn dùng Free Plan.

## Tài khoản và chi phí

Có thể đăng nhập OpenAI Platform bằng cùng tài khoản đang dùng ChatGPT. ChatGPT Plus không cung cấp API key hoặc số dư dùng API; cần cấu hình thanh toán/số dư API riêng. Tài liệu hiện hành về quyền lợi API chỉ liệt kê các gói Pro và Business đủ điều kiện, và nêu Plus là gói không đủ điều kiện: [API credits for ChatGPT subscribers](https://developers.openai.com/api/docs/guides/chatgpt-api-credits).

1. Mở [OpenAI Platform](https://platform.openai.com/).
2. Vào [Billing](https://platform.openai.com/settings/organization/billing/overview), kiểm tra tài khoản API có phương thức thanh toán/số dư hợp lệ. Người dùng tự quyết định số tiền và thực hiện thanh toán.
3. Mở [API keys](https://platform.openai.com/api-keys), tạo secret key cho dự án. Quyền key phải cho phép gọi Responses API. Hướng dẫn chính thức: [Developer quickstart](https://developers.openai.com/api/docs/quickstart).
4. Dán key vào `OPENAI_API_KEY=` trong `.env` ở thư mục gốc BONESCOPE. Không dán vào đoạn chat, JavaScript hoặc `.env.example`.

## Cấu hình đã chuẩn bị

```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.4-mini
OPENAI_REASONING_EFFORT=none
OPENAI_TIMEOUT_SECONDS=35
OPENAI_MAX_OUTPUT_TOKENS=1600
```

Chỉ cần điền key ở dòng đầu. `.env` đã được Git bỏ qua. Các biến Gemini cũ được giữ để tránh mất cấu hình của người dùng, nhưng chatbot không đọc chúng nữa. Không có cơ chế tự chuyển sang Gemini.

Chọn `gpt-5.4-mini` làm cấu hình ban đầu vì đây là biến thể nhỏ và nhanh hơn GPT-5.4. Model hỗ trợ Responses và reasoning `none`: [trang model chính thức](https://developers.openai.com/api/docs/models/gpt-5.4-mini). Tốc độ thật còn tùy mạng, tài khoản, câu hỏi và thời gian retrieval; chưa đo tốc độ thực tế bằng key của người dùng. Nếu đổi model, cần kiểm tra model đó hỗ trợ mức reasoning đã chọn.

## Chạy lại trong VS Code

1. Lưu `.env` bằng Ctrl+S.
2. Dừng phiên debug đang chạy bằng Shift+F5.
3. Chọn **💬 BoneScope: Chatbot tra cứu tài liệu**, bấm F5.
4. Mở `http://127.0.0.1:8765`, bấm Ctrl+F5 để tải lại giao diện.
5. Gửi “xin chào” để kiểm tra giao diện/API cục bộ, sau đó gửi “Tài liệu nói gì về osteochondroma?” để kiểm tra retrieval và bản nháp OpenAI.

“Xin chào” được trả lời cục bộ, không gọi OpenAI và không xác minh API key/số dư. Câu hỏi chuyên môn có nguồn mới đi qua bước tạo bản nháp có tính phí.

Lệnh PowerShell nếu chạy ngoài debug:

```powershell
.\.venv\Scripts\python.exe -m uvicorn rag.demo_api:app --host 127.0.0.1 --port 8765
```

Backend tự nạp `.env` ở thư mục gốc; biến môi trường đã có được ưu tiên. Chỉ chạy một máy chủ trên cổng 8765. Dừng lệnh terminal bằng Ctrl+C.

## Thời gian chờ và lỗi

- Tra cứu cục bộ: ngừng chờ sau 45 giây. Nếu việc nạp mô hình trong luồng nền đã bắt đầu, nó có thể vẫn tiếp tục chạy và được dùng lại ở câu hỏi sau.
- OpenAI: deadline mặc định 35 giây, cấu hình được từ 5–40 giây, SDK `max_retries=0`. Giới hạn mạng và retry được đặt rõ vì SDK mặc định có thể chờ lâu và tự thử lại: [OpenAI Python SDK](https://developers.openai.com/api/reference/python).
- Trình duyệt: dừng chờ toàn bộ yêu cầu sau 90 giây; bộ đếm chỉ biểu thị thời gian đã trôi qua.
- Thiếu key hoặc cấu hình sai: báo ngay trước retrieval.
- Key sai/bị thu hồi: cập nhật key, khởi động lại máy chủ.
- `openai_quota`: kiểm tra số dư/hạn mức API; mua Plus không khắc phục lỗi này.
- `openai_rate_limit`: chờ rồi thử lại thủ công.
- `openai_model_unavailable`/`openai_permission`: kiểm tra model và quyền key/tài khoản.
- Mất mạng, timeout, phản hồi trống hoặc chưa hoàn tất: thông báo riêng; không hiển thị phần trả lời bị cắt như một bản nháp hoàn chỉnh.

Chỉ câu hỏi và các đoạn nguồn cần thiết được gửi tới endpoint OpenAI chính thức. Responses được gọi với `store=false`; đây không phải cam kết về mọi hình thức lưu giữ dữ liệu phía nhà cung cấp. Không gửi đường dẫn tệp hoặc hash nguồn. Nội dung gốc cùng hash được giữ tại giao diện để đối chiếu. Không ghi API key hoặc lỗi nguyên văn của nhà cung cấp vào phản hồi/log ứng dụng.

## Bàn giao kỹ thuật

- `rag/generation.py`: SDK, cấu hình, prompt, giới hạn chờ và phân loại lỗi.
- `rag/demo_api.py`: nạp `.env`, kiểm tra key sớm, deadline retrieval, gọi bộ tạo bản nháp.
- `rag/demo_web/app.js` và `index.html`: nhãn OpenAI, bộ đếm chờ, hướng dẫn mạng và timeout.
- `requirements_rag.txt`: `openai==2.54.0`, `python-dotenv==1.2.4`; đã cài trong `.venv` của workspace.
- `.env.example`: mẫu cấu hình công khai. `.env`: chỗ người dùng tự điền key thật.

Kiểm tra tái lập, không cần key thật và không phát sinh gọi API trả phí:

```powershell
.\.venv\Scripts\python.exe -m pytest rag/tests/test_demo_api.py rag/tests/test_generation.py -q
node --check rag/demo_web/app.js
```

Kết quả lúc bàn giao: 26 bài kiểm tra Python đạt. Mock transport thực thi SDK thật để kiểm tra endpoint/payload, lỗi 400/401/403/404/429/500, lỗi mạng, deadline, không tự retry, và phản hồi rỗng/chưa hoàn tất. API test kiểm tra cấu hình thiếu, chào hỏi, nguồn, guard `answer_ready=false` và deadline retrieval. Có một cảnh báo deprecation hiện hữu từ Starlette/AnyIO. Chưa xác minh key, quyền model, số dư hoặc độ trễ OpenAI thật vì chưa có key OpenAI trong cấu hình người dùng.

Kiểm tra Chrome headless cũng đạt: chào hỏi qua máy chủ thật, thiếu key báo ngay, nhãn OpenAI và bấm nguồn với phản hồi mô phỏng, bộ đếm thời gian chờ và nút dừng; không có lỗi JavaScript. Ảnh trạng thái thiếu key: `.stitch/designs/openai-setup-required.png`. Máy chủ kiểm tra tạm cổng 8766 đã dừng sau kiểm tra; người dùng chạy phiên chính trong VS Code.
