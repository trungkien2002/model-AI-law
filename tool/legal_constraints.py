"""Source-versioned legal interpretation notes and bounded deterministic checks.
Not canned answers: the generator still applies user facts and writes its response.
"""
import re,json,hashlib
from common import ROOT
from rag import norm
NOTES={
 13:'Điều13 xác định quan hệ lao động theo nội dung việc làm có trả công/tiền lương và sự quản lý, điều hành, giám sát, không chỉ tên gọi. Không mặc định mọi thực tập là thử việc; phải hỏi tính chất thực tế và chương trình học khi chưa rõ.',
 24:'Điều24 cho phép ghi thử việc trong HĐLĐ hoặc giao kết hợp đồng thử việc riêng. Chưa ký HĐLĐ không tự chứng minh không có thử việc. Không tự suy toàn bộ3tháng hưởng100% từ ngày đầu; cần tách thời gian thử việc hợp lệ, phần vượt hạn, công việc và thỏa thuận lương.',
 20:'Khoản2Điều20: trong30ngày sau hết hạn mà vẫn làm, quyền/nghĩa vụ theo hợp đồng cũ; hết30ngày chưa ký mới thì chuyển thành không xác định thời hạn. Không nói chuyển hồi tố ngay từ ngày hết hạn. Phân biệt quy tắc ký thêm1lần và các ngoại lệ tại điểm c.',
 25:'Điều25 không có trần1tháng cho mọi công việc. Quản lý doanh nghiệp:180ngày; công việc cần cao đẳng trở lên:60ngày; trung cấp/công nhân kỹ thuật/nhân viên nghiệp vụ:30ngày; việc khác:06ngày làm việc. Thử1lần/công việc. Chưa rõ công việc/trình độ yêu cầu thì hỏi, không mặc định3tháng luôn hợp pháp hoặc luôn trái luật.',
 26:'Điều26: thử việc vẫn có lương thỏa thuận, ít nhất85% mức lương công việc. Không được coi tên thử việc là căn cứ làm không lương; không tự thêm mốc ngày thứ4.',
 36:'Điểm c khoản2Điều36 quy định ít nhất03ngày làm việc cho CHÍNH trường hợp điểm b khoản1 (ốm đau/tai nạn điều trị đủ ngưỡng, chưa hồi phục), kể cả hợp đồng không xác định thời hạn. Không dùng45ngày máy móc cho nhánh này. Điểm d khoản1 là vắng mặt sau thời hạn Điều31; điểm đ là tuổi nghỉ hưu; điểm e là bỏ việc05ngày làm việc liên tục. Không tráo d/đ/e. Thời hạn đặc thù phải kiểm thêm nguồn nếu có.',
 39:'Điều39: đơn phương không đúng35/36/37 là trái luật. Khi user đã xác định không có bất kỳ căn cứ khoản1Điều36, hợp đồng còn hiệu lực, không phải thử việc/hết hạn/thỏa thuận/sa thải thì kết luận theo giả định, không hỏi lại căn cứ đã bị loại trừ.',
 41:'Điều41 tách3nhánh: khoản1 nhận lại+tiền lương/bảo hiểm cho ngày không được làm+ít nhất02tháng lương và tiền do thiếu báo trước nếu vi phạm. Khoản2 là NLĐ không muốn tiếp tục: thêm trợ cấp thôi việc theo46 nếu đủ điều kiện. Khoản3 là NSDLĐ không muốn nhận lại và NLĐ đồng ý: mới có khoản bồi thường thỏa thuận thêm ít nhất02tháng. Không gộp khoản2với3. Lương kỳ trước đã đến hạn là khoản riêng, không gộp vào02tháng.',
 98:'Điểm c khoản1Điều98: làm thêm ngày nghỉ lễ/tết tối thiểu300% đơn giá/lương thực trả theo công việc. Mệnh đề đối với người hưởng lương ngày chỉ gắn với phần CHƯA KỂ tiền lương ngày lễ/tết, không có nghĩa mức300% chỉ dành người hưởng lương ngày. Khoản2: đêm thêm30% lương công việc ngày thường. Khoản3: làm thêm đêm thêm20% lương làm BAN NGÀY của loại ngày tương ứng; không luôn20% đơn giá ngày thường. Với lương giờ làm thêm ĐÊM ngày nghỉ HẰNG TUẦN:200%+30%+20%×200%=270%, không phải250%; lương giờ đêm ngày lễ:300%+30%+20%×300%=390%, chưa kể tiền lương ngày lễ theo điều kiện luật. Không chốt số tiền khi chưa rõ ngày nghỉ lễ thực tế, giờ và đơn giá.',
 108:'Khoản2Điều108 có nhánh làm thêm bảo vệ người/tài sản trong phòng ngừa/khắc phục thiên tai và ngoại lệ nguy cơ tính mạng/sức khỏe theo pháp luậtATVSLĐ. Không dùng điều kiện đồng ý/giới hạn giờ thông thường của107 để phủ định108; không kết luận bắt buộc bất chấp nguy hiểm.',
 122:'Điểm d khoản4Điều122 cấm xử lý kỷ luật TRONG thời gian bảo vệ thai sản/nuôi con dưới12tháng. Không coi là miễn mọi kỷ luật vĩnh viễn. Khoản5 mới là mất khả năng nhận thức/điều khiển khi mắc bệnh. Không tự thêm hình thức kỷ luật giảm lương.',
 123:'Điều123 cho phép xem lại thời hiệu sau thời gian bảo vệ khoản4Điều122, kéo dài theo điều kiện nhưng không quá60ngày từ khi hết thời gian bảo vệ; không bảo đảm chắc còn thời hiệu trong mọi vụ.',
 141:'Điều141 chỉ dẫn sang pháp luậtBHXH, không có bảng số ngày/tỷ lệ/tiền cụ thể. Nghỉ chăm con ốm không phải tự xin chấm dứt hợp đồng. Không dùng thông tin loại hợp đồng/báo trước để thay điều kiện tính chế độBHXH.',
 188:'Điểm a khoản1Điều188: tranh chấp sa thải hoặc đơn phương chấm dứt không bắt buộc hòa giải trước. Tranh chấp tiền lương thông thường cần xem thủ tục hòa giải theo khoản1. Trọng tài theo189 cần kiểm điều kiện thỏa thuận, không ép mọi vụ đều hòa giải rồi mới kiện.',
 190:'Điều190: hòa giải06tháng, trọng tài09tháng, Tòa án01năm từ ngày phát hiện hành vi bị cho là xâm phạm quyền; không tráo các mốc. Khoản4có khoảng thời gian không tính nếu chứng minh đủ điều kiện.',
}
def load_notes(sources):
 registry=json.loads((ROOT/'data/legal_constraints_verified.json').read_text('utf-8'));notes=[]
 by_article={int(s['article']):s for s in sources}
 for a,s in by_article.items():
  item=registry['articles'].get(str(a))
  if item:
   if hashlib.sha256(s['text'].encode()).hexdigest()!=item['source_sha256']:raise ValueError('Nguồn đã đổi: cần rà lại ghi chú pháp lý Điều'+str(a))
   notes.append({'article':a,'note':item['note']})
 return notes
