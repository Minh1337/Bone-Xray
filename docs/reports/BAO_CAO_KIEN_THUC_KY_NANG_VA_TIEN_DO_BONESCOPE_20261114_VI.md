# Báo cáo kiến thức kỹ năng và tiến độ thực hiện dự án BoneScope

**Ngày lập:** 14/11/2026 · **Mã nguồn đối chiếu:** `82cd17d`

**Đối tượng đọc:** người thực hiện đồ án và giảng viên hướng dẫn · **Phạm vi:** nguyên mẫu học tập và thực nghiệm chạy cục bộ trên Windows

## Tóm tắt điều hành

BoneScope đã hình thành một nguyên mẫu tích hợp: nhận ảnh X-quang và 22 trường metadata để chạy checkpoint phân loại 10 nhãn; tra cứu 22 nguồn văn bản với 794 đoạn; trò chuyện đa lượt; nhận ảnh để mô tả bằng model thị giác bên ngoài; và lưu lịch sử chữ cùng nguồn trong SQLite. Báo cáo này trả lời hai câu hỏi: **mỗi phần đã vận dụng kiến thức, công cụ và kỹ năng nào**; và **từ mốc khởi tạo đến nay những đầu ra nào đã hoàn thành**. Mỗi nhận định về tiến độ được gắn với mã nguồn, commit hoặc record kiểm tra để có thể đối chiếu.

Nguyên mẫu có thể trình diễn cục bộ trong phạm vi học tập. Lượt xác minh ngày 13/11 ghi 216 kiểm thử đạt, 1 skip trong sandbox, 227 subtests đạt; Chrome smoke riêng đạt 1/1 với dữ liệu tổng hợp và AI giả lập. Audit RAG đạt 22 nguồn/794 đoạn, replay 16/16. Đây là **bằng chứng kỹ thuật**, chưa phải đánh giá độc lập chất lượng chẩn đoán hoặc độ đúng của câu trả lời. Bảy gate G1–G7 vẫn `OPEN`; `answer_ready=false`. Đối chiếu hẹp của Giai đoạn 11 có 6/7 bước có artifact, bước hiệu chỉnh ngưỡng từ nhãn độc lập còn chờ. Vì vậy báo cáo không gán một tỷ lệ “100% toàn dự án”.

**Cách đọc báo cáo:** phần 1–3 giải thích hệ thống và kiến thức; phần 4 ánh xạ công nghệ đến nơi dùng; phần 5 trình bày kỹ năng qua quy trình thực hiện; phần 6 là bảng tiến độ theo thời gian; phần 7 nêu phần đã đủ cho demo và phần nghiên cứu còn mở. Báo cáo tổng kết kỹ thuật và số liệu thí nghiệm chi tiết nằm trong [báo cáo đồ án ngày 13/11](BAO_CAO_TONG_KET_DO_AN_BONESCOPE_20261113_VI.md).

<!-- pagebreak -->

## 1 Mục tiêu và cách xác định mức hoàn thành

BoneScope ban đầu là bộ kiểm tra ảnh X-quang cục bộ; sau đó được mở rộng thành Research Studio có kho tài liệu và chatbot. Đối tượng sử dụng đã được người dùng xác định là **học tập và báo cáo thực nghiệm**, không cung cấp cho bác sĩ hoặc người bệnh. Vì vậy “đã hoàn thành” trong bảng tiến độ nghĩa là **có chức năng hoặc artifact cụ thể, có lệnh tái lập hay kiểm thử tương ứng**; không nghĩa là đã được duyệt để dùng lâm sàng, triển khai công cộng, phát hành ảnh hoặc có câu trả lời AI luôn chính xác.

Các từ dùng thống nhất trong báo cáo:

| Thuật ngữ | Nghĩa trong BoneScope |
|---|---|
| Checkpoint | Trọng số mô hình ảnh hiện có trong `model/best_model.pt`; dự án tích hợp và kiểm tra suy luận, báo cáo này không nhận đã huấn luyện lại. |
| Metadata | 22 trường đầu vào đi cùng ảnh; bao gồm tuổi, giới và các cờ vị trí giải phẫu/tư thế theo schema model. |
| RAG | Luồng tìm đoạn văn bản liên quan rồi cung cấp chúng cho quá trình tạo câu trả lời hoặc hiển thị để người dùng tự đọc. |
| Corpus và chunk | Tập nguồn văn bản có xuất xứ và các đoạn được chia để lập chỉ mục; hiện có 22 nguồn, 794 đoạn. |
| Provenance | Thông tin nguồn, giấy phép, URL, ngày và hash cho phép truy vết artifact. |
| Đã kiểm tra kỹ thuật | API, giao diện, dữ liệu và phép tái lập hoạt động theo các ca kiểm thử đã ghi. |
| Đánh giá độc lập | Dữ liệu/nhãn và quyết định không dùng để xây dựng, chỉnh policy hay chọn model; trạng thái này chưa đạt. |

Một số thành phần nền là **tài nguyên bên ngoài được sử dụng**, gồm bộ dữ liệu BTXRD, Swin, multilingual E5 và model ngôn ngữ/thị giác qua provider. Đóng góp kỹ thuật thể hiện ở cách tích hợp chúng, hợp đồng dữ liệu, giao diện, luồng truy xuất, lưu trữ, kiểm tra và báo cáo giới hạn. Không đánh đồng phần sử dụng thư viện/model có sẵn với công bố một thuật toán hoặc bộ dữ liệu mới.

## 2 Bức tranh kiến trúc và luồng dữ liệu

