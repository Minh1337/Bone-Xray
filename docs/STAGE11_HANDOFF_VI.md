# Điểm tiếp tục giai đoạn 11

## Bàn giao mới nhất — thêm Giai đoạn 11A và catalogue ảnh BTXRD — 27/10/2026

- Đã tải BTXRD từ Figshare chính thức (CC BY 4.0; DOI `10.6084/m9.figshare.27865398.v1`). Archive 840,474,929 byte; MD5 nguồn khớp `59132a5036d030580ccade8add8f13df`; SHA-256 `e7c800c3b4e090262b160525a0765f9d93bcc53d639c03806a3ac47b0ded3373`.
- Manifest runtime: `data/external_datasets/BTXRD/reference/manifest.csv`; summary: `data/external_datasets/BTXRD/reference/summary.json`. Có 3.746 ảnh và đủ 22/22 metadata; 3.745 nhãn hợp lệ (1.879 no-tumor, 1.866 tumor), 1 ảnh `IMG001276.jpeg` xung đột nhiều subtype nên nhãn để trống; 21 nhóm exact duplicate gồm 42 ảnh.
- Không có patient/lesion IDs; checkpoint có nguồn huấn luyện BTXRD nhưng chỉ giữ `split_signature`, thiếu danh sách image ID từng split. Vì vậy mọi partition để `unassigned`, `independent_of_checkpoint_training=false`. Không tính hay tuyên bố accuracy trên BTXRD cho checkpoint đang có; muốn benchmark ảnh chụp mới phải có nguồn khác, độc lập, có quyền dùng và nhãn chuyên gia.
- Script tái lập: `tools/prepare_btxrd_reference.py` (yêu cầu `openpyxl==3.1.5`, đã khai báo trong `requirements_rag.txt`). Hướng dẫn tại `docs/guides/README_IMAGE_REFERENCE_VI.md`, register tại `docs/reference/btxrd_source_register.json`, lộ trình tại `docs/LO_TRINH_THUC_HIEN_DU_AN_AI.md`.
- Giai đoạn 11A hoàn tất phần tải/kiểm checksum/catalogue và đánh dấu rõ giới hạn leakage; mục tiêu external validation chưa thể nghiệm thu. Giai đoạn 11 RAG cũng chưa hoàn tất: `answer_ready=false`, chatbot chưa có. Trạng thái và các hạng mục trước đó giữ nguyên bên dưới.

### Việc tiếp tục

1. Tiếp tục tìm một bộ X-quang ngoài BTXRD có giấy phép, nhãn chuẩn chuyên gia và provenance; không dùng ảnh ngẫu nhiên trên web làm nhãn chuẩn.
2. Nếu có thể, khôi phục danh sách split train/validation/test gốc; không chia ngẫu nhiên ảnh hiện tại do thiếu patient/lesion IDs.
3. Song song tiếp tục RAG theo phần bàn giao cũ dưới đây: tập độc lập, false refusal/acceptance, xác minh nguồn/nhãn; chỉ sau nghiệm thu mới mở chatbot.

