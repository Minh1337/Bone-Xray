# Báo cáo đồ án BoneScope về phân loại ảnh X quang và tra cứu tài liệu u xương

**Phiên bản báo cáo:** 13/11/2026 · **Mã nguồn được rà soát:** `ac3ac770`

**Phạm vi:** học tập và nghiên cứu thực nghiệm cục bộ · **Kho mã:** [BoneScope trên GitHub](https://github.com/Minh1337/Bone-Xray)

**Phạm vi sử dụng.** BoneScope là nguyên mẫu học tập, không cung cấp cho bác sĩ hoặc người bệnh. Mô hình không được dùng để chẩn đoán, sàng lọc, phân loại nguy cơ hay quyết định điều trị. Điểm softmax không phải xác suất bệnh. Kết quả trong báo cáo là thực nghiệm nội nguồn, benchmark phát triển/hồi quy và kiểm tra kỹ thuật; chưa phải đánh giá độc lập hoặc bằng chứng hiệu lực lâm sàng.

## Tóm tắt

Đồ án xây dựng BoneScope, một nguyên mẫu chạy cục bộ gồm bộ phân loại ảnh X-quang kết hợp 22 trường metadata, kho truy xuất tài liệu có nguồn, chatbot nhiều lượt và lịch sử văn bản bằng SQLite. Bộ phân loại dùng checkpoint Swin và nhánh metadata hiện có; báo cáo không tuyên bố đã huấn luyện lại checkpoint. Ảnh gửi vào chat hiện trực tiếp trong tin nhắn và được giữ tạm trong tab để hỏi tiếp; ứng dụng không ghi byte ảnh vào lịch sử SQLite. Chế độ tra cứu cục bộ không cần API key, còn chat tạo sinh có thể gửi dữ liệu tới provider đã cấu hình.

Thực nghiệm trên 250 ảnh BTXRD, lấy 25 ảnh cho mỗi nhãn, ghi Top-1 bằng 0,776 khi có metadata và 0,480 khi vector metadata bằng 0; Macro-F1 lần lượt là 0,776 và 0,439. Chênh lệch Top-1 là 29,6 điểm phần trăm. Đây là đánh giá **nội nguồn** vì checkpoint đã được huấn luyện trên BTXRD và không có ID split gốc để tách tập kiểm định độc lập.

Kho RAG có 22 nguồn, 794 đoạn và index 794 × 384 chiều. Audit provenance đạt; replay 16/16 báo cáo khớp. Các tập truy vấn phát triển đã được xem hoặc do tác nhân soạn, nên chỉ số retrieval không ước lượng hiệu năng ngoài mẫu. Trên mã hiện tại, bộ hồi quy đạt 216 bài, 227 subtests; bài Chrome chạy riêng đạt 1/1 với ảnh tổng hợp và AI giả lập. Bảy cổng đánh giá G1–G7 còn mở và `answer_ready=false`. BoneScope phù hợp để trình bày một nguyên mẫu học tập có giới hạn; chưa đủ bằng chứng về hiệu lực lâm sàng, quyền phát hành từng ảnh hoặc chất lượng câu trả lời trên tập độc lập.

**Từ khóa:** ảnh X-quang xương; metadata; Swin Transformer; truy xuất tài liệu; chatbot; đánh giá nội nguồn.

<!-- pagebreak -->

## 1 Mục tiêu và phạm vi

Đồ án đặt ba câu hỏi: (1) có thể tích hợp ảnh và metadata trong một luồng dự đoán có hợp đồng đầu vào rõ ràng không; (2) checkpoint hiện có thay đổi thế nào khi metadata bị xóa; và (3) có thể tổ chức nguồn tham khảo để chatbot truy xuất, trích dẫn và lưu lịch sử mà vẫn chỉ lưu văn bản hay không. Phần mềm và các thí nghiệm trong báo cáo trả lời các câu hỏi này ở phạm vi nguyên mẫu, không suy rộng ra thực hành y khoa.

### Mục tiêu học tập

| Mục tiêu | Kết quả trong nguyên mẫu |
|---|---|
| Kết hợp ảnh X-quang với metadata | Pipeline Swin + MetadataMLP + Cross-Attention, 10 nhãn cấp ảnh |
| Tạo kho kiến thức có thể truy vết | Corpus text-only có source metadata, hash, index phiên bản và replay |
| Cho phép hỏi đáp nhiều lượt | Chat chữ, chế độ tra cứu tài liệu, chat ảnh tạm theo cuộc trò chuyện |
| Lưu hội thoại và mở lại | SQLite lưu văn bản và thông tin nguồn được phép; không lưu byte ảnh |
| Nêu rõ giới hạn và tái lập kết quả | Báo cáo tách metric nội nguồn khỏi kiểm định độc lập; có audit/replay và record kỹ thuật |

Sản phẩm phần mềm của đồ án là luồng tích hợp API, hợp đồng metadata, đối chiếu hash BTXRD, corpus/index có nguồn, giao diện hỏi đáp, lịch sử SQLite và bộ kiểm thử. Swin, E5, bộ BTXRD và model sinh văn bản là các thành phần hoặc nguồn bên ngoài được sử dụng có ghi xuất xứ; báo cáo không nhận đó là mô hình hoặc dữ liệu do đồ án tự phát minh.

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

Lượt kiểm tra ngày 13/11 không phát hiện cache nguồn thiếu; audit đối chiếu 10 bộ evaluation, replay khớp 16/16 báo cáo và không có mismatch. Xem [audit hiện hành](../reference/project_report_rag_audit_20261113.json) và [replay hiện hành](../reference/project_report_rag_replay_20261113.json).

## 4 Phương pháp thực nghiệm ảnh

### Mô hình và đầu vào

Mô hình kết hợp Swin Transformer cho ảnh, `MetadataMLP` cho 22 trường và Cross-Attention để hợp nhất đặc trưng; đầu ra gồm 10 nhãn cấp ảnh. Swin là backbone thị giác phân cấp dùng shifted windows, được giới thiệu cho phân loại và các tác vụ thị giác khác [2]. Hợp đồng metadata yêu cầu đủ trường theo schema, có ít nhất một vị trí giải phẫu và đúng một tư thế trong các giá trị được hỗ trợ. API giới hạn kích thước/định dạng ảnh và từ chối metadata thiếu hoặc ảnh hỏng.

Metadata chỉ tự điền khi hash byte ảnh khớp chính xác với một bản ghi BTXRD duy nhất và không mâu thuẫn. Với ảnh ngoài tập, hệ thống không đoán metadata từ tên file, không gán 0 cho trường chưa biết và chuyển sang luồng mô tả ảnh nếu người dùng chọn.

### Thiết kế đánh giá

Mẫu gồm 250 ảnh, 25 ảnh mỗi nhãn trong 10 nhãn, được lấy với seed `20261031`. Chạy hai điều kiện: metadata thật và vector metadata được đặt bằng 0. Đây là thí nghiệm nội nguồn/ablation trên bộ liên quan tới huấn luyện checkpoint; không đánh giá tổng quát hóa sang bệnh viện, thiết bị, dân số hoặc cohort ngoài.

Cùng một checkpoint và cùng 250 ảnh được dùng cho hai điều kiện để chênh lệch phản ánh thay đổi đầu vào metadata trong mẫu này. Manifest ảnh, hash checkpoint, hash bộ tiền xử lý, seed, phiên bản môi trường và ID mẫu nằm trong [record đánh giá](../reference/stage11_xray_in_source_evaluation_20261103.json). Vì thiếu danh sách ID của split gốc, báo cáo không ước lượng khoảng tin cậy cho hiệu năng trên dữ liệu độc lập và không gọi tập 250 ảnh là test set.

Top-1 và Top-3 đo tỷ lệ nhãn thật nằm trong một hoặc ba dự đoán đầu. Macro-F1 lấy trung bình F1 theo lớp để các lớp có trọng số bằng nhau. ECE 10-bin, MCE, Brier và NLL mô tả độ phù hợp giữa điểm softmax và kết quả quan sát trong mẫu; chúng không hiệu chuẩn xác suất lâm sàng.

## 5 Kết quả mô hình ảnh

### Kết quả tổng thể

| Điều kiện | Top-1 | Top-3 | Macro-F1 | Ghi chú |
|---|---:|---:|---:|---|
| Có đủ 22 metadata | 0,776 (194/250) | 0,940 (235/250) | 0,776 | Điều kiện tham chiếu |
| Vector metadata bằng 0 | 0,480 (120/250) | 0,720 (180/250) | 0,439 | Ablation, không phải cách xử lý metadata thiếu được khuyến nghị |
| Chênh lệch | −0,296 | −0,220 | −0,337 | Top-1 giảm 29,6 điểm phần trăm; 91/250 dự đoán đổi nhãn |

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

**Giới hạn ngưỡng.** Thăm dò trên 28 câu đã xem cho thấy cosine của nhóm dương và âm chồng lấn. Không có một ngưỡng dense đơn nào tách hoàn toàn hai nhóm trong bộ này. Không cài ngưỡng mặc định dựa trên mẫu đã xem; công cụ hiệu chỉnh chờ nhãn phù hợp. Strict lexical verifier cũng để ở chế độ opt-in vì có thể chặn câu dương. Coverage từ vựng không chứng minh entailment.

Hệ thống hiện hiển thị các passage có liên quan làm nguồn đọc thêm. Chưa có người chấm độc lập cho relevance, direct support, polarity, qualifiers và context; chưa có đánh giá entailment của câu trả lời sinh. RAG score không được gọi là độ chính xác chatbot.

## 7 Chatbot, hội thoại và lưu trữ

### Luồng hội thoại

Chatbot hỗ trợ hội thoại đa chủ đề; khi hỏi về xương, có thể truy xuất kho nguồn và trả citations. Chế độ chỉ tra cứu giới hạn đầu ra theo passages. Ảnh chờ gửi có hình xem trước, ảnh đã gửi xuất hiện trực tiếp trong tin nhắn và mở lớn được; câu hỏi chỉ có ảnh cũng được hỗ trợ. Chat ảnh cho phép hỏi tiếp trong cùng cuộc trò chuyện bằng cách giữ ảnh tạm trong tab. Chuyển hội thoại rồi quay lại trong cùng tab vẫn hiển thị ảnh ở đúng tin nhắn; đóng tab hoặc tải lại trang sẽ bỏ byte ảnh. Mở lại lịch sử sau đó chỉ còn chữ và nguồn, nên cần đính kèm ảnh lại nếu muốn tiếp tục phân tích.

### Lịch sử và dữ liệu gửi tới provider

SQLite lưu văn bản hội thoại và các trường nguồn được cho phép; không lưu byte ảnh. Lịch sử hỗ trợ mở lại, đổi tên và xóa. Ảnh chat được gửi tới vision provider đã cấu hình khi người dùng yêu cầu phân tích ảnh; ảnh không được lưu vào database lịch sử nhưng việc gửi tới provider vẫn là truyền dữ liệu ra ngoài máy. Vì vậy chỉ sử dụng ảnh có quyền gửi và không dùng dữ liệu bệnh nhân hoặc ảnh định danh.

Ở luồng classifier, ảnh và metadata được xử lý cục bộ; chatbot có thể nhận Top-3 và điểm số dạng tối thiểu trong phần giải thích ca, theo luồng ứng dụng. Cách xử lý này không thay thế kiểm tra data-flow của từng cấu hình triển khai.

### Model provider và chi phí

Ứng dụng hỗ trợ OpenRouter Free làm tuyến ưu tiên và Qwen làm fallback trả phí theo cấu hình; Groq là tùy chọn. Model Free có thể giới hạn tốc độ hoặc ngừng khả dụng. Việc gửi ảnh có thể phát sinh chi phí tùy model/provider. Người vận hành cần đọc cấu hình `.env`, không chia sẻ API key và theo dõi usage trước khi demo với dữ liệu thử được phép. Báo cáo không ghi key hoặc chi phí dự kiến.

Các smoke provider được ghi từ ngày 09/11 dùng câu thử ngắn và ảnh hình học tổng hợp; chúng xác nhận kết nối/chuyển tuyến, không đánh giá chất lượng mô tả X-quang. Xem [record provider smoke](../reference/chatbot_provider_smoke_20261109.json).

## 8 Kiểm chứng phần mềm ngày 13 tháng 11 năm 2026

Các lệnh hồi quy, audit, replay, chatbot doctor và kiểm tra register được chạy lại trên mã `ac3ac770133ca6cb9758bb450d37c4cdc7531d40`. Kết quả tóm tắt được lưu trong [record 13/11](../reference/project_report_verification_20261113.json); audit và replay có [JSON đầy đủ](../reference/project_report_rag_audit_20261113.json), [JSON replay](../reference/project_report_rag_replay_20261113.json). API parity 3/3 là kết quả lịch sử ngày 12/11, không chạy lại trong đợt này.

| Hạng mục | Kết quả | Diễn giải |
|---|---|---|
| Regression toàn dự án | 216 passed, 0 failed, 1 skipped; 227 subtests passed | Một cảnh báo deprecation của Starlette; bài Chrome bị skip trong sandbox |
| Browser smoke chạy riêng | PASS 1/1 ngoài sandbox | Chrome, SQLite tạm, ảnh tổng hợp và AI giả lập; gồm ảnh hiện trực tiếp trong tin nhắn |
| RAG audit | PASS, 22 nguồn, 794 chunks, 0 cache thiếu, 10 bộ evaluation | Kiểm tra provenance và cấu trúc |
| RAG replay | PASS, 16/16, 0 mismatch | Tái lập report đã lưu |
| Chatbot doctor | PASS, 13/13 | Kiểm tra cấu hình cục bộ, không gọi provider |
| API local parity ngày 12/11 | PASS, 3/3 ca tham chiếu, max score delta 0 | Hash model khớp theo [record 12/11](../reference/project_verification_20261112.json); không chạy lại ngày 13/11 |
| Register Stage 11 | PASS cấu trúc; 24 tham chiếu, 15 cohort rows | 7 gate vẫn OPEN |
| Liên kết Markdown ngày 12/11 | PASS, 954 link trong 54 file, 0 hỏng | Record cũ; liên kết của báo cáo 13/11 được kiểm tra riêng trước khi bàn giao |
| Provider calls trong record | Không có | Các kiểm tra kỹ thuật trên không tiêu token API |
| DOCX báo cáo 13/11 | Xuất từ Markdown và kiểm tra trực quan từng trang | Dùng Word trên Windows để chuyển PDF và Poppler để xem trang; renderer chuẩn không có LibreOffice trên máy này |

Các phép thử dùng dữ liệu tổng hợp và provider giả lập, không chấm độ đúng y khoa hoặc chất lượng văn bản do provider thật tạo. Trạng thái gate nghiên cứu vẫn được đánh giá riêng ở mục 9 và 14.

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

BoneScope hiện là nguyên mẫu học tập có thể trình diễn cục bộ với classifier, retrieval có nguồn, chatbot đa lượt, hội thoại ảnh tạm và lưu lịch sử văn bản. Bộ hồi quy và kiểm tra Chrome, RAG, API đã ghi nhận hỗ trợ việc tái lập các luồng phần mềm. Thí nghiệm metadata cho thấy đầu ra classifier phụ thuộc mạnh vào metadata, còn bộ retrieval hiện tại chưa đủ để chọn ngưỡng tin cậy chung.

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
.\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q
```

Lệnh audit, replay và doctor có trong [README tiếng Việt](../../README_VI.md) và [bàn giao tiếp quản](../../START_HERE_NEXT_CODEX_VI.md). Dùng tên record mới khi chạy lại để giữ nguyên bằng chứng lịch sử.

## 12 Tài liệu và artifact tham chiếu

- Kiểm chứng và demo: [record 13/11](../reference/project_report_verification_20261113.json), [audit RAG](../reference/project_report_rag_audit_20261113.json), [replay RAG](../reference/project_report_rag_replay_20261113.json), [checklist nghiệm thu](PRODUCT_ACCEPTANCE_CHECKLIST_VI.md).
- Ảnh và mô hình: [đánh giá 250 ảnh](../reference/stage11_xray_in_source_evaluation_20261103.json), [calibration và nhóm con](../reference/stage12_xray_subgroup_and_calibration_20261106.json), [catalogue BTXRD](../reference/stage12_btxrd_catalogue_and_mapping_analysis_20261105.json).
- Hồ sơ kỹ thuật trước đó: [xác minh 12/11](../reference/project_verification_20261112.json), [precheck nghiệm thu](../reference/project_acceptance_precheck_20261112.json), [rà soát cấu trúc](../reference/project_structure_review_20261111.json).
- Trạng thái nghiên cứu: [sổ G1–G7](../reference/stage11_acceptance_gate_status_20261029.csv), [blocker](../reference/STAGE11_GATE_CLOSURE_BLOCKERS_VI.md), [review nội bộ AI](STAGE11_AI_INTERNAL_GATE_REVIEW_20261112_VI.md).

## 13 Tài liệu tham khảo

1. Yao, S. et al. (2025). “A Radiograph Dataset for the Classification, Localization, and Segmentation of Primary Bone Tumors.” *Scientific Data*, 12, 88. [Bài báo BTXRD](https://www.nature.com/articles/s41597-024-04311-y), DOI: 10.1038/s41597-024-04311-y. Bài báo dẫn [archive Figshare](https://doi.org/10.6084/m9.figshare.27865398). Giấy phép bài báo không tự xác nhận quyền ở cấp từng tệp ảnh hoặc nguồn bên thứ ba.
2. Liu, Z. et al. (2021). “Swin Transformer: Hierarchical Vision Transformer using Shifted Windows.” *Proceedings of ICCV 2021*. [Bản bài báo trên arXiv](https://arxiv.org/abs/2103.14030). DOI hội nghị: 10.1109/ICCV48922.2021.00986.
3. Wang, L. et al. (2024). “Multilingual E5 Text Embeddings: A Technical Report.” [arXiv:2402.05672](https://arxiv.org/abs/2402.05672).
4. Lewis, P. et al. (2020). “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.” *Advances in Neural Information Processing Systems 33*. [Bài báo NeurIPS](https://proceedings.neurips.cc/paper/2020/hash/6b493230-Abstract.html).

## 14 Việc còn lại và điều kiện hoàn tất

Các mục dưới đây là điều kiện chưa được chứng minh trong workspace. Chúng không được thay bằng cách ghi “đã xong” trong báo cáo hoặc bằng review tự động của chính hệ thống.

| Ưu tiên | Bằng chứng cần bổ sung | Trạng thái |
|---|---|---|
| P0 · Retrieval | Tập câu hỏi khóa, nhãn độc lập và đánh giá trên dữ liệu chưa dùng để chọn policy | 28 truy vấn đã xem có score chồng lấn; `AWAITING_LABELS` |
| P0 · Mô hình ảnh | Cohort được phép, patient-level manifest, reference standard, split định trước và audit overlap | Chưa có; 250 ảnh hiện tại là nội nguồn |
| P0 · Quyền ảnh | Điều kiện archive Figshare, nguồn upstream, attribution và quyền từng ảnh | Chưa đủ hồ sơ; không phát hành archive hoặc ảnh |
| P1 · Demo | Chạy checklist trực tiếp trên máy sẽ trình bày | Browser smoke giả lập đạt; buổi demo chờ xác nhận |
| P1 · Dữ liệu | Chốt luồng local/provider, retention, log, backup, xóa và quyền truy cập | Chưa có phê duyệt triển khai |
| P1 · Nguồn RAG | Reviewer chấm direct support, polarity, qualifiers, context và adjudication | Chưa có nhãn độc lập; audit/replay chỉ chứng minh provenance, tái lập |
| P2 · G1–G7 | Owner khóa tiêu chí và người có thẩm quyền quyết định từng gate | 7 OPEN, 0 CLOSED |

**Mốc dùng được hiện tại:** nguyên mẫu local phù hợp để trình diễn học tập có giới hạn và trình bày các thí nghiệm đã ghi. Checklist kỹ thuật hẹp của Giai đoạn 11 đạt 6/7 mục (xấp xỉ 86% độ bao phủ checklist), nhưng mục cuối chờ nhãn; đây không phải tỷ lệ hoàn thành toàn dự án. Không có mẫu số và tiêu chí để tuyên bố một tỷ lệ “100%” chung. Các mục P0 là điều kiện để đánh giá độc lập hoặc phát hành dữ liệu, không phải điều kiện để báo cáo trung thực về nguyên mẫu học tập.