| Luồng | Đầu vào | Xử lý chính | Đầu ra và lưu trữ |
|---|---|---|---|
| Phân loại cục bộ | Ảnh hợp lệ + đủ 22 metadata | Tiền xử lý ảnh; Swin, nhánh metadata và Cross-Attention; xếp 10 điểm | Top-1/Top-3, điểm softmax, thời gian chạy; ca có thể được người dùng lưu ở SQLite riêng. |
| Ghép metadata BTXRD | Byte ảnh và manifest cục bộ | So SHA-256; chỉ chấp nhận kết quả duy nhất, không mâu thuẫn | Tự điền metadata đúng bản ghi; ảnh ngoài hoặc nhóm mâu thuẫn không được tự gán. |
| Tra cứu tài liệu | Câu hỏi về xương | BM25, embedding E5 và hợp nhất thứ hạng; policy kiểm soát phạm vi | Các đoạn ứng viên kèm URL, ID nguồn, hash hoặc trạng thái từ chối; `answer_ready=false`. |
| Chat đa chủ đề | Câu hỏi và lịch sử gần đây | Định tuyến câu hỏi tổng quát/tài liệu; gọi provider theo cấu hình | Bản nháp trả lời; lưu chữ và nguồn khi lượt hoàn tất. |
| Chat ảnh | JPEG/PNG/WEBP trong ô chat | Gửi ảnh đến vision provider; tìm thêm tối đa 4 đoạn liên quan | Mô tả ảnh có giới hạn; byte ảnh tồn tại tạm trong tab, không vào SQLite chat. |

**Hai loại lưu trữ khác nhau.** `bonescope/database.py` quản lý ca phân loại, gồm tên/hash ảnh, metadata, điểm, nhận xét và nhãn hiệu chỉnh; schema này không lưu byte ảnh. `rag/chat_history.py` quản lý cuộc trò chuyện, chỉ giữ văn bản và những trường nguồn được phép. Khi nói “không lưu ảnh trong lịch sử chat”, điều đó không có nghĩa mọi metadata hoặc hash ca đều không xuất hiện trong cơ sở dữ liệu quản lý ca. Hai luồng có mục đích và cấu trúc khác nhau.

## 3 Kiến thức và kỹ năng theo từng phần của dự án

### 3.1 Chuẩn bị môi trường và tổ chức mã

**Kiến thức vận dụng:** môi trường ảo Python, ghim phiên bản dependency, tách mã ứng dụng khỏi script khởi chạy, cấu hình debug, quản lý biến môi trường và vòng đời tiến trình. `requirements.txt`, `requirements_api.txt`, `requirements_rag.txt` và `requirements_dev.txt` tách nhóm phụ thuộc; `.vscode/launch.json` cung cấp cấu hình F5 cho chatbot, API và giao diện. `scripts/` chứa launcher Windows; `bonescope/`, `rag/` và `tools/` chia rõ ứng dụng, truy xuất và công cụ đánh giá.

**Cách dùng trong đồ án:** chạy server bằng Uvicorn ở `127.0.0.1`, nạp API key từ `.env` phía máy chủ, giữ `.env` ngoài Git. Việc đổi module sau refactor được đối chiếu lại với đường dẫn launcher và bản ghi hash. Kỹ năng thể hiện ở khả năng tạo môi trường chạy lại và sửa lỗi đường dẫn/cổng sau khi đổi cấu trúc, không chỉ ở việc viết một tệp Python đơn lẻ. Hướng dẫn thao tác nằm ở [README tiếng Việt](../../README_VI.md).

### 3.2 Dữ liệu ảnh và nguồn gốc BTXRD

**Kiến thức vận dụng:** đọc bảng dữ liệu, ánh xạ nhãn, kiểm tra tính đầy đủ, kiểm tra trùng byte, SHA-256, provenance và khác biệt giữa giấy phép bài báo với quyền của từng ảnh. Bài báo gốc mô tả BTXRD gồm 3.746 ảnh và một bảng dữ liệu đi kèm [1]. Trong dự án, `tools/prepare_btxrd_reference.py` dựng manifest cục bộ; `tools/analyze_btxrd_catalogue.py` thống kê phân bố, ảnh trùng và trường hợp mâu thuẫn. Catalogue ghi 3.725 hash duy nhất, 21 nhóm trùng byte và 9 nhóm có metadata mâu thuẫn.

**Cách dùng:** ảnh người dùng chọn được băm và so với manifest. Chỉ khi có đúng một bản ghi hợp lệ, dữ liệu của bản ghi mới được đưa vào form để chạy classifier. Tên tệp, nội dung pixel hoặc câu trả lời của model thị giác **không** được dùng làm bằng chứng tự điền tuổi, giới hay nhãn thật. Đây là kỹ năng thiết kế luồng dữ liệu theo nguồn gốc và xử lý bất định. Vì quyền ở cấp từng ảnh chưa được giải quyết đầy đủ, báo cáo không đề nghị phân phối lại archive hoặc ảnh mẫu ra ngoài môi trường được phép.

### 3.3 Tiền xử lý ảnh và mô hình học sâu

**Kiến thức vận dụng:** ảnh số, tensor, chuẩn hóa đầu vào, suy luận PyTorch, backbone Swin Transformer, mạng MLP cho metadata, MultiheadAttention và hàm softmax. Swin dùng biểu diễn phân cấp với shifted windows [2]. `bonescope/model_definition.py` mô tả `MetadataProcessor`, `MetadataMLP`, khối Cross-Attention và đầu phân loại phẳng 10 lớp; `bonescope/inference.py` nạp checkpoint, cấu hình và phép biến đổi tương ứng. Model không được gọi là “AI tự học từ cuộc trò chuyện”: trọng số ảnh không đổi khi người dùng chat.

