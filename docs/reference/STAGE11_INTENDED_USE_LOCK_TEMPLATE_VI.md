# Mẫu khóa intended use theo chức năng — Giai đoạn 11

> Đây là bản nháp governance để chủ dự án điền, xác nhận, ký và hash. Phần “hiện trạng ghi nhận” được tóm tắt từ tài liệu/code đã rà; không tự động trở thành mục đích pháp lý, tuyên bố sản phẩm, phê duyệt lâm sàng hay phân loại thiết bị. Đừng điền thông tin định danh/bệnh án. Nếu chưa ký, intended use vẫn **chưa khóa** và các quyết định phụ thuộc nó chưa đủ điều kiện.

## 1. Kiểm soát phiên bản

| Trường | Giá trị |
|---|---|
| Intended-use statement ID/version |  |
| Ngày lập (UTC) |  |
| Chủ sở hữu chịu trách nhiệm |  |
| Phiên bản ứng dụng/model/corpus liên quan |  |
| SHA-256 của bản cuối đã ký |  |
| Trạng thái | `draft` / `locked` / `superseded` |
| Bản trước bị thay thế và lý do (nếu có) |  |

## 2. Hiện trạng được ghi nhận trong workspace — chủ dự án phải xác nhận hoặc sửa

| Chức năng | Phạm vi đang mô tả | Giới hạn đã ghi nhận | Xác nhận / sửa của chủ dự án |
|---|---|---|---|
| Classifier X-quang | Demo coursework/nghiên cứu chạy cục bộ; ảnh raster và metadata; trả 10 softmax score, top labels và metadata model/device | Không có claim accuracy lâm sàng; score không hiệu chuẩn thành xác suất bệnh; không dùng chẩn đoán, sàng lọc, triage hoặc quyết định điều trị |  |
| RAG retrieval | Thí nghiệm retrieval học thuật cục bộ trên corpus văn bản cố định; nhận câu hỏi text và trả `candidates_found`, `insufficient_evidence` hoặc `out_of_scope` cùng passage/source | Không nhận ảnh; chưa có API sinh câu trả lời; không diễn giải ca cụ thể; passage candidate chưa chứng minh câu trả lời được hỗ trợ; `answer_ready=false` |  |
| Lưu hồ sơ ca | Demo ứng dụng cục bộ; code có thể giữ tên file, hash ảnh, metadata, score, comment và correction trong vùng lưu đã rà | Chỉ dữ liệu tổng hợp/không định danh cho tới khi privacy/security và data-governance được duyệt; hiện chưa có authentication/authorization ở case endpoint, mã hóa SQLite/WAL hoặc retention policy được cấu hình |  |
| Triển khai | Launcher tài liệu hóa bind `127.0.0.1`, chế độ phát triển một worker | Chưa duyệt shared host, public network, cơ sở y tế hoặc dữ liệu người bệnh thật |  |

Nguồn trạng thái hiện tại: [reviewer packet](STAGE11_REVIEWER_PACKET_VI.md), [local privacy/security review](STAGE11_LOCAL_PRIVACY_SECURITY_REVIEW_20261029.md), [online jurisdictional source review](stage11_online_evidence_review_20261028.md), [regulatory applicability checklist](STAGE11_REGULATORY_APPLICABILITY_REVIEW_VI.md). Bảng này là **snapshot cần owner attestation**, không phải kiểm thử runtime/penetration test.

## 3. Intended use khóa cho từng chức năng

Điền riêng từng chức năng; không dùng một mô tả tổng quát để che khác biệt giữa classifier, retrieval, case-history storage và deployment. Ghi `not applicable` cùng lý do thay vì để mơ hồ.

