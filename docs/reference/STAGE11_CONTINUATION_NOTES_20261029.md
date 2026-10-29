# Ghi chú tiếp tục BoneScope — 29/10/2026

## Tiếp nối corpus/retrieval — 29/10/2026

- Nguồn mới: Salmon et al. 2025, review tổn thương xương chày (PMC12123328, DOI 10.1016/j.ejro.2025.100653), trang PMC ghi CC BY 4.0. Tải JATS bằng kết nối mạng có kiểm soát; hash payload, parser identity/license và giới hạn scope ghi ở [ingestion record](stage11_tibia_source_ingestion_20261029.json). Text-only, figures/tables/references bị bỏ. Nguồn narrative, không systematic; không dùng để map BTXRD `osteofibroma`.
- Corpus dựng offline từ 22 nguồn: **794 chunk**; index rebuild **794×384** bằng model/revision đã pin. Bộ lọc section mới bỏ disclosure GenAI, funding, competing-interest; regression cho filter được thêm.
- Thêm [3-câu development probe](stage11_tibia_dysplasia_retrieval_dev_20261029.json) và report: Recall@5 3/3, MRR@5 0.444. Tự soạn sau khi đọc chính nguồn; không reviewer, negatives hoặc blind evidence.
- 16-report comparison: 4 reports có metric changes; expansion dev Recall@5 1.0→0.955; previously viewed `v2_test_regression` MRR@5 0.733→0.671; các thay đổi khác có cả tăng và giảm. Không tune config trên test. Chi tiết comparison nằm trong `stage11_policy_rerun_20261029_tibia_source_v1/comparison.json` và ingestion record.
- Audit PASS: 22 sources, 794 chunks, 10 evaluation JSON datasets, 794×384 index, 22/22 source caches, no errors. Audit đổi sang tự quét `evaluation*.json`; có regression test cho dataset mới không cần allowlist edit. Replay PASS 16/16, 0 mismatch. Full suite **85 passed/130 subtests**, một Starlette deprecation warning.
- Acceptance không đổi: **0/7 đóng**, `answer_ready=false`; chuẩn bị workspace vẫn khoảng 85% theo ước lượng quản lý.

## Trạng thái cần giữ

- Ước lượng phần chuẩn bị có thể làm trong workspace khoảng **85%** (ước lượng quản lý, không phải KPI đo chính thức); acceptance độc lập vẫn **0/7 cổng đóng**. Phần retrieval/pipeline có regression và artifact tái lập tốt hơn; Stage 11 **chưa nghiệm thu** do còn 7 cổng độc lập bên dưới. Giữ `answer_ready=false`.
- Checkpoint usage mới nhất lúc 01:40 ICT 29/10: cửa sổ 5 giờ đã dùng 90%, còn 10%; đã lưu tổng hợp tại checkpoint bên dưới. Usage là chỉ số tài khoản, không phải % tiến độ dự án.
- Người dùng yêu cầu chạy lại vào 03:00 ngày 29/10 theo giờ Asia/Bangkok. Heartbeat một lần đã được render thành suggested card vì scheduler yêu cầu `suggested_create` cho DTSTART/timezone neo cụ thể; activation chưa được xác minh, cần kiểm tra/accept card trong app trước khi tạo lịch khác. Mốc tương ứng 2026-10-29 03:00 ICT = 2026-10-28 20:00 UTC.

## Snapshot kỹ thuật cuối cùng

- Policy cuối hiện tại: `rag/policy.py`; config `rag/data/retrieval_config.json`. Cải thiện personal image routing cho câu kế tiếp dùng đại từ sau câu có bệnh nhân+modality, ảnh thu nhận tại phòng khám không nêu modality, bệnh nhân từ hospital/service và trẻ được chăm sóc. Có context-limited GCT alias qua MRI/bone imaging; từ viết tắt trơ vẫn out-of-scope. Chuyển alias sau các safety guards và bổ sung herbs/herbs-cure claim terms để không bypass guard. Thêm cortical destruction vào supported terms vì cụm này có trong registered corpus.
- Image-routing dev có **51 câu âm**, 51/51 được route đúng `insufficient_evidence` (negative abstention 51/51). Đây là agent-authored/in-sample/text-only, không phải estimate độc lập và không xử lý ảnh. Cumulative edge matrix riêng: **33/33** personal-image probes abstain cho specialist và **18/18** general-education controls ở trong scope. Probe bổ sung cuối gồm 5 ca cá nhân (5/5) và 2 control giáo dục (2/2), ghi tại `docs/reference/stage11_personal_image_routing_edge_probes_20261029_v5.json`.
- Full suite mới nhất: `python -m pytest api_tests rag/tests tests ui_tests -q` → **73 passed, 127 subtests passed, 0 failed**, một Starlette/AnyIO deprecation warning.
- Bundle hiện hành v7: `docs/reference/stage11_policy_rerun_20261029_personal_image_jats_wrapper_v7/`, 16 report. Manifest SHA-256 `3cde558d8350493aceb3fa836e683b7c7409d165676059f09ab0baf9e31fefa7`; comparison `cfa984d678f0ab9844192515b95ce0dfde2fb4b889325358d11f98894fae42ca`. So với base v6, image-routing report tăng 46→51 câu âm; accuracy/negative abstention vẫn 1.0 và 15 report khác không đổi. Tổng số mẫu routing tích lũy tăng 36→51 kể từ v2.
- Audit v7: `docs/reference/stage11_integrity_audit_20261029_personal_image_jats_wrapper_v7.json` PASS, 21 source caches, 759 chunks, 9 datasets, 16 reports, no errors. Replay v7: `docs/reference/stage11_replay_20261029_personal_image_jats_wrapper_v7.json` PASS 16/16, no preflight mismatches.
- Summary v7: `docs/reference/stage11_verification_summary_20261029_personal_image_jats_wrapper_v7.json`. Run record v7: `docs/reference/stage11_test_run_20261029_personal_image_jats_wrapper_v7.json`. Audit checks integrity/provenance only, not medical validity.
- GCT manual smoke-check (not scored) at `docs/reference/stage11_gct_policy_smokecheck_20261029.json`: two bone/imaging queries retrieved knee-review candidates, pituitary and herbal-cure queries were blocked, and one general query had an unrelated synovial candidate in top-3. Keep that as a future reviewer-labeled rank question; it is not an error-rate estimate or evidence that alias routing is clinically correct.
- Corpus unchanged: 21 registered sources /759 chunks. Do not ingest cached PMC11370983 mandibular ossifying fibroma case: it does not establish BTXRD `osteofibroma` label. Preserve source and parser record; retain mapping abstention. OFD review payload PMC10967096 remains separate.
- The user-authorized Save As target for the OFD review already existed in `rag/source_cache/`; SHA-256/size/PMCID/DOI were rechecked locally and `extract_jats_blocks` returned 54 blocks. It is the already-ingested PMC10967096 review (29 corpus chunks), not the PMC11370983 mandibular case. Do not overwrite or register a duplicate.
- Static privacy/security data-flow review is recorded at `docs/reference/STAGE11_LOCAL_PRIVACY_SECURITY_REVIEW_20261029.md`; no code changed. Keep deployment local-only and inputs synthetic/non-identifiable until authentication, authorization, encryption, retention/deletion, incident handling and legal/privacy review are resolved. Current FDA source review has been refreshed to the final CDS guidance issued 2026-01-29, superseding the 2026-01-06 issue.
- Reviewer packet now separates the declared current scope for the image classifier, text-only RAG retrieval, case-history storage and local launcher; it records inputs/outputs, limits and the signed function-specific intended-use details still needed before scope changes. It is a project record, not a legal intended-purpose determination.
- Closeout sequencing: reviewer packet now specifies the ordered dependencies—intended-use lock, privacy/regulatory review, image-rights/independence, specialist labels, blind protocol lock, frozen run, and signed gate decisions. This is a proposed runbook; no gate was closed.
- FDA source version was precision-checked against current FDA listings: final CDS guidance issued 2026-01-29 supersedes the 2026-01-06 issue. README, README_VI, project status, roadmap and handoff now point to current v7 and the source/privacy reviews; historical snapshots are labeled as historical.
- The v7 verification summary now pins SHA-256 for nine governance documents (reviewer packet, protocol, privacy review, continuation notes, status, handoff, roadmap, both READMEs); all pins verified against disk together with the source-review hash, OFD XML hash, v7 manifest/comparison and seven-open-gate state.
- Documentation validation: 21 Markdown files across docs and README were scanned for local link targets; all resolve. `git diff --check` has no whitespace errors (Git only reports existing LF→CRLF normalization advisories). No tests were rerun after documentation-only updates; the v7 recorded full suite remains 73 passed/127 subtests.
- Vietnam regulatory source screen now records AI Law 134/2025/QH15 (effective 2026-03-01), Decree 142/2026/NĐ-CP (effective 2026-05-01), and Decision 33/2026/QĐ-TTg issuing the high-risk AI list (effective 2026-08-15) from the Government portal. They are counsel-review leads only; inspect the full texts and annex against intended use, with no classification or legal interpretation made. The online evidence review also cites official Government records for medical-device and health/personal-data instruments.

## Bảy acceptance gates còn mở

1. Independent specialist review of source scope/answerability/evidence spans.
2. New blinded evaluation set with locked protocol.
3. Citation entailment validation.
4. Independent image cohort with usage rights, patient-level provenance and checkpoint-overlap audit.
5. Clinical safety review.
6. Privacy/security and health-data governance review before real-patient data/deployment.
7. Image-level upstream rights-chain verification for BTXRD Radiopaedia/MedPix materials before redistribution/commercial/derivative use.

Không tạo nhãn blind thay reviewer. Không tuyên bố clinical validity hoặc independent acceptance.

## Việc tiếp theo khi tiếp tục

