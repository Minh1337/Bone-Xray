# BoneScope — Hướng dẫn cài đặt và sử dụng trên Windows

BoneScope là ứng dụng chạy cục bộ để phân tích ảnh X-quang u xương bằng mô hình
học sâu, quản lý ca bằng SQLite và thử nghiệm truy xuất tài liệu RAG. Đây là
phần mềm nghiên cứu; kết quả không thay thế chẩn đoán hoặc tư vấn y khoa.

## 1. Lấy mã nguồn

Cài Git và Python **3.11 64-bit**, sau đó chạy:

```powershell
git clone https://github.com/Minh1337/Bone-Xray.git
cd Bone-Xray
```

Model chính nằm trong `model/`. Nếu checkout chỉ có Git LFS pointer, cài Git
LFS rồi tải dữ liệu:

```powershell
git lfs install
git lfs pull
```

Không commit hoặc chia sẻ ảnh bệnh nhân, database runtime, log hay secret.

## 2. Cài môi trường

Nhấp đúp `01_setup.bat`. Script tạo `.venv`, cài PyTorch và dependency mô hình,
chạy kiểm tra cơ bản rồi tạo log trong `logs/`.

Tiếp theo nhấp đúp `04_setup_api.bat` để cài FastAPI và chạy test API.
Không copy `.venv` từ máy khác; hãy tạo lại trên từng máy để tránh lỗi đường dẫn,
Python và phần cứng.

## 3. Khởi động ứng dụng

Nhấp đúp `07_start_ui.bat`, sau đó mở:

```text
http://127.0.0.1:8000/
```

API có tài liệu tại `http://127.0.0.1:8000/docs`. Không chạy
`05_start_api.bat` đồng thời với `07_start_ui.bat` vì cả hai dùng cổng 8000.
Nếu cần chạy API riêng, dùng `05_start_api.bat`.

## 4. Phân tích và lưu ca

1. Chọn ảnh JPG, PNG, BMP hoặc TIFF, tối đa 30 MiB.
2. Nạp `cases.json` hoặc một object metadata JSON đủ 22 trường.
3. Bảo đảm ảnh và metadata thuộc cùng một ca; không tự đoán các trường còn thiếu.
4. Bấm **Phân tích ảnh** để xem Top-1, Top-3 và điểm của 10 lớp.
5. Bấm **Lưu ca vào lịch sử** nếu muốn lưu kết quả vào SQLite.

Các trang chính:

- `/`: phân tích ảnh và metadata.
- `/history`: lịch sử ca đã lưu, lọc và phân trang.
- `/dashboard`: thống kê ca, hiệu chỉnh, nhận xét và thiết bị.
- `/case/{id}`: chi tiết ca, nhận xét và hiệu chỉnh nhãn độc lập.

Database `data/bonescope.db` được tạo tại máy và bị Git bỏ qua. Máy mới sẽ không
có lịch sử từ máy cũ. Nếu cần chuyển lịch sử, dừng ứng dụng rồi sao lưu/copy
database riêng; không đưa dữ liệu bệnh nhân lên repository công khai.

## 5. Tạo chỉ mục RAG cục bộ

RAG hiện mới có corpus, embedding, retrieval, đánh giá và chính sách routing;
**chưa có chatbot và chưa được nghiệm thu để trả lời y khoa**.

