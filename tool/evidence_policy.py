"""Bounded source policy and exact arithmetic; never executes user expressions.

Inputs are data (ASVS V1.5 / V5.3 intent); only project-pinned sources are used.
These checks cannot certify the legal correctness of an answer.
"""
from decimal import Decimal
import re
from rag import norm


def weekly_night_pay(hourly_wage, hours):
    """Only for confirmed overtime on weekly rest, at night, under Article 98.

    Caller must establish legal classification and wage basis first. No eval().
    """
    wage, duration = Decimal(str(hourly_wage)), Decimal(str(hours))
    if not wage.is_finite() or not duration.is_finite() or wage < 0 or not 0 <= duration <= 24:
        raise ValueError('Cần đơn giá không âm và số giờ hợp lệ trong ngày.')
    return {'base_overtime': str(wage * duration * 2),
            'night_addition': str(wage * duration * Decimal('.3')),
            'night_overtime_addition': str(wage * duration * 2 * Decimal('.2')),
            'total': str(wage * duration * Decimal('2.7')),
            'multiplier': '2.7', 'article': '98',
            'scope': 'Đơn giá đã xác định đúng; không phải tổng lương mọi kỳ.'}


def source_policy(state, sources):
    ids = {int(s['article']) for s in sources}
    q = norm(state['retrieval_query'])
    notes = []
    if 141 in ids:
        notes.append('Điều 141 chỉ dẫn sang pháp luật bảo hiểm xã hội. Kho này chưa có nguồn chế độ BHXH phù hợp thời điểm. Không tính số ngày, tỷ lệ hoặc số tiền chăm con chỉ từ Điều 141; hỏi thời điểm, tuổi con, hồ sơ và nguồn BHXH cần đối chiếu. Không lấy lương tháng nhân thẳng số ngày.')
    if 98 in ids and 'ban dem' in q and any(t in q for t in ('hang tuan', 'ngay nghi tuan')):
        notes.append('Chỉ nếu đã xác định làm thêm vào ban đêm của ngày nghỉ hằng tuần: khoản 1 điểm b, khoản 2 và khoản 3 Điều 98 cho các thành phần 200% + 30% + (20% × 200%) = 270% đơn giá giờ ngày thường, không phải 250%. Chưa có đúng đơn giá/số giờ thì chưa ra số tiền. Ngày lễ và ngày thường là nhánh khác.')
    if 36 in ids:
        notes.append('Chỉ có câu “bị đuổi không lý do” chưa xác định thử việc, loại và hiệu lực hợp đồng, hình thức chấm dứt. Hỏi phần chưa rõ; không hỏi lại phần USER đã chốt. Điều 35 là quyền đơn phương của người lao động, không phải quyền của doanh nghiệp. Vi phạm thời hạn báo trước cũng cần đối chiếu Điều 39, không loại khỏi trái luật chỉ vì có lý do.')
    if 188 in ids:
        notes.append('Tranh chấp tiền lương thông thường: xem hòa giải tại khoản 1 Điều 188 và ngoại lệ theo yêu cầu cụ thể. Tranh chấp đơn phương chấm dứt/sa thải là ngoại lệ điểm a. Không tạo Ủy ban giải quyết tranh chấp hoặc nêu cơ quan địa phương chưa có nguồn hiện hành.')
    return notes


def explicit_weekly_night_calculation(state, sources):
    """Narrow parser for an explicit confirmed classification and named wage basis.
    Unknown/ambiguous narratives return None; never infers a legal employment status.
    """
    q=norm(state['retrieval_query']);ids={int(s['article']) for s in sources}
    if 98 not in ids or 'da xac dinh' not in q or 'nghi hang tuan' not in q:
        return None
    if not ('ban dem' in q or ('sau 22 gio' in q and 106 in ids)):
        return None
    hs=re.findall(r'\b(\d+(?:[.,]\d+)?|mot|hai|ba|bon|nam|sau|bay|tam)\s+gio\s+lam\s+them',q)
    ws=re.findall(r'don gia gio[^\n;]{0,100}?\bla\s+(\d[\d.,]*)\s*(?:dong|vnd)\b',q)
    if len(hs)!=1 or len(ws)!=1:return None
    words={'mot':'1','hai':'2','ba':'3','bon':'4','nam':'5','sau':'6','bay':'7','tam':'8'}
    # Accept dotted thousands only, not ambiguous decimal currency forms.
    if not re.fullmatch(r'\d+|\d{1,3}(?:\.\d{3})+',ws[0]):return None
    result=weekly_night_pay(ws[0].replace('.',''),words.get(hs[0],hs[0]).replace(',','.'))
    result['qualification']='Theo giả định USER đã xác định toàn bộ giờ là làm thêm đêm ngày nghỉ hằng tuần; cần hỏi lại nếu giả định thực tế khác.'
    return result