1. Kiểm tra automation card lịch 03:00 ICT và usage hiện tại.
2. Đọc `docs/reference/stage11_verification_summary_20261029_personal_image_jats_wrapper_v7.json`, handoff hiện hành và `git status`; giữ toàn bộ thay đổi người dùng.
3. Rà code để đảm bảo GCT contextual path không bypass các policy guards; kiểm tra cả acronym ambiguous query và bilingual/case-bound controls. Chạy full suite sau mọi code change.
4. Tiếp tục online source due diligence, dùng primary sources và reusable license; chỉ cache/register khi quyền cụ thể của văn bản được xác minh và nội dung giải quyết coverage gap rõ ràng. Không kéo hình/third-party figures theo giấy phép bài báo.
5. Tăng chất lượng evidence entailment (không lexical allowlist-only): đề xuất gold span/qualifier rubric mới cho reviewer; không tự khẳng định đáp án. Bảo toàn current benchmark historic, tạo bundle mới mỗi lần đổi code/dataset.
6. Cập nhật report/hash và giữ `answer_ready=false`; ghi rõ nếu không thể đóng gate cần người ngoài.

## Lệnh tái lập đã dùng

```powershell
.\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q
.\.venv\Scripts\python.exe -m rag.build_evaluation_bundle --base docs/reference/stage11_policy_rerun_20261029_personal_image_jats_wrapper_v6 --output docs/reference/stage11_policy_rerun_20261029_personal_image_jats_wrapper_v7
.\.venv\Scripts\python.exe -m rag.audit --output docs/reference/stage11_integrity_audit_20261029_personal_image_jats_wrapper_v7.json
.\.venv\Scripts\python.exe -m rag.replay_reports --output docs/reference/stage11_replay_20261029_personal_image_jats_wrapper_v7.json
```

Bundle builder refuses overwrite; create the next version with a fresh directory.

## Sàng lọc nguồn mới — Frontiers exploratory series (29/10/2026)

- Bài Frontiers 2026 dẫn tới bộ 11 ảnh u dương tính (7 benign/4 malignant), do cộng tác viên cung cấp; nghiên cứu không re-annotate/adjudicate và không có ca bình thường. Tác giả không coi đây là external validation đại diện; không thể ước lượng specificity/false-positive.
- Repository GitHub yêu cầu trích dẫn nhưng trang đã xem không có data license hiển thị. Không tải/đọc ảnh, không ingest, và không tính là cohort đủ điều kiện. Cần rights/data-use grant, provenance + patient manifest, reference standard/adjudication, overlap audit và protocol khóa.
- Cập nhật tại `stage11_online_evidence_review_20261028.md`, `STAGE11_EXTERNAL_COHORT_DUE_DILIGENCE_VI.md` và reviewer packet; summary JSON ghi rõ trạng thái chờ xác minh.

## RAG grounding evidence — RaR 2025

RaR (npj Digital Medicine) chấm riêng relevance, consistency của câu trả lời với retrieved context và factual correctness; trên tập 65 câu độc lập, retrieval context liên quan 74% nhưng hallucination vẫn 9.2% khi context phù hợp. Dùng làm căn cứ giữ ba chiều đánh giá tách biệt trong rubric; không suy ra số liệu/ngưỡng của BoneScope. Link và diễn giải đã ghi trong online evidence review và reviewer packet.

### Evidence verifier miss analysis — 29/10/2026

- Thêm `tools/analyze_evidence_coverage.py` để chạy lại diagnostics trên reference chunks của bộ OFD dev; report `docs/reference/stage11_evidence_verifier_miss_analysis_20261029.json` pin SHA-256 dataset/corpus/config/mã.
- Kết quả: giữ 1/5 reference dương; 4 abstain. Ba do unknown Vietnamese tokens, một do literal `xi`; CT/MRI query duy nhất được giữ. Đây là lexical coverage diagnostic trên gold chunks đã xem, không phải retrieval rerun, independent test hay entailment.
- Không nới whitelist theo các câu đã xem. `--verify-evidence` tiếp tục disabled/opt-in đến khi có multilingual set mới được specialist gắn nhãn và review.

## Checkpoint tiếp tục lúc 01:40 ICT — 29/10/2026 (đạt mốc usage)

- Usage vừa đọc lúc 01:40:35 ICT: 90% đã dùng trong cửa sổ 5 giờ, còn 10%; đạt mốc người dùng yêu cầu để tổng hợp. Đây là mức usage tài khoản, không phải phần trăm hoàn thành dự án.
- Verification summary hiện hành được rà soát lại: 21 tệp Markdown, 0 liên kết cục bộ hỏng, 10 hash governance khớp; `answer_ready=false`, 7/7 acceptance gates còn mở. OFD cache parser xác nhận 54 khối, PMCID PMC10967096, DOI 10.1186/s13018-024-04682-3; 29 corpus chunks; SHA-256 `be017ab4d7546064180d5b00aece02264bb8d969d367c00233efd7b9a5ab1c7c`. Full test suite không chạy lại trong checkpoint này vì chỉ cập nhật tài liệu; lần chạy đã lưu vẫn là 73 passed/127 subtests.
- Sàng lọc cohort Frontiers/GitHub 11 ca: không eligible, không tải/ingest; bổ sung RaR 2025 như bằng chứng phương pháp; thêm review OFD/adamantinoma 2026 làm follow-up metadata-only vì publisher full text trả 502.
- Người dùng đã yêu cầu tiếp tục đúng 03:00 ICT hôm nay. Không tìm thấy automation đã lưu trong thư mục Codex; `automation_update` đã render một suggested one-time heartbeat card cho thread hiện tại với lịch DTSTART 2026-10-29 03:00 Asia/Bangkok và COUNT=1. Thử tạo ngay bị công cụ từ chối vì lịch neo múi giờ phải dùng suggested_create. Chưa có bằng chứng công cụ rằng card đã được chấp nhận/kích hoạt; khi tiếp quản phải kiểm tra trạng thái card, không tạo bản trùng. Nếu chưa active, card cần được xác nhận trong app; nếu mốc đã qua khi tiếp tục, chạy ngay.
- Giữ các thay đổi hiện có, không làm sạch/reset workspace. Ghi chú này và verification summary là điểm tiếp tục chính.

## Continuation checkpoint 01:44 ICT — lexical coverage diagnostic

- Usage đọc lúc 01:42 ICT: **92% đã dùng, còn 8%**. Mốc tổng hợp 10% còn lại đã lưu ở checkpoint trước; lần chạy này tiêu thụ thêm usage khi thêm chẩn đoán tái lập.
- Tạo `tools/analyze_evidence_coverage.py`, chạy hai lần cho cùng report SHA-256 `a4f844e10ceb71feee6e4d4dca4bc514c6eb7951ed4b3b0580f146ce4d0cae83`: trên 5 câu dương OFD đã xem, verifier lexical giữ 1/5 reference chunks và từ chối 4/5. Ba query dừng vì unknown Vietnamese tokens; một query thiếu literal `xi`; câu CT/MRI được giữ. Đây là checker trên gold chunks, không phải retrieval rerun hay benchmark mù. Không thay config/whitelist.
- Bằng chứng được thêm vào `docs/reference/EVIDENCE_CHECK_DESIGN_VI.md` và đầu handoff. Status, source/corpus/config/code hashes nằm trong JSON diagnostics; `answer_ready=false`, 7 cổng độc lập vẫn mở.
- 03:00 heartbeat vẫn chỉ là suggested card đã render; chưa xác minh active. Không tạo lịch thứ hai khi chưa kiểm tra/giải quyết card hiện có.

## Continuation checkpoint 01:47 ICT — cue trung tính song ngữ và evaluator v2

- Evidence config chỉ thêm `xap xi` và `approximately` thành cue trung tính, để cách diễn đạt xấp xỉ không bị đòi như literal evidence term. Thêm regression test tương ứng; targeted evidence tests 9/9 và full suite **74 passed, 127 subtests passed**, một cảnh báo deprecation. Run record: `stage11_test_run_20261029_evidence_neutral_phrases_v2.json`.
- Diagnostic chỉ trên năm gold reference chunks OFD tăng 1/5→2/5; ba câu vẫn bị unknown Vietnamese terms. Retrieval hybrid thực tế trên cùng dev tăng recall 1/5→2/5; positive abstention 4/5→3/5; negative abstention 2/2 giữ nguyên. Hai câu được qua là ofd01/ofd04; ba câu còn lại abstain. Dataset agent-authored/in-sample và frozen config mismatch; không chứng minh entailment, không bật checker.
- Reports: `stage11_evidence_verifier_miss_analysis_20261029_v2.json` và `stage11_evidence_verifier_ofd_actual_retrieval_20261029_v2.json`. Hash và run record được ghim trong verification summary. Bảy cổng vẫn mở; `answer_ready=false`.
- Usage gần nhất vừa đọc là 94% đã dùng, còn 6%; đã dừng công việc mở rộng để giữ checkpoint trong giới hạn người dùng đặt. Tiếp tục theo yêu cầu tới 10% còn lại nếu usage còn cho phép; schedule 03:00 chỉ ở trạng thái suggested/chưa xác minh active.


## Checkpoint 01:50 ICT — đồng bộ báo cáo trạng thái và usage

- Đồng bộ `docs/PROJECT_STATUS_VI.md` với full suite 74 passed/127 subtests và kết quả strict OFD v2 (2/5 recall; 3/5 positive abstention; negative 2/2). Nêu rõ estimate 85% chỉ là chuẩn bị kỹ thuật không trọng số; nghiệm thu độc lập 0/7, `answer_ready=false`.
- Kiểm tra `git diff --check`: không có lỗi whitespace; chỉ có cảnh báo Git LF→CRLF. Governance hashes 10/10 cập nhật/khớp.
- Usage gần nhất: **95% đã dùng, 5% còn lại**; ngưỡng 10% đã bị vượt. Chưa thực hiện thêm thay đổi kỹ thuật. Lịch 03:00 ICT chỉ ở trạng thái suggested card, chưa xác nhận active.


## Checkpoint 01:51 ICT — recheck nguồn cohort sơ cấp

