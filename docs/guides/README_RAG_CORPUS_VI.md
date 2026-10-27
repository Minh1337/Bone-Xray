# Kho tài liệu nguồn cho RAG

Giai đoạn 10 tạo kho văn bản nguồn để phát triển truy xuất. Embedding và chỉ mục đã được triển khai sau đó ở [giai đoạn 11](README_RAG_INDEX_VI.md); chatbot chưa được triển khai. Không đưa ảnh bệnh nhân hay metadata ca bệnh vào kho.

Sau vòng sửa bộ trích xuất giai đoạn 11, corpus hiện có **416 đoạn từ 12 nguồn**. Bản đầu có 489 đoạn; các danh mục References bị gán nhầm vào nội dung đã được loại, khoảng trắng của block/ô bảng được sửa và các mục danh sách ngắn được giữ lại. Chunk ID và mã băm có thể đổi; cần dùng corpus, source lock, index và evidence của cùng phiên bản.

## Nguồn và quyền sử dụng

`rag/data/sources.json` liệt kê 12 trang của National Cancer Institute (NCI). Chính sách [Reuse of NCI Information](https://www.cancer.gov/policies/copyright-reuse) cho phép tái sử dụng chữ, yêu cầu ghi nguồn và liên kết trang gốc. Kho chỉ trích phần chữ; không lưu hình, logo hoặc dùng nhãn hiệu PDQ để nhận diện một bản trích đoạn như bản tóm tắt PDQ đầy đủ. Các trang có thể được cập nhật, vì vậy mỗi lần tải cần ghi thời điểm và mã băm.

## Tạo và kiểm tra kho

Từ thư mục gốc dự án:

```powershell
.\.venv\Scripts\python.exe rag/build_corpus.py
.\.venv\Scripts\python.exe -m unittest discover -s rag/tests -v
```

Sau lần tải đầu, chạy `rag/build_corpus.py --offline` để tạo lại từ HTML đã lưu trong `rag/source_cache/`. Bộ HTML này được bỏ qua bởi Git; `rag/data/corpus.jsonl` và `rag/data/source_lock.json` là bản chụp có thể chia sẻ. `source_lock.json` lưu URL, nhà xuất bản, thời điểm truy cập, mã băm HTML và số đoạn. Mỗi dòng `corpus.jsonl` lưu mã nguồn, tiêu đề, URL, tên mục, mã băm nguồn, mã băm đoạn và văn bản. Khi tái tạo về sau, nội dung nguồn có thể đổi và mã băm sẽ cho thấy sự khác biệt.

`rag/data/evaluation_questions.json` chứa câu hỏi tiếng Việt, đáp án ngắn và nguồn/mục kỳ vọng. Hai câu ngoài phạm vi kiểm tra cách từ chối khẳng định thiếu bằng chứng và yêu cầu điều trị cá nhân hóa. Kết quả retrieval hiện tại nằm trong [hướng dẫn giai đoạn 11](README_RAG_INDEX_VI.md).

## Cập nhật và loại bỏ nguồn

Kiểm tra URL, ngày cập nhật và mã băm ít nhất mỗi quý và trước mỗi bản phát hành. Khi nguồn đổi, chạy lại pipeline, xem `git diff` của `corpus.jsonl` và `source_lock.json`, rà soát các đoạn thay đổi rồi mới chấp nhận bản mới. Nếu nguồn lỗi thời, không còn truy cập được hoặc không phù hợp, xóa nó khỏi `sources.json` và tạo lại kho; các đoạn của nguồn đó phải biến mất. Bất kỳ thay đổi nội dung nào cũng làm vô hiệu chỉ mục embedding ở giai đoạn sau và đòi hỏi tạo lại chỉ mục, chạy lại bộ câu hỏi kiểm thử. Git giữ lịch sử bản nguồn cũ; không dùng bản cũ để trả lời sau khi đã thay thế.

## Giới hạn và việc tiếp theo

Kho hiện nghiêng về ung thư xương nguyên phát, osteosarcoma, Ewing sarcoma và một số u hiếm. Nhiều nhãn của mô hình ảnh như simple bone cyst, osteofibroma và synovial osteochondroma chưa có nguồn chuyên biệt. Không dùng kho hiện tại để khẳng định về các nhãn đó. Cần bổ sung nguồn có xuất xứ và quyền sử dụng rõ, rà soát nội dung chuyên môn, xây lại chỉ mục và đo retrieval trên bộ câu hỏi tách riêng để đánh giá.

## Completion Note — Giai đoạn 10

- Ngày: 27/10/2026.
- Nguồn: 12 trang NCI; URL và mã băm lưu tại `rag/data/source_lock.json`.
- Pipeline: `rag/build_corpus.py`; chia đoạn theo tiêu đề và đoạn văn.
- Citation: `source_id`, URL, tên mục, thời điểm truy cập và mã băm trên từng đoạn.
- Bộ câu hỏi: 12 mục trong `rag/data/evaluation_questions.json`.
- Trạng thái: PASS cho kho nguồn và khả năng truy ngược kỹ thuật; độ phủ nhãn và thẩm định chuyên môn còn cần bổ sung trước khi dùng chatbot.
- Cập nhật từ giai đoạn 11: corpus hiện 416 đoạn; thêm `rag/data/evaluation_v2.json` gồm 28 câu dev/test với gold khóa theo mã băm đoạn. Kết quả và điểm tiếp tục ở `docs/STAGE11_HANDOFF_VI.md`.
