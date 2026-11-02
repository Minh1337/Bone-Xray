# BoneScope — đối chiếu phần còn thiếu theo mục tiêu đồ án

Ngày đối chiếu: **31/10/2026 (UTC+07)**.

Mục tiêu ghi trong README: **“Đồ án hệ thống hội thoại hỗ trợ phân tích ảnh X-quang u xương kết hợp mô hình học sâu và RAG.”** Phạm vi người dùng xác định: báo cáo học tập thực nghiệm, không cung cấp cho bác sĩ/người bệnh. Yêu cầu hội thoại mới: trò chuyện đa chủ đề, dùng kho tài liệu khi hỏi về xương.

Bản này tổng hợp từ mã và hồ sơ đã đọc; không chạy lại suy luận ảnh, huấn luyện, benchmark hay audit Giai đoạn 11. Không thay đổi `answer_ready=false`, nhãn dữ liệu, trọng số hoặc trạng thái gate. Các tài liệu trạng thái ngày 29/10 là bằng chứng lịch sử; các cập nhật hội thoại ngày 31/10 nằm trong hướng dẫn mới.

## 1. Những gì đã có

| Thành phần | Bằng chứng hiện có | Giới hạn của kết luận |
| --- | --- | --- |
| Phân loại ảnh | `inference.py`, `model_definition.py`, `model/best_model.pt`; Swin + Cross-Attention kết hợp ảnh và metadata; đầu ra 10 lớp | Có triển khai inference không chứng minh độ chính xác trên ảnh ngoài hoặc khả năng mô tả/khoanh vùng tổn thương. |
| API ảnh | `xray_api.py`: kiểm ảnh, metadata, `/predict`, Top-1/Top-3/điểm toàn bộ lớp | Nhận ảnh kèm đủ 22 trường metadata; không phải luồng chỉ có ảnh. |
| Giao diện và lưu ca | `xray_ui.py`, `xray_web/`, `case_api.py`, `database.py` | Giao diện ảnh tách khỏi chatbot; lịch sử ca và lịch sử hội thoại chưa liên kết. |
| Retrieval | Corpus/index, `rag/retrieval.py`, policy, bộ evaluator/audit/replay và hồ sơ nguồn | Các điểm phát triển/hồi quy đã xem không phải kiểm định độc lập; có nhãn/khái niệm chưa được giải quyết đầy đủ. |
| Chatbot | `rag/demo_api.py`, `rag/generation.py`, `rag/conversation.py`, `rag/demo_web/` | Nhận văn bản; có ngữ cảnh gần đây và Groq/OpenAI; chưa nhận ảnh hoặc prediction của ca. |
| Kiểm tra hội thoại mới | 58 kiểm tra API/SDK với mock; kiểm tra Chrome; hai phép thử Groq thật về nhớ ngữ cảnh và viết lại query | Không phải đánh giá chất lượng phân loại ảnh hoặc độ đúng y khoa của giải thích sinh ra. |

## 2. Những việc cần hoàn thành trước tiên

### P1 — Luồng ảnh → dự đoán → tài liệu → hội thoại

Thiếu phần tích hợp cốt lõi của đề tài. Cần một luồng demo thống nhất:

1. Người dùng chọn ảnh và nhập/nạp metadata đúng của ảnh.
2. Gọi mô hình cục bộ qua chức năng dự đoán hiện có.
3. Hiển thị ảnh, Top-3, điểm số, thời gian và thông tin model.
4. Lấy nhãn/model output làm ngữ cảnh để tìm tài liệu liên quan, với ánh xạ nhãn rõ ràng.
5. Sinh giải thích học thuật có nguồn; phân biệt dự đoán mô hình với thông tin trong tài liệu và với nhãn tham chiếu.
6. Hỏi nối tiếp về chính ca nghiên cứu đang mở; đổi ảnh phải xóa kết quả/ngữ cảnh ca cũ.

