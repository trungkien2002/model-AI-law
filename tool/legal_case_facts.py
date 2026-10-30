"""Small explicit rule evaluations; only user-stated premises, bounded to sources.
Unknown facts remain unknown. These outputs are not a factual finding about a real case.
"""
import re
from rag import norm
def derive_source_facts(state,sources):
 q=norm(state['retrieval_query']);available={int(s['article']):s['text'] for s in sources};facts={}
 if 'termination' not in state['topics']:return facts
 if 36 in available and 'khong xac dinh' in q and 'dieu tri' in q:
  duration=re.search(r'dieu tri[^.\n]{0,80}?(\d+)\s*thang',q)
  threshold=re.search(r'đã điều trị\s*(\d+)\s*tháng liên tục đối với người làm việc theo hợp đồng lao động không xác định thời hạn',available[36])
  if duration and threshold:
   continuous='lien tuc' in q and 'khong lien tuc' not in q
   facts['medical_duration_rule']={'source':'điểm b khoản1Điều36','user_months':int(duration[1]),'threshold_months':int(threshold[1]),'continuous_confirmed':continuous,'time_condition_met':int(duration[1])>=int(threshold[1]) if continuous else None,'scope':'Chỉ kiểm điều kiện thời gian; còn cần khả năng chưa hồi phục, Điều37 và thủ tục. Nếu áp dụng chính nhánh này, báo trước03ngày làm việc.'}
 contract_active='khong xac dinh thoi han' in q or bool(re.search(r'hop dong[^.\n]{0,45}con han',q))
 trial_excluded='da het thu viec' in q or 'khong thu viec' in q
 no_ground=bool(re.search(r'xac nhan[^.\n]{0,100}khong co[^.\n]{0,80}can cu',q)) and bool(re.search(r'dieu\s*36',q))
 no_mutual='khong thoa thuan nghi' in q or 'khong thoa thuan cham dut' in q
 no_discipline='khong bi ky luat' in q or 'khong bi sa thai' in q
 if 39 in available and contract_active and trial_excluded and no_ground and no_mutual and no_discipline:
  facts['article39_under_user_assumptions']={'conclusion':'Đơn phương chấm dứt trái pháp luật theo Điều39','scope':'Chỉ theo các giả định USER đã xác định; không phải kết quả điều tra. Không hỏi lại căn cứ đã được loại trừ.','wants_return':bool(re.search(r'muon[^.\n]{0,40}(?:nhan lai|quay lai|tro lai|tiep tuc lam)',q)),'consequence_source':'Điều41; phải nêu rõ nghĩa vụ nhận lại nếu NLĐ muốn tiếp tục, không gộp lương kỳ trước.'}
 return facts
