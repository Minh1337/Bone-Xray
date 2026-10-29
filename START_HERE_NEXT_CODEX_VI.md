# Bàn giao BoneScope cho phiên Codex tiếp theo

**Phạm vi mới nhất do người dùng nêu:** [đề tài báo cáo học tập thực nghiệm](docs/reference/STAGE11_USER_STATED_EDUCATIONAL_SCOPE_20261029.md), không cung cấp cho bác sĩ hoặc người bệnh. Ưu tiên retrieval/provenance/demo và báo cáo nghiên cứu; [bảng đối chiếu 7 bước kỹ thuật](docs/reference/STAGE11_EDUCATIONAL_COMPLETION_MATRIX_20261029.md) tách tiến độ đồ án khỏi gate lâm sàng. [QA register có thể chạy lại](tools/verify_stage11_registers.py) với [record v6](docs/reference/stage11_gate_cohort_register_qa_20261029_v6.json) kiểm 24 tham chiếu, không thay ký duyệt.

**Thăm dò bước 7 mới nhất:** [score overlap record](docs/reference/stage11_similarity_overlap_probe_20261029.json) trên 28 câu đã xem cho thấy không thể chọn một ngưỡng dense cosine đơn để giữ trọn 17 câu dương và loại trọn 11 câu âm. Chạy lại bằng `.\.venv\Scripts\python.exe -m tools.probe_stage11_similarity --output docs/reference/stage11_similarity_overlap_probe_rerun.json` nếu cần; khi tái chạy không ghi đè artifact lịch sử, chọn tên record mới. Không sửa retrieval threshold mặc định từ bộ này.

**Cập nhật tiếp nối 29/10/2026:** người dùng đã yêu cầu tiếp tục Giai đoạn 11 sau điểm dừng bên dưới và hỏi khi nào xây chatbot. Xem [mốc chatbot và điều kiện](docs/reference/STAGE11_CHATBOT_READINESS_VI.md). Archive `20261029_pause_handoff` là snapshot tại điểm dừng; các thay đổi sau đó phải được kiểm tra trong working tree và checkpoint mới. Những câu “chưa nhận yêu cầu tiếp tục” phía dưới là lịch sử tại thời điểm lưu, không còn ngăn việc làm theo yêu cầu tiếp nối.

**Điểm dừng: 29/10/2026 (UTC+07). Người dùng yêu cầu lưu toàn bộ tiến trình và tạm ngưng goal.** Không chạy tiếp nghiên cứu, tuning hoặc triển khai Giai đoạn 11 khi chưa nhận yêu cầu tiếp tục. Hồ sơ trong thư mục dự án đủ để tiếp quản mà không cần lịch sử cuộc chat; trạng thái goal trong ứng dụng không tự chuyển sang chat mới.

## Đọc theo thứ tự

1. [Báo cáo Giai đoạn 11 hiện hành](docs/reports/BAO_CAO_GIAI_DOAN_11_2026-10-29.md) và [tiến độ](docs/STAGE11_PROGRESS_2026-10-29.md).
2. [Trạng thái bàn giao dạng JSON](docs/reference/stage11_pause_handoff_20261029.json), gồm Git HEAD, hash đầu vào, hồ sơ kiểm chứng, lệnh và danh sách việc còn mở.
3. [Kế hoạch thực thi](docs/STAGE11_EXECUTION_PLAN_VI.md), [blocker theo 7 gate](docs/reference/STAGE11_GATE_CLOSURE_BLOCKERS_VI.md) và [register nghiệm thu](docs/reference/stage11_acceptance_gate_status_20261029.csv).
4. [Handoff kỹ thuật](docs/STAGE11_HANDOFF_VI.md) và [reviewer packet](docs/reference/STAGE11_REVIEWER_PACKET_VI.md) khi cần chi tiết. Các đoạn v8, continuation_v2 và số liệu cũ là lịch sử; bundle hiện hành là `cureus_abcrouting_v1`.

