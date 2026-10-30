"""Shared storage/configuration. No ML imports before project environment is set."""
import os, json, hashlib, time, re, sys, secrets, threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for key, value in json.loads((ROOT/'configs/storage_environment.json').read_text('utf-8'))['variables'].items():
    folder = ROOT/value
    folder.mkdir(parents=True, exist_ok=True)
    os.environ[key] = str(folder)
os.environ.update(HF_HUB_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1', DO_NOT_TRACK='1', WANDB_DISABLED='true', TOKENIZERS_PARALLELISM='false')
os.environ.update(PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
for stream in (sys.stdout,sys.stderr):
    if stream is not None and hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')

def confined(value):
    # ASVS v5.0.0-5.3.2: canonical paths restricted to the project directory.
    path = (ROOT/value).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('Đường dẫn phải nằm trong thư mục dự án.')
    return path

def read(path, default=None):
    try: return json.loads(Path(path).read_text('utf-8'))
    except FileNotFoundError: return default

def write(path, value):
    path = Path(path)
    temp = path.with_name(path.name+'.'+secrets.token_hex(4)+'.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), 'utf-8')
    atomic_replace(temp, path)

def atomic_replace(source,target):
    # Windows readers/antivirus can briefly deny FILE_SHARE_DELETE during atomic rename.
    # Retry the rename of the complete temp file; never rewrite a visible JSON in place.
    for attempt in range(20):
        try:os.replace(source,target);return
        except PermissionError:
            if attempt==19:raise
            time.sleep(.01*(attempt+1))

_APPEND_LOCK=threading.Lock()
def append(path, value):
    # Keep each complete JSONL record intact across concurrent request threads.
    line=json.dumps(value, ensure_ascii=False, allow_nan=False)+'\n'
    with _APPEND_LOCK:
        with Path(path).open('a', encoding='utf-8') as f:f.write(line)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def models(): return read(ROOT/'configs/models.json')['models']

def rows(path):
    # ASVS v5.0.0-5.2.1/5.2.2/1.5.2: bounded JSON, schema validation; no pickle input.
    path = confined(path)
    if path.suffix != '.jsonl' or path.stat().st_size > 100*1024*1024:
        raise ValueError('Chỉ nhận JSONL tối đa 100 MB.')
    result = []
    for n, line in enumerate(path.read_text('utf-8-sig').splitlines(), 1):
        if not line.strip(): continue
        row = json.loads(line)
        messages = row.get('messages')
        if not isinstance(messages, list) or not messages or messages[-1].get('role') != 'assistant':
            raise ValueError(f'Dòng {n}: cần messages và phản hồi assistant cuối.')
        for m in messages:
            if m.get('role') not in ('system','user','assistant') or not isinstance(m.get('content'), str) or not m['content'].strip():
                raise ValueError(f'Dòng {n}: role/content không hợp lệ; chỉ hỗ trợ văn bản.')
        result.append(row)
    if not result: raise ValueError('Tệp không có hội thoại.')
    return result

def fingerprint(row):
    return hashlib.sha256(json.dumps(row['messages'], sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def question(row):
    text = '\n'.join(m['content'].split('CÂU HỎI')[-1] for m in row['messages'] if m['role']=='user')
    return re.sub(r'\s+', ' ', text).strip().casefold()

def configuration(data):
    def number(key, default, low, high, kind=int):
        value = kind(data.get(key, default))
        if not low <= value <= high: raise ValueError(f'{key}: phải trong [{low}, {high}].')
        return value
    model = data.get('model', models()[0]['local_path'])
    if model not in [m['local_path'] for m in models()]: raise ValueError('Model không thuộc danh mục local.')
    train = str(confined(data.get('train_file','data/train/messages.jsonl')).relative_to(ROOT)).replace('\\','/')
    test_rows = rows('data/test/messages.jsonl')
    training = rows(train)
    held = {fingerprint(r) for r in test_rows}
    heldq = {question(r) for r in test_rows}
    if any(fingerprint(r) in held or question(r) in heldq for r in training):
        raise ValueError('Dữ liệu train trùng hội thoại/câu hỏi với tập test được bảo vệ.')
    valid = data.get('validation_file') or None
    if valid:
        valid = str(confined(valid).relative_to(ROOT)).replace('\\','/')
        vr = rows(valid)
        seen = held | {fingerprint(r) for r in training}
        seenq = heldq | {question(r) for r in training}
        if any(fingerprint(r) in seen or question(r) in seenq for r in vr):
            raise ValueError('Validation trùng train/test. Cần dữ liệu độc lập; không dùng test để chọn model.')
    rank=number('rank',8,8,16)
    if rank not in (8,16): raise ValueError('LoRA rank chỉ hỗ trợ 8 hoặc 16.')
    if 'initial_adapter_run' not in data and read(ROOT/'configs/training_defaults.json',{}).get('initial_adapter_run'):
        raise ValueError('Hãy mở lại tool để chọn rõ học nối adapter hay tạo adapter mới; cửa sổ cũ chưa có lựa chọn này.')
    initial_run=(data.get('initial_adapter_run') or '').strip()
    initial_sha=None
    if initial_run:
        if not re.fullmatch(r'[A-Za-z0-9_-]+',initial_run): raise ValueError('Mã run khởi tạo không hợp lệ.')
        origin=confined('runs/'+initial_run);old=read(origin/'config.json');artifact=read(origin/'artifact.json')
        if not old or not artifact or read(origin/'state.json',{}).get('status')!='completed': raise ValueError('Cần run đã hoàn tất và có adapter.')
        if old['model']!=model or old['rank']!=rank: raise ValueError('Model nền và rank phải khớp adapter nguồn.')
        initial_sha=sha(origin/'adapter/adapter_model.safetensors')
        if initial_sha!=artifact['sha256']: raise ValueError('Hash adapter nguồn không khớp artifact.')
    purpose=data.get('purpose','user')
    if purpose not in ('user','tool_smoke'): raise ValueError('Mục đích tác vụ không hợp lệ.')
    return dict(initial_adapter_run=initial_run or None,initial_adapter_sha256=initial_sha,model=model, train_file=train, validation_file=valid,purpose=purpose,
        max_seq_length=number('max_seq_length',4096,256,8192), batch_size=number('batch_size',1,1,4),
        accumulation=number('accumulation',4,1,64), rank=rank,
        learning_rate=number('learning_rate',0.0002,0.000001,0.005,float), epochs=number('epochs',3,1,20),
        seed=number('seed',42,0,2147483647), gradient_checkpointing=bool(data.get('gradient_checkpointing',True)),
        checkpoint_steps=number('checkpoint_steps',1,1,1000),
        method='QLoRA 4-bit NF4', assistant_only_loss=True, truncation='reject',
        compute_dtype='bfloat16',frozen_embeddings_dtype='float32_peft_preparation',attn_implementation='sdpa',lora_targets='language_attention_qkvo',
        warmup_ratio=0.05, weight_decay=0.0, max_grad_norm=1.0)

def encode(tokenizer, messages, limit):
    """Locate assistant spans in the model's own rendered chat; mask all other tokens."""
    full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    spans = []
    for i, message in enumerate(messages):
        if message['role'] != 'assistant': continue
        prefix = tokenizer.apply_chat_template(messages[:i], tokenize=False, add_generation_prompt=True)
        end = tokenizer.apply_chat_template(messages[:i+1], tokenize=False, add_generation_prompt=False)
        if not full.startswith(prefix) or not full.startswith(end):
            raise ValueError('Chat template không bảo đảm prefix; không thể xác minh assistant mask.')
        start = len(prefix)
        if not full[start:].startswith(message['content']):
            raise ValueError('Nội dung assistant bị chat template biến đổi; dừng để kiểm tra mask.')
        spans.append((start, len(end.rstrip('\n'))))
    tokens = tokenizer(full, add_special_tokens=False, return_offsets_mapping=True)
    ids, offsets = tokens['input_ids'], tokens['offset_mapping']
    labels = [token if b>a and any(a>=start and b<=end for start,end in spans) else -100 for token,(a,b) in zip(ids,offsets)]
    supervised = sum(x!=-100 for x in labels[1:])
    if not supervised: raise ValueError('Assistant mask không có token được giám sát.')
    return dict(input_ids=ids, labels=labels, tokens=len(ids), supervised_tokens=supervised,
                over_limit=max(0,len(ids)-limit))

def gpu():
    import subprocess
    try:
        output = subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu','--format=csv,noheader,nounits'], text=True, timeout=5, creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        name,total,used,util,temp = [v.strip() for v in output.splitlines()[0].split(',')]
        return dict(name=name,total_mb=float(total),used_mb=float(used),utilization=float(util),temperature=float(temp),scope='Toàn GPU, bao gồm ứng dụng khác')
    except Exception as exc: return dict(name=None,reason=str(exc),utilization=None,used_mb=None,total_mb=None)
