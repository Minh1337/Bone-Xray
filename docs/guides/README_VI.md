# Tài liệu kiểm tra mô hình X-quang trên Windows

## Tài liệu điều phối dự án

- [Lộ trình thực hiện dự án cho AI](../LO_TRINH_THUC_HIEN_DU_AN_AI.md): runbook chi tiết
  từ chuẩn bị môi trường, kiểm tra model, API, UI, SQLite đến kế hoạch RAG/LLM.
- [Báo cáo tiến độ dự án](../reports/Bao_cao_tien_do.docx): báo cáo theo chương, dùng để đọc,
  in hoặc bàn giao.

Tài liệu này là hướng dẫn thao tác kỹ thuật của giai đoạn kiểm tra model.

---

# Bước 1 — Kiểm tra mô hình X-quang trên Windows

Gói này dành cho Windows 10 64-bit, Ryzen 5 7535HS, RTX 3050 Laptop, RAM 8 GB.
Chạy từng ảnh, FP32, không training lại và không sửa trọng số. Chưa tích hợp API LLM.
RTX 3050 có nhiều dung lượng VRAM khác nhau; chương trình sẽ ghi dung lượng thực tế.
Chưa thể bảo đảm tốc độ/bộ nhớ trước khi chạy với trọng số thật trên máy của bạn.

## 1. Chuẩn bị

1. Giải nén toàn bộ ZIP vào một thư mục, ví dụ `D:\Bone_Xray_Local_Check`. Không chạy bên trong ZIP.
2. Cài Python 3.11 64-bit có Python Launcher. Bộ cài Windows có tại:
   https://www.python.org/downloads/release/python-3119/
   Chọn **Windows installer (64-bit)**, bật Python Launcher và Add python.exe to PATH.
   Đây là phiên bản được chọn cho môi trường tái lập này, không phải khuyến nghị dùng bản Python mới nhất.
3. Chép trọng số chính bạn xuất từ notebook vào `model/best_model.pt`.
   Tên phải chính xác; không dùng `last_checkpoint.pt` thay thế. Không cần tải trọng số lên chat.
4. Đặt ảnh test vào `test_images`. Giữ nguyên ảnh test gốc, không chụp màn hình hay resize lại.
5. Khi cài đặt cần Internet và vài GB dung lượng đĩa trống cho thư viện. Đóng ứng dụng nặng khi chạy vì RAM chỉ có 8 GB.

Gói đã có mã model/inference gốc và config, metadata processor, val_transform từ các tệp bạn gửi.
Không thay đổi tên lớp model hoặc cấu trúc mạng khi kiểm tra lần đầu.
Checkpoint và joblib có thể chứa mã thực thi: chỉ nạp bộ tệp do chính bạn xuất và tin cậy.

## 2. Cài môi trường

Nhấp đúp `01_setup.bat`. Đợi thông báo `Setup complete`.
Cửa sổ có thể ít cập nhật; tiến độ chi tiết nằm ở `logs/setup.log`.
Không cần bật PowerShell execution policy, không cần cài CUDA Toolkit riêng cho bộ kiểm tra này.
Cần driver NVIDIA tương thích với bản PyTorch CUDA. Nếu không nhận GPU, gửi log để xử lý;
không tự gỡ driver hoặc cài nhiều bản CUDA.

Lựa chọn môi trường: Python 3.11, torch 2.6.0 + torchvision 0.21.0 CUDA 12.4,
scikit-learn 1.6.1, Albumentations 2.0.8, timm 1.0.15.
Hai phiên bản sklearn/Albumentations được xác định từ tệp đã gửi. Phiên bản torch/timm
gốc của notebook chưa được xác minh; các bản trên là môi trường thử được ghim phiên bản.
Nếu strict load hoặc phép biến đổi lỗi, gửi log và phiên bản thư viện notebook, không bỏ strict=True.
Lệnh PyTorch được đối chiếu tại https://docs.pytorch.org/get-started/previous-versions/.

## 3. Điền cases.json

Mở `cases.json` bằng VS Code hoặc Notepad. Tệp là một danh sách ca.
Mẫu có null để buộc bạn nhập dữ liệu thật; chưa điền thì chương trình sẽ dừng rõ lý do.

- `id`: mã tự đặt, không trùng giữa các ca, ví dụ `case_001`.
- `image`: ví dụ `test_images/IMG000123.jpeg`. Dùng dấu `/` để tránh lỗi escape JSON.
- `metadata.age`: tuổi dạng số, ví dụ `35`, không phải chuỗi `"35"`.
- `metadata.gender`: đúng `"M"` hoặc `"F"` như dataset.
- 20 trường còn lại: số `0` hoặc `1`, giữ đúng giá trị trong dòng dataset của ảnh.
  Không tự suy ra các nhóm xương/khớp/chi từ tên ảnh. Không tự điền tất cả bằng 0.