Cài dependency và tạo index lần đầu:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements_rag.txt
.\.venv\Scripts\python.exe rag\build_index.py --download-model
.\.venv\Scripts\python.exe rag\audit.py
.\.venv\Scripts\python.exe rag\evaluate.py
.\.venv\Scripts\python.exe rag\retrieval.py "Chordoma thường xuất hiện ở vùng nào?" --top-k 5
```

Corpus hiện gồm **794 đoạn từ 22 nguồn**: 13 mục NCI và 9 nguồn ngoài NCI. Mỗi nguồn có provenance/license/scope theo registry; C12 TCIA QIN-SARCOMA và C13 Gitto được rà soát nhưng không ingest hoặc dùng làm evaluation vì không khớp task hoặc thiếu ảnh/quyền dữ liệu. Xem [cohort register](docs/reference/stage11_external_cohort_screening_register_20261029.csv) và [status dự án](docs/PROJECT_STATUS_VI.md).
Các bảng và captions từ BioC của BSG/Cureus bị loại; xem căn cứ trong
[rà soát nguồn trực tuyến](docs/reference/stage11_online_evidence_review_20261028.md).
Các thư mục
`rag\index\`, `rag\models\` và `rag\source_cache\` được tạo/tải tại máy và bị
Git bỏ qua. Lần sau chỉ cần chạy `rag\build_index.py` nếu model embedding đã có.

Hai tùy chọn thử nghiệm không bật mặc định:

```powershell
.\.venv\Scripts\python.exe rag\retrieval.py "..." --rerank-concepts
.\.venv\Scripts\python.exe rag\retrieval.py "..." --verify-evidence
```

`--rerank-concepts` cần kiểm định thêm trên tập độc lập. Historical v8
`--verify-evidence` chỉ giữ 1/22 câu dương trên dev và 0/8 trên V2 đã xem, nên
không dùng cho người dùng cuối; lexical coverage không xác minh entailment.
Cả hai chế độ vẫn trả `answer_ready: false`. Xem [hướng dẫn RAG](docs/README.md)
và [bàn giao giai đoạn 11](docs/STAGE11_HANDOFF_VI.md).

Catalogue ảnh tham chiếu BTXRD Figshare (record gốc ghi CC BY 4.0) đã được tải
và tạo manifest, nhưng checkpoint hiện tại dùng BTXRD và thiếu image IDs theo
split nên không thể tuyên bố đánh giá độc lập trên bộ này. Terms upstream của
ảnh Radiopaedia/MedPix chưa được audit riêng theo ảnh. Xem
[hướng dẫn bộ ảnh](docs/guides/README_IMAGE_REFERENCE_VI.md) và
[trạng thái dự án](docs/PROJECT_STATUS_VI.md). G4 đã sàng lọc 15 cohort candidates;
chưa có cohort đủ điều kiện external test với quyền, reference standard, patient-level
provenance và overlap clearance. C12 TCIA QIN-SARCOMA không khớp modality/disease/
endpoint; C13 Gitto chỉ phát hành workbook radiomics, không có ảnh X-ray; C14 Frontiers
chỉ có 11 ca tumor-positive và repository không hiển thị data license; C15 IIEST là bộ
hỗn hợp 217 ảnh, trong đó 69 ảnh cancer-labelled, chưa xác minh package/quyền/overlap. Bone-CNN và
SKELEX dùng cùng BTXRD lineage, không phải cohort độc lập mới. Không có dữ liệu nào
được nhận hoặc dùng để đánh giá. Xem [register](docs/reference/stage11_external_cohort_screening_register_20261029.csv),
[C14 screen](docs/reference/stage11_frontiers_11case_cohort_screen_20261029.json),
[C15 screen](docs/reference/stage11_iiest_69case_cohort_screen_20261029.json) và
[due diligence](docs/reference/STAGE11_EXTERNAL_COHORT_DUE_DILIGENCE_VI.md).
Dùng [checklist thẩm định](docs/reference/STAGE11_EXTERNAL_COHORT_DUE_DILIGENCE_VI.md)
trước khi truy cập hoặc đánh giá nguồn mới.

Lệnh `rag\audit.py` kiểm tra tính toàn vẹn của source lock, corpus, gold evidence/citation và index. Kết quả PASS không xác minh độ đúng y khoa; `answer_ready` vẫn false.

## 6. Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q
```

Full suite vừa chạy lại: **87 passed/132 subtests**, một cảnh báo deprecation Starlette. Đây là regression phần mềm, không phải kiểm định độc lập hay lâm sàng. Xem [run record mới với code/data hashes](docs/reference/stage11_test_run_20261029_postdocs_full.json). Corpus 22 nguồn/794 chunk; [fresh integrity audit](docs/reference/stage11_integrity_audit_20261029_workspace_recheck_v1.json) PASS và [fresh replay](docs/reference/stage11_replay_20261029_workspace_recheck_v1.json) PASS 16/16. Một số dev/V2 đã xem; chưa có reviewer-labeled blind set hoặc citation-entailment adjudication. Giai đoạn 11 chưa nghiệm thu độc lập và `answer_ready=false`. Xem [progress note](docs/STAGE11_PROGRESS_2026-10-29.md) và [checkpoint](docs/STAGE11_CHECKPOINT_LATEST.md).

