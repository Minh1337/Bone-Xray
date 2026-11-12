# Báo cáo tổng kết đồ án BoneScope

**Tên đề tài:** Xây dựng nguyên mẫu học tập kết hợp phân loại ảnh X-quang u xương, truy xuất tài liệu và chatbot đa lượt  
**Phiên bản báo cáo:** 12/11/2026 · **Phạm vi:** học tập và nghiên cứu thực nghiệm cục bộ  
**Trạng thái dữ liệu kiểm chứng:** theo record workspace ngày 12/11/2026

> **Phạm vi sử dụng:** BoneScope là nguyên mẫu học tập, không cung cấp cho bác sĩ hoặc người bệnh. Mô hình không được dùng để chẩn đoán, sàng lọc, phân loại nguy cơ hay quyết định điều trị. Điểm softmax không phải xác suất bệnh. Kết quả trong báo cáo là thực nghiệm nội nguồn, benchmark phát triển/hồi quy và kiểm tra kỹ thuật; chưa phải đánh giá độc lập hoặc bằng chứng hiệu lực lâm sàng.

## Tóm tắt điều hành

BoneScope kết hợp bốn luồng: phân loại ảnh X-quang bằng Swin Transformer có đầu vào 22 trường metadata; kho tài liệu xương dùng hybrid retrieval; chatbot hội thoại đa chủ đề; và lịch sử chat cục bộ bằng SQLite. Ảnh trong hội thoại được giữ tạm trong bộ nhớ tab để hỏi nối tiếp, không ghi byte ảnh vào SQLite. Luồng phân loại ảnh chạy cục bộ. Luồng chatbot có thể gửi câu chữ hoặc ảnh người dùng chọn tới nhà cung cấp AI bên ngoài theo cấu hình; vì vậy chỉ dùng dữ liệu được phép và không tải ảnh bệnh nhân thật lên dịch vụ.

Thực nghiệm phân tầng trên 250 ảnh BTXRD cho Top-1 0,776 khi có đủ metadata và 0,480 khi vector metadata bị xóa. Macro-F1 tương ứng là 0,776 và 0,439. Kết quả minh họa mức phụ thuộc của checkpoint vào metadata và được trình bày là đánh giá **in-source**: checkpoint đã được huấn luyện trên BTXRD, còn danh sách ID train/validation/test gốc không có để tách một tập kiểm định độc lập.

Kho RAG hiện có 22 nguồn, 794 đoạn và index 794 × 384 chiều. Audit provenance đạt PASS; replay 16/16 báo cáo khớp. Các tập truy vấn là bộ phát triển/hồi quy đã xem hoặc do agent soạn, nên các chỉ số retrieval mô tả hành vi trong mẫu, không phải ước lượng hiệu năng ngoài mẫu. Ứng dụng giữ `answer_ready=false`.

Regression trong sandbox đạt 213 bài và 227 subtests. Một bài kiểm thử Chrome bị bỏ qua trong sandbox và đạt khi chạy riêng ngoài sandbox với ảnh tổng hợp và AI giả lập. Bản ghi đối chiếu API trước đó đạt 3/3 ca tham chiếu với chênh lệch điểm bằng 0 và hash model khớp.

### Trạng thái hoàn thiện theo phạm vi đồ án

| Sản phẩm bàn giao | Trạng thái theo bằng chứng hiện có | Phạm vi kết luận |
|---|---|---|
| Nguyên mẫu local gồm chatbot, retrieval, luồng ảnh và lịch sử | Các luồng chính có trong mã; record kỹ thuật và smoke trước đây được lưu trong dự án | Đủ để trình diễn có giám sát trong phạm vi học tập; không xác nhận chất lượng y khoa |
| Báo cáo tổng kết và hướng dẫn chạy | Bản Markdown này đã cập nhật theo record 12/11; có hướng dẫn chạy và tái lập | DOCX đã xuất từ cùng nội dung; chưa kiểm tra hình ảnh từng trang vì máy không có LibreOffice và Word automation không khởi chạy được |
| Đánh giá mô hình ảnh | Có đánh giá in-source 250 ảnh và metadata ablation | Không phải holdout hoặc external validation |
| Đánh giá RAG | Có bộ dev/regression, audit provenance và replay | Chưa có nhãn độc lập hoặc đánh giá entailment |
| Acceptance gate G1–G7 | 7 OPEN, 0 CLOSED | Nằm ngoài mức nghiệm thu của bản demo học tập hiện tại |