- Tìm kiếm hẹp trên web và mở nguồn sơ cấp xác nhận không có cohort công khai mới đủ tiêu chuẩn. Bài Frontiers 2026 dùng BTXRD; test 750 ảnh là split theo image IDs, chưa chứng minh patient-level independence. Series ngoài 11 ảnh toàn tumor-positive, không có normal; tác giả không re-annotate/adjudicate và mô tả là exploratory. Không tải/cache/register ảnh.
- DeepTIRP là candidate ưu tiên để xin phép cho endpoint riêng tumor-vs-infection (423 external patients, histology/culture criteria), nhưng Zenodo access bị restricted, cần MTA/IRB, DOI bài dẫn (13858807) khác record tìm được (13858808), license không thấy. Chưa truy cập; không phải bộ 10-subtype eligible. Chi tiết và link sơ cấp ghi trong `stage11_online_evidence_review_20261028.md` và checklist cohort.
- Không đổi code/corpus; không chạy tests. Duy trì 7/7 acceptance gates mở và `answer_ready=false`.

## Checkpoint 01:52 ICT — usage sau recheck web

- Rà soát nguồn sơ cấp và lưu kết quả vào online evidence review; 23 Markdown files, 0 broken local links (scan sau khi bổ sung). Không tải hoặc đăng ký dữ liệu.
- Usage mới đọc: **96% đã dùng, 4% còn lại** trong cửa sổ 5 giờ. Mốc yêu cầu 10% đã vượt; dừng thay đổi mở rộng và lưu trạng thái.
- Thời điểm clock: 2026-10-28 18:50 UTC = 2026-10-29 01:50 ICT; mốc continuation 03:00 ICT chưa đến. Heartbeat vẫn chưa có xác nhận active.

- Đồng bộ README tiếng Anh/Việt: đổi full-suite mới nhất sang 74/127 subtests và liên kết run record v2; nhắc rõ Stage 11 chưa accepted. Thử đọc trạng thái lịch 03:00 trong UI thất bại do “Computer Use app approval timed out”; không click hay thay đổi app, nên activation tiếp tục chưa xác minh.

## Checkpoint 08:24 ICT — bundle v8 strict regression

- Tạo evaluation bundle v8 từ base v7 bằng lệnh `python -m rag.build_evaluation_bundle --base docs/reference/stage11_policy_rerun_20261029_personal_image_jats_wrapper_v7 --output docs/reference/stage11_policy_rerun_20261029_evidence_neutral_v8`. 16 report; manifest SHA-256 `2871ad8cc5b27f9dafa328123139a1b72624a7befaf61b7c4627cf0a0bff1f4a`; comparison chỉ đổi `osteofibrous_dysplasia_dev_strict.json`; 15 report metrics không đổi.
- Audit: PASS (21 cache, 759 chunks, 9 dataset, 16 report); replay: PASS 16/16, không preflight mismatch. Run record `stage11_evidence_neutral_bundle_v8_record_20261029.json`; summary mới `stage11_verification_summary_20261029_evidence_neutral_v8.json`.
- Năm strict datasets cộng gộp 4/40 dương qua (10%), 14/14 âm abstain. So với v7, thêm một OFD dương qua; vẫn 36/40 false abstention. Tập agent-authored/in-sample; filter lexical không chứng minh entailment, giữ disabled mặc định. Full suite tham chiếu gần nhất 74 passed/127 subtests; không chạy lại trong lượt bundle này.
- Đồng bộ README en/vi, project status và handoff sang v8; 7 acceptance gates mở và `answer_ready=false`. 23 Markdown links đã được kiểm ở checkpoint dưới; governance hashes sẽ được cập nhật vào verification summary sau thay đổi tài liệu.
- Usage sau reset gần nhất: 2% đã dùng, còn 98%; thời gian tại continuation khoảng 08:24 ICT (03:00 đã qua, nên chạy tiếp ngay). Lần đọc UI lịch 03:00 timeout ở app approval; chưa xác nhận scheduler active.

## Checkpoint 08:28 ICT — sensitivity của unknown-token gate

- Tạo `tools/compare_evidence_unknown_term_policy.py`; chỉ trong memory đổi `require_known_query_terms` true→false, production `rag/data/evidence_config.json` giữ nguyên. Chạy trên năm report strict của v8, cùng corpus/model/retrieval; report pin baseline manifest và source-code hashes.
- Candidate giữ 19/40 positive, so với 4/40 ở strict default; 14/14 negatives vẫn abstain trên chính các bộ đã xem. Theo nhóm: expansion 6/22, OFD 2/5, synovial source 3/4, synonym 1/1, V2 7/8. Candidate vẫn abstain 21/40 positives; không đo entailment. Đây là sensitivity analysis in-sample, không dùng làm bằng chứng an toàn; không thay config mặc định.
- Artifact `stage11_evidence_unknown_token_gate_experiment_20261029_v2.json`, SHA-256 `ce7b5dac6fa4ff45df7897d0b036701ce91a6b48f278ee408c388fd3925d33f5`; chi tiết vào EVIDENCE_CHECK_DESIGN, handoff, summary v8.
- Usage đọc lúc 08:27 ICT: 4% đã dùng / 96% còn lại trong cửa sổ mới. Mốc 03:00 ICT đã qua; tiếp tục ngay trong cửa sổ này. Không có reviewer, không đóng cổng; `answer_ready=false`.

- Utility v2 được chạy lại sau khi thêm kiểm tra đường dẫn nằm trong workspace, từ chối ghi đè report và xác nhận config production không bị thay. Candidate metrics giữ nguyên 19/40 positive, 14/14 negative abstention.

## Checkpoint 08:31 ICT — missing-term trace và lịch 13:30

- Report v3 bổ sung `evidence_check` per-question để nhóm missing terms trong thí nghiệm unknown-token gate. Khi bỏ hard reject unknown terms, remaining refusals thường do coverage literals/concepts chưa khớp: `tissue`, `symptoms`, `tests`, `don`, `cyst`, `cohort`, v.v. Không thêm alias từ các câu đã xem; cần reviewer xác nhận translation/qualifier map. Metrics không đổi so với v2: 19/40 positive candidate, 14/14 negative abstain; production config không đổi. SHA-256 report `5b1770a1ee2ba565152d9ff2d7933926cb77dbab73b6b5644724c3d0e49c604f`.
- Người dùng ủy quyền chạy tiếp tự động lúc 13:30 ICT ngày 29/10. `automation_update` tạo suggested one-time heartbeat card trong app, nhưng chưa có xác nhận activation. Card giữ prompt hiện hành; lần đọc UI trước đó đã timeout nên không thể chứng minh scheduler đã active.
- Usage lần đọc gần nhất 4% used/96% remaining trong window mới; mốc 13:30 chưa đến. Tiếp tục công việc cục bộ, cập nhật báo cáo và không claim Stage 11 accepted.

- Bổ sung `stage11_evidence_unknown_token_remaining_gap_analysis_20261029.json` (SHA-256 `59eab8e940b6d9f0632be91969a6808a56c7f51a715fc79b8138ae63244e057b`) để tổng hợp best-missing terms theo 21 câu dương còn abstain; chỉ một top candidate/câu, không phải exhaustive ontology. Đã liên kết vào Evidence Design và handoff.

## Checkpoint 08:44 ICT — source triage OFD và vận hành reviewer

- Tệp được người dùng cho phép tại `rag/source_cache/osteofibrous-dysplasia-review-2024.xml` đã có sẵn, nên giữ nguyên không ghi đè. Recheck SHA-256 `be017ab4d7546064180d5b00aece02264bb8d969d367c00233efd7b9a5ab1c7c`, PMCID PMC10967096, DOI 10.1186/s13018-024-04682-3; parser JATS chạy PASS (54 block: 22 heading, 32 paragraph), payload có liên kết CC BY 4.0 tường minh. Bản ghi hiện có cho thấy 29 chunk khớp corpus; không thay nội dung nguồn/corpus.
- Rà nguồn mới 2025–2026 bằng trang sơ cấp/abstract PubMed: Chen (50 ca, CC BY-NC-ND), Ramkumar (59 hồ sơ lịch sử, CC BY-NC-ND), Jayan pathology series (58 tumor; 12/58 chẩn đoán sửa sau review; radiology concordance 40% OFD/60% adamantinoma; không quan sát tiến triển trong follow-up biến thiên), Wu pediatric series (49 ca, abstract-only) và Hung genomic series (10 ca). AAOS OrthoInfo là nguồn giáo dục có bản quyền; Jayan & Rekhi review CC BY theo PubMed nhưng publisher trả 502. Các nguồn không đồng nhất, không giải quyết quan hệ tự nhiên hoặc BTXRD label; không có nguồn mới nào được cache/ingest.
- Tạo hồ sơ đối chiếu có cấu trúc `docs/reference/stage11_ofd_adamantinoma_source_triage_20261029.json`; cập nhật online evidence review, reviewer packet và handoff để phản ánh bất đồng, cỡ mẫu, license và giới hạn. Reviewer packet được đồng bộ sang v8; xác minh trực tiếp 17 hash dòng corpus/config/code/dataset trùng nội dung hiện hành, sửa bốn hash config/policy/audit/replay bị stale.
- Hoàn thiện quy trình CSV reviewer: enum `answerability`/`expected_status`, JSON-array fields, ghi risk kèm rationale và bắt buộc nhóm reviewer định nghĩa thang 1–4 trước khi khóa; mỗi reviewer giữ file độc lập và hash riêng, adjudication không ghi đè nhãn gốc. Cập nhật `STAGE11_INDEPENDENT_REVIEW_PROTOCOL_VI.md` và header `stage11_blind_label_template_20261028.csv`.
- Workspace changes ở checkpoint này là documentation/reviewer instruments; không đổi production code/config/corpus/gold và không chạy lại test suite. Link scan/gov hashes cần được refresh sau khi hoàn tất đợt cập nhật này. Giữ 7/7 acceptance gates mở, `answer_ready=false`.
- Usage đọc 08:44 ICT: 14% đã dùng, còn 86% trong cửa sổ 5 giờ; mục tiêu người dùng đặt là tiếp tục tới gần 10% còn lại. Lịch một lần 13:30 ICT hiện vẫn chỉ là suggested heartbeat card đã render, chưa xác minh active; không tạo lịch trùng.


## Checkpoint 09:00 ICT — tách phiếu nhãn khỏi adjudication

