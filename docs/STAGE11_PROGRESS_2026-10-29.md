# Giai đoạn 11 — tiến độ và goal đang theo dõi

**Cập nhật:** 29/10/2026. Goal Codex hiện hành: **Hoàn thiện Giai đoạn 11 BoneScope** (đang active). Goal đã lưu kế hoạch đầy đủ: rà soát nguồn có quyền; cải thiện retrieval/routing/evidence bằng benchmark dev tách biệt; regression/audit/replay; báo cáo, provenance và checkpoint; giữ `answer_ready=false` cho đến khi đủ chứng cứ và ký duyệt độc lập.

## Tiến độ

- **Chuẩn bị kỹ thuật tại workspace: khoảng 85%.** Đây là ước lượng quản lý đã dùng trong status dự án, không phải KPI đo lường hay nghiệm thu.
- **Acceptance gates: 0/7 đóng (0%).** G1 intended use, G2 blind review/adjudication, G3 citation entailment, G4 cohort/image rights/overlap, G5 safety, G6 privacy/security, G7 legal/regulatory đều OPEN.
- **Trạng thái sản phẩm:** `answer_ready=false`; Giai đoạn 11 chưa nghiệm thu.
- **G4:** 15 cohort leads đã sàng lọc; chưa có cohort đủ điều kiện external test. C12 là TCIA QIN-SARCOMA (public/CC BY 4.0 theo collection page hiện hành, nhưng modality/disease/endpoint không khớp); C13 Gitto et al. có workbook nhỏ nhưng không có ảnh X-ray; C14 Frontiers có 11 ảnh, thiếu negative group và repository không ghi license; C15 IIEST chỉ được mô tả là 69 ảnh cancer trong bộ hỗn hợp 217 ảnh, chưa xác minh package, rights, reference standard hoặc overlap. Rà soát nguồn cũng phát hiện BTXRD lấy ảnh từ Radiopaedia/MedPix; một bài primary 2025 mô tả các nguồn này có quy trình license/request/approval riêng. Cần giữ rights-chain per-image/source-level unresolved, dù Figshare có dataset-level license. Không tải hoặc dùng các ảnh cohort này để đánh giá; xem [due diligence](reference/STAGE11_EXTERNAL_COHORT_DUE_DILIGENCE_VI.md), [online evidence review](reference/stage11_online_evidence_review_20261028.md), [C14 screen](reference/stage11_frontiers_11case_cohort_screen_20261029.json) và [C15 screen](reference/stage11_iiest_69case_cohort_screen_20261029.json).

> 85% chỉ mô tả mức chuẩn bị các artifact/kỹ thuật trong workspace. Nó không thể cộng/trung bình với 0/7 thành một tỷ lệ tổng có ý nghĩa. Nghiệm thu vẫn 0% theo số cổng đã đóng.

## Việc đã hoàn tất và được lưu

1. Corpus hiện ghi nhận 22 nguồn/794 chunk, index 794×384; current bundle có integrity audit PASS và deterministic replay PASS 16/16.
2. Regression phần mềm vừa chạy lại trên working tree hiện tại: **87 passed/132 subtests**, một deprecation warning; [run record và code/data hashes](reference/stage11_test_run_20261029_postdocs_full.json).
3. Quy trình và hồ sơ G1–G7, reviewer packet, sampling plan, privacy/safety/regulatory worksheets, source due diligence và external cohort register đã được tạo/lưu.
4. G4 register đã bổ sung C12 QIN-SARCOMA, C13 Gitto ACT/chondrosarcoma và C14 Frontiers 11-case series; lý do task mismatch, quyền, dữ liệu ảnh khả dụng và disposition có hồ sơ máy đọc được.
5. Gate/cohort register QA xác nhận 7 gate vẫn OPEN, đủ 15 candidate không có ô trống, và 23/23 artifact link trong gate register trỏ tới file tồn tại; G4 liên kết đủ hồ sơ C12–C15 cùng source screen. JSON QA ghi hash từng artifact. Đây là kiểm tra cấu trúc, không đóng gate hay xác minh tính hợp lệ lâm sàng/pháp lý.
6. G1 intended-use draft được đối chiếu thêm với API/UI: 22 metadata fields, input ảnh/softmax, prediction RAM 10 phút, lưu SQLite chỉ sau thao tác riêng, RAG text-only với `answer_ready=false`, launcher loopback và case router không có per-user auth. Đây là static code facts cần xác nhận trên release/runtime, không phải sign-off.
7. Read-only technical-state cross-check xác nhận hash của corpus/source lock/retrieval config/index/evaluator/policy khớp audit và bundle; 16/16 report files, 16/16 dataset files, replay rows và hai regression code fingerprints khớp artifact đã ghi. [Sau đó đã chạy lại offline audit PASS, replay PASS 16/16 và full regression 87/132](reference/stage11_test_run_20261029_postdocs_full.json).
8. G7/G6 nguồn Việt Nam được đối chiếu sâu hơn: Decision 33 health-list summary, Decree 142 Arts. 8–9, transition date, Luật PDP 91/2025, Nghị định 356/2025 (thay NĐ13), NĐ330/2026, NĐ363/2026, upcoming NĐ392/2026, Luật Dữ liệu 60/2024, 08/VBHN-BYT và Thông tư 24/2026 được ghi vào regulatory review; vẫn chưa có legal classification/opinion hoặc privacy sign-off.
9. G7 source inventory được chuẩn hóa thành [registry máy đọc được](reference/stage11_regulatory_source_register_20261029.json) gồm 11 văn bản, URL/metadata hiệu lực, trạng thái ngày rà soát, câu hỏi reviewer và giới hạn; hai văn bản có hiệu lực tương lai 11/11 và 15/11/2026 được đánh dấu cần đọc bản ký sau ngày hiệu lực. Đây là provenance/triage, không phải legal opinion. QA v4 xác nhận 23/23 gate artifact hash-match; 600 liên kết Markdown nội bộ/31 tài liệu không có đích thiếu. Checkpoint mới nhất [20261029_093707](../checkpoints/20261029_093707/project_snapshot.zip), 836 files, ZIP SHA-256 `61775e31dd4d0d31ac44448896d76a0d3967be02eccd6e428d43a6414bbde604`, verifier PASS.



