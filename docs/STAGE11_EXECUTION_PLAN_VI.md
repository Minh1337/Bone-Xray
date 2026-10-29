# Kế hoạch thực thi Giai đoạn 11

**Định hướng hiện hành theo người dùng:** [báo cáo học tập thực nghiệm, không cung cấp cho bác sĩ/người bệnh](reference/STAGE11_USER_STATED_EDUCATIONAL_SCOPE_20261029.md). Ưu tiên hoàn thiện retrieval/provenance/đánh giá kỹ thuật và báo cáo trung thực. [Bảng đối chiếu 7 bước kỹ thuật](reference/STAGE11_EDUCATIONAL_COMPLETION_MATRIX_20261029.md) nêu phần đã thực hiện và khoảng trống ngưỡng similarity, có [thăm dò 28 câu đã xem](reference/stage11_similarity_overlap_probe_20261029.json). Các công việc clinical release trong kế hoạch bên dưới chỉ áp dụng nếu intended use đổi; register G1–G7 vẫn OPEN cho tới khi phạm vi và điều kiện áp dụng được owner/reviewer quyết định. [Record và regression mới](reference/stage11_educational_scope_verification_20261029.json): 94 passed/132 subtests; structural QA 24/24 refs, 15 cohort leads, 0/7 gate CLOSED.

**Tiếp tục theo yêu cầu người dùng ngày 29/10/2026.** Lệnh tạm dừng ghi dưới đây là snapshot lịch sử. [Mốc phát triển chatbot](reference/STAGE11_CHATBOT_READINESS_VI.md) tách prototype tra cứu nội bộ khỏi generator và diễn giải ca thực. Giữ 0/7 gate đóng, `answer_ready=false`.

**Cập nhật:** 29/10/2026  
**Trạng thái tại điểm dừng lịch sử:** tạm dừng theo yêu cầu người dùng ngày 29/10/2026; chuẩn bị kỹ thuật workspace lúc đó ước lượng khoảng **85%**; nghiệm thu độc lập **0/7 cổng đóng**; `answer_ready=false`. Người dùng đã yêu cầu tiếp tục sau đó; trạng thái hiện hành nằm ở hai đoạn đầu tài liệu. Xem [bàn giao cho Codex khác](../START_HERE_NEXT_CODEX_VI.md).

## Mục tiêu

Hoàn thiện lớp retrieval/evidence của BoneScope ở chế độ research-only; giữ nguồn và quyền sử dụng có provenance; cải thiện routing và khả năng abstain bằng tập dev được ghi rõ nguồn gốc; bảo đảm audit/replay/regression có thể tái lập; chuẩn bị hồ sơ để reviewer độc lập nghiệm thu. Không dùng điểm dev đã xem như bằng chứng độc lập. Không bật sinh câu trả lời lâm sàng hoặc `answer_ready=true` khi chưa đủ chứng cứ và chữ ký có thẩm quyền.

## Đã hoàn thành trong workspace

