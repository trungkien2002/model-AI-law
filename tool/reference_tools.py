"""Source-backed rule lookup, distinct from model generation or a verdict on a dispute."""
from rag import norm

def answer(plan):
    intent=plan['intent'];q=norm(plan['latest_question'])
    if intent=='documents':
        holding=any(x in q for x in ('giu','thu giu','ban chinh','van bang','ho chieu','chung chi','bang dai hoc'))
        deposit='dat coc' in q or 'bao dam' in q
        rules=[]
        if holding:rules.append('giữ bản chính giấy tờ tùy thân, văn bằng hoặc chứng chỉ của người lao động')
        if deposit:rules.append('buộc người lao động bảo đảm bằng tiền hoặc tài sản cho việc thực hiện hợp đồng lao động')
        if not rules:return None
        opening='Theo Điều 17 Bộ luật Lao động, người sử dụng lao động **không được** '+ '; '.join(rules)+'. Đây là quy định chung; việc xác định hành vi thực tế cần đối chiếu hồ sơ.'
        ids={x['chunk_id'] for x in plan['sources']}
        if 'ND283:D15' in ids:
            return (opening+'\n\nNếu hành vi thuộc thời kỳ áp dụng **Nghị định 283/2026/NĐ-CP, có hiệu lực từ 10/09/2026**, khoản 2 Điều 15 quy định mức phạt **20–25 triệu đồng đối với cá nhân** cho hành vi tương ứng. Tổ chức thuộc Điều 7 chịu mức **40–50 triệu đồng**; hộ kinh doanh xử phạt như cá nhân. Không tự cộng hai mức thành tổng phạt khi chưa xác định từng hành vi.\n\n'
                'Khoản 3 Điều 15 còn quy định trả lại bản chính đã giữ; đối với khoản tiền hoặc tài sản bảo đảm đã giữ thì phải trả lại, kèm tiền lãi theo căn cứ quy định.\n\n'
                'Bạn cho biết hành vi xảy ra khi nào, đã kết thúc hay còn tiếp diễn? Điều 67 có quy tắc chuyển tiếp: hành vi xảy ra và kết thúc trước ngày hiệu lực có thể thuộc văn bản tại thời điểm thực hiện, còn hành vi vẫn diễn ra khi văn bản mới có hiệu lực được xử lý theo quy định chuyển tiếp. Vì vậy chưa chốt mức phạt áp dụng cho vụ việc khi thiếu thời điểm.')
        if 'ND12:D9' in ids:
            return (opening+'\n\nBạn đang hỏi bối cảnh Nghị định 12/2022/NĐ-CP: khoản 2 Điều 9 ghi mức 20–25 triệu đồng cho các hành vi này. Nguồn lịch sử hiện chưa đủ quy tắc chủ thể để chốt mức áp dụng cho một tổ chức; không dùng Điều 7 của Nghị định 283/2026 để tự nhân đôi cho hành vi cũ.\n\n'
                'Cần đối chiếu thời điểm hành vi kết thúc hay còn tiếp diễn theo Điều 67 Nghị định 283/2026/NĐ-CP. Phần mức phạt của vụ việc chưa được xác nhận; phần cấm giữ bản chính/bảo đảm bằng tài sản theo Điều 17 vẫn phải được xem riêng.')
        return opening+' Bạn có thể yêu cầu đối chiếu việc trả lại giấy tờ hoặc khoản đã giữ, lưu hợp đồng và thông tin giao nhận để làm rõ.'
    if intent=='termination':
        facts=norm(plan['retrieval_query'])
        if not any(x in facts for x in ('xac dinh thoi han','khong xac dinh thoi han','vo thoi han','thay doi co cau','vi ly do kinh te','tai co cau','quyet dinh sa thai')):
            return ('Mình chưa thể kết luận chỉ từ lời kể “layoff không lý do”. Cần phân biệt **thay đổi cơ cấu/công nghệ hoặc lý do kinh tế** theo Điều 42 Bộ luật Lao động với **đơn phương chấm dứt** của công ty theo Điều 36; hai nhánh có điều kiện và cách xử lý khác nhau.\n\n'
                'Bạn đang làm theo loại hợp đồng nào, còn thời hạn không? Công ty thông báo lý do, hình thức và ngày nghỉ ra sao, có báo trước không?\n\n'
                'Trước mắt: giữ hợp đồng, bảng lương, thông báo và tin nhắn; yêu cầu công ty giải thích căn cứ bằng thông tin có thể lưu lại; đối chiếu các khoản chưa thanh toán theo Điều 48. Khi có các dữ kiện trên, mình có thể phân tích nhánh phù hợp và bước yêu cầu giải quyết tiếp theo. Chưa nên mặc định mọi layoff đều hợp pháp hoặc trái pháp luật.')
    if intent=='disciplinary_procedure' and not any(x in q for x in ('mang thai','thai san','dung hay sai','trai luat','co hop le','trong truong hop toi')):
        return ('Theo điểm a khoản 2 Điều 70 Nghị định 145/2020/NĐ-CP, phải thông báo **ít nhất 05 ngày làm việc** trước cuộc họp. Thông báo cần nêu nội dung, thời gian, địa điểm, người bị xử lý và hành vi vi phạm; bảo đảm các thành phần nhận được trước cuộc họp. Quy định này nói “thông báo”, không tự đặt thêm một yêu cầu hình thức văn bản ngoài căn cứ đã đối chiếu.\n\n'
            'Các thành phần theo điểm b, c khoản 1 Điều 122 Bộ luật Lao động gồm tổ chức đại diện người lao động tại cơ sở mà người bị xử lý là thành viên và người lao động. Người lao động có quyền tự bào chữa, nhờ luật sư hoặc tổ chức đại diện bào chữa; nếu chưa đủ 15 tuổi thì có người đại diện theo pháp luật tham gia.\n\n'
            'Theo điểm b, c khoản 2 Điều 70, có thủ tục xác nhận/đổi lịch; khi đã thông báo theo quy định mà thành phần không xác nhận hoặc vắng mặt, người sử dụng lao động vẫn có thể tiến hành họp. Đây là quy tắc thủ tục chung, chưa xác nhận căn cứ sa thải hoặc điều kiện xử lý một người cụ thể.')
    if intent=='contract_compare':
        return ('Khác biệt chính là có ấn định thời điểm kết thúc hay không:\n\n'
            '- **Hợp đồng xác định thời hạn:** hai bên xác định thời hạn và thời điểm chấm dứt, tối đa **36 tháng** kể từ ngày hợp đồng có hiệu lực.\n'
            '- **Hợp đồng không xác định thời hạn:** hai bên không ấn định thời hạn và thời điểm chấm dứt hiệu lực. Điều này không có nghĩa hợp đồng không thể chấm dứt.\n\n'
            'Căn cứ khoản 1 Điều 20 Bộ luật Lao động. Khi đánh giá việc gia hạn, báo trước hoặc cho nghỉ việc, cần đối chiếu thêm điều kiện riêng của tình huống; không suy các hệ quả đó chỉ từ tên loại hợp đồng.')
    if intent=='lactation' and not any(x in q for x in ('xu phat','muc phat','phat bao nhieu')):
        return ('Ngưỡng bắt buộc là **từ 1.000 lao động nữ trở lên**: người sử dụng lao động phải lắp đặt phòng vắt, trữ sữa mẹ tại nơi làm việc, theo khoản 5 Điều 80 Nghị định 145/2020/NĐ-CP.\n\n'
            'Dưới ngưỡng đó, quy định khuyến khích lắp đặt phù hợp điều kiện thực tế, nhu cầu của lao động nữ và khả năng của người sử dụng lao động. Đây là số lao động nữ, không phải tổng số lao động; đúng 1.000 đã thuộc ngưỡng bắt buộc.')
    return None
