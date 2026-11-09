# Báo cáo tổng kết đồ án BoneScope

**Đề tài:** Nguyên mẫu học tập kết hợp phân loại ảnh X-quang u xương (Swin + 22 metadata), truy xuất tài liệu có trích nguồn (RAG) và chatbot đa lượt

**Ngày chốt:** 09/11/2026 (UTC+07) · **Loại tài liệu:** báo cáo học tập có tính thực nghiệm

> [!IMPORTANT]
> BoneScope là nguyên mẫu **học tập/nghiên cứu nội bộ**, không cung cấp cho bác sĩ hay người bệnh, không phải thiết bị y tế và không dùng để chẩn đoán hay quyết định điều trị ([phạm vi do người dùng xác định](../reference/STAGE11_USER_STATED_EDUCATIONAL_SCOPE_20261029.md)). API luôn trả `answer_ready=false`; bảy gate nghiệm thu G1–G7 vẫn `OPEN`. Mọi số liệu dưới đây là **thực nghiệm nội nguồn hoặc trên bộ dev đã xem**, không phải kiểm định độc lập.

## Tóm tắt

BoneScope gồm bốn thành phần chạy cục bộ: (1) mô hình phân loại X-quang `Swin + MetadataMLP + Cross-Attention` trên 10 nhãn BTXRD; (2) kho RAG 22 nguồn công khai có provenance, 794 đoạn, chỉ mục `794 × 384` với `intfloat/multilingual-e5-small` và truy xuất lai BM25 + dense; (3) chatbot đa lượt có định tuyến chủ đề, từ chối ngoài phạm vi và chat ảnh tạm trong tab; (4) lịch sử hội thoại SQLite chỉ lưu văn bản và nguồn.

Kết quả chính: trên 250 ảnh BTXRD phân tầng (in-source), mô hình đạt Top-1 **0,776**, Top-3 **0,940**, Macro-F1 **0,776**, ECE 10-bin **0,037**. Khi xóa metadata về 0, Top-1 còn **0,480** và ECE tăng lên **0,208**, cho thấy nhánh metadata đóng góp lớn và mô hình trở nên tự tin quá mức khi thiếu metadata. RAG tái lập được 16/16 báo cáo đánh giá, audit provenance PASS. Bộ regression phần mềm offline đạt **202 passed / 132 subtests**; browser smoke và smoke provider thật cơ bản PASS.

Giới hạn chính: chưa có tập ảnh ngoài độc lập, chưa có reviewer độc lập chấm relevance/entailment, và chưa có ngưỡng similarity được hiệu chỉnh (bước 7 của checklist Giai đoạn 11).

## 1. Mục tiêu và phạm vi

| Mục tiêu học tập | Trạng thái |
| --- | --- |
| Xây pipeline phân loại X-quang có metadata và đánh giá được vai trò metadata | Đã làm; đánh giá in-source + ablation |
| Xây kho RAG có provenance, chỉ mục tái lập, evaluator và replay | Đã làm; audit/replay PASS |
| Chatbot đa lượt có định tuyến, từ chối ngoài phạm vi, trích nguồn | Đã làm; mock/browser/provider smoke PASS |
| Cơ chế từ chối theo ngưỡng score đã hiệu chỉnh (bước 7) | Có công cụ quét ngưỡng; **chưa có nhãn độc lập**, chưa cài ngưỡng |
| Đánh giá độc lập và nghiệm thu G1–G7 | Ngoài khả năng tự thực hiện; cần người có thẩm quyền |

Không thuộc phạm vi: dùng dữ liệu bệnh nhân thật, triển khai công khai, tuyên bố độ chính xác y khoa.

## 2. Dữ liệu

### 2.1. Ảnh BTXRD

