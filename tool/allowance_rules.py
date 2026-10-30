"""Source-backed allowance rule lookup; eligibility remains conditional on termination grounds."""
import re
from decimal import Decimal
from rag import norm

def worked_months(text):
    q=norm(text)
    matches=re.findall(r'(?:lam viec thuong xuyen|lam thuong xuyen|lam viec|cong tac)[^.;\n]{0,60}?(\d+(?:[.,]\d+)?)\s*(thang|nam)',q)
    values={Decimal(n.replace(',','.'))*(12 if unit=='nam' else 1) for n,unit in matches}
    return next(iter(values)) if len(values)==1 else None

def calculation_months(text):
    q=norm(text)
    matches=re.findall(r'thoi gian(?: lam viec)?(?: de)? (?:duoc )?tinh tro cap(?: mat viec(?: lam)?| thoi viec)?([^.;\n]{0,35}?)(\d+(?:[.,]\d+)?)\s*(thang|nam)',q)
    values=set()
    for gap,n,unit in matches:
        if any(x in gap for x in ('it hon','duoi','tren','hon','khong qua','toi da','toi thieu','<','>','≤','≥','-','−')):continue
        values.add(Decimal(n.replace(',','.'))*(12 if unit=='nam' else 1))
    return next(iter(values)) if len(values)==1 else None

def salary_months(months,loss):
    # Decimal only; these are already-qualified calculation months, not total tenure.
    if months<0 or months>1200:raise ValueError('Invalid allowance calculation period')
    whole=months//12;remaining=months%12
    years=whole+(Decimal('.5') if 0<remaining<=6 else 1 if remaining>6 else 0)
    return max(Decimal(2),years) if loss else years*Decimal('.5')

