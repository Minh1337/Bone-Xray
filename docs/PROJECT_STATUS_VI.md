# Trạng thái dự án và ghi chú bàn giao

Cập nhật: **27/10/2026**. Đọc cùng [lộ trình](LO_TRINH_THUC_HIEN_DU_AN_AI.md) để phân biệt phần đã triển khai với tiêu chí nghiệm thu. Điểm tiếp tục chi tiết ở [bàn giao Giai đoạn 11](STAGE11_HANDOFF_VI.md). Kết quả kỹ thuật không thay thế đánh giá lâm sàng.

## Trạng thái hiện tại

| Phần | Hiện trạng | Giới hạn chính |
| --- | --- | --- |
| Phân tích ảnh, API, UI, SQLite | Ứng dụng local hỗ trợ dự đoán 10 lớp, lưu ca, lịch sử, ghi chú, hiệu chỉnh nhãn và dashboard. | Chưa chứng minh độ chính xác lâm sàng; `prediction_id` chỉ tồn tại trong bộ nhớ một tiến trình. |
| Giai đoạn 10 — kho nguồn | 12 trang NCI và 1 bài CC BY 4.0, tổng cộng 439 đoạn; từng đoạn có nguồn, quyền tái sử dụng, mục và mã băm. | Nguồn bổ sung chỉ là cohort 51 ca nang xương đơn độc vùng đầu trên xương cánh tay; không khái quát hóa điều trị. Thiếu nguồn cho nhiều nhãn và chưa có thẩm định chuyên môn. |
| Giai đoạn 11 — retrieval | Hybrid local, routing, rerank khái niệm opt-in, evaluator và citation metadata. | Chưa có kiểm tra đủ bằng chứng đáng tin cậy; chưa có tập kiểm định độc lập. `answer_ready` luôn `false`. |
| Giai đoạn 11A — ảnh tham chiếu | Đã tải/xác minh archive BTXRD; manifest 3.746 ảnh, SHA-256 từng ảnh, nhãn 10 lớp, 22 metadata, nhóm ảnh trùng và provenance. | Có 1 ảnh nhãn xung đột; không có patient/lesion IDs và không khôi phục được checkpoint split. Chỉ dùng làm catalogue/phát triển, không phải kiểm định độc lập. |
| Giai đoạn 12 — chatbot | Chưa triển khai API hội thoại, LLM hoặc UI chat. | Chỉ bắt đầu nguyên mẫu sau khi các giới hạn retrieval/evidence được xử lý và ghi rõ. |
| Giai đoạn 13 — bàn giao | Chưa nghiệm thu. | Còn đánh giá toàn diện, bảo mật và đóng gói. |

## Việc đã xác nhận trong lần tiếp tục này

- Giai đoạn 11A: tải bộ BTXRD chính thức Figshare CC BY 4.0, DOI `10.6084/m9.figshare.27865398.v1`. Archive 840,474,929 byte; MD5 khớp `59132a5036d030580ccade8add8f13df`, SHA-256 `e7c800c3b4e090262b160525a0765f9d93bcc53d639c03806a3ac47b0ded3373`.
- Catalogue có 3.746 ảnh: 1.879 no-tumor và 1.866 nhãn u hợp lệ; 1 ảnh `IMG001276.jpeg` có nhiều subtype cùng bật nên được giữ với trạng thái lỗi, không tự gán. Có 21 nhóm exact-duplicate gồm 42 ảnh; không có patient/lesion IDs, nên mọi partition vẫn `unassigned`. Toàn bộ dữ liệu tải và manifest nằm trong thư mục Git-ignore `data/external_datasets/BTXRD/`.
- Model checkpoint khai báo BTXRD là nguồn huấn luyện nhưng không lưu danh sách ID của train/validation/test. Vì vậy không báo cáo accuracy/benchmark trên BTXRD cho checkpoint hiện tại. Đánh giá ảnh chụp X-quang ngoài thực tế cần một nguồn khác độc lập, có quyền sử dụng và nhãn chuyên gia.
- Hướng dẫn quy trình: [bộ ảnh tham chiếu](guides/README_IMAGE_REFERENCE_VI.md); register nguồn: [btxrd_source_register.json](reference/btxrd_source_register.json); script tái tạo: `tools/prepare_btxrd_reference.py`.