Không quy đổi các dòng này thành một tỷ lệ hoàn thành chung. “Sẵn sàng trình diễn cục bộ” chỉ mô tả khả năng trình bày nguyên mẫu theo giới hạn nêu trên.

## 1 Mục tiêu và phạm vi

### Mục tiêu học tập

| Mục tiêu | Kết quả trong nguyên mẫu |
|---|---|
| Kết hợp ảnh X-quang với metadata | Pipeline Swin + MetadataMLP + Cross-Attention, 10 nhãn cấp ảnh |
| Tạo kho kiến thức có thể truy vết | Corpus text-only có source metadata, hash, index phiên bản và replay |
| Cho phép hỏi đáp nhiều lượt | Chat chữ, chế độ tra cứu tài liệu, chat ảnh tạm theo cuộc trò chuyện |
| Lưu hội thoại và mở lại | SQLite lưu văn bản và thông tin nguồn được phép; không lưu byte ảnh |
| Nêu rõ giới hạn và tái lập kết quả | Báo cáo tách metric nội nguồn khỏi kiểm định độc lập; có audit/replay và record kỹ thuật |

### Ngoài phạm vi

- Không phải thiết bị y tế, dịch vụ tư vấn hay hệ thống hỗ trợ quyết định cho bác sĩ.
- Không đưa ra chẩn đoán, hướng dẫn điều trị, tiên lượng hoặc khuyến nghị cho bệnh nhân.
- Không tuyên bố mô hình đã được kiểm định trên bệnh nhân hoặc ảnh ngoài BTXRD.
- Không công bố ảnh, dữ liệu gốc, thông tin định danh hoặc thông tin xác thực API.
- Không coi tài liệu RAG liên quan là bằng chứng xác nhận một dấu hiệu trên ảnh.

Phạm vi học tập do người dùng nêu được ghi trong [bản ghi phạm vi](../reference/STAGE11_USER_STATED_EDUCATIONAL_SCOPE_20261029.md). Bản intended-use theo từng chức năng chưa được khóa; các giới hạn đó vẫn cần xuất hiện trong giao diện và báo cáo.

## 2 Kiến trúc hệ thống

| Thành phần | Xử lý | Đầu ra | Lưu ý |
|---|---|---|---|
| API phân loại ảnh | Ảnh + đúng 22 trường metadata qua checkpoint Swin và nhánh metadata | Top-3 nhãn, điểm softmax, mã ca | Chạy cục bộ; cần đủ metadata; điểm không phải xác suất bệnh |
| Ghép metadata BTXRD | So khớp SHA-256 của byte ảnh với manifest | Metadata chỉ khi khớp duy nhất và không mâu thuẫn | Không suy metadata từ tên file hoặc nội dung ảnh |
| RAG | BM25 kết hợp embedding E5-small trên corpus có provenance | Các đoạn ứng viên, nguồn, hoặc trạng thái từ chối | Kết quả passage là ứng viên truy xuất; chưa có đánh giá entailment độc lập |
| Chatbot chữ | Lịch sử gần đây, định tuyến câu hỏi, gọi provider theo cấu hình | Câu trả lời và nguồn khi dùng RAG | Free endpoint có thể bị giới hạn; Qwen dự phòng có thể phát sinh phí nếu được cấu hình |
| Chatbot ảnh | Ảnh người dùng chọn và lịch sử gần đây gửi tới vision provider | Mô tả quan sát và gợi ý nguồn đọc thêm | Ảnh giữ tạm trong tab; provider bên ngoài có thể nhận ảnh |
| Lịch sử SQLite | Văn bản câu hỏi/trả lời và trường nguồn được cho phép | Mở lại, đổi tên và xóa hội thoại | Không lưu byte ảnh; mở lại lịch sử cần đính kèm ảnh lại |

Chi tiết vận hành và hành vi hội thoại nằm trong [hướng dẫn chatbot](../guides/CHATBOT_CONVERSATION_VI.md), [hướng dẫn provider](../guides/OPENROUTER_CHATBOT_SETUP_VI.md) và [README tiếng Việt](../../README_VI.md).

## 3 Dữ liệu và nguồn gốc

### Bộ ảnh BTXRD