def answer(plan):
    q=norm(plan['retrieval_query']);latest=norm(plan['latest_question'])
    loss='tro cap mat viec' in q
    severance='tro cap thoi viec' in q
    months=worked_months(plan['latest_question'])
    if months is None:months=worked_months(plan['retrieval_query'])
    counted=calculation_months(plan['latest_question'])
    if counted is None:counted=calculation_months(plan['retrieval_query'])
    comparison=loss and severance
    if 'tro cap that nghiep' in q:
        return ('Trợ cấp mất việc và trợ cấp thất nghiệp là hai chế độ khác nhau. Phần nguồn hiện có xác định trợ cấp mất việc do người sử dụng lao động chi trả theo Điều 47 Bộ luật Lao động và khoản 2 Điều 8 Nghị định 145/2020/NĐ-CP. Chưa có đủ nguồn chế độ bảo hiểm thất nghiệp phù hợp để kết luận điều kiện hoặc mức hưởng trợ cấp thất nghiệp; không tự dùng công thức của trợ cấp mất việc cho khoản đó.')
    if any(x in latest for x in ('luong lam can cu','luong binh quan','muc luong de tinh','lay luong thang nao','tinh theo luong')):
        return ('Theo khoản 5 Điều 8 Nghị định 145/2020/NĐ-CP, tiền lương làm căn cứ tính trợ cấp thôi việc, trợ cấp mất việc là **tiền lương bình quân của 06 tháng liền kề theo hợp đồng lao động** trước khi thôi việc hoặc mất việc. Không mặc định chỉ lấy lương tháng cuối. Trường hợp có nhiều hợp đồng kế tiếp hoặc hợp đồng cuối vô hiệu về tiền lương cần đối chiếu quy định tương ứng tại khoản 5.\n\nBạn cung cấp cơ sở lương theo hợp đồng của 06 tháng liên quan nếu muốn tính số tiền; cần xác định riêng điều kiện hưởng và thời gian được tính theo Điều 46, Điều 47 Bộ luật Lao động.')
    if counted is None and worked_months(plan['latest_question']) is None and any(x in latest for x in ('bao hiem that nghiep','bhtn')) and any(x in latest for x in ('tru','loai','tinh')):
        return ('Khoản 3 Điều 8 Nghị định 145/2020/NĐ-CP xác định thời gian tính trợ cấp bằng thời gian làm việc thực tế, trừ thời gian tham gia bảo hiểm thất nghiệp theo quy định và thời gian đã được chi trả trợ cấp thôi việc/mất việc. Cần phân biệt con số sau khi trừ này với thời gian làm việc thường xuyên để xét điều kiện.\n\nRiêng trợ cấp mất việc, nếu đủ điều kiện tại Điều 47 Bộ luật Lao động và khoản 2 Điều 8, thời gian tính còn ít hơn 24 tháng vẫn có mức sàn 02 tháng tiền lương. Không tự kết luận mất khoản sàn chỉ vì thời gian sau khi trừ BHTN bằng 0.')
    if comparison:
        return ('Hai khoản này có điều kiện và mức tính khác nhau:\n\n'
            '- **Trợ cấp thôi việc:** theo Điều 46 Bộ luật Lao động, khi đủ điều kiện, mỗi năm làm việc được tính trợ cấp bằng **1/2 tháng tiền lương**. Không lấy mức tối thiểu 02 tháng của trợ cấp mất việc áp sang khoản này.\n'
            '- **Trợ cấp mất việc làm:** theo Điều 47, khi đủ điều kiện, mỗi năm làm việc được tính trợ cấp bằng **01 tháng tiền lương**, nhưng ít nhất **02 tháng tiền lương**.\n\n'
            'Điều 8 Nghị định 145/2020/NĐ-CP hướng dẫn việc xác định điều kiện, thời gian và tiền lương tính hai khoản. Phải phân biệt thời gian làm việc thường xuyên để xét điều kiện với thời gian còn lại sau khi trừ các khoảng theo quy định để tính trợ cấp; không cộng hoặc đổi tên hai khoản chỉ vì hợp đồng chấm dứt.')
    if loss:
        if 'sa thai' in q and 'ky luat' in q:
            return ('Không tự áp dụng mức tối thiểu 02 tháng trợ cấp mất việc cho mọi trường hợp kỷ luật sa thải. Khoản 2 Điều 8 Nghị định 145/2020/NĐ-CP và Điều 47 Bộ luật Lao động gắn khoản này với trường hợp mất việc theo khoản 11 Điều 34, cùng điều kiện thời gian làm việc.\n\n'
                'Bạn cho biết công ty chấm dứt do cơ cấu/kinh tế hay xử lý kỷ luật, và thời gian làm việc thường xuyên? Nếu đang tranh chấp tính hợp pháp của sa thải thì cần phân tích căn cứ và quyền lợi của nhánh đó riêng, chưa kết luận được trợ cấp chỉ từ tên gọi “sa thải”.')
        if months is not None and months<12:
            return (f'Với thời gian làm việc thường xuyên bạn nêu là **{months:g} tháng**, chưa đủ điều kiện **từ đủ 12 tháng** để áp dụng trợ cấp mất việc theo Điều 47 Bộ luật Lao động và khoản 2 Điều 8 Nghị định 145/2020/NĐ-CP. Không thể tự kết luận công ty phải trả tối thiểu 02 tháng theo quy tắc này.\n\n'
                'Đây là điều kiện của khoản trợ cấp mất việc; các khoản lương còn thiếu hoặc quyền lợi ở căn cứ khác cần đối chiếu riêng. Nếu thời gian nêu chưa gồm toàn bộ quá trình làm việc, bạn bổ sung để xác định lại.')
        if counted is not None and months is not None and counted>months:
            return ('Hai mốc thời gian đang không phù hợp: thời gian được tính trợ cấp lớn hơn thời gian làm việc thường xuyên đã nêu. Bạn kiểm lại thời gian làm việc và khoảng tham gia bảo hiểm thất nghiệp/đã được chi trả trợ cấp; mình chưa chốt mức cho hồ sơ có dữ kiện này. Căn cứ khoản 3 Điều 8 Nghị định 145/2020/NĐ-CP và Điều 47 Bộ luật Lao động.')
        opening='Mức tối thiểu là **02 tháng tiền lương**, nếu người lao động thuộc trường hợp được hưởng trợ cấp mất việc.'
        if counted is not None:
            try:factor=salary_months(counted,True)
            except ValueError:return 'Thời gian tính trợ cấp cần là số tháng hợp lý và không âm. Bạn kiểm lại dữ kiện để đối chiếu Điều 8 Nghị định 145/2020/NĐ-CP.'
            opening=f'Nếu đủ điều kiện hưởng và **{counted:g} tháng** là đúng thời gian được tính sau các khoản loại trừ, mức tương ứng là **{factor:g} tháng tiền lương**. Theo khoản 3 Điều 8 Nghị định 145/2020/NĐ-CP, tháng lẻ đến 06 tháng được quy đổi 1/2 năm, trên 06 tháng thành 01 năm; sau đó áp dụng công thức và mức sàn tại Điều 47 Bộ luật Lao động.'
        # A minimum is a floor, not a universal final payment for longer qualifying time.
        if counted is None and any(x in latest for x in ('tinh tien','so tien','bao nhieu tien')):
            opening='Cần xác định điều kiện hưởng, thời gian được tính và cơ sở tiền lương trước khi chốt số tiền. Mức tối thiểu **02 tháng tiền lương** chỉ là sàn của trợ cấp mất việc khi đủ điều kiện.'
        return (opening+'\n\n'
            'Khoản 2 Điều 8 Nghị định 145/2020/NĐ-CP quy định: người lao động làm việc thường xuyên từ đủ 12 tháng trở lên, thuộc trường hợp mất việc theo khoản 11 Điều 34 Bộ luật Lao động, mà thời gian làm việc **để tính trợ cấp mất việc ít hơn 24 tháng**, thì được chi trả ít nhất 02 tháng tiền lương. Vì vậy, phải tách thời gian làm việc thường xuyên với thời gian tính trợ cấp; không lấy thời gian tính dưới 24 tháng để hạ mức sàn này.\n\n'
            'Theo Điều 47, mỗi năm thời gian được tính tương ứng 01 tháng tiền lương, có thể cao hơn mức sàn. Khoản 3 và khoản 5 Điều 8 hướng dẫn trừ thời gian đã tham gia bảo hiểm thất nghiệp/đã được chi trả trợ cấp, quy đổi tháng lẻ và lấy tiền lương bình quân 06 tháng liền kề theo hợp đồng trước khi mất việc. Đây là tiền do người sử dụng lao động chi trả, khác trợ cấp thất nghiệp.\n\n'
            'Nếu áp dụng cho hồ sơ thực tế, cần xác định đúng lý do mất việc, toàn bộ thời gian làm việc, thời gian đã loại trừ và cơ sở lương; chưa thể coi mọi trường hợp nghỉ việc đều đủ điều kiện hưởng khoản này.')
    if severance:
        if months is not None and months<12:
            return f'Với thời gian làm việc thường xuyên **{months:g} tháng**, chưa đủ điều kiện từ đủ 12 tháng của khoản trợ cấp thôi việc theo Điều 46 Bộ luật Lao động và khoản 1 Điều 8 Nghị định 145/2020/NĐ-CP. Các quyền lợi khác cần được đối chiếu riêng; mức sàn 02 tháng của trợ cấp mất việc không áp sang đây.'
        return ('**Không mặc định trợ cấp thôi việc tối thiểu là 02 tháng tiền lương.** Theo Điều 46 Bộ luật Lao động, khi đủ điều kiện, mỗi năm thời gian làm việc được tính trợ cấp bằng **1/2 tháng tiền lương**. Mức sàn 02 tháng là quy tắc của trợ cấp mất việc, không áp chung cho trợ cấp thôi việc.\n\n'
            'Khoản 1 Điều 8 Nghị định 145/2020/NĐ-CP quy định điều kiện làm việc thường xuyên từ đủ 12 tháng và các căn cứ chấm dứt hợp đồng thuộc diện hưởng, cùng các trường hợp loại trừ. Khoản 3 quy định thời gian được tính sau khi trừ khoảng tham gia bảo hiểm thất nghiệp/đã được chi trả trợ cấp; tháng lẻ đến 06 tháng tính 1/2 năm, trên 06 tháng tính 01 năm. Khoản 5 dùng tiền lương bình quân 06 tháng liền kề theo hợp đồng.\n\n'
            'Bạn muốn tính số tiền cho hồ sơ nào thì cần lý do chấm dứt, thời gian làm việc/tham gia bảo hiểm thất nghiệp và cơ sở tiền lương; chưa thể chốt tiền chỉ từ tổng số tháng đã làm.')
    return 'Bạn muốn đối chiếu trợ cấp thôi việc hay trợ cấp mất việc? Hai khoản có điều kiện và công thức riêng theo Điều 46, Điều 47 Bộ luật Lao động và Điều 8 Nghị định 145/2020/NĐ-CP.'
