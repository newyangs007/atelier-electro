"""Build the magazine: index.html (+ product pages, sitemap, robots).
Run from the site root. Works with either tools/ (GitHub repo) or build/ (local) layout.
"""
import json, re, glob, os, html, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import static as ST

T = 'tools' if os.path.exists('tools/template.html') else 'build'
SITE = 'https://newyangs007.github.io/atelier-electro/'
e = html.escape
strip = lambda s: re.sub('<[^>]+>', '', s)

issues = []
FULL = {}
for f in sorted(glob.glob('issues/*.json')):
    j = json.load(open(f, encoding='utf-8'))
    FULL[j['edition']['date']] = j
    issues.append({"date": j['edition']['date'], "no": j['edition']['no'], "title": strip(j['cover']['title'])})
issues.sort(key=lambda a: a['date'], reverse=True)
latest = json.load(open('issues/%s.json' % issues[0]['date'], encoding='utf-8'))
prev = json.load(open('issues/%s.json' % issues[1]['date'], encoding='utf-8')) if len(issues) > 1 else None

# ---- 제품: 쿠팡 파트너스 링크가 있는 제품만 노출, 같은 제품 중복 제거 ----
_seen, _picks = set(), []
for _p in latest['picks']:
    _k = (_p.get('pc') or re.sub(r'\s+', '', _p['name']).lower())
    if not _p.get('cp') or _k in _seen:
        continue
    _seen.add(_k); _picks.append(_p)
latest['picks'] = _picks


# ---- MD 픽 롤링: 카테고리마다 1개씩 8개, 날짜마다 다른 제품, 어제 MD 픽은 되도록 제외 ----
def _sc(p):
    v = sum(p['sc']) / len(p['sc']); return round(v * 2) / 2


def upper(p):
    c = p.get('cat', '')
    if c == 'TV': return 'tv'
    if c in ('스마트폰', '태블릿', '노트북'): return 'mobile'
    if c == '워치': return 'wear'
    if c in ('이어폰', '오디오'): return 'audio'
    if c == '주방': return 'kitchen'
    if c in ('청소', '로봇') or p.get('icon') == 'robot': return 'clean'
    if c == '뷰티': return 'beauty'
    if c == '대형가전': return 'big'
    if c in ('난방', '가습', '계절', '생활'): return 'season'
    if c == 'AI디바이스': return 'aidev'
    return 'etc'


MD_ORDER = ['tv', 'mobile', 'wear', 'kitchen', 'beauty', 'clean', 'big', 'audio', 'season', 'aidev']


def _md(issue, exclude):
    import datetime
    day = datetime.date.fromisoformat(issue['edition']['date']).toordinal()
    ok = [p for p in issue['picks'] if p.get('cp') and p.get('img') and str(p.get('price', '')).endswith('원')]
    G = {}
    for p in ok:
        G.setdefault(upper(p), []).append(p)
    def pick(cat, pref=None):
        L = G.get(cat) or []
        if pref:
            L = [p for p in L if pref(p)] or L
        if not L:
            return None
        # 가격이 괜찮은 제품(정가 대비 20% 이상 할인) 먼저, 그다음 점수 순
        L = sorted(L, key=lambda p: (-(1 if (p.get('dc') or 0) >= 20 or _pct(p) >= 20 else 0), -_sc(p), p['id']))
        fresh = [p for p in L if p['id'] not in exclude] or L
        return fresh[day % len(fresh)]['id']
    out = []
    for cat, pref in (('kitchen', lambda p: p.get('sub') == '음식물처리기'), ('beauty', lambda p: p.get('brand') == '에이피알')):
        x = pick(cat, pref)
        if x: out.append((cat, x))
    rot = MD_ORDER[day % len(MD_ORDER):] + MD_ORDER[:day % len(MD_ORDER)]
    for cat in rot:
        if len(out) >= 8: break
        if cat in dict(out): continue
        x = pick(cat)
        if x: out.append((cat, x))
    order = {c: i for i, c in enumerate(MD_ORDER)}
    return [x for _, x in sorted(out, key=lambda t: order.get(t[0], 99))]


def _pct(p):
    m = re.search(r'([\d,]+)\s*원', p.get('why', ''))
    m2 = re.search(r'정가 ([\d,]+)원 대비 (\d+)%', p.get('why', ''))
    return int(m2.group(2)) if m2 else 0


