"""Separate generated prose from application-owned source links; retain raw in logs."""
import re
from urllib.parse import urlsplit


def remove_generated_urls(text):
    # ASVS V1.2: never render a model-selected URL as a trusted source link.
    cleaned = re.sub(r'\[([^\]\n]+)\]\(https?://[^\s\n]*\)', r'\1', text)
    cleaned = re.sub(r'https?://[^\s<>\]]+', '', cleaned)
    return cleaned.strip()


def source_links(text, sources):
    cited = set(map(int, re.findall(r'Điều\s*(\d+)', text, re.I)))
    links = []
    for s in sources:
        if int(s['article']) not in cited:
            continue
        url = s.get('url', '').split('#')[0]
        parsed = urlsplit(url)
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            continue
        pages = s.get('pdf_pages') or s.get('page_numbers') or []
        page = next((p for p in pages if isinstance(p, int) and p > 0), None)
        if page:
            url += '#page=' + str(page)
        label = 'Điều ' + str(s['article']) + ' — Bộ luật Lao động 2019'
        if page:
            label += ' (trang PDF ' + str(page) + ')'
        links.append({'article': int(s['article']), 'label': label, 'url': url})
    return links


def present(text, links, accepted, reasons, notices=()):
    # Validation details remain in result metadata, logs and the UI status bar.
    parts = []
    parts.append(text or 'Model không sinh được nội dung. Bạn có thể diễn đạt lại câu hỏi.')
    if links:
        parts.append('\n'.join('[' + s['label'] + '](' + s['url'] + ')' for s in links))
    return '\n\n'.join(parts)
