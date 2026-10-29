# Mẫu khai báo reviewer và ký nhận Giai đoạn 11

> Dùng một bản riêng cho mỗi reviewer; để trống cho đến khi người thật tự khai báo. Không đưa dữ liệu bệnh nhân hoặc thông tin định danh người bệnh vào biểu mẫu. Lưu bản đã ký trong vùng kiểm soát truy cập; chỉ chia sẻ bản đã khử thông tin liên hệ nếu công bố.

## 1. Kiểm soát hồ sơ

| Trường | Giá trị |
|---|---|
| Blind review / study ID |  |
| Reviewer opaque ID |  |
| Vai trò | `primary_reviewer` / `adjudicator` / `evaluation_statistician` / `privacy_security_reviewer` / `regulatory_reviewer` / `other` |
| Phiên bản protocol |  |
| Protocol SHA-256 |  |
| Intended-use statement SHA-256 |  |
| Rubric và acceptance worksheet SHA-256 |  |
| Thời điểm khóa protocol (UTC) |  |
| Thời điểm ký bản khai báo (UTC) |  |

## 2. Năng lực phù hợp với phần review

| Trường | Giá trị do reviewer tự khai |
|---|---|
| Họ tên |  |
| Chức danh/chuyên ngành |  |
| Đơn vị công tác |  |
| Đào tạo/chứng nhận liên quan |  |
| Phạm vi chuyên môn reviewer nhận đánh giá |  |
| Kinh nghiệm liên quan (mô tả ngắn, không cần hồ sơ bệnh án) |  |
| Hạn chế hoặc phần reviewer không đủ năng lực kết luận |  |

Không ghi số giấy phép, ngày sinh, địa chỉ nhà, tài khoản cá nhân hay thông tin nhận diện không cần thiết vào bản lưu chung. Chủ dự án xác minh credentials qua kênh phù hợp ngoài tập blind và chỉ lưu kết quả xác minh tối thiểu theo quy định của đơn vị.

## 3. Độc lập, bảo mật và xung đột lợi ích

Đánh dấu `Yes` / `No` / `Not applicable` và giải thích khi câu trả lời là `No` hoặc có ngoại lệ.

| Khai báo | Trả lời | Giải thích / biện pháp quản lý |
|---|---|---|
| Tôi không tạo hoặc gắn nhãn các bộ dev/gold hiện đang dùng để phát triển BoneScope. |  |  |
| Tôi không tune retrieval, policy, evidence config hay ngưỡng trên tập blind này. |  |  |
| Trước ngày ký, tôi chưa xem query, gold, hit/rank, similarity, route, output hay report của blind set này. |  |  |
| Tôi sẽ không trao đổi nhãn độc lập với reviewer khác trước khi các bản được khóa hash. |  |  |
| Tôi đã khai báo mọi lợi ích tài chính, quan hệ nghề nghiệp, quyền sở hữu trí tuệ, vai trò tác giả, hoặc lập trường học thuật có thể ảnh hưởng đánh giá. |  |  |
| Tôi đã khai báo việc từng tham gia điều trị/chẩn đoán/giảng dạy/công bố liên quan đến tài liệu hoặc ca đang review, nếu áp dụng. |  |  |
| Tôi đồng ý giữ bí mật nội dung blind và báo ngay sự cố lộ nhãn/dữ liệu. |  |  |

**Xung đột cụ thể:** `none declared` / mô tả; ghi rõ mục review bị ảnh hưởng và phương án: công khai / reviewer khác thay thế / recusal / giới hạn phạm vi / biện pháp khác.

**Recusal hoặc giới hạn phạm vi:**

____________________________________________________________________________

## 4. Xác nhận rubric và ngưỡng trước khi mở kết quả

Reviewer xác nhận đã xem và đồng ý áp dụng các nội dung dưới đây trước khi chạy retrieval hoặc unblind. Không điền `Agree` nếu chưa đọc hoặc còn bất đồng.

| Mục cần khóa | Trạng thái | Artifact/hash hoặc ý kiến |
|---|---|---|
| Intended-use boundary, nhóm người dùng và câu hỏi ngoài phạm vi |  |  |
| Định nghĩa fully answerable / partially answerable / in-scope unanswerable / out-of-scope |  |  |
| Rubric acceptable evidence groups, exact span và required qualifiers |  |  |
| Sampling frame, sampling unit, phân tầng và xử lý query family/cụm phụ thuộc |  |  |
| Mẫu số từng metric, cách xử lý missing/ambiguous labels và minimum denominator |  |  |
| CI method và mức tin cậy cho từng metric |  |  |
| Quy tắc dùng cận CI để kết luận pass / stop / inconclusive |  |  |
| Pass threshold, stop threshold và risk rationale cho từng gate/metric áp dụng |  |  |
| Quy tắc adjudication, bảo toàn nhãn gốc và hash trước unblinding |  |  |

Mọi ngưỡng ở worksheet phải được ký và hash trước khi mở kết quả. Nếu chưa thống nhất, ghi `Not locked`; khi đó không chạy để tuyên bố nghiệm thu. Các phiên bản sau unblinding phải có blind set mới nếu thay đổi rubric, query, threshold, corpus, index/model, code hoặc config.

## 5. Kết quả review và giới hạn kết luận

Chỉ hoàn tất sau khi review đúng phạm vi được phân công; không suy từ audit hash, test phần mềm hoặc retrieval metric sang độ đúng lâm sàng.

| Trường | Giá trị |
|---|---|
| Phạm vi đã review |  |
| Artifact kết quả và SHA-256 |  |
| Disagreement/adjudication record và SHA-256 (nếu có) |  |
| Cổng/metric được khuyến nghị | `pass` / `revise` / `stop` / `not evaluable` |
| Căn cứ và giới hạn |  |
| Sai lệch protocol, sự cố blind hoặc missingness |  |
| Residual risk và việc cần làm |  |
| Ngày ký kết luận (UTC) |  |
| Chữ ký reviewer / chữ ký số hoặc tham chiếu hồ sơ ký |  |

`pass` chỉ áp dụng cho cổng/phạm vi được reviewer xác nhận và không tự động đóng các cổng còn lại. Không đặt `answer_ready=true` chỉ dựa trên mẫu khai báo này; quyết định trạng thái do gate owner có thẩm quyền ghi sau khi kiểm tra toàn bộ bằng chứng và sign-off bắt buộc.
