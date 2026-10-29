# Chỉ mục vector và truy xuất RAG — giai đoạn 11

## Trạng thái mới nhất — 29/10/2026

Audit offline hiện PASS cho **21 nguồn đăng ký, 759 chunk, index 759 × 384, 9 dataset và 16 report** ([audit hiện hành](../reference/stage11_integrity_audit_20261029_evidence_neutral_v8.json), [summary](../reference/stage11_verification_summary_20261029_evidence_neutral_v8.json)); comparison được đối chiếu với manifest, replay kiểm hash report trước khi chạy. Parser nguồn yêu cầu định danh CC BY 4.0 tường minh, từ chối BY-NC/BY-ND/BY-SA và nhận wrapper PMC EFetch nếu chứa đúng một JATS article. Một ca PMC11370983 được cache riêng để source-review nhưng không thuộc registry/corpus. Corpus SHA-256 `b34d318c136f591d3b417e39603141f7d7836b960bf72d75a547653529e48d9d`; source-lock SHA-256 `45bb28d3b1f1e4c4d0344785e36a7860816bea26bd20c7ab8a4ffb3c7daa6fa1`; manifest SHA-256 `ad75159115ef04c360fda64dcb0f31b977158a607f3298b83fa63cabdd900a31`; retrieval config SHA-256 `c8f45d1af962c5b78a57096db2b219f66bd85168fdaf094daec7c7e083533aed`. Audit xác minh provenance/artifact, không phải clinical validation.

Expansion dev is agent-authored, viewed, and tuned (22 positive/3 negative): hybrid Recall@5 **22/22**, MRR **0.683**, evidence P/R/nDCG **0.200/0.977/0.753**, negative abstention **3/3**, false refusal **0/22**, routing **25/25**. The legacy flat gold list does not encode whether all listed chunks are jointly required; do not treat list completion as adjudicated evidence coverage. The viewed V2 regression is **8/8**, MRR **0.733**, negative abstention **6/6** after adding a three-chunk NCI chondrosarcoma route prompted by the already viewed p13 miss. This is in-sample tuning, not holdout validation. Concept rerank on current reports is **19/22**, MRR **0.573** on dev and **8/8**, MRR **0.938** on viewed V2; it remains opt-in because dev performance is lower and V2 is not independent. Source-specific synovial (4 positive/2 negative) remains **4/4** Recall@5, MRR **0.542**, negative abstention **2/2**; the separate synonym policy dev retrieved its one positive at rank 1 and abstained on the unsupported BTXRD mapping. The OFD review set (five positive/two policy-negative agent-authored cases) has ordinary retrieval **5/5**, MRR **0.700**, negative abstention **2/2** after exploratory query tuning on the same corpus; strict lexical mode passes only **2/5** positives. All these are development diagnostics, not independent evidence. The current bundle is [v8 (16 reports)](../reference/stage11_policy_rerun_20261029_evidence_neutral_v8/) with manifest SHA-256 `2871ad8cc5b27f9dafa328123139a1b72624a7befaf61b7c4627cf0a0bff1f4a`; comparison and complete run metadata are linked from the [v8 verification summary](../reference/stage11_verification_summary_20261029_evidence_neutral_v8.json).

The strict lexical `--verify-evidence` filter remains unsuitable as a general safety mechanism on the current 759-chunk corpus: expansion dev positive abstention **21/22**, viewed V2 **8/8**, synovial source-specific dev **4/4**, and OFD dev **3/5**. These indicate lexical coverage gaps, not missing clinical evidence; lexical matching does not prove entailment. Keep it opt-in. The current full suite passed **74 tests / 127 subtests** with one Starlette deprecation warning ([current summary](../reference/stage11_verification_summary_20261029_evidence_neutral_v8.json), [test record](../reference/stage11_test_run_20261029_evidence_neutral_phrases_v2.json)). Integrity audit: **PASS** for artifact provenance (21 registered source caches, 9 datasets, 16 reports, and validated comparison); deterministic replay: **16/16**, with all report hashes preflighted. These are technical checks and do not establish clinical validity. `answer_ready` remains `false` pending independent review, a blind evaluation set, and citation-entailment assessment.