Catalogue cục bộ có **3.746 ảnh**, 3.725 SHA-256 duy nhất; 21 nhóm trùng byte, trong đó 9 nhóm có metadata mâu thuẫn và bị chặn tự điền. Phân bố trung tâm: Center 1/2/3 = 2.938/549/259. Nhãn lệch mạnh: `no-tumor` 50,2%, `osteochondroma` 20,1%, các lớp hiếm như `osteofibroma` 1,2%. Chi tiết: [phân tích catalogue](../reference/stage12_btxrd_catalogue_and_mapping_analysis_20261105.json).

> [!WARNING]
> Checkpoint được huấn luyện trên BTXRD (`n_samples_seen_ = 2.616`) và không lưu danh sách ID train/val/test; BTXRD công khai không có `patient_id`. Vì vậy không có tập kiểm định sạch trong BTXRD cho checkpoint này.

### 2.2. Kho văn bản RAG

22 nguồn công khai text-only (NCI, review mở CC BY…), mỗi nguồn có URL, section, license và hash trong source lock; 794 đoạn. Không nhập hình ảnh từ nguồn. Xem [audit 09/11](../reference/stage11_integrity_audit_20261109_final_cureus_v1.json).

## 3. Phương pháp

### 3.1. Phân loại X-quang

- Backbone Swin Transformer cho ảnh, `MetadataMLP` cho 22 trường (tuổi, giới tính, 17 vị trí giải phẫu, 3 tư thế), hợp nhất bằng cross-attention, 10 lớp đầu ra.
- Ràng buộc đầu vào: ≥1 vị trí giải phẫu và đúng 1 tư thế; ảnh ≤ 30 MiB, ≤ 25 MP, single-frame.
- Metadata chỉ được tự điền khi byte ảnh khớp SHA-256 duy nhất và không mâu thuẫn trong manifest; không bao giờ tự điền 0 cho ảnh ngoài.
- Đánh giá: 250 ảnh phân tầng (25 × 10 lớp, `seed=20261031`), hai chế độ *đủ metadata* và *metadata = 0*; thêm ECE/MCE/Brier/NLL và phân rã theo tư thế, trung tâm, vùng, chế độ ánh xạ RAG.

### 3.2. RAG và chatbot

- Chunk có metadata nguồn → embedding E5-small có phiên bản → index NumPy gắn chunk/source/model hash → `rag.build_index` build lại được.
- Truy xuất lai BM25 + dense, route ưu tiên mềm cho một số khái niệm; `retrieve()` trả `out_of_scope` hoặc `insufficient_evidence` khi phù hợp.
- `rag.evaluate` tính Recall@k, MRR@k, tỷ lệ abstention trên câu âm; `rag.replay_reports` tái lập tất định các báo cáo theo hash dataset/corpus/config/index.
- Chatbot: OpenRouter Free trước (`openrouter/free` cho chữ, `google/gemma-4-31b-it:free` cho ảnh), fallback trả phí duy nhất `qwen/qwen3.5-flash-02-23` khi timeout 15 s/rate limit/phản hồi rỗng hoặc incomplete. Chỉ gửi Top-3 nhãn và điểm softmax của ca, không gửi ảnh ca, tuổi, giới tính, vị trí hay tên tệp.
- Ánh xạ 10 nhãn sang RAG qua `LABEL_GUIDE`: `direct` (4 nhãn có nguồn), `unresolved` (3 nhãn không tự gán tương đương), `aggregate` (2 nhãn gộp), `no_tumor`.

## 4. Kết quả

### 4.1. Phân loại X-quang (250 ảnh, in-source)

| Chế độ | Top-1 | Top-3 | Macro-F1 | ECE 10-bin | Brier | NLL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Đủ 22 metadata | **0,776** | **0,940** | **0,776** | 0,037 | 0,333 | 0,730 |
| Metadata = 0 | 0,480 | 0,720 | 0,439 | 0,208 | 0,762 | 2,722 |