- Protocol reviewer hiện tách rõ population fully answerable, partially answerable, in-scope unanswerable và out-of-scope; bổ sung hai metric riêng để partial query được abstain thay vì xuất route có vẻ trả lời đủ. Bổ sung raw agreement, Cohen kappa/CI riêng theo answerability và expected_status; AC1 chỉ là sensitivity đã định trước. Ghi cách chọn Wilson 95% cho tỷ lệ query độc lập, bootstrap theo sampling cluster khi có paraphrase/case phụ thuộc; worksheet hiện có 16 metric với toàn bộ thresholds/CI/sign-off còn trống chờ reviewer khóa. Đồng bộ roadmap sang snapshot 29/10 v8 và index 759×384, giữ các snapshot cũ là lịch sử. Audit code cho thấy evaluator hiện suy Boolean answerable từ evidence/source và pool positive/negative; nhãn partial mới chưa được dùng để tính riêng. Đã ghi blocker này ở protocol, packet, handoff, project status và README: cần evaluator extension có regression hoặc analysis riêng đã lock/hash và fixture-check trước blind run; không đổi code hay chạy test. Bổ sung định trước cận CI để pass/stop, cách tính mẫu theo precision/cluster, rà overlap với mọi tập đã xem và neo confidence 1–5; acceptance worksheet có 16 metric, toàn bộ ngưỡng/CI/sign-off còn trống. Tách 2 cột adjudication khỏi file reviewer; tạo adjudication log riêng theo từng item/disagreement domain, giữ hash cả hai bản gốc và final rationale; link trong packet/handoff/README. Đã thử kích hoạt lịch một lần 13:30 bằng automation tool; app trả “Automation schedule has no future runs”. Hai lần trước chỉ tạo suggested card; không có lịch active được xác nhận, không thử tạo trùng. Tham khảo Cohen (1960), Gwet (2008), NIST Wilson-score guidance và nghiên cứu Radiology về dữ liệu phân cụm.
- Không sửa production, corpus, evaluation gold hay test; không chạy test vì thay đổi chỉ là protocol/worksheet. `answer_ready=false`; 7 cổng nghiệm thu còn mở.
- Usage tại 09:02 ICT: 22% đã dùng, 78% còn lại trong cửa sổ 5 giờ. Yêu cầu continuation 13:30 ICT vẫn chưa đến; trạng thái heartbeat suggested card chưa được xác minh active.


## Checkpoint 09:03 ICT — reviewer artifact integrity refresh

- Kiểm tra 22 Markdown và 280 liên kết nội bộ; không có link hỏng. CSV validation: sampling manifest 18 cột/0 dòng, independent label 17 cột/0 dòng (không có adjudication), adjudication log 18 cột/0 dòng, acceptance worksheet 16 metric rows; các trường threshold, denominator, CI/decision và sign-off vẫn để reviewer khóa trước unblinding. `query_clarity_stratum` không xuất hiện trong sampling manifest.
- Cập nhật governance hashes trong verification summary cho protocol, packet, handoff, README/status/roadmap, declaration, sampling manifest, label và adjudication templates. `git diff --check` sạch về whitespace; chỉ còn cảnh báo chuẩn hóa LF/CRLF. Không chạy tests, không đổi production code/config/corpus/gold.
- Usage mới nhất khi ghi checkpoint: 22% used / 78% còn; lịch tiếp tục một lần 13:30 ICT vẫn chưa được xác nhận active. `answer_ready=false`; 7 cổng vẫn mở.


## Checkpoint 09:06 ICT — pre-register sampling design

- Bổ sung `stage11_blind_sampling_plan_template_20261029.json`: khóa hash sampling frame, đơn vị/cụm, strata, inclusion/exclusion, dedup/overlap, design/cỡ mẫu, PRNG và seed commitment, script hash, custodian, phân quyền mapping, điều kiện unblinding, quản lý dữ liệu và deviation. Tất cả trường run-specific để null/empty; không có patient data. Liên kết từ protocol, reviewer packet, handoff và README_VI.
- QA lại 22 Markdown/284 local links (0 hỏng), JSON parse và 4 CSV schema pass; ngưỡng/cỡ mẫu/CI/sign-off vẫn để trống chờ reviewer. Hash governance được đồng bộ. Chỉ thay tài liệu/template; không chạy tests và không sửa code/config/corpus/gold.
- Usage tại checkpoint trước 09:06 ICT: 22% đã dùng/78% còn theo lần đọc gần nhất; `answer_ready=false`, 7 gate mở; lịch một lần 13:30 vẫn không xác nhận được active.

- Format review: sampling-plan file is explicitly a JSON record template, not a JSON Schema; metadata now labels it `pre_registration_template`.

## Checkpoint 09:05 ICT — sampling plan linked and hash-verified

- Đồng bộ sampling-plan template vào project status/roadmap; QA 22 Markdown, 286 local links, 0 broken. Tất cả 19 governance hashes khớp bytes; bốn CSV có cấu trúc hợp lệ và sampling-plan JSON parse được.
- `git diff --check` không có whitespace error; chỉ cảnh báo LF/CRLF của Git trên các tệp đã sửa. Không chạy tests, không sửa production code/config/corpus/gold. Usage lần đọc 09:05 ICT: 23% used/77% remaining. 7 gate vẫn mở, `answer_ready=false`; continuation một lần 13:30 vẫn không xác minh được active.


## Checkpoint 09:06 ICT — khóa xử lý missingness và emergency unblinding

- Bổ sung sampling-plan các trường bắt buộc pre-lock cho missing/unavailable items, replacement, early stop, cấm thay mẫu theo outcome và thẩm quyền/biên bản emergency unblinding. Quy tắc mặc định ghi rõ không thay mục dựa vào retrieval output, nhãn hoặc việc metric pass; protocol liên kết các quyết định này vào kế hoạch.
- Usage lần đọc 09:06 ICT: 24% used/76% remaining. Chỉ sửa governance docs/templates; không chạy tests, không đổi code/config/corpus/gold. 7 gate mở, `answer_ready=false`; lịch 13:30 vẫn chưa được xác minh active.


## Checkpoint 09:07 ICT — evaluator contract for partial labels

- Protocol bổ sung hợp đồng triển khai evaluator trước blind run có partial: kiểm nhãn ba mức và cặp status, population disjoint/OOS riêng, metric tử số-mẫu số theo population, giữ legacy report với nhãn suy diễn, fail-closed khi thiếu/không hợp lệ, fixture tính tay và yêu cầu giữ metrics cũ không đổi. Đây là spec, evaluator hiện chưa được sửa và blind run chưa thể dùng partial cho pass/fail.
- Rà lại primary-source metadata trên FDA, vanban.chinhphu.vn: 08/VBHN-BYT, TT 24/2026, Luật 91/2025, NĐ 356/2025 và NĐ 102/2025; hồ sơ đã ghi recheck trong verification summary. Không phát hiện điều cần sửa trong legal-lead wording; không đưa ra phân loại pháp lý.
- Usage lần đọc 09:07 ICT: 24% used/76% còn. Không sửa production, không chạy tests. 7 acceptance gates mở; `answer_ready=false`.


## Checkpoint 09:08 ICT — intended-use lock record

- Tạo `STAGE11_INTENDED_USE_LOCK_TEMPLATE_VI.md` để owner xác nhận snapshot theo chức năng (classifier, RAG, case storage/API, deployment), claims/forbidden uses, users, population, input/output, human oversight, jurisdictions, data governance và lifecycle. Phần scope lấy từ workspace đánh dấu cần owner xác nhận; trường future clinical/commercial để trống. Sign-off regulatory/privacy/safety tách riêng và không thay thế owner sign-off.
- Liên kết mẫu làm prerequisite trong reviewer protocol/packet, handoff, project status, roadmap và README_VI. Sampling plan giữ field intended-use hash. Chưa có chữ ký thật nên scope chưa khóa; 7 gates mở.
- Usage đọc lúc 09:08 ICT: 25% used / 75% còn. Không tests, không code/config/corpus/gold changes. Lịch 13:30 ICT chưa được xác minh active.


## Checkpoint 09:10 ICT — safety hazard-analysis preparation

- Tạo safety guide và CSV một hàng/ hazard scenario (header-only), phân biệt hazard/event sequence/hazardous situation/harm, controls/verification/residual risk, scale và acceptance rule do safety lead khóa; không điền rating hay ngưỡng sẵn. Thêm prompt cho classifier, RAG, workflow và data/privacy; prompt không phải finding.
- Nguồn sơ cấp rà 29/10: FDA final human-factors guidance tháng 8/2026, FDA software hazard-analysis guidance, FDA recognized ISO 14971 record (không quy định mức risk acceptability chung), và WHO report ethics oversight AI-health research tháng 7/2026. Online evidence review, reviewer packet, intended-use template, project status, roadmap, handoff và README_VI được đồng bộ.
- Usage lúc 09:10 ICT: 25% used/75% còn. Không tests/code/config/corpus/gold changes; clinical-safety gate vẫn mở đến khi safety lead điền/ký.


## Checkpoint 09:11 ICT — privacy/security closeout form

- Tạo [privacy/security gate template](STAGE11_PRIVACY_SECURITY_GATE_TEMPLATE_VI.md) gồm 16 miền evidence, từ purpose/controller/data map/minimization đến authz, encryption, temp/WAL/backup, retention, incident, third parties, residual risk và chữ ký theo thẩm quyền. Ghi rõ baseline static review có giới hạn và không thay runtime verification, pentest hay legal assessment.
- Liên kết vào acceptance gate, README_VI, status/roadmap/handoff. Phiếu để trống, chưa có reviewer/evidence thực nên gate vẫn open. Usage lúc 09:11 ICT: 26% used/74% còn. Không tests, code/config/corpus/gold changes.

- Discoverability: thêm Stage 11 governance links vào `README.md`, `docs/README.md` và reviewer packet để owner/reviewer tìm được các template trước khi ký; không thêm thông tin cá nhân hay dữ liệu người bệnh.

## Checkpoint 09:13 ICT — language/translation review criteria

