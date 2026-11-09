# Quy trình vận hành và hoàn thiện thực nghiệm BoneScope

Tài liệu này hướng dẫn chạy chatbot local, kiểm tra môi trường, xem trước nguồn mới và chuẩn bị đánh giá retrieval. Chatbot/mô hình chỉ phục vụ đồ án học tập thực nghiệm; các bước dưới đây không xác nhận độ đúng y khoa hay cho phép dùng dữ liệu bệnh nhân.

## 1. Chạy chatbot trên Windows

Ở máy hiện tại, dependency, index, embedding, mô hình ảnh, cấu hình OpenRouter và SQLite đã qua kiểm tra local trong [readiness record](../reference/chatbot_local_readiness_20261109.json). Kiểm tra này không gọi nhà cung cấp AI.

- Khởi động: nhấp đúp `08_start_chatbot.bat`, hoặc chọn cấu hình **BoneScope: Chatbot tra cứu tài liệu** trong VS Code rồi nhấn F5. Mở `http://127.0.0.1:8765/` nếu trình duyệt không tự mở.
- Kiểm tra trước khi chạy: nhấp đúp `09_check_chatbot.bat`, chạy tác vụ VS Code **Check BoneScope chatbot environment**, hoặc chạy `.\.venv\Scripts\python.exe -m tools.chatbot_doctor`.
- Cài lại dependency chatbot trên một checkout mới: chạy `01_setup.bat`, tạo `.env` từ `.env.example` và điền key ở máy local, sau đó chạy `10_setup_chatbot.bat`. Script lưu log cài đặt ở `logs/chatbot_setup.log`; không đưa `.env` hoặc log có dữ liệu nhạy cảm lên Git.
- Nếu cổng 8765 đang được dùng, launcher kiểm tra health endpoint local. Nó không tự dừng tiến trình khác. Dừng server cũ bằng Shift+F5 trong VS Code hoặc Ctrl+C ở cửa sổ server; có thể chọn cổng khác bằng `python -m tools.run_chatbot --port 8766`.

Doctor kiểm tra dependency cốt lõi, cấu hình model allowlist, trạng thái key mà không in giá trị, hash index/corpus, model assets và integrity SQLite. `PASS` không chứng minh API key còn quota, model trả lời đúng, hoặc citation hỗ trợ claim. `WARN` có thể chỉ ra một tính năng tùy chọn như index hoặc classifier chưa sẵn sàng.

## 2. Regression phần mềm

Sau khi cài dependency phát triển (`.\.venv\Scripts\python.exe -m pip install -r requirements_dev.txt`), chạy từ thư mục gốc:

```powershell
.\.venv\Scripts\python.exe -m pytest api_tests rag\tests tests ui_tests -q
```

Test chatbot/provider dùng mock; browser test cần Google Chrome cài trên máy. Các test này kiểm tra hành vi phần mềm, không đo chất lượng đọc X-quang, độ đúng của nguồn hoặc tính khái quát. Xem [bản xác minh tổng hợp gần nhất](../reference/final_verification_20261109.json); cần chạy lại suite sau thay đổi mã để có số liệu mới.

## 3. Xem trước nguồn văn bản mới

`tools.preview_rag_source` chỉ phân tích payload local đã tải về; nó không tự duyệt web và không cập nhật corpus đang chạy. Hỗ trợ HTML, NCBI BioC JSON, Europe PMC JATS XML và NCI glossary JSON qua parser corpus hiện có; đây không phải trình nhập PDF hay ảnh.

Tạo một JSON khai báo nguồn dựa trên schema của `rag/data/sources.json`. Các trường bắt buộc: `id`, `title`, `url`, `license`, `license_url`, `scope`; nguồn ngoài NCI cần thêm `authors`, `publisher`. JATS/BioC phải có định danh PMCID/DOI khớp payload. Chỉ dùng nội dung có quyền sử dụng đã được người phụ trách xác minh.

```powershell
.\.venv\Scripts\python.exe -m tools.preview_rag_source `
  --source .temp\candidate_source.json `
  --payload .temp\downloaded_article.xml `
  --output .temp\candidate_preview
