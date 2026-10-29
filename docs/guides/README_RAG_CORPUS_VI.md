# Kho tài liệu nguồn cho RAG

Giai đoạn 10 tạo kho văn bản nguồn để phát triển truy xuất. Embedding và chỉ mục đã được triển khai sau đó ở [giai đoạn 11](README_RAG_INDEX_VI.md); chatbot chưa được triển khai. Không đưa ảnh bệnh nhân hay metadata ca bệnh vào kho.

**Snapshot hiện hành (28/10/2026):** 759 chunk/21 nguồn; corpus SHA-256 `b34d318c136f591d3b417e39603141f7d7836b960bf72d75a547653529e48d9d`. Parser loại mục Data Availability Statement khỏi review OFD; source cache gốc vẫn được giữ nguyên và xác minh bằng SHA-256. Ngoài 13 mục NCI và 8 nguồn ngoài NCI, corpus có review synovial chondromatosis 2026 (35 chunk) và review OFD 2024 (29 chunk), cả hai từ Europe PMC JATS XML với PMCID/DOI và CC BY 4.0 xác minh trong payload. Review OFD là narrative review, không phải guideline, và nêu rõ không có systematic evaluation/meta-analysis; không dùng để suy mapping nhãn BTXRD `osteofibroma`. BioC table blocks/captions của BSG và Cureus bị loại; bảng BSG có nội dung ghi adapted từ WHO 2020. Không tự đồng nhất nhãn BTXRD `synovial osteochondroma` với synovial chondromatosis; review OFD cũng không xác lập mapping nhãn BTXRD `osteofibroma`. Bone-RADS chỉ áp dụng cho tổn thương đơn độc tình cờ trên CT/MRI ở người lớn; BSG phản ánh hệ thống UK; các review hình ảnh không phải guideline điều trị. Rà soát chi tiết tại [ghi chú nguồn trực tuyến](../reference/stage11_online_evidence_review_20261028.md).

Snapshot trước ngày 27/10/2026 gồm **439 đoạn từ 13 nguồn**: 13 mục NCI và một bài Open Orthopaedics Journal CC BY 4.0. Nguồn cohort là nghiên cứu hồi cứu 51 nang xương đơn độc đầu trên xương cánh tay điều trị bằng BMA/DBM, không phải hướng dẫn điều trị chung. Đây là mốc lịch sử; snapshot hiện hành và hash mới ở đầu tài liệu.

Bản trước có 416 đoạn/12 nguồn sau khi sửa bộ trích xuất; bản đầu có 489 đoạn. Các danh mục References bị loại, khoảng trắng block/ô bảng được sửa, mục danh sách ngắn được giữ lại. Chunk ID và mã băm có thể đổi; cần dùng corpus, source lock, index và evidence cùng phiên bản.

## Nguồn và quyền sử dụng

