# Phạm vi do người dùng xác định — đề tài học tập thực nghiệm

**Ngày ghi nhận:** 29/10/2026 (UTC+07). **Nguồn:** thông điệp của người dùng trong goal đang thực hiện: “Mục đích làm đề tài này của tôi k phải để cung cấp cho bác sĩ hay người bệnh, nó chỉ là 1 báo cáo học tập có tính thực nghiệm”. Đây là chỉ dẫn về mục tiêu sản phẩm của dự án, không phải chữ ký trên intended-use lock hoặc ý kiến pháp lý.

## Ý nghĩa cho Giai đoạn 11

- Đích bàn giao trước mắt là **báo cáo học tập và bản thực nghiệm cục bộ**, không phải dịch vụ tư vấn/diễn giải ca cho bác sĩ hay người bệnh. Trình bày kết quả RAG như retrieval candidates, metric dev và giới hạn của chúng. Bản giao diện tra cứu local có thể dùng để minh họa quy trình; nó không cần tự sinh lời khuyên để đáp ứng mục tiêu đề tài.
- Không suy từ câu này rằng có quyền dùng dữ liệu bệnh nhân thật, phát hành dữ liệu/ảnh bên thứ ba, triển khai public hoặc tuyên bố độ chính xác y khoa. Giữ demo với câu hỏi giáo dục và dữ liệu được phép; hiện `answer_ready=false`.
- Đánh giá kỹ thuật Stage 11 theo mục tiêu gốc của lộ trình: nguồn/chunk có provenance, index tái lập, retrieval/evaluator, routing/abstention, corpus/index audit, replay và báo cáo trung thực. Điểm dev đã xem hoặc do agent soạn chỉ là kết quả thực nghiệm trong mẫu, không trở thành chứng cứ kiểm định độc lập.
- Bảy gate G1–G7 đang ghi trong register vẫn **OPEN**. Khi phạm vi được owner khóa chính thức, owner và reviewer thích hợp phải xác định gate/tiêu chí nào áp dụng cho **báo cáo thực nghiệm**, gate nào chỉ áp dụng cho triển khai/claims lâm sàng. Không tự đổi CLOSED/N/A, không tự ký, không lấy “chỉ học tập” làm miễn trừ pháp lý.

## Quyết định còn cần ghi rõ trong intended-use lock

| Trường | Định hướng từ người dùng | Điều chưa được xác nhận |
| --- | --- | --- |
| Mục đích | Báo cáo học tập có tính thực nghiệm | Định nghĩa sản phẩm bàn giao, tiêu chí chấm và người có quyền khóa scope |
| Người dùng trực tiếp | Không cung cấp cho bác sĩ hay người bệnh | Nhóm học viên/người hướng dẫn, quyền truy cập thực tế và trình diễn công khai hay nội bộ |
| Dữ liệu | Không có phép dùng dữ liệu người bệnh từ chỉ dẫn này | Corpus/ảnh nào được phép trích, lưu, minh họa và chia sẻ trong báo cáo |
| Output chatbot | Demo tra cứu nguồn là phù hợp với mục tiêu hiện nêu | Có yêu cầu LLM sinh câu trả lời học thuật hay chỉ cần retrieval + trích nguồn |
| Địa điểm và hình thức trình bày | Chưa nêu | Trường/lớp, quốc gia, host cục bộ, bản web/demo công khai hay không |

**Bước tiếp theo:** dùng phạm vi này để owner hoàn thiện [intended-use lock](STAGE11_INTENDED_USE_LOCK_TEMPLATE_VI.md), sau đó reviewer xác định mức bằng chứng phù hợp với những claims thực sự ghi trong báo cáo. Cho tới khi có quyết định đó, `G1=OPEN`; không ép mục tiêu lâm sàng vào đề tài học tập và cũng không coi đề tài học tập là đã nghiệm thu độc lập.