| Trường bắt buộc | Classifier ảnh | RAG retrieval | Lưu hồ sơ/API |
|---|---|---|---|
| Mục đích cụ thể / nhiệm vụ được hỗ trợ |  |  |  |
| Người dùng dự kiến và năng lực tối thiểu |  |  |  |
| Người/bệnh nhân chịu tác động |  |  |  |
| Môi trường và quy trình sử dụng |  |  |  |
| Input, chất lượng/điều kiện đầu vào |  |  |  |
| Output, uncertainty/abstention và giới hạn |  |  |  |
| Quyết định mà output có thể ảnh hưởng |  |  |  |
| Human oversight và người có quyền override |  |  |  |
| Claims được phép dùng trong tài liệu/marketing |  |  |  |
| Claims/cách dùng bị cấm |  |  |  |
| Population, bệnh lý, tuổi/địa lý/phạm vi giải phẫu |  |  |  |
| Target jurisdiction/market; lý do chọn |  |  |  |
| Data controller/custodian và data-flow boundary |  |  |  |
| Lifecycle: cập nhật model/corpus, monitoring, incident, retirement |  |  |  |
| Evidence còn thiếu và điều kiện go/no-go |  |  |  |

## 4. Cấm suy rộng khi chưa có quyết định được ký

- Không suy “research demo” thành cho phép dùng trên bệnh nhân, hoặc suy một disclaimer thành miễn trừ nghĩa vụ/phân loại pháp lý.
- Không suy từ classifier X-quang sang RAG text-only, hoặc ngược lại; đánh giá intended use, evidence và jurisdiction riêng cho từng chức năng và tích hợp của chúng.
- Không coi top label, softmax score, retrieval hit, citation presence, replay/audit PASS hay reviewer agreement là chẩn đoán, xác suất đã hiệu chuẩn, entailment hoặc clinical validation.
- Không dùng dữ liệu người thật, triển khai lâm sàng/thương mại hoặc bật answer generation chỉ nhờ hoàn thành mẫu này. Phải có quyền dữ liệu, privacy/security, safety, regulatory và independent validation phù hợp.

## 5. Điều kiện thay đổi và mở lại gate

Tạo phiên bản mới khi thay người dùng, mục đích, claims, input/output, population, thị trường, deployment, human oversight, nguồn dữ liệu hoặc chức năng. Ghi impact assessment và mở lại mọi gate bị ảnh hưởng; thay đổi sau unblinding có thể cần bộ blind mới. Lưu bản cũ bất biến cùng hash và ngày hiệu lực.

## 6. Safety review liên quan

Sau khi owner khóa intended use, safety lead đánh giá hazard/use-error theo [safety review guide và CSV template](STAGE11_SAFETY_REVIEW_GUIDE_VI.md); template này không thiết lập rating/ngưỡng mặc định.

## 7. Sign-off trước khi dùng làm protocol input

| Người chịu trách nhiệm | Phạm vi xác nhận | Họ tên/vai trò | Chữ ký/tham chiếu chữ ký | Ngày UTC |
|---|---|---|---|---|
| Chủ dự án / product owner | Tính đúng của mô tả chức năng, claims và phạm vi dự kiến |  |  |  |
| Regulatory reviewer đủ năng lực | Chỉ nhận xét theo jurisdiction/phạm vi được giao; không ký thay chủ dự án |  |  |  |
| Privacy/data-governance reviewer | Dòng dữ liệu và điều kiện xử lý trong phạm vi được giao |  |  |  |
| Clinical safety lead (nếu scope có tác động lâm sàng) | Intended workflow, hazard/oversight trong phạm vi được giao |  |  |  |

**Kết quả:** `locked` / `not locked`; **SHA-256:** ; **người duyệt khóa protocol:** ; **ngày giờ UTC:** .

Nếu intended use còn thiếu chữ ký/field trọng yếu, ghi `not locked`; không lấy giá trị mặc định trong mẫu làm quyết định của tổ chức. Đánh giá nguồn quản lý ở [online evidence review](stage11_online_evidence_review_20261028.md); đó là danh sách đầu mối chính thức để chuyên gia tra cứu, không phải tư vấn pháp lý hay phân loại BoneScope.