Bài báo giới thiệu BTXRD mô tả bộ dữ liệu đa trung tâm gồm 3.746 ảnh xương, nhãn toàn cục/thông tin lâm sàng và annotation vùng u [1]. Catalogue cục bộ được báo cáo gồm **3.746 ảnh**, với **3.725 hash SHA-256 duy nhất**. Có 21 nhóm ảnh trùng byte; 9 nhóm được ghi nhận metadata mâu thuẫn và bị chặn tự điền. Phân bố trung tâm là Center 1/2/3 = 2.938/549/259. Các lớp mất cân bằng; `no-tumor` chiếm khoảng 50,2%, trong khi `osteofibroma` khoảng 1,2%.

Checkpoint `model/best_model.pt` được huấn luyện trên BTXRD. Hồ sơ tiền xử lý ghi `n_samples_seen_ = 2.616`, nhưng checkpoint không giữ danh sách ID từng ảnh của các tập huấn luyện, validation và test. BTXRD công khai cũng không cung cấp patient ID đủ để tái lập chắc chắn split theo bệnh nhân của checkpoint. Vì vậy 250 ảnh đánh giá trong báo cáo không được gọi là holdout hoặc external test.

Trang bài báo ghi giấy phép CC BY-NC-ND 4.0 cho **bài báo** và lưu ý tài liệu bên thứ ba có thể có điều kiện riêng [1]. Đây không phải bằng chứng đủ để kết luận quyền tái sử dụng từng tệp ảnh trong archive; quyền ở cấp ảnh, nguồn gốc patient-level và overlap với dữ liệu huấn luyện chưa được xác minh đầy đủ. Báo cáo không phân phối lại ảnh hoặc archive dữ liệu. Trạng thái này cần được giải quyết trước khi chia sẻ dataset, phát hành demo có ảnh hoặc tuyên bố kết quả trên cohort độc lập. Xem [phân tích catalogue và mapping](../reference/stage12_btxrd_catalogue_and_mapping_analysis_20261105.json) và [sổ cổng G4](../reference/stage11_external_cohort_screening_register_20261029.csv).

### Kho văn bản

Corpus hiện tại có 22 nguồn và 794 chunks, vector index 794 × 384 dùng `intfloat/multilingual-e5-small`; báo cáo kỹ thuật E5 mô tả các biến thể multilingual embedding small/base/large và cách huấn luyện [3]. Source registry giữ URL, metadata nguồn, phạm vi license và hash. Corpus hiện chỉ chứa văn bản; audit nguồn không xác nhận đoạn văn có đủ căn cứ cho một claim cụ thể.

Record kỹ thuật 12/11 cho biết không thiếu cache nguồn, 10 bộ evaluation được kiểm tra, 16 report replay được đối chiếu và không có mismatch. Xem [record xác minh workspace](../reference/project_verification_20261112.json), [audit](../reference/stage11_integrity_audit_20261110_completion.json) và [replay](../reference/stage11_replay_20261110_completion.json).

## 4 Phương pháp thực nghiệm ảnh

### Mô hình và đầu vào

Mô hình kết hợp Swin Transformer cho ảnh, `MetadataMLP` cho 22 trường và Cross-Attention để hợp nhất đặc trưng; đầu ra gồm 10 nhãn cấp ảnh. Swin là backbone thị giác phân cấp dùng shifted windows, được giới thiệu cho phân loại và các tác vụ thị giác khác [2]. Hợp đồng metadata yêu cầu đủ trường theo schema, có ít nhất một vị trí giải phẫu và đúng một tư thế trong các giá trị được hỗ trợ. API giới hạn kích thước/định dạng ảnh và từ chối metadata thiếu hoặc ảnh hỏng.

Metadata chỉ tự điền khi hash byte ảnh khớp chính xác với một bản ghi BTXRD duy nhất và không mâu thuẫn. Với ảnh ngoài tập, hệ thống không đoán metadata từ tên file, không gán 0 cho trường chưa biết và chuyển sang luồng mô tả ảnh nếu người dùng chọn.

### Thiết kế đánh giá

Mẫu gồm 250 ảnh, 25 ảnh mỗi nhãn trong 10 nhãn, được lấy với seed `20261031`. Chạy hai điều kiện: metadata thật và vector metadata được đặt bằng 0. Đây là thí nghiệm nội nguồn/ablation trên bộ liên quan tới huấn luyện checkpoint; không đánh giá tổng quát hóa sang bệnh viện, thiết bị, dân số hoặc cohort ngoài.

