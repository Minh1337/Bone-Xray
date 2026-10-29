# Điểm tiếp tục giai đoạn 11

## Current handoff state — 29/10/2026

- The historic v8 metrics remain a baseline; corpus-expanded continuation is recorded separately. Latest full regression, after current read-only audit/replay, is **87 passed / 132 subtests**, one Starlette deprecation warning. [Latest run record with hashes](reference/stage11_test_run_20261029_postdocs_full.json).
- Latest offline audit: PASS on 22 sources/794 chunks, 10 evaluation sets, index 794×384, with no missing source cache. Latest deterministic replay: PASS, 16/16 reports matched, zero preflight mismatches. [Audit](reference/stage11_integrity_audit_20261029_workspace_recheck_v1.json) · [Replay](reference/stage11_replay_20261029_workspace_recheck_v1.json).
- G4 screening now includes 15 leads. C12 TCIA QIN-SARCOMA has an endpoint/modality mismatch; C13 Gitto's record does not provide radiographs; C14 Frontiers lacks a displayed image license and negative group; C15 IIEST is a mixed 217-image set with only 69 cancer-labelled, and no verified package, rights or image manifest. All remain NOT ELIGIBLE / NOT EVALUABLE; no images were accessed or downloaded. [Due diligence record](reference/STAGE11_EXTERNAL_COHORT_DUE_DILIGENCE_VI.md) · [C14 screen](reference/stage11_frontiers_11case_cohort_screen_20261029.json) · [C15 screen](reference/stage11_iiest_69case_cohort_screen_20261029.json). Primary-source review also records reuse of BTXRD by recent papers and unresolved Bone-CNN/BTXRD image-count discrepancy [here](reference/stage11_public_bone_tumor_cohort_literature_check_20261029.json).
- Current corpus continuation adds `tibia-lesions-dysplasia-2025` (CC BY 4.0, JATS payload hash recorded in the ingestion JSON): corpus 22 sources/794 chunks, index 794×384. Full suite 86/132 subtests; audit PASS on 10 evaluation datasets; 16-report replay PASS with no preflight mismatch. Four of sixteen reports changed some metrics after corpus growth, including a development recall decrease and a previously viewed test MRR decrease. Config was not tuned against the test split. New 3-question probe is agent-authored/in-sample only. Most recent source record: [ingestion and comparison](reference/stage11_tibia_source_ingestion_20261029.json). External cohort G4 still has no eligible dataset; the restricted Zenodo lead remains NOT ELIGIBLE / NOT EVALUABLE. Keep all seven gates OPEN and `answer_ready=false`.
- Follow-up dev-only tuning adds a soft route for explicit aneurysmal bone cyst wording to the existing Cureus review. Expansion dev improved from Recall@5 0.955/MRR 0.644 to 1.000/0.689; negative abstention remained 3/3. Other seven dev datasets did not change. The 16-report comparison has only expansion dev metric changes; viewed test reports are unchanged. Full suite 86/132 PASS, audit PASS and deterministic replay 16/16 PASS. Records: [experiment](reference/stage11_cureus_abc_route_dev_experiment_20261029.json), [bundle](reference/stage11_policy_rerun_20261029_cureus_abcrouting_v1/manifest.json), [audit](reference/stage11_integrity_audit_20261029_cureus_abcrouting_v1.json), [replay](reference/stage11_replay_20261029_cureus_abcrouting_v1.json), [test run](reference/stage11_test_run_20261029_cureus_abcrouting_full.json). This is in-sample retrieval evidence, not independent validation.
- Privacy code follow-up changes only new-case display label to generic `uploaded-image.<suffix>`; test uploads a synthetic identifier-like filename and confirms it is not persisted. No migration/runtime DB/backup review; G6 remains OPEN. [Test record](reference/stage11_test_run_20261029_privacy_filename_minimization_full.json).
- OFD/adamantinoma source-rights recheck screened four official records; corpus/source registry/cache unchanged. Two recent retrospective studies are CC BY-NC-ND, one CC-BY review lacks retrievable full text/version confirmation, and one CC BY case report was not added because current reviews cover the topic. [Recheck record](reference/stage11_ofd_adamantinoma_source_rights_recheck_20261029_v2.json).
- Gate closure blockers have been separated from workspace preparation: signed intended use, independent review/labels, cohort rights, safety/privacy verification and qualified legal review are absent; the per-gate action path is in [blocker matrix](reference/STAGE11_GATE_CLOSURE_BLOCKERS_VI.md).
- Latest workspace checkpoint: [`checkpoints/20261029_093707/project_snapshot.zip`](../checkpoints/20261029_093707/project_snapshot.zip), 836 files, 164,803,676 bytes uncompressed, SHA-256 `61775e31dd4d0d31ac44448896d76a0d3967be02eccd6e428d43a6414bbde604`; verifier PASS (836 files, ZIP CRC PASS). Fresh regression 87/132, offline audit, deterministic replay, progress/goals, G4 register through C15, 23-reference structural QA, BTXRD upstream rights-chain review, portal scan and regulatory source map are included. Acceptance gates remain **0/7 closed**; `answer_ready=false`. See [progress note](STAGE11_PROGRESS_2026-10-29.md). The v8 heading and older snapshot details below are historical technical context.
- The read-only current-state provenance QA record was created before the fresh audit/replay/regression rerun; it confirms matching corpus/config/index hashes and 16-report inputs at that earlier point. The later rerun is recorded in [latest full run record](reference/stage11_test_run_20261029_postdocs_full.json).


## Snapshot mới nhất: cue trung tính song ngữ và bundle v8 — 29/10/2026

