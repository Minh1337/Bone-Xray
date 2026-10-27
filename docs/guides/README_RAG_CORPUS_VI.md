# Kho tài liệu nguồn cho RAG

Giai đoạn 10 tạo kho văn bản nguồn để phát triển truy xuất. Embedding và chỉ mục đã được triển khai sau đó ở [giai đoạn 11](README_RAG_INDEX_VI.md); chatbot chưa được triển khai. Không đưa ảnh bệnh nhân hay metadata ca bệnh vào kho.

Sau cập nhật ngày 27/10/2026, corpus hiện có **439 đoạn từ 13 nguồn**: 12 trang NCI và một bài Open Orthopaedics Journal được cấp CC BY 4.0. Nguồn bổ sung là cohort hồi cứu 51 nang xương đơn độc vùng đầu trên xương cánh tay điều trị bằng BMA/DBM; đây không phải hướng dẫn điều trị chung. Metadata mỗi đoạn có publisher, authors, source date, license, license URL và scope. Khối lượt tải/metrics trên trang bị loại khỏi corpus. Corpus hash: `552eb6b313ca472dc92e5a20280dbf02a39d74091439a895099127c6b96c8dfb`.

Bản trước có 416 đoạn/12 nguồn sau khi sửa bộ trích xuất; bản đầu có 489 đoạn. Các danh mục References bị loại, khoảng trắng block/ô bảng được sửa, mục danh sách ngắn được giữ lại. Chunk ID và mã băm có thể đổi; cần dùng corpus, source lock, index và evidence cùng phiên bản.

## Nguồn và quyền sử dụng

`rag/data/sources.json` liệt kê 12 trang National Cancer Institute và một bài CC BY 4.0. Chính sách [Reuse of NCI Information](https://www.cancer.gov/policies/copyright-reuse) cho phép tái sử dụng chữ theo điều kiện của NCI. Bài Open Orthopaedics được ghi tác giả/nhà xuất bản và [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Kho chỉ trích phần chữ; không lưu hình, logo hoặc dùng nhãn hiệu PDQ để nhận diện bản trích đoạn như bản PDQ đầy đủ. Các trang có thể được cập nhật, nên mỗi lần tải cần ghi thời điểm và mã băm.

## Tạo và kiểm tra kho

Từ thư mục gốc dự án:

```powershell
.\.venv\Scripts\python.exe rag/build_corpus.py
.\.venv\Scripts\python.exe -m unittest discover -s rag/tests -v
```

Sau lần tải đầu, chạy `rag/build_corpus.py --offline` để tạo lại từ HTML đã lưu trong `rag/source_cache/`. Bộ HTML bị Git bỏ qua; `rag/data/corpus.jsonl` và `rag/data/source_lock.json` là bản chụp có thể chia sẻ. `source_lock.json` lưu URL, publisher, license, scope, thời điểm truy cập, mã băm HTML và số đoạn. Mỗi dòng corpus lưu provenance tương ứng. Pipeline chỉ cho phép host NCI và Open Orthopaedics; nguồn ngoài NCI phải khai báo rõ CC BY 4.0 và phạm vi bằng chứng. Không thêm nguồn nếu chưa kiểm tra giấy phép và toàn văn.

`rag/data/evaluation_questions.json` chứa câu hỏi tiếng Việt, đáp án ngắn và nguồn/mục kỳ vọng. Hai câu ngoài phạm vi kiểm tra cách từ chối khẳng định thiếu bằng chứng và yêu cầu điều trị cá nhân hóa. Kết quả retrieval hiện tại nằm trong [hướng dẫn giai đoạn 11](README_RAG_INDEX_VI.md).

## Cập nhật và loại bỏ nguồn

Kiểm tra URL, ngày cập nhật và mã băm ít nhất mỗi quý và trước mỗi bản phát hành. Khi nguồn đổi, chạy lại pipeline, xem `git diff` của `corpus.jsonl` và `source_lock.json`, rà soát các đoạn thay đổi rồi mới chấp nhận bản mới. Nếu nguồn lỗi thời, không còn truy cập được hoặc không phù hợp, xóa nó khỏi `sources.json` và tạo lại kho; các đoạn của nguồn đó phải biến mất. Bất kỳ thay đổi nội dung nào cũng làm vô hiệu chỉ mục embedding ở giai đoạn sau và đòi hỏi tạo lại chỉ mục, chạy lại bộ câu hỏi kiểm thử. Git giữ lịch sử bản nguồn cũ; không dùng bản cũ để trả lời sau khi đã thay thế.

## Giới hạn và việc tiếp theo

Kho hiện nghiêng về ung thư xương nguyên phát, osteosarcoma, Ewing sarcoma và một số u hiếm. Nguồn nang xương mới chỉ đề cập một can thiệp trên một vị trí giải phẫu và không lấp đầy khoảng trống hướng dẫn tổng quát. Nhiều nhãn như osteofibroma và synovial osteochondroma vẫn thiếu nguồn phù hợp; không dùng kho để khẳng định ngoài các đoạn có bằng chứng. Truy vấn tiếng Việt cho bài mới hiện bị từ chối do coverage/routing dù truy vấn tiếng Anh lấy đúng hit. Cần giải quyết lỗi này, bổ sung nguồn có quyền rõ, rà soát chuyên môn và đánh giá trên bộ tách riêng.

## Completion Note — Giai đoạn 10

- Ngày: 27/10/2026.
- Nguồn: hiện 13 nguồn (12 NCI, 1 Open Orthopaedics CC BY 4.0); URL và mã băm lưu tại `rag/data/source_lock.json`.
- Pipeline: `rag/build_corpus.py`; chia đoạn theo tiêu đề và đoạn văn.
- Citation: `source_id`, URL, tên mục, thời điểm truy cập và mã băm trên từng đoạn.
- Bộ câu hỏi: 12 mục trong `rag/data/evaluation_questions.json`.
- Trạng thái: PASS cho kho nguồn và khả năng truy ngược kỹ thuật; độ phủ nhãn và thẩm định chuyên môn còn cần bổ sung trước khi dùng chatbot.
- Cập nhật từ giai đoạn 11: corpus hiện 439 đoạn; index đã xây lại. `evaluation_v2.json` (28 câu) và `evaluation_evidence_v3.json` đã đồng bộ corpus hash nhưng là regression đã xem. Kết quả và điểm tiếp tục ở `docs/STAGE11_HANDOFF_VI.md`.