- Corpus text-only có **22 nguồn/794 chunk**; index **794×384**. Nguồn tibia 2025 CC BY 4.0 được lưu payload, kiểm parser/license và ghi hash cùng giới hạn phạm vi trong [ingestion record](reference/stage11_tibia_source_ingestion_20261029.json).
- Bundle đối chiếu gồm 16 report; audit provenance PASS trên 10 evaluation datasets và 22 source caches; deterministic replay PASS **16/16**, 0 preflight mismatch. Xem [audit](reference/stage11_integrity_audit_20261029_tibia_source_v1.json) và [replay](reference/stage11_replay_20261029_tibia_source_v1.json).
- Follow-up privacy minimization: tên file uploader không còn được persist trong bản ghi mới; API test dùng filename giả định danh và xác nhận chỉ còn `uploaded-image.png`. Bản ghi cũ, hash/metadata/comments, WAL/backup và host chưa được đánh giá; G6 vẫn OPEN. [Test record](reference/stage11_test_run_20261029_privacy_filename_minimization_full.json).
- Full software regression vừa chạy lại: **87 passed/132 subtests**, một Starlette deprecation warning; [run record mới nhất với code/data hashes](reference/stage11_test_run_20261029_postdocs_full.json). Đây là kiểm tra phần mềm, không phải nghiệm thu y khoa.
- Re-run audit offline mới nhất PASS cho 22 nguồn/794 chunk, index 794×384; deterministic replay PASS 16/16, zero preflight mismatch. [Audit record](reference/stage11_integrity_audit_20261029_workspace_recheck_v1.json) · [replay record](reference/stage11_replay_20261029_workspace_recheck_v1.json).
- Probe retrieval tibia đạt Recall@5 3/3, MRR@5 0.444 nhưng chỉ là ba positive do agent soạn/in-sample, không có negatives hoặc reviewer labels. Corpus growth làm metric đổi ở 4/16 reports; expansion dev Recall@5 và tập V2 test đã xem giảm. Không tune trên test. Chi tiết trong [ingestion/comparison](reference/stage11_tibia_source_ingestion_20261029.json).
- Đã thêm route ưu tiên mềm cho cue rõ `aneurysmal bone cyst`/`nang xuong phinh mach` tới review Cureus CC BY 4.0, `preferred_count=3`. Chọn trên expansion dev đã xem để phục hồi chunk vàng c10: Recall@5 0.955→1.000, MRR 0.644→0.689, negative abstention 3/3; 7 dev datasets còn lại không đổi. Full 16-report bundle chỉ expansion dev đổi metric, test đã xem không đổi. Đây là dev optimization, không phải independent evidence; xem [experiment record](reference/stage11_cureus_abc_route_dev_experiment_20261029.json), [bundle manifest](reference/stage11_policy_rerun_20261029_cureus_abcrouting_v1/manifest.json), [audit](reference/stage11_integrity_audit_20261029_cureus_abcrouting_v1.json), [replay](reference/stage11_replay_20261029_cureus_abcrouting_v1.json) và [full regression](reference/stage11_test_run_20261029_cureus_abcrouting_full.json).
- Link QA mới nhất: **566** local file links trong 30 tài liệu Markdown dưới `docs/`, 0 đích thiếu; cohort register 14 dòng/8 cột; gate register 7 dòng/8 cột. `git diff --check` không có lỗi whitespace ngoài cảnh báo chuẩn hóa LF/CRLF.
- Structural QA riêng xác nhận **7/7 gate OPEN**, **15/15** cohort candidate có đủ trường, và **23/23** artifact được liệt kê trong gate register hiện tồn tại; G4 đã liên kết hồ sơ C12–C15 và literature screen; G5 có 5 prompt hazard sơ bộ, gồm freshness/context/provenance RAG, chưa chấm rating hoặc ký. SHA-256 từng artifact được lưu tại [gate/cohort QA record](reference/stage11_gate_cohort_register_qa_20261029_v4.json). Đây chỉ là tính toàn vẹn/cross-reference, không phải xác nhận nội dung hoặc đóng gate.
- Read-only provenance recheck khớp SHA-256 corpus, source lock, retrieval config, index manifest, evaluator/policy với audit/bundle; 16/16 report và dataset files, replay cùng fingerprint regression record cũng khớp. Sau đó offline audit **PASS**, replay **16/16 PASS** và full regression **87/132 PASS** trên code/data state hiện tại; chỉ có cập nhật tài liệu sau lần chạy regression. Xem [technical-state QA](reference/stage11_current_technical_state_qa_20261029.json) và [latest run record](reference/stage11_test_run_20261029_postdocs_full.json).
- Recheck bốn nguồn OFD/adamantinoma từ PubMed/PMC/publisher: không đổi corpus; hai CC BY-NC-ND bị loại, một review CC-BY chờ toàn văn/phiên bản license, một case report CC BY chưa thêm vì không có gap retrieval đã chứng minh. [Rights recheck](reference/stage11_ofd_adamantinoma_source_rights_recheck_20261029_v2.json) · [evidence review](reference/stage11_online_evidence_review_20261028.md).
- Checkpoint mới nhất: [`checkpoints/20261029_093707/project_snapshot.zip`](../checkpoints/20261029_093707/project_snapshot.zip), 836 files / 164,803,676 uncompressed bytes, ZIP SHA-256 `61775e31dd4d0d31ac44448896d76a0d3967be02eccd6e428d43a6414bbde604`; verifier PASS, 836 files/CRC PASS. Snapshot có regression 87/132, audit/replay mới nhất, báo cáo cập nhật, goal/progress, register G4 15 ứng viên, 23 prepared-artifact references, hồ sơ C12–C15, rights-chain review, portal scan và regulatory review. Xem [checkpoint note](STAGE11_CHECKPOINT_LATEST.md).

## Cổng nghiệm thu và việc phải làm

Trạng thái chi tiết chuẩn tắc nằm trong [acceptance gate register](reference/stage11_acceptance_gate_status_20261029.csv). Các mục sau đều **OPEN**; biểu mẫu và runbook đã chuẩn bị không được tính là bằng chứng đóng cổng.