- Protocol bổ sung kiểm soát query dịch/paraphrase: bảo toàn bản gốc, provenance người/quy trình dịch, rà phủ định/qualifier/tuổi/vị trí/subtype, cluster song ngữ để không thổi phồng N, báo riêng theo ngôn ngữ; nếu thiếu reviewer đủ năng lực thì ghi not evaluated. Sampling-plan ghi provenance/cluster rule trước khi mở kết quả.
- Handoff step numbering được rà sau khi thêm prerequisite privacy/safety. Usage 09:13 ICT: 27% used/73% remaining. Không tests, code/config/corpus/gold changes. Seven gates remain open; answer_ready=false.


## Checkpoint 09:14 ICT — inter-rater CI and navigation audit

- Đã ghi rõ CI của Cohen kappa cũng phải bootstrap theo cụm độc lập, tính lại ma trận/kappa mỗi lần; không coi bản dịch/paraphrase là N độc lập. Sampling plan yêu cầu provenance bản dịch, reviewer locale và cluster rule.
- Rà README tiếng Việt/README dự án/docs index/reviewer packet/handoff; sửa bước đánh số trùng, thêm đường vào intended-use, safety và privacy worksheets. Không thấy nội dung sign-off giả hoặc ngưỡng/rating tự đặt.
- Usage 09:14 ICT: 28% used/72% remaining. Chỉ docs/templates và governance hashes; không chạy tests, không đổi production/corpus/gold. 7/7 gate vẫn open và `answer_ready=false`.


## Checkpoint 09:15 ICT — report version discrepancy

- Đọc metadata/text của báo cáo DOCX: thực là v1.7, ngày 27/10/2026; docs index trước đây ghi nhầm v1.4. Đã sửa index thành snapshot lịch sử và trỏ sang status/handoff 29/10. Không chỉnh DOCX vì renderer trong skill documents không tìm thấy `soffice.exe`; không có bản LibreOffice bundled trong runtime đã nạp, nên không thể hoàn tất render-and-inspect bắt buộc.
- Usage 09:15 ICT: 29% used/71% còn. DOCX giữ nguyên; nội dung hiện hành ở README/status/handoff/verification summary. Không test, không đổi production/corpus/gold.


## Checkpoint 09:17 ICT — cập nhật FDA software-risk source

- Đối chiếu PDF chính thức FDA: bản final ngày 14/06/2023 *Content of Premarket Submissions for Device Software Functions* tuyên bố thay thế hướng dẫn tháng 05/2005. PDF mô tả risk-management file, hazards/misuse có thể dự đoán, chuỗi sự kiện tới hazardous situation, risk assessment, controls, residual-risk evaluation và traceability. Đã đổi trích dẫn lỗi thời ở safety guide và online evidence review sang bản 2023, ghi rõ đây là nonbinding method reference trong ngữ cảnh device-software submission; không suy ra BoneScope thuộc FDA hay đổi intended use/gate.
- Verification summary ghi nguồn mới, URL trang hướng dẫn và giới hạn phạm vi. Lần quét `docs/` không còn URL cũ `73065/download`; cả 2 văn bản safety hiện trỏ PDF 2023.
- Usage đọc 09:17 ICT: 29% used / 71% remaining; usage reset khoảng 13:18 ICT. Lịch continuation 13:30 chưa xác nhận active. Chỉ sửa nguồn và governance docs; không test hoặc sửa production/config/corpus/gold. `answer_ready=false`, 7 gate còn open.


## Checkpoint 09:19 ICT — handoff navigation and source/hash QA

- Rà chéo reviewer packet với handoff: register vẫn có đúng 7 cổng kết hợp 11/11A scope, mỗi cổng có evidence và reviewer; sửa danh sách hành động trong handoff bị trùng số 5 thành thứ tự 1–8. Đây là tám hành động triển khai của runbook, không đổi số lượng cổng hay trạng thái.
- Quét repo-wide Markdown: 47 file, 324 relative links, không có link gãy. Đã refresh SHA-256 cho safety guide, online evidence review, handoff và continuation note trong verification summary; xác minh 26/26 governance hashes khớp. `git diff --check` không có lỗi whitespace; chỉ còn cảnh báo chuẩn hóa LF/CRLF ở tệp trong working tree.
- Usage lần đọc gần nhất 09:17 ICT: 29% used /71% còn. Không chạy tests, không đổi production/config/corpus/gold. DOCX vẫn là snapshot lịch sử vì thiếu LibreOffice renderer; acceptance 0/7, `answer_ready=false`.


## Checkpoint 09:21 ICT — current Stage 11 report

- Tạo [báo cáo tổng hợp Giai đoạn 11 ngày 29/10](../reports/BAO_CAO_GIAI_DOAN_11_2026-10-29.md), có snapshot metrics/limits, bảng 7 gate, closeout evidence/reviewer, runbook theo dependency và nguồn FDA 2023. Ghi rõ 85% chỉ là ước lượng chuẩn bị không trọng số; mọi probe là in-sample/đã xem; evaluator partial, entailment, cohort ngoài, safety/privacy, intended-use và per-image upstream rights còn mở. Thêm vào docs index/project status; Word v1.7 giữ nguyên là snapshot lịch sử do không có LibreOffice renderer để làm render-and-verify.
- QA sau khi thêm báo cáo: 48 Markdown/346 relative links, 0 hỏng; 588 JSON trong `docs/` parse thành công. Bộ đếm tăng từ 344 sau khi thêm hai lối vào report trong README/README_VI; governance hash được refresh, không còn mismatch. Usage 09:20 ICT: 30% used /70% còn. Không tests/production/config/corpus/gold changes; 7 gate vẫn open.


## Checkpoint 09:30 ICT — evaluator tách answerability ba mức

- Sửa `rag/evaluate.py`: nếu có trường `answerability`, bắt buộc mọi item đều đủ label và `expected_status`, enum/cặp giá trị hợp lệ; partial→`insufficient_evidence`, full→`candidates_found`, unanswerable phân riêng in-scope/OOS. Nhãn fully answerable phải có evidence gold hoặc source+section target. Invalid/mixed schema fail-closed. Metrics legacy giữ nguyên cho dataset không có trường mới; ba mức báo riêng denominators/routing/raw hits/evidence theo population, OOS không vào negative-abstention in-scope. Không thay production retrieval/policy.
- Thêm regression fixture tổng hợp cho đủ bốn population, status mismatch, mixed/malformed/unhashable schema, thiếu gold cho full-answerable và dataset-wide mixed schema ngoài selected split; targeted evaluator **11 passed**, full suite **79 passed/127 subtests**, 0 failed, một Starlette deprecation warning. Ghi record tại [test run](stage11_test_run_20261029_partial_answerability_evaluator.json).
- Strict replay tool trên bundle lịch sử dừng đúng ở preflight vì manifest pin SHA evaluator cũ (0 report artifacts so sánh; bundle không bị sửa). Compatibility replay mới xác minh corpus/lock/config/index/policy/dataset/report hashes, chạy lại đủ 16 report và có 16/16 trường khớp sau khi loại timestamp và duy nhất `implementation_sha256.evaluate.py`; [compatibility record](stage11_legacy_report_compatibility_20261029.json).
- Đồng bộ protocol, reviewer packet, README/README_VI, project status, handoff và báo cáo Stage 11. Evaluator blocker đã đóng ở mức code; vẫn chưa có labels do reviewer, blind set hoặc adjudication. 7/7 gates còn Open, `answer_ready=false`. DOCX v1.7 vẫn snapshot lịch sử.
- Usage đọc 09:30 ICT: 35% used /65% remaining. Hiện không đổi corpus/gold/config/index; production policy không đổi.



## Checkpoint 09:39 ICT — source/hash QA refresh

- Đối chiếu lại link và JSON sau các sửa nguồn FDA/RaR: 28 tệp Markdown hiện có trong workspace, 358 link nội bộ, 0 đích file bị gãy; 591 JSON trong `docs/` parse được. 4 fragment heading bị heuristic giản lược đánh dấu để lưu ý, không tính là link file hỏng; cần kiểm slug thủ công nếu phát hiện điều hướng lỗi. Sáu CSV stage11 template/header đều có row width nhất quán. `git diff --check` không báo lỗi; chỉ có cảnh báo line-ending LF/CRLF.
- Tìm thấy một số hash ở verification summary còn trỏ revision cũ của test_evaluation/test_evidence/test_retrieval và online evidence review. Đã tính lại các SHA hiện hành và sẽ đồng bộ toàn bộ 30 governance artifact entry. FDA 2023 PDF là nguồn thiết bị-phần mềm không ràng buộc, chỉ làm ngữ cảnh phương pháp; không đưa ra kết luận regulatory cho BoneScope.
- Recheck usage 09:38 ICT: 39% used /61% remaining. Ghi nhận bộ evaluator target 11/11, full suite 79/79 tests (127 subtests), 0 fail; chỉ là regression software, không thay thế nhãn reviewer/bộ mù. Acceptance gates vẫn 0/7 đóng, `answer_ready=false`; báo cáo DOCX v1.7 giữ trạng thái lịch sử.


### 09:44 ICT QA correction

- Đã kiểm tra fragment bằng slug heading Unicode/duplicate-aware thay vì heuristic sơ bộ. Tìm thấy và sửa đúng một link thực sự sai trong `docs/PROJECT_STATUS_VI.md`: anchor đã transliterate chữ có dấu sang ASCII; nay trùng GitHub heading slug tiếng Việt. Quét lại xác nhận **359 relative links, 4 markdown anchor links, 0 đích tệp/heading bị gãy**. Bốn cảnh báo anchor trước đó đều được kiểm lại, không phải bốn lỗi. Dòng full-suite 74/74 còn sót trong reviewer packet/project status đã được thay bằng 79/79, giữ run record cũ ở nhãn lịch sử.


## Checkpoint 09:45 ICT — cập nhật nghiên cứu VLM/RAG bone-tumor 2026

