# Giao diện chatbot BoneScope

Cập nhật giao diện 13/11/2026. Research Studio dùng logo BoneScope cùng màn hình X-quang và có hai lối vào chính trên màn hình chào. Giao diện dùng HTML, CSS và JavaScript thuần với font hệ thống.

Phần tạo bản nháp ưu tiên **OpenRouter Free**; sau timeout, rate limit, phản hồi rỗng hoặc chưa hoàn tất có thể chuyển sang **Qwen trả phí dự phòng** (`qwen/qwen3.5-flash-02-23`). Groq chỉ tham gia khi bật rõ ràng và hiện mặc định tắt. Nhãn câu trả lời cho biết model thực tế. Xem [hướng dẫn cấu hình](OPENROUTER_CHATBOT_SETUP_VI.md).

Chọn **Tra cứu cục bộ** để xem các đoạn nguồn trên máy. Chế độ này cần chỉ mục RAG và dùng mẫu giải thích cục bộ cho kết quả X-quang. **Trò chuyện + tài liệu** và **Hỏi AI theo tài liệu** dùng nhà cung cấp đã cấu hình. Xem [hướng dẫn hội thoại và câu hỏi thử](CHATBOT_CONVERSATION_VI.md).

Ô chat có nút **Ảnh** (hoặc dán trực tiếp `Ctrl+V` / kéo–thả tệp ảnh vào ô nhập) để đính kèm JPEG, PNG hoặc WEBP (tối đa 10 MiB). Vision chat dùng `google/gemma-4-31b-it:free` (model multimodal miễn phí), với prompt yêu cầu trả lời tiếng Việt, tách quan sát khỏi khả năng giải thích, thận trọng với chồng hình và ký hiệu R/L, không tự đoán metadata, nhãn hay điểm phân loại. Máy chủ chỉ thêm vị trí/tư thế từ BTXRD khi SHA-256 khớp duy nhất với manifest; không đưa nhãn ground-truth vào prompt. Ảnh không khớp chỉ được phân tích theo pixel và AI phải nói rõ vùng/chi tiết không chắc chắn. Sau phân tích, hệ thống tìm tối đa 4 đoạn tài liệu BoneScope dựa trên câu hỏi và phần mô tả ảnh; các thẻ này là nguồn đọc thêm, không xác nhận phát hiện trên ảnh. Nếu kho không có đoạn phù hợp hoặc đang bận, kết quả phân tích ảnh vẫn hiển thị và giao diện báo tình trạng tra cứu. Sau khi gửi, tệp được gỡ khỏi ô soạn; ảnh được giữ trong RAM của tab theo từng cuộc trò chuyện và gửi lại ở các lượt tiếp theo. **Bỏ ảnh** hủy tệp đang chờ gửi; **Xóa ngữ cảnh** gỡ ảnh đã gửi khỏi chat hiện tại. Ảnh không lưu vào SQLite; đóng/tải lại tab hoặc mở lịch sử ở tab khác thì cần đính kèm ảnh lại. Mọi phản hồi ảnh vẫn chưa kiểm chứng và không dùng để chẩn đoán.

Nút **Phân tích X-quang** chạy bộ Swin cục bộ. Khi chọn ảnh, hệ thống đối chiếu SHA-256 với manifest BTXRD đã tải trong `data/external_datasets/BTXRD/`; chỉ ảnh gốc trùng byte mới tự điền metadata. Kết quả cho ảnh BTXRD không phải đánh giá độc lập vì checkpoint được huấn luyện từ cùng nguồn. Ảnh không khớp có thể chuyển sang nút **Hỏi AI về ảnh** để mô tả trực quan mà không điền metadata. Không suy đoán tuổi/giới tính, không đặt trường chưa biết thành 0; nhập thủ công chỉ khi có metadata được ghi nhận cho đúng ảnh. Metadata vẫn có thể nạp từ `cases.json`.