Giải thích chi tiết lý do 0/7 và điều kiện/người chịu trách nhiệm cho từng cổng: [gate closure blockers](reference/STAGE11_GATE_CLOSURE_BLOCKERS_VI.md).

## Việc còn phải làm

1. Khóa intended use và jurisdiction theo từng chức năng; nhận sign-off owner/reviewer (G1).
2. Chốt protocol/rubric, chỉ định reviewer độc lập, chạy sampling mù, adjudicate và ký kết quả trước khi mở nhãn (G2).
3. Đánh giá claim-to-evidence support/entailment, polarity, qualifiers, false acceptance/refusal trên tập được reviewer gán nhãn; không dùng lexical checker thay entailment (G3).
4. Tìm cohort có quyền ảnh/data-use rõ, reference standard phù hợp, patient-level manifest và overlap audit; hoặc giữ G4 OPEN (G4).
5. Hoàn tất hazard/use-error review và residual-risk sign-off theo intended use (G5).
6. Rà dataflow/threat model, retention, access, deletion, logs/backups/runtime và nhận privacy/security sign-off (G6).
7. Nhận kết luận pháp lý/quy định từ reviewer đủ thẩm quyền theo function và jurisdiction (G7).
8. Khi có đủ bằng chứng được phép, cập nhật gate register; chạy lại phù hợp regression, corpus/index audit, replay; tạo checkpoint và cập nhật báo cáo/handoff.

## Artifacts chính

- [Execution plan](STAGE11_EXECUTION_PLAN_VI.md)
- [Handoff](STAGE11_HANDOFF_VI.md)
- [Project status](PROJECT_STATUS_VI.md)
- [Acceptance gate register](reference/stage11_acceptance_gate_status_20261029.csv)
- [External cohort screening register](reference/stage11_external_cohort_screening_register_20261029.csv)
- [QIN-SARCOMA machine-readable screen](reference/stage11_tcia_qin_sarcoma_screen_20261029.json)
- [Gitto cohort machine-readable screen](reference/stage11_gitto_chondrosarcoma_cohort_screen_20261029.json)
- [Public bone-tumor cohort literature screen](reference/stage11_public_bone_tumor_cohort_literature_check_20261029.json)
- [C14 Frontiers 11-case screen](reference/stage11_frontiers_11case_cohort_screen_20261029.json)
- [Gate/cohort register QA with file hashes](reference/stage11_gate_cohort_register_qa_20261029_v4.json)
- [Current technical-state provenance cross-check](reference/stage11_current_technical_state_qa_20261029.json)
- [Post-documentation full regression + audit/replay record](reference/stage11_test_run_20261029_postdocs_full.json)
- [QIN-SARCOMA due diligence](reference/STAGE11_EXTERNAL_COHORT_DUE_DILIGENCE_VI.md#sàng-lọc-bổ-sung--tcia-qin-sarcoma-29102026)

