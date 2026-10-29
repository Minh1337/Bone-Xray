# Rà soát tĩnh luồng dữ liệu cục bộ — Giai đoạn 11

**Ngày:** 2026-10-29  
**Trạng thái:** rà soát mã nguồn theo phạm vi hẹp; không phải pentest, kiểm định cấu hình máy chạy, rà soát pháp lý hay phê duyệt xử lý dữ liệu người bệnh.  
**Kết luận:** chỉ giữ ứng dụng ở chế độ demo local với dữ liệu tổng hợp/không định danh. Cổng privacy/security của Giai đoạn 11 vẫn mở.

**Cập nhật nguồn quy định (29/10/2026):** FDA hiện liệt kê bản cuối tháng 02/2026 *Cybersecurity in Medical Devices: Quality Management System Considerations and Content of Premarket Submissions*; chính FDA ghi bản này thay thế hướng dẫn cuối tháng 06/2025 và đã điều chỉnh để phù hợp QMSR (hiệu lực 02/02/2026). Vì intended use/jurisdiction BoneScope chưa khóa và chưa xác định tình trạng thiết bị, đây chỉ là nguồn hiện hành để regulatory/security reviewer đánh giá applicability, không phải tuyên bố hướng dẫn FDA trực tiếp áp dụng cho prototype. Static review ở tài liệu này không đáp ứng cyber risk assessment, secure-development evidence, SBOM, runtime assessment, pentest hay regulatory submission. [FDA current guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cybersecurity-medical-devices-quality-system-considerations-and-content-premarket) · [Regulatory applicability checklist](STAGE11_REGULATORY_APPLICABILITY_REVIEW_VI.md).

## Phạm vi đã đọc

- `xray_api.py`: nhận và kiểm tra ảnh, chạy predictor, giữ prediction tạm.
- `case_api.py`: endpoint lưu/đọc/xóa ca, comments, corrections và dashboard.
- `database.py`: schema SQLite và lưu trữ.
- `xray_ui.py`: gắn routes và static UI.
- `05_start_api.bat`, `docs/guides/README_FASTAPI_VI.md`: cách chạy được tài liệu hóa.

Không gọi API đang chạy, không đọc database ca thực tế, không tải ảnh lên và không kiểm tra ACL/backup/antivirus/encryption của máy chủ.

## Dòng dữ liệu theo mã hiện tại

1. `POST /predict` nhận ảnh và JSON metadata. Metadata bị giới hạn độ dài; ảnh được stream vào `TemporaryDirectory`, giới hạn 30 MiB, kiểm MIME/giải mã, một frame và 25 triệu pixel (`xray_api.py:121-169`). Ảnh chỉ nằm trong thư mục tạm khi inference; không được đưa vào SQLite.
2. Kết quả gồm prediction ID ngẫu nhiên, hash ảnh, metadata, scores và model metadata. Server giữ bản ghi tạm trong RAM tối đa 10 phút và giới hạn 1.000 mục (`xray_api.py:175-194`).
3. `POST /cases` chuyển bản ghi tạm vào SQLite. DB lưu nhãn filename chung `uploaded-image.<suffix>` cho prediction mới (không lưu tên file do uploader gửi), image hash, metadata, scores, nhãn hiệu chỉnh và thời điểm; comments/corrections lưu trong các bảng riêng (`database.py:53-88, 114-139, 190-245`). Không lưu pixel ảnh trong DB theo code đã đọc.
4. SQLite bật WAL, đặt ở `data/bonescope.db` và không có mã hóa/retention configuration trong các file đã rà (`database.py:16-30`). Xóa ca dùng DELETE và foreign-key cascade; chưa xác minh việc xóa vật lý khỏi WAL, backup hay media (`database.py:180-183`).
5. Hướng dẫn launcher bind `127.0.0.1`, một worker (`05_start_api.bat:10`); hướng dẫn cấm đổi sang `0.0.0.0` và cấm đưa ảnh/metadata ra dịch vụ ngoài (`docs/guides/README_FASTAPI_VI.md:72-76`).

## Findings cần giữ làm điều kiện chặn