**Cách dùng:** ảnh và vector metadata đi vào hai nhánh, đặc trưng được hợp nhất ở các tầng trước khi xếp 10 nhãn. 22 trường đầu vào là schema thô; sau tiền xử lý, số chiều vector có thể khác 22. Điểm softmax là điểm tương đối của checkpoint, không phải xác suất mắc bệnh đã hiệu chuẩn. `bonescope/check_model.py` và `bonescope/verify_api.py` kiểm tra asset/hash và parity với các ca mẫu. Báo cáo này chỉ xác nhận **tích hợp và đánh giá checkpoint đang có**, không suy diễn rằng quá trình huấn luyện, tách tập hay tối ưu hyperparameter đã được tái dựng đầy đủ trong repo.

### 3.4 Thiết kế thực nghiệm và đọc chỉ số

**Kiến thức vận dụng:** lấy mẫu phân tầng, Top-1/Top-3, precision/recall/F1 theo lớp, Macro-F1, ablation, calibration và kiểm tra subgroup. `tools/evaluate_xray_checkpoint.py` chạy cùng 250 ảnh theo hai điều kiện, có 22 metadata và đặt vector sau biến đổi bằng 0. `tools/analyze_xray_calibration_and_subgroups.py` tính ECE, MCE, Brier, NLL và phân rã theo nhóm. Mẫu lấy 25 ảnh cho mỗi nhãn trong 10 nhãn, seed cố định.

**Kết quả và cách hiểu:** Top-1 là 0,776 với metadata và 0,480 khi xóa vector metadata; Macro-F1 lần lượt xấp xỉ 0,776 và 0,439. Chênh lệch quan sát được trên **mẫu nội nguồn** cho thấy đầu ra nhạy với metadata, nên API không tự thay metadata thiếu bằng số 0. Nó không chứng minh hiệu quả trên bệnh nhân mới. Checkpoint liên quan đến BTXRD, nhưng không có manifest split gốc/patient ID đủ để khẳng định 250 ảnh này là holdout độc lập. Kỹ năng quan trọng là **nêu đúng mẫu số, điều kiện thử và giới hạn suy luận**.

### 3.5 API và kiểm tra đầu vào

**Kiến thức vận dụng:** HTTP, REST, `multipart/form-data`, JSON, mã trạng thái lỗi, validation, vòng đời FastAPI, giới hạn tài nguyên và kiểm tra đầu ra model. `bonescope/xray_api.py` dùng FastAPI/Uvicorn, nhận `UploadFile`, kiểm tra đuôi và nội dung ảnh, giới hạn 30 MiB/25 triệu pixel, chỉ ảnh một frame và đủ metadata; `bonescope/validation.py` kiểm tra schema; `rag/demo_api.py` phục vụ Research Studio, tra cứu và chat. Kỹ thuật này bám đúng cơ chế gửi file form-data của FastAPI [5].

**Cách dùng:** request sai nhận lỗi rõ ràng; ảnh hợp lệ được xử lý trong thư mục tạm rồi xóa; điểm đầu ra phải đủ 10 nhãn, hữu hạn và tổng gần 1. Mô hình được nạp khi cần dưới khóa để tránh chạy nhiều tác vụ ảnh cùng lúc. `TrustedHostMiddleware` và địa chỉ loopback giới hạn demo cục bộ. Đây là thiết kế cho môi trường học tập đơn máy, **chưa phải** một API public có xác thực tài khoản và bảo mật triển khai.

### 3.6 Thu thập văn bản và xây corpus có thể truy vết

**Kiến thức vận dụng:** chọn nguồn, điều kiện sử dụng, trích xuất HTML/JATS/BioC, làm sạch văn bản, chia đoạn, metadata và khóa phiên bản. `rag/build_corpus.py` đọc `rag/data/sources.json` và cache nguồn, tạo `rag/data/corpus.jsonl` với `source_id`, tiêu đề, section, URL, license và hash văn bản. `rag/data/source_lock.json` khóa quan hệ nguồn–nội dung. Mục đích của hash là phát hiện artifact thay đổi; hash **không** chứng minh câu trả lời được nguồn hỗ trợ.

**Cách dùng:** nguồn không có quyền ingest phù hợp không được tự thêm. Một đoạn có thể được hiển thị kèm thông tin xuất xứ để người đọc kiểm tra trực tiếp. `rag/audit.py` đối chiếu source cache, chunk, index, model asset và các evaluation set. Hiện có 22 nguồn, 794 đoạn; audit ngày 13/11 không báo cache thiếu. Kỹ năng thể hiện ở việc duy trì khả năng truy vết từ một thẻ nguồn trong UI về văn bản và hồ sơ nguồn tương ứng.

### 3.7 Tìm kiếm ngữ nghĩa và hợp nhất thứ hạng

**Kiến thức vận dụng:** embedding, cosine similarity sau chuẩn hóa L2, truy xuất từ khóa BM25, mở rộng câu hỏi song ngữ, reciprocal rank fusion và ranking. `intfloat/multilingual-e5-small` được dùng để mã hóa đoạn và truy vấn [3]. `rag/build_index.py` tạo ma trận NumPy 794 × 384 cùng manifest hash; `rag/retrieval.py` kiểm tra version/hash trước khi truy vấn; `rag/lexical.py` triển khai BM25 và hợp nhất thứ hạng.

