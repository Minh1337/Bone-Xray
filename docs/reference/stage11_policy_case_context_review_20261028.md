# Rà soát policy ảnh cá nhân theo ngữ cảnh ca bệnh — 28/10/2026

## Phát hiện và sửa đổi

Rà soát compositional phát hiện matcher ảnh cá nhân có thể bỏ lọt những câu mà dấu hiệu ca bệnh nằm xa modality: `patient of mine`, `case I am treating`, tiếng Việt `ca bệnh tôi đang theo dõi`, hoặc yêu cầu `review` thay vì `interpret/read`. Sau khi mở rộng khoảng cách, một câu hỏi giáo dục tổng quát bị chặn nhầm nếu nhắc “patient of mine” ở câu trước câu hỏi.

Policy hiện dùng các cụm sở hữu/điều trị cụ thể cho khoảng cách xa và chỉ kết hợp cue trong cùng câu. Bộ 30 negative probes hiện hành cho kết quả **30/30 `insufficient_evidence`** với reason `image_requires_specialist_assessment`. Regression controls giữ câu giáo dục chung trong phạm vi, gồm câu có nhắc bệnh nhân ở câu riêng trước đó. Các probes được soạn và dùng để sửa/tinh chỉnh cùng policy, vì vậy đây là kết quả **in-sample**, không phải blind test, sensitivity estimate, hay bằng chứng xử lý ảnh đính kèm.

## Reproduction record

| Artifact | SHA-256 / result |
|---|---|
| Policy implementation `rag/policy.py` | `c3ea2f53a5d931d6328ab6d7ec2fbbd947f6c2ddda0faa8ef76a5ceec30e8fce` |
| Regression tests `rag/tests/test_retrieval.py` | `a8b81a4689bed8b0c1e91f93b33360b299b6c4eb3b152509dc759990913b3467` |
| Probe dataset `rag/data/evaluation_image_routing_dev_20261028.json` | `d2cef8209dfa92c59f6427b39d870534f20461624fcb541314ab09f1abb8ef70` — 30 negative cases |
| Evaluator report | `docs/reference/stage11_policy_rerun_20261028_post_case_context_sentence_scope/image_routing_dev.json`, SHA-256 `9d3d7d3e0626a757c8357b758c72ad2e31f5e9bf0ec0dc42a66a933575d73739` — 30/30 expected specialist abstentions |
| Targeted run | `python -m pytest rag/tests/test_retrieval.py -q` — 13 passed, 56 subtests passed |
| Full-suite run | [`stage11_test_run_20261028_post_case_context_sentence_scope.json`](stage11_test_run_20261028_post_case_context_sentence_scope.json) — 66/66 passed, one Starlette deprecation warning |
| Final bundle manifest | `5ed1556dd4cf51c76ae27e9f77dd7f884494252a6bc5e3a72e41d86681b163bb` — 16 reports |
| Final deterministic replay | [`stage11_replay_20261028_post_case_context_sentence_scope.json`](stage11_replay_20261028_post_case_context_sentence_scope.json) — PASS 16/16 |
| Final integrity audit | [`stage11_integrity_audit_20261028_post_case_context_sentence_scope.json`](stage11_integrity_audit_20261028_post_case_context_sentence_scope.json) — PASS artifact integrity/provenance |

The full test suite and replay verify software behavior and reproducibility only. They do not establish independent clinical validity, image-attachment detection, diagnostic accuracy, or acceptance for medical use. `answer_ready` remains `false`.


## Bổ sung: diễn đạt kết cục lành/ác và ngữ cảnh bệnh nhân — 28/10/2026

Probe thủ công trước sửa phát hiện false negative với `patient's X-ray ... benign`, `radiograph ... malignant`, `review her radiograph for malignancy`, cùng ngữ cảnh `patient I am seeing`/`case I manage`; tiếng Việt cũng có câu hỏi về phim của con và phim của bệnh nhân đang điều trị. Policy đã bổ sung dấu hiệu sở hữu nhân xưng, ngữ cảnh ca/bệnh nhân và từ vựng kết cục `benign/malignant`, `look/appear`, `normal/abnormal`, `có vẻ`, `tổn thương`. Ghép cue vẫn giới hạn trong cùng câu để không chặn câu giáo dục ở câu tiếp theo chỉ vì câu trước nhắc bệnh nhân.

Hồ sơ mới nhất: [probe JSON](stage11_personal_image_outcome_probes_20261028.json), SHA-256 `e917ac9a022e5ef6cad1c52c0d6b770d356479e0306a26f4fc9aaf325778d132`: **8/8** câu ảnh cá nhân được route `insufficient_evidence / image_requires_specialist_assessment`; **6/6** câu hỏi giáo dục làm đối chứng vẫn trong scope. Các câu được viết để tìm/sửa lỗi và được chạy cùng policy đang phát triển; đây là probe in-sample, text-only, không phải test mù/độc lập/đại diện, không đo năng lực nhận diện ảnh đính kèm.

Full suite sau thay đổi và cập nhật default bundle: **66 passed, 75 subtests passed**, một cảnh báo deprecation. Targeted `rag/tests/test_retrieval.py -q`: **13 passed, 64 subtests passed**. Snapshot mới có 16 báo cáo, replay PASS 16/16 và audit PASS trên 21 cache/9 dataset/16 report. Bundle/replay/audit/test-run và policy implementation hashes nằm trong [verification summary mới](stage11_verification_summary_20261028_post_personal_image_outcome_context.json); lệnh audit/replay mặc định cũng trỏ về bundle này. Các kết quả chỉ xác nhận software regression, tái lập và artifact integrity, không chứng minh độ đúng lâm sàng hay nghiệm thu độc lập. `answer_ready` vẫn `false`.


## Bổ sung v2: cách nói sở hữu/ca bệnh khác và dấu hiệu “đáng lo” — 28/10/2026

Matrix mở rộng tìm ra bốn miss: `radiograph I obtained for my patient` (động từ yêu cầu `comment` chưa nhận diện), `ca tôi đang điều trị`, `bệnh nhân tôi đang theo dõi có đáng lo`, và `người bệnh tôi đang khám ... bất thường`. Policy thêm các cue ca/bệnh nhân này cùng `comment/opinion`, `đáng lo/lo ngại/bất thường/nguy hiểm`. Regression xác nhận **12/12** câu ảnh cá nhân mới/cũ được abstain với reason `image_requires_specialist_assessment`, trong khi **6/6** controls giáo dục (kể cả nhắc patient trong câu riêng trước đó) vẫn trong scope. Probe cumulative: [JSON v2](stage11_personal_image_outcome_probes_v2_20261028.json).

Sau policy v2: full suite **66 passed, 79 subtests**, targeted retrieval **13 passed, 68 subtests**; replay **16/16 PASS**, audit **PASS** trên 21 cache/9 dataset/16 report. Bundle manifest SHA-256 `5d38921a426c77707363f93328b45ad28a8f97f2db9e5404ba979fd3b4617955`; comparison không thấy metric nào đổi trên 16 báo cáo đang có. Snapshot và run records tại [verification summary](stage11_verification_summary_20261028_post_personal_image_outcome_context.json). Các probes vẫn in-sample và chỉ text; không đánh giá ảnh đính kèm/metadata, độ đúng y khoa, hay nghiệm thu độc lập.