_prev_md = (prev.get('md') or prev.get('top3') or []) if prev else []
_md_ids = _md(latest, set(_prev_md))
_t3 = _md_ids[:3]
if latest.get('md') != _md_ids or latest.get('prev_md') != _prev_md or latest.get('top3') != _t3:
    _raw = json.load(open('issues/%s.json' % issues[0]['date'], encoding='utf-8'))
    _raw['md'], _raw['prev_md'], _raw['top3'], _raw['prev_top3'] = _md_ids, _prev_md, _t3, _prev_md[:3]
    json.dump(_raw, open('issues/%s.json' % issues[0]['date'], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
latest['md'], latest['prev_md'], latest['top3'], latest['prev_top3'] = _md_ids, _prev_md, _t3, _prev_md[:3]


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
        # 전일 대비는 어제도 쿠팡 링크가 있던 제품(같은 가격 기준)만 표시
        if q is not None and q.get('cp') and a is not None and b is not None and a != b:
            p['pd'] = ('▼' if a < b else '▲') + format(abs(a - b), ',') + '원 (전일 대비)'

cfg = json.load(open(T + '/config.json', encoding='utf-8')) if os.path.exists(T + '/config.json') else {}
dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
t = open(T + '/template.html', encoding='utf-8').read()
t = t.replace('/*__BRANDS__*/', open(T + '/brands.json', encoding='utf-8').read())
t = t.replace('/*__ICONS__*/', open(T + '/icons.txt', encoding='utf-8').read())
t = t.replace('/*__ARCHIVE__*/', dump(issues)).replace('/*__ISSUE__*/', dump(latest))
ADS = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=%s"\n     crossorigin="anonymous"></script>' % cfg['ads']['client']) if (cfg.get('ads') or {}).get('client') else ''
ST.ADS_HEAD = ADS
BCSS = ('body{margin:0;font-family:-apple-system,"Apple SD Gothic Neo","Noto Sans KR",sans-serif;color:#111;background:#fafafa;word-break:keep-all;line-height:1.6}'
        '.top{position:sticky;top:0;z-index:5;background:#000;color:#fff}.w{max-width:860px;margin:0 auto;padding:0 16px}'
        '.top .w{display:flex;align-items:center;gap:14px;height:52px}.top a{color:#fff;text-decoration:none}.logo{font-weight:900;font-size:20px;flex:1}'
        '.bc{font-size:13px;color:#666;margin:16px 0 0}.bc a{color:#666}h1{font-size:26px;margin:8px 0 4px}h1 small,h2 small{font-weight:500;color:#888;font-size:.6em;margin-left:6px}'
        '.lead{color:#444;margin:0 0 16px}h2{font-size:19px;border-bottom:2px solid #111;padding-bottom:6px;margin:26px 0 10px}'
        'ul{list-style:none;margin:0;padding:0}.pl li a{display:flex;gap:12px;align-items:center;background:#fff;border:1px solid #e5e5e5;border-radius:12px;padding:10px;margin-bottom:8px;color:#111;text-decoration:none}'
        '.pl .im{flex:none;width:84px;height:84px;display:flex;align-items:center;justify-content:center}.pl img{max-width:84px;max-height:84px;object-fit:contain}'
        '.pl .tx{display:flex;flex-direction:column;gap:2px;min-width:0}.pl b{font-size:15px}.pl .pr{font-weight:800}.pl .mt{font-size:12.5px;color:#666}'
        '.nl li{background:#fff;border:1px solid #e5e5e5;border-radius:12px;padding:12px;margin-bottom:8px}.nl p{margin:4px 0;font-size:14px;color:#333}.nl small{color:#777}.nl a{color:#777}'
        '.bl{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px}.bl a{display:flex;flex-direction:column;background:#fff;border:1px solid #e5e5e5;border-radius:12px;padding:12px;color:#111;text-decoration:none}'
        '.bl span{font-size:12.5px;color:#666}.bl em{font-style:normal;font-size:12.5px;color:#e0301e;font-weight:700}'
        '.note{font-size:12.5px;color:#777;margin:18px 0}footer{padding:28px 16px;color:#777;font-size:12px}')
t = t.replace('<!--__VERIFY__-->', ADS + '\n' + '\n'.join(cfg.get('verify', [])) + '\n<script>window.AE_FORM=%s;window.AE_STATS=%s;window.AE_ADS=%s;</script>' % (dump(cfg.get('form')), dump(cfg.get('stats')), dump(cfg.get('ads'))))
t = t.replace('<!--__JSONLD__-->', ST.jsonld_index(latest))
t = t.replace('<!--__FAQ__-->', ST.faq_html(ST.faq(latest, 'ko')))
t = ST.inject(t, ST.ssr_index(latest))
open('index.html', 'w', encoding='utf-8').write(t)

# ---- product pages ----
os.makedirs('p', exist_ok=True)
# 쿠팡 링크가 빠진 제품의 지난 페이지는 지움(검색에 구매 버튼 없는 페이지가 남지 않게)
_live = {p['page'] for p in latest['picks']}
for _f in glob.glob('p/*.html'):
    if _f not in _live:
        os.remove(_f)
S = latest['sources']
BR = json.load(open(T + '/brands.json', encoding='utf-8'))
LBL = ['수요', '검증', '타이밍', '접근성', '마진']


def score(sc):
    return round(sum(sc) / len(sc) * 2) / 2


PAGE = open(T + '/product.html', encoding='utf-8').read()
urls = [SITE, SITE + 'privacy.html']
for p in latest['picks']:
    v = score(p['sc'])
    verdict = '추천템' if v >= 4 else ('조건부' if v >= 3.5 else '관망')
    src = ''.join('<li><a href="%s" target="_blank" rel="noopener">%s</a></li>' % (e(S[s]['u']), e(S[s]['t'])) for s in p.get('src', []) if s in S)
    rows = ''.join('<tr><th>%s</th><td class="n">%d</td><td>%s</td></tr>' % (LBL[i], x, e((p.get('scw') or [''] * 5)[i])) for i, x in enumerate(p['sc']))
    img = ('../' + p['img']) if p.get('img') else ''
    buy = ('<a class="cp" href="%s" target="_blank" rel="noopener sponsored">쿠팡에서 가격 보기 ↗</a>' % e(p['cp'])) if p.get('cp') else ''
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
        '{{DISC}}': '이 페이지의 ‘쿠팡에서 가격 보기’ 링크는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.' if p.get('cp') else '',
        '{{EDITION}}': e(latest['edition']['label']), '{{DESC}}': e(p['why'] + ' ' + p['usp'])[:160],
        '{{JSONLD}}': ST.jsonld_product(p, latest),
        '{{ADS}}': ADS,
    }.items():
        out = out.replace(k, val)
    if p.get('cp'):  # 모바일 하단 고정 구매 바: 가격과 쿠팡 버튼이 항상 보이게
        out = out.replace('</body>', '<div class="stk" role="complementary" aria-label="쿠팡 가격 보기"><div><b>%s</b><small>%s 기준</small></div><a class="cp" href="%s" target="_blank" rel="noopener sponsored">쿠팡에서 가격 보기 ↗</a></div>'
                          '<style>.stk{display:none}@media(max-width:759px){.stk{position:fixed;left:0;right:0;bottom:0;z-index:20;display:flex;align-items:center;gap:12px;justify-content:space-between;background:#fff;border-top:1px solid #ddd;padding:10px 16px calc(10px + env(safe-area-inset-bottom))}'
                          '.stk b{display:block;font-size:17px}.stk small{font-size:12px;color:#666}.stk a{flex:none;background:#e0301e;color:#fff;font-weight:700;text-decoration:none;padding:12px 16px;border-radius:10px;font-size:14px}body{padding-bottom:72px}}</style></body>'
                          % (e(p['price']), e(latest['edition']['date'].replace('-', '.')), e(p['cp'])), 1)
    open(p['page'], 'w', encoding='utf-8').write(out)
    urls.append(SITE + p['page'])

# ---- 브랜드별 페이지(b/<brand>.html): 브랜드 정보 + 그 브랜드 제품 + 관련 뉴스 ----
ENB = (latest.get('en') or {}).get('brands', {})


def bslug(b):
    x = re.sub(r'[^a-z0-9]+', '-', (ENB.get(b) or b).lower()).strip('-')
    return 'b/%s.html' % (x or ('brand-%d' % (abs(hash(b)) % 10000)))


os.makedirs('b', exist_ok=True)
for _f in glob.glob('b/*.html'):
    os.remove(_f)
_by = {}
for p in latest['picks']:
    _by.setdefault(p['brand'], []).append(p)
BRAND_PAGES = {}
for b, ps in sorted(_by.items(), key=lambda kv: -len(kv[1])):
    path = bslug(b)
    BRAND_PAGES[b] = path
    ps = sorted(ps, key=lambda p: -score(p['sc']))
    info = BR.get(b, {})
    short = re.sub(r'(전자|생활)$', '', b)
    keys = {b, short, ENB.get(b, b)}
    NOT = {'모바': '모바일', '메타': '메타버스'}

    def hit(k, t):
        return k and k in t and not (k in NOT and t.count(k) == t.count(NOT[k]))
    news = [n for n in latest['news'] if any(hit(k, n['h'] + ' ' + n['p']) for k in keys)][:8]
    cats = sorted({p['cat'] for p in ps})
    cards = ''.join(
        '<li><a href="../%s"><span class="im">%s</span><span class="tx"><b>%s</b><span class="pr">%s</span><span class="mt">%s · %s · 소싱 점수 %.1f</span></span></a></li>' % (
            e(p['page']), ('<img src="../%s" alt="%s" loading="lazy">' % (e(p['img']), e(p['name']))) if p.get('img') else '', e(p['name']), e(p['price']),
            e(p['cat']), e(p['ch']), score(p['sc'])) for p in ps)
    nws = ''.join('<li><b>%s</b><p>%s</p><small>%s · %s</small></li>' % (e(n['h']), e(n['p']), e(n.get('d', '')),
                  ', '.join('<a href="%s" target="_blank" rel="noopener">%s</a>' % (e(S[x]['u']), e(S[x]['t'].split(',')[0])) for x in ([n['s']] if isinstance(n.get('s'), str) else n.get('s', [])) if x in S)) for n in news)
    title = '%s 가전·IT 추천 %d종 가격 비교 · %s | 가전레이더' % (b, len(ps), latest['edition']['date'].replace('-', '.'))
    desc = '%s(%s) %s 추천 제품 %d종의 오늘 최저가·다나와 순위·소싱 점수를 정리했습니다. %s' % (b, ENB.get(b, b), '·'.join(cats), len(ps), (info.get('f') or ''))
    url = SITE + path
    ldo = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', 'name': title, 'url': url, 'description': desc[:300], 'inLanguage': 'ko-KR',
         'about': {'@type': 'Brand', 'name': b, 'alternateName': ENB.get(b, b)},
         'isPartOf': {'@id': SITE + '#website'}},
        {'@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': SITE + p['page'], 'name': p['name']} for i, p in enumerate(ps)]},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': '가전레이더', 'item': SITE},
            {'@type': 'ListItem', 'position': 2, 'name': '브랜드', 'item': SITE + 'brands.html'},
            {'@type': 'ListItem', 'position': 3, 'name': b, 'item': url}]}]}
    html_ = ('<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
             '<title>%s</title><meta name="description" content="%s"><link rel="canonical" href="%s"><link rel="icon" href="../favicon.svg">'
             '<meta property="og:type" content="website"><meta property="og:title" content="%s"><meta property="og:description" content="%s"><meta property="og:url" content="%s"><meta property="og:image" content="%s">%s'
             '<script type="application/ld+json">%s</script><style>%s</style></head><body>'
             '<header class="top"><div class="w"><a class="logo" href="../">가전레이더</a><a href="../brands.html">브랜드</a><a href="../archive.html">과월호</a></div></header>'
             '<main class="w"><nav class="bc"><a href="../">홈</a> › <a href="../brands.html">브랜드</a> › %s</nav><h1>%s <small>%s</small></h1>'
             '<p class="lead">%s</p><h2>추천 제품 %d종 <small>%s 기준</small></h2><ul class="pl">%s</ul>%s'
             '<p class="note">가격·순위는 %s 다나와 공개 자료 기준이며 판매처마다 다를 수 있습니다. 각 제품 페이지에 출처가 있습니다.</p></main>'
             '<footer class="w">가전레이더 GAJEON RADAR · 가전 전문 매거진 · 매일 아침 7시</footer></body></html>') % (
        e(title), e(desc[:160]), url, e(title), e(desc[:160]), url, e(SITE + (ps[0].get('img') or 'og.png')), ADS,
        json.dumps(ldo, ensure_ascii=False).replace('</', '<\\/'), BCSS,
        e(b), e(b), e(ENB.get(b, '')) if ENB.get(b, b) != b else '',
        e(' · '.join(x for x in [info.get('c', ''), info.get('f', ''), ('대표 제품: ' + info['p']) if info.get('p') else ''] if x) or '브랜드 정보 확인 중'),
        len(ps), e(latest['edition']['label']), cards,
        ('<h2>관련 뉴스</h2><ul class="nl">%s</ul>' % nws) if nws else '', e(latest['edition']['date']))
    open(path, 'w', encoding='utf-8').write(html_)
    urls.append(url)
