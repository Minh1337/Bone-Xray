# Chỉ mục vector và truy xuất RAG — giai đoạn 11

Kho nguồn nằm trong `rag/data/`; chỉ mục và mô hình tải về nằm trong `rag/index/` và `rag/models/`, được Git bỏ qua. Không đưa ảnh hoặc dữ liệu ca bệnh vào chỉ mục.

## Tạo chỉ mục

Từ thư mục gốc dự án:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements_rag.txt
.\.venv\Scripts\python.exe rag/build_index.py --download-model
.\.venv\Scripts\python.exe rag/evaluate.py
.\.venv\Scripts\python.exe rag/compare.py --output-dir .temp/stage11_rerun
.\.venv\Scripts\python.exe rag/retrieval.py "Chordoma thường xuất hiện ở vùng nào?" --top-k 5
```

Lần xây lại gần nhất dùng `rag/build_index.py` không có `--download-model`. Mô hình `intfloat/multilingual-e5-small` được ghim theo revision trong `rag/retrieval.py`; vector dùng chuẩn `passage: ` cho đoạn và `query: ` cho câu hỏi, chuẩn hóa L2. Kho hiện có **439 đoạn × 384 chiều từ 13 nguồn**; corpus hash là `552eb6b313ca472dc92e5a20280dbf02a39d74091439a895099127c6b96c8dfb`. Không có dịch vụ embedding bên ngoài khi truy vấn.

`rag/index/manifest.json` schema 2 lưu mã băm corpus, source lock, trọng số, các tệp tokenizer/pooling/configuration, ma trận vector và thứ tự chunk. Khi các đầu vào này đổi, truy xuất dừng và yêu cầu xây lại chỉ mục; index schema cũ cũng cần xây lại. Vector tải lên phải hữu hạn và chuẩn hóa L2. Kết quả truy xuất kèm `source_id`, tiêu đề, URL, mục, thời điểm truy cập, mã băm nguồn và đoạn văn để gắn citation thật ở giai đoạn chatbot.

## Cách tìm kiếm và trạng thái trả về

CLI mặc định dùng hybrid: embedding câu hỏi gốc, embedding từ khóa mở rộng Việt–Anh và BM25 được kết hợp theo reciprocal rank fusion. Trọng số 2/1/1, hằng số 60, cửa sổ 80 nằm tại `rag/data/retrieval_config.json`. `--mode dense` dùng embedding thuần; `--raw` bỏ qua routing để xem lỗi truy xuất.

`retrieve()` chạy bộ quy tắc trong `rag/policy.py` trước tìm kiếm. Nó có thể trả `out_of_scope`, `insufficient_evidence` hoặc `candidates_found`. Trạng thái cuối chỉ có nghĩa là có đoạn ứng viên; `answer_ready` luôn là `false` vì chưa có mô-đun xác minh đủ bằng chứng. Bộ quy tắc chỉ nhận một số dạng câu hỏi đã định nghĩa và vẫn bỏ lọt câu hỏi liên quan u xương nhưng không có câu trả lời trong kho. API Python `search()` giữ mặc định dense/raw để so sánh; `Retriever.search()` mặc định hybrid/raw.

`score` là cosine của câu hỏi gốc; `ranking_score` là điểm RRF khi dùng hybrid. `--min-score` lọc theo cosine gốc trước khi kết hợp thứ hạng. Không diễn giải hai điểm này thành xác suất hoặc ngưỡng an toàn đã được kiểm định. `--source-id` có thể lặp để giới hạn tập nguồn.

Hai chế độ thử nghiệm mới (không bật mặc định): `--rerank-concepts` xếp lại 80 ứng viên theo các khái niệm của câu hỏi; `--verify-evidence` đòi đủ độ phủ từ vựng và từ chối từ chưa biết. Bộ lọc nghiêm ngặt hiện có tỷ lệ từ chối nhầm rất cao, không nên dùng cho người dùng cuối. Xếp hạng lại giữ các ứng viên chưa chắc chắn và trả diagnostics; nó không xác minh được sự đúng đắn của kết luận. Không kết hợp hai cờ, không dùng cùng `--raw`. Cả hai vẫn trả `answer_ready: false`.

## Đánh giá và giới hạn

`evaluation_questions.json` giữ 12 câu regression cũ, đo đúng nguồn và mục. `evaluation_v2.json` thêm 28 câu, mỗi phần dev/test có 8 câu có đáp án và 6 câu âm. V2 đo đúng đoạn bằng nguồn/mục/mã băm và chứa trích đoạn làm bằng chứng. Công cụ từ chối đánh giá nếu corpus hoặc evidence không còn khớp. Đây là dữ liệu do AI soạn, chưa được chuyên gia độc lập thẩm định; phần test đã được chạy trong phiên 27/10 và không được dùng để chỉnh phương án rồi tiếp tục coi là test chưa từng thấy.

`rag/evaluate.py --mode hybrid --apply-policy --dataset rag/data/evaluation_v2.json --split test --summary` chạy riêng một phép đo. Thêm `--output` để lưu JSON đầy đủ. `rag/compare.py` chạy cùng các cấu hình trên một model local; báo cáo lưu hash corpus, config, model revision, mã thực thi và từng hit. Kết quả cuối đã lưu tại `docs/reference/stage11_20261027/`. Cần kiểm định ngưỡng trên tập phát triển riêng trước khi dùng fallback tự động.

Các nhãn u chưa có nguồn chuyên biệt trong kho vẫn là khoảng trống nội dung. Trước khi chatbot ở **giai đoạn 12** được đưa vào sử dụng, cần mở rộng nguồn, kiểm tra citation, xử lý câu hỏi thiếu bằng chứng và kiểm thử từ chối chẩn đoán hoặc phác đồ cá nhân hóa. Có thể dựng nguyên mẫu chatbot ngay sau khi retrieval hoạt động, nhưng nghiệm thu giai đoạn 12 phụ thuộc các kiểm thử đó và rà soát chuyên môn.

## Completion Note — Giai đoạn 11

- Ngày: 27/10/2026.
- Mô hình: `intfloat/multilingual-e5-small`, revision được ghim trong `rag/retrieval.py`; checksum trọng số và vector trong `rag/index/manifest.json`.
- Vector store hiện tại: NumPy cục bộ, **439 đoạn × 384 chiều**; schema 2, top-k 5; chưa đặt ngưỡng cosine.
- Baseline trước sửa corpus: source+section recall@5 = 0,60 (6/10), MRR@5 = 0,417; không trả hit cho câu âm = 0/2.
- Kết quả cuối trên corpus mới: dense 7/10, MRR 0,483; hybrid 8/10, MRR 0,700. Routing từ chối được 2/2 câu âm của bộ cũ.
- V2 dev với hybrid/routing: đúng đoạn 6/8, MRR 0,625; không trả hit cho câu âm 4/6.
- V2 test với hybrid/routing: đúng đoạn **7/8**, MRR **0,713**; không trả hit cho câu âm **4/6**. Chưa có câu dương bị chặn trong bộ này.
- Citation kỹ thuật: truy ngược được URL/mục/mã băm cho từng hit; đã kiểm thử việc từ chối chỉ mục cũ khi source lock đổi.
- Trạng thái: **BLOCKED để dùng làm nền cho câu trả lời y khoa của chatbot**. Còn lỗi xếp hạng và chưa có mô-đun kiểm tra đủ bằng chứng; các câu về DNA tại nhà bảo đảm phát hiện sớm hoặc thực phẩm chức năng chữa khỏi chordoma vẫn nhận hit. Xem danh sách ca trượt và điểm tiếp tục tại [bàn giao giai đoạn 11](../STAGE11_HANDOFF_VI.md). Kiểm thử ở vòng hybrid này: 12/12 đạt; vòng bổ sung bên dưới đạt 20/20.

### Vòng thử xếp hạng và kiểm tra bằng chứng tiếp theo

Kết quả khám phá của `--rerank-concepts`: 10/10 câu regression đúng nguồn/mục, 8/8 mỗi phần V2 đúng đoạn và 9/10 câu V3 đúng đoạn. Khả năng từ chối câu âm vẫn như baseline. Bộ `--verify-evidence` từ chối 100% câu âm trong phép thử nhưng cũng chặn 5/10 câu dương V3 và 8/8 câu dương V2 test đã xem; **không đạt**, không bật mặc định. Không đổi gold/cấu hình theo kết quả V3 sau phép thử này.

V3 có 20 câu do AI soạn, đã được sử dụng; không phải tập đánh giá độc lập. Báo cáo tại `docs/reference/stage11_evidence_rank_20261027/`. Tái lập bằng `python rag/compare_evidence.py --output-dir .temp/evidence_rerun` (phải là thư mục mới). Kiểm thử RAG hiện **20/20 đạt**; giai đoạn 11 vẫn chưa nghiệm thu.