- Rà soát bài JMIR AI xuất bản 21/09/2026, Shi & Tong, DOI 10.2196/99757/PMCID PMC13639421. Ghi vào online evidence review/reviewer packet/report: cohort đơn trung tâm 42 ca biopsy-confirmed u/u giả u, ảnh smartphone chụp PACS qua X-ray/CT/MRI; 3–5 lát/ca do một chuyên gia chọn; 1 Qwen3-VL 32B Thinking Q4, 2×2 persona × RAG; radiologist top-1 12/42→6/42 (29%→14%; P=.03), không thay đổi có ý nghĩa ở persona orthopedic-oncologist. Tác giả nêu thiếu clean-image control/blinded comparator, chọn lát không mù/độc lập và không multiplicity correction.
- Disposition: hazard-identification literature only, không phải acceptance-threshold hay hiệu quả BoneScope; không phải external test cho classifier vì modality, model, prompt, endpoint và cohort khác, chỉ ca tumor/tumor-like, không có ảnh thường. Bài ghi dataset không public vì privacy/data protection, có thể yêu cầu sau institutional/ethics approval, có phụ lục ảnh nhưng quyền từng ảnh/data-use authority/overlap chưa được xác minh. Không tải hoặc ingest.
- Người đánh giá cần đưa tín hiệu này vào rubric RAG/false reassurance/diagnostic-shift như scenario định tính; không quy kết quan hệ nhân quả hay chuyển số liệu sang BoneScope. Source review: https://ai.jmir.org/2026/1/e99757.


### 09:46 ICT — cohort due-diligence register and final link pass

- Thêm nghiên cứu Shi/Tong vào checklist cohort ảnh tách khỏi các nguồn external-test tiềm năng: appendix có ảnh nhưng full dataset bị giới hạn theo privacy/institutional data protection; khác modality/model/endpoint, ca positive-only; dùng làm risk literature, không eligible classifier external test. Chưa download, request hay đăng ký dữ liệu.
- Chạy slug-aware Markdown scanner: 28 Markdown, 361 relative links, 5 section anchors, 0 đích hỏng; 591 docs JSON parse, 0 lỗi; 6 Stage 11 CSV template có row-width nhất quán. `git diff --check` PASS, còn cảnh báo line-ending normalization. Các sửa trong lượt này chỉ thuộc documentation/governance; không thay evaluator, production, corpus, config, gold, index hoặc test.
- Usage đọc 09:46 ICT: 42% used /58% remaining. Hồ sơ mới nhất đã cập nhật nghiên cứu JMIR AI 2026, nhưng 7 gate vẫn Open và `answer_ready=false`.


### 09:47 ICT — safety guide hazard context and documentation QA

- Safety-review guide now links the JMIR AI 2026 bone-tumor VLM/RAG study as a qualitative hazard-identification prompt only; no rating or risk conclusion is assigned. Cohort due-diligence checklist separately marks it not eligible for the BoneScope classifier external test; source review records the conflicting practical boundary: public CC BY article/supplement appendices versus full dataset's privacy/institutional access restriction. No image download or ingestion.
- Full slug-aware link QA after these edits: 28 Markdown files, 362 local links including six section anchors, zero broken targets; 591 docs JSON parse, no errors. Six Stage 11 CSV templates remain rectangular. Prior `git diff --check` PASS had only LF/CRLF notices; latest edit is Markdown-only. Usage at 09:46 ICT: 43% used/57% remaining.

### 09:50 ICT — STARD-AI published-guideline crosswalk

- Rechecked the 2025 Nature Medicine version and 2026 author correction: STARD-AI is finalized (40 items; 4 modified, 14 new); the correction only adds an omitted steering-committee member. Verified the relevant numbered data/fairness/availability/audit items against the primary article and accepted manuscript.
- Added a Vietnamese applicability crosswalk for diagnostic-accuracy studies of the BoneScope image classifier and linked it from the independent-review protocol, reviewer packet, online evidence review, and current Stage 11 report. Explicitly excludes retrieval-only RAG metrics; no study checklist is marked complete and no gate status changes.
- Usage at 09:50 ICT: 44% used/56% remaining. Documentation/research only; no code, corpus, gold data or test run.
- Verified the accepted manuscript's repository license is CC BY and created a 48-row response CSV (40 numbered items including subitems) from the source text, with attribution/license/change note repeated in each data row and reviewer status/evidence fields left blank. Linked the template in protocol, source review, crosswalk and report; this blank checklist is not reviewer evidence or author endorsement. Usage read 09:53 ICT: 45% used/55% remaining. No gate was closed.
- Indexed the crosswalk/template in the central docs README and Vietnamese README; added a conditional handoff step for classifier diagnostic-accuracy reporting, keeping gate/control distinction and RAG exclusion clear. Latest link QA after all additions: 29 Markdown, 378 local links, six anchors, zero broken; 591 docs JSON valid; seven rectangular CSV templates (checklist is 48 data rows ×12 columns). Usage read 09:54 ICT: 46% used/54% remaining. No code/test changes.
- Independent targeted search found Büyüktoka et al., *Diagnostic and Interventional Radiology* 2026, DOI 10.4274/dir.2026.263945, comparing five MLLMs on the same 3,746-image BTXRD source. Recorded the 100 prompt-pilot exclusion, 3,646 analysis records, class-wise false-positive/malignant-miss pattern, same-source/non-external disposition and CC BY-NC 4.0 article terms. Added to source review, cohort due-diligence exclusion, safety guide, reviewer gate and current report; no images accessed. The source itself reports under TRIPOD-LLM; STARD-AI's stated applicability to diagnostic LLM classification is kept as a checklist-selection note, not criticism. Usage read 09:57 ICT: 48% used/52% remaining. No model/data/test change.
- A separate search surfaced Huang/Yao/Li et al. 2024 publisher abstract: 2,127-case, six-facility database and binary X-ray system, but no direct download/license/patient-level split/reference-standard details in the accessible record; partial author/site/time overlap with BTXRD makes independence unresolved, not disproved. Added a bounded “literature lead only” disposition to source review, due-diligence table, reviewer packet and report. No contact, access, download or reuse. Usage remained 48% used/52% remaining at 09:58 ICT.
- Current full link/structure QA after those source updates: 29 Markdown, 382 local links including 9 heading anchors, 0 broken; 591 docs JSON parse, 0 errors; seven rectangular Stage 11 CSVs including the blank 48-row STARD-AI template; all checked markdown table blocks in reviewer packet and cohort due-diligence retain consistent row width. Verification summary holds 32 refreshed governance hashes. `git diff --check` PASS with only LF/CRLF normalization advisories. No tests rerun or clinical/patient images accessed.
- Added a concise current-source disposition to the top-level project status so the latest Stage 11 evidence is visible without opening the long chronology. Usage read 10:00 ICT: 50% used/50% remaining. The independent gates and `answer_ready=false` remain unchanged.
- **10:09 ICT source follow-up:** official Journal of Clinical Radiology issue index exposes the Huang/Yao/Li 2024 Chinese abstract: 2,127 cases, six facilities, 2013–2022, X-ray/CT/MRI, binary X-ray AUC 0.8499. Official BTXRD data descriptor confirms Yao Shunhan and Yuanxiang Huang are coauthors and Center 1 collection spans 2013-07 to 2023-07; shared authors + overlapping window elevate lineage due diligence but do not prove case/image overlap or independence. “Open-source” does not establish image reuse rights. Added this candidate to the structured cohort register and updated due diligence, online review, reviewer packet, report, status and handoff; no contact/access/download/ingestion.
- Added the publisher-indexed 2026 DeepSeek-R1-0528/Bone-RADS feasibility study as future generative risk-output literature only. Abstract-visible fields describe clinical/history/radiology/pathology inputs and risk-category/diagnosis outputs; sample, detailed performance, data-rights and protocol remain unverified because article page text renders as placeholders. Updated online review, hazard guide, reviewer packet, current report and structured evidence summary. Not evidence for retrieval-only RAG or BoneScope performance.
- Documentation QA after these additions: 29 Markdown, 390 local links including 11 section anchors, 0 broken; 591 docs JSON parsed, 0 errors; 7 Stage 11 CSVs rectangular, including STARD-AI checklist 48×12. `git diff --check` passed; output only has LF/CRLF normalization notices. Usage read 10:09 ICT: 54% used/46% remaining. No tests rerun; no code, model, corpus, gold, index or patient-image changes. Seven gates remain open, `answer_ready=false`.


## Checkpoint 10:16 ICT — KJR 2026 full-text human-factors review

- Đã đọc publisher full text KJR 2026, bổ sung cohort/method/results/limitations vào source review và structured summary; ghi rõ pipeline dùng báo cáo cấu trúc + complaint text, không nhận pixel theo workflow mô tả. 217 ca reader evaluation, ba radiologist MSK; quan sát automation bias theo kinh nghiệm. Đây là hazard lead cho generator tương lai, không phải retrieval-RAG/BoneScope performance hay external cohort. Không lấy/download/request dataset hoặc ảnh.
- Đồng bộ safety guide, reviewer packet, STARD-AI crosswalk, báo cáo Stage 11, project status và các governance hashes; cập nhật QA tiếp sau. Không sửa code/model/corpus/gold/index; không chạy tests. 7/7 gates open; answer_ready=false.
- Usage lần đọc gần nhất: 57% used /43% remaining (2026-10-29 10:16 ICT). Mục tiêu tiếp tục đến gần 10% remaining.


## Checkpoint 10:20 ICT — LLM reporting-guideline scope clarified

- Kiểm tra publisher sources: MI-CLEAR-LLM 2025 update có 8 nhóm mục cho healthcare LLM accuracy; FLAIR 2026 có 32 mục/6 nhóm radiology reporting. Đã thêm scope disposition trong online evidence review, crosswalk, Stage 11 report, handoff và reviewer packet: dùng cho study LLM/generator tương lai, không phải retrieval/entailment/abstention validation và không thay blind protocol/gates.
- Đọc chi tiết KJR harm/subgroup tables: 20 Top-1 harm cases, 8 downgrade malignant/intermediate-to-benign; 11/20 ở reader ít kinh nghiệm nhất; low-frequency n=64/217, Gemini Top-1 68.6% vs 49.0%, Top-3 93.2% vs 65.6%. Ghi đầy đủ nhưng không dùng như BoneScope rates/thresholds.
- QA: 25 Markdown/345 local links/18 heading anchors/0 broken; 591 JSON/0 errors; 7 CSV rectangular; git diff --check pass (newline warnings only). No tests rerun. Usage last read 59% used/41% remaining. 7 gates open; answer_ready=false.