- 91/250 ca (36,4%) đổi nhãn Top-1 khi bỏ metadata; recall của `no-tumor` và `synovial osteochondroma` về 0.
- Theo trung tâm (đủ metadata): Center 1 = 0,821, Center 2 = 0,692, Center 3 = 0,658 Top-1, cho thấy suy giảm theo trung tâm ngay trong dữ liệu nội nguồn.
- Nhóm `direct` đạt Top-1 0,82; nhóm `aggregate` chỉ 0,56.
- Độ trễ trung vị 25,2 ms/ảnh trên RTX 3050 Laptop.

Nguồn: [đánh giá in-source](../reference/stage11_xray_in_source_evaluation_20261103.json), [calibration & subgroup](../reference/stage12_xray_subgroup_and_calibration_20261106.json), [báo cáo chi tiết Giai đoạn 12](STAGE12_EXPERIMENTAL_CHATBOT_AND_BTXRD_REPORT_VI.md).

### 4.2. Truy xuất RAG (bộ dev/stress đã xem)

| Bộ | Kết quả | Ghi chú |
| --- | --- | --- |
| Expansion dev (25 câu) | Recall@5 1,000; MRR@5 0,689; abstention âm 3/3 | Sau route ABC, tối ưu in-sample |
| Stress song ngữ (20 câu) | Exact-gold recall@5 8/10; MRR 0,633; abstention âm 10/10 | Hai miss có candidate liên quan, cần reviewer |
| OFD dev (7 câu) | Recall@5 5/5; MRR 0,70 | Câu hỏi lấy từ nguồn vừa ingest |
| Replay bundle `cureus_abcrouting_v1` | 16/16 khớp, 0 mismatch | [record 09/11](../reference/stage11_replay_20261109_final_cureus_v1.json) |

**Thăm dò ngưỡng (bước 7):** trên 28 câu đã xem, cosine dense top-1 thấp nhất của nhóm dương là 0,8003, cao nhất của nhóm âm là 0,9087. Hai miền chồng nhau nên **không có ngưỡng đơn** tách trọn hai nhóm ([record](../reference/stage11_similarity_overlap_probe_20261029.json)). Hệ thống vì thế dựa vào routing để từ chối, không cài ngưỡng mặc định. Công cụ [`calibrate_retrieval_threshold.py`](../../tools/calibrate_retrieval_threshold.py) đã sẵn sàng nhận nhãn reviewer và đang ở trạng thái `AWAITING_LABELS` ([readiness](../reference/retrieval_threshold_readiness_20261109.json)).

**Evidence verifier lexical:** chặn nhầm 7/7 câu dương trên V2 test và 3/5 trên OFD dev, nên để opt-in/tắt mặc định. Độ phủ từ vựng không đo được entailment.

### 4.3. Kiểm chứng phần mềm

| Kiểm tra | Kết quả |
| --- | --- |
| Regression offline (`api_tests`, `rag/tests`, `tests`, `ui_tests`) | **202 passed, 0 failed / 132 subtests** (09/11/2026, 1 cảnh báo deprecation Starlette) |
| Audit provenance RAG | PASS: 22 nguồn / 794 chunks, 0 lỗi |
| Register QA | PASS: 24 tham chiếu, 15 cohort leads, 7/7 gate OPEN |
| Browser Chrome headless (AI giả lập, DB tạm) | PASS: nhiều lượt ảnh, retry, lịch sử, mobile 320/390 px, dark mode ([record](../reference/chatbot_browser_regression_20261109.json)) |
| Provider thật (input tối thiểu) | PASS: chữ Free 3,34 s; ảnh hình học qua Qwen 29,59 s; chi phí báo về \$0,000249 ([record](../reference/chatbot_provider_smoke_20261109.json)) |
| Readiness cục bộ (`tools.chatbot_doctor`) | PASS 13/13 kiểm tra, không gọi provider ([record](../reference/chatbot_local_readiness_20261109.json)) |

## 5. Thảo luận

