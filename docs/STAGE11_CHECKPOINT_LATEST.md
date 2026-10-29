# Checkpoint dự án BoneScope — bản mới nhất 29/10/2026

## Checkpoint mới nhất đã xác minh

`checkpoints/20261029_093707/project_snapshot.zip`: **836 files**, 164,803,676 bytes giải nén; SHA-256 `61775e31dd4d0d31ac44448896d76a0d3967be02eccd6e428d43a6414bbde604`. Utility verifier PASS: 836 files, ZIP CRC PASS. Snapshot includes Vietnam regulatory source register, G7 source review, synchronized 23/23 prepared-artifact QA v4, the gate-closure blocker matrix and current project reports/progress. All seven gates remain OPEN; `answer_ready=false`.

## QA tài liệu mới nhất

QA liên kết mới nhất: 600 local links trong 31 Markdown files ở `docs/`, không có đích thiếu. Register cohort có 15 dòng, gate register 7 dòng; structural QA v4 xác nhận 23/23 prepared artifacts tồn tại và hash khớp. `git diff --check` sạch; Git chỉ báo cảnh báo chuẩn hóa LF/CRLF. G5 đã bổ sung prompt sơ bộ về stale/mâu thuẫn/mất ngữ cảnh hoặc sai provenance của passage RAG; rating và sign-off vẫn để trống. Gate QA v4 kiểm tra 23 prepared-artifact references, gồm registry G7; mọi hash khớp sau khi tái lập record. Các pointer được đồng bộ sau khi tạo ZIP.

Goal, phần trăm tiến độ và checklist bàn giao được lưu tại [STAGE11_PROGRESS_2026-10-29.md](STAGE11_PROGRESS_2026-10-29.md) và [STAGE11_EXECUTION_PLAN_VI.md](STAGE11_EXECUTION_PLAN_VI.md); register CSV liên kết trong tài liệu là nguồn trạng thái từng cổng.

## Cập nhật retrieval sau snapshot trước

Route ABC soft preference đã được thêm và kiểm tra trên dev: expansion Recall@5 0,955→1,000, MRR 0,644→0,689; negative abstention giữ 3/3; 7 dev datasets khác không đổi. Bundle comparison đổi đúng một report trong 16, các test đã xem không đổi. Regression 86/132 PASS, audit PASS, replay 16/16 PASS. Đây không phải kiểm định độc lập. [Experiment](reference/stage11_cureus_abc_route_dev_experiment_20261029.json) · [Bundle](reference/stage11_policy_rerun_20261029_cureus_abcrouting_v1/manifest.json) · [Audit](reference/stage11_integrity_audit_20261029_cureus_abcrouting_v1.json) · [Replay](reference/stage11_replay_20261029_cureus_abcrouting_v1.json) · [Test record](reference/stage11_test_run_20261029_cureus_abcrouting_full.json).

## Privacy minimization follow-up

Case mới chỉ lưu nhãn tên file chung `uploaded-image.<suffix>`; API test xác nhận filename tổng hợp có identifier không được persist. Không migrate dữ liệu cũ, không bỏ hash/metadata/comments, chưa xác minh DB/WAL/backup/runtime; G6 vẫn OPEN. Full suite 86/132 PASS. [Test record](reference/stage11_test_run_20261029_privacy_filename_minimization_full.json).

## Snapshot trước đó (lịch sử): archive sau cập nhật source/retrieval

`checkpoints/20261029_080012/project_snapshot.zip`: **819 files**, 164,658,400 bytes giải nén, SHA-256 `1ddada26f810ec5f030d4b24d267f3e66af59e38f42ec37c503fb3aed0c3d7fe`. Tạo bởi checkpoint utility và tự xác minh **PASS** (819 files, CRC PASS). Archive bao gồm execution plan Giai đoạn 11, route ABC và dev experiment, filename minimization code/test, payload source-cache tibia, corpus/source lock, evaluation dev, bundle 16 report, audit/replay, full regression 86/132, Link QA 497/497 và tài liệu cập nhật; loại virtualenv và các checkpoint cũ. ZIP tự xác minh PASS ngay sau tạo; các dòng cập nhật con trỏ/hash trong status/checkpoint note được đồng bộ ngay sau đó. Completion state vẫn 0/7 gates, `answer_ready=false`.

## Bản lưu tiếp nối mới nhất — 29/10/2026