Top-1 và Top-3 đo tỷ lệ nhãn thật nằm trong một hoặc ba dự đoán đầu. Macro-F1 lấy trung bình F1 theo lớp để các lớp có trọng số bằng nhau. ECE 10-bin, MCE, Brier và NLL mô tả độ phù hợp giữa điểm softmax và kết quả quan sát trong mẫu; chúng không hiệu chuẩn xác suất lâm sàng.

## 5 Kết quả mô hình ảnh

### Kết quả tổng thể

| Điều kiện | Top-1 | Top-3 | Macro-F1 | Ghi chú |
|---|---:|---:|---:|---|
| Có đủ 22 metadata | 0,776 (194/250) | 0,940 (235/250) | 0,776 | Điều kiện tham chiếu |
| Vector metadata bằng 0 | 0,480 (120/250) | 0,720 (180/250) | 0,439 | Ablation, không phải cách xử lý metadata thiếu được khuyến nghị |
| Chênh lệch | −0,296 | −0,220 | −0,337 | 91/250 dự đoán Top-1 thay đổi |

Khi metadata bị xóa, `no-tumor` và `synovial osteochondroma` có recall 0 trong mẫu. Kết quả này hỗ trợ quyết định kỹ thuật yêu cầu metadata đầy đủ cho classifier; không chứng minh classifier có hiệu lực chẩn đoán.

### Hiệu chuẩn và nhóm con

| Chỉ số | 22 metadata | Metadata bằng 0 |
|---|---:|---:|
| Top-1 accuracy | 0,7760 | 0,4800 |
| Điểm softmax Top-1 trung bình | 0,7892 | 0,6875 |
| ECE 10-bin | 0,0367 | 0,2075 |
| MCE 10-bin | 0,0671 | 0,3461 |
| Brier score | 0,3334 | 0,7616 |
| NLL | 0,7295 | 2,7223 |

Ở điều kiện metadata bằng 0, điểm softmax trung bình vẫn 0,6875 dù Top-1 accuracy chỉ 0,4800. Trong bin confidence `(0.9, 1.0]`, confidence trung bình đạt 0,9668 nhưng accuracy quan sát là 0,6207. Do đó UI hiển thị điểm là **điểm tương đối chưa hiệu chuẩn**, không phải xác suất mắc bệnh.

Kết quả theo trung tâm cũng khác biệt: Center 1 đạt Top-1 0,8208, Center 2 đạt 0,6923 và Center 3 đạt 0,6579 trong mẫu. Center 1 chiếm phần lớn catalogue gốc; sample theo trung tâm không đủ để giải thích nguyên nhân hoặc khẳng định hiệu năng giữa các cơ sở.

### Kết quả theo lớp

| Nhãn | Precision | Recall | F1 |
|---|---:|---:|---:|
| `no-tumor` | 1,000 | 1,000 | 1,000 |
| `synovial osteochondroma` | 1,000 | 0,920 | 0,958 |
| `multiple osteochondromas` | 0,889 | 0,960 | 0,923 |
| `osteosarcoma` | 0,909 | 0,800 | 0,851 |
| `simple bone cyst` | 0,724 | 0,840 | 0,778 |
| `giant cell tumor` | 0,850 | 0,680 | 0,756 |
| `other mt` | 0,750 | 0,600 | 0,667 |
| `osteochondroma` | 0,500 | 0,960 | 0,658 |
| `osteofibroma` | 0,857 | 0,480 | 0,615 |
| `other bt` | 0,591 | 0,520 | 0,553 |

Mỗi lớp có support 25. Các ước lượng theo lớp vì vậy có độ bất định cao, đặc biệt với lớp hiếm hoặc nhãn gộp. Không diễn giải chúng như xác suất chất lượng trên quần thể triển khai.

Nguồn số liệu: [đánh giá in-source](../reference/stage11_xray_in_source_evaluation_20261103.json), [calibration và subgroup](../reference/stage12_xray_subgroup_and_calibration_20261106.json), [phân tích catalogue](../reference/stage12_btxrd_catalogue_and_mapping_analysis_20261105.json).

## 6 Kết quả truy xuất tài liệu

### Thiết kế

