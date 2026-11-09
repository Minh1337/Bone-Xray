# OpenRouter Free trước, Qwen trả phí dự phòng

Cập nhật: 09/11/2026. Mỗi yêu cầu bắt đầu bằng model OpenRouter miễn phí (`openrouter/free` cho chat và `google/gemma-4-31b-it:free` cho ảnh). Nếu model miễn phí bị giới hạn, trả lời chưa hoàn tất, phản hồi rỗng hoặc quá 15 giây, ứng dụng thử `qwen/qwen3.5-flash-02-23` trên OpenRouter. Đây là model trả phí theo token; model thực tế được ghi trên nhãn câu trả lời. Qwen nhận tối thiểu 2.400 token đầu ra và reasoning được giới hạn tối đa 512 token để giảm lỗi cạn ngân sách đầu ra. Khi Gemma ảnh bị rate limit, ứng dụng còn thử Free Router một lần trước khi dùng Qwen. Groq vẫn tắt theo cấu hình hiện tại.

## Cấu hình model và chi phí

- Model chat chính phải là `openrouter/free` hoặc ID có hậu tố `:free`. Model ảnh chính hiện là `google/gemma-4-31b-it:free`.
- Model trả phí dự phòng được khóa đúng vào `qwen/qwen3.5-flash-02-23`; model khác bị từ chối. Thời gian chờ mặc định trước khi chuyển là 15 giây và có thể chỉnh trong khoảng 5–40 giây.
- Bảng giá OpenRouter hiện niêm yết Qwen ở mức $0.065/triệu token đầu vào và $0.26/triệu token đầu ra. Ảnh được tính vào đầu vào theo lượng token xử lý, nên một lượt có ảnh thường tốn hơn lượt chỉ có chữ; chi phí thực tế xem trong OpenRouter Activity. Không có mức phí cố định cho mỗi ảnh.
- Groq vẫn là một tùy chọn Free riêng nhưng `GROQ_FALLBACK_ENABLED=false`; hiện không tham gia tuyến mặc định. Chỉ bật sau khi xác nhận tài khoản Groq vẫn ở Free Plan.

Xem [trang model Qwen và giá hiện hành](https://openrouter.ai/qwen/qwen3.5-flash-02-23), [giá/gói OpenRouter](https://openrouter.ai/pricing/), [Groq Free Plan](https://community.groq.com/t/do-i-get-charged-for-anything-on-the-groq-free-plan/832), [Groq models](https://console.groq.com/docs/models) và [Groq rate limits](https://console.groq.com/docs/rate-limits).

## Thiết lập key

1. Tạo API key tại [OpenRouter](https://openrouter.ai/settings/keys).
2. Mở file .env ở thư mục gốc BONESCOPE.
3. Dán key vào OPENROUTER_API_KEY=. Không gửi key qua chat, không chụp màn hình có key và không commit .env.
4. Kiểm tra các dòng cấu hình:

~~~dotenv
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your-key-here
OPENROUTER_MODEL=openrouter/free
OPENROUTER_VISION_MODEL=google/gemma-4-31b-it:free
OPENROUTER_PAID_FALLBACK_MODEL=qwen/qwen3.5-flash-02-23
OPENROUTER_FREE_FALLBACK_AFTER_SECONDS=15
GROQ_FALLBACK_ENABLED=false
GROQ_MODEL=openai/gpt-oss-20b
GROQ_VISION_MODEL=qwen/qwen3.8-27b
~~~

5. Không cần bật Groq để dùng Qwen dự phòng. Qwen chỉ được gọi sau khi model miễn phí bị giới hạn, trả lời chưa hoàn tất hoặc quá ngưỡng chờ.
6. Lưu .env, dừng máy chủ VS Code bằng Shift+F5, rồi nhấn F5 để chạy lại. Mỗi yêu cầu mới bắt đầu bằng OpenRouter.

## Cách hoạt động khi chạm hạn mức

- OpenRouter miễn phí trả lời trong ngưỡng: không gọi model trả phí.
- Model miễn phí timeout, rate limit, trả phản hồi chưa hoàn tất hoặc rỗng: chuyển sang Qwen trả phí; trường hợp model ảnh cố định rate limit thì thử Free Router trước.
- Nếu Qwen lỗi, ứng dụng báo lỗi và không tự lặp lại yêu cầu Qwen. Chỉ khi chủ dự án bật Groq và đã xác nhận Free Plan, lỗi rate limit của Qwen mới thử thêm tuyến Groq Free.
- Nhãn kết quả ghi “Qwen3.5 Flash · trả phí dự phòng” khi đã dùng model tính phí. Mỗi yêu cầu mới lại bắt đầu bằng model miễn phí.
- Ảnh được gửi đến provider thực tế đã xử lý yêu cầu. Ảnh không lưu vào SQLite; lịch sử chỉ lưu văn bản và nguồn.

## Lưu ý dữ liệu

Luồng chat ảnh gửi pixel ảnh và nội dung câu hỏi tới dịch vụ đã xử lý yêu cầu. Không đính kèm ảnh nhận diện cá nhân hoặc dữ liệu nhạy cảm. Luồng Swin phân tích ca BTXRD vẫn chạy cục bộ; khi xin AI viết giải thích, chỉ phần ngữ cảnh tóm tắt do máy chủ tạo được gửi tới provider. Lịch sử chat vẫn lưu cục bộ trong SQLite.

## Chẩn đoán nhanh

| Mã lỗi | Cách xử lý |
| --- | --- |
| openrouter_key_missing | Điền OPENROUTER_API_KEY trong .env. |
| openrouter_rate_limit | Model miễn phí đã bị giới hạn; ứng dụng tự thử Qwen trả phí dự phòng. |
| openrouter_timeout | Model miễn phí quá thời gian chờ; ứng dụng tự chuyển sang Qwen trả phí. |
| openrouter_model_not_allowed | Chỉ dùng model miễn phí đã cấu hình hoặc Qwen dự phòng được khóa trong ứng dụng. |
| groq_free_model_invalid | Dùng một trong hai model Groq đã cho phép; không thay bằng model trả phí. |
| provider_invalid | Đặt LLM_PROVIDER=openrouter; không chọn OpenAI/Groq làm tuyến chính. |

Không thực hiện API call thật trong quá trình chuyển đổi. Câu chào có thể được xử lý cục bộ; hãy kiểm tra phản hồi hiển thị provider khi gửi câu hỏi tạo câu trả lời.