1. **Metadata là thông tin then chốt.** Ablation cho thấy metadata cải thiện ~30 điểm Top-1 và giảm ECE gần 6 lần. Hệ quả thiết kế: bắt buộc đủ 22 trường, không tự điền 0, chuyển ảnh ngoài sang luồng mô tả.
2. **Điểm softmax không phải xác suất lâm sàng.** Ca đoán sai vẫn có điểm Top-1 trung bình ~0,60; khi thiếu metadata, bin (0,9; 1,0] có độ chính xác thực tế chỉ 0,62. UI luôn ghi “điểm tương đối chưa hiệu chuẩn”.
3. **Retrieval tốt trên dev nhưng chưa đủ để tự sinh câu trả lời y khoa.** Score dương/âm chồng nhau, verifier lexical chặn nhầm nhiều; cần reviewer chấm claim-span ↔ passage trước khi tin vào câu trả lời sinh.
4. **Vision LLM có thể bịa giải phẫu.** Đã ghi nhận trường hợp nhầm vùng chậu thành xương sườn; prompt hiện tách quan sát khỏi diễn giải, cấm kết luận “bình thường” khi thiếu căn cứ, và nguồn RAG sau ảnh chỉ là tài liệu đọc thêm.
5. **Quyền riêng tư theo thiết kế:** SQLite không lưu byte ảnh; `CaseStore` chỉ giữ ca trong RAM 30 phút; tên tệp tải lên được thay bằng tên chung.

## 6. Hạn chế và hướng phát triển

| Hạn chế | Hướng xử lý (cần người/thẩm quyền ngoài dự án) |
| --- | --- |
| Không có tập ảnh ngoài có quyền, tách theo bệnh nhân, reference standard chuyên gia | Cohort được cấp quyền + audit overlap với checkpoint (G4) |
| Chưa có nhãn retrieval/entailment độc lập | Reviewer dùng [reviewer packet](../reference/STAGE11_REVIEWER_PACKET_VI.md); chạy `calibrate_retrieval_threshold` trên nhãn đó (G2/G3, bước 7) |
| Intended use chưa được owner khóa | Hoàn thiện [intended-use lock](../reference/STAGE11_INTENDED_USE_LOCK_TEMPLATE_VI.md) (G1) |
| Chưa có đánh giá an toàn/riêng tư/pháp lý độc lập | Reviewer tương ứng (G5–G7) |
| Chất lượng mô tả ảnh của vision LLM chưa được chấm | Bộ ảnh minh họa có quyền và rubric chấm |

## 7. Tái lập

```powershell
.\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q
.\.venv\Scripts\python.exe -m rag.audit --output docs/reference/stage11_integrity_audit_YYYYMMDD_cureus_v1.json
.\.venv\Scripts\python.exe -m rag.replay_reports --output docs/reference/stage11_replay_YYYYMMDD_cureus_v1.json
.\.venv\Scripts\python.exe -m tools.verify_stage11_registers
.\.venv\Scripts\python.exe -m tools.chatbot_doctor
.\.venv\Scripts\python.exe -m tools.run_chatbot   # hoặc 08_start_chatbot.bat, mở http://127.0.0.1:8765
```

Kết quả chạy lại ngày 09/11/2026 được ghi tại [final_verification_20261109.json](../reference/final_verification_20261109.json).

## 8. Kết luận

Đồ án đã hoàn thành các mục tiêu kỹ thuật có thể tự thực hiện: pipeline phân loại X-quang có đánh giá và ablation metadata, kho RAG tái lập được với audit/replay, chatbot đa lượt có định tuyến, từ chối và trích nguồn, cùng bộ kiểm thử tự động đầy đủ. Theo checklist bảy bước Giai đoạn 11, sáu bước có artifact; bước 7 dừng ở mức có công cụ và bằng chứng rằng chưa thể chọn ngưỡng từ dữ liệu hiện có. Phần còn lại cần nhãn và chữ ký của reviewer độc lập, nên không được tự đánh dấu hoàn tất. Kết quả phù hợp để trình bày như **báo cáo học tập thực nghiệm**, không phải bằng chứng hiệu lực lâm sàng.
