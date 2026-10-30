"""Conservative Decimal calculator; no inferred dates, workdays, or wage components."""
import re
from decimal import Decimal, InvalidOperation
from rag import norm

def money(raw,unit=''):
    raw=raw.replace(' ','')
    if unit in ('trieu','tr'):
        if not re.fullmatch(r'\d+(?:[.,]\d{1,2})?',raw):raise ValueError('ambiguous money')
        return Decimal(raw.replace(',','.'))*1000000
    if not re.fullmatch(r'\d+|\d{1,3}(?:[.,]\d{3})+',raw):raise ValueError('ambiguous money')
    return Decimal(raw.replace('.','').replace(',',''))

def parse(question,prior=()):
    text='\n'.join([*prior,question]);q=norm(text)
    result={'missing':[],'basis':{},'warnings':[]}
    # ASVS 2.2.1/2.2.3: unambiguous positive numbers and reasonable related ranges.
    try:
        hours=re.findall(r'(?:lam them(?: gio)?|tang ca)\s*(\d+(?:[.,]\d+)?)\s*(?:tieng|gio)|(?:\b)(\d+(?:[.,]\d+)?)\s*(?:tieng|gio)\s*(?:lam them|tang ca)',q)
        if not hours:
            hours=[(x,'') for x in re.findall(r'(\d+(?:[.,]\d+)?)\s*(?:tieng|gio)\s*(?:vao |ngay |chu nhat|thu bay)',q)]
        hs=[Decimal((a or b).replace(',','.')) for a,b in hours]
        hs=list(dict.fromkeys(hs))
        duration=hs[0] if len(hs)==1 else None
        if duration is not None and not 0<duration<=24:raise ValueError('hours out of range')
        hourly=re.findall(r'(?:don gia(?: tien luong)? gio|luong gio)[^\n;]{0,45}?(\d[\d.,]*)\s*(dong|vnd|trieu|tr)\b',q)
        monthly=re.findall(r'(\d[\d.,]*)\s*(trieu|tr|dong|vnd)\s*(?:dong)?\s*/?\s*(?:mot )?thang',q)
        wage=money(*hourly[-1]) if hourly else None
        if wage is not None:result['basis']['hourly_wage']=str(wage)
        if wage is None and monthly:
            amount=money(*monthly[-1]);result['basis']['monthly_wage']=str(amount)
            # Explicit normal hours or explicit workdays AND hours/day, never guess 22/26.
            normal=re.findall(r'(?:tong (?:so )?gio|gio cong chuan|gio lam viec binh thuong)[^\n;]{0,35}?(\d+(?:[.,]\d+)?)\s*gio',q)
            days=re.findall(r'(\d+)\s*ngay\s*(?:cong chuan|lam viec binh thuong)',q)
            daily=re.findall(r'(\d+(?:[.,]\d+)?)\s*(?:gio|tieng)\s*/\s*ngay',q)
            denominator=Decimal(normal[-1].replace(',','.')) if normal else (Decimal(days[-1])*Decimal(daily[-1].replace(',','.')) if days and daily else None)
            if denominator is not None:
                if not 0<denominator<=248:raise ValueError('normal hours out of range')
                # A net salary, allowances, or explicit uncertain basis needs clarification.
                if any(x in q for x in ('luong net','thuc linh','bao gom phu cap','gom tien an')):
                    result['missing'].append('phần tiền lương thực trả của công việc dùng làm căn cứ, tách khoản không tính')
                else:
                    wage=amount/denominator;result['basis'].update(normal_hours=str(denominator),hourly_wage=str(wage),assumption='Tiền lương tháng đã nêu là đúng phần lương làm căn cứ theo Điều55; cần xác nhận nếu có khoản loại trừ.')
            else:result['missing'].append('tổng giờ làm việc bình thường dùng làm căn cứ trong tháng (hoặc ngày công và giờ/ngày), cùng xác nhận phần lương được tính')
        if wage is None and not monthly:result['missing'].append('đơn giá lương giờ thực trả của ngày làm việc bình thường, hoặc lương tháng và giờ làm căn cứ')
        if wage is not None and not 0<wage<=100000000:raise ValueError('wage out of range')
        if duration is None:result['missing'].append('số giờ làm thêm cụ thể cho cùng một loại ngày/ca')
        weekly=any(x in q for x in ('nghi hang tuan','nghi thu 7 va cn','nghi thu bay va chu nhat','nghi thu 7 va chu nhat','nghi thu 7 va cn','ngay nghi tuan')) or ('chu nhat' in q and re.search(r'nghi[^.\n]{0,40}(cn|chu nhat)',q))
        holiday=any(x in q for x in ('ngay le','ngay tet','mung 1/1','quoc khanh'))
        daytime=any(x in q for x in ('ban ngay','khong lam dem','khong vao ban dem'))
        nighttime=not daytime and any(x in q for x in ('ban dem','lam dem','22h','22 gio'))
        if not weekly and not holiday and not any(x in q for x in ('ngay thuong','ngay lam viec binh thuong')):
            result['missing'].append('ngày làm thêm có phải nghỉ hằng tuần/lễ hay ngày làm việc bình thường')
        if not daytime and not nighttime:result['missing'].append('giờ làm thêm là ban ngày hay có giờ ban đêm (22h–06h)')
        if holiday:result['missing'].append('ngày lễ cụ thể, cách trả lương và phần lương lễ đã hưởng để tách đúng các khoản')
        result['rate']='2' if weekly and not nighttime else '2.7' if weekly and nighttime else '1.5' if daytime and not holiday else None
        if result['rate'] is None and not result['missing']:result['missing'].append('đơn giá làm thêm ban ngày tương ứng để xác định đúng phần làm thêm ban đêm')
        result['duration']=str(duration) if duration is not None else None
        if not result['missing'] and result['rate'] and wage:
            result['total']=str((wage*Decimal(result['rate'])*duration).quantize(Decimal('1')))
    except (ValueError,InvalidOperation):
        result['missing'].append('số liệu không mơ hồ, trong phạm vi hợp lý; vui lòng ghi lại đơn giá, giờ công và ca làm')
    result['missing']=list(dict.fromkeys(result['missing']))
    return result