def evidence_errors(text, state, sources):
    q, a = norm(state['retrieval_query']), re.sub(r'[*_`#]', '', norm(text)).replace('\\','')
    ids = {int(s['article']) for s in sources}
    errors = []
    if 'uy ban giai quyet tranh chap' in a:
        errors.append('Nguồn không có Ủy ban giải quyết tranh chấp lao động; không dùng nơi nộp đơn tự tạo.')
    if re.search(r'dieu\s*220', a) and any(t in a for t in ('khoi kien', 'hoa giai', 'tranh chap')):
        errors.append('Điều220 là hiệu lực thi hành, không phải căn cứ thủ tục giải quyết tranh chấp.')
    if 141 in ids and any(t in q for t in ('bao nhieu', 'tinh', 'muc huong', 'so ngay')):
        # Conservative gate: even hedged numeric entitlements require insurance sources.
        if re.search(r'\d+(?:[.,]\d+)?\s*(?:%|ngay|thang|trieu|dong)', a):
            errors.append('Chỉ có Điều141, chưa có nguồn BHXH để đưa con số ngày/tỷ lệ/tiền hưởng. Bỏ con số không có căn cứ và hỏi nguồn/dữ kiện cần thiết.')
    if 98 in ids and ('ban dem' in q or 'ban dem' in a) and 'hang tuan' in q:
        if re.search(r'200\s*%?\s*\+\s*30\s*%?\s*\+\s*20\s*%(?!\s*[×*x])', a):
            errors.append('Công thức thiếu cơ sở20%×200%; không cộng20điểm phần trăm thành250%.')
        for m in re.finditer(r'250\s*%',a):
            if not re.search(r'khong|sai|loai bo',a[max(0,m.start()-45):m.start()]):
                errors.append('Tỷ lệ250% không đủ cho nhánh làm thêm đêm ngày nghỉ hằng tuần; cần270% theo các giả định đã xác định.')
    calc=explicit_weekly_night_calculation(state,sources)
    if calc:
        paid=re.findall(r'(?:tra|nhan)\s+(\d[\d.]*)\s*dong',q)
        if len(paid)==1 and re.fullmatch(r'\d+|\d{1,3}(?:\.\d{3})+',paid[0]) and Decimal(paid[0].replace('.',''))<Decimal(calc['total']):
            for m in re.finditer(r'(?:la|da|nay)\s+du(?:\s+toi thieu)?',a):
                if not re.search(r'khong|chua',a[max(0,m.start()-20):m.start()]):
                    errors.append('Khoản đã trả thấp hơn kết quả hàm tính theo giả định USER; không được kết luận đã đủ. Kết quả cần đối chiếu: '+calc['total']+'đồng.')
    return list(dict.fromkeys(errors))