| Cổng | Việc còn phải làm để đóng | Vai trò cần tham gia | Phụ thuộc | Trạng thái |
| --- | --- | --- | --- | --- |
| G1 — Intended use và scope | Owner khóa mục đích sử dụng riêng cho classifier ảnh, text RAG, lưu hồ sơ ca và deployment; reviewer đủ chuyên môn rà theo chức năng/jurisdiction; ký scope và giới hạn. | Product/project owner; regulatory, privacy, safety reviewers khi áp dụng | — | OPEN; chưa có chữ ký |
| G2 — Đánh giá mù độc lập | Chốt rubric/version, preregister câu hỏi và sampling; reviewer độc lập đủ chuyên môn gán nhãn mù; adjudicate bất đồng; khóa và ký release record trước khi mở kết quả. | Reviewer lâm sàng độc lập; adjudicator; custodian | G1 | OPEN; chưa có reviewer, blind sample hoặc labels |
| G3 — Hỗ trợ bằng chứng/citation entailment | Chấm claim/span–evidence về relevance, direct support, polarity, qualifiers và context trên protocol đóng băng; báo cáo disagreement/adjudication, false acceptance/refusal và abstention. | Reviewer evidence độc lập; RAG/evaluation lead | G1, G2 | OPEN; chưa có human labels; lexical gate không đo entailment |
| G4 — Quyền ảnh và độc lập cohort | Chỉ nhận cohort sau khi có image-level rights/DUA, stable patient/lesion/image manifest, reference standard/adjudication, audit overlap với BTXRD/checkpoint/pretraining và protocol endpoint. | Data custodian/steward; rightsholder; cohort auditor | G1 | OPEN; 15 leads đã sàng lọc, chưa có cohort đủ điều kiện |
| G5 — An toàn | Reviewer khóa intended-use-specific hazard/use-error analysis, severity/likelihood rationale, controls, residual risk và ký quyết định. | Clinical safety lead; reviewer lâm sàng độc lập | G1 | OPEN; hiện chỉ có guide/template/scenarios sơ bộ |
| G6 — Riêng tư và bảo mật | Rà dataflow và threat model của deployment thực tế; xác nhận access control, retention/deletion, incident response, verification và sign-off. | Privacy officer; security reviewer; system owner | G1 | OPEN; local review còn control chưa xử lý và chưa có approval |
| G7 — Pháp lý/quy định | Qualified reviewer/counsel đánh giá từng function, intended use và jurisdiction; ghi nghĩa vụ/pathway áp dụng, rationale và ký kết luận. | Regulatory reviewer/counsel; product owner | G1 | OPEN; mới có source map, chưa có kết luận áp dụng |



Lý do các gate vẫn OPEN và blocker theo từng vai trò được tách tại [gate closure blockers](reference/STAGE11_GATE_CLOSURE_BLOCKERS_VI.md).

## Thứ tự thực hiện

1. Owner hoàn tất G1, gồm intended use cho từng chức năng và jurisdiction mục tiêu; giữ research-only cho đến khi quyết định có chữ ký.
2. Sau khi G1 khóa, chỉ định reviewer/custodian độc lập và chốt protocol, sampling, rubric, quyền dữ liệu trước khi xem labels/kết quả; thực hiện G2 và G3 theo blind workflow.
3. Tiến hành G4 chỉ khi data custodian cung cấp rights chain, DUA, manifest và reference standard. Nếu không đủ patient IDs hoặc overlap evidence, giữ cohort ở `NOT ELIGIBLE / NOT EVALUABLE`.
4. Hoàn thành G5–G7 với reviewer đủ thẩm quyền theo deployment/intended use thực tế; tài liệu tham khảo và biểu mẫu không thay quyết định của họ.
5. Sau khi có evidence đủ điều kiện, chạy lại audit/replay/regression trên dữ liệu được phép; đóng từng gate trong register bằng artifact, ngày, reviewer/role và chữ ký. Chỉ khi cả 7 gate được đóng hợp lệ mới đánh giá lại readiness.

## Quy tắc tiếp tục

- Giữ benchmark dev, historical regression và blind evaluation thành các nhóm tách biệt; ghi rõ tập đã xem/in-sample và mọi metric giảm.
- Nguồn mới chỉ đưa vào corpus khi đã kiểm tra license/terms ở cấp payload và ghi attribution, hash, parser, ngày truy cập, scope/limitations; không suy quyền ảnh từ license bài báo.
- Không xóa hoặc ghi đè audit/replay/report lịch sử; tạo artifact mới có versioned name.
- Mỗi lần thay corpus/config/code phải tạo source lock và ghi hash, chạy phù hợp full regression, corpus/index audit, deterministic replay và cập nhật report/handoff/checkpoint.
- `answer_ready=false` cho tới khi acceptance evidence và qualified sign-off thực sự tồn tại; không tự ký hoặc điền thay reviewer.