RAG kết hợp BM25 và dense retrieval trên embedding E5-small. Đây là thiết kế triển khai của BoneScope; nghiên cứu nền tảng RAG mô tả việc kết hợp bộ nhớ tham số của mô hình với bộ nhớ phi tham số có thể truy xuất, nhưng không xác nhận chất lượng của pipeline này [3, 4]. Các đoạn giữ source ID và metadata để UI hiển thị nguồn. Routing nhận diện một số chủ đề, phân biệt câu hỏi trong phạm vi và một số câu hỏi ngoài phạm vi; khi không có bằng chứng phù hợp, API có thể trả `insufficient_evidence` hoặc `out_of_scope`.

### Bộ phát triển và kết quả đã ghi

| Bộ đánh giá | Cỡ mẫu | Kết quả được ghi | Giới hạn |
|---|---:|---|---|
| Expansion dev | 25 câu | Recall@5 1,000; MRR@5 0,689; câu âm từ chối 3/3 | Đã dùng trong phát triển/tuning |
| Stress song ngữ | 20 câu | Exact-gold Recall@5 8/10; MRR 0,633; câu âm từ chối 10/10 | Bộ đã xem; hai miss có candidate liên quan |
| OFD dev | 7 câu | Recall@5 5/5; MRR 0,70 | Câu hỏi được tạo sau khi ingest nguồn liên quan |
| Replay hiện hành | 16 report | 16/16 khớp, không mismatch | Kiểm tra tái lập, không phải đánh giá mới |

> **Giới hạn ngưỡng:** thăm dò trên 28 câu đã xem cho thấy cosine của nhóm dương và âm chồng lấn. Không có một ngưỡng dense đơn nào tách hoàn toàn hai nhóm trong bộ này. Không cài một ngưỡng mặc định dựa trên mẫu đã xem; công cụ hiệu chỉnh chờ nhãn phù hợp. Strict lexical verifier cũng để ở chế độ opt-in vì có thể chặn câu dương. Coverage từ vựng không chứng minh entailment.

Hệ thống hiện hiển thị các passage có liên quan làm nguồn đọc thêm. Chưa có người chấm độc lập cho relevance, direct support, polarity, qualifiers và context; chưa có đánh giá entailment của câu trả lời sinh. RAG score không được gọi là độ chính xác chatbot.

## 7 Chatbot, hội thoại và lưu trữ

### Luồng hội thoại

Chatbot hỗ trợ hội thoại đa chủ đề; khi hỏi về xương, có thể truy xuất kho nguồn và trả citations. Chế độ chỉ tra cứu giới hạn đầu ra theo passages. Chat ảnh cho phép câu hỏi tiếp nối trong cùng cuộc trò chuyện bằng cách giữ ảnh tạm trong tab; chọn xóa ngữ cảnh, đóng tab hoặc tải lại sẽ bỏ ảnh khỏi bộ nhớ trình duyệt. Mở lại lịch sử không khôi phục ảnh, nên cần đính kèm lại.

### Lịch sử và dữ liệu gửi tới provider

SQLite lưu văn bản hội thoại và các trường nguồn được cho phép; không lưu byte ảnh. Lịch sử hỗ trợ mở lại, đổi tên và xóa. Ảnh chat được gửi tới vision provider đã cấu hình khi người dùng yêu cầu phân tích ảnh; ảnh không được lưu vào database lịch sử nhưng việc gửi tới provider vẫn là truyền dữ liệu ra ngoài máy. Vì vậy chỉ sử dụng ảnh có quyền gửi và không dùng dữ liệu bệnh nhân hoặc ảnh định danh.

Ở luồng classifier, ảnh và metadata được xử lý cục bộ; chatbot có thể nhận Top-3 và điểm số dạng tối thiểu trong phần giải thích ca, theo luồng ứng dụng. Cách xử lý này không thay thế kiểm tra data-flow của từng cấu hình triển khai.

### Model provider và chi phí

Ứng dụng hỗ trợ OpenRouter Free làm tuyến ưu tiên và Qwen làm fallback trả phí theo cấu hình; Groq là tùy chọn. Model Free có thể giới hạn tốc độ hoặc ngừng khả dụng. Việc gửi ảnh có thể phát sinh chi phí tùy model/provider. Người vận hành cần đọc cấu hình `.env`, không chia sẻ API key và theo dõi usage trước khi chạy với dữ liệu thật. Report không ghi key hoặc chi phí dự kiến.

Các smoke provider được ghi từ ngày 09/11 dùng câu thử ngắn và ảnh hình học tổng hợp; chúng xác nhận kết nối/chuyển tuyến, không đánh giá chất lượng mô tả X-quang. Xem [record provider smoke](../reference/chatbot_provider_smoke_20261109.json).