- Literature refresh sau snapshot v8: toàn văn KJR 2026 reader study (217 ca, 3 radiologist) được ghi như hazard human-factors cho generator tương lai, gồm 20 Top-1 harm events/8 malignant-or-intermediate→benign downgrades, có giới hạn single-center/selected cohort/second-look. MI-CLEAR-LLM 2025 và FLAIR 2026 được đối chiếu từ publisher: reporting aids cho LLM radiology/generator, không thay retrieval relevance, citation entailment, abstention hoặc blind evaluation. Không dataset/ảnh nào được truy cập hay xin. Xem [online evidence review](reference/stage11_online_evidence_review_20261028.md), [reviewer packet](reference/STAGE11_REVIEWER_PACKET_VI.md), [safety guide](reference/STAGE11_SAFETY_REVIEW_GUIDE_VI.md) và [reporting crosswalk](reference/STAGE11_STARD_AI_REPORTING_CROSSWALK_VI.md).
- Scoping review JMIR 2026 về 157 healthcare RAG/GraphRAG generative studies ghi nhận 29,9% independent retrieval evaluation, 14,0% fine-grained evidence verification và 28,7% formal safety evaluation; do eligibility yêu cầu generated outputs nên đây là bối cảnh/rationale để giữ riêng các lớp protocol, không phải benchmark của retrieval-only BoneScope. [Review và scope details](reference/stage11_online_evidence_review_20261028.md#tổng-quan-phương-pháp-đánh-giá-healthcare-rag--jmir-2026).
- Cell Reports Medicine scoping review (2026, 251 medical RAG papers) reported explicit bias evaluation in 7/251, safety in 24/251 and low-resource settings in 6/251; search to 2025-07-01 with seven manually added records. These descriptive review counts reinforce multilingual/bias/safety domains but are not a BoneScope benchmark or RAG validation. [PubMed record and evidence notes](reference/stage11_online_evidence_review_20261028.md).
- Cohort search found a restricted-access lead: Zimbalist et al. 2024 report 1,421 Rambam radiographs (973 normal/448 abnormal; 137 benign/311 malignant), with patient-level separation in the study’s own 80/20 split. Data are available upon request only. Potential binary-endpoint cohort, not public and not automatically external to BoneScope; rights/DUA, reference-standard details, manifest and checkpoint/pretraining overlap are unverified. No data were downloaded and no one was contacted. [Primary article and due-diligence disposition](reference/stage11_online_evidence_review_20261028.md#lead-cohort-request-only--rambamweizmann-zimbalist-et-al-2024).

- Rà soát thêm các dạng “patient sent me an MRI”, “I reviewed the scan”, ảnh từ service, bệnh nhân cụ thể đã khám ở câu trước, và CT của con. Mở rộng policy carry-forward chỉ khi có cụm ca/bệnh nhân + modality, câu sau hỏi kết quả/đọc ảnh; đối chứng “typically/common/in general” vẫn giữ trong scope.
- Image-routing dev tăng **46→51**, 51/51 expected status khớp. Cumulative text-only matrix hiện **33/33** personal-image probes abstain và **18/18** controls education giữ trong scope. Tất cả do agent soạn/in-sample, không độc lập, mù, đại diện hay chuyên gia gắn nhãn; không xử lý ảnh thật.
- Bundle [v8, 16 report](reference/stage11_policy_rerun_20261029_evidence_neutral_v8/) được dựng lại từ v7 sau thay đổi cue neutral; manifest SHA-256 `2871ad8cc5b27f9dafa328123139a1b72624a7befaf61b7c4627cf0a0bff1f4a`. Chỉ strict OFD report đổi; 15 report metrics còn lại không đổi. Audit **PASS** (21 source caches/759 chunks, 9 datasets, 16 reports), replay **16/16 PASS**, không mismatch. [Bundle run record](reference/stage11_evidence_neutral_bundle_v8_record_20261029.json), [audit](reference/stage11_integrity_audit_20261029_evidence_neutral_v8.json), [replay](reference/stage11_replay_20261029_evidence_neutral_v8.json).
- Trên năm bộ strict lexical đã lưu, tổng cộng chỉ **4/40 câu dương** được qua (10%); **14/14 câu âm** abstain. So với v7, chỉ thêm một câu OFD dương qua (OFD strict Recall@5 1/5→2/5); các bộ expansion 1/22, synovial 0/4, synonym 1/1, V2 0/8 không đổi. Dữ liệu agent-authored/in-sample; giữ filter opt-in/disabled mặc định vì 90% positive abstention và không đo entailment.
- Thí nghiệm riêng unknown-token hard gate (config in-memory, không đổi production) tăng candidate positive 4/40→19/40, trong khi 14/14 negatives vẫn abstain trên các tập đã xem; còn 21/40 positives abstain. Missing-term diagnostics gồm tissue/symptoms/tests và các literals như don/cyst/cohort; không tự thêm whitelist từ bộ đã xem. Vì bỏ unknown tokens có thể lờ qualifier chưa ánh xạ và negatives ít/đã xem, đây chỉ là sensitivity analysis, không bật filter. [Report v3](reference/stage11_evidence_unknown_token_gate_experiment_20261029_v3.json), [bảng missing terms](reference/stage11_evidence_unknown_token_remaining_gap_analysis_20261029.json), [phân tích chi tiết](reference/EVIDENCE_CHECK_DESIGN_VI.md).
- Corpus không đổi; `--verify-evidence` vẫn opt-in do false refusal và không chứng minh citation entailment. GCT smoke-check và một top-3 nhiễu được ghi riêng, không tính thành benchmark. `answer_ready=false`.
- Chẩn đoán mới 29/10: `tools/analyze_evidence_coverage.py` kiểm tra riêng 5 gold reference chunks của OFD, không chạy retrieval; strict lexical checker giữ 1/5, abstain 4/5 do unknown Vietnamese tokens/literal mismatches. Không thêm whitelist theo dev; xem [report JSON](reference/stage11_evidence_verifier_miss_analysis_20261029.json) và [phân tích thiết kế](reference/EVIDENCE_CHECK_DESIGN_VI.md).
- Cập nhật v2: thêm cue trung tính “xấp xỉ/approximately”, diagnostic reference-chunk tăng 1/5→2/5. Evaluator hybrid thật trên cùng dev có Recall@5 2/5 (so với snapshot lịch sử 1/5), positive abstention 3/5, negative abstention 2/2; `frozen_evidence_config_matches=false`. Đây là kết quả in-sample, không entailment. Giữ gate tắt mặc định; xem [diagnostic v2](reference/stage11_evidence_verifier_miss_analysis_20261029_v2.json), [retrieval report v2](reference/stage11_evidence_verifier_ofd_actual_retrieval_20261029_v2.json), và [thiết kế](reference/EVIDENCE_CHECK_DESIGN_VI.md).
- Hồ sơ hiện hành: [verification summary v8](reference/stage11_verification_summary_20261029_evidence_neutral_v8.json), [latest full suite 79/127](reference/stage11_test_run_20261029_partial_answerability_evaluator.json), [legacy-report compatibility 16/16](reference/stage11_legacy_report_compatibility_20261029.json), [v7 historical snapshot](reference/stage11_verification_summary_20261029_personal_image_jats_wrapper_v7.json), [five new cases/two controls](reference/stage11_personal_image_routing_edge_probes_20261029_v5.json). Bảy cổng nghiệm thu vẫn mở.
- Sàng lọc cohort mới: bộ Frontiers/GitHub gồm 11 ca u dương tính (7 benign/4 malignant), không có normal, không có re-annotation/adjudication theo bài và quyền ảnh chưa được xác minh. Chưa eligible cho external test; không tải/ingest. RaR 2025 được thêm làm căn cứ đánh giá tách relevance, answer-context support và correctness. Chi tiết trong [reviewer packet](reference/STAGE11_REVIEWER_PACKET_VI.md), [checklist cohort](reference/STAGE11_EXTERNAL_COHORT_DUE_DILIGENCE_VI.md) và [online evidence review](reference/stage11_online_evidence_review_20261028.md).
- Rà lại abstract database Huang et al. 2024 trên mục lục số báo chính thức: 2.127 ca/sáu cơ sở (2013–2022), multimodal X-ray/CT/MRI và test AUC 84,99% cho binary X-ray model. Hai đồng tác giả Yao/Huang và cửa sổ thu nhận Guangxi chồng lấp với BTXRD; lineage cần làm rõ, chưa chứng minh trùng hay độc lập; “open-source” không thay quyền ảnh. Thêm nghiên cứu khả thi Bone-RADS/DeepSeek 2026 như hazard prompt cho future generation, không áp cho retrieval-only RAG và không dùng metric; chi tiết ở [online evidence review](reference/stage11_online_evidence_review_20261028.md), [due diligence](reference/STAGE11_EXTERNAL_COHORT_DUE_DILIGENCE_VI.md) và [safety guide](reference/STAGE11_SAFETY_REVIEW_GUIDE_VI.md).
- Rà mới OFD/adamantinoma 2025–2026: Chen et al. (50 ca) bàn luận giả thuyết phổ tiến hóa nhưng có ca tái phát được phân loại lại; Ramkumar et al. (59 hồ sơ) và Jayan et al. (58 khối u, 12 chẩn đoán sửa sau review) không quan sát tiến triển trong follow-up hạn chế; Jayan báo radiology concordance 40% OFD/60% adamantinoma; Wu et al. báo 49 ca nhi khoa; Hung et al. chỉ có 10 ca hệ gen. Bằng chứng khác nhau, không giải quyết quan hệ tự nhiên hay mapping BTXRD và không phải benchmark BoneScope. Hai bài là CC BY-NC-ND; các bài còn lại chưa có quyền mở được xác minh hoặc bị AAOS bảo hộ; không cache/ingest. [Source-triage JSON](reference/stage11_ofd_adamantinoma_source_triage_20261029.json) và [review nguồn trực tuyến](reference/stage11_online_evidence_review_20261028.md).
- Rà soát tĩnh code data-flow (29/10, không phải pentest): launcher bind `127.0.0.1`; upload tạm trong thư mục hệ điều hành, giới hạn 30 MiB/25 megapixel; ảnh không ghi vào SQLite, nhưng metadata/hash/điểm và nhận xét được lưu cục bộ. Pending prediction giữ metadata/hash/điểm tối đa 10 phút. Các endpoint case/comment/correction/dashboard chưa có authentication hoặc phân quyền; database không mã hóa và chưa có retention/secure-deletion policy. Giữ local-only với dữ liệu tổng hợp/không định danh cho tới khi privacy/security reviewer phê duyệt. Chi tiết ở [reviewer packet](reference/STAGE11_REVIEWER_PACKET_VI.md) và [bản ghi data-flow](reference/STAGE11_LOCAL_PRIVACY_SECURITY_REVIEW_20261029.md).
- Reviewer packet nay có trình tự đóng 7 cổng với dependencies, artifact/sign-off và điều kiện mở lại khi intended use hoặc cấu hình đổi; đây là runbook đề xuất, chưa có tổ chức ký phê duyệt. [Reviewer packet](reference/STAGE11_REVIEWER_PACKET_VI.md).
- Cập nhật jurisdictional source check: FDA có final CDS guidance ngày 29/01/2026; Việt Nam có Luật AI 134/2025/QH15, Nghị định 142/2026/NĐ-CP và Quyết định 33/2026/QĐ-TTg về danh mục AI rủi ro cao, cùng đầu mối luật thiết bị y tế và dữ liệu cá nhân/y tế. Cần chuyên gia rà toàn văn/phụ lục theo intended use; chưa kết luận BoneScope thuộc danh mục. Chỉ ghi nhận để luật sư/chuyên gia regulatory/privacy rà theo mục đích, không phải kết luận phân loại hoặc tư vấn pháp lý. [Online source review](reference/stage11_online_evidence_review_20261028.md).
- Rà soát 29/10 đã cập nhật FDA cybersecurity final guidance tháng 02/2026 (thay bản 06/2025; QMSR hiệu lực 02/02/2026), IMDRF GMLP N88 FINAL:2025 và phân biệt FDA AI lifecycle draft với AI PCCP final. Có checklist chuyển giao theo từng chức năng tại [regulatory applicability review](reference/STAGE11_REGULATORY_APPLICABILITY_REVIEW_VI.md). Không có kết luận pháp lý/phân loại thiết bị; intended use, jurisdiction và privacy/security gates còn mở.

## Rà soát cohort và quyền truy cập mới nhất — 28/10/2026

- Thêm hàng rào reuse cho source builder: `validate_source()` nay bắt buộc khai báo NCI policy chính xác và được gọi trong cả offline/online build. Regression xác nhận cache offline có NCI license sai bị từ chối. Bundle mới `post_offline_license_guard` giữ nguyên 16/16 report và toàn bộ metric; manifest `e7e6122d476ed14a3f38701a92a7a97e2d7b40e4c0766c4316e2bdd5763a1557`, comparison `8689b2e6787bd5f382a9964f1b3386ee35a73f5572a1dc834c97cfb307baecf5`. Audit PASS 21 cache/9 dataset/16 report/comparison; replay preflight 16 hash và PASS 16/16; full suite 68 passed/79 subtests. Audit/replay tamper checks đều chặn bản sao bị sửa. [Verification summary](reference/stage11_verification_summary_20261028_offline_license_guard.json), SHA-256 `617b1ee956def964fbff7a3027b8ca5eab69c1c783fedb231a21528e884369e1`; [test record](reference/stage11_test_run_20261028_offline_license_guard.json). Đây là bằng chứng integrity/phần mềm, không phải xác nhận y khoa hay nghiệm thu độc lập.
- DeepTIRP: bài mô tả 1.044 bệnh nhân phát triển, 354 internal test, 171 validation, 423 external cho tác vụ u xương so với nhiễm trùng; Zenodo files restricted, chỉ xem xét yêu cầu học thuật phi thương mại theo MTA. Bài ghi DOI `13858807`, bản ghi Zenodo đúng tiêu đề tìm được là `13858808` và không hiện license. Chưa tải tệp; cần tác giả xác nhận DOI/phiên bản, quyền, manifest và overlap trước mọi đánh giá.
- Họ cohort Munich/Freiburg 2021/2022/2024: các bài lần lượt báo cáo 934/111, 880/96 và 804 bệnh nhân/1.785 ảnh. Cùng nhóm nghiên cứu và khoảng thu nhận chồng lấp khiến overlap cần được làm rõ; exact overlap chưa chứng minh. Không cộng số ca, không coi là các nguồn external độc lập; không thấy public image package.
- Thêm SNUH-BoneTumor (19.757 ảnh crop, hỗn hợp pathology/clinical-imaging labels, reasonable request; đã dùng trong SKELEX nên không external đối với model đó) và Xie 2024 (878 ca pathology, external 83, output 5 nhóm histology, dữ liệu chưa thấy công khai). Xie và Song 2024 có tác giả/mạng lưới Guangzhou chung nên cohort overlap phải được làm rõ; không đếm thành hai external cohort độc lập. Cả hai vẫn cần rights, manifest và overlap review với BoneScope.
- Thêm họ cohort gối Sun Yat-sen/Quảng Đông: Shao 2024 (333 pathology-confirmed OS dạng tiêu xương vs GCT; external 54 ca) và Xu 2024 (687 ca u + 1.988 đối chứng; external 56 u + 145 bình thường, reference tumor hỗn hợp). Cả hai data statements cho phép yêu cầu, nhưng overlap người bệnh/trung tâm chưa rõ; xin linkage/manifests, rights và checkpoint overlap, không tính hai bài là independent trước khi xác minh.
- Thẩm định Yamana et al. 2025: 642 ca pathology-confirmed/1.129 ảnh từ ba bệnh viện, 40 loại u; kết quả chính là five-fold CV nội bộ, phần reader comparison dùng mẫu chọn 128 ca (113 được DINO phát hiện). Đưa vào danh sách request-only, không coi là external cohort. CC BY-NC-ND 4.0 của bài không cấp quyền ảnh bệnh nhân; cần hỏi data custodian về rights, manifests, overlap và một test set độc lập bị khóa.
- Sàng lọc BoneMet (ICLR 2025): dữ liệu chuột mô hình di căn xương do ung thư vú, ảnh xoay nhiều góc/thời điểm, nhãn ở cấp động vật; repository ghi CC BY-NC 4.0. Loại khỏi external cohort cho u xương nguyên phát ở người; không tải dữ liệu nhiều TB. Chi tiết và nguồn chính tại [online evidence review](reference/stage11_online_evidence_review_20261028.md).
- Cập nhật hồ sơ ở [online evidence review](reference/stage11_online_evidence_review_20261028.md), [checklist cohort](reference/STAGE11_EXTERNAL_COHORT_DUE_DILIGENCE_VI.md), [reviewer packet](reference/STAGE11_REVIEWER_PACKET_VI.md) và [verification summary](reference/stage11_verification_summary_20261028_offline_license_guard.json). SHA-256 online review được ghi trong verification summary. Không ứng viên mới nào đổi trạng thái nghiệm thu; `answer_ready=false`.
- Replay mới nhất preflight hash đủ 16 report artifact, không có mismatch và 16/16 báo cáo khớp. Audit mới nhất PASS trên 21 source cache, 9 evaluation sets, 16 reports và comparison; phạm vi chỉ integrity/provenance, không phải medical validity. Bằng chứng: [replay](reference/stage11_replay_20261028_offline_license_guard.json), [audit](reference/stage11_integrity_audit_20261028_offline_license_guard.json).

## Rà soát benchmark BTXRD được trích dẫn trong bài 2026 — 28/10/2026

- Thẩm định thêm bài Bone-CNN 2026: bài dùng benchmark Figshare BTXRD, nêu mẫu 884 ảnh/9 lớp; dữ liệu gốc Figshare là 3.746 ảnh. Bài nói không có patient IDs và dùng image-level split; Data Availability chỉ hướng người đọc hỏi corresponding author. Vì vậy không tính bài này là dataset mới, patient-level holdout hay external cohort.
- Figshare hiện ghi CC BY 4.0 cho archive; quyền upstream từng ảnh Radiopaedia/MedPix vẫn cần kiểm tra riêng. Không ingest bài model/benchmark vào corpus kiến thức bệnh vì không bổ sung nguồn lâm sàng độc lập. Ghi chú: [online evidence review](reference/stage11_online_evidence_review_20261028.md).

## Cập nhật policy ảnh cá nhân và bundle tái dựng — 28/10/2026

- Policy định tuyến ảnh cá nhân được mở rộng cho possessive tiếng Việt (`của tôi`, `bệnh nhân này`, `ca bệnh này`) và English `patient's` sau khi rà thấy một cách hỏi không nằm trong các cue cũ. Không dùng cue trần `patient` để tránh bắt câu giáo dục chung.
- Bổ sung case-specific context xa modality (`patient of mine`, ca đang điều trị/theo dõi), cùng động từ `review/assess/examine`. Cue dài chỉ áp dụng trong cùng câu; một câu giáo dục tổng quát có nhắc patient ở câu trước vẫn qua policy. Bốn dạng câu bắt lọt route `insufficient_evidence`.
- Ghi lại mẫu miss, regression control và hash tại [rà soát policy case-context](reference/stage11_policy_case_context_review_20261028.md).
- Bộ probe ảnh cá nhân agent-authored có 30 negative; 30/30 abstain đúng với reason `image_requires_specialist_assessment`, routing accuracy 30/30. Cùng tập đã dùng để nhận diện và sửa pattern, nên hoàn toàn in-sample; không đại diện, không độc lập/mù, và không kiểm tra tệp ảnh đính kèm.
- Snapshot baseline [bundle v2](reference/stage11_policy_rerun_20261028_post_personal_image_outcome_context_v2/) có 16 report; manifest SHA-256 `5d38921a426c77707363f93328b45ad28a8f97f2db9e5404ba979fd3b4617955`, comparison SHA-256 `20e688f0d8afb24e8984f2bbc1dd7abe364dfbb1478acc2c60e038ac3fad30bd`, không có metric nào đổi trong 16 báo cáo so với bundle trước. [Replay](reference/stage11_replay_20261028_post_personal_image_outcome_context_v2.json) PASS 16/16; [audit](reference/stage11_integrity_audit_20261028_post_personal_image_outcome_context_v2.json) PASS provenance/artifact trên 9 dataset, 21/21 source cache và index 759 × 384.
- Thêm `rag/build_evaluation_bundle.py` để dựng lại report bundle và comparison từ manifest cấu hình cũ; kiểm tra replay/audit không thay thế review y khoa.
- Bổ sung bốn false negative về ảnh do người hỏi chụp/được gắn với ca bệnh, cụm tiếng Việt “ca tôi/người bệnh tôi” và kết cục “đáng lo/bất thường”; thêm cue `comment/opinion` và controls giáo dục. Probe cumulative **12/12** ca ảnh cá nhân abstain, **6/6** câu giáo dục vẫn trong scope; in-sample, text-only.
- Chuyển mặc định của `rag/replay_reports.py` và `rag/audit.py` sang bundle `post_offline_license_guard`; chạy không truyền `--bundle`/`--report-dir`: replay PASS 16/16, audit PASS 21 cache/9 dataset/16 report. Hash và lệnh nằm trong [verification summary của snapshot lịch sử này](reference/stage11_verification_summary_20261028_offline_license_guard.json).
- Full pytest sau policy v2 (snapshot lịch sử): **66 passed, 79 subtests passed**, 0 failed; lần chạy mới nhất sau offline reuse guard: **68 passed, 79 subtests passed**, 0 failed, một cảnh báo deprecation Starlette; targeted retrieval **13 passed, 68 subtests passed**. Run record có Python/pytest version và implementation/test hashes tại [test run hiện hành](reference/stage11_test_run_20261028_offline_license_guard.json). Đây là regression phần mềm, không phải review độc lập hay đánh giá lâm sàng.
- Đối chiếu CLAIM 2024/DECIDE-AI vào [protocol review](reference/STAGE11_INDEPENDENT_REVIEW_PROTOCOL_VI.md) và [checklist cohort](reference/STAGE11_EXTERNAL_COHORT_DUE_DILIGENCE_VI.md). Mẫu cổng nay tách answerable-candidate coverage khỏi Recall@5; các ngưỡng/cỡ mẫu vẫn để reviewer chuyên môn quyết định trước khi mở test mù. CLAIM được áp dụng cho báo cáo đánh giá ảnh riêng, DECIDE-AI cho nghiên cứu workflow lâm sàng tương lai; không tài liệu nào được xem là bằng chứng hệ thống đã đạt các cổng đó.
- Recheck payload OFD: XML đã có sẵn trong cache; parser xác thực PMCID/DOI và tuyên bố CC BY 4.0, dựng 29 chunk, toàn bộ `(chunk_id, text_sha256)` trùng corpus hiện tại. Kết quả được ghi tại [online evidence review](reference/stage11_online_evidence_review_20261028.md) và [verification summary](reference/stage11_verification_summary_20261028_offline_license_guard.json).
- Mở trực tiếp record Figshare BTXRD: archive ghi CC BY 4.0; đây vẫn là cohort ảnh nguồn, không phải external. Đối chiếu thêm: Radiopaedia case uploads được cung cấp theo CC BY-NC-SA; MedPix/NLM giới hạn mặc định ở personal/local institutional teaching, mục đích khác cần quyền contributor. Project chưa có rights chain theo ảnh; CC BY trên archive chưa đủ xác minh quyền upstream. Xem [online evidence review](reference/stage11_online_evidence_review_20261028.md) và [CSV rights-chain trống](reference/stage11_image_rights_chain_template_20261028.csv) trước mọi redistribution, commercial hoặc derivative image use. CSV chỉ là biểu mẫu, chưa chứng minh quyền.

## Cập nhật nguồn cohort ngoài và provenance nhãn — 28/10/2026

- Đọc trực tiếp bài gốc BTXRD và bài SKELEX 2026: SKELEX dùng cùng chín metadata subtype BTXRD; tác giả nêu thiếu patient IDs và chia tập subtype theo ảnh, dù có hash/SSIM de-duplication. Báo cáo “external” Centers 2/3 của họ là held-out nguồn/trung tâm bên trong BTXRD lineage, không phải cohort ngoài mới hoặc patient-level external test. Bài SKELEX có license CC BY-NC-ND 4.0; không ingest/adapt nội dung vào corpus. [Ghi chú nguồn](reference/stage11_online_evidence_review_20261028.md).
- Đối chiếu thêm bài nhà xuất bản ngày 08/10/2026: đánh giá BTXRD cùng MURA theo split ảnh và leave-one-center-out. MURA là bộ X-ray chi trên normal/abnormal, không phải nhãn u xương pathology-based cho taxonomy này; không tạo external tumor cohort phù hợp. License bài CC BY-NC-ND 4.0, không ingest.
- Record Figshare gốc của BTXRD hiện ghi CC BY 4.0; mirror Hugging Face có metadata license xung đột. Bài BTXRD nói đã tuân thủ terms của Radiopaedia/MedPix, nhưng chưa audit quyền từng ảnh nguồn tại workspace. Việc xác nhận license record không thay đổi nguồn ảnh/leakage hoặc tính độc lập.
- Sửa độ chính xác provenance: BTXRD gốc mô tả Center 1 là pathology-confirmed **hoặc** xác nhận bởi hai radiologists; Center 2/3 được tìm trong kho ảnh theo keyword. Quy trình labeling/segmentation mô tả riêng; không có per-image confirmation pathway cho subtype hiếm.
- Xác minh lại Li et al. 2026: cohort Ruijin 471 bệnh nhân có pathology confirmation theo bài, một ảnh đại diện mỗi bệnh nhân; hai reader độc lập, còn third-reader consensus được nói rõ cho tranh chấp vùng annotation. Endpoint benign/non-benign; dữ liệu chỉ theo yêu cầu. Ghi nhận là candidate ưu tiên để thẩm định. Bài nói Ruijin không tham gia BTXRD và khác nguồn địa lý, hỗ trợ độc lập ở mức cơ sở; workspace chưa có dữ liệu, quyền, manifest/hash hay image-level overlap audit nên chưa thể gọi là external test.
- Thêm candidate Song et al. 2024: bài báo mô tả external center test 262 ca pathology-confirmed, 233 người có X-ray; hai radiologists phân nhóm benign/intermediate/malignant theo WHO 2020. Cohort có endpoint phù hợp hơn để cân nhắc riêng ba nhóm nhưng không khớp 10 subtype, và dữ liệu ảnh/manifest không thấy công khai. Data-availability statement “No datasets were generated or analysed” không giải thích đường truy cập cohort đã báo cáo; cần làm rõ. Overlap với BTXRD/checkpoint/pretraining và quyền ảnh chưa xác minh; CC BY 4.0 của bài không phải giấy phép ảnh. [Chi tiết và câu hỏi thẩm định](reference/STAGE11_EXTERNAL_COHORT_DUE_DILIGENCE_VI.md).
- Đồng bộ [checklist cohort ngoài](reference/STAGE11_EXTERNAL_COHORT_DUE_DILIGENCE_VI.md), [online source review](reference/stage11_online_evidence_review_20261028.md), [lộ trình](LO_TRINH_THUC_HIEN_DU_AN_AI.md) và [reviewer packet](reference/STAGE11_REVIEWER_PACKET_VI.md). Đây là rà soát tài liệu nguồn, chưa thay thế review chuyên gia hoặc cohort access.

## Cập nhật mới nhất — sửa loại trừ mục hành chính OFD — 28/10/2026

- Rà soát chunk phát hiện JATS heading `Data Availability Statement` chưa khớp mục loại trừ `data availability`; thêm biến thể heading và regression test để phần này không còn được index.
- Tải gốc đã có trong cache Europe PMC (143,385 byte, SHA-256 `be017ab4d7546064180d5b00aece02264bb8d969d367c00233efd7b9a5ab1c7c`). Parser giữ nguyên payload nguồn, corpus sau dựng lại còn **21 nguồn/759 chunk**, gồm **29 chunk OFD**, vector index **759 × 384**.
- Tại snapshot trước mở rộng cue possessive, audit provenance/integrity **PASS** (9 dataset, 21/21 cache), deterministic replay **PASS 16/16**, full suite **66 passed, 61 subtests passed**, một cảnh báo deprecated Starlette. Kết quả full suite này là lịch sử, trước policy mới. Đây là xác minh kỹ thuật, không phải review y khoa độc lập.
- Lệnh tái dựng: `.\.venv\Scripts\python.exe rag/build_corpus.py --offline` rồi `.\.venv\Scripts\python.exe rag/build_index.py`; chi tiết hash ở [verification summary của snapshot lịch sử này](reference/stage11_verification_summary_20261028_offline_license_guard.json) và [reviewer packet](reference/STAGE11_REVIEWER_PACKET_VI.md).


## Cập nhật mới nhất — route chondrosarcoma và hồi quy đã xem — 28/10/2026

- Audit miss p13 cho thấy đoạn gold nằm ở `nci-chondrosarcoma:0003`, nhưng route trước đó chỉ giữ hai chunk đầu của trang. Route theo tên bệnh nay giữ ba chunk NCI chuyên biệt trước khi điền kết quả toàn kho; p13 truy hồi gold ở hạng 3.
- Hybrid trên V2 viewed regression chuyển **7/8 → 8/8**, MRR **0,692 → 0,733**, negative abstention vẫn 6/6. Concept rerank đạt 8/8, MRR 0,938; dev vẫn giảm 22/22 xuống 19/22 nên giữ opt-in. Vì route được chỉnh sau khi xem p13, số V2 là in-sample, không phải holdout và không chứng minh tổng quát hóa. [Bundle có manifest](reference/stage11_policy_rerun_20261028_post_ofd/manifest.json), [comparison mô tả](reference/stage11_policy_rerun_20261028_post_ofd/comparison.json).
- Historical full suite trước policy ảnh cá nhân **66 passed, 61 subtests passed**; snapshot ở thời điểm đó đạt **66/66**; lần chạy mới nhất sau offline license guard đạt **68/68**. Audit PASS trên 9 dataset/16 report; replay PASS 16/16. Các kết quả xác nhận kỹ thuật/provenance, không phải tính đúng y khoa.


## Cập nhật mới nhất — NCI Glossary và policy ánh xạ nhãn — 28/10/2026

- NCI API glossary đã được ingest với payload SHA-256 `714b563f81886de34d24d8e6d13aa1fde5772adae18f2ba2c29bfaa60d6194c5`; parser chỉ lấy definition text, xác thực dictionary/language/audience/term ID/term name, loại pronunciation/audio. Định nghĩa này chỉ là thuật ngữ bệnh nhân khái quát.
- Probe truy vấn phát hiện câu hỏi “nhãn BTXRD có đồng nghĩa không?” ban đầu trả candidate do chồng lặp từ khóa. Đã bổ sung abstention `unverified_dataset_label_mapping` và test; câu hỏi định nghĩa vẫn lấy chunk NCI hạng 1, còn câu mapping dừng ở `insufficient_evidence`. Hai probe dev agent-authored đạt 2/2 routing, positive Recall@5 1/1, negative abstention 1/1; đây không phải đánh giá độc lập.
- Tại snapshot 28/10: corpus 21 nguồn/759 chunk; audit integrity PASS trên 9 dataset và 16 report; deterministic replay PASS 16/16; full pytest PASS 66 test/79 subtests với một cảnh báo deprecation. Các điều kiện reviewer độc lập, tập blind và citation entailment vẫn mở; `answer_ready=false`. Xem [reviewer packet](reference/STAGE11_REVIEWER_PACKET_VI.md), [online source review](reference/stage11_online_evidence_review_20261028.md), [verification summary của snapshot lịch sử này](reference/stage11_verification_summary_20261028_offline_license_guard.json) và [test record](reference/stage11_test_run_20261028_offline_license_guard.json).


## Cập nhật trước — review OFD, corpus 20 nguồn (snapshot lịch sử) — 28/10/2026

- Đã thêm `rag/replay_reports.py`: chạy lại 16 cấu hình trong bundle snapshot 28/10 với model/index đã khóa, so sánh toàn bộ nội dung report trừ timestamp tạo file. Lệnh `.\.venv\Scripts\python.exe rag/replay_reports.py --output docs/reference/stage11_replay_20261028.json` đạt **PASS 16/16**; kết quả tại [replay JSON](reference/stage11_replay_20261028.json). Đây là tái lập kỹ thuật, không phải reviewer/kiểm định lâm sàng.

- Đã lưu full-text JATS của Liu et al., *Osteofibrous dysplasia: a narrative review* (2024; PMCID PMC10967096; DOI 10.1186/s13018-024-04682-3) từ Europe PMC. Payload 143,385 byte, SHA-256 `be017ab4d7546064180d5b00aece02264bb8d969d367c00233efd7b9a5ab1c7c`; license CC BY 4.0 được ghi trong payload. Nguồn được kiểm tra trực tiếp tại [Europe PMC](https://europepmc.org/articles/PMC10967096) và [publisher](https://link.springer.com/article/10.1186/s13018-024-04682-3). Parser loại funding, contributor, conflict, data-availability và các mục hành chính. Nguồn chỉ là narrative review; chính tác giả ghi không có systematic evaluation/meta-analysis. Nội dung lịch sử về “ossifying fibroma” không chứng minh định nghĩa hay mapping nhãn `osteofibroma` của BTXRD.
- Source routing chỉ dùng cụm đầy đủ `osteofibrous dysplasia`; acronym `OFD` không được dùng để route. `osteofibroma` vẫn là unsupported term và một case dev âm giữ nguyên câu hỏi mapping nhãn BTXRD. Bộ dev OFD có 5 câu truy hồi và 2 câu policy âm; sau khi dùng exploratory retrieval để hoàn thiện câu hỏi trên cùng corpus, kết quả in-sample là Recall@5 5/5, MRR 0,700, routing 7/7; negative abstention 2/2. Đây là chẩn đoán dev đã tune, không phải holdout/đánh giá lâm sàng. Strict lexical mode chỉ đạt 1/5 câu dương và routing 3/7; giữ opt-in.
- Corpus được dựng lại offline thành **21 nguồn / 759 chunk**, index **759 × 384**. SHA corpus `b34d318c136f591d3b417e39603141f7d7836b960bf72d75a547653529e48d9d`, source lock `45bb28d3b1f1e4c4d0344785e36a7860816bea26bd20c7ab8a4ffb3c7daa6fa1`, index manifest `ad75159115ef04c360fda64dcb0f31b977158a607f3298b83fa63cabdd900a31`.
- Evaluation bundle tại snapshot 28/10 là `reference/stage11_policy_rerun_20261028_post_offline_license_guard/` gồm 16 báo cáo; audit PASS kiểm 21/21 payload cache, 9 dataset và 16 report, với code/config/index/evidence hashes. Audit PASS xác nhận provenance/integrity only, không phải tính đúng y khoa. Summary và packet: [verification summary của snapshot lịch sử này](reference/stage11_verification_summary_20261028_offline_license_guard.json), [reviewer packet](reference/STAGE11_REVIEWER_PACKET_VI.md).
- Các bộ chính sau khi dựng lại: expansion dev 22/22 Recall@5, MRR 0,683, negative abstention 3/3; V2 đã xem 7/8, MRR 0,692, negative abstention 6/6. Strict lexical: expansion 1/22, V2 0/8, synovial source 0/4, OFD 1/5 positives. Không diễn giải các số liệu dev/v2 này như xác suất lâm sàng.
- Tại snapshot lịch sử này, full suite đã chạy lại: **66 passed, 61 subtests passed**, một cảnh báo deprecation Starlette. Fixture audit được sửa để khai báo payload SHA-256 hợp lệ; production audit không nới lỏng. Xem [test record](reference/stage11_test_run_20261028.json).


## Bản ghi trước đó — corpus 19 nguồn, route synovial và loại bảng BioC — 28/10/2026

- Đã thêm review Zmerly et al., *Medicina* 2026 (PMCID PMC13414048, DOI 10.3390/medicina62071388): Europe PMC JATS HTTP 200 khớp danh tính bài và chứa giấy phép CC BY 4.0; payload SHA `13b37e87aba2bac5f29c4cde583a99e9a0bc6ce62c02fb4787068f6ada04d8b8`. Parser thêm **35 text-only chunks**. Corpus hiện **19 nguồn / 738 chunk**, index **738 × 384**. Corpus SHA `6d2f2d5a1ec4c2bb0e4aa3b14871b8decc3ca28f04aa26b4d7c7e4072f94ff2b`; source lock `856af5c908697b86f351b63b1bc75bfcf8718ed3b93cf56cb33f2cdc30e89909`; index manifest `481eb99c3cc5eaf026a0e611ad20ac43c3f01f35c4c57cd370543877d9c2d244`; retrieval config `970f6075f39589842c5dd0dfc7c079e94b366def82c1a0eda6aaa6d1a9652970`. Audit của snapshot 19 nguồn tại [báo cáo integrity lịch sử](reference/stage11_integrity_audit_20261028.json), nguồn và căn cứ license tại [online evidence review](reference/stage11_online_evidence_review_20261028.md).
- Retrieval ưu tiên tối đa hai kết quả từ nguồn theo cue tường minh, nay gồm synovial chondromatosis; abstract chỉ được ưu tiên khi người hỏi yêu cầu tổng quan. `synovial chondromatosis` canonical được hỗ trợ; label BTXRD `synovial osteochondroma` vẫn bị policy chặn, không tự ánh xạ. Caller allowlist không bị mở rộng.
- Bộ dev synovial có 4 câu dương/2 câu âm, do agent soạn sau khi xem bài: sau khi thêm synonym lấy trực tiếp từ review, Recall@5 vẫn **4/4**, MRR tăng **0,508 → 0,542**, negative abstention **2/2**, routing **6/6**. Tuning trên chính dev set nên kết quả in-sample. Bộ synonym riêng gồm 1 câu dương/1 câu âm: hạng dương 1, negative abstention 1/1; strict lexical cũng qua 1/1 ca dương này, nhưng mẫu số không đủ để kết luận entailment. Cả hai bộ do agent soạn, không phải holdout hay rà soát y khoa. Báo cáo tái chạy bằng evaluator mới tại `stage11_policy_rerun_20261028_post_image_policy_compositional/`.
- Bộ expansion dev sau khi gắn lại hash corpus và rà gold: Recall@5 **22/22**, MRR **0,691**, negative abstention **3/3**, routing **25/25**. Tất cả 22 câu dùng gold list kiểu cũ; **21/22** lấy đủ mọi chunk được liệt kê, nhưng danh sách cũ không xác định các chunk là bắt buộc hay thay thế. V2 test đã xem, chỉ hồi quy: Recall@5 **7/8**, MRR **0,692**, negative abstention **6/6**, lấy đủ list **7/8**. Cả hai không độc lập; mọi retrieval/routing metric cũ khớp khi tái chạy. Không gọi list-completion là accepted-evidence-group completion.
- Concept rerank trên corpus hiện tại: expansion dev **19/22**, MRR **0,598** (hybrid 22/22, 0,691); V2 test đã xem **8/8**, MRR **0,875** (hybrid 7/8, 0,692). Vì kết quả dev thấp hơn và V2 đã xem, giữ opt-in; báo cáo tái chạy hiện ở `stage11_policy_rerun_20261028_post_image_policy_compositional/`.
- Policy chặn thêm các cách diễn đạt tổ hợp về phim/ảnh cá nhân được đính kèm hoặc tải lên. Snapshot đó đạt **24/24**; snapshot `post_personal_image` sau đó đạt **26/26**; snapshot mới nhất `post_case_context` đạt **30/30**. Các bộ đều agent-authored, in-sample, không độc lập/mù/đại diện; kiểm tra không bao gồm tệp ảnh đính kèm. Evaluator lịch sử nằm trong `stage11_policy_rerun_20261028_post_image_policy_compositional/`.
- Giới hạn giao diện: `retrieve()` nhận câu hỏi dạng văn bản, không nhận metadata tệp đính kèm hay pixel ảnh. Do đó pattern hiện tại chỉ xử lý yêu cầu ảnh được diễn đạt trong chữ; không thể khẳng định sẽ chặn câu “bạn nghĩ sao?” kèm ảnh hoặc kiểm tra ảnh upload. Chưa có chatbot sinh đáp án; `answer_ready=false` vẫn là chốt an toàn.
- Strict `--verify-evidence` trên corpus 19 nguồn vẫn không đạt với các bộ chính: expansion dev Recall@5 1/22 và lấy đủ gold list 1/22, V2 0/8 và 0/8, synovial source 0/4; positive abstention lần lượt 21/22, 8/8, 4/4. Đây là coverage từ vựng, không entailment; giữ opt-in.
- BioC parser hiện loại table blocks/captions bên cạnh hình, references và footnotes; một bảng BSG được ghi là adapted từ WHO 2020 nên không đưa vào corpus khi chưa kiểm tra quyền thành phần bên thứ ba. Corpus/index được dựng lại offline từ payload đã cache. Tại snapshot trước OFD, audit **PASS** trên 19 nguồn, 738 chunk, index 738 × 384; bảy tập evidence và **13/13 evaluation reports** được kiểm tra theo manifest, gồm report/config/code hashes và đường dẫn tương đối an toàn. Audit đối chiếu chunk với source lock ở `source_sha256`, ngày nguồn, accessed-at, DOI/PMCID, kiểm tra định dạng payload SHA-256 và đã xác minh cache **19/19** không thiếu/lệch hash ở snapshot đó trong workspace này. Full suite **59 passed / 45 subtests** là snapshot cũ; chưa rerun sau parser/index/policy/evaluator-schema changes. Snapshot hashes/evaluation/cổng ở [verification summary của snapshot lịch sử này](reference/stage11_verification_summary_20261028_offline_license_guard.json).
- Rà quyền tái sử dụng đủ **21 mục** registry: 13 mục NCI theo chính sách tái sử dụng văn bản NCI, 8 nguồn ngoài NCI CC BY 4.0 đã xác minh bằng bài/payload cụ thể. Policy NCI và URL được ghi tường minh trong `sources.json`, source lock và chunk metadata; phạm vi NCI chỉ là text, không ảnh/logo. Đây là provenance, không xác nhận nội dung y khoa.
- Evaluator hỗ trợ gold với nhiều nhóm evidence thay thế qua `evidence_groups`; mỗi nhóm là một tập chunk đủ theo nhãn reviewer, các nhóm là phương án độc lập. Audit xác thực hash/chunk/source/section cho từng nhóm. Precision/recall/nDCG evidence chọn nhóm được bao phủ tốt nhất; báo thêm số nhóm được lấy đủ và rank hoàn tất nhóm. Với gold kiểu cũ `evidence`, giữ nguyên metric và chỉ báo độ phủ đủ toàn bộ danh sách; không giả định danh sách đó là một nhóm bắt buộc. Báo cáo evaluator, so sánh và SHA manifest tại `stage11_policy_rerun_20261028_post_image_policy_compositional/`.
- Rà code phát hiện completion rank cũ cộng dư 1; evaluator đã sửa, tái chạy 13 báo cáo. Chỉ số retrieval/routing/P/R/nDCG giữ nguyên; legacy-list completion MRR đúng là **0,668** (dev) và **0,692** (V2), completion@5 vẫn 21/22 và 7/8. Không dataset hiện tại nào có `evidence_groups` do reviewer gắn.
- Gap taxonomy vẫn mở: bài gốc BTXRD mô tả nhiều đường xác nhận nhưng không công bố provenance theo từng subtype hiếm. WHO ICD-O-3.1 liệt kê `osteofibroma` như alias mã hóa của `ossifying fibroma` M-9262/0; review OFD CC BY 4.0 năm 2024 ghi nhận thuật ngữ `ossifying fibroma` từng được dùng lịch sử cho OFD trước khi thuật ngữ xương chày/xương mác được chuẩn hóa. Các nguồn này chứng minh nomenclature phụ thuộc hệ thống/thời kỳ, chưa chứng minh BTXRD dùng định nghĩa nào cho từng ảnh. Giữ nhãn dataset và alias provenance riêng, không tự gán mô bệnh học theo lớp. “Synovial osteochondroma” vẫn không có mapping xác nhận; nguồn SAGE chỉ CC BY-NC 3.0, không ingest. Cần protocol gốc hoặc chuyên gia giải phẫu bệnh cơ xương phân xử; chi tiết tại [online evidence review](reference/stage11_online_evidence_review_20261028.md).
- Tìm kiếm ngoài BTXRD chưa xác nhận dataset ảnh u xương công khai, độc lập, có quyền và nhãn/patient-level provenance đầy đủ. Cohort 471 bệnh nhân trong bài đa trung tâm 2026 là candidate ưu tiên để xin quyền: bài mô tả pathology-confirmed, một ảnh đại diện/bệnh nhân và hai reader; third-reader consensus áp dụng cho bất đồng vùng annotation, không được xác nhận là adjudication nhãn chẩn đoán. Endpoint benign/non-benign, dữ liệu chỉ chia sẻ theo yêu cầu. Bài *eBioMedicine* 2020 mô tả external test 291 bệnh nhân/639 ảnh từ hai center (tổng cohort 2.899 ảnh/1.356 bệnh nhân), nhãn mô bệnh học và patient-level CV; dữ liệu chỉ theo yêu cầu và endpoint ba lớp không tương ứng trực tiếp với 10 lớp. Chưa có dữ liệu hay quyền truy cập cho cả hai. Bản Hugging Face là mirror cùng BTXRD, còn trang ghi license không nhất quán; không dùng thay nguồn Figshare hoặc làm external test. Chi tiết và link trong [online evidence review](reference/stage11_online_evidence_review_20261028.md).
- Đã sàng lọc thêm IIEST (69 ảnh u trong tập nhỏ hỗn hợp), bộ 150 ảnh gom từ website với ground truth dựa trên mô tả ca, Bone-CNN 2026 (884 ảnh subset Figshare BTXRD, split theo ảnh do thiếu patient ID), và VinDr-SpineXR restricted-access (bất thường cột sống, không phải taxonomy u xương); không phù hợp làm test ngoài độc lập cho checkpoint này. Lý do và link primary source nằm trong online review.
- **Giai đoạn 11 chưa nghiệm thu để làm chatbot hoặc trả lời y khoa.** `answer_ready=false`; còn reviewer chuyên môn độc lập, rubric/label adjudication, tập blind và kiểm chứng citation entailment/false acceptance.

### Các bước nghiệm thu còn lại

1. Chủ dự án xác nhận/ký [intended-use lock](reference/STAGE11_INTENDED_USE_LOCK_TEMPLATE_VI.md); reviewer độc lập nhận [hồ sơ reviewer](reference/STAGE11_REVIEWER_PACKET_VI.md), ký [bản khai báo năng lực/độc lập/xung đột](reference/STAGE11_REVIEWER_DECLARATION_TEMPLATE_VI.md), evaluation lead khóa/hash [kế hoạch lấy mẫu](reference/stage11_blind_sampling_plan_template_20261029.json) trước khi rút mẫu; curator giữ [sampling manifest](reference/stage11_blind_sampling_manifest_template_20261029.csv) riêng và xác nhận hash; dùng [CSV nhãn độc lập](reference/stage11_blind_label_template_20261028.csv), giữ mỗi bản bất biến; khi bất đồng, log riêng bằng [CSV adjudication](reference/stage11_adjudication_log_template_20261029.csv). Điền [acceptance-gate worksheet](reference/stage11_acceptance_gate_template_20261028.csv) trước khi mở kết quả.
2. Privacy/security/legal reviewers điền [phiếu closeout](reference/STAGE11_PRIVACY_SECURITY_GATE_TEMPLATE_VI.md) theo intended use và cấu hình đã khóa; không dùng dữ liệu thật trước khi thẩm quyền phù hợp ký.
3. Sau khi intended use được khóa, safety lead điền [hazard-analysis template](reference/STAGE11_SAFETY_REVIEW_GUIDE_VI.md), ký thang và tiêu chí chấp nhận trước khi đánh giá residual risk.
4. Evaluator ba mức cho `answerable`/`partially_answerable`/`unanswerable` đã được triển khai, fail-closed khi thiếu/sai nhãn và có regression tổng hợp; legacy reports giữ metric. Xem [test record 79/127](reference/stage11_test_run_20261029_partial_answerability_evaluator.json) và [compatibility comparison 16/16](reference/stage11_legacy_report_compatibility_20261029.json). Trước blind run, reviewer phải cung cấp label/status đúng schema; freeze test mới và đặt pass/stop trước unblind; báo theo population, nhóm tổn thương, ngôn ngữ, nguồn và intent. Code hỗ trợ nhãn partial không đồng nghĩa đã đo safety cho nhóm này.
5. Kiểm định citation entailment, false acceptance/refusal, abstention và routing; rà soát từng ca sai. Không tune trên test đã mở.
6. Giữ `answer_ready=false` tới khi reviewer chuyên môn ký cổng nghiệm thu.
7. Với nhánh ảnh 11A, chỉ tiếp tục một trong hai cohort tiềm năng sau khi người dùng chọn kênh liên hệ và chủ dữ liệu xác nhận quyền, de-identification, patient-level provenance, nhãn chuẩn, endpoint mapping và overlap với checkpoint; chưa bộ nào là benchmark sẵn dùng.
8. Dùng [checklist thẩm định cohort ngoài BTXRD](reference/STAGE11_EXTERNAL_COHORT_DUE_DILIGENCE_VI.md) trước khi đăng ký, tải hoặc đánh giá bất kỳ bộ ảnh nào.
9. Nếu mở một nghiên cứu diagnostic-accuracy cho classifier ảnh, điền [STARD-AI checklist 40 mục/48 dòng phản hồi (+header)](reference/stage11_stard_ai_reporting_checklist_template_20261029.csv) và xem [crosswalk áp dụng Stage 11](reference/STAGE11_STARD_AI_REPORTING_CROSSWALK_VI.md). Đây là checklist đầy đủ báo cáo, không phải gate pass; không áp nó cho retrieval-only RAG và không dùng thay blind protocol, reviewer labels hay safety/regulatory approval.
10. Với nghiên cứu AI ảnh, rà CLAIM 2024 (44 mục) theo modality; chọn thêm TRIPOD+AI cho prediction-model development/evaluation và/hoặc STARD-AI cho diagnostic accuracy có reference standard theo aim/design. TRIPOD-LLM dành cho nghiên cứu LLM biomedical/healthcare; CHART nếu đánh giá generative chatbot tóm tắt evidence/health advice; DECIDE-AI cho early-stage live clinical evaluation. Xem [crosswalk và scope](reference/STAGE11_STARD_AI_REPORTING_CROSSWALK_VI.md). Không áp các reporting checklist này cho retrieval-only RAG và không dùng thay protocol đánh giá retrieval/evidence/abstention.
11. Nếu có randomized clinical trial trong tương lai, bắt đầu từ core SPIRIT 2025/CONSORT 2025 hiện hành, rồi rà SPIRIT-AI/CONSORT-AI (2020) và yêu cầu journal; hai extension AI có trước core 2025 nên cần người phụ trách trial xác nhận cách hài hòa. Hiện Stage 11 không có trial.
12. Nếu trial có người tham gia 0–19 tuổi, kiểm tra SPIRIT-C/CONSORT-C 2026 (17/13 mục) cùng core 2025; với trial có AI intervention, rà giao điểm giữa extension theo tuổi và theo AI, rồi xác nhận yêu cầu journal hiện hành. Đây là chuẩn báo cáo có điều kiện, không phải gate cho retrieval-only hiện tại. [Crosswalk](reference/STAGE11_STARD_AI_REPORTING_CROSSWALK_VI.md).
13. Khi chuẩn bị một nghiên cứu y học/manuscript tương lai có dùng GenAI ở bất kỳ giai đoạn nào, cân nhắc GAMER để báo cáo tên/version/vai trò và kiểm chứng nội dung; GAMER không đo hiệu năng BoneScope hay thay guideline theo study design. [GAMER](https://ebm.bmj.com/content/30/6/390.full) · [crosswalk](reference/STAGE11_STARD_AI_REPORTING_CROSSWALK_VI.md).

## Bàn giao mới nhất — thêm Giai đoạn 11A và catalogue ảnh BTXRD — 27/10/2026

- Đã tải BTXRD từ Figshare chính thức (CC BY 4.0; DOI `10.6084/m9.figshare.27865398.v1`). Archive 840,474,929 byte; MD5 nguồn khớp `59132a5036d030580ccade8add8f13df`; SHA-256 `e7c800c3b4e090262b160525a0765f9d93bcc53d639c03806a3ac47b0ded3373`.
- Manifest runtime: `data/external_datasets/BTXRD/reference/manifest.csv`; summary: `data/external_datasets/BTXRD/reference/summary.json`. Có 3.746 ảnh và đủ 22/22 metadata; 3.745 nhãn hợp lệ (1.879 no-tumor, 1.866 tumor), 1 ảnh `IMG001276.jpeg` xung đột nhiều subtype nên nhãn để trống; 21 nhóm exact duplicate gồm 42 ảnh.
- Không có patient/lesion IDs; checkpoint có nguồn huấn luyện BTXRD nhưng chỉ giữ `split_signature`, thiếu danh sách image ID từng split. Vì vậy mọi partition để `unassigned`, `independent_of_checkpoint_training=false`. Không tính hay tuyên bố accuracy trên BTXRD cho checkpoint đang có; muốn benchmark ảnh chụp mới phải có nguồn khác, độc lập, có quyền dùng và nhãn chuyên gia.
- Script tái lập: `tools/prepare_btxrd_reference.py` (yêu cầu `openpyxl==3.1.5`, đã khai báo trong `requirements_rag.txt`). Hướng dẫn tại `docs/guides/README_IMAGE_REFERENCE_VI.md`, register tại `docs/reference/btxrd_source_register.json`, lộ trình tại `docs/LO_TRINH_THUC_HIEN_DU_AN_AI.md`.
- Giai đoạn 11A hoàn tất phần tải/kiểm checksum/catalogue và đánh dấu rõ giới hạn leakage; mục tiêu external validation chưa thể nghiệm thu. Giai đoạn 11 RAG cũng chưa hoàn tất: `answer_ready=false`, chatbot chưa có. Trạng thái và các hạng mục trước đó giữ nguyên bên dưới.

### Việc tiếp tục

1. Tiếp tục tìm một bộ X-quang ngoài BTXRD có giấy phép, nhãn chuẩn chuyên gia và provenance; không dùng ảnh ngẫu nhiên trên web làm nhãn chuẩn.
2. Nếu có thể, khôi phục danh sách split train/validation/test gốc; không chia ngẫu nhiên ảnh hiện tại do thiếu patient/lesion IDs.
3. Song song tiếp tục RAG theo phần bàn giao cũ dưới đây: tập độc lập, false refusal/acceptance, xác minh nguồn/nhãn; chỉ sau nghiệm thu mới mở chatbot.

Nguồn: [Figshare BTXRD](https://figshare.com/articles/dataset/A_Radiograph_Dataset_for_the_Classification_Localization_and_Segmentation_of_Primary_Bone_Tumors/27865398), [bài báo Scientific Data](https://www.nature.com/articles/s41597-024-04311-y).

Lệnh tái tạo catalogue sau khi cài dependency:

```powershell
\.venv\Scripts\python.exe -m pip install -r requirements_rag.txt
\.venv\Scripts\python.exe tools\prepare_btxrd_reference.py
```

## Bàn giao mới nhất — cập nhật hybrid vocabulary — 27/10/2026

- Corpus hiện **439 đoạn / 13 nguồn** (12 NCI, 1 Open Orthopaedics CC BY 4.0); hash `552eb6b313ca472dc92e5a20280dbf02a39d74091439a895099127c6b96c8dfb`. Trang nguồn đã lọc khối Metrics/downloads khỏi corpus. Index 439 × 384 đã được dựng lại.
- `retrieval_config.json` lên `hybrid-v2`; thêm đồng nghĩa Việt–Anh cho unicameral/simple bone cyst, vị trí humerus, cohort hồi cứu, cỡ mẫu, tiêm và kết quả tránh mổ mở. `simple bone cyst` được chuyển khỏi danh sách unsupported vì hiện có bằng chứng trong corpus; các nhãn thiếu khác vẫn bị chặn.
- Tập dev mới `rag/data/evaluation_expansion_dev_v1.json`: 6 câu có đáp án, 3 câu âm. Kết quả apply-policy hybrid: Recall@5 **6/6**, MRR@5 **0,639**, negative abstention **3/3**, routing accuracy **9/9**. Báo cáo tại `docs/reference/stage11_expansion_dev_v1.json`. Tập do AI soạn, dùng khi phát triển/tuning và có rà lại evidence sau khi xem hit; không phải test độc lập.
- Đã gắn lại bằng chứng cho câu dev V2 `n04` vì nguồn mới trả lời được câu simple bone cyst. Test split V2 không đổi nhưng đã xem trước đó; toàn bộ V2 chỉ regression. Với policy bật: 17 câu dương Recall@5 **14/17**, MRR@5 **0,688**; 11/11 câu âm được từ chối; routing accuracy **33/33**. `frozen_config_matches=false` là điều dự kiến do vocabulary đã đổi. Báo cáo: `docs/reference/stage11_20261027_config_v2_regression.json`.
- RAG test: **23 passed, 24 subtests passed**. Full suite: **39 passed, 31 subtests passed**, một cảnh báo deprecation Starlette. Thêm kiểm tra ngăn Metrics vào corpus và kiểm tra expansion/routing tiếng Việt.
- `answer_ready` tiếp tục false; không có chatbot. Điểm tiếp theo là thiết kế tập độc lập do người khác rà soát, rồi đo retrieval/false refusal/false acceptance trên nhiều nhãn. Tiếp tục xác minh `osteofibroma`; không xem kết quả dev là bằng chứng an toàn y khoa.

Lệnh tái lập: `.\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q`; `.\.venv\Scripts\python.exe rag\evaluate.py --mode hybrid --apply-policy --dataset rag\data\evaluation_expansion_dev_v1.json --output docs\reference\stage11_expansion_dev_v1.json --summary`. Các mục cũ phía dưới là lịch sử, số liệu được giữ theo thời điểm đo.

## Bàn giao phiên trước — 27/10/2026

- Đã mở rộng `rag/data/sources.json` thêm một nguồn Open Orthopaedics CC BY 4.0; nguồn ghi rõ tác giả, publisher, ngày, URL, giấy phép và scope. Nghiên cứu là cohort hồi cứu 51 ca UBC đầu trên xương cánh tay về một phương pháp điều trị, không phải chỉ dẫn tổng quát.
- Pipeline hiện xác thực host, giấy phép và scope cho nguồn ngoài NCI, gắn metadata nguồn lên từng chunk, đồng thời lọc email/boilerplate của trang nguồn.
- Corpus/index mới: **440 chunks, 13 sources, 384 dimensions**. Corpus SHA-256: `466a467a7b27dae86ab94b6b76d33d22ef32618a2b2719aeb6f25d3f242b5a15`. `evaluation_v2.json` và `evaluation_evidence_v3.json` được đồng bộ hash corpus; gold/câu hỏi không thay đổi. Các tập này đã được xem, không phải đánh giá độc lập.
- RAG tests: **21 passed, 21 subtests passed**. Full project: **37 passed, 28 subtests passed**, một cảnh báo deprecation Starlette.
- Chạy lại hybrid trên `evaluation_v2.json` (28 câu đã xem; retrieval thô, `apply_policy=false`): Recall@5 **13/16 = 0,8125**, MRR@5 **0,66875**; **12/12 câu âm vẫn có hit**. Báo cáo đầy đủ tại `docs/reference/stage11_20261027_source_expansion_v1.json`. Không dùng kết quả này để tuyên bố khả năng từ chối hay đánh giá độc lập.
- Truy vấn tiếng Anh về nguồn mới lấy đúng source và hit, nhưng `status=candidates_found`, `answer_ready=false`. Câu hỏi tương đương tiếng Việt trả `insufficient_evidence`/`corpus_coverage_gap`; cần sửa/đo lại multilingual retrieval và routing.
- Nguồn AAOS không được ingest do điều khoản hạn chế tái sử dụng; tải MDPI bị 403, PMC gặp lỗi TLS. Hai nguồn không toàn văn kiểm chứng được nên không đưa vào corpus. Nhãn `osteofibroma` vẫn chưa được xác minh với metadata dataset gốc/chuyên gia.
- Giai đoạn 11 **chưa hoàn tất**; chatbot chưa được xây. Không bật sinh câu trả lời hoặc `answer_ready` dựa riêng trên hit.

### Lệnh tiếp tục

```powershell
.\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q
.\.venv\Scripts\python.exe rag/retrieval.py "What did the retrospective cohort report about unicameral bone cysts of the proximal humerus?" --top-k 5
```

Trước tiên xử lý lỗi tiếng Việt trên bằng các câu dev mới; không tuning trên test V2/V3 đã xem. Sau đó mới tìm tiếp nguồn CC BY/được phép, xác minh nhãn `osteofibroma`, bổ sung tập độc lập và đánh giá đủ bằng chứng. Phần dưới ghi lịch sử các vòng trước, giữ nguyên để tra cứu.

## Điểm bàn giao tại phiên trước — 27/10/2026

Lần tiếp tục này đã đọc README tiếng Anh/Việt và toàn bộ Markdown trong `docs/`, đối chiếu code với handoff, rồi chạy toàn bộ suite:

```powershell
\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q
# 36 passed, 28 subtests passed; một Starlette deprecation warning
```

Repository bắt đầu ở `main`, `HEAD=d1ef896` (`Harden RAG policy routing and document handoff`), working tree sạch, local branch ahead `origin/main` một commit. Policy routing mới và 15 regression cases đã commit; đoạn lịch sử ngay dưới đây ghi “chưa commit” tại thời điểm cũ và không còn mô tả trạng thái hiện nay.

**Tiến độ kỹ thuật:** không đổi corpus/index/gold trong lượt này. Giai đoạn 11 vẫn chưa nghiệm thu; strict lexical evidence filter đã thất bại do false refusal, reranker mới được đo trên các tập đã xem, `answer_ready` luôn `false`, và chưa có chatbot.

**Bước phát triển kế tiếp:** mở rộng corpus có kiểm soát. Đã tìm thấy tài liệu AAOS hữu ích cho simple bone cyst và multiple osteochondromas, nhưng chưa ingest vì cần xác minh quyền tái sử dụng. Nhãn `osteofibroma` chưa được tự ý đồng nhất với osteofibrous dysplasia. Xác minh nguồn dữ liệu nhãn và điều khoản trước; sau đó cập nhật `sources.json`, tạo lại corpus/index, gắn lại gold và lưu báo cáo mới vào thư mục mới. Không sửa các tập V2/V3 đã xem rồi gọi chúng là đánh giá độc lập.

Xác minh API/model thật đã hoàn tất: `verify_api.py` trả `API_LOCAL_PARITY_PASSED` cho 3/3 ca, sai lệch score tối đa 0, metadata và hash ảnh khớp; metadata thiếu bị từ chối 422, ảnh hỏng bị từ chối 415. Báo cáo runtime: `api_results/20261027_212246_844539/api_report.json` (Git bỏ qua). Phép này chỉ so với baseline local, không phải notebook parity hay đánh giá lâm sàng.

## Cập nhật phiên làm việc ngày 27/10/2026 lúc 17:27

Đã hoàn thiện và kiểm tra phần routing an toàn cho các câu hỏi có tuyên bố
không được corpus hiện tại xác minh trong `rag/policy.py`. Policy hiện nhận
diện bốn nhóm chính: thuốc/thảo dược/thực phẩm chức năng được cho là chữa
bệnh, thiết bị hoặc xét nghiệm tại nhà hứa hẹn chẩn đoán, yêu cầu giá/chi phí
ngoài kho NCI, và thiết bị/ứng dụng thay thế bác sĩ hoặc chuyên gia. Các câu
này được trả về `insufficient_evidence` trước khi nạp model. Đã bổ sung 15
regression cases tiếng Việt/Anh trong `rag/tests/test_retrieval.py`.

Validation đã chạy bằng môi trường chuẩn `.venv`:

```powershell
.\.venv\Scripts\python.exe -m pytest rag/tests -q
# 20 passed, 21 subtests passed
git diff --check
# không có lỗi whitespace
```

Tại thời điểm bàn giao, hai file dưới đây **đang sửa nhưng chưa commit**:

- `rag/policy.py`
- `rag/tests/test_retrieval.py`

Các thư mục `.pytest_cache/` và `__pycache__/` chỉ là file cache bị Git
ignore, không phải thay đổi cần bàn giao. Không chạy lại API/model thật trong
phiên này vì mục tiêu là hoàn thiện routing và test; API vẫn cần được khởi
động rồi kiểm tra riêng theo hướng dẫn bên dưới.

### Việc làm đầu tiên vào phiên sau

1. Chạy lại `.\.venv\Scripts\python.exe -m pytest rag/tests -q` sau khi mở
   workspace để xác nhận môi trường.
2. Xem `git diff -- rag/policy.py rag/tests/test_retrieval.py`, sau đó quyết
   định commit hai thay đổi này cùng nhau; không commit cache.
3. Nếu tiếp tục giai đoạn 11, tạo một tập câu hỏi mới độc lập để đánh giá
   policy và rerank; không tối ưu thêm chỉ trên V2/V3 đã xem.
4. Bổ sung nguồn cho `simple bone cyst`, `osteofibroma` và
   `synovial osteochondroma`, rồi xây lại corpus/index theo hướng dẫn nếu dữ
   liệu thay đổi.
5. Khi cần xác minh tích hợp, khởi động API trước rồi chạy `verify_api.py`;
   ghi kết quả mới vào tài liệu, không coi việc routing test là kiểm chứng
   độ chính xác lâm sàng.

## Điểm dừng mới nhất sau vòng thử kiểm tra bằng chứng

Ngày 27/10/2026, đã hoàn thành thử nghiệm bổ sung bằng model/index hiện có, không tải thêm model. **Phần xếp hạng lại cải thiện các câu đã biết; bộ lọc đủ bằng chứng bằng từ vựng thất bại vì từ chối nhầm nhiều câu tiếng Việt. Cả hai giữ opt-in, mặc định vẫn hybrid như vòng trước; answer_ready luôn false.** Chưa nghiệm thu giai đoạn 11, chưa có chatbot.

File mới: `rag/evidence.py`, `rag/data/evidence_config.json`, `rag/data/evaluation_evidence_v3.json`, `rag/compare_evidence.py`, `rag/tests/test_evidence.py`. `retrieval.py` và `evaluate.py` thêm cờ `--rerank-concepts` hoặc `--verify-evidence` (không dùng cả hai; không dùng với `--raw`). Corpus/index/gold V2 không thay đổi. Bộ kiểm thử hiện **20/20 đạt**, gồm giữ citation/lọc nguồn, không dùng heading để chứng minh một sự kiện, không cho phép sinh đáp án chỉ từ kết quả kiểm tra, và phân biệt đâu/đau, mẫu/máu trước khi bỏ dấu.

Thiết kế và mục tiêu thử nghiệm đã ghi trước lần đo tại `docs/reference/EVIDENCE_CHECK_DESIGN_VI.md`. V3 gồm 20 câu Việt/Anh (10 dương/10 âm) đóng băng trước lần chạy; do cùng AI soạn, có sự kiện trùng nguồn cũ, **không phải kiểm định độc lập**. Không đổi từ vựng/gold theo kết quả V3 sau khi đã chạy. Các tập test V2/V3 đều đã được xem và phải coi là regression từ phiên sau.

Kết quả cuối tại **`docs/reference/stage11_evidence_rank_20261027/`**, mỗi file lưu hash mã thực thi, cấu hình và gold. Thư mục `stage11_evidence_20261027/` giữ thử nghiệm lọc đầu tiên; `stage11_20261027/` là vòng hybrid trước. Không ghi đè các thư mục đó.

| Bộ câu hỏi | Hybrid mặc định đúng nguồn/đoạn | Thêm xếp hạng khái niệm | MRR sau xếp hạng | Từ chối nhầm câu dương khi lọc nghiêm ngặt |
| --- | --- | --- | --- | --- |
| Regression cũ | 8/10 | **10/10** | 0,950 | 1/10 |
| V2 dev | 6/8 | **8/8** | 0,813 | 5/8 |
| V2 test đã xem | 7/8 | **8/8** | 0,938 | 8/8 |
| V3 stress | 8/10 | **9/10** | 0,750 | 5/10 |

Xếp hạng lại **không** cải thiện từ chối câu âm: V2 vẫn 4/6 mỗi phần, V3 vẫn 0/10. Bộ lọc nghiêm ngặt từ chối toàn bộ câu âm trong phép thử nhưng mất nhiều câu dương; không đạt điều kiện nội bộ đã chốt, không được bật mặc định hoặc quảng bá như giải pháp an toàn. Nó dựa trên độ phủ từ/cụm từ trong một đoạn, không kiểm tra quan hệ, phủ định, số liệu hoặc sự đúng đắn của một kết luận.

### Việc cần tiếp tục chính xác

1. Ưu tiên phương án kiểm tra đủ bằng chứng có xử lý ngôn ngữ tốt hơn. Không tiếp tục thêm từ vào whitelist chỉ để đạt điểm trên V2/V3 đã xem. Các từ tiếng Việt thông dụng như "kiểm tra", "xâm lấn", "nhìn đôi" hiện khiến bộ lọc nghiêm ngặt từ chối nhầm; chồng lấn khái niệm và bỏ dấu vẫn có thể sai.
2. Rà soát phần rerank trên một tập kiểm định mới độc lập trước khi cân nhắc bật mặc định. Rerank xử lý được `q01/q02/p13` cũ, nhưng V3 còn trượt **ep08** (triệu chứng Ewing bằng tiếng Việt). Các ca n05/n06/n11/n12 cũ vẫn thiếu cơ chế quyết định đủ nguồn khi không bật bộ lọc nghiêm ngặt.
3. Tiếp tục bổ sung nguồn cho nhãn thiếu và thẩm định nội dung; nếu corpus đổi phải gắn lại gold và xây lại index theo hướng dẫn bên dưới. Không đưa ứng dụng sang trạng thái chatbot y khoa đã nghiệm thu.

Lệnh tái lập (dùng thư mục mới, runner cố ý từ chối ghi đè):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s rag/tests -v
.\.venv\Scripts\python.exe rag/compare_evidence.py --output-dir .temp/evidence_rerun
.\.venv\Scripts\python.exe rag/retrieval.py "Xét nghiệm nào giúp xác nhận chẩn đoán u xương ác tính?" --rerank-concepts
```

Kết quả phía dưới mô tả lịch sử vòng triển khai trước, được giữ để biết thay đổi nào đã xảy ra. Báo cáo Word **đã cập nhật bản 1.3**, Completion Note và Phụ lục E, xuất qua Word để kiểm tra bố cục **21 trang**. Truy vấn offline sau cùng xác nhận câu về chẩn đoán tìm được `nci-primary-bone-cancer:0014` khi thêm rerank; bộ lọc thử nghiệm trả thiếu bằng chứng cho thuật ngữ chưa biết. Không có tác vụ tải/đánh giá còn chạy.

Cập nhật ngày 27/10/2026 sau vòng sửa trích xuất, thử tìm kiếm kết hợp và đánh giá. Đây là điểm bàn giao cho AI hoặc kỹ sư tiếp tục công việc. Các thay đổi chưa commit từ phiên trước phải được giữ nguyên; mã nền nằm tại commit `59f4dfd`. Giai đoạn 11 chưa nghiệm thu, chưa triển khai chatbot.

## Điểm bắt đầu của phiên hiện tại

- Kho: 12 nguồn NCI, 489 đoạn; chỉ mục local E5 small 384 chiều.
- Baseline trên 12 câu cũ: source+section recall@5 = 0,60, MRR@5 = 0,417; hai câu ngoài phạm vi chưa được từ chối.
- `rag/build_index.py`, `rag/retrieval.py`, `rag/evaluate.py` đã có. Chưa có chatbot.

## Những việc đã thực hiện trong phiên này

1. Lưu baseline top-10 của corpus cũ tại `docs/reference/rag_baseline_20261027.json` trước khi sửa dữ liệu.
2. Sửa `rag/build_corpus.py`: nhận heading h5/h6 để loại References, chèn khoảng trắng ở block/ô bảng lồng nhau, giữ các mục danh sách ngắn như Pain và Swelling. Corpus hiện có **416 đoạn từ cùng 12 nguồn**, không phải 489 đoạn. ID đoạn của bản cũ có thể đổi; không dùng ID cũ để trỏ vào corpus mới.
3. Xây lại chỉ mục local, schema 2. Manifest kiểm tra cả tokenizer, pooling và cấu hình embedding, ngoài trọng số/model/corpus/vector; kiểm tra vector hữu hạn và chuẩn hóa L2.
4. Thêm `rag/lexical.py`: mở rộng từ khóa Việt–Anh theo cụm dài nhất, BM25 và reciprocal rank fusion. Cấu hình nằm ở `rag/data/retrieval_config.json`, trọng số original dense/expanded dense/BM25 = 2/1/1, hằng số RRF 60, cửa sổ 80. Đây là từ điển do AI soạn, không phải mô hình dịch hay nội dung y khoa đã thẩm định.
5. Thêm `rag/policy.py` để nhận diện một số yêu cầu liều điều trị, kết luận từ ảnh/model score, thay đổi chỉ dẫn, ngoài chủ đề và nhãn chưa đủ nguồn. Bộ quy tắc còn bỏ lọt câu có chủ đề u xương nhưng không có bằng chứng; không phải bộ bảo vệ đầy đủ cho chatbot.
6. CLI `rag/retrieval.py` mặc định dùng hybrid và routing; `--raw` bỏ qua routing, `--mode dense` dùng baseline. Python `search()` vẫn mặc định dense/raw để so sánh; `retrieve()` trả trạng thái và hit. `candidates_found` chỉ nghĩa là có ứng viên; **answer_ready luôn false**, chưa cho phép tự sinh kết luận.
7. Thêm `rag/data/evaluation_v2.json`: **28 câu**, tách dev/test trước lần đo (mỗi phần 8 câu có đáp án và 6 câu âm). Gold khóa bằng nguồn/mục/mã băm đoạn và trích đoạn ngắn. Tập do cùng AI soạn, chưa được chuyên gia độc lập rà soát. Phần test đã được chạy và xem kết quả trong phiên này; từ phiên sau không được coi nó là tập chưa từng thấy.
8. `rag/evaluate.py` lưu toàn bộ hit, gold rank, trạng thái, hash corpus/config/mã thực thi. `rag/compare.py` chạy các phép so sánh với một lần nạp model. Kết quả cuối ở `docs/reference/stage11_20261027/`; các file rời `rag_clean_dense_20261027.json` và `rag_hybrid_regression_20261027.json` là thử nghiệm trung gian trên corpus 415 đoạn, không phải bản cuối.

## Kết quả cuối của vòng này

| Bộ câu hỏi | Cách chạy | Recall@5 | MRR@5 | Không trả hit cho câu âm |
| --- | --- | --- | --- | --- |
| 12 câu cũ, corpus cũ | Dense trước sửa | 6/10 | 0,417 | 0/2 |
| 12 câu cũ, corpus 416 đoạn | Dense | 7/10 | 0,483 | 0/2 |
| 12 câu cũ, corpus 416 đoạn | Hybrid có routing | 8/10 | 0,700 | 2/2 |
| V2 dev | Dense | 5/8 | 0,542 | 0/6 |
| V2 dev | Hybrid có routing | 6/8 | 0,625 | 4/6 |
| V2 test | Dense | 6/8 | 0,542 | 0/6 |
| V2 test | Hybrid có routing | 7/8 | 0,713 | 4/6 |

Recall của bộ cũ xét đúng nguồn và mục; V2 yêu cầu đúng đoạn bằng chứng theo mã băm, nên không so trực tiếp hai thước đo. Không có câu có đáp án bị routing chặn trong bộ này. Kết quả mới là bằng chứng kỹ thuật ban đầu, không chứng minh khả năng tổng quát hay an toàn lâm sàng.

Kiểm thử RAG: **12/12 đạt**; bao gồm lỗi h6, từ ngắn bị mất, dữ liệu dính chữ, sai tokenizer, lọc nguồn, routing trước khi nạp model, và không tính hit chỉ vì cùng tên mục nhưng khác đoạn bằng chứng. Các bài kiểm thử ứng dụng cũ không được chạy lại trong vòng sửa RAG này.

## Ca trượt ghi nhận ở vòng hybrid trước

- Regression `q01`, `q02`: vẫn chưa tìm đúng nguồn/mục về nguyên phát so với di căn và xác nhận chẩn đoán.
- V2 dev `p01`, `p02`: thiếu bằng chứng đúng về lan tràn của u lành và các cách sinh thiết.
- V2 test `p13`: câu về bác sĩ giải phẫu bệnh và kính hiển vi ở chondrosarcoma; chỉ trả các đoạn định nghĩa trong top 5.
- V2 dev `n05`, `n06`: vẫn trả ứng viên cho nước ép cần tây và phí sinh thiết tại bệnh viện địa phương.
- V2 test `n11`, `n12`: vẫn trả ứng viên cho xét nghiệm DNA tại nhà bảo đảm phát hiện sớm và thực phẩm chức năng chữa khỏi chordoma. **Chưa có bộ kiểm tra đủ bằng chứng theo nội dung câu hỏi.**

## Hướng công việc ghi ở vòng trước

1. Đọc các hit và gold trong báo cáo cuối, phân biệt lỗi xếp hạng với thiếu nguồn. Giữ số liệu đã ghi; không đổi gold hoặc thêm cụm từ vào policy chỉ để che các ca test trượt.
2. Bổ sung nguồn chuyên biệt cho các nhãn còn thiếu, ghi quyền sử dụng và nguồn gốc, rồi rà soát chuyên môn. `osteochondroma` và `giant cell tumor` mới có nội dung rải rác; một lần nhắc tên không đủ coi là đã phủ nhãn.
3. Thử bước xếp hạng lại/evidence verification và xử lý câu mơ hồ. Chọn phương án dựa trên dev/regression; sau đó cần tập test mới do người hoặc AI độc lập soạn và chuyên gia rà soát. V2 test đã tiêu thụ.
4. Đặt tiêu chí nghiệm thu trước lần kiểm định mới, gồm tỷ lệ truy xuất đúng đoạn và từ chối câu không có nguồn. Chưa có threshold cosine được hiệu chỉnh; score giữ nguyên là cosine của câu hỏi gốc, ranking_score là RRF, không chuyển đổi thành xác suất.
5. Sau khi corpus đổi, rà soát và gắn lại evidence trong evaluation_v2; công cụ cố ý báo lỗi nếu hash corpus/gold cũ. Sau khi model/tokenizer hoặc format index đổi, xây lại index. Chỉ sang nghiệm thu chatbot khi retrieval và kiểm tra đủ bằng chứng được xác minh.

## Lệnh tái lập

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s rag/tests -v
.\.venv\Scripts\python.exe rag/build_index.py
.\.venv\Scripts\python.exe rag/compare.py --output-dir .temp/stage11_rerun
.\.venv\Scripts\python.exe rag/retrieval.py "Ewing sarcoma di căn thường lan đến đâu?"
```

Đối chiếu `.temp/stage11_rerun/summary.json` với `docs/reference/stage11_20261027/summary.json`; không ghi đè bằng chứng cũ. Chỉ dùng `--download-model` nếu máy chưa có model. Model/cache/index không được Git theo dõi; corpus, config, bộ câu hỏi và báo cáo JSON có thể dùng để tái dựng. Mã băm corpus cuối: `176311a556429af4fb3b2c2e327851b957463a1e57300fc9df973182a0a8a035`.

## Khi tiếp quản

Đọc file này trước, sau đó `PROJECT_STATUS_VI.md` và `guides/README_RAG_INDEX_VI.md`. Kiểm tra `git status` và đọc code thay đổi trước khi sửa. Chạy kiểm thử RAG bằng `.\.venv\Scripts\python.exe -m unittest discover -s rag/tests -v`. Không đánh dấu giai đoạn 11 hoàn thành chỉ vì chỉ mục hoặc lệnh chạy thành công.

## Kiểm tra trước khi kết thúc vòng hybrid trước

- Truy vấn offline sau cùng: câu Ewing di căn trả `nci-ewing-patient:0017` kèm URL; yêu cầu liều hóa trị trả `out_of_scope`, không có hit. Không có lệnh tải hoặc đánh giá còn đang chạy.
- Liên kết Markdown trong docs và README đã được kiểm tra; `git diff --check` đạt.
- `docs/reports/Bao_cao_tien_do.docx` đã cập nhật bản **1.2**, Completion Note giai đoạn 10–11 và phụ lục D; đã xuất qua Word và kiểm tra bố cục **20 trang**. File PDF/PNG trong `.temp` chỉ phục vụ kiểm tra, không phải đầu ra cần bàn giao.
- Điểm tiếp tục cụ thể: **đánh giá phương án xếp hạng lại và kiểm tra đủ bằng chứng**, sau đó bổ sung nguồn và dùng tập kiểm định độc lập mới. Không được coi `candidates_found` là đủ điều kiện sinh câu trả lời.

## Cập nhật an toàn giao diện — 28/10/2026

- Trang phân tích, lịch sử và chi tiết ca nay trình bày output softmax dạng số `0–1` với bốn chữ số thập phân; không đổi payload API. Biểu đồ thanh chỉ là cách hiển thị tương đối của cùng output.
- Cảnh báo trên các trang ảnh/lịch sử nêu rõ prototype chỉ cho học tập/nghiên cứu, không dùng để chẩn đoán, sàng lọc, phân loại cấp cứu hay quyết định điều trị; softmax chưa hiệu chuẩn cho lâm sàng và không được diễn giải thành xác suất mắc bệnh. API `/predict` có notice tương ứng.
- Kiểm tra giao diện/API sau đổi: `api_tests/test_api.py` và `ui_tests/test_ui_routes.py`, 11 passed. Full suite vừa chạy ([run record](reference/stage11_test_run_20261028_offline_license_guard.json)): 68 passed, 79 subtests passed (một cảnh báo deprecation Starlette); audit integrity PASS 21 nguồn/759 chunk, đủ 9 bộ dữ liệu và 16 báo cáo, không lỗi; replay PASS 16/16. Báo cáo: [audit](reference/stage11_integrity_audit_20261028_offline_license_guard.json), SHA-256 `ebb77c1a3f828aa58086e33fcc4fdafa357e9f48cbde153c52710b1ea1cb3e04`; [replay](reference/stage11_replay_20261028_offline_license_guard.json), SHA-256 `ef83358b6ebccdc41c28e32ef0a75d8a7336cae81686485fe730166d4b07e08c`. Đây là kiểm tra kỹ thuật, không xác nhận hiệu năng hoặc an toàn lâm sàng.
- Tóm tắt snapshot hợp nhất (source/cache, corpus, audit, replay, run record, UI softmax và hash rà soát nguồn trực tuyến): [verification summary](reference/stage11_verification_summary_20261028_offline_license_guard.json), SHA-256 `617b1ee956def964fbff7a3027b8ca5eab69c1c783fedb231a21528e884369e1`.

Lưu ý thời điểm: full suite được chạy trước các bổ sung tài liệu governance và chẩn đoán lỗi strict lexical ở cuối handoff này. `implementation_hashes` trong run record giữ nguyên hash handoff tại đúng thời điểm chạy; sau lần chạy không sửa mã thực thi, cấu hình, corpus hoặc test. Các kiểm tra tài liệu/hash mới không được trình bày như một lần chạy pytest khác.

## Chẩn đoán lỗi từ chối nhầm của strict lexical trên OFD — 28/10/2026

Đọc trực tiếp 7 truy vấn và `evidence_check` trong report strict đã pin tại `stage11_policy_rerun_20261028_post_personal_image_outcome_context_v2/osteofibrous_dysplasia_dev_strict.json` (SHA-256 `ab6c4ab99b7130920136473b35f66c7dfc794ff77c369c729dd400076f5bf7b1`): chỉ **1/5** truy vấn dương qua; 2 truy vấn âm bị abstain theo policy. Các chẩn đoán của 4 ca dương bị từ chối:

- `ofd01`: cụm tiếng Việt “xấp xỉ” bị accent-fold thành hai token, và `xi` trở thành literal bắt buộc dù câu hỏi đang hỏi con số xấp xỉ; đây là lỗi phân đoạn/diễn đạt, không phải thiếu nguồn.
- `ofd02`: câu Việt–Anh pha trộn có unknown `vo`, literal `intra/cortical/mid/shaft` và còn thiếu literal `tissue`; so khớp cụm/cross-language hiện không mô hình hóa tương đương khái niệm.
- `ofd03`: nhiều từ mô tả X-quang phổ thông bị đánh dấu unknown (`ton`, `tieu`, `lech`, `tam`, `phia`, `gian`, `vo`, `lan`, `vao`, `tuy`) và concept `symptoms` bị thiếu; câu hỏi không thể qua ngưỡng strict.
- `ofd05`: “thống kê gộp” phân thành unknown `thong/tich/gop`, trong khi `he` thành literal bắt buộc; filter không hiểu paraphrase Việt của “systematic review/meta-analysis”.

Đây là chẩn đoán lỗi của bộ parse hiện tại trên dev đã xem, không phải ước lượng tổng quát và không biện minh cho việc thêm từng token vào whitelist. Giữ `--verify-evidence` opt-in; không đổi `require_known_query_terms` dựa trên báo cáo này. Hướng cần nghiên cứu là biểu diễn truy vấn đa ngôn ngữ theo khái niệm có provenance và giữ qualifier/quan hệ, sau đó đánh giá trên bộ mới được reviewer độc lập khóa trước; ngay cả độ phủ khái niệm vẫn không chứng minh entailment.


## Checkpoint trước đó — 29/10/2026 13:39:42 ICT (lịch sử)

Da luu [checkpoint moi nhat](STAGE11_CHECKPOINT_LATEST.md) va ban ZIP trong `checkpoints/20261029_133942/` (nay la snapshot lich su; ban moi nhat la `checkpoints/20261029_081419/`). Bundle continuation v2 da build 16/16 report; audit PASS, replay PASS 16/16; 0 report doi metrics so voi v8. Bundle v1 bi ngat va audit FAIL cua bundle mac dinh cu duoc giu de truy vet. Manifest checkpoint ghi hash hien tai, thay cho governance/doc hashes lich su v8 khi doi chieu workspace. Stage 11 chua nghiem thu: 7/7 gates Open, `answer_ready=false`; ~85% chi la uoc luong chuan bi cu.


- Full regression re-run `api_tests rag/tests tests ui_tests`: **79 passed, 127 subtests passed**, 1 Starlette deprecation warning; record và hash implementation: [continuation full-suite record](reference/stage11_test_run_20261029_continuation_full.json). Đây là software regression, không phải nghiệm thu lâm sàng/độc lập.


### Unknown-token gate diagnostic — 29/10/2026

Chạy lại so sánh trên 5 strict reports của bundle continuation v2, chỉ tắt `require_known_query_terms` trong bộ nhớ. Trong 40 positive đã xem, 19 còn ứng viên (positive abstention 21/40 = 52,5%); 14/14 negative vẫn abstain, 0 false candidate accept. Đây vẫn là lexical coverage, không kiểm tra entailment; các tập in-sample nên không bật checker production. Cấu hình production không đổi. [Artifact và query-level kết quả](reference/stage11_evidence_unknown_token_gate_experiment_20261029_continuation_v1.json).


### Recheck workspace 29/10/2026
Full regression trên trạng thái hiện tại: **79 passed, 127 subtests passed**, 1 cảnh báo deprecation Starlette, exit code 0. Record và SHA-256 implementation: [continuation recheck](reference/stage11_test_run_20261029_continuation_recheck.json). Kết quả chỉ xác nhận regression phần mềm. 7/7 acceptance gates vẫn Open; `answer_ready=false`.


Recheck ngày 29/10 trên bundle continuation v2: audit provenance PASS cho 21 nguồn/759 chunks/9 bộ đánh giá, cache đầy đủ; replay PASS 16/16 (0 preflight mismatch). [Audit](reference/stage11_integrity_audit_20261029_continuation_recheck.json) · [Replay](reference/stage11_replay_20261029_continuation_recheck.json). Hash được ghi tại [recheck full regression](reference/stage11_test_run_20261029_continuation_recheck.json) và hai JSON recheck; đây không phải clinical validation.

Dùng [register trạng thái 7 acceptance gates](reference/stage11_acceptance_gate_status_20261029.csv) khi bàn giao: mọi cổng còn `OPEN`; bảng ghi riêng chứng cứ đóng cần thu và artifact/missing evidence hiện tại.


## Checkpoint mới — 29/10/2026 14:03 ICT
Tạo bằng `tools/create_project_checkpoint.py` và tự verify ngay sau khi ghi; kiểm tra lặp lại độc lập cũng PASS. Snapshot: `checkpoints/20261029_070343/project_snapshot.zip` (763 file; 163,178,097 byte giải nén; ZIP 133,472,911 byte). Archive SHA-256 `50d2dd6f2dcd87cafeb1c654ddaff284551f8c1d9364c4c1ba6b042db1ca0fd7`; manifest SHA-256 `3d1d5392edee8f21eaf0483e5169b900827b5b1e96cc654951144d19f48e0524`. Manifest ghi HEAD `b6d67fbfea778a8abfe40b9d012dd3f99b0de0ff`, audit/replay PASS, 16/16 reports, 0 preflight mismatch, 0/7 gates, `answer_ready=false`. ZIP chứa source cache và recheck/register; bỏ `.git`, `.venv` và checkpoint cũ. Không tạo commit hay thay đổi staging.


Register được mở rộng thêm vai trò chịu trách nhiệm và phụ thuộc gate cho từng mục. QA lại: 7/7 dòng có owner role, prerequisite, evidence, gap và đường dẫn artifact tồn tại; tất cả OPEN. Thay đổi này xảy ra sau ZIP `20261029_070343`, nên snapshot hiện hành cần được cập nhật ở lần đóng gói tới.

For G1 handoff, review [function-specific intended-use draft](reference/STAGE11_INTENDED_USE_DRAFT_FOR_OWNER_REVIEW_20261029.md) against intended-use lock template. It is unsigned and does not change G1 status; `answer_ready=false`.

G5 có [5 preliminary hazard prompts](reference/stage11_preliminary_hazard_scenarios_20261029.csv) làm đầu vào reviewer. Kịch bản freshness/context/provenance trong RAG được ghi như prompt để reviewer thẩm định; đây chưa phải hazard analysis hoàn tất; chưa gán severity/likelihood/residual risk, chưa xác nhận hazard và chưa có safety-lead sign-off.

G6 handoff có [baseline privacy/security 16 mục](reference/stage11_privacy_security_baseline_20261029.csv); phân biệt gap đã thấy trong code với các mục chưa thể đánh giá ở runtime/jurisdiction. Không có mục pass; cần reviewer và bằng chứng trên intended use/deployment được khóa.


## Checkpoint cập nhật — 29/10/2026 14:08 ICT
Snapshot `checkpoints/20261029_070849/project_snapshot.zip` gồm 766 file / 163,203,941 byte giải nén (archive 133,484,453 byte), đã tự verify và được xác minh lại độc lập: 766 member, CRC PASS. SHA-256 ZIP `76433eaa32b346163bac0dac8570770524c951d154c5af59548c4f4ebbb35ed7`; manifest SHA-256 `8740df9a5052e334c65ed274478db4f270d3a48d6dbb8e04a75f15a28aece5c7`. Manifest ghi HEAD `b6d67fbfea778a8abfe40b9d012dd3f99b0de0ff`, audit/replay PASS, 16 reports, 0/7 gates, `answer_ready=false`. Snapshot đã chứa intended-use draft, 4 hazard scenarios, 16-item privacy baseline, reviewer packet và updated gate register. Các cập nhật tự tham chiếu đoạn này sẽ nằm ở checkpoint sau.

Latest software regression after adding checkpoint tool coverage: **83 passed, 130 subtests, 1 Starlette deprecation warning**, exit 0. Four focused checkpoint tests (three subtests) also pass; [record](reference/stage11_test_run_20261029_checkpoint_tool_full.json), SHA-256 `58f749a486b26b0d3cd91c0714c2e439e5e2236d3302d3cc80bc9a6aa636445d`.

G4: xem [cohort screening register](reference/stage11_external_cohort_screening_register_20261029.csv) cho 10 candidate; chưa có bộ nào đủ access + image rights + reference standard + independence/overlap evidence. Không gọi external test cho đến khi các điều kiện được xác minh.

G3 dùng [evidence-group label sheet](reference/stage11_retrieval_evidence_group_label_template_20261029.csv) để chấm relevance và support relation riêng. Citation entailment của generated claims là N/A/not evaluable ở snapshot retrieval-only hiện tại; cần human labels/adjudication cho query-evidence support, gate vẫn OPEN.


## Checkpoint cập nhật — 29/10/2026 14:14 ICT
Snapshot `checkpoints/20261029_071435/project_snapshot.zip` gồm 770 file / 163,223,037 byte giải nén (archive 133,492,269 byte). Tự verify sau khi tạo và xác minh chỉ đọc độc lập: **PASS**, 770 file, CRC PASS. ZIP SHA-256 `d2cb184e2e3c9b4886d4a752f1399a1338a983d3ee3e38e9388371e4bbc7d5aa`; manifest SHA-256 `78fd2e01a8ccb027f595c8769e8c861536596776ad1711ba9b8aa5fa8e05c2d9`. HEAD `b6d67fbfea778a8abfe40b9d012dd3f99b0de0ff`; readiness metadata PASS; audit/replay PASS, 16 reports, 0 mismatches; 0/7 gates closed; `answer_ready=false`. Archive includes G3 evidence-group template, G4 cohort register, latest full regression record and all previous worktree evidence. The note additions about this ZIP were made after archive creation and will be in the next snapshot.


Expanded documentation link QA across all 28 Markdown files in `docs/`: checked 444 local links, fixed one broken relative path in continuation notes, rerun 444 checked / 0 missing. This is workspace link-integrity only; external URLs were not fetched.
