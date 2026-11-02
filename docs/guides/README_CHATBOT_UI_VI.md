# Giao diện chatbot BoneScope

Cập nhật: 31/10/2026. Giao diện được triển khai trực tiếp trong `rag/demo_web`, dựa trên bố cục Stitch và các token trong `rag/demo_web/DESIGN.md`. Dùng HTML, CSS, JavaScript thuần; không cần chạy npm, Vite hay tải font từ Internet.

Phần tạo bản nháp hiện hỗ trợ **Groq/OpenAI**, chọn bằng `LLM_PROVIDER` trong `.env`. Workspace đang chọn Groq: xem [hướng dẫn Groq Free](GROQ_CHATBOT_SETUP_VI.md). Có thể chọn lại OpenAI theo [hướng dẫn kết nối OpenAI](OPENAI_CHATBOT_SETUP_VI.md).

Chatbot đã có **hội thoại đa chủ đề và ngữ cảnh gần đây**, dùng nguồn khi hỏi về xương. Xem [hướng dẫn hội thoại và câu hỏi thử](CHATBOT_CONVERSATION_VI.md). Chế độ mặc định trên giao diện là “Trò chuyện + tài liệu”; có thể chọn “Chỉ tra cứu tài liệu”.

## Chạy bằng VS Code

1. Mở thư mục gốc `BONESCOPE` trong VS Code.
2. Vào **Run and Debug** (`Ctrl+Shift+D`).
3. Chọn **💬 BoneScope: Chatbot tra cứu tài liệu** rồi bấm **F5**.
4. Khi máy chủ sẵn sàng, trình duyệt tự mở. Có thể mở thủ công `http://127.0.0.1:8765`.
5. Nếu còn giao diện cũ, bấm **Ctrl+F5** trong trình duyệt để tải lại CSS/JavaScript.
6. Dừng máy chủ bằng **Shift+F5** trong VS Code.

Không mở `index.html` bằng cách nhấp đúp: giao diện và API dùng chung máy chủ FastAPI. File `.env` ở thư mục gốc được cấu hình debug nạp; API key chỉ nằm phía máy chủ. Khi cổng 8765 đang được dùng, dừng phiên chạy trước bằng cửa sổ đã khởi động nó trước khi bấm F5 lần nữa.

## Các thao tác đã triển khai

- Bố cục desktop với thanh điều hướng và danh sách câu hỏi trong cuộc trò chuyện hiện tại.
- Menu thu gọn trên điện thoại, điều khiển bằng bàn phím và phím Escape.
- Màn hình chào, câu hỏi gợi ý, ô nhập tự tăng chiều cao, giới hạn 1.000 ký tự.
- Enter gửi; Shift+Enter xuống dòng; không gửi khi đang ghép ký tự bằng bộ gõ.
- Trạng thái đang chờ, dừng chờ, thông báo lỗi và thử lại.
- Hiển thị đoạn văn, tiêu đề, danh sách, chữ đậm và mã ngắn bằng DOM an toàn.
- Bấm `[S1]`, `[S2]` để mở và chuyển đến đoạn nguồn tương ứng. Nguồn giữ giấy phép, liên kết, ID và hash đối chiếu.
- Sao chép bản nháp; xuất cuộc trò chuyện thành Markdown, kèm các đoạn nguồn của từng phản hồi.
- Chế độ sáng/tối lưu trên trình duyệt; hộp hướng dẫn sử dụng.
- Cuộc trò chuyện mới hủy chờ và bỏ qua kết quả cũ đến muộn.

Cuộc trò chuyện nằm trong bộ nhớ của tab; tải lại trang sẽ xóa nội dung. Dùng nút xuất để lưu trước khi đóng. Nút dừng ngừng chờ ở trình duyệt; tác vụ đã gửi có thể vẫn được máy chủ/nhà cung cấp AI xử lý.

## Thiết kế và bàn giao

- Dự án Stitch riêng: https://stitch.withgoogle.com/projects/7327687804675427525
- ID màn hình, hệ thống thiết kế, tệp triển khai và ảnh xem trước: `.stitch/metadata.json`.
- HTML tham chiếu Stitch: `.stitch/designs/desktop-reference.html` (bản mẫu, không phải tệp chạy ứng dụng).
- Ảnh giao diện thật: `.stitch/designs/chatbot-desktop.png`, `chatbot-mobile.png`, `chatbot-dark.png`.

Giao diện thực tế điều chỉnh bản Stitch để dùng font hệ thống, SVG nội tuyến và các chức năng đang có. Không hiển thị tài khoản, nguồn, số lượng tài liệu hoặc kết quả mô phỏng như dữ liệu thật.

## Kiểm tra đã thực hiện

Đã kiểm tra trên Chrome headless: phản hồi “xin chào” qua API FastAPI thật; gợi ý; nguồn và trích dẫn; không diễn giải thẻ HTML trong câu trả lời; xuất Markdown; sáng/tối và lưu tùy chọn; hướng dẫn; lỗi/thử lại; dừng chờ; tạo cuộc trò chuyện mới khi yêu cầu đang chạy. Không có lỗi JavaScript ở các luồng đã kiểm tra.

Đã đo ở 1366×768, 390×844, 320×568: không tràn ngang, ô nhập nằm trong khung nhìn. Ảnh desktop được chụp thêm ở 1440×900. Phản hồi có nguồn và lỗi dùng fixture giả lập để kiểm tra giao diện; không gọi Gemini, không kiểm định chất lượng retrieval hay câu trả lời. Máy chủ kiểm tra tạm dùng cổng 8766 được dừng sau kiểm tra.

Phạm vi Giai đoạn 11 và các acceptance gate không thay đổi. Backend tiếp tục trả `answer_ready=false`.