| Mức áp dụng | Quan sát | Ý nghĩa và xử lý trước khi mở rộng |
|---|---|---|
| Cao nếu chia sẻ máy/API hoặc triển khai; chưa phải exploit được kiểm chứng | Các endpoint `/cases`, `/cases/{id}`, comments, corrections, delete và dashboard không có authentication/per-user authorization trong router (`case_api.py:42-113`). Hướng dẫn chỉ hỗ trợ bind loopback cho demo. | Không đổi host/mở firewall/đặt reverse proxy hoặc chia sẻ máy khi chưa có identity, access control, CSRF/threat review phù hợp và kiểm thử. ID ca không phải cơ chế phân quyền. |
| Cao nếu dùng dữ liệu định danh | SQLite/WAL lưu metadata và nội dung nhận xét; không thấy encryption-at-rest, retention schedule hay quy trình xóa/backup được cấu hình trong phạm vi mã (`database.py:16-30, 53-88`). | Chưa đưa dữ liệu sức khỏe/ảnh có thể nhận diện vào app. Trước thử nghiệm cần data controller, mục đích/cơ sở xử lý, tối thiểu hóa trường, mã hóa, phân quyền, lưu giữ/xóa có xác minh, backup và quy trình sự cố được người phụ trách duyệt. |
| Trung bình, cần xác nhận tại máy chạy | Ảnh inference được ghi tạm vào đĩa và xóa theo vòng đời `TemporaryDirectory`, nhưng quyền thư mục tạm, volume, backup/snapshot và forensic recovery không được đánh giá. | Xác minh cấu hình host/volume và bảo đảm temp storage phù hợp trước khi dùng dữ liệu nhạy cảm; giới hạn byte/pixel không thay thế biện pháp bảo vệ dữ liệu. |
| Có giới hạn nhưng chưa thay thế governance | Prediction metadata/hash/scores còn trong process RAM tối đa 10 phút; case đã lưu tồn tại đến khi xóa thủ công. | Viết retention/deletion policy, ownership, kiểm chứng cascade và cả WAL/backup; không tuyên bố xóa an toàn từ endpoint DELETE hiện có. |

## Hành động bắt buộc trước khi xử lý dữ liệu thật hoặc deploy

- Chốt intended purpose/jurisdiction, data controller, authority/consent/notice và data-use scope với privacy/legal reviewer.
- Thêm xác thực, role-based authorization và kiểm tra truy cập cho mọi endpoint dữ liệu; quyết định CSRF/rate-limit/audit logging theo threat model.
- Quy định tối thiểu hóa metadata/comments; cấm identifiers không cần thiết và nội dung tự do có thể ghi lộ thông tin.
- Chọn mã hóa khi lưu/truyền và quản lý khóa; kiểm tra quyền file, host accounts, backups, logs, temp volume và quy trình incident.
- Định nghĩa retention, xóa bản ghi và bản sao/WAL/backup; xác minh bằng kiểm thử trên môi trường tách biệt.
- Có reviewer bảo mật/riêng tư độc lập ký trước khi đưa dữ liệu người bệnh vào app; clinical safety và regulatory review vẫn là các cổng riêng.

Rà soát tĩnh ban đầu không thay đổi code. Follow-up 29/10/2026: `xray_api.py` hiện chỉ lưu tên chung `uploaded-image` cùng suffix đã kiểm tra, thay vì basename uploader gửi; integration regression giả lập tên `patient-identifier-123.png` và xác nhận DB nhận `uploaded-image.png`. Đây là giảm thiểu một trường định danh cho bản ghi mới, không xóa/sửa bản ghi cũ, không thay hash/metadata/comments, và không đóng G6. Không đọc DB runtime hay kiểm tra WAL/backup/ACL; suite 86 passed/132 subtests, 1 deprecation warning. [Test record và code hashes](stage11_test_run_20261029_privacy_filename_minimization_full.json). Các endpoint và giới hạn vẫn được mô tả theo source hiện tại, không khẳng định trạng thái runtime. Chi tiết intended-use boundary nằm trong [reviewer packet](STAGE11_REVIEWER_PACKET_VI.md) và [review nguồn](stage11_online_evidence_review_20261028.md).