- Giữ nguyên tên khóa có khoảng trắng hoặc dấu gạch nối như `hip bone`, `knee-joint`.
- Không biết metadata thì gửi lại dòng dữ liệu để xử lý, không tự bịa giá trị.
- `true_label`: nhãn thật nếu có, nếu chưa có giữ `null`.
- `expected_top1`: nhãn do notebook dự đoán trên đúng ảnh này, không phải nhãn thật;
  chưa có thì giữ `null`.
- `expected_scores`: nếu có, là object đủ 10 tên lớp và xác suất softmax từ notebook;
  chưa có giữ `null`. Không dán 12 xác suất phân cấp trực tiếp vào đây.

Các tên lớp đúng: `no-tumor`, `osteochondroma`, `multiple osteochondromas`,
`simple bone cyst`, `giant cell tumor`, `osteofibroma`, `synovial osteochondroma`,
`other bt`, `osteosarcoma`, `other mt`.

Để thêm ca, sao chép object đầu trong mảng, ngăn cách bằng dấu phẩy, đổi id và dữ liệu.
Không thêm dấu phẩy sau phần tử cuối. Lần đầu chỉ dùng 1–3 ảnh.
Nếu metadata hiện nằm trong CSV/Excel, có thể gửi các dòng tương ứng để chuyển sang JSON;
chưa cần gửi toàn bộ dataset.

## 4. Chạy kiểm tra

Nhấp đúp `02_run_check.bat`. Mặc định chọn CUDA nếu PyTorch nhận GPU, nếu không thì dùng CPU.
Chương trình kiểm tra đầu vào, tính SHA256, nạp model strict, kiểm tra config và metadata,
rồi chạy mỗi ảnh 1 lần làm nóng + 3 lần đo. Thời gian gồm đọc ảnh, tiền xử lý và dự đoán,
không gồm nạp model. Nạp model được đo riêng. Batch size suy luận luôn là 1.
Mỗi lượt tạo thư mục kết quả mới để không ghi đè lượt trước.

Nếu thiếu VRAM, chương trình ghi lỗi; đóng các ứng dụng dùng GPU rồi thử lại.
Có thể dùng `03_run_cpu.bat` để thử CPU. Không giảm kích thước ảnh hoặc thay preprocessing.
Với RAM 8 GB, CPU cũng có thể chậm hoặc thiếu bộ nhớ; log sẽ giúp quyết định bước tiếp.

## 5. Đọc và gửi kết quả

Mở thư mục mới nhất trong `results`:
- `report.json`: môi trường, mã kiểm tra tệp, điểm số đủ 10 lớp, thời gian, RAM/VRAM và lỗi.
- `predictions.csv`: bảng tóm tắt (chỉ tạo sau khi đã chạy tới giai đoạn dự đoán).
- `run_log.txt`: log ngắn.
Gửi `report.json` và `run_log.txt`; nếu cài lỗi, gửi `logs/setup.log`.
Nếu không thấy results, gửi `logs/last_run_console.txt`.
Không cần gửi ảnh hoặc trọng số lại để chỉ xem lỗi môi trường.

`TECHNICAL_CHECK_PASSED` chỉ nghĩa là mô hình nạp được và đầu ra vượt qua kiểm tra kỹ thuật.
Nếu `notebook_comparison = NOT_PROVIDED`, chưa xác minh khớp notebook.
`TOP1_ONLY` chỉ đối chiếu nhãn, chưa đối chiếu mọi điểm số.
`SCORES_CHECKED` có sai số tối đa và ngưỡng 1e-4. Sai số vượt ngưỡng cần xem xét,
không tự kết luận checkpoint hỏng và không tự nới ngưỡng để nhận PASS.
Kiểm tra lặp lại dùng ngưỡng 1e-5. Nhãn dự đoán sai so với true_label được ghi nhận riêng,
không đồng nghĩa với lỗi chạy mã. Vài ca này không thay thế đánh giá trên 563 ảnh test.

## 6. Phạm vi xác minh gói

Đã kiểm tra cú pháp và unit test cho kiểm tra metadata/đường dẫn/điểm tham chiếu trên môi trường soạn gói.
Chưa chạy cài đặt trên Windows, chưa chạy GPU RTX 3050 và chưa nạp best_model.pt vì chưa có tệp.
Không có tải ảnh lên Internet hoặc gọi API LLM trong mã kiểm tra. Bước cài thư viện dùng Internet.
Giao diện và API LLM sẽ được xây sau khi kiểm tra mô hình này hoàn tất.