## Trạng thái tại điểm dừng

- Chuẩn bị workspace **khoảng 85%**, là ước lượng quản lý, không phải tỷ lệ hoàn thành toàn bộ Giai đoạn 11. **Nghiệm thu 0/7 cổng (0%)**, tất cả OPEN; `answer_ready=false`.
- Corpus **22 nguồn / 794 chunks**, index **794×384**, model embedding `intfloat/multilingual-e5-small` với revision/hash trong index manifest. Bundle hiện hành: `docs/reference/stage11_policy_rerun_20261029_cureus_abcrouting_v1`.
- Regression gần nhất đã ghi: **87 passed / 132 subtests**, một cảnh báo Starlette; offline audit PASS; deterministic replay PASS **16/16**, không preflight mismatch. Lượt lưu/tạm dừng chỉ kiểm tra bảo toàn dữ liệu và hash, không chạy lại hay nâng mức bằng chứng của các kết quả đó.
- Đã lưu: nguồn có license/provenance, corpus/index, retrieval/routing, dev experiments, evidence diagnostics, evaluator, regression/audit/replay, biểu mẫu review và báo cáo. Strict evidence filter vẫn opt-in/tắt mặc định; lexical coverage không chứng minh entailment. Chưa có answer generator được nghiệm thu.
- G4 có **15 leads**, chưa cohort nào đủ điều kiện external evaluation. BTXRD nằm trong nguồn huấn luyện khai báo của checkpoint; thiếu split/patient mapping và rights-chain upstream. Không dùng BTXRD như external test của model hiện tại.
- Báo cáo Markdown ngày 29/10 là bản hiện hành; các DOCX cũ là snapshot lịch sử, chưa được cập nhật/kiểm tra bố cục lại.

## Các việc phải tiếp tục sau khi người dùng cho chạy lại

| Cổng | Công việc còn thiếu | Vai trò/bằng chứng cần có |
| --- | --- | --- |
| G1 | Khóa intended use theo từng chức năng, deployment và jurisdiction | Owner và reviewer liên quan ký scope thực tế; bản draft hiện tại chưa có hiệu lực |
| G2 | Freeze rubric/sampling trước khi xem labels; thu nhãn mù và adjudication | Reviewer lâm sàng độc lập, sampling manifest, nhãn thật, adjudication và release có chữ ký |
| G3 | Đánh giá support/entailment theo claim-span, polarity, qualifiers, context; đo false accept/refusal | Nhãn độc lập và adjudication; không thay bằng strict lexical checker |
| G4 | Làm rõ quyền từng ảnh, reference standard, patient-level manifest và overlap với checkpoint/pretraining | Custodian/rights holder/cohort auditor; chưa có cohort được cleared, không tự liên hệ bên ngoài |
| G5 | Hazard/use-error analysis theo intended use; verify controls và residual risk | Safety lead/reviewer ký; các prompt sơ bộ chưa phải safety approval |
| G6 | Xác minh deployment/data-flow, access control, retention/deletion, DB/WAL/backup và incident response | Privacy/security reviewer và owner ký; filename minimization chỉ là một kiểm soát nhỏ |
| G7 | Đọc đầy đủ nguồn pháp lý theo chức năng/jurisdiction/ngày vận hành, ghi applicability và pathway | Reviewer regulatory/counsel đủ thẩm quyền; source register chưa phải legal opinion |

G1 là dependency cần xử lý trước; G2/G3 cần người độc lập. Không tạo thêm tài liệu trùng lặp để thay cho bằng chứng thiếu. Nếu cải thiện code/retrieval, dùng dev riêng có provenance, không tune trên tập test đã xem hoặc blind set; cập nhật audit/replay/regression và báo cáo sau thay đổi. Nguồn online mới phải được kiểm tra lại ở primary/official source; lưu ngày, license, payload/hash và giới hạn. Không tự nâng `answer_ready` hoặc đổi gate thành CLOSED.

