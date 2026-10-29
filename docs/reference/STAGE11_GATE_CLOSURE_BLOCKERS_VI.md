# Vì sao nghiệm thu Stage 11 vẫn 0/7 — blocker và bước đóng cổng

**Cập nhật:** 29/10/2026  
**Trạng thái:** hồ sơ và kỹ thuật đã được chuẩn bị đáng kể; chưa có cổng nào đủ điều kiện ghi CLOSED. Tài liệu này tách rõ artifact đã có khỏi bằng chứng/phê duyệt còn thiếu. Không tự chấm điểm một phần và không thay reviewer.

## Vì sao 85% không mâu thuẫn với 0/7

- **Khoảng 85%** là ước lượng quản lý về phần chuẩn bị trong workspace: code, corpus có provenance, retrieval/evaluation, audit/replay, runbooks, templates và hồ sơ reviewer. Nó không phải tỷ lệ nghiệm thu, không có trọng số chuẩn hóa, và không được cộng với số gate.
- **0/7** là số cổng đã được đóng theo tiêu chí trong register. Muốn tăng số này phải có đúng loại bằng chứng cho từng cổng, người chịu trách nhiệm có thẩm quyền, kết luận/đối chiếu cần thiết và chữ ký hoặc release record. Việc tạo thêm biểu mẫu, tra luật, chạy benchmark nội bộ hay hash ZIP không thay các điều kiện đó.
- Các phần đang chuẩn bị có giá trị, nhưng chưa được tính là nghiệm thu độc lập. Nếu chuyển sang `CLOSED` khi chưa có reviewer/evidence phù hợp thì status sẽ gây hiểu nhầm về kiểm định và mức sẵn sàng sản phẩm.

## Blocker theo từng cổng

| Gate | Đã có trong workspace | Điều kiện chặn trạng thái CLOSED | Người/nhóm cần hành động tiếp |
|---|---|---|---|
| **G1 — Intended use** | Draft theo bốn chức năng (classifier, text RAG, lưu case, deployment), lock template và quan sát code tĩnh. | Product owner chưa chốt từng chức năng, người dùng, claim, dữ liệu, deployment và jurisdiction; chưa có bản scope được ký; reviewer đủ chuyên môn chưa xác nhận phạm vi. | Product/project owner trước; regulatory, privacy và safety reviewer theo chức năng/thị trường. |
| **G2 — Blind labels/adjudication** | Protocol, sampling plan/template, label/adjudication forms và reviewer declaration. | Chưa bổ nhiệm reviewer độc lập/adjudicator; chưa khóa protocol và mẫu trước khi mở nhãn; chưa có blind labels, adjudication log hay release record có chữ ký. | Custodian chuẩn bị freeze; tổ chức độc lập chỉ định reviewer lâm sàng và adjudicator. |
| **G3 — Citation/evidence support** | Evidence-group schema, reviewer packet, retrieval/evidence diagnostics và lịch sử regression. | Chưa có human ratings độc lập cho relevance, direct support, polarity, qualifiers và context; chưa có adjudication/disagreement. Lexical checks không phải entailment. Text RAG hiện không sinh câu trả lời nên citation entailment của generated answer là N/A; điều đó không thay đánh giá support của passage. | Evidence lead đóng protocol; reviewer độc lập thực hiện nhãn sau khi G1/G2 được khóa. |
| **G4 — Cohort, rights, overlap** | 15 leads được sàng lọc; screening register, image-rights templates, upstream BTXRD rights-chain review. | Chưa có cohort đủ điều kiện. Cần quyền dùng ở cấp ảnh/DUA, provenance và manifest ổn định, reference standard, endpoint phù hợp, patient/image overlap và pretraining audit độc lập. Dataset-level license hoặc bài báo công khai không đủ. | Data custodian/rightsholder cung cấp hồ sơ; cohort auditor độc lập xác minh. |
| **G5 — Safety** | Safety guide, hazard template và 5 preliminary prompts. | Intended use chưa khóa; chưa có severity/likelihood rationale theo use case, xác minh controls, residual-risk decision hay safety sign-off đủ thẩm quyền. | Sau G1, clinical safety lead và reviewer lâm sàng đánh giá từng hazard và ký. |
| **G6 — Privacy/security** | Static local review, privacy/security template và 16-item baseline; đã giảm lưu tên file mới. | Chưa có threat/data-flow review của deployment thực tế; access control, retention/deletion, backups/WAL/logs, runtime/host và incident controls chưa được kiểm chứng; chưa có privacy/security approval. | System owner cung cấp deployment/data-flow và bằng chứng vận hành; privacy officer và security reviewer kiểm tra/ký. |
| **G7 — Legal/regulatory** | Review theo nguồn chính thức và registry máy đọc được gồm 11 instruments; có ngày hiệu lực, nguồn và giới hạn. | Chưa khóa thị trường/intended use/provider-deployer role; chưa có ý kiến counsel/reviewer về applicability, classification/pathway và nghĩa vụ. Hai PDF chính thức 363/392 quá lớn để extractor đọc toàn văn trong lượt này; chỉ metadata/title/date được kiểm tra, chưa phân tích điều khoản. | Owner chọn jurisdiction/function; qualified counsel/regulatory reviewer đọc bản ký và ghi rationale/kết luận. |

## Đường đi tới nghiệm thu

1. **G1:** product owner chốt scope theo chức năng và thị trường; pin release/model/corpus/launch config để reviewer biết chính xác thứ được xét.
2. **G2 + G3:** độc lập chỉ định reviewer/custodian; freeze protocol và sampling trước khi lộ labels; thu nhãn mù, adjudicate; ghi evidence-level ratings riêng cho retrieval support.
3. **G4:** chỉ tiến hành external evaluation khi rights chain, manifest, reference standard và overlap audit đạt; nếu không có cohort phù hợp, giữ G4 OPEN và nêu hạn chế.
4. **G5–G7:** dựa trên G1 đã khóa, reviewer kiểm hazard, deployment/data flows và quy định theo function/jurisdiction; ghi bằng chứng, người đánh giá, ngày và quyết định.
5. Chỉ cập nhật từng gate sang **CLOSED** khi closure evidence trong [register chuẩn](stage11_acceptance_gate_status_20261029.csv) đã được đáp ứng và reviewer có thẩm quyền chấp thuận. Sau đó mới đánh giá readiness tổng thể; hiện vẫn `answer_ready=false`.

## Căn cứ trạng thái hiện tại

- [Acceptance gate register](stage11_acceptance_gate_status_20261029.csv)
- [QA v4: 23/23 artifact links and hashes](stage11_gate_cohort_register_qa_20261029_v4.json)
- [Intended-use draft](STAGE11_INTENDED_USE_DRAFT_FOR_OWNER_REVIEW_20261029.md)
- [Reviewer protocol](STAGE11_INDEPENDENT_REVIEW_PROTOCOL_VI.md)
- [Regulatory review and source register](STAGE11_REGULATORY_APPLICABILITY_REVIEW_VI.md)

Structural QA PASS chỉ xác nhận file tồn tại/hash và cấu trúc hồ sơ; không xác nhận tính đúng chuyên môn, quyền dữ liệu, an toàn, tuân thủ hoặc chữ ký.