- Repository ở nhánh `main`, `HEAD` là `d1ef896` (`Harden RAG policy routing and document handoff`); khi bắt đầu lượt, working tree sạch và nhánh local ahead `origin/main` 1 commit.
- Đọc README tiếng Anh/Việt và toàn bộ Markdown trong `docs/`, gồm roadmap, hướng dẫn, thiết kế evidence và handoff.
- Kiểm tra commit mới: policy routing đã được commit; ghi chú trước đó nói hai file policy/test chưa commit là lỗi thời.
- Chạy `\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q`: **36 passed, 28 subtests passed**, một cảnh báo deprecated từ Starlette.
- Khởi động API cục bộ trên CUDA và chạy `verify_api.py`: **API_LOCAL_PARITY_PASSED**, 3/3 ca khớp baseline local (sai lệch score tối đa 0, Top-1/metadata/hash ảnh khớp); metadata thiếu trả 422, ảnh hỏng trả 415. JSON đầy đủ tại `api_results/20261027_212246_844539/api_report.json` (runtime, Git bỏ qua).
- Phép parity này chỉ đối chiếu API với kết quả chạy local đã lưu; **không** xác minh parity với notebook và **không** chứng minh độ chính xác lâm sàng.
- Giai đoạn 11 vẫn chưa đạt điều kiện làm nền cho chatbot y khoa. Kết quả hybrid/rerank và thất bại của strict lexical filter được giữ nguyên như trong handoff và báo cáo thử nghiệm; các tập V2/V3 đã xem không phải kiểm định độc lập.

## Quyết định về mở rộng corpus

Đã bổ sung một bài từ Open Orthopaedics Journal theo CC BY 4.0; tác giả, nhà xuất bản, URL, giấy phép và phạm vi nghiên cứu nằm trong `rag/data/sources.json`, source lock và metadata từng đoạn. Corpus hiện **439 đoạn/13 nguồn**; hash `552eb6b313ca472dc92e5a20280dbf02a39d74091439a895099127c6b96c8dfb`. Khối metrics tải trang đã loại bỏ. Index 384 chiều đã được dựng lại. Nguồn AAOS không được ingest vì điều khoản tái sử dụng hạn chế; nguồn MDPI bị 403 và PMC gặp lỗi chứng thực TLS. Nhãn `osteofibroma` chưa được đối chiếu metadata dataset gốc/chuyên gia.

Đã mở rộng vocabulary retrieval lên `hybrid-v2` cho các cách gọi tiếng Việt/Anh của unicameral/simple bone cyst, humerus, cohort, cỡ mẫu và kết quả điều trị. Tập dev riêng 9 câu đạt **Recall@5 6/6**, từ chối/ngoài phạm vi **3/3**, routing accuracy 9/9. Tập do AI soạn và đã dùng để điều chỉnh; không phải test độc lập. V2 hồi quy (đã xem; dev n04 được gắn lại bằng chứng sau khi thêm nguồn) đạt Recall@5 **14/17**, MRR@5 **0,688**, từ chối câu âm 11/11; không phải kiểm định độc lập. `answer_ready` vẫn false.

Kiểm thử toàn dự án sau cập nhật vocabulary v2: **39 passed, 31 subtests passed**, một cảnh báo deprecation của Starlette. RAG riêng: **23 passed, 24 subtests passed**. Bộ dev mở rộng đạt 6/6 câu có đáp án trong top 5 và 3/3 câu âm được routing đúng; V2 regression đạt 14/17 câu dương, 11/11 câu âm. Các tập do AI soạn/đã xem, không phải kiểm định độc lập. `answer_ready=false`.

## Việc tiếp theo

1. Tìm nguồn ảnh khác BTXRD có quyền sử dụng, nhãn chuẩn được chuyên gia xác nhận và provenance đủ để đánh giá tổng quát.
2. Nếu nhà phát hành cung cấp, khôi phục danh sách split gốc của checkpoint; không suy ra split từ archive hiện tại.
3. Cần tập RAG độc lập do người khác soạn/rà soát; V2/V3 đã xem không phải kiểm định mới.
4. Xác minh `osteofibroma` với metadata dataset gốc/người chuyên môn; đánh giá kiểm tra đủ bằng chứng theo ngữ nghĩa.
5. Chỉ triển khai prototype chatbot sau khi retrieval/evidence được xác minh; không bật `answer_ready` hay tuyên bố độ chính xác ảnh trên BTXRD có overlap chưa loại trừ.

## Lệnh kiểm tra

```powershell
\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q
git diff --check
```

Đọc [README tiếng Việt](../README_VI.md), [hướng dẫn corpus](guides/README_RAG_CORPUS_VI.md), [hướng dẫn retrieval](guides/README_RAG_INDEX_VI.md) và [điểm bàn giao Giai đoạn 11](STAGE11_HANDOFF_VI.md) trước khi sửa pipeline. Các model/index/cache local bị Git bỏ qua; không xóa hoặc ghi đè bằng chứng trong `docs/reference/`.