## Source-status correction and literature checkpoint — 10:20 ICT, supersedes partial 10:09 note

- Note 10:09 nói số liệu Bone-RADS/DeepSeek chưa verified do page rendering hạn chế đã được supersede: publisher English abstract được mở sau đó, xác nhận n=511, sensitivity 0.876 (95% CI 0.829-0.924), specificity 0.699 (0.644-0.754), AUC 0.788 (0.751-0.824), 306 direct histology matches, 84 additional differential matches, 121 with none; 41/275 benign/malignant mismatches theo exclusions abstract. Unresolved: pathology có bị prompt leakage không, pixel input, rights, blinding, overlap/training contamination. Vẫn literature lead, không phải BoneScope evidence.
- Sau đó bổ sung KJR full-text reader study và MI-CLEAR-LLM/FLAIR reporting scopes; tiếp tục thêm JMIR 2026 scoping review về 157 generative healthcare RAG/GraphRAG studies. Review report retrieval-layer evaluation 29.9%, fine-grained evidence verification 14.0%, citation/source correctness 7.6%, formal safety 28.7%; review excludes retrieval-only systems, nên dùng chỉ cho taxonomy/rationale, không benchmark BoneScope.
- KJR paper exact hazard report: 20 Top-1 harm events, 8 malignant/intermediate-to-benign downgrades, 11/20 in the least experienced reader; low-frequency cases 64/217 and Gemini Top-1 68.6% vs 49.0%, Top-3 93.2% vs 65.6%. These are study-specific, not BoneScope rates or thresholds.


## Checkpoint 10:20 ICT — JMIR RAG review and roadmap reconciliation

- Added Zhao et al. JMIR 2026 scoping review (157 generative healthcare RAG/GraphRAG studies, search through 14 May 2026, OSF-registered PRISMA-ScR) as methodological rationale. Since eligibility requires generated outputs, it excludes retrieval-only systems; no benchmark/quality inference transferred. Added distinct evaluation coverage rates and caveats to source review, reviewer packet, report, handoff, project status and structured summary.
- Reconciled roadmap Stage 11 current-status line: latest recorded software regression is 79 passed/127 subtests (evaluator 11); earlier 74-test snapshot is superseded. No tests rerun.
- Latest QA: 25 Markdown/349 local links/21 heading anchors/0 broken; 591 JSON/0 errors; 7 CSV rectangular; git diff --check pass with 9 line-ending notices. Usage last read 59% used/41% remaining. No code/model/corpus/gold/index changes; all 7 acceptance gates remain open and answer_ready=false.


## Checkpoint 10:26 ICT — Cell Reports Medicine review verified

- Publisher/PubMed source verified Yang et al. Cell Reports Medicine 2026, DOI 10.1016/j.xcrm.2026.102927: search period to 2025-07-01, 244 screened + 7 manually added = 251; 7/251 explicitly evaluate bias, 24/251 safety, 6/251 low-resource. RAG definition includes retrieval integrated into generated LLM output; retrieval-only is out of scope. Added exact denominator/search caveat to online source review and independent-review protocol, plus report/handoff summaries. Not a checklist or BoneScope benchmark.
- Clarified STARD-AI CSV count: 40 items, 48 response rows due subitems, plus header (49 total rows, 12 columns).
- Latest docs QA: 25 Markdown/350 local links/21 heading links/0 broken; 591 JSON/0 errors; 7 rectangular CSVs; git diff --check pass with 11 line-ending notices. Usage last read 63% used/37% remaining. Tests not rerun; gates 0/7 closed; answer_ready=false.


## Checkpoint 10:28 ICT — KJR pipeline and privacy scope detail

- Added publisher-verified KJR methods: GPT-5.4, Gemini 3.1 Pro, Claude Opus 4.6, Llama 4 Maverick; temperature 0/vendor default; each Top-3 and justification shown with weighted 2/1.5/1 aggregate. Reader diagnosis codes/prior reports hidden; nonreader prepared worklist; supplement contains third-party privacy detail but that supplement was not reviewed, so no privacy-safeguard conclusion. Updated source review, reviewer packet, safety guide.
- QA remains 25 Markdown/350 local links/21 anchors/0 broken; 591 JSON/0 errors; 7 rectangular CSVs including STARD-AI 49x12; `git diff --check` 0 exit, 11 newline notices. Usage last read 63% used/37% remaining. No tests rerun.

## Checkpoint 10:37 ICT — regulatory source refresh and OFD payload/parser verification

- Added [regulatory applicability review](STAGE11_REGULATORY_APPLICABILITY_REVIEW_VI.md): function-specific reviewer handoff, current-vs-draft source status, current FDA cybersecurity guidance (February 2026 supersedes June 2025; QMSR effective 2026-02-02), final IMDRF GMLP N88:2025, FDA AI lifecycle draft vs PCCP final, and a seven-step closeout checklist. Linked from source review, intended-use lock, independent protocol, reviewer packet, privacy/security review, handoff, report, project status and docs index. No legal classification made.
- User authorized saving the OFD review XML to `rag/source_cache/osteofibrous-dysplasia-review-2024.xml`. On inspection the exact file was already present (last modified 2026-10-28) and registered in corpus/source metadata; I preserved it. It is 143,385 bytes, SHA-256 `be017ab4d7546064180d5b00aece02264bb8d969d367c00233efd7b9a5ab1c7c`; JATS identifies PMCID PMC10967096, PMID 38539216, DOI 10.1186/s13018-024-04682-3, title and explicit CC BY 4.0. `rag.build_corpus.extract_jats_blocks` accepted it and `chunks_for` reproduces all 29 current corpus chunks exactly (IDs, source hash and text hashes); administrative/reference sections excluded. No cache/corpus changes. A fresh network fetch was blocked by OS egress restrictions; UI automation had stopped when it could not resolve the browser URL, so no claim of re-downloading in this turn.
- Docs QA after edits: 28 Markdown files, 417 local links, 21 section anchors, zero broken; 591 JSON parse, zero errors; 7 Stage 11 CSVs rectangular; all 33 governance hashes match. `git diff --check` exit 0, only existing LF/CRLF advisory output. No tests rerun; latest full-suite record remains 79 passed/127 subtests, evaluator 11/11 in its prior record.
- No production code, model, evaluation labels, test sets, index, patient data or image assets changed. All seven acceptance gates remain open (0/7 closed); `answer_ready=false`.

- Static implementation cross-check found one stale sentence in the current v8 structured summary claiming the evaluator could not separate `partially_answerable`; this is superseded by the implemented three-level schema and will be replaced with an explicit note that blind independent labels are still absent. `answer_ready` remains hard-coded false in retrieval output; no answer-generation endpoint surfaced in the scoped source scan.

### 10:48 ICT — TRIPOD+AI/TRIPOD-LLM scope audit

- Publisher/primary text checked for TRIPOD+AI (BMJ 2024; 27 main items/52 subitems) and TRIPOD-LLM (Nature Medicine; 19 main items with subitems and task/design modules). Clarified selection alongside STARD-AI by prespecified study aim/design, including possible overlap for future classifier or generator studies. Reporting guidelines are not appraisal/validation/approval tools and do not cover the current retrieval-only pipeline; RAG relevance, support, abstention and false routing remain under the separate blind protocol. Added scope language to crosswalk, source review, current report, handoff and project status; added both source records/disposition to v8 summary.
- Latest docs-only QA: 28 Markdown, 424 local links/21 heading anchors/0 broken; 591 docs JSON parsed/0 errors; 7 Stage 11 CSV templates rectangular; 33 governance hashes synchronized; `git diff --check` PASS with LF/CRLF advisories only. No tests rerun. Usage last read 67% used/33% remaining; all seven gates remain Open and `answer_ready=false`.

### Regulatory applicability refinement — Việt Nam

- Rechecked Government portal metadata and signed Decision 33/2026/QĐ-TTg (effective 2026-08-15) and Decree 142/2026. Clarified that sector-level healthcare listing does not itself classify BoneScope; reviewers must compare each frozen function against the annex entry conditions/exclusions, identify provider/deployer roles, and determine whether transition provisions apply to actual operating dates. No annex/legal classification is claimed. Added the concrete reviewer task to the regulatory checklist and current report.
- Follow-up docs QA and summary hashes are being refreshed after this source-status edit. No app/code/model/corpus/evaluation data changed; no tests rerun.

### Reporting guideline matrix and Vietnam applicability scope — 11:12 ICT

- Expanded the crosswalk to a compact decision table for TRIPOD+AI, TRIPOD-LLM, STARD-AI, MI-CLEAR-LLM/FLAIR and DECIDE-AI. Verified TRIPOD-LLM publication details (19 main items/50 subitems, 14/32 common items/subitems plus task/design-specific modules) and DECIDE-AI scope/count (27 items; early-stage live clinical evaluation). Added the selection logic to independent-review protocol and reviewer packet. Reporting aids do not replace study conduct, risk-of-bias, or clinical validation.
- Rechecked official Government portal and signed Decision 33 metadata; regulatory reviewer must inspect system-specific annex conditions/exclusions, provider/deployer roles and transition relevance. No legal classification is made. Current documentation QA: 28 Markdown, 426 local links/21 anchors/0 broken; 591 JSON/0 errors; 7 Stage 11 CSVs rectangular; 33 hashes synchronized. `git diff --check` PASS (exit 0; LF/CRLF advisories only). Latest usage read 72% used/28% remaining; 0/7 gates closed, `answer_ready=false`.

### CHART scope check — 11:32 ICT

- Checked the BMJ Medicine CHART statement and BMJ explanation/elaboration: 12 items/39 subitems for performance studies of generative chatbots that summarize clinical evidence or provide health advice. Added as a future generator/chatbot reporting aid to the selection matrix, protocol, reviewer packet context, handoff, report, project status and structured source record. Explicitly excludes current retrieval-only RAG; no answer generator exists. CANGARU was not promoted as a final guideline because the CHART source describes it as in development for medical writing.
- Documentation link/hash revalidation pending this edit; no production, model, corpus, label, or patient-data change. Tests not rerun; 0/7 acceptance gates closed.

