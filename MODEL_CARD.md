# model AI law

Trợ lý tiếng Việt về pháp luật lao động. Model nền: **Qwen/Qwen3-4B-Instruct-2507**, khoảng 4 tỷ tham số, non-thinking. Bản phát hành GGUF Q8_0, ngữ cảnh cấu hình 8.192 token.

## Nguồn gốc

QLoRA/LoRA học nối tiếp: 150 mẫu (3 epoch), thêm 310 mẫu (1 epoch), thêm 5.278 mẫu (1 epoch). Tổng 5.738 bản ghi đưa vào ba đợt không đồng nghĩa 5.738 tình huống độc lập. Đợt cuối gồm cả dữ liệu cũ/chưa duyệt theo lựa chọn thực nghiệm. Run cuối: `20261029-080822-887db3`. Trọng số phát hành lấy đúng blob GGUF của model đang phục vụ `nic-luat-lao-dong-5278:latest`, không phải model nền chưa fine-tune.

## Kết quả và giới hạn

Token accuracy ghi nhận khi train ba đợt: 69,11%, 72,87%, 81,65%. Đây là mức khớp token nhãn khi học trên các tập khác nhau, **không phải độ chính xác pháp luật**. Chưa có phép đo độc lập chứng minh tỷ lệ sai luật thấp hơn model gốc. Kiểm tra tình huống còn thấy lỗi điều/khoản, thiếu quyền lợi, bỏ phép tính và sai cách hiểu nghĩa vụ. Fine-tune không làm chất lượng tăng đều qua mọi ca.

Model độc lập không tự tra luật. Kho RAG và runtime trong repository là thành phần riêng, chứa văn bản có phiên bản, không mặc định là toàn bộ pháp luật hiện hành. Dẫn nguồn không chứng minh mọi diễn giải đúng. Cần đối chiếu văn bản, thời điểm và dữ kiện trước khi dùng cho quyết định thực tế.

## Phạm vi phát hành

Không kèm lịch sử chat, mật khẩu, khóa API, optimizer, checkpoint train, dữ liệu train thô hoặc giao diện desktop. Mã RAG là snapshot pipeline thực tế; mã chọn nguồn/kiểm tra có thể từ chối đáp án và chưa xử lý hoàn toàn mọi câu hỏi nhiều vế. Không bật self-review như một chứng nhận pháp lý.

## Tài nguyên

Tệp GGUF khoảng 4,28 GB. Dung lượng bộ nhớ chạy còn gồm KV cache và runtime, tăng theo ngữ cảnh và số lượt đồng thời. Thử nghiệm cục bộ dùng RTX 5070 12 GB; không bảo đảm tốc độ tương đương trên máy khác. RAG ví dụ cần Python 3.11+, Ollama và thư viện trong requirements-rag.txt. Chỉ tệp model có thể dùng mà không cài Python RAG.

## Giấy phép

Apache-2.0 cho mã phát hành và model phái sinh theo giấy phép model nền. Văn bản luật và metadata nguồn giữ thông tin xuất xứ; giấy phép không tuyên bố sở hữu nội dung bên thứ ba. Xem LICENSE và NOTICE.