```

Đầu ra gồm `source.json`, `chunks.jsonl` và `preview.json` với trạng thái `REVIEW_REQUIRED`. Đọc lại danh tính bài, license, phạm vi, nội dung chunk và hash trước khi chủ dự án chấp nhận. Thời gian mtime của file chỉ là thời gian hệ thống ghi nhận, không chứng minh ngày tải thực. Thư mục xem trước phải nằm ngoài `rag/data`, `rag/source_cache`, `rag/index` và `rag/models`.

Chỉ sau khi con người duyệt quyền, danh tính và nội dung mới cập nhật registry/cache, rồi chạy lại `rag/build_corpus.py --offline`, `rag/build_index.py`, audit và replay bằng tên report/bundle mới. Các lệnh build corpus/index làm thay đổi artifact đang hoạt động; giữ snapshot/hash trước đó, xem diff, chạy regression và không ghi đè report lịch sử. Không đưa dữ liệu xem trước vào kho chỉ vì parser chạy thành công.

## 4. Hiệu chỉnh ngưỡng retrieval bằng nhãn đã khóa

Ngưỡng chưa được hiệu chỉnh; runtime không cài threshold mới. Báo cáo hiện hành là `AWAITING_LABELS`, không có candidate threshold. Tool chỉ chuẩn bị quy trình và không thể tạo nhãn, tiêu chí chấp nhận hay xác minh sự độc lập của reviewer.

Để tạo bộ dữ liệu trống mới, dùng một đường dẫn chưa tồn tại:

```powershell
.\.venv\Scripts\python.exe -m tools.calibrate_retrieval_threshold `
  --init --output .temp\retrieval_review_dataset.json
```

Reviewer/owner có thẩm quyền phải khóa trước câu hỏi, `cluster_id`, split (`calibration` hoặc `holdout`), answerability và `expected_status`; không dùng câu hỏi bệnh nhân. Cụm câu hỏi tương tự phải nằm cùng một split. Ghi rõ protocol/cỡ mẫu/đơn vị lấy mẫu ngoài JSON nếu schema hiện tại chưa biểu diễn được yêu cầu đó. Chọn cả hai tiêu chí (`min_fully_answerable_retention`, `max_unsupported_candidate_rate`) sau khi thống nhất rủi ro và mục tiêu; không lấy số mặc định từ bộ dev đã xem. `purpose: reviewer_supplied` chỉ mô tả nguồn dữ liệu do người dùng cung cấp, không chứng nhận reviewer độc lập.

Chạy phân tích vào file report mới:

```powershell
.\.venv\Scripts\python.exe -m tools.calibrate_retrieval_threshold `
  --dataset .temp\retrieval_review_dataset.json `
  --output .temp\retrieval_threshold_review.json
```

Tool chọn candidate chỉ từ calibration; holdout chỉ được chấm sau khi đã chọn candidate và không tạo đường cong tuning trên holdout. Chỉ số dùng dense cosine top-1, không phải hybrid ranking score, xác suất đúng hay mức entailment. Partial và câu trong phạm vi nhưng thiếu nguồn được báo riêng; câu ngoài phạm vi không tham gia chọn threshold và vẫn cần policy guard. Kết quả `CANDIDATE_REQUIRES_REVIEW` vẫn cần reviewer đánh giá, cỡ mẫu và bất định; không tự cài vào runtime. Tách hiệu chỉnh khỏi dữ liệu dùng để chọn/tối ưu mô hình là nguyên tắc đánh giá cơ bản; xem [hướng dẫn threshold của scikit-learn](https://scikit-learn.org/stable/modules/classification_threshold.html).

Các trạng thái như `AWAITING_LABELS`, `AWAITING_CRITERIA`, `INSUFFICIENT_CALIBRATION_POPULATIONS`, `NO_FEASIBLE_THRESHOLD` và `CALIBRATION_ONLY` là kết quả chưa đủ để cài threshold. Mọi trạng thái hiện giữ `runtime_policy_changed=false`, `answer_ready=false` và G1–G7 OPEN.

## 5. Rà soát claim và giới hạn dữ liệu ảnh

Khi review câu trả lời sinh, đối chiếu từng claim với đoạn/span nguồn được dẫn, giữ polarity, điều kiện và giới hạn phạm vi; ghi rõ nguồn chỉ là tài liệu đọc thêm khi nó không xác minh quan sát ảnh. Dùng [CSV trống review claim](../reference/answer_claim_review_template_20261110.csv) để ghi từng claim; không tự điền reviewer hay kết luận. Không biến marker `[S1]` do model tự viết thành citation đã xác thực. Với cohort X-quang, còn thiếu bộ ảnh ngoài BTXRD có quyền, patient/lesion-level split đáng tin cậy và reference standard độc lập. Không dùng dự đoán của mô hình làm ground truth.

Các metric retrieval hiện có là development/regression đã xem; đánh giá BTXRD hiện có là in-source. Chưa có nhãn/reviewer độc lập hoặc quyết định nghiệm thu để đóng gate. Vì vậy có thể hoàn thiện công cụ và báo cáo tái lập, nhưng chưa thể tuyên bố dự án đã hoàn tất 100% hay model đã được kiểm định độc lập.
