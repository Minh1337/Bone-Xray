# Dùng Groq Free cho chatbot BoneScope

Cập nhật: 31/10/2026. Đã tích hợp Groq, chọn `LLM_PROVIDER=groq` trong `.env` và chuẩn bị chỗ điền key. Người dùng chỉ cần tạo key và khởi động lại máy chủ. Chưa gọi Groq thật khi bàn giao vì chưa có key.

## 1. Tạo tài khoản và key

1. Truy cập [Groq Console](https://console.groq.com/), đăng ký/đăng nhập tài khoản.
2. Giữ tài khoản ở **Free Plan** để thử nghiệm miễn phí. Không cần nâng lên Developer để làm theo hướng dẫn này. Xem [thông tin Free Plan](https://community.groq.com/t/do-i-get-charged-for-anything-on-the-groq-free-plan/832).
3. Mở [API Keys](https://console.groq.com/keys), chọn tạo API key, đặt tên dễ nhớ như `BoneScope-demo`, rồi sao chép key. Cách tạo key và lưu vào biến môi trường được mô tả ở [Groq Quickstart](https://console.groq.com/docs/quickstart).
4. Dán trực tiếp vào `.env` của dự án; không dán vào chat, JavaScript hoặc `.env.example`.

## 2. Điền cấu hình

File: `C:\Users\Admin\Desktop\Project\MainProject\BONESCOPE\.env`.

Các dòng đã được chuẩn bị:

```dotenv
LLM_PROVIDER=groq
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-20b
GROQ_REASONING_EFFORT=low
GROQ_TIMEOUT_SECONDS=35
GROQ_MAX_OUTPUT_TOKENS=2400
```

Dán key sau dấu `=` ở dòng `GROQ_API_KEY=` rồi Ctrl+S. Mỗi biến chỉ nên có một dòng khai báo. Giữ các cấu hình còn lại như mẫu cho lần chạy đầu. Các key OpenAI/Gemini cũ được giữ nguyên; khi `LLM_PROVIDER=groq`, ứng dụng chỉ dùng `GROQ_API_KEY`.

Model `openai/gpt-oss-20b` được Groq phục vụ trên hạ tầng Groq; key cần tạo tại Groq Console. Định danh model tham khảo tại [trang GPT-OSS 20B](https://console.groq.com/docs/model/openai/gpt-oss-20b).

## 3. Chạy trong VS Code

1. Dừng phiên debug cũ bằng **Shift+F5**.
2. Vào **Run and Debug** (`Ctrl+Shift+D`), chọn **💬 BoneScope: Chatbot tra cứu tài liệu**.
3. Nhấn **F5**, mở `http://127.0.0.1:8765`.
4. Nhấn **Ctrl+F5 trong trình duyệt** để tải lại JavaScript/giao diện. Phần cuối trang sẽ ghi **Groq cần kết nối mạng**.
5. Gửi **xin chào** để kiểm tra giao diện và API cục bộ.
6. Gửi **Tài liệu nói gì về osteochondroma?** để kiểm tra retrieval và bản nháp Groq. Khi có kết quả, nhãn sẽ là **Groq · bản nháp chưa kiểm chứng**; bấm `[S1]` để đọc nguồn.

Chào hỏi được xử lý cục bộ nên không xác minh key/quota Groq. Câu hỏi có nguồn mới gọi model. Gọi lần đầu có thể cần nạp mô hình retrieval trên máy.

Chạy trong terminal PowerShell nếu không dùng debug:

```powershell
.\.venv\Scripts\python.exe -m uvicorn rag.demo_api:app --host 127.0.0.1 --port 8765
```

Dừng terminal bằng Ctrl+C. Chỉ chạy một máy chủ trên cổng 8765.

## 4. Thư viện đã có trong dự án

Không cần cài thêm gói `groq` ở workspace hiện tại. Ứng dụng dùng SDK OpenAI đã cài (`openai==2.54.0`), kết nối tới endpoint chính thức `https://api.groq.com/openai/v1`. Cách này được Groq hỗ trợ: [OpenAI compatibility](https://console.groq.com/docs/openai).

Khi dựng môi trường mới trên máy khác, cài các dependency của dự án:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements_api.txt -r requirements_rag.txt
```

Để quay lại OpenAI, đổi `LLM_PROVIDER=openai`, điền `OPENAI_API_KEY` và cấu hình OpenAI, rồi khởi động lại. Xem [hướng dẫn OpenAI](OPENAI_CHATBOT_SETUP_VI.md). Nhà cung cấp không tự thay đổi khi hết quota, thiếu key hoặc gặp lỗi.

## 5. Hạn mức và xử lý lỗi

Free Plan có giới hạn request và token theo phút/ngày, tùy model và tài khoản. Xem [Rate limits](https://console.groq.com/docs/rate-limits) và mục Limits trong Console để biết hạn mức thực tế. Phần hướng dẫn này không đảm bảo một số câu hỏi/ngày cố định vì mỗi câu hỏi kèm nhiều đoạn nguồn có độ dài khác nhau.

| Thông báo/mã lỗi | Cách xử lý |
| --- | --- |
| `groq_key_missing` | Điền `GROQ_API_KEY` rồi lưu `.env` và chạy lại máy chủ. |
| `groq_auth` | Key sai/bị thu hồi; tạo hoặc sao chép lại key đúng. |
| `groq_rate_limit`, `groq_quota` | Chờ hạn mức khôi phục, xem Limits; ứng dụng không tự gửi lại. |
| `groq_request_too_large` | Yêu cầu vượt giới hạn token. Thử câu hỏi cụ thể hơn hoặc giảm `GROQ_MAX_OUTPUT_TOKENS`; nếu vẫn lỗi, cần điều chỉnh lượng đoạn nguồn gửi vào. |
| `groq_model_unavailable`, `groq_permission` | Kiểm tra model còn hoạt động và quyền model/key của tài khoản. |
| `groq_config_invalid` | Với GPT-OSS, mức reasoning phải là `low`, `medium` hoặc `high`; giữ `low` cho lần đầu. |
| `groq_timeout`, `groq_connection` | Kiểm tra mạng/proxy/tường lửa, thử lại sau. |
| `groq_incomplete` | Không hiển thị bản nháp chưa hoàn tất. Thử yêu cầu ngắn hơn; giới hạn token có tính cả phần reasoning. |

Tra cứu cục bộ ngừng chờ sau 45 giây; bước model mặc định có deadline 35 giây; trình duyệt ngừng chờ toàn bộ sau 90 giây. Nút dừng chỉ dừng chờ ở trình duyệt; tác vụ đã gửi có thể vẫn được xử lý. Biến môi trường có sẵn của tiến trình được ưu tiên hơn `.env`.

## Bàn giao và kiểm tra

- `rag/generation.py`: chọn provider, key/model riêng, endpoint chính thức và lỗi có mã theo provider.
- `rag/demo_api.py`: `/api/config` chỉ trả tên provider/model và trạng thái có key, không trả key; trạng thái này không kiểm tra key trực tuyến.
- `rag/demo_web/app.js`, `index.html`: nhãn nhà cung cấp lấy từ cấu hình máy chủ và phản hồi thật.
- Groq dùng Responses API với reasoning `low`; bỏ trường `store` vì hướng dẫn Groq liệt kê trường này là chưa hỗ trợ. Nội dung hiển thị chỉ lấy `output_text`. Tham khảo [Groq Responses API](https://console.groq.com/docs/responses-api).
- `.env` đã được Git bỏ qua; `.env.example` chỉ chứa mẫu rỗng.

Kiểm tra tái lập, không gọi dịch vụ ngoài và không dùng key thật:

```powershell
.\.venv\Scripts\python.exe -m pytest rag/tests/test_demo_api.py rag/tests/test_generation.py -q
node --check rag/demo_web/app.js
```

Kết quả: **39 bài kiểm tra Python đạt**, gồm hồi quy OpenAI và luồng Groq qua SDK thật với mock transport: chọn đúng endpoint/key, payload, lỗi 401/404/413/429/500, không retry/fallback, cấu hình không hợp lệ, trạng thái UI không lộ key, bảo toàn nguồn và `answer_ready=false`. Có một cảnh báo deprecation Starlette/AnyIO hiện hữu. Chưa kiểm tra chất lượng tiếng Việt, số dư/quota hay độ trễ của Groq thật bằng tài khoản người dùng.

Kiểm tra Chrome headless đạt: lấy cấu hình Groq từ API thật, chào hỏi cục bộ, báo thiếu key ngay, nhãn Groq/OpenAI theo phản hồi mô phỏng, bấm nguồn và bố cục 390px; không có lỗi JavaScript. Ảnh kiểm tra: `.stitch/designs/groq-setup-required.png`. Máy chủ kiểm tra tạm cổng 8766 đã dừng; người dùng chạy phiên chính trong VS Code.

Giai đoạn 11, bộ dữ liệu và acceptance gate không thay đổi.
