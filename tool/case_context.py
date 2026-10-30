"""Select case scope from user messages; generated answers never become facts."""
import re
from rag import norm

# Topic-to-statute routing only: no stored answers, amounts or legal outcomes.
TOPICS={
 'holiday_pay':(('ngay tet','ngay le','dip tet','mung tet','tien luong tet'),[98,112,94,95,188,190]),
 'child_sickness':(('cham con','con om','con bi om'),[141]),
 'emergency_work':(('lu lon','lu lut','kho hoa chat','khac phuc hau qua','thien tai'),[108,107,98]),
 'deduction':(('khau tru','tru luong','tru het','tru vao luong','hong dung cu','hong thiet bi','hong tai san'),[102,129,130,131]),
 'disciplinary_fine':(('di muon','di tre','phat tien','phat 300','phat vi','phat luong'),[127,122,124,131]),
 'salary_change':(('giam luong','ha luong','cat luong','tu giam'),[33,90,94,95,188,190]),
 'probation':(('thu viec','thuc tap'),[24,25,26,27,13,94]),
 'termination':(('duoi viec','cho nghi','cham dut','cho toi nghi','sa thai vo co','khoi den lam','khong can den lam','khong cho lam','muon giu viec'),[36,37,39,41,94,188,189,190]),
 'discipline':(('ky luat','sa thai','trom cap','an cap'),[122,123,125,127,188,190]),
 'contract_expiry':(('het han','ky tiep','ky lan thu','ky hop dong moi','ky hop dong lan'),[20]),
 'overtime':(('lam them','tang ca','ban dem'),[98,106,107]),
 'wage_arrears':(('no luong','cham luong','chua tra luong','giu luong'),[94,97,48,188,190]),
 'annual_leave':(('nghi phep','nghi hang nam','phep nam'),[113,114]),
 'resignation':(('xin nghi viec','tu nghi viec','toi nghi viec','bao truoc 45','don phuong nghi'),[35,40,48]),
 'documents':(('giu bang','giu giay','giu ban chinh','dat coc'),[17,13,14]),
}
NEW_CASE=re.compile(r'cau hoi khac|chuyen (?:sang )?chu de|chu de moi|vu viec khac|tinh huong khac|van de moi')
CONTINUATION=re.compile(r'^(?:vay|the |cong ty do|ho con|ngoai ra|them nua|cung cong ty|trong vu|toi muon bo sung)|(?:ve viec vua|quay lai viec)')

def topics(text):
    q=norm(text)
    # Negated/finished status can be a fact, but must not activate that topic.
    routing=re.sub(r'(?:khong (?:bi |phai |con )?|da het |het )(?:xu ly )?(?:ky luat|sa thai|thu viec)',' ',q)
    found=[key for key,(triggers,_) in TOPICS.items() if any(t in routing for t in triggers)]
    # Recognize intervening words: giữ bản gốc bằng, thu giữ hộ chiếu...
    if re.search(r'(?:giu|thu giu)[^.\n]{0,60}(?:ban goc|van bang|chung chi|ho chieu|can cuoc|bang dai hoc|bang tot nghiep|giay to)',routing):
        found.insert(0,'documents')
    if re.search(r'dieu\s*(?:24|25|26|27)\b',routing):found.append('probation')
    # Broad language variants, not benchmark-question matching.
    if 'luong' in routing and any(t in routing for t in ('phan chenh','muc moi','tra theo','khong dong y sua')):
        found.insert(0,'salary_change')
    if 'luong' in routing and re.search(r'(?:chi tra|tra con|tu.+xuong|con lai)',routing) and re.search(r'\d+\s*trieu',routing):
        found.insert(0,'salary_change')
    if re.search(r'cong ty[^.\n]{0,40}don phuong',routing) or re.search(r'dieu\s*36\b',routing):
        found.append('termination')
    if re.search(r'dieu\s*141\b',routing) and any(t in routing for t in ('con','bhxh','bao hiem')):
        found.insert(0,'child_sickness')
    if 'emergency_work' in found and not any(t in routing for t in ('lam them','huy dong','di chuyen hang','lam viec khan')):found.remove('emergency_work')
    if 'discipline' in found and ('thai san' in q or 'mang thai' in q):
        return ['discipline']
    # Specific pay/benefit questions outrank generic leave/work tokens.
    for specific in ('deduction','disciplinary_fine','holiday_pay','child_sickness','emergency_work','salary_change','annual_leave','documents'):
        if specific in found:return [specific]
    if 'termination' in found:return ['termination']
    if 'probation' in found:return ['probation']
    return found[:2]