Nguồn: [Figshare BTXRD](https://figshare.com/articles/dataset/A_Radiograph_Dataset_for_the_Classification_Localization_and_Segmentation_of_Primary_Bone_Tumors/27865398), [bài báo Scientific Data](https://www.nature.com/articles/s41597-024-04311-y).

Lệnh tái tạo catalogue sau khi cài dependency:

```powershell
\.venv\Scripts\python.exe -m pip install -r requirements_rag.txt
\.venv\Scripts\python.exe tools\prepare_btxrd_reference.py
```

## Bàn giao mới nhất — cập nhật hybrid vocabulary — 27/10/2026

- Corpus hiện **439 đoạn / 13 nguồn** (12 NCI, 1 Open Orthopaedics CC BY 4.0); hash `552eb6b313ca472dc92e5a20280dbf02a39d74091439a895099127c6b96c8dfb`. Trang nguồn đã lọc khối Metrics/downloads khỏi corpus. Index 439 × 384 đã được dựng lại.
- `retrieval_config.json` lên `hybrid-v2`; thêm đồng nghĩa Việt–Anh cho unicameral/simple bone cyst, vị trí humerus, cohort hồi cứu, cỡ mẫu, tiêm và kết quả tránh mổ mở. `simple bone cyst` được chuyển khỏi danh sách unsupported vì hiện có bằng chứng trong corpus; các nhãn thiếu khác vẫn bị chặn.
- Tập dev mới `rag/data/evaluation_expansion_dev_v1.json`: 6 câu có đáp án, 3 câu âm. Kết quả apply-policy hybrid: Recall@5 **6/6**, MRR@5 **0,639**, negative abstention **3/3**, routing accuracy **9/9**. Báo cáo tại `docs/reference/stage11_expansion_dev_v1.json`. Tập do AI soạn, dùng khi phát triển/tuning và có rà lại evidence sau khi xem hit; không phải test độc lập.
- Đã gắn lại bằng chứng cho câu dev V2 `n04` vì nguồn mới trả lời được câu simple bone cyst. Test split V2 không đổi nhưng đã xem trước đó; toàn bộ V2 chỉ regression. Với policy bật: 17 câu dương Recall@5 **14/17**, MRR@5 **0,688**; 11/11 câu âm được từ chối; routing accuracy **28/28**. `frozen_config_matches=false` là điều dự kiến do vocabulary đã đổi. Báo cáo: `docs/reference/stage11_20261027_config_v2_regression.json`.
- RAG test: **23 passed, 24 subtests passed**. Full suite: **39 passed, 31 subtests passed**, một cảnh báo deprecation Starlette. Thêm kiểm tra ngăn Metrics vào corpus và kiểm tra expansion/routing tiếng Việt.
- `answer_ready` tiếp tục false; không có chatbot. Điểm tiếp theo là thiết kế tập độc lập do người khác rà soát, rồi đo retrieval/false refusal/false acceptance trên nhiều nhãn. Tiếp tục xác minh `osteofibroma`; không xem kết quả dev là bằng chứng an toàn y khoa.

Lệnh tái lập: `.\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q`; `.\.venv\Scripts\python.exe rag\evaluate.py --mode hybrid --apply-policy --dataset rag\data\evaluation_expansion_dev_v1.json --output docs\reference\stage11_expansion_dev_v1.json --summary`. Các mục cũ phía dưới là lịch sử, số liệu được giữ theo thời điểm đo.

## Bàn giao phiên trước — 27/10/2026

- Đã mở rộng `rag/data/sources.json` thêm một nguồn Open Orthopaedics CC BY 4.0; nguồn ghi rõ tác giả, publisher, ngày, URL, giấy phép và scope. Nghiên cứu là cohort hồi cứu 51 ca UBC đầu trên xương cánh tay về một phương pháp điều trị, không phải chỉ dẫn tổng quát.
- Pipeline hiện xác thực host, giấy phép và scope cho nguồn ngoài NCI, gắn metadata nguồn lên từng chunk, đồng thời lọc email/boilerplate của trang nguồn.
- Corpus/index mới: **440 chunks, 13 sources, 384 dimensions**. Corpus SHA-256: `466a467a7b27dae86ab94b6b76d33d22ef32618a2b2719aeb6f25d3f242b5a15`. `evaluation_v2.json` và `evaluation_evidence_v3.json` được đồng bộ hash corpus; gold/câu hỏi không thay đổi. Các tập này đã được xem, không phải đánh giá độc lập.
- RAG tests: **21 passed, 21 subtests passed**. Full project: **37 passed, 28 subtests passed**, một cảnh báo deprecation Starlette.
- Chạy lại hybrid trên `evaluation_v2.json` (28 câu đã xem; retrieval thô, `apply_policy=false`): Recall@5 **13/16 = 0,8125**, MRR@5 **0,66875**; **12/12 câu âm vẫn có hit**. Báo cáo đầy đủ tại `docs/reference/stage11_20261027_source_expansion_v1.json`. Không dùng kết quả này để tuyên bố khả năng từ chối hay đánh giá độc lập.
- Truy vấn tiếng Anh về nguồn mới lấy đúng source và hit, nhưng `status=candidates_found`, `answer_ready=false`. Câu hỏi tương đương tiếng Việt trả `insufficient_evidence`/`corpus_coverage_gap`; cần sửa/đo lại multilingual retrieval và routing.
- Nguồn AAOS không được ingest do điều khoản hạn chế tái sử dụng; tải MDPI bị 403, PMC gặp lỗi TLS. Hai nguồn không toàn văn kiểm chứng được nên không đưa vào corpus. Nhãn `osteofibroma` vẫn chưa được xác minh với metadata dataset gốc/chuyên gia.
- Giai đoạn 11 **chưa hoàn tất**; chatbot chưa được xây. Không bật sinh câu trả lời hoặc `answer_ready` dựa riêng trên hit.

### Lệnh tiếp tục

```powershell
.\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q
.\.venv\Scripts\python.exe rag/retrieval.py "What did the retrospective cohort report about unicameral bone cysts of the proximal humerus?" --top-k 5
```

Trước tiên xử lý lỗi tiếng Việt trên bằng các câu dev mới; không tuning trên test V2/V3 đã xem. Sau đó mới tìm tiếp nguồn CC BY/được phép, xác minh nhãn `osteofibroma`, bổ sung tập độc lập và đánh giá đủ bằng chứng. Phần dưới ghi lịch sử các vòng trước, giữ nguyên để tra cứu.

## Điểm bàn giao tại phiên trước — 27/10/2026

Lần tiếp tục này đã đọc README tiếng Anh/Việt và toàn bộ Markdown trong `docs/`, đối chiếu code với handoff, rồi chạy toàn bộ suite:

```powershell
\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q
# 36 passed, 28 subtests passed; một Starlette deprecation warning
```

Repository bắt đầu ở `main`, `HEAD=d1ef896` (`Harden RAG policy routing and document handoff`), working tree sạch, local branch ahead `origin/main` một commit. Policy routing mới và 15 regression cases đã commit; đoạn lịch sử ngay dưới đây ghi “chưa commit” tại thời điểm cũ và không còn mô tả trạng thái hiện nay.

**Tiến độ kỹ thuật:** không đổi corpus/index/gold trong lượt này. Giai đoạn 11 vẫn chưa nghiệm thu; strict lexical evidence filter đã thất bại do false refusal, reranker mới được đo trên các tập đã xem, `answer_ready` luôn `false`, và chưa có chatbot.

**Bước phát triển kế tiếp:** mở rộng corpus có kiểm soát. Đã tìm thấy tài liệu AAOS hữu ích cho simple bone cyst và multiple osteochondromas, nhưng chưa ingest vì cần xác minh quyền tái sử dụng. Nhãn `osteofibroma` chưa được tự ý đồng nhất với osteofibrous dysplasia. Xác minh nguồn dữ liệu nhãn và điều khoản trước; sau đó cập nhật `sources.json`, tạo lại corpus/index, gắn lại gold và lưu báo cáo mới vào thư mục mới. Không sửa các tập V2/V3 đã xem rồi gọi chúng là đánh giá độc lập.

Xác minh API/model thật đã hoàn tất: `verify_api.py` trả `API_LOCAL_PARITY_PASSED` cho 3/3 ca, sai lệch score tối đa 0, metadata và hash ảnh khớp; metadata thiếu bị từ chối 422, ảnh hỏng bị từ chối 415. Báo cáo runtime: `api_results/20261027_212246_844539/api_report.json` (Git bỏ qua). Phép này chỉ so với baseline local, không phải notebook parity hay đánh giá lâm sàng.

## Cập nhật phiên làm việc ngày 27/10/2026 lúc 17:27

Đã hoàn thiện và kiểm tra phần routing an toàn cho các câu hỏi có tuyên bố
không được corpus hiện tại xác minh trong `rag/policy.py`. Policy hiện nhận
diện bốn nhóm chính: thuốc/thảo dược/thực phẩm chức năng được cho là chữa
bệnh, thiết bị hoặc xét nghiệm tại nhà hứa hẹn chẩn đoán, yêu cầu giá/chi phí
ngoài kho NCI, và thiết bị/ứng dụng thay thế bác sĩ hoặc chuyên gia. Các câu
này được trả về `insufficient_evidence` trước khi nạp model. Đã bổ sung 15
regression cases tiếng Việt/Anh trong `rag/tests/test_retrieval.py`.

Validation đã chạy bằng môi trường chuẩn `.venv`:

```powershell
.\.venv\Scripts\python.exe -m pytest rag/tests -q
# 20 passed, 21 subtests passed
git diff --check
# không có lỗi whitespace
```

Tại thời điểm bàn giao, hai file dưới đây **đang sửa nhưng chưa commit**:

- `rag/policy.py`
- `rag/tests/test_retrieval.py`

Các thư mục `.pytest_cache/` và `__pycache__/` chỉ là file cache bị Git
ignore, không phải thay đổi cần bàn giao. Không chạy lại API/model thật trong
phiên này vì mục tiêu là hoàn thiện routing và test; API vẫn cần được khởi
động rồi kiểm tra riêng theo hướng dẫn bên dưới.

### Việc làm đầu tiên vào phiên sau

1. Chạy lại `.\.venv\Scripts\python.exe -m pytest rag/tests -q` sau khi mở
   workspace để xác nhận môi trường.
2. Xem `git diff -- rag/policy.py rag/tests/test_retrieval.py`, sau đó quyết
   định commit hai thay đổi này cùng nhau; không commit cache.
3. Nếu tiếp tục giai đoạn 11, tạo một tập câu hỏi mới độc lập để đánh giá
   policy và rerank; không tối ưu thêm chỉ trên V2/V3 đã xem.
4. Bổ sung nguồn cho `simple bone cyst`, `osteofibroma` và
   `synovial osteochondroma`, rồi xây lại corpus/index theo hướng dẫn nếu dữ
   liệu thay đổi.
5. Khi cần xác minh tích hợp, khởi động API trước rồi chạy `verify_api.py`;
   ghi kết quả mới vào tài liệu, không coi việc routing test là kiểm chứng
   độ chính xác lâm sàng.

## Điểm dừng mới nhất sau vòng thử kiểm tra bằng chứng

Ngày 27/10/2026, đã hoàn thành thử nghiệm bổ sung bằng model/index hiện có, không tải thêm model. **Phần xếp hạng lại cải thiện các câu đã biết; bộ lọc đủ bằng chứng bằng từ vựng thất bại vì từ chối nhầm nhiều câu tiếng Việt. Cả hai giữ opt-in, mặc định vẫn hybrid như vòng trước; answer_ready luôn false.** Chưa nghiệm thu giai đoạn 11, chưa có chatbot.

File mới: `rag/evidence.py`, `rag/data/evidence_config.json`, `rag/data/evaluation_evidence_v3.json`, `rag/compare_evidence.py`, `rag/tests/test_evidence.py`. `retrieval.py` và `evaluate.py` thêm cờ `--rerank-concepts` hoặc `--verify-evidence` (không dùng cả hai; không dùng với `--raw`). Corpus/index/gold V2 không thay đổi. Bộ kiểm thử hiện **20/20 đạt**, gồm giữ citation/lọc nguồn, không dùng heading để chứng minh một sự kiện, không cho phép sinh đáp án chỉ từ kết quả kiểm tra, và phân biệt đâu/đau, mẫu/máu trước khi bỏ dấu.

Thiết kế và mục tiêu thử nghiệm đã ghi trước lần đo tại `docs/reference/EVIDENCE_CHECK_DESIGN_VI.md`. V3 gồm 20 câu Việt/Anh (10 dương/10 âm) đóng băng trước lần chạy; do cùng AI soạn, có sự kiện trùng nguồn cũ, **không phải kiểm định độc lập**. Không đổi từ vựng/gold theo kết quả V3 sau khi đã chạy. Các tập test V2/V3 đều đã được xem và phải coi là regression từ phiên sau.

Kết quả cuối tại **`docs/reference/stage11_evidence_rank_20261027/`**, mỗi file lưu hash mã thực thi, cấu hình và gold. Thư mục `stage11_evidence_20261027/` giữ thử nghiệm lọc đầu tiên; `stage11_20261027/` là vòng hybrid trước. Không ghi đè các thư mục đó.

| Bộ câu hỏi | Hybrid mặc định đúng nguồn/đoạn | Thêm xếp hạng khái niệm | MRR sau xếp hạng | Từ chối nhầm câu dương khi lọc nghiêm ngặt |
| --- | --- | --- | --- | --- |
| Regression cũ | 8/10 | **10/10** | 0,950 | 1/10 |
| V2 dev | 6/8 | **8/8** | 0,813 | 5/8 |
| V2 test đã xem | 7/8 | **8/8** | 0,938 | 8/8 |
| V3 stress | 8/10 | **9/10** | 0,750 | 5/10 |

Xếp hạng lại **không** cải thiện từ chối câu âm: V2 vẫn 4/6 mỗi phần, V3 vẫn 0/10. Bộ lọc nghiêm ngặt từ chối toàn bộ câu âm trong phép thử nhưng mất nhiều câu dương; không đạt điều kiện nội bộ đã chốt, không được bật mặc định hoặc quảng bá như giải pháp an toàn. Nó dựa trên độ phủ từ/cụm từ trong một đoạn, không kiểm tra quan hệ, phủ định, số liệu hoặc sự đúng đắn của một kết luận.

### Việc cần tiếp tục chính xác

1. Ưu tiên phương án kiểm tra đủ bằng chứng có xử lý ngôn ngữ tốt hơn. Không tiếp tục thêm từ vào whitelist chỉ để đạt điểm trên V2/V3 đã xem. Các từ tiếng Việt thông dụng như "kiểm tra", "xâm lấn", "nhìn đôi" hiện khiến bộ lọc nghiêm ngặt từ chối nhầm; chồng lấn khái niệm và bỏ dấu vẫn có thể sai.
2. Rà soát phần rerank trên một tập kiểm định mới độc lập trước khi cân nhắc bật mặc định. Rerank xử lý được `q01/q02/p13` cũ, nhưng V3 còn trượt **ep08** (triệu chứng Ewing bằng tiếng Việt). Các ca n05/n06/n11/n12 cũ vẫn thiếu cơ chế quyết định đủ nguồn khi không bật bộ lọc nghiêm ngặt.
3. Tiếp tục bổ sung nguồn cho nhãn thiếu và thẩm định nội dung; nếu corpus đổi phải gắn lại gold và xây lại index theo hướng dẫn bên dưới. Không đưa ứng dụng sang trạng thái chatbot y khoa đã nghiệm thu.

Lệnh tái lập (dùng thư mục mới, runner cố ý từ chối ghi đè):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s rag/tests -v
.\.venv\Scripts\python.exe rag/compare_evidence.py --output-dir .temp/evidence_rerun
.\.venv\Scripts\python.exe rag/retrieval.py "Xét nghiệm nào giúp xác nhận chẩn đoán u xương ác tính?" --rerank-concepts
```

Kết quả phía dưới mô tả lịch sử vòng triển khai trước, được giữ để biết thay đổi nào đã xảy ra. Báo cáo Word **đã cập nhật bản 1.3**, Completion Note và Phụ lục E, xuất qua Word để kiểm tra bố cục **21 trang**. Truy vấn offline sau cùng xác nhận câu về chẩn đoán tìm được `nci-primary-bone-cancer:0014` khi thêm rerank; bộ lọc thử nghiệm trả thiếu bằng chứng cho thuật ngữ chưa biết. Không có tác vụ tải/đánh giá còn chạy.

Cập nhật ngày 27/10/2026 sau vòng sửa trích xuất, thử tìm kiếm kết hợp và đánh giá. Đây là điểm bàn giao cho AI hoặc kỹ sư tiếp tục công việc. Các thay đổi chưa commit từ phiên trước phải được giữ nguyên; mã nền nằm tại commit `59f4dfd`. Giai đoạn 11 chưa nghiệm thu, chưa triển khai chatbot.

## Điểm bắt đầu của phiên hiện tại

- Kho: 12 nguồn NCI, 489 đoạn; chỉ mục local E5 small 384 chiều.
- Baseline trên 12 câu cũ: source+section recall@5 = 0,60, MRR@5 = 0,417; hai câu ngoài phạm vi chưa được từ chối.
- `rag/build_index.py`, `rag/retrieval.py`, `rag/evaluate.py` đã có. Chưa có chatbot.

## Những việc đã thực hiện trong phiên này

1. Lưu baseline top-10 của corpus cũ tại `docs/reference/rag_baseline_20261027.json` trước khi sửa dữ liệu.
2. Sửa `rag/build_corpus.py`: nhận heading h5/h6 để loại References, chèn khoảng trắng ở block/ô bảng lồng nhau, giữ các mục danh sách ngắn như Pain và Swelling. Corpus hiện có **416 đoạn từ cùng 12 nguồn**, không phải 489 đoạn. ID đoạn của bản cũ có thể đổi; không dùng ID cũ để trỏ vào corpus mới.
3. Xây lại chỉ mục local, schema 2. Manifest kiểm tra cả tokenizer, pooling và cấu hình embedding, ngoài trọng số/model/corpus/vector; kiểm tra vector hữu hạn và chuẩn hóa L2.
4. Thêm `rag/lexical.py`: mở rộng từ khóa Việt–Anh theo cụm dài nhất, BM25 và reciprocal rank fusion. Cấu hình nằm ở `rag/data/retrieval_config.json`, trọng số original dense/expanded dense/BM25 = 2/1/1, hằng số RRF 60, cửa sổ 80. Đây là từ điển do AI soạn, không phải mô hình dịch hay nội dung y khoa đã thẩm định.
5. Thêm `rag/policy.py` để nhận diện một số yêu cầu liều điều trị, kết luận từ ảnh/model score, thay đổi chỉ dẫn, ngoài chủ đề và nhãn chưa đủ nguồn. Bộ quy tắc còn bỏ lọt câu có chủ đề u xương nhưng không có bằng chứng; không phải bộ bảo vệ đầy đủ cho chatbot.
6. CLI `rag/retrieval.py` mặc định dùng hybrid và routing; `--raw` bỏ qua routing, `--mode dense` dùng baseline. Python `search()` vẫn mặc định dense/raw để so sánh; `retrieve()` trả trạng thái và hit. `candidates_found` chỉ nghĩa là có ứng viên; **answer_ready luôn false**, chưa cho phép tự sinh kết luận.
7. Thêm `rag/data/evaluation_v2.json`: **28 câu**, tách dev/test trước lần đo (mỗi phần 8 câu có đáp án và 6 câu âm). Gold khóa bằng nguồn/mục/mã băm đoạn và trích đoạn ngắn. Tập do cùng AI soạn, chưa được chuyên gia độc lập rà soát. Phần test đã được chạy và xem kết quả trong phiên này; từ phiên sau không được coi nó là tập chưa từng thấy.
8. `rag/evaluate.py` lưu toàn bộ hit, gold rank, trạng thái, hash corpus/config/mã thực thi. `rag/compare.py` chạy các phép so sánh với một lần nạp model. Kết quả cuối ở `docs/reference/stage11_20261027/`; các file rời `rag_clean_dense_20261027.json` và `rag_hybrid_regression_20261027.json` là thử nghiệm trung gian trên corpus 415 đoạn, không phải bản cuối.

## Kết quả cuối của vòng này

| Bộ câu hỏi | Cách chạy | Recall@5 | MRR@5 | Không trả hit cho câu âm |
| --- | --- | --- | --- | --- |
| 12 câu cũ, corpus cũ | Dense trước sửa | 6/10 | 0,417 | 0/2 |
| 12 câu cũ, corpus 416 đoạn | Dense | 7/10 | 0,483 | 0/2 |
| 12 câu cũ, corpus 416 đoạn | Hybrid có routing | 8/10 | 0,700 | 2/2 |
| V2 dev | Dense | 5/8 | 0,542 | 0/6 |
| V2 dev | Hybrid có routing | 6/8 | 0,625 | 4/6 |
| V2 test | Dense | 6/8 | 0,542 | 0/6 |
| V2 test | Hybrid có routing | 7/8 | 0,713 | 4/6 |

Recall của bộ cũ xét đúng nguồn và mục; V2 yêu cầu đúng đoạn bằng chứng theo mã băm, nên không so trực tiếp hai thước đo. Không có câu có đáp án bị routing chặn trong bộ này. Kết quả mới là bằng chứng kỹ thuật ban đầu, không chứng minh khả năng tổng quát hay an toàn lâm sàng.

Kiểm thử RAG: **12/12 đạt**; bao gồm lỗi h6, từ ngắn bị mất, dữ liệu dính chữ, sai tokenizer, lọc nguồn, routing trước khi nạp model, và không tính hit chỉ vì cùng tên mục nhưng khác đoạn bằng chứng. Các bài kiểm thử ứng dụng cũ không được chạy lại trong vòng sửa RAG này.

## Ca trượt ghi nhận ở vòng hybrid trước

- Regression `q01`, `q02`: vẫn chưa tìm đúng nguồn/mục về nguyên phát so với di căn và xác nhận chẩn đoán.
- V2 dev `p01`, `p02`: thiếu bằng chứng đúng về lan tràn của u lành và các cách sinh thiết.
- V2 test `p13`: câu về bác sĩ giải phẫu bệnh và kính hiển vi ở chondrosarcoma; chỉ trả các đoạn định nghĩa trong top 5.
- V2 dev `n05`, `n06`: vẫn trả ứng viên cho nước ép cần tây và phí sinh thiết tại bệnh viện địa phương.
- V2 test `n11`, `n12`: vẫn trả ứng viên cho xét nghiệm DNA tại nhà bảo đảm phát hiện sớm và thực phẩm chức năng chữa khỏi chordoma. **Chưa có bộ kiểm tra đủ bằng chứng theo nội dung câu hỏi.**

## Hướng công việc ghi ở vòng trước

1. Đọc các hit và gold trong báo cáo cuối, phân biệt lỗi xếp hạng với thiếu nguồn. Giữ số liệu đã ghi; không đổi gold hoặc thêm cụm từ vào policy chỉ để che các ca test trượt.
2. Bổ sung nguồn chuyên biệt cho các nhãn còn thiếu, ghi quyền sử dụng và nguồn gốc, rồi rà soát chuyên môn. `osteochondroma` và `giant cell tumor` mới có nội dung rải rác; một lần nhắc tên không đủ coi là đã phủ nhãn.
3. Thử bước xếp hạng lại/evidence verification và xử lý câu mơ hồ. Chọn phương án dựa trên dev/regression; sau đó cần tập test mới do người hoặc AI độc lập soạn và chuyên gia rà soát. V2 test đã tiêu thụ.
4. Đặt tiêu chí nghiệm thu trước lần kiểm định mới, gồm tỷ lệ truy xuất đúng đoạn và từ chối câu không có nguồn. Chưa có threshold cosine được hiệu chỉnh; score giữ nguyên là cosine của câu hỏi gốc, ranking_score là RRF, không chuyển đổi thành xác suất.
5. Sau khi corpus đổi, rà soát và gắn lại evidence trong evaluation_v2; công cụ cố ý báo lỗi nếu hash corpus/gold cũ. Sau khi model/tokenizer hoặc format index đổi, xây lại index. Chỉ sang nghiệm thu chatbot khi retrieval và kiểm tra đủ bằng chứng được xác minh.

## Lệnh tái lập

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s rag/tests -v
.\.venv\Scripts\python.exe rag/build_index.py
.\.venv\Scripts\python.exe rag/compare.py --output-dir .temp/stage11_rerun
.\.venv\Scripts\python.exe rag/retrieval.py "Ewing sarcoma di căn thường lan đến đâu?"
```

Đối chiếu `.temp/stage11_rerun/summary.json` với `docs/reference/stage11_20261027/summary.json`; không ghi đè bằng chứng cũ. Chỉ dùng `--download-model` nếu máy chưa có model. Model/cache/index không được Git theo dõi; corpus, config, bộ câu hỏi và báo cáo JSON có thể dùng để tái dựng. Mã băm corpus cuối: `176311a556429af4fb3b2c2e327851b957463a1e57300fc9df973182a0a8a035`.

## Khi tiếp quản

Đọc file này trước, sau đó `PROJECT_STATUS_VI.md` và `guides/README_RAG_INDEX_VI.md`. Kiểm tra `git status` và đọc code thay đổi trước khi sửa. Chạy kiểm thử RAG bằng `.\.venv\Scripts\python.exe -m unittest discover -s rag/tests -v`. Không đánh dấu giai đoạn 11 hoàn thành chỉ vì chỉ mục hoặc lệnh chạy thành công.

## Kiểm tra trước khi kết thúc vòng hybrid trước

- Truy vấn offline sau cùng: câu Ewing di căn trả `nci-ewing-patient:0017` kèm URL; yêu cầu liều hóa trị trả `out_of_scope`, không có hit. Không có lệnh tải hoặc đánh giá còn đang chạy.
- Liên kết Markdown trong docs và README đã được kiểm tra; `git diff --check` đạt.
- `docs/reports/Bao_cao_tien_do.docx` đã cập nhật bản **1.2**, Completion Note giai đoạn 10–11 và phụ lục D; đã xuất qua Word và kiểm tra bố cục **20 trang**. File PDF/PNG trong `.temp` chỉ phục vụ kiểm tra, không phải đầu ra cần bàn giao.
- Điểm tiếp tục cụ thể: **đánh giá phương án xếp hạng lại và kiểm tra đủ bằng chứng**, sau đó bổ sung nguồn và dùng tập kiểm định độc lập mới. Không được coi `candidates_found` là đủ điều kiện sinh câu trả lời.