**Cách dùng:** query có prefix `query:`, passage có prefix `passage:`; các thứ hạng dense và từ khóa được hợp nhất, rồi policy có thể giữ nguồn ưu tiên khi có tín hiệu chủ đề rõ. Kết quả là **ứng viên đọc**, không là bằng chứng tự động rằng một claim đã được xác nhận. Trên 28 truy vấn đã xem, điểm của câu dương/âm chồng lấn; vì vậy chưa đặt ngưỡng similarity toàn cục mặc định. Công cụ hiệu chỉnh còn ở trạng thái `AWAITING_LABELS` để tránh chọn ngưỡng bằng chính dữ liệu đã dùng trong phát triển.

### 3.8 Hội thoại RAG và model tạo sinh

**Kiến thức vận dụng:** RAG, prompt theo vai trò, lịch sử đa lượt, tool calling, phân biệt câu hỏi tổng quát với câu hỏi cần nguồn, timeout/rate limit và khống chế dữ liệu gửi provider. Nghiên cứu RAG nền tảng mô tả việc kết hợp mô hình tham số với bộ nhớ truy xuất [4]; triển khai BoneScope là một pipeline ứng dụng riêng, không mặc nhiên thừa hưởng kết quả thực nghiệm của bài báo. `rag/conversation.py` yêu cầu gọi công cụ tìm tài liệu khi câu hỏi liên quan đến xương; `rag/generation.py` gửi các đoạn cần thiết vào payload và gắn nhãn nguồn `[S1]`, `[S2]` theo lượt hiện tại.

**Cách dùng:** lời chào hoặc câu hỏi đa chủ đề có thể trả lời như hội thoại; câu hỏi về xương được tra cứu kho cục bộ. Lịch sử dùng để hiểu ý hỏi tiếp, **không dùng làm bằng chứng**. Đoạn nguồn là dữ liệu, không được thay thế hướng dẫn hệ thống. `OPENROUTER_MODEL=openrouter/free` là tuyến trước; Qwen cố định có thể được gọi khi free timeout, giới hạn hoặc phản hồi rỗng/chưa hoàn tất; Groq tùy chọn và tắt trong `.env.example`. Việc chọn provider không bảo đảm câu trả lời đúng, và fallback trả phí có thể phát sinh chi phí. OpenAI SDK trong dependency là client tương thích API; nó không có nghĩa ứng dụng đang dùng ChatGPT Plus hoặc OpenAI API làm tuyến chính.

### 3.9 Chat ảnh và giới hạn của hiểu ảnh

**Kiến thức vận dụng:** multimodal input, định dạng/MIME, giới hạn dung lượng, ngữ cảnh ảnh theo cuộc trò chuyện, tách quan sát khỏi diễn giải và xử lý bất định. `rag/demo_api.py`, `rag/generation.py` và `rag/demo_web/app.js` nhận ảnh trong ô chat, gửi đến vision provider và giữ ảnh tạm theo phiên tab. Sau phân tích, ứng dụng có thể tìm tối đa 4 đoạn tài liệu liên quan để người dùng đọc thêm.

**Cách dùng:** ảnh xuất hiện trực tiếp trong tin nhắn sau khi gửi; phần đính kèm biến mất khỏi ô soạn. Câu hỏi tiếp theo trong cùng tab có thể gửi lại ảnh đang mở; tải lại trang hoặc mở ở tab khác thì cần đính kèm lại. `.env.example` đặt `google/gemma-4-31b-it:free` cho tuyến thị giác miễn phí; việc fallback sang Qwen có thể phát sinh chi phí. Ảnh ngoài BTXRD không được gán metadata từ suy đoán của vision model. Tài liệu đọc thêm **không** xác nhận nhận xét của AI về ảnh. Đây là khả năng mô tả/phục vụ học tập, chưa có thẩm định độ chính xác X-quang độc lập.

### 3.10 SQLite và thiết kế dữ liệu tối thiểu

**Kiến thức vận dụng:** quan hệ một-nhiều, khóa ngoại, giao dịch, chỉ mục, CRUD, vòng đời dữ liệu và nguyên tắc chỉ lưu trường cần dùng. `rag/chat_history.py` có bảng `conversations` và `messages`; hai message của một lượt được lưu trong cùng giao dịch cùng nguồn đã lọc theo danh sách trường. Có thao tác mở, đổi tên, xóa; `ON DELETE CASCADE` dọn message khi xóa hội thoại. `bonescope/database.py` dùng bảng ca, bình luận và nhãn hiệu chỉnh riêng; nhãn sửa không ghi đè dự đoán gốc.

**Cách dùng:** byte ảnh chat không được ghi vào `data/chat_history.db`; câu hỏi, câu trả lời và nguồn được giữ trên máy chủ local. Hạn mức 500 hội thoại và 2.000 message mỗi hội thoại gây lỗi có giải thích thay vì âm thầm xóa dữ liệu. Trong UI, kết quả đến muộn không được gắn sang hội thoại mới hoặc tái tạo hội thoại đã bị xóa. SQLite phù hợp nguyên mẫu cục bộ; hiện không có tài khoản, mã hóa ở tầng ứng dụng hoặc cơ chế phân quyền đa người dùng.

### 3.11 Giao diện và trải nghiệm người dùng

**Kiến thức vận dụng:** bố cục responsive, hệ thống màu/kiểu chữ/spacing, trạng thái loading–error–retry, biểu mẫu nhiều bước, xem trước ảnh, điều khiển bằng bàn phím và accessibility. `rag/demo_web/` dùng HTML/CSS/JavaScript thuần; `rag/demo_web/DESIGN.md` ghi design tokens, trạng thái sáng/tối và thành phần. `package.json` cài `@google/design.md` và cung cấp lệnh `design:lint`. Không có bằng chứng rằng giao diện runtime là ứng dụng React hoặc mã Stitch được deploy nguyên trạng; `DESIGN.md` là đặc tả phục vụ triển khai và kiểm tra thiết kế.