Không gửi điểm dự đoán do trình duyệt tự khai như kết quả thật; sử dụng prediction ID/kết quả do máy chủ quản lý. Không diễn giải softmax thành xác suất mắc bệnh. Giữ ảnh ở pipeline cục bộ; xác định rõ phần kết quả/metadata nào được phép gửi nhà cung cấp LLM. Những thay đổi về ảnh/ca phải đi trong phạm vi demo học tập trên dữ liệu được phép, không mở toàn bộ nhánh y khoa đang được policy chặn.

### P2 — Đánh giá thực nghiệm mô hình ảnh

Cần một bộ kết quả có thể bảo vệ được trong báo cáo: manifest mẫu đánh giá, nhãn tham chiếu, nguồn/quyền dùng, quan hệ với train/validation/test; bảng số mẫu theo lớp, confusion matrix, macro-F1, precision/recall theo lớp, Top-1/Top-3 và thời gian suy luận trên máy dùng demo. Phải phân biệt kiểm tra code, parity với notebook và độ chính xác dự đoán.

Hồ sơ hiện hành chỉ ra checkpoint có nguồn BTXRD; danh sách split/patient mapping gốc chưa được khôi phục đầy đủ. Vì vậy, không lấy BTXRD hiện có làm tập kiểm tra độc lập của checkpoint này. Có thể làm thí nghiệm phát triển và ghi rõ giới hạn; để đưa ra nhận định tổng quát hơn cần dữ liệu độc lập phù hợp hoặc huấn luyện/đánh giá lại với split được lưu và kiểm soát rò rỉ.

### P3 — Hợp đồng đầu vào và phạm vi “đọc ảnh”

Mô hình hiện cần 22 trường: tuổi, giới tính, vị trí xương/khớp/chi và tư thế chụp. Cần làm giao diện nhập/nạp thuận tiện, giải thích rõ dữ liệu bắt buộc và xử lý thiếu dữ kiện bằng thông báo. Không tự đặt metadata thiếu bằng 0 hoặc đoán theo tên file.

Hiện đầu ra là phân loại trong 10 nhãn. Nếu đề cương chỉ yêu cầu phân loại và giải thích có nguồn, đây là chức năng cần hoàn thiện. Nếu đề cương còn yêu cầu xác định vị trí/khoanh vùng hoặc mô tả dấu hiệu X-quang chi tiết, đó là chức năng bổ sung cần phương pháp, dữ liệu và tiêu chí đánh giá riêng. Heatmap minh họa sự chú ý không tự chứng minh vùng tổn thương được xác định đúng.

### P4 — Liên kết nhãn với nguồn và đánh giá giải thích

Cần bảng ánh xạ từng nhãn của checkpoint sang thuật ngữ/tài liệu phù hợp. Không đồng nhất một tên nhãn dữ liệu với một khái niệm y khoa chỉ vì giống từ; các nhãn tổng hợp như `other bt`, `other mt` cần giới hạn giải thích. Hồ sơ trước đã ghi điểm vướng như `osteofibroma`/`osteofibrous dysplasia` và `synovial osteochondroma`/`synovial chondromatosis`.

Cần một bộ câu hỏi/ca mẫu để đánh giá: chọn đúng nguồn, mỗi ý có căn cứ trong đoạn nguồn, không nâng dự đoán thành kết luận, không nhầm ca khi đổi ảnh, phản hồi phù hợp khi mô hình sai hoặc tài liệu thiếu. Chấm câu trả lời sinh ra tách với điểm retrieval và với accuracy của classifier; giữ bài phát triển và bài đánh giá chưa dùng để chỉnh hệ thống rõ ràng.

### P5 — Tái lập và đối chiếu nguồn huấn luyện

Đối chiếu notebook/mã huấn luyện gốc với kiến trúc, preprocessing, metadata processor, thứ tự nhãn và checkpoint. Lưu split manifest, seed, cấu hình, log và kết quả đánh giá gốc khi khôi phục được; không suy có đủ split chỉ từ `group_column=patient_id` trong config. Ghi các thành phần chưa có để người đọc hiểu giới hạn tái lập.