# 브랜드 목록
_bl = ''.join('<li><a href="%s"><b>%s</b><span>%s</span><em>%d종</em></a></li>' % (e(BRAND_PAGES[b]), e(b), e(ENB.get(b, '') if ENB.get(b, b) != b else BR.get(b, {}).get('c', '')), len(_by[b]))
              for b in sorted(_by, key=lambda x: (-len(_by[x]), x)))
open('brands.html', 'w', encoding='utf-8').write(
    ('<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
     '<title>브랜드별 가전·IT 추천 모아 보기 | 가전레이더</title><meta name="description" content="삼성전자·LG전자·애플·다이슨 등 %d개 브랜드의 추천 가전·IT 제품을 브랜드별로 모아 봅니다.">'
     '<link rel="canonical" href="%sbrands.html"><link rel="icon" href="favicon.svg">%s<style>%s</style></head><body>'
     '<header class="top"><div class="w"><a class="logo" href="./">가전레이더</a><a href="brands.html">브랜드</a><a href="archive.html">과월호</a></div></header>'
     '<main class="w"><h1>브랜드별 모아 보기</h1><p class="lead">%s 기준 %d개 브랜드 · 제품 %d종</p><ul class="bl">%s</ul></main>'
     '<footer class="w">가전레이더 GAJEON RADAR · 가전 전문 매거진</footer></body></html>') % (len(_by), SITE, ADS, BCSS.replace('../', ''), e(latest['edition']['label']), len(_by), len(latest['picks']), _bl))
