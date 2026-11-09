# Groq Free dự phòng

Hướng dẫn cấu hình chính hiện tại: [OpenRouter chính, Groq Free dự phòng](OPENROUTER_CHATBOT_SETUP_VI.md).

Ứng dụng ưu tiên OpenRouter với model :free. Groq chỉ được gọi sau khi OpenRouter trả rate limit; tuyến dự phòng dùng model allowlist cho văn bản và ảnh. Groq miễn phí phụ thuộc tài khoản đang ở Free Plan. Nếu tài khoản đã nâng lên Developer, hãy tắt GROQ_FALLBACK_ENABLED để tránh phát sinh phí.