`retrieval_config.json` defines high-precision cues for unicameral/simple bone cyst, routine knee MRI, general radiographic features, Bone-RADS, and synovial chondromatosis. The verified phrase `synovial osteochondromatosis` is a supported synonym for the canonical condition; the unresolved BTXRD class label `synovial osteochondroma` remains unsupported and is not auto-mapped. The full phrase `osteofibrous dysplasia` routes to its 2024 CC BY 4.0 narrative review; acronym `OFD` is not routed, and BTXRD `osteofibroma` remains unsupported because the review does not define that dataset label. If exactly one source family matches, retrieval reserves the route-specific `preferred_count` (default two; three for the explicit NCI chondrosarcoma route) and fills remaining slots from the full corpus. If the query also explicitly requests an overview, the source abstract is preferred; other source hits and full-corpus candidates remain eligible. Ambiguous/conflicting cues do not route; an explicit caller allowlist cannot be widened. This development heuristic is recorded as `preferred_source_id`/`preferred_section`, not a clinical decision rule. Review these rules with the evaluation config hash before changing them.

Kho nguồn nằm trong `rag/data/`; chỉ mục và mô hình tải về nằm trong `rag/index/` và `rag/models/`, được Git bỏ qua. Không đưa ảnh hoặc dữ liệu ca bệnh vào chỉ mục.

## Tạo chỉ mục