_bld = {'@context': 'https://schema.org', '@graph': [
    {'@type': 'CollectionPage', 'name': '브랜드별 모아 보기 · 가전레이더', 'url': SITE + 'brands.html', 'inLanguage': 'ko-KR'},
    {'@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': SITE + BRAND_PAGES[b], 'name': b} for i, b in enumerate(sorted(_by, key=lambda x: (-len(_by[x]), x)))]}]}
_h = open('brands.html', encoding='utf-8').read().replace('</head>', '<script type="application/ld+json">%s</script></head>' % json.dumps(_bld, ensure_ascii=False).replace('</', '<\\/'), 1)
open('brands.html', 'w', encoding='utf-8').write(_h)
urls.append(SITE + 'brands.html')
# 제품 페이지에 브랜드 페이지 링크
for p in latest['picks']:
    if p['brand'] in BRAND_PAGES:
        h = open(p['page'], encoding='utf-8').read()
        h = h.replace('<p class="eb" style="color:var(--ink-2);margin:10px 0 0">%s · ' % e(p['brand']),
                      '<p class="eb" style="color:var(--ink-2);margin:10px 0 0"><a href="../%s" style="color:inherit">%s 제품 모두 보기 ›</a> · ' % (e(BRAND_PAGES[p['brand']]), e(p['brand'])), 1)
        open(p['page'], 'w', encoding='utf-8').write(h)

