# Chỉ mục vector và truy xuất RAG — giai đoạn 11

Kho nguồn nằm trong `rag/data/`; chỉ mục và mô hình tải về nằm trong `rag/index/` và `rag/models/`, được Git bỏ qua. Không đưa ảnh hoặc dữ liệu ca bệnh vào chỉ mục.

## Tạo chỉ mục

Từ thư mục gốc dự án:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements_rag.txt
.\.venv\Scripts\python.exe rag/build_index.py --download-model
.\.venv\Scripts\python.exe rag/evaluate.py
.\.venv\Scripts\python.exe rag/retrieval.py "Chordoma thường xuất hiện ở vùng nào?" --top-k 5
```

Lần xây lại tiếp theo dùng `rag/build_index.py` không có `--download-model`. Mô hình `intfloat/multilingual-e5-small` được ghim theo revision trong `rag/retrieval.py`; vector dùng chuẩn `passage: ` cho đoạn và `query: ` cho câu hỏi, chuẩn hóa L2 rồi xếp hạng theo tích vô hướng. Chỉ mục NumPy lưu tại máy và đủ nhỏ cho kho 489 đoạn. Không có dịch vụ embedding bên ngoài khi truy vấn.

`rag/index/manifest.json` lưu mã băm corpus, source lock, trọng số embedding, ma trận vector và thứ tự chunk. Khi corpus, nguồn, mô hình hoặc vector đổi, truy xuất dừng và yêu cầu xây lại chỉ mục. Kết quả truy xuất kèm `source_id`, tiêu đề, URL, mục, thời điểm truy cập, mã băm nguồn và đoạn văn để gắn citation thật ở giai đoạn chatbot.

## Đánh giá và giới hạn

`rag/evaluate.py` đo khả năng trả về đúng **nguồn và mục** trong top-k trên 10 câu tiếng Việt có đáp án; hai câu ngoài phạm vi đo tỷ lệ không trả kết quả khi đặt ngưỡng. Bộ 12 câu này nhỏ và được soạn từ nguồn hiện có, vì vậy điểm số chỉ là smoke test retrieval, chưa đại diện cho người dùng thật. Score embedding là độ tương đồng, không phải xác suất đúng hay bằng chứng lâm sàng. Cần kiểm định ngưỡng trên tập dev độc lập trước khi dùng fallback tự động; không chọn ngưỡng theo chính bộ câu hỏi báo cáo rồi coi là đã tổng quát hóa.

Các nhãn u chưa có nguồn chuyên biệt trong kho vẫn là khoảng trống nội dung. Trước khi chatbot ở **giai đoạn 12** được đưa vào sử dụng, cần mở rộng nguồn, kiểm tra citation, xử lý câu hỏi thiếu bằng chứng và kiểm thử từ chối chẩn đoán hoặc phác đồ cá nhân hóa. Có thể dựng nguyên mẫu chatbot ngay sau khi retrieval hoạt động, nhưng nghiệm thu giai đoạn 12 phụ thuộc các kiểm thử đó và rà soát chuyên môn.

## Completion Note — Giai đoạn 11

- Ngày: 27/10/2026.
- Mô hình: `intfloat/multilingual-e5-small`, revision được ghim trong `rag/retrieval.py`; checksum trọng số và vector trong `rag/index/manifest.json`.
- Vector store: NumPy cục bộ, 489 đoạn × 384 chiều; top-k mặc định 5.
- Kết quả: source+section recall@5 = **0,60** (6/10), MRR@5 = **0,417**. Hai câu ngoài phạm vi đều trả về 5 đoạn khi chưa đặt ngưỡng (negative abstention = 0/2).
- Citation kỹ thuật: truy ngược được URL/mục/mã băm cho từng hit; đã kiểm thử việc từ chối chỉ mục cũ khi source lock đổi.
- Trạng thái: **BLOCKED để dùng làm nền cho câu trả lời y khoa của chatbot**. Cần cải thiện truy xuất, mở rộng bộ đánh giá và thiết kế bộ kiểm tra phạm vi/từ chối riêng. Điểm tương đồng của hai câu ngoài phạm vi khoảng 0,80, chồng lên điểm của câu có đáp án; chưa có ngưỡng an toàn được chứng minh.