`rag/data/sources.json` là registry đang hoạt động: 13 mục NCI (bao gồm mục Glossary osteochondroma), Open Orthopaedics, Cureus, BSG/BJC, review MRI gối, review X-quang chi, SSR Bone-RADS, review synovial chondromatosis và review OFD. NCI tuân theo chính sách [Reuse of NCI Information](https://www.cancer.gov/policies/copyright-reuse). Các nguồn ngoài NCI được xác nhận license từng bài; parser đòi định danh CC BY 4.0 tường minh và từ chối BY-NC/BY-ND/BY-SA từ cả câu license lẫn URL/href, không suy license chỉ từ khả năng truy cập trên PMC hay một phần chuỗi tên license. Cách kiểm tra và giới hạn được ghi trong [rà soát nguồn trực tuyến](../reference/stage11_online_evidence_review_20261028.md#explicit-license-identity-validation--28102026). Quy tắc này không cấp quyền cho hình, tài liệu bên thứ ba hoặc ảnh bệnh nhân. Bài BSG có scope điều trị/dịch vụ UK. Kho văn bản không lưu hình hoặc logo. Mỗi lần tải cần giữ nguồn gốc, thời điểm truy cập và hash.

## Tạo và kiểm tra kho

Từ thư mục gốc dự án:

```powershell
.\.venv\Scripts\python.exe rag/build_corpus.py
.\.venv\Scripts\python.exe -m unittest discover -s rag/tests -v
```

Sau lần tải đầu, chạy `rag/build_corpus.py --offline` để tạo lại từ HTML đã lưu trong `rag/source_cache/`. Cả chế độ online và offline đều validate registry trước khi đọc/ghi payload; NCI phải khai báo đúng chuỗi policy reuse và URL policy, nguồn ngoài NCI phải khai báo CC BY 4.0 cùng URL license. Bộ HTML bị Git bỏ qua; `rag/data/corpus.jsonl` và `rag/data/source_lock.json` là bản chụp có thể chia sẻ. `source_lock.json` lưu URL, publisher, license, scope, thời điểm truy cập, mã băm payload nguồn và số đoạn. Mỗi dòng corpus lưu provenance tương ứng. Pipeline dùng host allowlist tường minh cho NCI (bao gồm mục Glossary osteochondroma), Open Orthopaedics, PMC/NCBI BioC và Europe PMC JATS; nguồn ngoài NCI phải khai báo định danh/endpoint nguồn khi áp dụng và phạm vi bằng chứng. Không thêm nguồn nếu chưa kiểm tra giấy phép và toàn văn.

`rag/data/evaluation_questions.json` chứa câu hỏi tiếng Việt, đáp án ngắn và nguồn/mục kỳ vọng. Hai câu ngoài phạm vi kiểm tra cách từ chối khẳng định thiếu bằng chứng và yêu cầu điều trị cá nhân hóa. Kết quả retrieval hiện tại nằm trong [hướng dẫn giai đoạn 11](README_RAG_INDEX_VI.md).

## Cập nhật và loại bỏ nguồn

Kiểm tra URL, ngày cập nhật và mã băm ít nhất mỗi quý và trước mỗi bản phát hành. Khi nguồn đổi, chạy lại pipeline, xem `git diff` của `corpus.jsonl` và `source_lock.json`, rà soát các đoạn thay đổi rồi mới chấp nhận bản mới. Nếu nguồn lỗi thời, không còn truy cập được hoặc không phù hợp, xóa nó khỏi `sources.json` và tạo lại kho; các đoạn của nguồn đó phải biến mất. Bất kỳ thay đổi nội dung nào cũng làm vô hiệu chỉ mục embedding ở giai đoạn sau và đòi hỏi tạo lại chỉ mục, chạy lại bộ câu hỏi kiểm thử. Git giữ lịch sử bản nguồn cũ; không dùng bản cũ để trả lời sau khi đã thay thế.

## Giới hạn và việc tiếp theo

Kho hiện nghiêng về ung thư xương nguyên phát, osteosarcoma, Ewing sarcoma và một số u hiếm. Nguồn nang xương mới chỉ đề cập một can thiệp trên một vị trí giải phẫu và không lấp đầy khoảng trống hướng dẫn tổng quát. Nhiều nhãn như osteofibroma và synovial osteochondroma vẫn thiếu nguồn phù hợp; không dùng kho để khẳng định ngoài các đoạn có bằng chứng. Truy vấn tiếng Việt cho bài mới hiện bị từ chối do coverage/routing dù truy vấn tiếng Anh lấy đúng hit. Cần giải quyết lỗi này, bổ sung nguồn có quyền rõ, rà soát chuyên môn và đánh giá trên bộ tách riêng.

## Completion Note — Giai đoạn 10

- Ngày: 27/10/2026.
- Nguồn tại snapshot hiện hành: 21 nguồn (13 NCI, 1 Open Orthopaedics, 1 Cureus, 1 BSG/BJC, 1 review MRI gối, 1 review X-quang chi, 1 SSR Bone-RADS, 1 review synovial chondromatosis, 1 review OFD); URL và mã băm lưu tại `rag/data/source_lock.json`.
- Pipeline: `rag/build_corpus.py`; chia đoạn theo tiêu đề và đoạn văn.
- Citation: `source_id`, URL, tên mục, thời điểm truy cập và mã băm trên từng đoạn.
- Bộ câu hỏi: 12 mục trong `rag/data/evaluation_questions.json`.
- Trạng thái: PASS cho kho nguồn và khả năng truy ngược kỹ thuật; độ phủ nhãn và thẩm định chuyên môn còn cần bổ sung trước khi dùng chatbot.
- Snapshot lịch sử trước lần bổ sung nguồn 28/10: corpus 439 đoạn. Các tập `evaluation_v2.json` và `evaluation_evidence_v3.json` đã được xem; không xem là held-out validation. Trạng thái và hash hiện hành ở `docs/STAGE11_HANDOFF_VI.md`.