today = latest['edition']['date']
# ---- 과월호(archive.html): 연도 → 월 → 주차 → 일 ----
import datetime as _dt
_order = [a['date'] for a in issues]  # newest first
for i, d in enumerate(_order):
    ST.NEIGHBORS[d] = (_order[i + 1] if i + 1 < len(_order) else None, _order[i - 1] if i > 0 else None)
WD = '월화수목금토일'


def week_of(d):
    """한국식 월 주차: 월요일 시작, 그 주의 목요일이 속한 달·순번."""
    t = _dt.date.fromisoformat(d)
    mon = t - _dt.timedelta(days=t.weekday())
    th = mon + _dt.timedelta(days=3)
    first = th.replace(day=1)
    first_thu = first + _dt.timedelta(days=(3 - first.weekday()) % 7)
    return th.year, th.month, (th - first_thu).days // 7 + 1, mon, mon + _dt.timedelta(days=6)


def md(x):
    return '%02d.%02d' % (x.month, x.day)


def archive_html():
    tree = {}
    for a in issues:
        y, m, n, mon, sun = week_of(a['date'])
        tree.setdefault(y, {}).setdefault(m, {}).setdefault((n, mon, sun), []).append(a)
    body = []
    for y in sorted(tree, reverse=True):
        cnt = sum(len(v) for mm in tree[y].values() for v in mm.values())
        body.append('<section class="yr"><h2 id="y%d">%d년 <small>%d호</small></h2>' % (y, y, cnt))
        for m in sorted(tree[y], reverse=True):
            mc = sum(len(v) for v in tree[y][m].values())
            body.append('<details class="mo" open><summary id="m%d-%02d">%d월 <small>%d호</small></summary>' % (y, m, m, mc))
            for (n, mon, sun) in sorted(tree[y][m], key=lambda k: k[1], reverse=True):
                body.append('<div class="wk"><h3>%d주차 <small>%s–%s</small></h3><ul>' % (n, md(mon), md(sun)))
                for a in tree[y][m][(n, mon, sun)]:
                    t = _dt.date.fromisoformat(a['date'])
                    body.append('<li><a href="issue/%s.html"><b>No.%03d</b><span class="d">%s (%s)</span><span class="t">%s</span></a></li>' % (
                        a['date'], a['no'], md(t), WD[t.weekday()], e(a['title'])))
                body.append('</ul></div>')
            body.append('</details>')
        body.append('</section>')
    jump = ''.join('<a href="#m%d-%02d">%d.%02d</a>' % (y, m, y, m) for y in sorted(tree, reverse=True) for m in sorted(tree[y], reverse=True))
    return ('<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>과월호 전체 보기 · 가전레이더 GAJEON RADAR</title><meta name="description" content="가전 전문 매거진 가전레이더의 지난 호를 연도·월·주차·날짜별로 모아 봅니다.">'
            '<link rel="canonical" href="%sarchive.html"><link rel="icon" href="favicon.svg">%s<style>'
            'body{margin:0;font-family:-apple-system,"Apple SD Gothic Neo","Noto Sans KR",sans-serif;color:#111;background:#fafafa;word-break:keep-all}'
            '.top{position:sticky;top:0;z-index:5;background:#000;color:#fff}.w{max-width:820px;margin:0 auto;padding:0 16px}'
            '.top .w{display:flex;align-items:center;gap:12px;height:52px}.top a{color:#fff;text-decoration:none}.logo{font-weight:900;font-size:20px;flex:1}'
            '.jump{position:sticky;top:52px;z-index:4;background:#111}.jump .w{display:flex;gap:6px;overflow-x:auto;height:44px;align-items:center;scrollbar-width:none}'
            '.jump a{color:#fff;text-decoration:none;border:1px solid #444;border-radius:999px;padding:5px 11px;font-size:13px;white-space:nowrap}'
            'h1{font-size:26px;margin:22px 0 4px}.lead{color:#555;margin:0 0 14px;font-size:14px}h2{font-size:22px;border-bottom:2px solid #111;padding-bottom:6px;margin:26px 0 8px}'
            'small{font-weight:500;color:#888;font-size:.7em;margin-left:4px}summary{font-size:18px;font-weight:800;padding:10px 0;cursor:pointer;scroll-margin-top:100px}'
            '.wk h3{font-size:14px;color:#e0301e;margin:8px 0 4px}ul{list-style:none;margin:0 0 6px;padding:0}'
            'li a{display:grid;grid-template-columns:72px 92px 1fr;gap:8px;align-items:baseline;padding:11px 12px;background:#fff;border:1px solid #e5e5e5;border-radius:10px;margin-bottom:6px;color:#111;text-decoration:none}'
            'li a:hover{border-color:#111}.d{color:#666;font-size:13px}.t{font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}'
            '@media(max-width:520px){li a{grid-template-columns:64px 1fr}.t{grid-column:1/-1;white-space:normal}}'
            'footer{padding:30px 0;color:#777;font-size:12px}</style></head><body>'
            '<header class="top"><div class="w"><a class="logo" href="./">가전레이더</a><a href="./">최신 호</a><a href="./#subscribe">구독</a></div></header>'
            '<nav class="jump" aria-label="월별 바로가기"><div class="w">%s</div></nav>'
            '<main class="w"><h1>과월호 전체 보기</h1><p class="lead">가전 전문 매거진 가전레이더 · 전체 %d호 · 연도 → 월 → 주차 → 날짜 순. 주차는 월요일 시작, 목요일이 속한 달 기준입니다.</p>%s</main>'
            '<footer class="w">가전레이더 GAJEON RADAR · 매일 아침 7시 발행</footer></body></html>') % (SITE, ADS, jump, len(issues), ''.join(body))


