# Thử nghiệm kiểm tra độ phủ khái niệm

Chốt trước lần chạy đầu ngày 27/10/2026. Sử dụng corpus 416 đoạn và model E5 hiện có. Không đổi gold của V2; kết quả V2 hiện là regression vì đã xem trong vòng trước.

Phương án: phân tích cụm từ trong câu hỏi bằng danh sách khái niệm Việt–Anh và từ vựng xuất hiện trong corpus; từ có nghĩa chưa nhận diện sẽ yêu cầu làm rõ. Tìm trên tối đa 80 ứng viên rồi yêu cầu có đoạn phủ các khái niệm cần thiết, ưu tiên nguồn tổng quát khi câu hỏi tổng quát. Đây là kiểm tra từ vựng, không phải suy luận entailment hoặc xác nhận kết luận; câu có đủ từ vẫn có thể sai quan hệ, phủ định hoặc con số. `answer_ready` tiếp tục luôn false.

Tính năng thử nghiệm qua cờ `--verify-evidence`, không tự bật mặc định. Điều kiện kỹ thuật để cân nhắc bật sau này: recall không giảm trên bộ regression cũ/V2, không từ chối nhầm quá 10% câu dương và từ chối ít nhất 80% câu âm trên stress suite mới. Đây là mục tiêu thử nghiệm nội bộ, không phải ngưỡng an toàn lâm sàng. Nếu không đạt, giữ opt-in và ghi đủ ca trượt; không sửa từ vựng theo stress test rồi coi kết quả đó là kiểm định mới.

Stress suite `rag/data/evaluation_evidence_v3.json` gồm 10 câu dương và 10 câu âm bằng Việt/Anh, do cùng AI soạn và đóng băng trước lần đo; chưa phải tập độc lập hoặc thẩm định chuyên môn. File config riêng nằm tại `rag/data/evidence_config.json` để không thay cấu hình baseline.

## Kết quả sau khi chạy

Phương án lọc nghiêm ngặt **không đạt**: V3 từ chối 10/10 câu âm nhưng cũng từ chối nhầm 5/10 câu dương; V2 test đã xem bị chặn cả 8/8 câu dương. Nguyên nhân nổi bật là câu tiếng Việt dùng từ chưa có trong danh sách, không phải thiếu bằng chứng trong corpus. Giữ opt-in qua `--verify-evidence`; không bật mặc định.

### Chẩn đoán miss theo từng câu OFD — 29/10/2026

Để tách lỗi phủ từ khỏi lỗi retrieval, `tools/analyze_evidence_coverage.py` chạy `EvidenceVerifier` trực tiếp trên các reference chunk đã được gắn trong bộ OFD dev, không chạy lại dense/hybrid retrieval. Kết quả tái lập: **1/5** câu dương được giữ; **4/5** bị abstain. Ba câu bị `unrecognized_question_terms` do các token tiếng Việt/cụm ghép không có trong vocabulary như `vo`, `ton`, `tieu`, `gian`, `tuy`, `thong`, `tich`, `gop`; một câu khác bị thiếu literal `xi` trong cụm “xấp xỉ”. Câu CT/MRI duy nhất được giữ. Đây là câu hỏi agent-authored/in-sample và checker lexical trên gold reference chunk; kết quả không chứng minh retrieval recall, entailment, hay độ đúng y khoa.

Không thêm alias/whitelist riêng để làm đẹp 5 câu đã xem. Việc bỏ hard reject với unknown terms có thể làm mất một chi tiết có ý nghĩa; cần bộ dịch thuật/khái niệm được chuyên gia xác lập, kiểm trên câu hỏi mới mù và đo riêng false acceptance/false abstention trước khi sửa mặc định. Giữ checker tắt cho người dùng.

Tái lập bằng `python tools/analyze_evidence_coverage.py`; report/hash đầu vào ở [chẩn đoán JSON](stage11_evidence_verifier_miss_analysis_20261029.json). Report chỉ kiểm tra reference chunks đã gắn sẵn, không thay thế evaluator hoặc review độc lập.

### Thử cue trung tính song ngữ — kết quả v2, 29/10/2026

Sau khi bổ sung `xấp xỉ`/`approximately` vào nhóm cue trung tính (không phải khái niệm bằng chứng bắt buộc), diagnostic giữ **2/5 reference chunks**, tăng từ 1/5. Câu có “xấp xỉ” được giữ; ba câu tiếng Việt khác vẫn abstain vì từ chưa nhận diện. Đây vẫn là năm câu dev đã xem, nên không dùng để chọn/tinh chỉnh whitelist tiếp theo.

