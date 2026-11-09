# Biên bản AI-only internal review BoneScope

**Ngày:** 10/11/2026  
**Phạm vi:** cấu trúc repository, tính nhất quán code, regression phần mềm, provenance RAG và tài liệu vận hành.  
**Loại review:** AI-assisted internal review. `independent: false`.  
**Mục đích:** hoàn thiện báo cáo học tập/thực nghiệm và kiểm tra chất lượng phần mềm; không phải review lâm sàng, pháp lý, bảo mật độc lập hoặc chứng nhận sản phẩm.

## Kết luận

Trong phạm vi đã kiểm tra, không phát hiện lỗi nghiêm trọng mới do lần tái cấu trúc package gây ra. Repository đã được tổ chức thành `bonescope/` cho source nghiệp vụ, `scripts/` cho launcher, `tools/` cho tiện ích và các thư mục test/docs riêng. Các entrypoint Python, launcher và cấu hình VS Code đã được kiểm tra sau khi di chuyển.

Phần kỹ thuật có thể xác minh trong workspace được xem là **hoàn tất với giới hạn**. Không thay đổi `answer_ready=false`; G1-G7 vẫn `OPEN`.

## Bằng chứng đã kiểm tra

- Full regression: `209 passed`, `227 subtests passed`, 1 cảnh báo deprecation Starlette/AnyIO.
- RAG provenance audit: `PASS`, 22 nguồn / 794 chunks, không thiếu source cache.
- Deterministic replay: `PASS`, 16/16 report khớp, không có preflight mismatch.
- Chatbot doctor: `13/13 PASS`, không gọi provider thật.
- Frontend syntax: `node --check rag/demo_web/app.js` đạt.
- Package entrypoints: `python -m bonescope.check_model --help` và `python -m bonescope.verify_api --help` đạt.
- VS Code `launch.json` và `tasks.json` parse hợp lệ.
- Launcher test sau khi chuyển vào `scripts/`: `7 passed`.
- Pattern scan không phát hiện API key/private key trong file tracked. Cấu hình MCP cá nhân `.mcp.json` đã được gỡ khỏi repository và thêm vào `.gitignore`.

## Các điểm đã xem xét

| Nhóm | Kết quả | Giới hạn |
| --- | --- | --- |
| Import/package | PASS | Đã kiểm tra qua full regression và module help; chưa phải đánh giá mọi môi trường Python khác máy hiện tại |
| Launcher/API/UI | PASS | Không gọi provider thật trong regression; live provider latency/quality không được xác nhận |
| RAG/provenance | PASS về tính toàn vẹn artifact | Audit/replay không đo entailment, factual correctness hoặc chất lượng y khoa |
| Documentation | PASS về đường dẫn vận hành chính | Một số record lịch sử giữ tên/path cũ để bảo toàn provenance của snapshot |
| Secret hygiene | PASS trong phạm vi pattern scan | Không thay thế secret scanner, privacy review hoặc security assessment |

## Findings và disposition

1. **Không có finding blocker về code** trong phạm vi review AI và regression hiện hành.
2. **Không thể gọi review này là independent review:** người thực hiện, bộ câu hỏi và tiêu chí đều thuộc cùng quy trình AI/workspace.
3. **Claim-to-source entailment của generator:** `not evaluable` nếu chưa có nhãn claim-span độc lập và adjudication.
4. **Cohort ảnh ngoài, quyền dữ liệu và checkpoint split:** chưa đủ bằng chứng để đánh dấu eligible hoặc external validation.
5. **Intended use, safety, privacy/security và regulatory:** cần quyết định owner hoặc người có thẩm quyền; AI review không thay thế chữ ký.

## Trạng thái sau review

- `answer_ready=false`
- G1-G7: `OPEN`
- Retrieval threshold: `AWAITING_LABELS`; không cài threshold runtime mới.
- Các benchmark hiện có chỉ là development/regression đã xem, không phải đánh giá độc lập.

Biên bản này được dùng để minh bạch hóa giới hạn của review AI-only, không dùng để nâng claim, đóng gate hoặc tuyên bố hệ thống phù hợp chẩn đoán/điều trị.
