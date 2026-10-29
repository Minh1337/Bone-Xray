# Phiếu closeout privacy/security và quản trị dữ liệu — Giai đoạn 11

> Phiếu trống cho data controller/privacy counsel/security reviewer. Không phải DPIA/đánh giá pháp lý, pentest, chứng nhận bảo mật hoặc phê duyệt dùng dữ liệu. Điền theo intended-use statement đã được owner ký và jurisdiction cụ thể; nếu thiếu căn cứ, ghi `not assessed`/`not evaluable`, không suy ra đạt. Không ghi dữ liệu nhận diện hoặc kể case thật vào phiếu.

## 1. Phiên bản và thẩm quyền

| Trường | Giá trị |
|---|---|
| Study / deployment ID |  |
| Intended-use version + SHA-256 |  |
| Application/model/corpus/config versions |  |
| Jurisdiction(s) and proposed setting |  |
| Data controller / institution |  |
| Data processor / hosting owner (nếu có) |  |
| Security reviewer / qualification |  |
| Privacy/legal reviewer / qualification |  |
| Review date (UTC) |  |
| Phiếu này SHA-256 |  |

## 2. Known baseline từ static review hiện có

[Static review 29/10/2026](STAGE11_LOCAL_PRIVACY_SECURITY_REVIEW_20261029.md) chỉ đọc source và hướng dẫn; không gọi API runtime, không xem DB ca thật và không xác minh host/ACL/backup. Tài liệu hiện mô tả launcher bind `127.0.0.1`; case endpoints chưa có authentication/per-user authorization; SQLite/WAL không cấu hình encryption-at-rest hoặc retention; upload pixels vào temp dir; metadata, filename/hash, scores, comments/corrections có thể được giữ; xóa vật lý qua WAL/backup chưa xác minh. Hãy xác nhận lại trên đúng commit, cấu hình và host; không xem các ghi chú này là bằng chứng runtime.

## 3. Checklist evidence — ghi một dòng cho từng mục áp dụng

Mỗi mục ghi một trạng thái: `open`, `pass_with_evidence`, `gap`, `not_applicable_with_reason` hoặc `not_evaluable`. `pass` cần artefact/evidence và reviewer xác nhận; không dùng lời hứa hoặc thiết kế dự kiến thay cho kiểm chứng. Thêm hàng khi cần.

| ID | Phạm vi review | Câu hỏi / evidence cần có | Status | Artefact/hash/version | Owner | Reviewer | Gap, residual risk, điều kiện chặn |
|---|---|---|---|---|---|---|---|
| P01 | Purpose / authority | Mục đích, vai trò controller, thẩm quyền xử lý và data-use scope được xác định; applicable legal basis/notice/consent/ethics route do chuyên gia xác nhận |  |  |  |  |  |
| P02 | Data inventory | Data-flow map theo từng chức năng gồm image, filename, metadata, hash, scores, comments, corrections, logs, cache/temp, DB/WAL, backup và export |  |  |  |  |  |
| P03 | Data minimization | Mỗi field cần thiết, giới hạn, redaction/de-identification, free-text policy và cách ngăn identifiers không cần thiết |  |  |  |  |  |
| P04 | Data subjects / transparency | Người chịu tác động, thông báo/quyền áp dụng, cách xử lý yêu cầu chủ thể và ngoại lệ được người đủ thẩm quyền rà |  |  |  |  |  |
| P05 | Research ethics / access | Ethics/IRB hoặc quyết định miễn trừ; data-use agreement, consent/waiver và quyền tái sử dụng nếu áp dụng |  |  |  |  |  |
| P06 | Identity / authentication | Cấu hình thực tế và threat model; xác thực trước mọi endpoint/hành động xử lý hoặc xem dữ liệu khi bối cảnh yêu cầu |  |  |  |  |  |
| P07 | Authorization / isolation | Role/access matrix, per-user/tenant isolation, least privilege, admin path, session/CSRF/CORS/network boundary và negative access checks |  |  |  |  |  |
| P08 | At-rest / in-transit security | Mã hóa DB/WAL/temp/backups/export, transport, key custody/rotation/recovery; evidence trên host thật |  |  |  |  |  |
| P09 | Temporary files / memory | Temp directory ACL, abnormal shutdown, cleanup, swap/crash dump, volume snapshot/backup và data remanence |  |  |  |  |  |
| P10 | Retention / deletion | Policy theo loại dữ liệu; TTL, user deletion, cascade, WAL/checkpoint, backups và chứng cứ xác minh xóa; retention owner |  |  |  |  |  |
| P11 | Logs / observability | Không lộ ảnh, identifiers, access tokens hoặc nội dung nhạy cảm; retention/access và audit log được rà |  |  |  |  |  |
| P12 | Third parties / transfers | Vendors, processors, analytics, model/API egress, remote support, localization/cross-border transfer và hợp đồng/quyền |  |  |  |  |  |
| P13 | Threat / vulnerability review | Abuse cases, dependency/container/host exposure, patching, backup restore, incident response; independent test phù hợp phạm vi |  |  |  |  |  |
| P14 | Incident / rights handling | Owner, triage, containment, breach/escalation timelines theo law/policy đã được counsel xác nhận, notification, evidence preservation and drill |  |  |  |  |  |
| P15 | Change / lifecycle | Model/corpus/config updates, access changes, monitoring, drift, user training, decommission and data-return/deletion |  |  |  |  |  |
| P16 | Residual risk / decision | Risk acceptance criteria được controller/authority phê duyệt; residual-risk decision, constraints, stop/go and reopening triggers |  |  |  |  |  |

## 4. Decision và điều kiện triển khai

- Intended-use version được review:  
- Dữ liệu / nhóm chủ thể trong phạm vi:  
- Quyết định: `not_approved` / `approved_with_constraints` / `approved_for_defined_scope` / `not_applicable_with_reason`  
- Dữ liệu tổng hợp/synthetic-only constraint còn áp dụng?  
- Hành động đóng gap, owner và deadline:  
- Residual risk được chấp nhận bởi đúng authority? (evidence/signoff):  
- Điều kiện dừng/incident trigger và ngày review lại:  
- Decision record + SHA-256:  

| Người ký | Vai trò/thẩm quyền | Phạm vi | Chữ ký/tham chiếu | Ngày UTC |
|---|---|---|---|---|
| Data controller / owner |  |  |  |  |
| Privacy/legal reviewer |  |  |  |  |
| Security reviewer |  |  |  |  |
| Institutional/ethics authority (nếu áp dụng) |  |  |  |  |

Dữ liệu thật chỉ được đưa vào khi các authority phù hợp đã ký phạm vi cụ thể và mọi điều kiện chặn đã đóng bằng chứng. Một review cục bộ hoặc bind vào loopback không tự tạo authentication, bảo vệ dữ liệu hay tuân thủ luật. Các văn bản nguồn hiện được liệt kê tại [online source review](stage11_online_evidence_review_20261028.md); cần counsel kiểm tra toàn văn, hiệu lực/chuyển tiếp và jurisdiction đúng thời điểm.