def clause_citation_errors(text,sources):
 clean=re.sub(r'[*_`#]','',text.lower());articles={}
 for source in sources:
  matches=list(re.finditer(r'(?m)^\s*(\d+)\.\s*',source['text']))
  articles[int(source['article'])]={int(m.group(1)):source['text'][m.end():matches[i+1].start() if i+1<len(matches) else len(source['text'])] for i,m in enumerate(matches)}
 refs=[]
 for m in re.finditer(r'(?:điểm\s*([a-zđ])\s*[,;]?\s*)?khoản\s*(\d+)\s*(?:[,;]\s*)?(?:điểm\s*([a-zđ])\s*)?(?:của\s*)?điều\s*(\d+)',clean):refs.append((int(m[4]),int(m[2]),m[1] or m[3]))
 for m in re.finditer(r'điều\s*(\d+)\s*(?:[,;]\s*)?khoản\s*(\d+)\s*(?:[,;]?\s*điểm\s*([a-zđ]))?',clean):refs.append((int(m[1]),int(m[2]),m[3]))
 errors=[]
 for article,clause,point in refs:
  if article not in articles:continue
  sections=articles[article]
  if clause not in sections:errors.append(f'Nguồn Điều{article} không có khoản{clause}; không tự gán số khoản.')
  elif point and point not in re.findall(r'(?m)^\s*([a-zđ])\)',sections[clause].lower()):errors.append(f'Nguồn khoản{clause}Điều{article} không có điểm{point}; cần dẫn lại đúng vị trí hoặc chỉ dẫn cấpĐiều nếu chưa chắc.')
 return list(dict.fromkeys(errors))
def canonicalize_flat_article_citations(text,sources):
 """Remove invented sub-numbering only when the supplied article has no clauses.
 Legal prose is untouched; raw model output and every normalization are retained.
 """
 changes=[]
 for source in sources:
  if re.search(r'(?m)^\s*\d+\.\s*',source['text']):continue
  a=int(source['article'])
  patterns=[rf'(?:điểm\s+[a-zđ]\s*)?khoản\s*\d+\s*[,;]?\s*(?:của\s*)?điều\s*{a}(?!\d)',rf'điều\s*{a}(?!\d)\s*[,;]?\s*khoản\s*\d+(?:\s*[,;]?\s*điểm\s*[a-zđ])?']
  for pattern in patterns:
   def replace(m):changes.append({'article':a,'before':m.group(),'after':'Điều '+str(a),'reason':'Supplied article has no numbered clauses; citation label only, not a legal fact correction'});return 'Điều '+str(a)
   text=re.sub(pattern,replace,text,flags=re.I)
 return text,changes