**Cách dùng:** sidebar lịch sử, ô soạn tự tăng chiều cao, ảnh xem trước và mở lớn, hộp thoại ca ba bước, nguồn có thể mở, phím Enter/Shift+Enter, nhãn ARIA, chế độ tối và `prefers-reduced-motion`. Thiết kế đặt luồng “Tra cứu cục bộ” cạnh chat provider để người dùng hiểu lựa chọn nguồn và dữ liệu gửi ra ngoài. Hướng dẫn UI ghi kích thước 1366×768, 390×844 và 320×568 từng được kiểm tra; smoke ngày 13/11 dùng ảnh tổng hợp và AI giả lập. Chuyển động làm giao diện dễ theo dõi, không được lấy làm bằng chứng chất lượng mô hình.

### 3.12 Kiểm thử, tái lập và quản lý phiên bản

**Kiến thức vận dụng:** unit/integration test, mock provider, regression, kiểm tra trình duyệt, parity API, hash artifact, audit/replay và Git LFS. Các thư mục `tests/`, `api_tests/`, `rag/tests/`, `ui_tests/` kiểm các ranh giới tương ứng; `tools/chatbot_doctor.py` kiểm cấu hình cục bộ; `rag/audit.py` và `rag/replay_reports.py` so artifact/report; `tools/verify_stage11_registers.py` kiểm cấu trúc các sổ G1–G7. `.gitattributes` lưu checkpoint `.pt` bằng Git LFS, `.gitignore` loại dữ liệu runtime và secret.

**Cách dùng:** record ngày 13/11 cố định commit đã kiểm, số bài đạt/skip và phạm vi browser smoke; record 12/11 ghi API parity 3/3. Test dùng dữ liệu tổng hợp hoặc model giả lập khi kiểm UI/nhà cung cấp, nên không chấm được chất lượng phản hồi thực. Đây là kỹ năng tách **“chạy đúng phần mềm”** khỏi **“đúng về mặt học thuật và chuyên môn”**.

### 3.13 Thuật ngữ u xương và ánh xạ nhãn

**Kiến thức vận dụng:** phân biệt nhãn của dataset, tên khái niệm trong tài liệu và nhận định về một ảnh cụ thể. `rag/case_context.py` ghi rõ 10 nhãn checkpoint bằng bảng `LABEL_GUIDE`: bốn nhãn có tên trùng thuật ngữ trong corpus được tra cứu khái niệm chung (`direct`); ba nhãn có khái niệm gần nhưng chưa xác minh tương đương được đánh dấu `unresolved`; hai nhóm `other bt`/`other mt` là nhãn gộp (`aggregate`); `no-tumor` không phải tên bệnh (`no_tumor`). Đây là bảng làm việc do tác nhân lập, **chưa phải ontology đã được chuyên gia duyệt**.

**Cách dùng:** hệ thống không tự đổi `osteofibroma` thành `osteofibrous dysplasia`, hoặc `synovial osteochondroma` thành `synovial chondromatosis` chỉ vì tên nghe gần nhau. Ngay cả với nhóm `direct`, tài liệu trả về chỉ giải thích khái niệm, không xác minh nhãn của ca X-quang. Ngữ cảnh gửi cho model tạo sinh từ ca classifier được giảm xuống Top-3, điểm và trạng thái ánh xạ; ảnh và 22 metadata ở lại máy trong luồng giải thích ca. Kỹ năng cốt lõi ở đây là **kiểm soát phép suy từ nhãn dữ liệu sang tri thức chuyên môn**.

## 4 Bảng ánh xạ công nghệ và hiện vật

| Thành phần hoặc công cụ | Kiến thức chính | Nơi dùng và hiện vật kiểm tra | Vai trò đã thực hiện |
|---|---|---|---|
| Python, NumPy, pandas, scikit-learn, joblib | Tiền xử lý, tính toán, dữ liệu bảng | `bonescope/model_definition.py`, `bonescope/inference.py`, `tools/evaluate_xray_checkpoint.py` | Nạp preprocessing và checkpoint; biến đổi metadata; đo chỉ số nội nguồn. |
| PyTorch, timm, Pillow, OpenCV/Albumentations | Tensor, Swin, ảnh số, inference | `bonescope/model_definition.py`, `bonescope/xray_api.py`, `model/` | Đọc ảnh hợp lệ, chạy mô hình ảnh, kiểm tra điểm đầu ra. |
| FastAPI, Pydantic, Uvicorn, HTTPX | API, schema, vòng đời server | `bonescope/xray_api.py`, `rag/demo_api.py`, `api_tests/` | Cung cấp endpoint local, validation và kiểm thử request. |
| SQLite | Lưu trữ quan hệ, giao dịch, CRUD | `bonescope/database.py`, `rag/chat_history.py` | Quản lý ca và lịch sử chat theo hai schema riêng. |
| sentence-transformers, multilingual E5, NumPy | Embedding, cosine, index | `rag/build_index.py`, `rag/retrieval.py`, `rag/index/manifest.json` | Tìm đoạn văn bản có ngữ nghĩa tương tự, kiểm tra phiên bản index. |
| BM25 và RRF tự triển khai | Lexical search, fusion | `rag/lexical.py`, `rag/data/retrieval_config.json` | Bổ sung từ khóa và hợp nhất thứ hạng cho câu hỏi Việt/Anh. |
| Bảng ánh xạ nhãn và ngữ cảnh ca | Thuật ngữ, bất định và tối thiểu hóa dữ liệu | `rag/case_context.py`, `rag/data/retrieval_config.json` | Chặn ánh xạ tương đương chưa kiểm chứng; chỉ đưa Top-3 và trạng thái cần thiết vào lời giải thích. |
| OpenRouter, Groq tùy chọn, OpenAI SDK | Kết nối provider, timeout, fallback | `rag/generation.py`, `.env.example` | Tạo bản nháp hội thoại/ảnh; free ưu tiên, fallback theo cấu hình. |
| HTML, CSS, JavaScript, SVG, `DESIGN.md` | UI responsive, token, accessibility | `rag/demo_web/`, `xray_web/`, `package.json` | Hiển thị chat, ca ảnh, nguồn, lịch sử và trạng thái tương tác. |
| pytest, Chrome headless, hash/replay | Kiểm thử và tái lập | `tests/`, `ui_tests/`, `docs/reference/` | Xác minh luồng phần mềm và giữ record có thể đối chiếu. |
| Git, Git LFS, VS Code, PowerShell | Quản lý mã, asset lớn, chạy/debug | `.gitattributes`, `.vscode/launch.json`, `scripts/` | Lưu lịch sử dự án, chạy demo và bàn giao trên Windows. |
| Markdown, python-docx | Viết và xuất báo cáo | `docs/reports/`, `tools/export_report_docx.py` | Lưu tài liệu có phiên bản và bản Word để nộp/xem xét. |