Sau phần cập nhật hồ sơ G4 và đồng bộ status, đã tạo `checkpoints/20261029_072041/project_snapshot.zip`: 770 files, 163,232,924 bytes giải nén, SHA-256 `3cd37faf029317cdc1bb7ea28847372604e4a3b614b858b8fd8ac80728e12d10`. Tự xác minh sau tạo **PASS**, 770/770 files và ZIP CRC PASS. Link QA tại bản ghi: **458/458** local Markdown links trong `docs/`, 0 lỗi.

### Tiếp nối source/retrieval 29/10/2026

- Nguồn CC BY 4.0 tibia lesion đã thêm: 22 nguồn/794 chunk, index 794×384. Full suite 85/130; 10 evaluation datasets trong audit PASS; replay 16/16 PASS. Bốn trên 16 reports có metric changes; chi tiết ở [ingestion/comparison record](reference/stage11_tibia_source_ingestion_20261029.json).
- Snapshot tiếp nối đã lưu sau đoạn này trong `checkpoints/`; dùng ZIP manifest/hash mới nhất làm bằng chứng archive. Tình trạng nghiệm thu không đổi: 0/7 gates; `answer_ready=false`.

Lead Zenodo 10.5281/zenodo.13858808 đã được ghi thành C11 trong [register](reference/stage11_external_cohort_screening_register_20261029.csv) và [online source review](reference/stage11_online_evidence_review_20261028.md): 10.1 GB files restricted; không thấy license/quyền ảnh; không tải/ingest; NOT ELIGIBLE / NOT EVALUABLE. Có 11 ứng viên G4, chưa ứng viên nào được cleared. Tiến độ chuẩn bị vẫn ước lượng ~85%; acceptance 0/7; `answer_ready=false`.

Checkpoint theo yeu cau luu toan bo tien trinh. Ma nguon, tai lieu, cau hinh, model duoc Git theo doi va cache nguon van ban duoc dong goi vao `checkpoints/20261029_081419/project_snapshot.zip`; danh sach file, SHA-256, Git HEAD, branch, status va ban diff nam cung thu muc. Checkpoint mới nhất hiện tại là `checkpoints/20261029_093707/project_snapshot.zip`; các ghi chú snapshot tiếp nối phía dưới là lịch sử. Khong thay doi index/staging hay tao commit.

## Trang thai da xac minh

- Stage 11 van dang thuc hien; uoc luong cu ~85% chi la phan chuan bi trong workspace, khong phai ti le nghiem thu. 7/7 cong nghiem thu doc lap van Open; `answer_ready=false`.
- Bundle continuation v2 gom 16 bao cao; audit PASS cho 21 nguon, 759 chunks, index 759 x 384, 9 datasets. Replay PASS 16/16, preflight khong mismatch. So bao cao doi metric so voi v8: 0.
- [Audit PASS](reference/stage11_integrity_audit_20261029_continuation_v2.json), [Replay PASS](reference/stage11_replay_20261029_continuation_v2.json), [Manifest moi](reference/stage11_policy_rerun_20261029_continuation_v2/manifest.json), [Comparison](reference/stage11_policy_rerun_20261029_continuation_v2/comparison.json).
- Ket qua chi xac minh tinh toan ven/tai lap tren dev da xem; khong chung minh clinical validity hoac citation entailment.
- `stage11_integrity_audit_20261029_continuation_latest.json` la FAIL cua bundle mac dinh cu do hash evaluator/evidence_config khong con khop. Khong dung no lam ket luan ve bundle v2. V8 va governance/doc hashes cua no la snapshot lich su; file manifest checkpoint nay luu hash hien tai.
- `stage11_policy_rerun_20261029_continuation_v1` bi ngat sau 3 report, khong co manifest hoan chinh; giu de truy vet, khong dung lam bundle nghiem thu.

## Tiep tuc tu day

1. Doc checkpoint nay, bao cao Stage 11, handoff va reviewer packet. Kiem tra Git diff/usage va hash truoc khi sua.
2. Dung `.venv/Scripts/python.exe`. Python mac dinh thieu numpy. Chon ro bundle continuation v2 khi audit/replay; cac default hien tro bundle lich su.
3. Lay reviewer doc lap, khoa intended use va blind protocol, thu nhan labels/adjudication thuc te, xac minh entailment/false acceptance/refusal; giu 7 gate Open toi khi co bang chung va chu ky thuc.
4. Nhanh anh 11A can quyen su dung, reference standard, patient-level manifest va overlap clearance; candidate upon-request chua du dieu kien external validation. Khong tu lien he ben ngoai.
5. Bao cao Word v1.7 ngay 27/10 la snapshot cu; dung bao cao Markdown ngay 29/10 va checkpoint nay.

