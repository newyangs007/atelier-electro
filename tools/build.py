"""Build the magazine: index.html (+ product pages, sitemap, robots).
Run from the site root. Works with either tools/ (GitHub repo) or build/ (local) layout.
"""
import json, re, glob, os, html

T = 'tools' if os.path.exists('tools/template.html') else 'build'
SITE = 'https://newyangs007.github.io/atelier-electro/'
e = html.escape
strip = lambda s: re.sub('<[^>]+>', '', s)

issues = []
for f in sorted(glob.glob('issues/*.json')):
    j = json.load(open(f, encoding='utf-8'))
    issues.append({"date": j['edition']['date'], "no": j['edition']['no'], "title": strip(j['cover']['title'])})
issues.sort(key=lambda a: a['date'], reverse=True)
latest = json.load(open('issues/%s.json' % issues[0]['date'], encoding='utf-8'))
prev = json.load(open('issues/%s.json' % issues[1]['date'], encoding='utf-8')) if len(issues) > 1 else None


def won(s):
    m = re.fullmatch(r'\s*([\d,]+)\s*원\s*~?\s*', s or '')
    return int(m.group(1).replace(',', '')) if m else None


def slug(p):
    if p.get('pc'):
        return 'p/%s.html' % p['pc']
    base = re.sub(r'[^a-z0-9]+', '-', (p.get('q') or '').lower()).strip('-')
    if len(base) < 4:
        base = re.sub(r'[^a-z0-9]+', '-', p['name'].lower()).strip('-')
    return 'p/%s.html' % (base or p['id'])


# price change vs previous issue + product page path (added to the embedded copy only)
prevmap = {}
if prev:
    for q in prev['picks']:
        prevmap[q.get('pc') or q['name']] = q
for p in latest['picks']:
    p['page'] = slug(p)
    if prev:
        q = prevmap.get(p.get('pc') or p['name'])
        a, b = won(p.get('price')), won(q.get('price')) if q else None
        if q is None:
            p['pd'] = '신규 편입'
        elif a is not None and b is not None and a != b:
            p['pd'] = ('▼' if a < b else '▲') + format(abs(a - b), ',') + '원 (전일 대비)'

cfg = json.load(open(T + '/config.json', encoding='utf-8')) if os.path.exists(T + '/config.json') else {}
dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
t = open(T + '/template.html', encoding='utf-8').read()
t = t.replace('/*__BRANDS__*/', open(T + '/brands.json', encoding='utf-8').read())
t = t.replace('/*__ICONS__*/', open(T + '/icons.txt', encoding='utf-8').read())
t = t.replace('/*__ARCHIVE__*/', dump(issues)).replace('/*__ISSUE__*/', dump(latest))
t = t.replace('<!--__VERIFY__-->', '\n'.join(cfg.get('verify', [])) + '\n<script>window.AE_FORM=%s;</script>' % dump(cfg.get('form')))
open('index.html', 'w', encoding='utf-8').write(t)

# ---- product pages ----
os.makedirs('p', exist_ok=True)
S = latest['sources']
BR = json.load(open(T + '/brands.json', encoding='utf-8'))
LBL = ['수요', '검증', '타이밍', '접근성', '마진']


def score(sc):
    return round(sum(sc) / len(sc) * 2) / 2


PAGE = open(T + '/product.html', encoding='utf-8').read()
urls = [SITE]
for p in latest['picks']:
    v = score(p['sc'])
    verdict = '추천템' if v >= 4 else ('조건부' if v >= 3.5 else '관망')
    src = ''.join('<li><a href="%s" target="_blank" rel="noopener">%s</a></li>' % (e(S[s]['u']), e(S[s]['t'])) for s in p.get('src', []) if s in S)
    rows = ''.join('<tr><th>%s</th><td class="n">%d</td><td>%s</td></tr>' % (LBL[i], x, e((p.get('scw') or [''] * 5)[i])) for i, x in enumerate(p['sc']))
    img = ('../' + p['img']) if p.get('img') else ''
    buy = ('<a class="cp" href="%s" target="_blank" rel="noopener sponsored">쿠팡에서 구매 ↗</a>' % e(p['cp'])) if p.get('cp') else ''
    dan = ('<a href="https://prod.danawa.com/info/?pcode=%s" target="_blank" rel="noopener">다나와 가격 비교 ↗</a>' % e(p['pc'])) if p.get('pc') else ''
    country = BR.get(p['brand'], {}).get('c', '')
    out = PAGE
    for k, val in {
        '{{TITLE}}': e(p['name']), '{{BRAND}}': e(p['brand']), '{{COUNTRY}}': e(country), '{{CAT}}': e(p['cat']),
        '{{PRICE}}': e(p['price']), '{{PD}}': e(p.get('pd', '')), '{{REV}}': e(str(p.get('rev', '—'))), '{{RATE}}': e(str(p.get('rate', '—'))),
        '{{SCORE}}': '%.1f' % v, '{{VERDICT}}': verdict, '{{WHY}}': e(p['why']), '{{TARGET}}': e(p['target']), '{{USP}}': e(p['usp']),
        '{{SIGNAL}}': e(p['ch'] + ' · 등록 ' + p['reg']), '{{NOTE}}': e(p['note']), '{{ROWS}}': rows, '{{SRC}}': src,
        '{{IMG}}': ('<img src="%s" alt="%s">' % (e(img), e(p['name']))) if img else '',
        '{{IMGC}}': e(p.get('imgc') or ('다나와 등록 이미지' if img else '')), '{{OGIMG}}': e(SITE + p['img']) if p.get('img') else e(SITE + 'og.png'),
        '{{URL}}': e(SITE + p['page']), '{{BUY}}': buy, '{{DANAWA}}': dan,
        '{{DISC}}': '이 페이지의 ‘쿠팡에서 구매’ 링크는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.' if p.get('cp') else '',
        '{{EDITION}}': e(latest['edition']['label']), '{{DESC}}': e(p['why'] + ' ' + p['usp'])[:160],
    }.items():
        out = out.replace(k, val)
    open(p['page'], 'w', encoding='utf-8').write(out)
    urls.append(SITE + p['page'])

today = latest['edition']['date']
open('sitemap.xml', 'w', encoding='utf-8').write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    ''.join('  <url><loc>%s</loc><lastmod>%s</lastmod></url>\n' % (u, today) for u in urls) + '</urlset>\n')
open('robots.txt', 'w', encoding='utf-8').write('User-agent: *\nAllow: /\nSitemap: %ssitemap.xml\n' % SITE)
print(issues[:1], len(urls) - 1, 'product pages')
