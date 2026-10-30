"""Bounded lexical fallback over reviewed provisions, never an invented source."""
import math,re
from datetime import date
from collections import Counter
from rag import norm,words,STOP

NOISE=set('toi ban minh cho biet hoi xin hay giup theo quy dinh phap luat bo luat nam dieu khoan truong hop cong ty doanh nghiep nguoi lao dong nhu the nao co duoc khong nhung cac va cua thi la voi trong mot ve nay'.split())|set(STOP)

def terms(text):
    return set(words(text))-NOISE

def fallback(question,sources,limit=4,as_of=None):
    q=norm(question)
    if not any(x in q for x in ('lao dong','hop dong','luong','cong ty','cong doan','bhxh','bao hiem','viec lam','nghi viec','nghi ngoi')):return []
    query=terms(question)
    if len(query)<3:return []
    when=as_of or date.today().isoformat()
    unique={s['chunk_id']:s for s in sources
            if (not s.get('valid_from') or s['valid_from']<=when)
            and (not s.get('valid_to') or when<=s['valid_to'])}
    docs=[(s,terms(s['text']),terms(s['text'].split('\n',1)[0])) for s in unique.values()]
    df=Counter(t for _,tokens,_ in docs for t in tokens)
    ranked=[]
    for s,tokens,title in docs:
        shared=query&tokens;headline=query&title
        # Broad labor words alone must not turn an unsupported topic into a conclusion.
        if len(shared)<3 or not headline:continue
        score=sum(math.log(1+len(docs)/(1+df[t])) for t in shared)+2*len(headline)
        ranked.append((score,s))
    ranked.sort(key=lambda row:row[0],reverse=True)
    if not ranked or ranked[0][0]<7:return []
    return [dict(s,retrieval_score=round(score,3)) for score,s in ranked[:limit] if score>=ranked[0][0]*.65]

def citation_ids(ids,sources):
    """Keep valid citations even when prose does not repeat an article number."""
    allowed={s['chunk_id'] for s in sources}
    if not isinstance(ids,list):return []
    return list(dict.fromkeys(x for x in ids if isinstance(x,str) and x in allowed))