## Pham vi ban luu

ZIP gom tat ca file hien co do Git theo doi hoac untracked khong bi ignore, cong `rag/source_cache`. Deleted tracked files duoc ghi trong Git status/diff. Du lieu/model/cache/index bi ignore khac van nam tai vi tri goc; day khong phai backup toan bo runtime. Dung hash va provenance trong audit de doi chieu truoc khi tai lap. Checkpoint khong chua `.git`, `.venv` hoac cac checkpoint cu.


- Full regression re-run `api_tests rag/tests tests ui_tests`: **79 passed, 127 subtests passed**, 1 Starlette deprecation warning; record và hash implementation: [continuation full-suite record](reference/stage11_test_run_20261029_continuation_full.json). Đây là software regression, không phải nghiệm thu lâm sàng/độc lập.


### Unknown-token gate diagnostic — 29/10/2026

Chạy lại so sánh trên 5 strict reports của bundle continuation v2, chỉ tắt `require_known_query_terms` trong bộ nhớ. Trong 40 positive đã xem, 19 còn ứng viên (positive abstention 21/40 = 52,5%); 14/14 negative vẫn abstain, 0 false candidate accept. Đây vẫn là lexical coverage, không kiểm tra entailment; các tập in-sample nên không bật checker production. Cấu hình production không đổi. [Artifact và query-level kết quả](reference/stage11_evidence_unknown_token_gate_experiment_20261029_continuation_v1.json).


### Recheck sau checkpoint — 29/10/2026
Full regression trên workspace hiện tại đạt **79 passed, 127 subtests passed**, 1 cảnh báo Starlette, exit code 0. Record/hash: [continuation recheck](reference/stage11_test_run_20261029_continuation_recheck.json). ZIP ở trên là checkpoint trước recheck; source tree có record/docs recheck mới này, sẽ gói vào snapshot kế tiếp. Không có sửa implementation.


### Audit/replay recheck bổ sung — 29/10/2026
Bundle continuation v2 được audit lại: PASS, 21 nguồn, 759 chunks, 9 evaluation sets, cache đầy đủ. Replay PASS 16/16, không có preflight mismatch. SHA-256 audit `3e721c69e61e109d629f1c7a2043f636a4e6b98e72f143435e04b68d8171aa02`; replay `49140e27f554bd19833e9802f80630615219383d45b85c2fb1b800ce62d0f633`. Cả hai artifact recheck hiện nằm trong workspace; ZIP checkpoint trước đó chưa gồm chúng.


### Gate register — 29/10/2026
Đã tạo [register trạng thái 7 cổng](reference/stage11_acceptance_gate_status_20261029.csv) với điều kiện đóng, artifact chuẩn bị và khoảng trống theo từng gate. Tất cả vẫn OPEN; register không phải sign-off. ZIP hiện hành chưa gồm register mới.

Gate register QA: đủ 7 dòng G1–G7, cả 7 `OPEN`, không bỏ trống trường thiết yếu và mọi đường dẫn artifact trong bảng đã được xác minh tồn tại tại workspace. Việc tồn tại chỉ chứng minh hồ sơ/mẫu đã chuẩn bị, không chứng minh sign-off hoặc nghiệm thu.


## Tạo checkpoint lặp lại được
Dùng `python tools/create_project_checkpoint.py --dry-run` để xem số file/kích thước trước khi đóng gói; sau đó chạy `python tools/create_project_checkpoint.py` để tạo thư mục timestamp trong `checkpoints/`. Xác minh snapshot bằng `python tools/create_project_checkpoint.py --verify-dir checkpoints/<timestamp>`; verifier kiểm SHA-256 của archive và từng thành viên, kích thước, danh sách manifest và ZIP CRC. Công cụ đóng gói file tracked đang có và untracked không bị ignore, thêm `rag/source_cache`, ghi SHA-256 từng file và ZIP, Git HEAD/branch/status/patch, cùng snapshot audit/replay/acceptance gate từ record trong workspace; loại `.git`, `.venv`, cache/runtime bị ignore và checkpoint cũ. Kiểm tra lựa chọn hiện hành đã gồm gate register và các artifact recheck mới.


