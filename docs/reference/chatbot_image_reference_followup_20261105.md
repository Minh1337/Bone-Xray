# Bàn giao luồng ảnh BTXRD theo mã — 05/11/2026

## Đã làm

- Hộp thoại **Ca ảnh · metadata** cho nạp một ảnh BTXRD theo `image_id` trong `reference/manifest.csv`, ví dụ `IMG000001`. Backend chỉ phục vụ tệp dưới `data/external_datasets/BTXRD/reference/source/` sau khi kiểm tra mã và đường dẫn; giao diện vẫn gọi endpoint SHA-256 hiện có để ghép metadata. Ảnh ngoài bộ dữ liệu tiếp tục cần metadata đúng ca hoặc dùng vision chat.
- Kiểm tra catalogue hiện hành: 3.725 hash khác nhau cho 3.746 ảnh; 9 nhóm trùng byte có metadata mâu thuẫn. Endpoint từ chối tự ghép metadata cho 9 nhóm và không nạp ảnh theo mã từ các nhóm đó. Nếu chỉ nhãn khác nhau nhưng metadata giống, chỉ điền metadata, không trả nhãn mâu thuẫn.
- Đã cập nhật hướng dẫn chatbot và bộ ảnh tham chiếu. Không thay checkpoint, retrieval config, corpus/index hoặc trạng thái acceptance. `answer_ready=false`; G1–G7 `OPEN`.
- Luồng SQLite được siết thêm: phản hồi lưu đến muộn không gắn lại ID cũ vào cuộc trò chuyện mới; mở lịch sử đến muộn không ghi đè màn hình mới; API từ chối tạo lại hội thoại đã xóa. Chạm giới hạn cục bộ sẽ báo lỗi, không âm thầm xóa lịch sử cũ.
- Đồng bộ hệ thống giao diện Pro Obsidian & Bioluminescent Cyan (`rag/demo_web/graphite.css`) cho các thành phần mới ngày 05/11 (`#attach-image`, `.image-attachment`, `.case-reference-picker`, `#case-reference-load`, `#case-image-match-note`, `#ask-ai-about-case-image`) và bổ sung kiểm thử tự động toàn chuỗi (`test_btxrd_reference_image_lookup_autofill_and_real_model_inference`, `test_generate_image_answer_sends_data_url_and_reports_rate_limit_wait`).

## Kiểm chứng

- `python -m pytest api_tests rag/tests tests ui_tests -q` qua `.venv` sau khi bổ sung test tích hợp BTXRD theo mã + suy luận thật, test phân tích catalogue/calibration và test vision transport: **176 passed, 132 subtests passed**, 1 cảnh báo deprecation của Starlette. Kiểm tra tập trung SQLite + API: **20 passed**.
- `node --check rag/demo_web/app.js`: pass.
- `python -m rag.audit --report-dir docs/reference/stage11_policy_rerun_20261029_cureus_abcrouting_v1`: PASS (22 nguồn, 794 chunk).
- `python -m rag.replay_reports --bundle docs/reference/stage11_policy_rerun_20261029_cureus_abcrouting_v1`: PASS (`16/16` báo cáo khớp, `0` preflight mismatch).
- `python -m tools.verify_stage11_registers`: PASS (`24/24` prepared-artifact references khớp SHA-256, `15` cohort rows, `0/7` gate CLOSED).
- `git diff --check`: pass, chỉ có cảnh báo chuyển LF/CRLF của Git trên Windows.
- Smoke API & kiểm thử tích hợp trên dữ liệu thật: `GET /api/reference-images/IMG000001` và `IMG000002` trả 200; `POST /api/case/metadata-match` trả `matched=true` (`sha256_exact`); `POST /api/case` chạy mô hình Swin + Cross-Attention thật (`model/best_model.pt`) trả Top-1 `osteosarcoma` cho `IMG000002` với `answer_ready=false`; `GET /api/reference-images/IMG000430` chặn đúng nhóm trùng byte mâu thuẫn metadata (`409`).
- Test image-chat dùng provider giả lập và mock transport (`httpx.MockTransport`): xác nhận gửi data URL ảnh base64 tới model vision (`qwen/qwen3.8-27b`), trích xuất thông báo chờ `retry-after` khi gặp `429`, phản hồi có `answer_ready=false`, không lưu ảnh/lượt chat vào SQLite, từ chối file giả ảnh. Không chứng minh Groq/OpenAI thật trả lời được trên tài khoản này nếu không gọi mạng ngoài.
- Browser smoke trên máy chủ tạm `127.0.0.1:8769`: mở hộp thoại, nhập `IMG000001`, bấm **Nạp ảnh**; trình duyệt hiển thị ảnh 0,43 MiB và thông báo khớp SHA-256. Bước metadata kế tiếp hiển thị tuổi 48, giới tính F và 20/20 trường vị trí/tư thế được điền. Máy chủ tạm đã dừng. Chưa gọi Groq/OpenAI thật; các API tests không sử dụng khóa cá nhân.
- Manifest kiểm chứng tổng hợp mới: [`docs/reference/stage12_integrated_chatbot_verification_20261105.json`](stage12_integrated_chatbot_verification_20261105.json) (và cập nhật đồng bộ [`stage12_integrated_chatbot_verification_20261103.json`](stage12_integrated_chatbot_verification_20261103.json)).

## Việc tiếp theo

1. Trong VS Code, F5 cấu hình chatbot, Ctrl+F5 trình duyệt, mở **Ca ảnh · metadata**, nhập `IMG000001`, bấm **Nạp ảnh** và chạy mô hình nếu muốn. Bước giải thích có thể cần provider; riêng nhập ảnh và metadata đã được kiểm tra trên trình duyệt.
2. Kiểm tra trực tiếp luồng vision với tài khoản provider đã cấu hình, gồm 429, timeout và ảnh không thuộc BTXRD; không gửi ảnh người bệnh thật.
3. Giữ các đánh giá BTXRD là in-source; cần split/patient IDs và cohort độc lập trước khi công bố hiệu năng ngoài nguồn. G1–G7 vẫn chờ reviewer/owner theo hồ sơ Giai đoạn 11.

Working tree đang có nhiều thay đổi chưa commit từ các lượt chatbot trước. Xem `git status --short` trước khi sửa; đừng ghi đè tệp `.env` hoặc `data/chat_history.db` của người dùng. Checkpoint cũ là snapshot lịch sử và chưa bao gồm toàn bộ thay đổi hiện nay.