## Lệnh đối chiếu khi được yêu cầu tiếp tục

Chạy tại thư mục gốc của dự án. Trên máy hiện tại dùng Python trong `.venv`; Python hệ thống không đủ dependencies cho RAG. Khi chuyển máy, dựng lại môi trường theo README/requirements và đối chiếu [bản ghi phiên bản môi trường](docs/reference/stage11_environment_at_pause_20261029.json); `.venv` không nằm trong backup.

```powershell
git status --short
git log -3 --oneline
python -X utf8 checkpoints/20261029_pause_handoff/verify_resume_bundle.py
.\.venv\Scripts\python.exe -m rag.audit --report-dir docs/reference/stage11_policy_rerun_20261029_cureus_abcrouting_v1
.\.venv\Scripts\python.exe -m rag.replay_reports --bundle docs/reference/stage11_policy_rerun_20261029_cureus_abcrouting_v1
.\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q
```

Không dùng default bundle lịch sử trong audit/replay. Trước mọi rebuild, kiểm hash của corpus, config, source lock, index và model với JSON bàn giao; nếu khác, ghi nguyên nhân rồi tạo record mới, giữ nguyên record lịch sử. Trên chat Codex mới, chỉ tạo goal mới nếu người dùng yêu cầu; goal cũ được tạm ngưng trong chat hiện tại.

## Bản lưu để chuyển phiên/máy

Thư mục [checkpoints/20261029_pause_handoff](checkpoints/20261029_pause_handoff) gồm:

- `project_snapshot.zip` và `manifest.json`: source, tài liệu, test, model do Git theo dõi, cấu hình, corpus và source cache; SHA-256 từng file do checkpoint utility ghi.
- `assets_runtime.zip` và `assets_runtime_manifest.json`: index, model embedding, BTXRD đang có, kết quả/API artifacts, logs và bản SQLite nhất quán của dữ liệu runtime cục bộ. Đây là lưu trữ nội bộ, không phát hành lại dữ liệu hay xác nhận quyền tái sử dụng.
- `repository.bundle`: lịch sử và refs Git hiện có; thay đổi chưa commit nằm trong snapshot/patch, không nằm trong bundle Git.
- `bundle_manifest.json` và `verify_resume_bundle.py`: hash các thành phần và kiểm tra nội dung archive. SHA-256 của archive được lưu bên ngoài archive để tránh tự tham chiếu.

Giữ nguyên workspace hiện tại là cách tiếp quản nhanh nhất. Nếu chuyển máy, chép **toàn bộ thư mục checkpoint trên**, xác minh bằng script, rồi giải nén source và assets vào **thư mục mới** giữ nguyên relative paths. Nếu cần lịch sử Git, clone `repository.bundle` trước, rồi chép nội dung snapshot/patch lên checkout; đọc manifest để nhận biết thay đổi chưa commit. Không giải nén đè lên một checkout có công việc chưa sao lưu. Bộ ảnh/model/runtime được giữ cục bộ; không cần tải lại để khôi phục nội dung đã lưu. Môi trường Python, driver/CUDA, ứng dụng Codex và credentials phải thiết lập riêng; backup không chứa `.git` trực tiếp, `.venv`, installer/cache hệ thống hoặc các checkpoint cũ.

## Câu lệnh có thể gửi cho Codex khác

> Đọc AGENTS.md và START_HERE_NEXT_CODEX_VI.md trong dự án BONESCOPE. Tôi cho phép tiếp tục Giai đoạn 11 từ điểm tạm dừng ngày 29/10/2026. Đối chiếu hash và trạng thái thực tế trước khi sửa; tiếp tục các việc trong kế hoạch và blocker matrix, giữ answer_ready=false và không tự đóng gate/chứng nhận review độc lập. Lưu mọi thay đổi và bằng chứng vào dự án.