### P6 — Demo và kiểm thử toàn chuỗi

Cần phép thử thật từ ảnh và metadata hợp lệ đến dự đoán, truy xuất tài liệu và hội thoại trên cùng giao diện. Bao gồm đổi ảnh, tải ảnh hỏng, metadata thiếu, model chưa nạp, API LLM lỗi/giới hạn và các câu nối tiếp đang nói về ảnh cũ. Các test UI/API với predictor giả không thay thế phép thử này.

### P7 — Báo cáo và bàn giao đúng phiên bản hiện tại

Cập nhật sơ đồ kiến trúc, mô tả phương pháp, dữ liệu/split, quy trình tái lập, các bảng thực nghiệm, giới hạn và demo. Báo cáo cần phân biệt ảnh được phân loại bởi Swin + metadata, văn bản được tìm bằng RAG và diễn đạt bằng LLM. Thêm so sánh/ablation phù hợp câu hỏi nghiên cứu nếu muốn tuyên bố RAG hay metadata làm hệ thống tốt hơn; chỉ có demo chạy được chưa chứng minh mức cải thiện.

README và một số tài liệu cũ còn ghi “offline hoàn toàn”, “chưa có chatbot/generator”. Thực tế chatbot mới dùng Groq/OpenAI trên mạng; kiến trúc hiện tại là mô hình ảnh/retrieval cục bộ kết hợp LLM từ xa. Cần cập nhật tài liệu chính thức hoặc xây phương án LLM local nếu offline hoàn toàn là tiêu chí bắt buộc. Ảnh/metadata/hội thoại được gửi hoặc lưu ở đâu phải được mô tả đúng cấu hình thực tế.

## 3. Thứ tự đề nghị cho phạm vi học tập

1. Chốt đầu ra demo là **phân loại ảnh 10 lớp + giải thích có nguồn + hỏi đáp theo ảnh đang chọn**, nếu phù hợp đề cương.
2. Làm P1 và P3: tích hợp ảnh và metadata vào chatbot.
3. Làm P4 và P6: ánh xạ nhãn, liên kết nguồn, kiểm tra luồng thật và các ca lỗi.
4. Làm P2/P5: hoàn thiện dữ liệu đánh giá, split, parity và kết quả thực nghiệm; ghi rõ mức bằng chứng có thể đạt.
5. Làm P7: cập nhật báo cáo, hình minh họa, video/demo, slide và hướng dẫn chạy.

Không quy đổi các khoảng trống này thành một tỷ lệ phần trăm tùy ý. Bảy acceptance gate của hồ sơ Stage 11 vẫn OPEN theo register; cần xác định tiêu chí phù hợp mục tiêu báo cáo học tập, không lấy gate lâm sàng làm phần trăm hoàn thành đồ án hoặc tự đóng gate.

## 4. Căn cứ đã đọc

- `README.md`: tên và mục tiêu đề tài.
- `docs/LO_TRINH_THUC_HIEN_DU_AN_AI.md`: chức năng và phạm vi kỹ thuật gốc.
- `docs/reference/STAGE11_USER_STATED_EDUCATIONAL_SCOPE_20261029.md`: mục tiêu học tập thực nghiệm.
- `START_HERE_NEXT_CODEX_VI.md`, `docs/PROJECT_STATUS_VI.md`: bằng chứng lịch sử và các giới hạn.
- `docs/guides/README_IMAGE_REFERENCE_VI.md`: BTXRD, split/overlap và giới hạn đánh giá.
- `inference.py`, `model/config.json`, `xray_api.py`, `xray_ui.py`, `api_validation.py`: pipeline ảnh/metadata.
- `rag/demo_api.py`, `rag/conversation.py`, `rag/generation.py`, `rag/demo_web/`: chatbot văn bản hiện hành.
- `docs/guides/CHATBOT_CONVERSATION_VI.md`: kiểm tra và giới hạn hội thoại ngày 31/10.