## 8 Kiểm chứng phần mềm hiện hành

Các kết quả sau được trích từ [record 12/11](../reference/project_verification_20261112.json). Chúng là bằng chứng kỹ thuật trên workspace đã ghi, không phải tuyên bố rằng toàn bộ lệnh đã được chạy lại trong phiên lập báo cáo này.

| Hạng mục | Kết quả | Diễn giải |
|---|---|---|
| Regression offline | 213 passed, 0 failed, 1 skipped; 227 subtests passed | Một Starlette deprecation warning |
| Browser smoke hiện hành | PASS 1/1 khi chạy riêng ngoài sandbox | Chrome 157, SQLite tạm, ảnh tổng hợp và AI giả lập. Lần chạy trong sandbox bị skip trước điều hướng |
| RAG audit | PASS, 22 nguồn, 794 chunks, 0 cache thiếu, 10 bộ evaluation | Kiểm tra provenance và cấu trúc |
| RAG replay | PASS, 16/16, 0 mismatch | Tái lập report đã lưu |
| Chatbot doctor | PASS, 13/13 | Kiểm tra cấu hình cục bộ, không gọi provider |
| API local parity | PASS, 3/3 ca tham chiếu, max score delta 0 | Hash model khớp; metadata thiếu và ảnh hỏng bị từ chối |
| Register Stage 11 | PASS cấu trúc; 24 tham chiếu, 15 cohort rows | 7 gate vẫn OPEN |
| Markdown links | PASS, 954 link trong 54 file, 0 hỏng | Liên kết trong snapshot được kiểm tra |
| Provider calls trong record | Không có | Các kiểm tra kỹ thuật trên không tiêu token API |
| Precheck nghiệm thu local | Chạy lại sau khi sửa DOCX exporter: 213 passed, 0 failed, 1 skipped; chatbot doctor 13/13; exporter tests 2/2 | Xem [record precheck nghiệm thu](../reference/project_acceptance_precheck_20261112.json) |
| DOCX render | Chưa render được | LibreOffice không có trong môi trường; cấu trúc đã đọc được nhưng bố cục từng trang chưa kiểm tra trực quan |

Workspace có thay đổi chưa commit; record ghi HEAD `a35e60e9c6682cec097b7e81103b4c5b61b62efe` và ba hash implementation liên quan. Khi chạy lại, tạo record mới để giữ lịch sử; không ghi đè evidence trước.

## 9 Hạn chế và rủi ro cần công khai

1. **Không có đánh giá ảnh độc lập.** Checkpoint thiếu ID split gốc; BTXRD có overlap với dữ liệu huấn luyện. Kết quả 250 ảnh là in-source.
2. **Metadata quyết định mạnh tới đầu ra.** Ablation làm giảm Top-1 gần 30 điểm phần trăm và có lớp recall bằng 0. Ảnh thiếu metadata không được đưa vào classifier bằng cách tự điền giá trị.
3. **Điểm softmax có thể tự tin khi sai.** Không gọi điểm số là xác suất bệnh và không dùng làm ngưỡng điều trị.
4. **Vision model có thể mô tả sai giải phẫu hoặc bỏ sót.** Câu trả lời là bản nháp quan sát bằng AI; tài liệu đọc thêm không xác minh mô tả trên ảnh.
5. **RAG chưa được chấm độc lập.** Các bộ hiện có đã xem; retrieval candidate không tương đương passage support hay entailment.
6. **Quyền dữ liệu còn giới hạn.** Không có hồ sơ đầy đủ về quyền ở cấp ảnh và audit overlap cho cohort độc lập. Không phát hành ảnh, archive hoặc kết luận dựa trên cohort như kiểm định bên ngoài.
7. **Chưa có phê duyệt cho triển khai.** Cấu hình local demo không phải đánh giá bảo mật/privacy cho VPS hoặc mạng công khai.
8. **Các acceptance gate chưa đóng.** Sổ G1–G7 ghi 7 OPEN, 0 CLOSED; `answer_ready=false`. Báo cáo học tập không tự đóng các cổng này.

## 10 Kết luận

BoneScope hiện là nguyên mẫu học tập có thể trình diễn cục bộ với classifier, retrieval có nguồn, chatbot đa lượt, hội thoại ảnh tạm và lưu lịch sử văn bản. Các kiểm tra kỹ thuật ghi nhận trong workspace hỗ trợ việc tái lập một số luồng và đối chiếu model/API. Thí nghiệm metadata cho thấy đầu ra classifier phụ thuộc mạnh vào metadata, còn bộ retrieval hiện tại chưa đủ để chọn ngưỡng tin cậy chung.