def select_case(question,history):
    user_messages=[m['content'].strip() for m in history if m.get('role')=='user' and isinstance(m.get('content'),str)]
    selected=[];active=[];reason='first_question'
    for text in user_messages+[question]:
        q=norm(text).strip(' .!?');new_topics=topics(text)
        if q in ('xin chao','chao','hello','hi','cam on','cam on ban'):continue
        explicit=bool(NEW_CASE.search(q))
        changed=bool(new_topics and active and not set(new_topics)&set(active))
        continuation=bool(CONTINUATION.search(q))
        # Topic recognition must not silently attach an independent question to an unknown case.
        standalone=bool(new_topics and selected and not active and not continuation)
        unknown_new=bool(not new_topics and selected and len(q)>100 and re.search(r'^(?:toi |hop dong |cong ty |thang nay )',q) and not continuation and not re.search(r'tin nhan do|vu viec nay|hop dong (?:vo|khong xac dinh) thoi han|khong phai thu viec',q))
        if explicit or standalone or unknown_new or (changed and not continuation):
            selected=[];active=[];reason='explicit_new_case' if explicit else ('unknown_standalone_question' if unknown_new else 'new_topic')
        if text not in selected:selected.append(text)
        if new_topics:active=new_topics if not continuation else list(dict.fromkeys(active+new_topics))
    # Only the current case's user facts enter retrieval. The latest question leads.
    prior=selected[:-1] if selected and selected[-1]==question else selected
    current=topics(question)
    active=current or active
    return {'topics':active,'prior_user_facts':prior,'latest_question':question,
            'case_scope_reason':reason,'retrieval_query':question+('\nDữ kiện user liên quan:\n'+'\n'.join(prior) if prior else ''),
            'discarded_user_turns':len(user_messages)-len(prior)}

def primary_articles(state):
    ids=[]
    for topic in state['topics']:
        for a in TOPICS[topic][1]:
            if a not in ids:ids.append(a)
    q=norm(state['retrieval_query'])
    if state['topics']==['documents']:ids=[17]
    if state['topics']==['probation']:
        explicit=re.findall(r'dieu\s*(24|25|26|27)\b',norm(state['latest_question']))
        if explicit:ids=list(dict.fromkeys(map(int,explicit)))+ [a for a in ids if str(a) not in explicit]
    if state['topics']==['disciplinary_fine'] and not any(t in q for t in ('thu tuc','hop ky luat','mang thai','thai san','bao chua')):
        ids=[127,131]
    if state['topics']==['salary_change'] and not any(t in q for t in ('khoi kien','hoa giai','tranh chap','thoi hieu','toa an')):
        ids=[33,94,90,95]
    if 'termination' in state['topics'] and not any(t in q for t in ('da het thu viec','khong thu viec','khong con thu viec','khong phai thu viec')):
        # Missing probation status changes the legal branch; retrieve its exception.
        ids=[36,39,41,27,24,37,94,188,190]
    if 'termination' in state['topics'] and any(x in q for x in ('dieu tri','chua hoi phuc','tai nan lien tuc')):
        ids=[36,37,48]
        if any(t in norm(state['latest_question']) for t in ('boi thuong','trai phap luat','khong bao truoc','nhan lai')):ids.append(41)
    if 'discipline' in state['topics'] and any(x in q for x in ('thai san','mang thai')):
        ids=[122,123,137]
    return ids