def check_answer(text,state,sources=()):
 q=norm(state['retrieval_query']);a=re.sub(r'[*_`#]','',norm(text));errors=[]
 for m in re.finditer(r'khoan\s*3\s*(?:cua\s*)?dieu\s*24|dieu\s*24\s*[,;]?\s*khoan\s*3',a):
  nearby=a[m.end():m.end()+400]
  if not re.search(r'duoi\s*0?1\s*thang',nearby):errors.append('Khoản3Điều24 chỉ về không áp dụng thử việc với HĐLĐ dưới01tháng; thỏa thuận ghi thử việc trong HĐLĐ/hợp đồng thử việc riêng là khoản1. Không gán nhầm khoản.')
 if any(t in q for t in ('khong thoa thuan','khong dong y')):
  for m in re.finditer(r'ban\s+(?:da\s+)?(?:dong y|thoa thuan)',a):
   if not any(t in a[max(0,m.start()-25):m.start()] for t in ('neu','khong','chua','khi')):errors.append('Đảo ngược dữ kiện: user nói không đồng ý/không thỏa thuận; không được kể lại là bạn đã đồng ý.')
 if any(t in a for t in ('ban khong thuoc dien duoc bao ve','ban khong thuoc truong hop duoc bao ve')) and not any(t in q for t in ('khong thuoc dien duoc bao ve','khong thuoc bat ky truong hop nao tai dieu 37')):errors.append('User chưa xác nhận không thuộc các diện bảo vệ; không tự gán tình trạng sức khỏe/thai sản/nghỉ phép của user.')
 if re.search(r'ban\s+(?:cung\s+)?khong\s+(?:nam|thuoc)\s+trong[^.\n]{0,50}bao ve',a) and not re.search(r'khong\s+(?:nam|thuoc)[^.\n]{0,50}bao ve',q):errors.append('Không được tự xác nhận user nằm ngoài các trường hợp bảo vệ khi user chưa cung cấp dữ kiện này.')
 if re.search(r'khoi kien\s+(?:tai |ra |den )?(?:hoi dong )?trong tai',a):errors.append('Phân biệt thủ tục: yêu cầu Hội đồng trọng tài lao động giải quyết theo điều kiện luật; khởi kiện là tạiTòa án. Không gọi khởi kiện tại trọng tài.')
 if 'holiday_pay' in state['topics'] and 'luong' in q:
  if not re.search(r'300\s*%',text):errors.append('Câu lương ngày lễ/tết bỏ mức tối thiểu300% ở điểm c khoản1Điều98; cần xác định ngày thực sự thuộc nghỉ lễ, không bỏ nguyên tắc.')
  if any(x in a for x in ('thu viec','duoi viec','cham dut hop dong')) and not any(x in q for x in ('thu viec','duoi viec','cham dut')):errors.append('Đưa tình huống thử việc/chấm dứt không do user cung cấp vào câu lương Tết.')
  if 'duong lich' not in q and re.search(r'ban (?:da |dang )?lam[^.\n]{0,60}tet duong lich',a):errors.append('User chưa nói Tết Dương lịch; không tự xác định loại Tết, cần hỏi ngày cụ thể.')
 if 'probation' in state['topics'] and 'luong' in q and not re.search(r'85\s*%',text):errors.append('Câu về lương thử việc thiếu ngưỡng85% của Điều26.')
 if 'probation' in state['topics']:
  for clause in re.split(r'[\n;]',a):
   if not any(t in clause for t in ('toi da','khong qua','gioi han','tran')):continue
   groups=[(('cao dang','dai hoc'),60),(('trung cap','cong nhan ky thuat','nhan vien nghiep vu'),30),(('quan ly doanh nghiep',),180),(('cong viec khac',),6)]
   for names,days in groups:
    if any(t in clause for t in names) and re.search(r'\d',clause) and not re.search(r'(?<!\d)0?'+str(days)+r'\s*ngay',clause):errors.append('Trần Điều25 cho nhóm '+names[0]+' là '+str(days)+' ngày'+(' làm việc' if days==6 else '')+'; không thay bằng số tháng/tuần khác.')
 if 'probation' in state['topics'] and re.search(r'3\s*thang|90\s*ngay',q):
  known_role=any(t in q for t in ('ky su','dai hoc','cao dang','trung cap','quan ly doanh nghiep','nhan vien nghiep vu','cong nhan ky thuat','pho thong'))
  if not known_role and '180' not in a and any(t in a for t in ('qua dai','da het','vuot qua','khong con','khong duoc phep')):errors.append('Chưa biết chức danh/công việc: không kết luận3tháng luôn vượt hạn; Điều25 có nhánh quản lý doanh nghiệp180ngày. Cần hỏi công việc và tách ngưỡng theo nhóm.')
 if 'termination' in state['topics'] and any(x in q for x in ('dieu tri','chua hoi phuc')):
  threshold=12
  source36=next((s['text'] for s in sources if int(s['article'])==36),'')
  found=re.search(r'đã điều trị\s*(\d+)\s*tháng liên tục đối với người làm việc theo hợp đồng lao động không xác định thời hạn',source36)
  if found:threshold=int(found[1])
  if 'khong xac dinh' in q:
   for m in re.finditer(r'(?:nguong|moc|thoi gian dieu tri toi thieu)\s*(?:toi thieu\s*)?(\d+)\s*thang',a):
    if int(m[1])!=threshold:errors.append('Mâu thuẫn số liệu điều trị: ngưỡng hợp đồng không xác định thời hạn trong nguồn là '+str(threshold)+'tháng liên tục; không viết một ngưỡng khác kể cả khi chỗ khác ghi đúng.')
  duration=re.search(r'dieu tri[^.\n]{0,80}?(\d+)\s*thang',q)
  if duration and int(duration[1])>=threshold and not re.search(r'(?:0?3|ba)\s*ngay\s*lam\s*viec',a):errors.append('Nhánh điểm b khoản1Điều36 cần đối chiếu mốc03ngày làm việc tại điểm c khoản2, không tự áp45ngày.')
  if 'khong xac dinh' in q:
   for paragraph in a.split('\n\n'):
    if 'khong xac dinh' in paragraph and re.search(r'0?6\s*thang',paragraph) and not re.search(str(threshold)+r'\s*thang',paragraph) and not any(t in paragraph for t in ('khong ap dung','khong phai')):errors.append('Nguồn điểm b khoản1Điều36: HĐ không xác định thời hạn cần điều trị'+str(threshold)+'tháng liên tục chưa hồi phục;06tháng thuộc HĐ xác định12–36tháng, không tráo nhóm.')
  for m in re.finditer(r'45\s*ngay\s*lam\s*viec',a):
   if not any(t in a[max(0,m.start()-25):m.start()] for t in ('khong phai','khong ap dung')):errors.append('Mốc45ngày thông thường là ngày, không phải45ngày làm việc; riêng nhánh bệnh/tai nạn đủ ngưỡng là03ngày làm việc.')
 if 'ban dem' in q and 'nghi hang tuan' in q:
  minimum=200+30+20*200//100
  for m in re.finditer(r'tong(?: cong)?\s*(?:la|bang|it nhat)?\s*[:=]?\s*(\d{3})\s*%',a):
   tail=a[m.end():].lstrip()
   if int(m.group(1))<minimum and not tail.startswith(('+','×','*')):errors.append('Tổng tối thiểu lương giờ làm thêm đêm ngày nghỉ hằng tuần phải tính200+30+20%×200='+str(minimum)+'%, không cộng20điểm phần trăm trên lương ngày thường.')
 if any(t in a for t in ('khoi kien','toa an')):
  for clause in re.split(r'[.\n;]',a):
   if re.search(r'(?:khoi kien|toa an)[^\d.\n;]{0,80}(?:0?6|0?9)\s*thang',clause) and not any(t in clause for t in ('khong phai','khong dong nghia','khong tu','khong mat')):errors.append('Không dùng06/09tháng làm thời hiệu yêu cầuTòa án; khoản3Điều190 là01năm từ ngày phát hiện, có điều kiện khoản4.')
   if 'mat quyen khoi kien' in clause and re.search(r'0?6\s*thang',clause) and 'khong mat' not in clause:errors.append('Quá06tháng hòa giải không tự đồng nghĩa mất mọi quyền khởi kiện; phân biệt các mốc Điều190.')
 if re.search(r'(?:khong duoc lam|khong lam viec)[^.\n]{0,80}bao gom[^.\n]{0,60}luong thang truoc',a):errors.append('Lương kỳ trước đã đến hạn phải tách khỏi tiền lương cho ngày không được làm do chấm dứt; không nói khoản này bao gồm khoản kia.')
 for agency in ('so lao dong','phong lao dong','cuc lao dong','phong ld','so ld','bo lao dong','bo ld','toa an nhan dan cap huyen','co quan quan ly lao dong cap huyen'):
  if agency in a:errors.append('Chưa có nguồn thẩm quyền hiện hành cho tên cơ quan cụ thể '+agency+'; dùng cách gọi cơ quan có thẩm quyền và nói cần xác minh.')
 return list(dict.fromkeys(errors+clause_citation_errors(text,sources)))