def explain(result):
    rate=result.get('rate')
    if 'total' in result:
        b=result['basis'];hourly=Decimal(b['hourly_wage'])
        total_number=format(int(result['total']),',').replace(',','.')
        opening=f"Theo dữ kiện và cơ sở lương bạn đã xác định, tiền làm thêm tối thiểu cho phần giờ này là **{total_number} đồng**."
        hourly_display=format(hourly,',.4f').replace(',','_').replace('.',',').replace('_','.').rstrip('0').rstrip(',')
        total_display=format(int(result['total']),',').replace(',','.')
        calculation=f"Phép tính: {hourly_display} đồng/giờ × {rate.replace('.',',')} × {result['duration']} giờ = {total_display} đồng (làm tròn đến đồng)."
        assumption=b.get('assumption','Đơn giá giờ được hiểu là tiền lương giờ thực trả của ngày làm việc bình thường, đúng căn cứ theo Điều 55 Nghị định 145/2020/NĐ-CP.')
        if rate=='2.7':calculation+=' Hệ số làm thêm đêm ngày nghỉ tuần: 200% + 30% + 20% × 200% = 270%.'
        return opening+'\n\n'+calculation+'\n\n'+assumption+' Căn cứ: Điều 98 Bộ luật Lao động và Điều 55, Điều 57 Nghị định 145/2020/NĐ-CP. Kết quả chỉ cho các giờ/cơ sở lương đã nêu, chưa phải tổng quyền lợi mọi kỳ.'
    rule='Nếu toàn bộ giờ là ban ngày của ngày nghỉ hằng tuần, tiền làm thêm tối thiểu = đơn giá lương giờ ngày thường × 200% × số giờ làm thêm. Nếu làm đêm cần tách phần giờ và khoản trả thêm.' if rate in ('2','2.7') else 'Tiền làm thêm phải tính theo đơn giá lương giờ đúng căn cứ, loại ngày và số giờ/ca làm, không lấy lương tháng chia mặc định cho 22/24/26 ngày.'
    return 'Mình chưa thể chốt một số tiền chính xác vì còn thiếu dữ kiện tính lương.\n\n'+rule+'\n\nBạn bổ sung: '+ '; '.join(result['missing'])+'. Theo Điều 98 Bộ luật Lao động và Điều 55, Điều 57 Nghị định 145/2020/NĐ-CP, cần xác định đúng căn cứ trước khi tính; mình sẽ tính tiếp khi có các thông tin này.'