Kết quả phù hợp để báo cáo về thiết kế phần mềm và thực nghiệm nội nguồn. Chúng không chứng minh hiệu quả chẩn đoán, độ an toàn, khả năng tổng quát hóa hoặc tính phù hợp để sử dụng lâm sàng. Trước khi demo, chỉ dùng dữ liệu được phép; không tải ảnh bệnh nhân thật lên provider; giữ service trên `127.0.0.1`; công khai các giới hạn trên khi trình bày.

**Kết luận nghiệm thu:** báo cáo này chốt trạng thái của nguyên mẫu học tập theo bằng chứng hiện có. Đây không phải tuyên bố toàn bộ Giai đoạn 11 đã nghiệm thu: 7 gate G1–G7 vẫn OPEN, không có bộ nhãn độc lập hoặc cohort ảnh ngoài đủ quyền trong hồ sơ hiện hành.

## 11 Hướng dẫn chạy và tái lập

### Chạy chatbot local

Trong thư mục gốc dự án, dùng môi trường `.venv` đã cài dependency:

```powershell
.\.venv\Scripts\python.exe -m tools.run_chatbot
```

Hoặc chạy cấu hình VS Code **BoneScope: Chatbot tra cứu tài liệu** bằng F5. Giao diện local thường ở `http://127.0.0.1:8765`. Không bind ra mạng công khai. Cấu hình provider/API key xem [hướng dẫn OpenRouter](../guides/OPENROUTER_CHATBOT_SETUP_VI.md). Không ghi API key vào báo cáo hoặc Git.

### Lệnh kiểm tra khi cần tái lập

```powershell
.\.venv\Scripts\python.exe -m tools.chatbot_doctor
.\.venv\Scripts\python.exe -m rag.audit --output docs/reference/stage11_integrity_audit_YYYYMMDD.json
.\.venv\Scripts\python.exe -m rag.replay_reports --output docs/reference/stage11_replay_YYYYMMDD.json
.\.venv\Scripts\python.exe -m tools.verify_stage11_registers
```

Record lịch sử và hướng dẫn đầy đủ nằm trong [bàn giao tiếp quản](../../START_HERE_NEXT_CODEX_VI.md). Các lệnh tái lập regression có trong README; khi chạy chúng sẽ dùng thời gian máy và trạng thái dependency hiện tại.

## 12 Tài liệu và artifact tham chiếu

- [Checklist nghiệm thu demo học tập](PRODUCT_ACCEPTANCE_CHECKLIST_VI.md)
- [Record xác minh tổng hợp 12/11/2026](../reference/project_verification_20261112.json)
- [Record precheck nghiệm thu local 12/11/2026](../reference/project_acceptance_precheck_20261112.json)
- [Rà soát cấu trúc sau refactor](../reference/project_structure_review_20261111.json)
- [Phân tích BTXRD và ánh xạ nhãn](../reference/stage12_btxrd_catalogue_and_mapping_analysis_20261105.json)
- [Đánh giá checkpoint trên 250 ảnh](../reference/stage11_xray_in_source_evaluation_20261103.json)
- [Calibration và subgroup](../reference/stage12_xray_subgroup_and_calibration_20261106.json)
- [Audit và replay RAG 12/11](../reference/stage11_integrity_audit_20261110_completion.json), [replay](../reference/stage11_replay_20261110_completion.json)
- [Sổ nghiệm thu G1–G7](../reference/stage11_acceptance_gate_status_20261029.csv) và [blocker theo từng gate](../reference/STAGE11_GATE_CLOSURE_BLOCKERS_VI.md)
- [Báo cáo review nội bộ AI-only ngày 12/11](STAGE11_AI_INTERNAL_GATE_REVIEW_20261112_VI.md)

## 13 Tài liệu nghiên cứu và nguồn kỹ thuật