Nếu không muốn tìm ảnh bằng Explorer, mở **Phân tích X-quang**, nhập mã như `IMG000001` vào ô **Nạp ảnh BTXRD có sẵn theo mã** rồi bấm **Nạp ảnh** (hoặc bấm trực tiếp một nút **Mẫu nhanh** như `IMG000002 · osteosarcoma`, `IMG000240 · osteochondroma`, `IMG000234 · giant cell tumor`, `IMG000236 · simple bone cyst`, `IMG000001 · other mt`, `IMG001868 · no-tumor`). Mã nằm trong cột `image_id` của `data/external_datasets/BTXRD/reference/manifest.csv`; ảnh gốc nằm trong `data/external_datasets/BTXRD/reference/source/BTXRD/images/`. Giao diện tải ảnh từ máy chủ local và đối chiếu hash để tự điền 22 metadata. Ảnh có cùng byte nhưng metadata mâu thuẫn trong manifest sẽ bị chặn, không tự điền. Bước này không cần API key hoặc Groq; bước **Chạy mô hình & giải thích** dùng mẫu giải thích trên máy khi chọn **Tra cứu cục bộ**, hoặc có thể gọi nhà cung cấp AI ở chế độ hỏi đáp.

## Lịch sử hội thoại trên máy

Các lượt hoàn tất tự lưu trong `data/chat_history.db` bằng SQLite. Mục **Lịch sử hội thoại** ở thanh bên cho phép mở lại, đổi tên và xóa hội thoại. Bản ghi gồm văn bản hỏi đáp và đoạn nguồn. Khi mở lại một lượt hỏi ảnh, hãy đính kèm lại tệp nếu cần hỏi tiếp về ảnh đó.

Mỗi lần bấm **Cuộc trò chuyện mới**, giao diện bỏ mã phiên đang mở; câu trả lời lưu đến muộn không được gắn vào phiên mới. Máy chủ không tạo lại một hội thoại đã xóa nếu một yêu cầu lưu cũ đến sau. Khi chạm giới hạn lưu cục bộ (500 hội thoại hoặc 2.000 tin nhắn trong một hội thoại), ứng dụng báo lỗi lưu thay vì tự xóa các lượt cũ.

Cơ sở dữ liệu nằm trên máy chạy FastAPI và đã được Git bỏ qua (`data/*.db`). Có thể sao lưu hoặc xóa `data/chat_history.db` khi máy chủ đã dừng. Đây là kho cục bộ đơn người dùng, không có tài khoản hay mã hóa ở tầng ứng dụng; chỉ chạy máy chủ trên `127.0.0.1` và không nhập dữ liệu nhận diện người bệnh.

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
- Giao diện sáng/tối đồng bộ cho chatbot và hộp thoại ca ảnh; chuyển động khi hiện nội dung và chờ kết quả, tự tắt khi hệ điều hành bật hạn chế chuyển động.
- Hộp thoại nhập ca ba bước có kiểm tra dữ liệu, nạp nhanh ảnh BTXRD theo mã `IMG000001` hoặc 6 chip mẫu tiêu biểu (`.btxrd-sample-chip`), tự khớp SHA-256 cho 22 trường metadata, thanh tiến độ 20 trường nhị phân, tóm tắt trước khi chạy và trạng thái dừng chờ; ô nhập câu hỏi hỗ trợ đính kèm ảnh bằng nút **Ảnh**, dán `Ctrl+V` hoặc kéo–thả. Sau khi gửi, phần đính kèm trong composer biến mất; ảnh nằm ở thanh ngữ cảnh riêng và được giữ riêng cho từng chat trong RAM của tab đến khi xóa ngữ cảnh hoặc đóng/tải lại tab.

Lịch sử hội thoại được lưu trên máy trong SQLite và có thể mở lại. Ngữ cảnh ca ảnh chỉ tồn tại tạm thời; bản ghi chat không chứa ảnh, metadata hay mã ca. Nút dừng ngừng chờ ở trình duyệt; tác vụ đã gửi có thể vẫn được máy chủ/nhà cung cấp AI xử lý.

## Thiết kế và bàn giao

