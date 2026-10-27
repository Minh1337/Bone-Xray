# Thử nghiệm kiểm tra độ phủ khái niệm

Chốt trước lần chạy đầu ngày 27/10/2026. Sử dụng corpus 416 đoạn và model E5 hiện có. Không đổi gold của V2; kết quả V2 hiện là regression vì đã xem trong vòng trước.

Phương án: phân tích cụm từ trong câu hỏi bằng danh sách khái niệm Việt–Anh và từ vựng xuất hiện trong corpus; từ có nghĩa chưa nhận diện sẽ yêu cầu làm rõ. Tìm trên tối đa 80 ứng viên rồi yêu cầu có đoạn phủ các khái niệm cần thiết, ưu tiên nguồn tổng quát khi câu hỏi tổng quát. Đây là kiểm tra từ vựng, không phải suy luận entailment hoặc xác nhận kết luận; câu có đủ từ vẫn có thể sai quan hệ, phủ định hoặc con số. `answer_ready` tiếp tục luôn false.

Tính năng thử nghiệm qua cờ `--verify-evidence`, không tự bật mặc định. Điều kiện kỹ thuật để cân nhắc bật sau này: recall không giảm trên bộ regression cũ/V2, không từ chối nhầm quá 10% câu dương và từ chối ít nhất 80% câu âm trên stress suite mới. Đây là mục tiêu thử nghiệm nội bộ, không phải ngưỡng an toàn lâm sàng. Nếu không đạt, giữ opt-in và ghi đủ ca trượt; không sửa từ vựng theo stress test rồi coi kết quả đó là kiểm định mới.

Stress suite `rag/data/evaluation_evidence_v3.json` gồm 10 câu dương và 10 câu âm bằng Việt/Anh, do cùng AI soạn và đóng băng trước lần đo; chưa phải tập độc lập hoặc thẩm định chuyên môn. File config riêng nằm tại `rag/data/evidence_config.json` để không thay cấu hình baseline.

## Kết quả sau khi chạy

Phương án lọc nghiêm ngặt **không đạt**: V3 từ chối 10/10 câu âm nhưng cũng từ chối nhầm 5/10 câu dương; V2 test đã xem bị chặn cả 8/8 câu dương. Nguyên nhân nổi bật là câu tiếng Việt dùng từ chưa có trong danh sách, không phải thiếu bằng chứng trong corpus. Giữ opt-in qua `--verify-evidence`; không bật mặc định.

Sau kết quả đó, đã tách phần xếp hạng khái niệm thành phương án khám phá `--rerank-concepts`, không lọc câu theo từ chưa biết. Nó đạt 10/10 câu regression, 8/8 mỗi phần V2 và 9/10 câu V3; khả năng từ chối câu âm không cải thiện. Kết quả rerank là khám phá trên các tập đã xem, không phải phép kiểm định chưa từng thấy. Cần một tập mới độc lập trước khi dùng kết quả này để chấp nhận phương án mặc định.

Số liệu và diagnostics từng câu tại `stage11_evidence_rank_20261027/`; không chỉnh gold hoặc whitelist theo các ca này rồi tiếp tục coi đó là kiểm định độc lập. Corpus và cấu hình hybrid cũ vẫn giữ nguyên.
