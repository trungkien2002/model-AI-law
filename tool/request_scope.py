"""Classify task and scope before retrieval. Unknown questions never inherit a topic."""
import re
from rag import norm
from case_context import topics as legacy_topics, primary_articles

def social(text):
    q=norm(text).strip()
    q=re.sub(r'ban co nghe(?: ro| thay)? khong|nghe ro khong','',q).strip()
    if re.fullmatch(r'[\W\d]*(?:(?:alo|a lo|hello|hi|chao|xin chao|chao ban|test|kiem tra ket noi)[\W\d]*)+',q):
        return 'greeting'
    if q in ('xin nao','xin cha','xin chao ban','cam on','cam on ban'):return 'greeting'
    return None

def classify(text):
    q=norm(text)
    if social(text):return 'greeting'
    # Specific legal domains precede incidental words such as "kỷ luật" or "lương".
    if any(x in q for x in ('nghi viec rieng','nghi cuoi','nghi ket hon','nghi tang','dam tang')):return 'personal_leave'
    if 'noi quy' in q:return 'internal_rules'
    if any(x in q for x in ('cao tuoi','tuoi nghi huu','nguoi ve huu','da nghi huu')) and any(x in q for x in ('hop dong','ky tiep','lam viec')):return 'elderly_employment'
    if any(x in q for x in ('vo sinh','vo toi sinh','vo sap sinh','vo sinh mo')) or (any(x in q for x in ('thai san','sinh con','sinh mo')) and any(x in q for x in ('bhxh','bao hiem xa hoi','lao dong nam','nguoi chong'))):return 'social_insurance_maternity'
    if any(x in q for x in ('an toan lao dong','an toan ve sinh lao dong','gian giao','sap do','de doa tinh mang','nguy co tai nan','noi lam viec nguy hiem','tu choi lam viec','roi bo noi lam viec')):return 'occupational_safety'
    if any(x in q for x in ('tro cap mat viec','tro cap thoi viec')):return 'employment_allowance'
    if any(x in q for x in ['vat sua','tru sua','phong sua']):return 'lactation'
    if any(x in q for x in ['ky luat','sa thai']) and any(x in q for x in ['hop','thong bao','thanh phan','thu tuc','trinh tu']):return 'disciplinary_procedure'
    if re.search(r'(giu|thu giu|nop|ban chinh).{0,65}(bang|van bang|ho chieu|chung chi|giay to)',q) or 'dat coc' in q:return 'documents'
    if any(x in q for x in ['het han','qua han']) and 'hop dong' in q:return 'contract_expiry'
    if ('xac dinh thoi han' in q or 'vo thoi han' in q) and any(x in q for x in ['khac','so sanh','phan biet']):return 'contract_compare'
    if any(x in q for x in ['lam them','tang ca']):return 'overtime'
    if 'thu viec' in q:return 'probation'
    if any(x in q for x in ['layoff','cat giam nhan su','cat giam lao dong','mat viec','khong li do','khong ly do']):return 'termination'
    old=legacy_topics(text)
    if old:return old[0]
    if 'luong' in q and any(x in q for x in ['tra luong','thanh toan luong','chi luong','ky luong']):return 'wage_payment'
    if 'nghi dinh' in q:
        if re.search(r'\d+\s*/\s*20\d{2}',q):return 'document_lookup'
        return 'clarify_decree'
    return 'unknown'

def scope(question,history):
    intent=classify(question)
    old=[m['content'].strip() for m in history if m.get('role')=='user']
    q=norm(question).strip()
    correction=bool(re.search(r'^(khong[, ]|khong y|y toi|toi hoi|khong phai y|doi chu de|cau hoi khac)',q))
    follow=bool(re.search(r'^(vay|the |con |ban co giai phap|ban co cach|toi khong dong y|co duoc khong|dung khong|nhu vay|toi nen lam gi|lam sao|bo sung|toi bo sung|toi muon bo sung|trong truong hop do|ho van|ho con|cong ty do)',q))
    fact_update=bool(re.search(r'^(da ky|toi ky|hop dong cua toi|luong cua toi|muc luong la|toi lam|da xac dinh|don gia|tong so gio|gio cong|ban ngay|ban dem|bo sung|toi bo sung|\d{1,3}\s*(?:ngay|gio)|thang\s*\d)',q))
    prior=[]
    if intent not in ('greeting','clarify_decree','document_lookup') and not correction and (follow or (fact_update and intent=='unknown')):
        for text in reversed(old):
            previous=classify(text)
            if previous=='greeting':continue
            if intent=='unknown' and (follow or fact_update) and previous!='unknown':intent=previous
            if previous not in (intent,'unknown'):break
            if previous=='unknown' and not (follow or fact_update):break
            prior.insert(0,text)
            if len(prior)>=4:break
    return dict(intent=intent,topics=[intent] if intent not in ('unknown','greeting') else [],
        latest_question=question,prior_user_facts=prior,case_scope_reason='explicit_followup' if prior else 'independent_question',
        retrieval_query=question+('\n'+'\n'.join(prior) if prior else ''),discarded_user_turns=len(old)-len(prior))

def article_plan(state):
    mapping={
        'contract_compare':[20], 'contract_expiry':[20,34,36,39,41],
        'wage_payment':[94,95,96,97,98,102], 'overtime':[98,106,107],
        'probation':[25,24,26,27], 'documents':[17],
        'employment_allowance':[34,46,47,48],
        'personal_leave':[115], 'internal_rules':[118,119,120,121],
        'elderly_employment':[20,148,149,169],
        'occupational_safety':[], 'social_insurance_maternity':[],
        'disciplinary_procedure':[122], 'termination':[36,39,41,42,44,47,48,188,190],
        'lactation':[], 'document_lookup':[],
    }
    if state['intent'] in mapping:return mapping[state['intent']]
    return primary_articles(state) if state['intent'] not in ('unknown','greeting','clarify_decree') else []