## 7. Tài liệu và giới hạn

- [README tổng quan](README.md)
- [Trạng thái dự án](docs/PROJECT_STATUS_VI.md)
- [Báo cáo tổng hợp Giai đoạn 11 — 29/10/2026](docs/reports/BAO_CAO_GIAI_DOAN_11_2026-10-29.md)
- [Lộ trình thực hiện](docs/LO_TRINH_THUC_HIEN_DU_AN_AI.md)
- [Hướng dẫn corpus RAG](docs/guides/README_RAG_CORPUS_VI.md)
- [Hướng dẫn index và retrieval](docs/guides/README_RAG_INDEX_VI.md)
- [Hệ quy chiếu ảnh X-quang](docs/guides/README_IMAGE_REFERENCE_VI.md)
- [Thiết kế kiểm tra bằng chứng](docs/reference/EVIDENCE_CHECK_DESIGN_VI.md)
- [Quy trình thẩm định độc lập Giai đoạn 11](docs/reference/STAGE11_INDEPENDENT_REVIEW_PROTOCOL_VI.md)
- [Crosswalk reporting guideline AI/y tế (trọng tâm STARD-AI)](docs/reference/STAGE11_STARD_AI_REPORTING_CROSSWALK_VI.md)
- [CSV checklist STARD-AI trắng, có attribution CC BY](docs/reference/stage11_stard_ai_reporting_checklist_template_20261029.csv)
- [Hồ sơ reviewer và snapshot hash Giai đoạn 11](docs/reference/STAGE11_REVIEWER_PACKET_VI.md)
- [Mẫu intended-use lock theo chức năng](docs/reference/STAGE11_INTENDED_USE_LOCK_TEMPLATE_VI.md)
- [Hướng dẫn safety review và hazard analysis](docs/reference/STAGE11_SAFETY_REVIEW_GUIDE_VI.md)
- [CSV trống cho hazard scenario](docs/reference/stage11_safety_hazard_analysis_template_20261029.csv)
- [Mẫu khai báo reviewer, độc lập và ký nhận](docs/reference/STAGE11_REVIEWER_DECLARATION_TEMPLATE_VI.md)
- [Mẫu adjudication log tách biệt, giữ nguyên hai bản nhãn gốc](docs/reference/stage11_adjudication_log_template_20261029.csv)
- [Kế hoạch khóa phương pháp và seed lấy mẫu mù](docs/reference/stage11_blind_sampling_plan_template_20261029.json)
- [Mẫu sampling manifest mù, giữ riêng source/cluster/overlap mapping](docs/reference/stage11_blind_sampling_manifest_template_20261029.csv)
- [Rà soát nguồn trực tuyến và regulatory](docs/reference/stage11_online_evidence_review_20261028.md)
- [Rà soát privacy/security cục bộ](docs/reference/STAGE11_LOCAL_PRIVACY_SECURITY_REVIEW_20261029.md)
- [Phiếu closeout privacy/security theo phạm vi](docs/reference/STAGE11_PRIVACY_SECURITY_GATE_TEMPLATE_VI.md)
- [Checklist cohort ảnh ngoài BTXRD](docs/reference/STAGE11_EXTERNAL_COHORT_DUE_DILIGENCE_VI.md)
- [CSV trống ghi nhận quyền tái sử dụng theo ảnh](docs/reference/stage11_image_rights_chain_template_20261028.csv)
- [Integrity audit hiện hành](docs/reference/stage11_integrity_audit_20261029_cureus_abcrouting_v1.json)
- [Deterministic replay hiện hành](docs/reference/stage11_replay_20261029_cureus_abcrouting_v1.json)
- [Full regression record mới nhất](docs/reference/stage11_test_run_20261029_postdocs_full.json)
- [Progress note Giai đoạn 11](docs/STAGE11_PROGRESS_2026-10-29.md)

Mô hình ảnh chưa được tuyên bố là có accuracy lâm sàng hoặc xác suất đã hiệu
chuẩn. RAG còn thiếu nguồn cho một số nhãn, chưa có chatbot, chưa có citation
generation và chưa được phép dùng để tự chẩn đoán hay đề xuất phác đồ.