**Kỹ năng không nên tự nhận là đã chứng minh:** huấn luyện mới Swin/E5 từ đầu; kiểm định lâm sàng; phát hành bộ ảnh có đủ quyền; triển khai VPS nhiều người dùng; chấm độ đúng ảnh và citation bằng reviewer độc lập. Các mục này có thể là hướng phát triển hoặc yêu cầu nghiệm thu khác, nhưng không phải kết quả đã hoàn thành trong hồ sơ hiện hành.

## 5 Quy trình làm việc thể hiện kiến thức đã áp dụng

Một quy trình tái lập tiêu biểu đi từ **nguồn dữ liệu → kiểm tra xuất xứ → chuẩn hóa/đánh chỉ mục → API và UI → kiểm thử → báo cáo**:

1. Xác định phạm vi và quyền nguồn. Với ảnh, lập manifest/hash và cấm tự ghép metadata khi không khớp; với văn bản, giữ URL, giấy phép và bản cache có khóa.
2. Nạp artifact mô hình đã có cùng preprocessing phù hợp. Chạy `bonescope.check_model` và parity API; không đổi trọng số hoặc schema chỉ để request “chạy được”.
3. Tạo corpus, index E5, BM25 và policy. Mọi lần đổi corpus/model/config phải làm lại index hoặc để manifest phát hiện dữ liệu cũ.
4. Cho người dùng chọn luồng: classifier cần metadata hợp lệ; tra cứu cục bộ không cần API key; chat tạo sinh có thể gửi nội dung và ảnh đến provider theo cấu hình.
5. Lưu đúng phạm vi: lịch sử chat giữ chữ và nguồn; ảnh chat chỉ sống tạm trong tab; ca phân loại có schema riêng. Đối chiếu thao tác xóa và kết quả đến muộn.
6. Chạy regression, browser smoke, audit/replay và lưu record gắn với commit; đánh dấu phép nào dùng mock, phép nào chạy thật. Báo cáo chỉ số theo đúng nguồn dữ liệu và giới hạn.

Luồng này cho thấy kỹ năng kỹ thuật gắn với **ra quyết định có căn cứ**: khi dữ liệu thiếu hoặc không rõ nguồn, hệ thống từ chối tự điền; khi tập đánh giá đã dùng để phát triển, chỉ báo cáo như dev/regression; khi chưa có nhãn độc lập, giữ ngưỡng ở trạng thái chờ.

## 6 Bảng tiến độ hoàn thành từ khi khởi tạo đến ngày 14 tháng 11 năm 2026

**Cơ sở lập bảng:** `git log` của nhánh hiện tại, lộ trình dự án, bản bàn giao, các record kiểm chứng và mã nguồn còn tồn tại. Ngày là ngày commit hoặc ngày record; một số công việc đã thực hiện liên tục giữa hai mốc, nên bảng dùng **khoảng thời gian** thay vì bịa ngày hoàn thành riêng cho từng dòng. “Hoàn thành” luôn kèm phạm vi cụ thể.