Sau khi tạo ZIP, công cụ tự gọi verifier và chỉ báo thành công khi toàn bộ kiểm tra qua. Verifier mới đã chạy chỉ đọc trên snapshot `20261029_133942`: **PASS**, 756 file, CRC PASS, archive SHA-256 khớp `4a22160be756aadbaceba0a40b5743ea83e6f525e03beaef5dd31ae7f2d40e03`. Đây xác nhận ZIP cũ nguyên vẹn; không có nghĩa ZIP cũ chứa các recheck/register được tạo sau đó.

Manifest generator đã được bổ sung để tự lấy audit/replay mới nhất, số report, preflight mismatch, số gate đóng/tổng và `answer_ready=false`; smoke check trả PASS/PASS, 16 replay, 0 mismatch, 0/7 gate.


## Checkpoint mới — 29/10/2026 14:03 ICT
Tạo bằng `tools/create_project_checkpoint.py` và tự verify ngay sau khi ghi; kiểm tra lặp lại độc lập cũng PASS. Snapshot: `checkpoints/20261029_070343/project_snapshot.zip` (763 file; 163,178,097 byte giải nén; ZIP 133,472,911 byte). Archive SHA-256 `50d2dd6f2dcd87cafeb1c654ddaff284551f8c1d9364c4c1ba6b042db1ca0fd7`; manifest SHA-256 `3d1d5392edee8f21eaf0483e5169b900827b5b1e96cc654951144d19f48e0524`. Manifest ghi HEAD `b6d67fbfea778a8abfe40b9d012dd3f99b0de0ff`, audit/replay PASS, 16/16 reports, 0 preflight mismatch, 0/7 gates, `answer_ready=false`. ZIP chứa source cache và recheck/register; bỏ `.git`, `.venv` và checkpoint cũ. Không tạo commit hay thay đổi staging.


Register được mở rộng thêm vai trò chịu trách nhiệm và phụ thuộc gate cho từng mục. QA lại: 7/7 dòng có owner role, prerequisite, evidence, gap và đường dẫn artifact tồn tại; tất cả OPEN. Thay đổi này xảy ra sau ZIP `20261029_070343`, nên snapshot hiện hành cần được cập nhật ở lần đóng gói tới.


Đã bổ sung [intended-use draft for owner review](reference/STAGE11_INTENDED_USE_DRAFT_FOR_OWNER_REVIEW_20261029.md), tách classifier ảnh, text RAG, case storage và deployment, với giới hạn và quyết định cần owner/reviewer. Chưa ký nên G1 vẫn OPEN. File này được tạo sau ZIP hiện hành và sẽ được đưa vào checkpoint tiếp theo.


### Safety prep — 29/10/2026
Đã lập [5 preliminary hazard prompts](reference/stage11_preliminary_hazard_scenarios_20261029.csv) theo chức năng hiện hữu. Rating, risk decision, residual risk và sign-off để trống; intended use chưa khóa, nên G5 vẫn OPEN. Artifact này đã được rà soát, gắn vào gate QA v4 và sẽ nằm trong checkpoint mới của lượt này.


### Privacy/security baseline — 29/10/2026
Đã phân rã G6 thành [16 hạng mục baseline](reference/stage11_privacy_security_baseline_20261029.csv) với trạng thái gap/not_evaluable, evidence đóng và vai trò accountable. Không có mục nào pass; static review không xác minh runtime. Artifact mới sau ZIP hiện hành, cần lấy vào checkpoint kế tiếp.


## Checkpoint cập nhật — 29/10/2026 14:08 ICT
Snapshot `checkpoints/20261029_070849/project_snapshot.zip` gồm 766 file / 163,203,941 byte giải nén (archive 133,484,453 byte), đã tự verify và được xác minh lại độc lập: 766 member, CRC PASS. SHA-256 ZIP `76433eaa32b346163bac0dac8570770524c951d154c5af59548c4f4ebbb35ed7`; manifest SHA-256 `8740df9a5052e334c65ed274478db4f270d3a48d6dbb8e04a75f15a28aece5c7`. Manifest ghi HEAD `b6d67fbfea778a8abfe40b9d012dd3f99b0de0ff`, audit/replay PASS, 16 reports, 0/7 gates, `answer_ready=false`. Snapshot đã chứa intended-use draft, 4 hazard scenarios, 16-item privacy baseline, reviewer packet và updated gate register. Các cập nhật tự tham chiếu đoạn này sẽ nằm ở checkpoint sau.

Checkpoint manifest giờ có `readiness_metadata_check` và danh sách cảnh báo fail-visible: audit/replay vắng hoặc không PASS, replay khác 16 report/có mismatch, gate register khác 7 dòng hoặc status ngoài OPEN/CLOSED sẽ tạo WARNING thay vì trông như trạng thái sạch. Smoke check hiện hành: PASS, warnings rỗng; code update sau ZIP 20261029_070849 và sẽ vào snapshot tiếp theo.