_ald = {'@context': 'https://schema.org', '@graph': [
    {'@type': 'CollectionPage', 'name': '과월호 전체 보기 · 가전레이더', 'url': SITE + 'archive.html', 'inLanguage': 'ko-KR', 'isPartOf': {'@id': SITE + '#website'}},
    {'@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': SITE + 'issue/%s.html' % a['date'], 'name': 'No.%03d %s' % (a['no'], a['title'])} for i, a in enumerate(issues)]},
    {'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': '가전레이더', 'item': SITE}, {'@type': 'ListItem', 'position': 2, 'name': '과월호', 'item': SITE + 'archive.html'}]}]}
open('archive.html', 'w', encoding='utf-8').write(archive_html().replace('</head>', '<script type="application/ld+json">%s</script></head>' % json.dumps(_ald, ensure_ascii=False).replace('</', '<\\/'), 1))
urls.append(SITE + 'archive.html')
# ---- static issue pages (KO + EN), English home, markdown copies, RSS, llms.txt ----
os.makedirs('issue', exist_ok=True)
os.makedirs('en/issue', exist_ok=True)
pairs = [(SITE, SITE + 'en/')]
for d, j in FULL.items():
    for p in j['picks']:
        p.setdefault('page', slug(p))
    ko_u, en_u = SITE + 'issue/%s.html' % d, SITE + 'en/issue/%s.html' % d
    open('issue/%s.html' % d, 'w', encoding='utf-8').write(ST.page(j, 'ko', '../', ko_u, en_u))
    open('en/issue/%s.html' % d, 'w', encoding='utf-8').write(ST.page(j, 'en', '../../', en_u, ko_u))
    open('issue/%s.md' % d, 'w', encoding='utf-8').write(ST.markdown(j, 'ko'))
    open('en/issue/%s.md' % d, 'w', encoding='utf-8').write(ST.markdown(j, 'en'))
    pairs.append((ko_u, en_u))