### Trial and diagnostic-accuracy reporting guideline version check — 11:00 ICT

- Verified primary BMJ statements: CONSORT 2025 is a 30-item results-reporting checklist and supersedes CONSORT 2010; SPIRIT 2025 is a 34-item protocol checklist and supersedes SPIRIT 2013. The 2020 AI extensions contain 14 CONSORT-AI items and 15 SPIRIT-AI items, originally mapped to the prior core versions. Added explicit current-core and AI-extension rows to crosswalk/report/handoff/status and a scoped registry record; any future trial lead must reconcile the extensions with 2025 core and current journal instructions. No trial exists in present scope; none of these reporting aids is conduct or acceptance evidence.
- Documentation-only QA after edits: 30 Markdown files, 427 local links, 21 heading anchors, 0 broken; 591 docs JSON parse, 0 errors; 7 Stage 11 CSV templates rectangular; 35 governance artifact hashes synchronized; `git diff --check` PASS (LF/CRLF notices only). No tests rerun; `answer_ready=false`, gates 0/7 closed.
- Registry audit found STARD-AI had a crosswalk and checklist but no row in the structured reporting-standards inventory. Added its published 2025 diagnostic-accuracy scope, 40-item count, 2026 correction boundary and retrieval-only exclusion. No claim that the checklist was completed or endorsed by its authors.
- Checked the official SPIRIT–CONSORT extension directory: it identifies current 2025-core-based extensions separately from legacy-core extensions and presently lists SPIRIT-AI under SPIRIT 2013. Added this dated directory observation to the online evidence review, report, crosswalk and structured snapshot; a future trial lead must recheck the non-exhaustive directory and reconcile with the journal's live instructions.
- Final QA after all additions: 30 Markdown files, 427 local links, 21 heading anchors, 0 broken; 591 docs JSON parse, 0 errors; 7 Stage 11 CSV templates rectangular; 35 governance artifact hashes synchronized; `git diff --check` PASS (exit 0, only LF/CRLF advisories). No tests rerun; `answer_ready=false`, gates remain 0/7 closed.
- A subsequent source-precision correction narrowed the directory observation to SPIRIT-AI only; the CONSORT-AI claim now cites the BMJ 2020 statement's stated CONSORT 2010 base. Re-ran QA afterward with the same counts and zero errors; refreshed the online-source digest and all 35 governance hashes. No code/tests/data changed.
- Because bone-tumour trials may include young participants, checked the BMJ/SPIRIT–CONSORT primary 2026 paediatric extensions: SPIRIT-C adds 17 protocol items and CONSORT-C adds 13 results-reporting items for participants aged 0–19, alongside the 2025 core. Added a conditional crosswalk row, protocol/handoff/report/status notes, and two structured source records. They are explicitly future-trial-only; if the trial also tests an AI intervention, a methodologist must reconcile age- and AI-specific extensions with the current core/journal. No clinical trial or paediatric cohort is in the current retrieval-only validation scope.
- Latest docs-only QA after pediatric-extension update: 30 Markdown files / 429 local links / 21 anchors / 0 broken; 591 docs JSON / 0 parse errors; 7 Stage 11 CSV templates rectangular; 35 governance hashes refreshed; `git diff --check` exit 0 with LF/CRLF notices only. No tests rerun; `answer_ready=false`, gates 0/7 closed.
- Renamed the crosswalk's visible heading to reflect its expanded AI/healthcare reporting-guideline scope while keeping the established path so existing handoff links remain stable. No changes to clinical scope, code, corpus or evaluator. Latest usage read 79% used / 21% remaining; do not pad work to exhaust the limit.
- Checked the primary BMJ/EQUATOR GAMER statement (9 items): it is about transparent disclosure of GenAI use in medical research/manuscript preparation, not performance of the AI system under study. Added as a conditional disclosure aid to the crosswalk, online source review, current report and structured inventory. Explicitly do not declare a manuscript-level GAMER checklist completed for this internal project report.
- Updated both document indexes to show the crosswalk's broader scope. Final documentation QA after all current edits: 30 Markdown, 430 local links, 21 heading anchors, 0 broken; 591 documentation JSON/0 parse errors; 7 rectangular Stage 11 CSVs; 35 governance hashes synchronized; `git diff --check` exit 0 with line-ending notices only. No tests rerun; no code/corpus/model/index/patient-data change; gates remain 0/7 closed.
- Propagated the conditional GAMER disclosure note to the independent-review protocol, current project status and Stage 11 handoff so the crosswalk is discoverable for future manuscript planning. Documentation QA was rerun after this propagation.
- FLAIR primary article review added a currency limitation: the authors note the radiology-focused search may have omitted earlier work and that periodic updating may be needed. Added the caveat to crosswalk/report/online review and source inventory; no change to current retrieval-only applicability.
- Final docs-only QA after all current edits: counts and integrity hashes recorded in the verification summary; 7/7 acceptance gates remain Open, `answer_ready=false`. No tests rerun and no code, model, corpus, index or patient-data changes.
- Re-ran the packaged DOCX renderer in verbose mode for the historical Word snapshot; it failed before conversion because the required `soffice.exe` is absent from PATH/runtime. Removed the temporary QA directory and preserved the old DOCX; do not claim it was refreshed or visually verified. The Markdown report remains the current deliverable.
### 11:18 ICT — CLAIM 2024 reporting-scope completion

- Publisher/PMC/RSNA primary materials confirm CLAIM 2024 Update comprises 44 items and is a medical-imaging AI research reporting guideline; the 2024 article explicitly excludes radiomics/pathomics scope. Added CLAIM to the guideline-selection table and clarified modality vs aim/design selection alongside TRIPOD+AI (prediction-model development/evaluation) and STARD-AI (diagnostic accuracy vs reference standard).
- Synced concise scope language to the online evidence review, Stage 11 report, project status and handoff. CLAIM remains conditional on a separate image-classifier study; it does not apply to retrieval-only RAG and is not a quality appraisal, validation or acceptance gate. No code, model, corpus, labels, index, or patient images changed.
- Docs-only QA completed after the crosswalk sync: 30 Markdown files / 430 local links including 21 heading anchors / 0 broken; 591 docs JSON / 0 parse errors; seven Stage 11 CSV templates rectangular; 35 governance hashes synchronized; `git diff --check` exits 0 with repository LF/CRLF notices only. No tests rerun. External independent review, cohort/rights, clinical safety, privacy/security and legal sign-offs remain open; 7/7 acceptance gates stay Open and `answer_ready=false`.
### 11:25 ICT — Restricted Rambam cohort lead screened

- Primary JMI article / PMC and institutional author copy reviewed for Zimbalist et al. 2024. Reports 1,421 single-center radiographs (973 normal, 448 abnormal; 137 benign/311 malignant), age 5–40, and a patient-level split internal to the original study. Data are available on request, not as a public image download.
- Added as a restricted-access candidate to the due-diligence table, online source review, reviewer packet, project status and handoff. It may fit a future prespecified binary endpoint, but data-use authority/DUA, image rights, patient/image manifest and hash, reference-standard/adjudication details, and overlap with BoneScope checkpoint/pretraining remain unverified. It is not an eligible external test, not a 10-subtype cohort, and not evidence of independent validation. No data were downloaded and no external party was contacted.
- Candidate, source disposition and hashes are recorded in the evidence-neutral verification summary. Added a candidate-specific preflight that checks scope/labels first, then authority/DUA/image rights, then controlled transfer/manifest/hash/overlap only after approvals. Documentation-only QA after the update: 30 Markdown / 434 local links including 22 heading anchors / 0 broken; 591 JSON / 0 parse errors; 7 Stage 11 CSV templates rectangular; 35 governance hashes synchronized. No tests rerun. All seven acceptance gates remain Open and `answer_ready=false`; no patient/image data were accessed and no external party was contacted.

### 11:32 ICT — CLAIM 2026 explanation/elaboration source added

- Reviewed the RSNA-hosted CLAIM 2026 *Explanation, Elaboration and Examples* companion (Radiology: Artificial Intelligence 8:e260835). It elaborates the existing 44-item CLAIM 2024 Update with item intent and literature examples; it is not presented as a separate checklist or revision.
- Added the companion source to the reporting crosswalk, online evidence review and structured source inventory. It provides reviewers a current interpretation resource while keeping CLAIM conditional on a separate image-classifier study; retrieval-only RAG scope and all Stage 11 gates are unchanged.
- Final docs-only QA: 30 Markdown / 434 local links including 22 heading anchors / 0 broken; 591 docs JSON / 0 parse errors; 7 Stage 11 CSV templates rectangular; 35 governance hashes synchronized; `git diff --check` exit 0 with only repository LF/CRLF advisories. No tests rerun, code/model/corpus/index/patient data unchanged, 7/7 gates Open and `answer_ready=false`.


## Checkpoint luu tien trinh — 29/10/2026 13:39:42 ICT

Da luu [checkpoint moi nhat](../STAGE11_CHECKPOINT_LATEST.md) va ban ZIP trong `checkpoints/20261029_133942/`. Bundle continuation v2 da build 16/16 report; audit PASS, replay PASS 16/16; 0 report doi metrics so voi v8. Bundle v1 bi ngat va audit FAIL cua bundle mac dinh cu duoc giu de truy vet. Manifest checkpoint ghi hash hien tai, thay cho governance/doc hashes lich su v8 khi doi chieu workspace. Stage 11 chua nghiem thu: 7/7 gates Open, `answer_ready=false`; ~85% chi la uoc luong chuan bi cu.


### Unknown-token gate diagnostic — 29/10/2026

Chạy lại so sánh trên 5 strict reports của bundle continuation v2, chỉ tắt `require_known_query_terms` trong bộ nhớ. Trong 40 positive đã xem, 19 còn ứng viên (positive abstention 21/40 = 52,5%); 14/14 negative vẫn abstain, 0 false candidate accept. Đây vẫn là lexical coverage, không kiểm tra entailment; các tập in-sample nên không bật checker production. Cấu hình production không đổi. [Artifact và query-level kết quả](stage11_evidence_unknown_token_gate_experiment_20261029_continuation_v1.json).
