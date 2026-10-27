# Trạng thái dự án và ghi chú bàn giao

Cập nhật: **27/10/2026 sau vòng phát triển giai đoạn 11**. Đọc cùng [lộ trình](LO_TRINH_THUC_HIEN_DU_AN_AI.md) để phân biệt phần đã triển khai với tiêu chí nghiệm thu. Commit nền là `59f4dfd`; các thay đổi tài liệu và RAG sau đó hiện nằm trong working tree, xem `git status`. **AI tiếp quản đọc [điểm tiếp tục giai đoạn 11](STAGE11_HANDOFF_VI.md) trước.** Kết quả không thay thế đánh giá lâm sàng.

## Việc đã hoàn thành

| Phần | Thay đổi thực tế | Trạng thái |
| --- | --- | --- |
| Phân tích ảnh | Ứng dụng nhận X-quang và metadata, nạp mô hình cục bộ, trả 10 điểm số và Top-3. | Có chức năng và bài kiểm thử; chưa chứng minh độ chính xác lâm sàng. |
| Lưu ca | `/predict` cấp `prediction_id`; `/cases` lấy kết quả do máy chủ giữ, chỉ lưu một lần trong 10 phút. Không nhận điểm số tự khai từ trình duyệt. | Đã sửa và kiểm thử vòng đời ca. |
| Giao diện | Dữ liệu từ người dùng/API được chèn bằng text an toàn hoặc escape; lịch sử ca có phân trang theo `limit`/`offset`. | Đã sửa và chạy kiểm thử UI/API. |
| Dữ liệu kiểm thử | Bài kiểm thử ca dùng SQLite tạm, không ghi vào CSDL vận hành. | Đã kiểm tra. |
| Cấu trúc file | `docs/guides/` chứa hướng dẫn, `docs/reports/` chứa Word, `docs/reference/` chứa tham chiếu API; `rag/data/` chứa dữ liệu nguồn. Đã cập nhật `verify_api.py`, pipeline RAG và đường dẫn tài liệu. | Đã chuyển và rà soát các tham chiếu. |
| Giai đoạn 10 | 12 trang NCI, hiện 416 đoạn sau sửa bộ trích xuất; giữ URL, mục, thời điểm và mã băm. | Đạt ở mức kho nguồn có thể truy vết; độ phủ y khoa còn thiếu. |
| Giai đoạn 11 | Hybrid local; index 416 × 384, manifest schema 2; có thêm rerank khái niệm và bộ lọc thử nghiệm; 12 câu regression, 28 câu V2 và 20 câu stress V3. | Rerank triển vọng nhưng opt-in; bộ lọc chặn nhầm nhiều câu dương. **Chưa đạt điều kiện dùng làm nền trả lời y khoa**. |

Chi tiết pipeline: [kho nguồn](guides/README_RAG_CORPUS_VI.md) và [chỉ mục](guides/README_RAG_INDEX_VI.md). Trọng số embedding, chỉ mục, HTML tải về, CSDL và kết quả runtime nằm trong các đường dẫn Git bỏ qua; bản checkout mới phải tải mô hình và tạo lại chỉ mục.

## Bằng chứng kiểm tra gần nhất

- `python -m unittest discover -s tests -v`: **4/4 đạt**.
- `python -m unittest discover -s api_tests -v`: **11/11 đạt**. Log `Test failure` trong bài kiểm tra xử lý lỗi là lỗi giả lập có chủ đích.
- `python -m unittest discover -s ui_tests -v`: **1/1 đạt**.
- `python -m unittest discover -s rag/tests -v`: **20/20 đạt trong vòng giai đoạn 11 mới nhất**. Các kết quả tests/api_tests/ui_tests ở trên là lần chạy trước đó, không được chạy lại trong vòng sửa RAG này.
- `rag/build_corpus.py --offline`: hiện tạo **416 đoạn từ 12 nguồn**. Đã sửa References dùng h6, các block/ô bảng dính chữ và mục danh sách ngắn bị loại; chỉ mục đã xây lại theo schema 2.
- `rag/retrieval.py` với `HF_HUB_OFFLINE=1`: truy vấn mẫu trả đoạn cùng URL/mục/mã băm; không cần kết nối mạng lúc tìm kiếm.
- `python -m pip check`: không có phụ thuộc bị hỏng; `git diff --check`: không có lỗi whitespace.
- Bộ cũ: baseline trước sửa corpus 6/10, MRR 0,417; hiện hybrid đúng nguồn/mục **8/10, MRR 0,700**, routing từ chối 2/2 câu âm.
- V2 dev/test mỗi phần 8 câu có đáp án và 6 câu âm. Hybrid đúng đoạn **6/8 trên dev và 7/8 trên test**; cả hai từ chối 4/6 câu âm. Tập do AI soạn, test đã được xem kết quả, chưa có thẩm định độc lập. Báo cáo đầy đủ: `docs/reference/stage11_20261027/`.
- Thử `--rerank-concepts`: đúng 10/10 câu cũ, 8/8 mỗi phần V2 đã xem và 9/10 câu V3 stress. Không tăng tỷ lệ từ chối câu âm. Bộ lọc `--verify-evidence` không đạt vì chặn nhầm 5/10 câu dương V3 và 8/8 câu dương V2 test đã xem. Cả hai opt-in, mặc định hybrid không đổi. Báo cáo mới: `docs/reference/stage11_evidence_rank_20261027/`; V3 cũng đã được dùng, chưa độc lập.
- `verify_api.py` lần kiểm tra gần nhất **không chạy được vì không có server tại `127.0.0.1:8000`**. Đây không phải kết quả so sánh suy luận API; muốn kiểm tra lại phải khởi động ứng dụng trước.