Readiness metadata warning-path smoke check: fixture thiếu audit/replay/gate register cho ra `WARNING` với từng nguyên nhân rõ ràng; `answer_ready=false` giữ nguyên. Workspace thật trả `PASS`, audit/replay PASS, 16 reports, 0 mismatch, 7 gates (0 đóng). Fixture dùng temp directory và không để lại file.


### Regression sau checkpoint — checkpoint utility
Thêm 4 focused tests (3 subtests) cho exclusions, valid/tampered manifest và fail-visible readiness metadata. Focused test PASS; full suite **83 passed, 130 subtests**, 1 warning Starlette, exit 0. [Record](reference/stage11_test_run_20261029_checkpoint_tool_full.json), SHA-256 `58f749a486b26b0d3cd91c0714c2e439e5e2236d3302d3cc80bc9a6aa636445d`. Test/report sau ZIP `20261029_070849`; cần snapshot kế tiếp.


### G4 cohort register — 29/10/2026
Đã chuẩn hóa 10 lead thành [screening register](reference/stage11_external_cohort_screening_register_20261029.csv), giữ riêng access, quyền ảnh, reference standard và overlap. Không candidate nào eligible/evaluable theo evidence hiện có. Register sau ZIP hiện hành.


### G3 evidence-group label schema — 29/10/2026
Đã tạo [reviewer label template per evidence group](reference/stage11_retrieval_evidence_group_label_template_20261029.csv) (22 columns) và cập nhật protocol. Tách relevance khỏi support relation; citation entailment của generated answer được ghi N/A/not evaluable vì generator chưa tồn tại. Chưa có labels; G3 OPEN; artifact sau ZIP gần nhất.


## Checkpoint cập nhật — 29/10/2026 14:14 ICT
Snapshot `checkpoints/20261029_071435/project_snapshot.zip` gồm 770 file / 163,223,037 byte giải nén (archive 133,492,269 byte). Tự verify sau khi tạo và xác minh chỉ đọc độc lập: **PASS**, 770 file, CRC PASS. ZIP SHA-256 `d2cb184e2e3c9b4886d4a752f1399a1338a983d3ee3e38e9388371e4bbc7d5aa`; manifest SHA-256 `78fd2e01a8ccb027f595c8769e8c861536596776ad1711ba9b8aa5fa8e05c2d9`. HEAD `b6d67fbfea778a8abfe40b9d012dd3f99b0de0ff`; readiness metadata PASS; audit/replay PASS, 16 reports, 0 mismatches; 0/7 gates closed; `answer_ready=false`. Archive includes G3 evidence-group template, G4 cohort register, latest full regression record and all previous worktree evidence. The note additions about this ZIP were made after archive creation and will be in the next snapshot.

Documentation link QA on 6 key handoff/reviewer documents checked 315 local Markdown targets; found 2 broken relative links in the Stage 11 report and corrected them to `../reference/...`. Re-run: 315 checked, 0 missing. This doc fix is after checkpoint `20261029_071435`.


Expanded documentation link QA across all 28 Markdown files in `docs/`: checked 444 local links, fixed one broken relative path in continuation notes, rerun 444 checked / 0 missing. This is workspace link-integrity only; external URLs were not fetched.

Summary synchronization: current-state leads in project status, handoff and executive report now show 83/130 and checkpoint `20261029_071435`; older v8/79 references are retained only in historical sections. Rechecking all docs after edit: 445 local links, 0 missing. These summary edits postdate the ZIP.


## Checkpoint cập nhật — 29/10/2026 16:31 ICT

Snapshot mới nhất được tạo bởi `tools/create_project_checkpoint.py`: `checkpoints/20261029_093707/project_snapshot.zip`, 836 files / 164,803,676 bytes giải nén; ZIP SHA-256 `61775e31dd4d0d31ac44448896d76a0d3967be02eccd6e428d43a6414bbde604`. Tool verifier PASS, 836 files, CRC PASS. Bao gồm QA v4 với 23/23 artifact SHA-256 khớp, 15 cohort rows, 7/7 gates OPEN, nguồn pháp quy Việt Nam đã lập registry. Các pointer trong execution plan, handoff, status, progress, checkpoint note và báo cáo được đồng bộ sau khi tạo ZIP. Gate acceptance 0/7 đóng; `answer_ready=false`.