1. Yao, S. et al. (2025). “A Radiograph Dataset for the Classification, Localization, and Segmentation of Primary Bone Tumors.” *Scientific Data*, 12, 88. [Bài báo và mô tả dataset BTXRD](https://pmc.ncbi.nlm.nih.gov/articles/PMC11739492/). DOI dataset được bài báo dẫn: [10.6084/m9.figshare.27865398](https://doi.org/10.6084/m9.figshare.27865398). Giấy phép hiển thị trên trang bài báo là CC BY-NC-ND 4.0 cho bài báo; cần kiểm tra riêng điều kiện của archive và nguồn từng ảnh trước khi tái sử dụng.
2. Liu, Z. et al. (2021). “Swin Transformer: Hierarchical Vision Transformer using Shifted Windows.” *Proceedings of ICCV 2021*. [Bản bài báo trên arXiv](https://arxiv.org/abs/2103.14030). DOI hội nghị: 10.1109/ICCV48922.2021.00986.
3. Wang, L. et al. (2024). “Multilingual E5 Text Embeddings: A Technical Report.” [arXiv:2402.05672](https://arxiv.org/abs/2402.05672).
4. Lewis, P. et al. (2020). “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.” *Advances in Neural Information Processing Systems 33*. [Bài báo NeurIPS](https://proceedings.neurips.cc/paper/2020/hash/6b493230-Abstract.html).

## 14 Việc còn lại và điều kiện hoàn tất

Các mục dưới đây là điều kiện chưa được chứng minh trong workspace. Chúng không được thay bằng cách ghi “đã xong” trong báo cáo hoặc bằng review tự động của chính hệ thống.

| Ưu tiên | Việc còn lại | Điều kiện để ghi nhận hoàn tất | Trạng thái hiện tại |
|---|---|---|---|
| P0 | Xác định xử lý câu hỏi yếu/ngoài phạm vi cho retrieval | Thu thập tập câu hỏi đã khóa, nhãn phù hợp và đánh giá trên dữ liệu chưa dùng để chọn policy; nếu chưa có thì giữ routing hiện hành, không đặt một cosine threshold chung | Đã xác định điểm dương/âm chồng lấn trong 28 truy vấn đã xem; bước hiệu chỉnh `AWAITING_LABELS` |
| P0 | Đánh giá độc lập classifier ảnh | Có cohort được phép dùng, manifest ảnh/patient-level, reference standard và audit overlap với train/pretraining; định nghĩa split trước khi chạy | Chưa có; kết quả 250 ảnh hiện tại là in-source |
| P0 | Xác nhận quyền dataset/ảnh BTXRD | Đối chiếu điều kiện archive Figshare, nguồn upstream, attribution và quyền ở cấp từng ảnh; lưu hồ sơ quyết định | Chưa đủ bằng chứng; không phát hành archive/ảnh |
| P1 | Kiểm tra giao diện trên máy trình diễn | Chạy các bước nghiệm thu trực tiếp với cấu hình dự kiến | Browser smoke đạt ngoài sandbox với ảnh tổng hợp và AI giả lập. Buổi nghiệm thu trực tiếp đang chờ người nghiệm thu |
| P1 | Đánh giá privacy/security theo cách chạy thực tế | Chốt data flow local/provider, cấu hình bind, retention, log, backup, deletion và quyền truy cập; kiểm tra trên môi trường demo dự kiến | Chỉ có rà soát code và checklist; chưa có phê duyệt triển khai |
| P1 | Chấm độc lập hỗ trợ nguồn RAG | Reviewer đánh giá relevance, direct support, polarity, qualifiers và context theo protocol; ghi bất đồng/adjudication | Chưa có nhãn độc lập; audit/replay hiện chỉ xác minh provenance và tái lập |
| P2 | Quyết định G1–G7 | Owner khóa intended use/tiêu chí; từng gate nhận đúng bằng chứng và quyết định của vai trò có thẩm quyền theo register | 7 gate OPEN, 0 CLOSED; AI review chỉ là rà soát nội bộ |

**Mốc dùng được hiện tại:** nguyên mẫu local phù hợp để trình diễn học tập có giới hạn và trình bày các thí nghiệm đã ghi. Checklist kỹ thuật hẹp của Giai đoạn 11 đạt 6/7 mục (xấp xỉ 86% độ bao phủ checklist), nhưng mục cuối chờ nhãn; đây không phải tỷ lệ hoàn thành toàn dự án. Không có cơ sở tính một phần trăm “100%” chung khi chưa thống nhất mẫu số và tiêu chí. Những mục P0 ở trên ngăn việc tuyên bố đã có đánh giá độc lập hoặc hiệu năng tổng quát; chúng không ngăn việc trình bày nguyên mẫu đúng phạm vi học tập.