## Giới hạn và rủi ro đang mở

1. **Đủ bằng chứng chưa được giải quyết:** mặc định còn 2/10 câu cũ và 1/8 câu V2 test trượt. Rerank opt-in xử lý được các ca đó trên tập đã xem, nhưng chưa kiểm định độc lập và vẫn bỏ lọt câu thiếu nguồn. Bộ lọc từ vựng không thể bật mặc định vì false refusal cao. Chưa có ngưỡng similarity đã kiểm định. `candidates_found` chỉ là ứng viên; `answer_ready` luôn false.
2. **Kho nguồn thiếu nhãn:** một số lớp ảnh như simple bone cyst, osteofibroma và synovial osteochondroma chưa có nguồn chuyên biệt. Không để chatbot suy luận chắc chắn về các nhãn đó từ kho hiện tại.
3. **`prediction_id` là trạng thái trong bộ nhớ của một tiến trình:** mất khi khởi động lại, hết hạn sau 10 phút và không dùng chung giữa nhiều worker. Nếu triển khai nhiều worker hoặc cần lưu ca bền vững, phải thiết kế kho trạng thái dùng chung.
4. **Chưa có chatbot, API/chat UI, bộ kiểm thử citation và an toàn.** Điểm softmax của mô hình ảnh không phải xác suất bệnh đã hiệu chuẩn hoặc chẩn đoán mô bệnh học.
5. **Chưa xác minh lại API với model thật sau lần sắp xếp file** bằng `verify_api.py` khi server đang chạy. Kiểm thử tự động hiện dùng predictor giả cho API.

## Việc tiếp theo, theo thứ tự

1. **Hoàn thiện giai đoạn 11:** theo checkpoint mới ở `STAGE11_HANDOFF_VI.md`; bổ sung nguồn và kiểm tra đủ bằng chứng có xử lý ngôn ngữ tốt hơn, kiểm định rerank trên tập mới độc lập. V2/V3 đã sử dụng; không chỉnh từ vựng chỉ để đạt điểm trên chúng. Chạy `rag/compare_evidence.py` để tái lập vào thư mục mới, giữ bằng chứng cũ.
2. **Xác minh hệ thống:** khởi động ứng dụng, chạy `verify_api.py` với ba ca tham chiếu, kiểm tra không thay đổi kết quả mô hình; ghi commit và log kiểm thử trong tài liệu.
3. **Bắt đầu giai đoạn 12 khi retrieval đủ tin cậy:** chọn LLM chạy local phù hợp RAM/VRAM, dựng luồng kiểm tra phạm vi → truy xuất → đánh giá đủ bằng chứng → sinh câu trả lời tiếng Việt → gắn citation từ `source_id`/URL/mục thực. Kiểm thử câu không có nguồn, prompt injection, thông tin định danh và yêu cầu chẩn đoán/phác đồ cá nhân hóa; mời người có chuyên môn rà soát.
4. **Giai đoạn 13:** đánh giá toàn diện và đóng gói sau khi các tiêu chí của giai đoạn 12 đạt.

## Lệnh để tiếp tục

Chạy từ thư mục gốc dự án, sau khi thiết lập `.venv`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements_rag.txt
.\.venv\Scripts\python.exe -m unittest discover -s rag/tests -v
.\.venv\Scripts\python.exe rag/build_index.py --download-model  # chỉ lần đầu tại máy mới
.\.venv\Scripts\python.exe rag/evaluate.py
.\.venv\Scripts\python.exe rag/retrieval.py "Chordoma thường xuất hiện ở vùng nào?" --top-k 5
```

Khi đã có `rag/models/e5-small/`, xây lại chỉ mục bằng `rag/build_index.py` không có `--download-model`. Để chạy `verify_api.py`, khởi động ứng dụng theo [hướng dẫn UI](guides/README_UI_VI.md) ở một terminal trước, sau đó chạy script ở terminal khác. `model_definition.py` và mã nạp mô hình vẫn ở thư mục gốc vì checkpoint và lệnh khởi chạy phụ thuộc vị trí import hiện tại.