| Thời điểm | Đầu ra đã hoàn thành | Bằng chứng tiêu biểu | Trạng thái tại 14/11 |
|---|---|---|---|
| 27/10 | Khởi tạo bộ phân loại X-quang local, môi trường, kiểm tra model, API/UI cơ bản và lộ trình. | Commit `4660d6e`, `27a62b4`; `bonescope/`, `model/`, `scripts/`. | Hoàn thành nền phần mềm. |
| 27/10 | Thêm corpus RAG, retrieval, evaluation và policy/evidence cơ bản. | Commit `59f4dfd`, `99e9817`, `d1ef896`; `rag/`. | Hoàn thành nền truy xuất, tiếp tục mở rộng sau đó. |
| 27–29/10 | Mở rộng nguồn, khóa xuất xứ, index, audit và bộ báo cáo replay Giai đoạn 11; lưu handoff. | Commit `b6d67fb`, `5166988`, `84d5b75`; sổ nguồn và record GĐ11. | Pipeline có artifact; acceptance nghiên cứu chưa đóng. |
| 02/11 | Dựng chatbot hội thoại và giao diện demo đầu tiên. | Commit `76e950f`; `rag/demo_api.py`, `rag/demo_web/`. | Luồng trò chuyện chạy local. |
| 03/11 | Tích hợp classifier với chatbot, ngữ cảnh ca, nguồn RAG và thực nghiệm 250 ảnh/ablation. | Commit `82ccb06`; record `stage11_xray_in_source_evaluation_20261103.json`. | Nguyên mẫu tích hợp; kết quả ảnh nội nguồn. |
| 03–09/11 | Lịch sử SQLite, chat ảnh nhiều lượt, metadata BTXRD theo hash, catalogue và calibration; UI responsive. | Record SQLite 03/11, catalogue 05/11, subgroup 06/11, browser/provider smoke 09/11. | Chức năng đã triển khai và kiểm tra trong phạm vi record. |
| 09–10/11 | Rà lỗi đầu vào retrieval và chatbot; xác minh lại test/audit/replay; dọn cấu trúc package và launcher. | Commit `dd6c8aa` đến `a262b61`; record 10/11. | Refactor và validation đã kiểm tra. |
| 10–12/11 | Sửa đường dẫn sau refactor, parity API, launcher và precheck nghiệm thu demo. | Record `project_verification_20261112.json`; parity 3/3; checklist demo. | Bàn giao phần mềm local với giới hạn rõ. |
| 13/11 | Bổ sung tra cứu cục bộ, thống nhất logo, hiển thị ảnh ngay trong chat và hoàn thiện báo cáo đồ án. | Commit `c9db10d`, `ac3ac77`, `82cd17d`; record 13/11. | Chức năng và báo cáo hiện hành đã kiểm chứng. |
| 14/11 | Lập báo cáo riêng về kiến thức, kỹ năng và tiến độ bằng cách đối chiếu mã/record/commit. | Tài liệu này và bản Word cùng tên. | Hoàn thành báo cáo bổ trợ sau khi xuất và kiểm tra bố cục. |

**Chú giải:** các commit 27/10 chứa nhiều thành phần có thể đã tồn tại trước khi được đưa vào Git. Ngày commit chứng minh mốc **ghi nhận trong repository**, không nhất thiết là ngày đầu tiên tác giả học hoặc viết từng thành phần. Các dòng từ 03–09/11 dùng record có ngày thay cho commit riêng khi một checkpoint gom nhiều thay đổi.

### Đối chiếu với lộ trình kỹ thuật

| Nhóm lộ trình | Phần đã có đầu ra | Điều còn thiếu để tuyên bố hoàn tất đầy đủ |
|---|---|---|
| GĐ 0–9 Môi trường, model, API, UI, SQLite, kiểm thử, Git | Mã chạy local, launcher, kiểm tra model/API, giao diện, schema và regression. | Không suy diễn thành sẵn sàng vận hành public hoặc an toàn lâm sàng. |
| GĐ 10 Corpus tài liệu | 22 nguồn, 794 đoạn, source lock, cache/hash và audit. | Cần reviewer cho mức độ hỗ trợ từng claim nếu muốn nâng mức chứng cứ. |
| GĐ 11 Index và retrieval | E5 794 × 384, BM25/hybrid, audit và replay 16/16; 6/7 bước checklist hẹp có artifact. | Bước 7 còn `AWAITING_LABELS`; chưa có ngưỡng kiểm định trên nhãn độc lập. |
| GĐ 12 Chatbot | Hội thoại đa chủ đề, RAG, nguồn, ảnh nhiều lượt, SQLite chữ và UI. | Cần chấm độc lập độ đúng câu trả lời/ảnh trước mọi tuyên bố chất lượng. |
| GĐ 13 Đánh giá và đóng gói | Có báo cáo, checklist demo, test, record kiểm chứng và hướng dẫn chạy. | Chưa có cohort ngoài đủ quyền, reviewer/sign-off và 7 gate đóng; không gọi toàn giai đoạn là hoàn tất. |

## 7 Kết quả kiểm chứng hiện hành và phạm vi sử dụng

| Phép kiểm | Kết quả gần nhất được ghi | Phạm vi diễn giải đúng |
|---|---|---|
| Regression phần mềm 13/11 | 216 passed, 0 failed, 1 skipped; 227 subtests passed | Kiểm tra code/API/tính năng; skip Chrome trong sandbox không được đổi thành pass. |
| Browser smoke chạy riêng 13/11 | 1/1 pass | Chrome với SQLite tạm, ảnh tổng hợp, AI và retrieval giả lập. |
| API parity 12/11 | 3/3 ca, score delta 0 | Kiểm tra cùng checkpoint/hợp đồng đầu vào, không đo accuracy bên ngoài. |
| RAG audit và replay 13/11 | PASS 22 nguồn/794 đoạn; 16/16 report khớp | Tính toàn vẹn và tái lập artifact, không đo entailment. |
| Chatbot doctor 13/11 | 13/13 pass | Kiểm tra cấu hình local, không gọi provider thật. |
| Giai đoạn 11 và G1–G7 | 6/7 bước kỹ thuật có artifact; 7/7 gate `OPEN`; `answer_ready=false` | Bước 7 chờ nhãn; gate là điều kiện đánh giá riêng, không phải tỷ lệ hoàn thành demo. |

**Có thể báo cáo với giảng viên:** cách hệ thống chạy, kiến trúc, thực nghiệm nội nguồn, khả năng tra cứu có nguồn, giao diện và lịch sử chat, cùng các giới hạn của từng phép kiểm. Trước buổi trình bày, chạy [checklist nghiệm thu demo](PRODUCT_ACCEPTANCE_CHECKLIST_VI.md) trên đúng máy sẽ dùng và dùng dữ liệu được phép. Không đưa ảnh bệnh nhân định danh lên provider, không mở server local ra Internet và không gọi softmax là xác suất bệnh.