Từ thư mục gốc dự án:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements_rag.txt
.\.venv\Scripts\python.exe rag/build_index.py --download-model
.\.venv\Scripts\python.exe rag/audit.py
.\.venv\Scripts\python.exe rag/evaluate.py
.\.venv\Scripts\python.exe rag/compare.py --output-dir .temp/stage11_rerun
.\.venv\Scripts\python.exe rag/retrieval.py "Chordoma thường xuất hiện ở vùng nào?" --top-k 5
```

Snapshot lịch sử trước 28/10/2026: lần xây lại dùng `rag/build_index.py` không có `--download-model`, khi đó có 439 đoạn × 384 chiều từ 13 nguồn. Trạng thái hiện hành, corpus hash và index manifest ở đầu tài liệu. Mô hình `intfloat/multilingual-e5-small` được ghim revision; vector dùng tiền tố `passage:`/`query:` và chuẩn hóa L2. Không có dịch vụ embedding bên ngoài khi truy vấn.

`rag/index/manifest.json` schema 2 lưu mã băm corpus, source lock, trọng số, các tệp tokenizer/pooling/configuration, ma trận vector và thứ tự chunk. Khi các đầu vào này đổi, truy xuất dừng và yêu cầu xây lại chỉ mục; index schema cũ cũng cần xây lại. Vector tải lên phải hữu hạn và chuẩn hóa L2. Kết quả truy xuất kèm `source_id`, tiêu đề, URL, mục, thời điểm truy cập, mã băm nguồn và đoạn văn để gắn citation thật ở giai đoạn chatbot.

`rag/audit.py` kiểm tra offline allowlist host/giấy phép, registry/source lock, metadata/hash chunk, gold evidence/quote/chunk ID, model revision/trọng số/tokenizer, hợp đồng embedding, và checksum/shape/chuẩn hóa vector index; không nạp embedding model. Evaluator cũng yêu cầu gold khớp `(chunk_id, source, section, text hash)`. Có thể lưu báo cáo bất biến để review cùng thay đổi:

Gold cũ dùng `evidence` cho một nhóm chunk. Với nhiều tập bằng chứng thay thế, dùng `evidence_groups: [[chunk, ...], [alternative, ...]]`; mỗi nhóm phải đủ theo nhãn reviewer. Audit xác thực mọi chunk ở mọi nhóm. Báo cáo vẫn tính Recall/MRR nếu có một chunk phù hợp, đồng thời báo `complete_evidence_group_count` và `evidence_group_rank`; precision/recall/nDCG evidence dùng nhóm được bao phủ tốt nhất thay vì phạt phương án thay thế. Không khai báo đồng thời `evidence` và `evidence_groups`.

```powershell
.\.venv\Scripts\python.exe rag\audit.py --output docs\reference\stage11_integrity_audit_YYYYMMDD.json
```

Audit PASS chỉ xác nhận tính toàn vẹn và provenance của artifact, không xác nhận nội dung y khoa đúng, entailment, độ phủ nguồn hoặc khả năng từ chối an toàn.

## Cách tìm kiếm và trạng thái trả về

CLI mặc định dùng hybrid: embedding câu hỏi gốc, embedding từ khóa mở rộng Việt–Anh và BM25 được kết hợp theo reciprocal rank fusion. Trọng số 2/1/1, hằng số 60, cửa sổ 80 nằm tại `rag/data/retrieval_config.json`. `--mode dense` dùng embedding thuần; `--raw` bỏ qua routing để xem lỗi truy xuất.

`retrieve()` chạy bộ quy tắc trong `rag/policy.py` trước tìm kiếm. Nó có thể trả `out_of_scope`, `insufficient_evidence` hoặc `candidates_found`. Policy chặn một số cụm trực tiếp và tổ hợp nhắc ảnh cá nhân kèm yêu cầu nhận định; image-routing dev hiện có 51 câu âm và 51/51 được route đúng `insufficient_evidence`. Cumulative text-only edge matrix riêng có 33/33 personal-image probes abstain cho specialist và 18/18 câu giáo dục vẫn trong scope; vòng mới nhất thêm 5 probe cá nhân và 2 control giáo dục. Các probe không độc lập, mù hoặc đại diện; biến thể khác vẫn có thể lọt. `candidates_found` chỉ có nghĩa là có đoạn ứng viên; `answer_ready` luôn là `false`. API Python `search()` giữ mặc định dense/raw để so sánh; `Retriever.search()` mặc định hybrid/raw.

**Giới hạn ảnh:** `retrieve()` nhận văn bản; API này không đọc tệp đính kèm, pixel ảnh hoặc cờ cho biết request có ảnh. Các probe đo cách hỏi bằng chữ, không chứng minh phát hiện ảnh upload hay câu hỏi mơ hồ như “bạn nghĩ sao?”. Không nối kết quả retrieval thành diễn giải ảnh; `answer_ready=false`.

`score` là cosine của câu hỏi gốc; `ranking_score` là điểm RRF khi dùng hybrid. `--min-score` lọc theo cosine gốc trước khi kết hợp thứ hạng. Không diễn giải hai điểm này thành xác suất hoặc ngưỡng an toàn đã được kiểm định. `--source-id` có thể lặp để giới hạn tập nguồn.

Hai chế độ thử nghiệm mới (không bật mặc định): `--rerank-concepts` xếp lại 80 ứng viên theo các khái niệm của câu hỏi; `--verify-evidence` đòi đủ độ phủ từ vựng và từ chối từ chưa biết. Bộ lọc nghiêm ngặt hiện có tỷ lệ từ chối nhầm rất cao, không nên dùng cho người dùng cuối. Xếp hạng lại giữ các ứng viên chưa chắc chắn và trả diagnostics; nó không xác minh được sự đúng đắn của kết luận. Không kết hợp hai cờ, không dùng cùng `--raw`. Cả hai vẫn trả `answer_ready: false`.

## Đánh giá và giới hạn

`evaluation_questions.json` giữ 12 câu regression cũ, đo đúng nguồn và mục. `evaluation_v2.json` thêm 28 câu, mỗi phần dev/test có 8 câu có đáp án và 6 câu âm. V2 đo đúng đoạn bằng nguồn/mục/mã băm và chứa trích đoạn làm bằng chứng. Công cụ từ chối đánh giá nếu corpus hoặc evidence không còn khớp. Đây là dữ liệu do AI soạn, chưa được chuyên gia độc lập thẩm định; phần test đã được chạy trong phiên 27/10 và không được dùng để chỉnh phương án rồi tiếp tục coi là test chưa từng thấy.

`rag/evaluate.py --mode hybrid --apply-policy --dataset rag/data/evaluation_v2.json --split test --summary` chạy riêng một phép đo. Thêm `--output` để lưu JSON đầy đủ. `rag/compare.py` chạy cùng các cấu hình trên một model local; báo cáo lưu hash corpus, config, model revision, mã thực thi và từng hit. Kết quả cuối đã lưu tại `docs/reference/stage11_20261027/`. Cần kiểm định ngưỡng trên tập phát triển riêng trước khi dùng fallback tự động.

Các nhãn u chưa có nguồn chuyên biệt trong kho vẫn là khoảng trống nội dung. Trước khi chatbot ở **giai đoạn 12** được đưa vào sử dụng, cần mở rộng nguồn, kiểm tra citation, xử lý câu hỏi thiếu bằng chứng và kiểm thử từ chối chẩn đoán hoặc phác đồ cá nhân hóa. Có thể dựng nguyên mẫu chatbot ngay sau khi retrieval hoạt động, nhưng nghiệm thu giai đoạn 12 phụ thuộc các kiểm thử đó và rà soát chuyên môn.

## Completion Note — Giai đoạn 11

- Ngày: 27/10/2026.
- Mô hình: `intfloat/multilingual-e5-small`, revision được ghim trong `rag/retrieval.py`; checksum trọng số và vector trong `rag/index/manifest.json`.
- Vector store tại snapshot lưu ở phần cũ: NumPy cục bộ, **439 đoạn × 384 chiều**; schema 2, top-k 5; chưa đặt ngưỡng cosine.
- Baseline trước sửa corpus: source+section recall@5 = 0,60 (6/10), MRR@5 = 0,417; không trả hit cho câu âm = 0/2.
- Kết quả cuối trên corpus mới: dense 7/10, MRR 0,483; hybrid 8/10, MRR 0,700. Routing từ chối được 2/2 câu âm của bộ cũ.
- V2 dev với hybrid/routing: đúng đoạn 6/8, MRR 0,625; không trả hit cho câu âm 4/6.
- V2 test với hybrid/routing: đúng đoạn **7/8**, MRR **0,713**; không trả hit cho câu âm **4/6**. Chưa có câu dương bị chặn trong bộ này.
- Citation kỹ thuật: truy ngược được URL/mục/mã băm cho từng hit; đã kiểm thử việc từ chối chỉ mục cũ khi source lock đổi.
- Trạng thái: **BLOCKED để dùng làm nền cho câu trả lời y khoa của chatbot**. Còn lỗi xếp hạng và chưa có mô-đun kiểm tra đủ bằng chứng; các câu về DNA tại nhà bảo đảm phát hiện sớm hoặc thực phẩm chức năng chữa khỏi chordoma vẫn nhận hit. Xem danh sách ca trượt và điểm tiếp tục tại [bàn giao giai đoạn 11](../STAGE11_HANDOFF_VI.md). Kiểm thử ở vòng hybrid lịch sử này: 12/12 đạt; vòng bổ sung bên dưới đạt 20/20. Đây không phải số liệu của bộ image-routing dev 26 câu trong snapshot hiện tại.

### Lịch sử rà soát — trạng thái trước khi ingest nguồn synovial 28/10/2026

- Thêm `rag/audit.py` và regression tests để xác minh liên kết registry → source lock → corpus → gold evidence → index mà không tải model.
- Audit snapshot 28/10: **PASS**, 21 nguồn, 759 chunk. Snapshot hiện hành là `docs/reference/stage11_integrity_audit_20261029_evidence_neutral_v8.json`.
- Dev expansion (9 câu, đã dùng để phát triển): hybrid + policy Recall@5 **6/6**, MRR **0,639**, câu âm abstention **3/3**, routing **9/9**.
- V2 test (14 câu, đã xem trước đó; chỉ dùng hồi quy): đúng evidence Recall@5 **7/8**, MRR **0,713**, negative abstention **6/6**, routing **14/14**; positive abstention **0/8**. Đây không phải kiểm định độc lập.
- Full suite snapshot cũ: **48 passed, 40 subtests passed**. Giai đoạn 11 vẫn **INCOMPLETE/BLOCKED cho sinh câu trả lời y khoa**: cần đánh giá do chuyên gia/người đánh giá độc lập, nhất là false acceptance, false refusal và citation entailment. `answer_ready` vẫn `false`.

### Vòng thử xếp hạng và kiểm tra bằng chứng tiếp theo

Kết quả khám phá của `--rerank-concepts`: 10/10 câu regression đúng nguồn/mục, 8/8 mỗi phần V2 đúng đoạn và 9/10 câu V3 đúng đoạn. Khả năng từ chối câu âm vẫn như baseline. Bộ `--verify-evidence` từ chối 100% câu âm trong phép thử nhưng cũng chặn 5/10 câu dương V3 và 8/8 câu dương V2 test đã xem; **không đạt**, không bật mặc định. Không đổi gold/cấu hình theo kết quả V3 sau phép thử này.

V3 có 20 câu do AI soạn, đã được sử dụng; không phải tập đánh giá độc lập. Báo cáo tại `docs/reference/stage11_evidence_rank_20261027/`. Tái lập bằng `python rag/compare_evidence.py --output-dir .temp/evidence_rerun` (phải là thư mục mới). Kiểm thử RAG hiện **20/20 đạt**; giai đoạn 11 vẫn chưa nghiệm thu.