open('en/index.html', 'w', encoding='utf-8').write(ST.page(latest, 'en', '../', SITE + 'en/', SITE))
full_sorted = [FULL[a['date']] for a in issues]
open('rss.xml', 'w', encoding='utf-8').write(ST.rss(full_sorted, 'ko'))
open('en/rss.xml', 'w', encoding='utf-8').write(ST.rss(full_sorted, 'en'))
open('llms.txt', 'w', encoding='utf-8').write(ST.llms_txt(latest, issues))
alt = {}
for k, v in pairs:
    alt[k] = (k, v)
    alt[v] = (k, v)
urls = urls + [u for pr in pairs for u in pr if u not in urls]


def sm(u):
    x = '  <url><loc>%s</loc><lastmod>%s</lastmod>' % (u, today)
    if u in alt:
        x += '<xhtml:link rel="alternate" hreflang="ko" href="%s"/><xhtml:link rel="alternate" hreflang="en" href="%s"/>' % alt[u]
    return x + '</url>\n'


open('sitemap.xml', 'w', encoding='utf-8').write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' +
    ''.join(sm(u) for u in urls) + '</urlset>\n')
open('robots.txt', 'w', encoding='utf-8').write('User-agent: *\nAllow: /\nSitemap: %ssitemap.xml\n' % SITE)
print(issues[:1], len(latest['picks']), 'product pages', len(urls), 'urls')

# ---- Apps Script 발송용 메일 템플릿(mail/today.json, mail/welcome.json) ----
import subprocess as _sp, sys as _sys
_sp.run([_sys.executable, 'tools/mailjson.py', 'issues/%s.json' % issues[0]['date']], check=True)
