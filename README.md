# model AI law

Model tiếng Việt chuyên hướng luật lao động, fine-tune từ **Qwen3-4B-Instruct-2507**. Tải model GGUF Q8_0 để nạp vào Ollama; kho luật và mã RAG có sẵn trong repository, sử dụng tùy chọn. Không cần giao diện NIC.

## 1. Tải và nạp model

Cài [Ollama](https://ollama.com/download) và Python 3.11 trở lên. Clone repository hoặc tải Source code rồi giải nén. Mở terminal tại thư mục repository:

```bash
python download_model.py
ollama create model-ai-law -f Modelfile
ollama run model-ai-law
```

Tệp tải ở [Releases v1.0.0](https://github.com/trungkien2002/model-AI-law/releases/tag/v1.0.0). Trọng số được chia thành 3 phần do giới hạn mỗi release asset của GitHub. Script tải, kiểm SHA256 từng phần và ghép thành `model/model-ai-law-Q8_0.gguf` (~4,28 GB). Các tệp `.partXX` không thể nạp trực tiếp vào Ollama.

Nếu đã tải thủ công đủ ba phần vào một thư mục:

```bash
python download_model.py --local-parts /path/to/parts
ollama create model-ai-law -f Modelfile
```

Tên hiển thị dự án là **model AI law**, tên kỹ thuật dùng trong Ollama là `model-ai-law`.

## 2. Dùng thêm kho RAG

Model tải về không tự truy xuất kho luật. Để dùng snapshot pipeline có tra cứu nguồn giống dự án gốc, sau khi nạp model và đảm bảo Ollama đang chạy trên `127.0.0.1:11434`:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements-rag.txt
python rag_query.py "Điều 25 Bộ luật Lao động quy định thời gian thử việc thế nào?"
```

Kết quả gồm câu trả lời và link nguồn đã được ứng dụng chọn. `--json` xuất các trường cho tích hợp ứng dụng khác. Ví dụ Python có lịch sử hội thoại:

```python
from rag_query import create_service
service = create_service()
history = []
result = service.answer("Tôi đang thử việc, lương phải đạt bao nhiêu?", history, log=False)
print(result["answer"])
history.extend([{"role": "user", "content": "Tôi đang thử việc, lương phải đạt bao nhiêu?"},
                {"role": "assistant", "content": result["answer"]}])
```

RAG lấy bản văn từ `data/sources`, tạo chỉ mục lexical trong bộ nhớ, dùng tokenizer đi kèm để tính ngân sách ngữ cảnh. Không dùng dịch vụ embedding trả phí. Không lưu hội thoại trong ví dụ mặc định. `create_service()` nạp model trước khi bắt đầu giới hạn thời gian trả lời; lần khởi động đầu có thể chậm, tối đa chờ 300 giây. Máy cần Internet để tải model/thư viện lần đầu; sau khi cài đủ, inference và kho luật chạy cục bộ. Các link văn bản gốc cần Internet để mở.

## 3. Nội dung repository

- `model_manifest.json`, `SHA256SUMS`: dung lượng, hash và nguồn gốc trọng số.
- `Modelfile`: cấu hình model độc lập, ngữ cảnh 8.192 token.
- `data/`: văn bản và metadata cần cho RAG, ghi chú đối chiếu.
- `tool/`: snapshot mã suy luận, chọn nguồn và xử lý câu hỏi của dự án.
- `models/Qwen3-4B-Instruct-2507/`: tokenizer, không chứa trọng số model nền.
- `MODEL_CARD.md`: quá trình fine-tune, giới hạn và giấy phép.

Đây là model nghiên cứu/thực nghiệm. Không coi token accuracy hoặc trích dẫn là chứng nhận đáp án đúng luật. Xem model card trước khi sử dụng cho quyết định pháp lý.