Đã chạy thêm evaluator hybrid thực tế với strict checker trên cùng bộ OFD dev: **Recall@5 2/5 (0,4)** so với report v7 lịch sử **1/5 (0,2)**; positive abstention **3/5 (0,6)** so với **4/5 (0,8)**; negative abstention giữ **2/2 (1,0)**. Các ca dương được chấp nhận là `ofd01` và `ofd04`; `ofd02`, `ofd03`, `ofd05` vẫn abstain. Dataset được soạn bởi agent và đã dùng trong phát triển; `frozen_evidence_config_matches=false`, nên so sánh chỉ mô tả khám phá, không phải phép đo trên cấu hình đóng băng hay benchmark độc lập. Các status `candidates_found` chỉ nói bộ lọc từ vựng cho qua, không xác nhận câu trả lời/citation entailment.

Giữ strict checker **opt-in/disabled mặc định**. Xem [diagnostic reference-chunk v2](stage11_evidence_verifier_miss_analysis_20261029_v2.json), [kết quả retrieval thực tế v2](stage11_evidence_verifier_ofd_actual_retrieval_20261029_v2.json), và [bản ghi full suite](stage11_test_run_20261029_evidence_neutral_phrases_v2.json) (74 passed, 127 subtests; một cảnh báo deprecation).

### Regression đồng loạt bundle v8

Sau khi cập nhật neutral cues, v8 dựng lại 16 report từ v7 với cùng dataset và cấu hình, audit **PASS** (21 cache/759 chunks/9 datasets/16 reports), replay **PASS 16/16**, không preflight mismatch. Chỉ `osteofibrous_dysplasia_dev_strict.json` đổi metric; 15 report khác giữ nguyên. Trên 5 report strict (expansion, OFD, synovial source, synonym, V2), checker cho qua **4/40** câu dương và abstain **14/14** câu âm; so với v7, chỉ OFD tăng từ 1/5 lên 2/5. Các tập đều agent-authored/in-sample; 90% positive abstention khiến gate tiếp tục không phù hợp mặc định. Xem [bundle v8](stage11_policy_rerun_20261029_evidence_neutral_v8/), [run record](stage11_evidence_neutral_bundle_v8_record_20261029.json), [verification summary v8](stage11_verification_summary_20261029_evidence_neutral_v8.json), [audit](stage11_integrity_audit_20261029_evidence_neutral_v8.json) và [replay](stage11_replay_20261029_evidence_neutral_v8.json).

### Thí nghiệm bỏ riêng hard reject token chưa nhận diện — 29/10/2026

Để đo riêng nguồn false refusal, `tools/compare_evidence_unknown_term_policy.py` chạy lại năm report strict của bundle v8 bằng bản sao config trong bộ nhớ; chỉ đổi `require_known_query_terms: true→false`. Các khái niệm và literal đã nhận diện vẫn phải được phủ bởi passage, production config không sửa. Kết quả candidate: câu dương được giữ tăng **4/40→19/40**; abstention dương giảm **36/40→21/40**. 14/14 câu âm vẫn abstain, không có negative candidate trong bộ đã xem. Theo report: expansion **1/22→6/22**, OFD **2/5→2/5**, synovial source **0/4→3/4**, synonym **1/1→1/1**, V2 **0/8→7/8**.

Đây là chẩn đoán về độ nhạy với unknown tokens, không phải khuyến nghị đổi production. Các bộ đều agent-authored/đã xem, chỉ có 14 âm; bỏ unknown tokens có thể bỏ qua từ chưa ánh xạ nhưng mang qualifier/điều kiện quan trọng. Candidate vẫn abstain 21/40 câu dương và không kiểm tra quan hệ, phủ định hoặc entailment. Trong 21 câu còn bị từ chối, diagnostic thấy các coverage gap như `tissue`, `symptoms`, `tests` và literals `don`, `cyst`, `cohort`; đây là dấu hiệu cần ontology song ngữ được reviewer xác lập, không phải danh sách để thêm trực tiếp từ bộ đã xem. Bảng tần suất của `best_missing` (một candidate tốt nhất mỗi câu, không phải toàn bộ thiếu hụt) tại [gap analysis JSON](stage11_evidence_unknown_token_remaining_gap_analysis_20261029.json). Vì vậy không đổi `evidence_config.json`, giữ checker disabled mặc định. [Report JSON v3 với missing terms/statuses và hash](stage11_evidence_unknown_token_gate_experiment_20261029_v3.json). Các lần v1/v2 được giữ làm history.

Sau kết quả đó, đã tách phần xếp hạng khái niệm thành phương án khám phá `--rerank-concepts`, không lọc câu theo từ chưa biết. Nó đạt 10/10 câu regression, 8/8 mỗi phần V2 và 9/10 câu V3; khả năng từ chối câu âm không cải thiện. Kết quả rerank là khám phá trên các tập đã xem, không phải phép kiểm định chưa từng thấy. Cần một tập mới độc lập trước khi dùng kết quả này để chấp nhận phương án mặc định.

Số liệu và diagnostics từng câu tại `stage11_evidence_rank_20261027/`; không chỉnh gold hoặc whitelist theo các ca này rồi tiếp tục coi đó là kiểm định độc lập. Corpus và cấu hình hybrid cũ vẫn giữ nguyên.
