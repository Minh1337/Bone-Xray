# Điểm tiếp tục giai đoạn 11

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