- Đặc tả triển khai hiện tại: [`rag/demo_web/DESIGN.md`](../../rag/demo_web/DESIGN.md).
- Các ảnh/mockup thiết kế đã được loại khỏi repository vì không cần cho runtime; giao diện thực tế được phục vụ trực tiếp từ [`rag/demo_web/`](../../rag/demo_web/).

Giao diện thực tế dùng font hệ thống, SVG nội tuyến và các chức năng đang có. Không hiển thị tài khoản, nguồn, số lượng tài liệu hoặc kết quả mô phỏng như dữ liệu thật.

## Kiểm tra đã thực hiện

**Tiếp nối 09/11:** kiểm tra Chrome headless tái lập được bằng `.\.venv\Scripts\python.exe -m pytest ui_tests/test_chatbot_browser.py -q`. Cần Chrome/Chromium đã cài và module Python `websockets` hỗ trợ tham số `proxy`; nếu thiếu, pytest báo SKIP và không được tính là đã kiểm chứng trình duyệt. Có thể chỉ đường dẫn Chrome qua biến `BONESCOPE_TEST_CHROME`. Kiểm tra dùng hồ sơ trình duyệt/ảnh hình học/SQLite tạm, phản hồi AI và retrieval giả lập, không gọi provider. Đã đạt các luồng thử lại đúng ảnh sau lần lưu đầu, hỏi ảnh qua nhiều lượt, đổi chat rồi quay lại, xóa ngữ cảnh, reload không giữ ảnh, mở/đổi tên/xóa chat, giữ định dạng câu trả lời và nhãn nguồn đọc thêm, giao diện 320×568/390×844 và lưu chế độ tối. Toàn suite mới nhất: **172 passed / 132 subtests**. Xem [bản ghi kiểm chứng 09/11](../reference/chatbot_browser_regression_20261109.json). Các kiểm tra bên dưới là bằng chứng lịch sử.

Đã kiểm tra trên Chrome headless: phản hồi “xin chào” qua API FastAPI thật; gợi ý; nguồn và trích dẫn; không diễn giải thẻ HTML trong câu trả lời; xuất Markdown; sáng/tối và lưu tùy chọn; hướng dẫn; lỗi/thử lại; dừng chờ; tạo cuộc trò chuyện mới khi yêu cầu đang chạy. Không có lỗi JavaScript ở các luồng đã kiểm tra.

Đã đo ở 1366×768, 390×844, 320×568: không tràn ngang, ô nhập nằm trong khung nhìn. Ảnh desktop được chụp thêm ở 1440×900. Phản hồi có nguồn và lỗi dùng fixture giả lập để kiểm tra giao diện; không gọi Gemini, không kiểm định chất lượng retrieval hay câu trả lời. Máy chủ kiểm tra tạm dùng cổng 8766 được dừng sau kiểm tra.

Lịch sử SQLite được kiểm tra riêng trong [bản ghi xác minh](../reference/chat_history_sqlite_verification_20261103.json): 49 kiểm thử liên quan đạt; kiểm tra trình duyệt xác nhận gửi lượt chat qua luồng giao diện, tải lại, mở lại câu trả lời và nguồn đã lưu, rồi xóa hội thoại. Kiểm tra riêng cũng xác nhận dữ liệu còn sau khi khởi động lại tiến trình FastAPI trên cùng DB tạm. Lượt trả lời AI được giả lập; không gọi Groq/OpenAI. Tất cả kiểm thử dùng DB tạm, không chạm lịch sử thật của người dùng.

Phạm vi Giai đoạn 11 và các acceptance gate không thay đổi. Backend tiếp tục trả `answer_ready=false`.

Provider thật cũng đã có [smoke riêng 09/11](../reference/chatbot_provider_smoke_20261109.json): câu chữ Free đạt sau 3,343 giây; ảnh hình học tự tạo được Qwen xử lý sau tổng 29,594 giây, một lượt trả phí với cost được báo về $0,000248755. Không dùng ảnh X-quang hoặc lịch sử người dùng; chưa đánh giá chất lượng đọc ảnh. Đây là bằng chứng tách riêng với regression offline ở trên.