def bounded_application_answer(state,sources):
    """Transparent narrow tools, not a generated answer or a general legal verdict."""
    q=norm(state['retrieval_query']);ids={int(s['article']) for s in sources}
    if 'child_sickness' in state['topics'] and 141 in ids and any(t in q for t in ('bao nhieu','so ngay','ty le','so tien','tinh tien','muc huong')):
        age=re.search(r'con\s*(?:toi\s*)?(\d+)\s*tuoi',q)
        known_age=('Bạn đã cho biết con '+age[1]+' tuổi. ') if age else ''
        if age and int(age[1])>=7:known_age+='Điều141 nói đến chăm sóc con nhỏ dưới07tuổi, nên không tự áp nhánh này cho tuổi đã nêu; cần xem nguồn chế độ phù hợp khác. '
        ask=('thời điểm nghỉ, hồ sơ y tế và tình trạng tham gia BHXH' if age else 'thời điểm nghỉ, tuổi con, hồ sơ y tế và tình trạng tham gia BHXH')
        return {'route':'needs_insurance_sources','answer':
            'Kho hiện tại có Điều 141 Bộ luật Lao động 2019 (số 45/2019/QH14), nhưng chưa có nguồn BHXH phù hợp để tính số ngày, tỷ lệ hoặc số tiền bạn hỏi. Điều 141 dẫn chế độ sang pháp luật BHXH; tôi chưa thể dùng nó để đưa một con số chắc chắn.\n\n'
            +known_age+'Cần xác định '+ask+'; nếu tính tiền còn phải có đúng căn cứ lương và công thức của chế độ áp dụng. Bạn đã cung cấp phần nào thì không cần gửi lại. Hãy bổ sung nguồn BHXH hoặc thông tin hồ sơ còn thiếu, che thông tin cá nhân không cần thiết.\n\n'
            'Trước mắt, giữ giấy tờ khám chữa bệnh, ghi nhận ngày nghỉ và trao đổi với đơn vị làm hồ sơ về văn bản họ đang áp dụng. Không lấy lương tháng nhân thẳng số ngày hoặc tự đoán một tỷ lệ. Đây là bước yêu cầu bổ sung nguồn, chưa phải kết luận mức hưởng.'}
    calc=explicit_weekly_night_calculation(state,sources)
    if not calc:return None
    fmt=lambda n:format(Decimal(n),',.0f').replace(',','.')
    total=Decimal(calc['total']);paid=re.findall(r'(?:tra|nhan)\s+(\d[\d.]*)\s*dong',q)
    opening='Theo các giả định bạn đã xác định, khoản tối thiểu cho số giờ này là '+fmt(total)+' đồng.'
    if len(paid)==1 and re.fullmatch(r'\d+|\d{1,3}(?:\.\d{3})+',paid[0]):
        amount=Decimal(paid[0].replace('.',''));delta=total-amount
        opening=('Khoản '+fmt(amount)+' đồng chưa đủ; còn chênh '+fmt(delta)+' đồng so với mức tối thiểu '+fmt(total)+' đồng cho số giờ này.') if delta>0 else ('Khoản '+fmt(amount)+' đồng không thấp hơn mức tối thiểu '+fmt(total)+' đồng cho số giờ này.')
    answer=opening+'\n\nĐiểm b khoản 1, khoản 2 và khoản 3 Điều 98 Bộ luật Lao động 2019 (số 45/2019/QH14) được đối chiếu cho nhánh làm thêm vào ban đêm của ngày nghỉ hằng tuần: 200% + 30% + (20% × 200%) = 270% đơn giá giờ ngày thường. Phần 20% cuối tính trên mức ban ngày của ngày nghỉ hằng tuần, không cộng thành 250%.\n\n'
    answer+='Từng thành phần của phép tính: '+fmt(calc['base_overtime'])+' đồng làm thêm ngày nghỉ + '+fmt(calc['night_addition'])+' đồng phần đêm + '+fmt(calc['night_overtime_addition'])+' đồng phần làm thêm ban đêm = '+fmt(total)+' đồng.\n\n'
    answer+='Giữ bảng ca, đơn giá giờ, bảng công và bảng lương, gửi phép tính để yêu cầu đối chiếu khoản chênh. Kết quả do công cụ tính, chỉ theo giả định USER đã xác định toàn bộ giờ thuộc đúng nhánh và đơn giá đã đúng căn cứ; không phải kết luận mọi khoản lương hay bồi thường. Nếu một phần giờ thuộc ngày khác hoặc đơn giá chưa đúng, cần tách lại trước khi tính.'
    return {'route':'calculation_under_user_assumptions','answer':answer,'calculation':calc}