**Chưa được tuyên bố:** accuracy trên cohort ảnh độc lập; model đọc ảnh đúng theo chuyên gia; citation entailment đã được thẩm định; quyền phát hành từng ảnh; phê duyệt bảo mật/quy định cho hệ thống public. G1–G7 giữ `OPEN` cho đến khi có chủ thể và bằng chứng tương ứng. Báo cáo bổ trợ này không thay thế chữ ký của giảng viên, reviewer hoặc quyết định nghiệm thu.

## 8 Hồ sơ đối chiếu và tài liệu tham khảo

### Hồ sơ trong dự án

- [Báo cáo tổng kết đồ án ngày 13/11](BAO_CAO_TONG_KET_DO_AN_BONESCOPE_20261113_VI.md) trình bày phương pháp và số liệu chi tiết.
- [Bản bàn giao hiện hành](../../START_HERE_NEXT_CODEX_VI.md) ghi điểm dừng, lệnh chạy, giới hạn và kiểm chứng.
- [Record kiểm chứng 13/11](../reference/project_report_verification_20261113.json), [record API 12/11](../reference/project_verification_20261112.json) và [checklist demo](PRODUCT_ACCEPTANCE_CHECKLIST_VI.md).
- [Đối chiếu 7 bước Giai đoạn 11](../reference/STAGE11_EDUCATIONAL_COMPLETION_MATRIX_20261029.md), [sổ 7 gate](../reference/stage11_acceptance_gate_status_20261029.csv), [lộ trình](../LO_TRINH_THUC_HIEN_DU_AN_AI.md).
- [Đánh giá ảnh nội nguồn](../reference/stage11_xray_in_source_evaluation_20261103.json), [catalogue BTXRD](../reference/stage12_btxrd_catalogue_and_mapping_analysis_20261105.json), [kiểm tra subgroup](../reference/stage12_xray_subgroup_and_calibration_20261106.json).
- [Hướng dẫn UI](../guides/README_CHATBOT_UI_VI.md), [design tokens](../../rag/demo_web/DESIGN.md) và [hướng dẫn vận hành/nghiên cứu](../guides/RESEARCH_WORKFLOW_VI.md).

### Tài liệu nền bên ngoài

1. Yao S và cộng sự. “A Radiograph Dataset for the Classification, Localization, and Segmentation of Primary Bone Tumors.” *Scientific Data* 12, 88 (2025). [Bản toàn văn PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11739492/). Bài báo không tự xác nhận quyền tái sử dụng ở cấp từng ảnh nguồn.
2. Liu Z và cộng sự. “Swin Transformer: Hierarchical Vision Transformer using Shifted Windows.” ICCV 2021. [Bài báo arXiv](https://arxiv.org/abs/2103.14030).
3. Wang L và cộng sự. “Multilingual E5 Text Embeddings: A Technical Report.” 2024. [Bài báo arXiv](https://arxiv.org/abs/2402.05672).
4. Lewis P và cộng sự. “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.” NeurIPS 2020. [Bài báo hội nghị](https://proceedings.neurips.cc/paper/2020/hash/6b493230-Abstract.html).
5. FastAPI. [Request Files](https://fastapi.tiangolo.com/tutorial/request-files/) và Python. [Thư viện sqlite3](https://docs.python.org/3/library/sqlite3.html). Dùng để đối chiếu cơ chế API và cơ sở dữ liệu; hành vi thực tế của BoneScope được xác định bởi mã và record kiểm thử trong dự án.

## 9 Gợi ý giải thích báo cáo khi bảo vệ đồ án

Khi bảo vệ, demo một ảnh **được phép sử dụng**, một câu tra cứu cục bộ và thao tác mở lại lịch sử. Nêu rõ Swin cần 22 metadata hợp lệ, chat ảnh không tạo metadata thật, còn record/bảng tiến độ chỉ xác nhận các luồng phần mềm đã kiểm tra.

| Câu hỏi có thể gặp | Cách trả lời ngắn dựa trên hồ sơ |
|---|---|
| AI có tự học sau mỗi cuộc trò chuyện không? | Không. SQLite ghi lịch sử chữ; checkpoint Swin và model E5 không được huấn luyện lại từ chat. |
| Vì sao ảnh lạ không chạy classifier ngay? | Checkpoint cần metadata hợp lệ. Model thị giác mô tả pixel không phải nguồn xác thực tuổi, giới hoặc nhãn ca. |
| Vì sao Top-1 bằng 0,776 chưa phải accuracy lâm sàng? | Mẫu 250 ảnh là nội nguồn BTXRD; chưa có split gốc và cohort ngoài đủ quyền để kiểm định độc lập. |
| Nguồn RAG có chứng minh AI nói đúng không? | Chưa. Audit xác nhận xuất xứ và replay, còn hỗ trợ trực tiếp của từng claim cần người chấm độc lập. |
| Có thể gọi dự án hoàn tất 100% không? | Có thể nói nguyên mẫu local và hồ sơ demo đã có; GĐ11 còn 1 bước chờ nhãn, G1–G7 đều mở. Không có mẫu số hợp lệ cho 100% toàn dự án. |

**Kết luận:** BoneScope đã có nguyên mẫu học tập chạy local và hồ sơ kỹ thuật cho các luồng chính. Đồ án vận dụng suy luận ảnh có metadata, tra cứu tài liệu có nguồn, hội thoại đa lượt, lưu trữ có kiểm soát và đánh giá tái lập. Độ đúng chuyên môn, quyền ảnh, chấp thuận triển khai và 7 acceptance gate vẫn chưa được xác nhận.
