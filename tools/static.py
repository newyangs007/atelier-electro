"""Static (no-JS) renderers for 가전레이더: issue pages (KO/EN), SSR fragments for index.html,
JSON-LD, FAQ, RSS, llms.txt and markdown copies. Used by build.py.
Everything here is rendered from the issue JSON, so search engines and AI crawlers that do not run
JavaScript still read the full issue.
"""
import json, re, html

e = html.escape
SITE = 'https://newyangs007.github.io/atelier-electro/'
ADS_HEAD = ''  # set by build.py from tools/config.json
BRAND = {'ko': '가전레이더', 'en': 'Gajeon Radar'}
strip = lambda s: re.sub('<[^>]+>', '', s or '')
LBL = {'ko': ['수요', '검증', '타이밍', '접근성', '마진'], 'en': ['Demand', 'Proof', 'Timing', 'Access', 'Margin']}
REG = {'ko': {'KR': '한국', 'US': '미국', 'JP': '일본', 'CN': '중국', 'EU': '유럽'},
       'en': {'KR': 'Korea', 'US': 'US', 'JP': 'Japan', 'CN': 'China', 'EU': 'Europe'}}
CTRY_EN = {'KR': 'Korea', 'US': 'US', 'JP': 'Japan', 'CN': 'China', 'DE': 'Germany', 'IT': 'Italy', 'GB': 'UK', 'CH': 'Switzerland',
           'AU': 'Australia', 'IN': 'India', 'SG': 'Singapore', 'FR': 'France', 'EU': 'Europe'}
CTRY_KO = {'KR': '한국', 'US': '미국', 'JP': '일본', 'CN': '중국', 'DE': '독일', 'IT': '이탈리아', 'GB': '영국', 'CH': '스위스',
           'AU': '호주', 'IN': '인도', 'SG': '싱가포르', 'FR': '프랑스', 'EU': '유럽'}
NEWSCAT = {'ko': {'AI': 'AI가전', '디바이스': 'AI디바이스', '소형': '소형가전', '대형': '대형가전'},
           'en': {'AI': 'AI appliances', '디바이스': 'AI devices', '소형': 'Small appliances', '대형': 'Major appliances'}}
PICKCAT_EN = {'난방': 'Heating', '가습': 'Humidifiers', '주방': 'Kitchen', '뷰티': 'Beauty', '청소': 'Cleaning',
              'AI디바이스': 'AI devices', '대형가전': 'Major appliances'}


def score(sc):
    return round(sum(sc) / len(sc) * 2) / 2


def verdict(v, L):
    if L == 'en':
        return 'Top pick' if v >= 4 else ('Conditional' if v >= 3.5 else 'Watch')
    return '추천템' if v >= 4 else ('조건부' if v >= 3.5 else '관망')


def en_price(s):
    s = (s or '').strip()
    if not s or s == '—':
        return s or '—'
    if s == '출시 시 확정':
        return 'TBA'
    m = re.fullmatch(r'([\d,]+)\s*원(~?)', s)
    if m:
        return ('from ' if m.group(2) else '') + 'KRW ' + m.group(1)
    m = re.fullmatch(r'(\d+)만\s*~\s*(\d+)만\s*원', s)
    if m:
        return 'KRW %sk–%sk' % (int(m.group(1)) * 10, int(m.group(2)) * 10)
    m = re.fullmatch(r'(\d+)만\s*원', s)
    if m:
        return 'KRW %sM' % (int(m.group(1)) / 100)
    m = re.fullmatch(r'([\d,]+)위안\s*\(예상\)', s)
    if m:
        return 'CNY %s (expected)' % m.group(1)
    m = re.fullmatch(r'([\d,]+)엔(~?)', s)
    if m:
        return ('from ' if m.group(2) else '') + 'JPY ' + m.group(1)
    return s


def tr(issue, L):
    """Return a view of the issue in language L (falls back to Korean when a translation is missing)."""
    en = issue.get('en') or {}
    T = {'cover_title': issue['cover']['title'], 'cover_deck': issue['cover']['deck'],
         'figs': [f['l'] for f in issue['cover']['figs']], 'trends': issue['trends'], 'news': issue['news'],
         'launches': issue['launches'], 'picks': {}, 'brands': {}}
    if L == 'en' and en:
        T['cover_title'] = en.get('cover', {}).get('title', T['cover_title'])
        T['cover_deck'] = en.get('cover', {}).get('deck', T['cover_deck'])
        if len(en.get('cover', {}).get('figs', [])) == len(T['figs']):
            T['figs'] = en['cover']['figs']
        if len(en.get('trends', [])) == len(issue['trends']):
            T['trends'] = [dict(t, **x) for t, x in zip(issue['trends'], en['trends'])]
        if len(en.get('news', [])) == len(issue['news']):
            T['news'] = [dict(n, h=x[0], p=x[1]) for n, x in zip(issue['news'], en['news'])]
        if len(en.get('launches', [])) == len(issue['launches']):
            T['launches'] = [dict(l, cat=x[0], p=x[1], pr=en_price(l.get('pr'))) for l, x in zip(issue['launches'], en['launches'])]
        T['brands'] = en.get('brands', {})
    for p in issue['picks']:
        q = dict(p)
        x = (en.get('picks') or {}).get(p['id']) if L == 'en' else None
        if x:
            q.update(name=x[0], ch=x[1], why=x[2], target=x[3], usp=x[4])
            q['md'] = x[5] if len(x) > 5 else p.get('md')
            q['price'] = en_price(p['price'])
            q['cat'] = PICKCAT_EN.get(p['cat'], p['cat'])
        q['brand_l'] = T['brands'].get(p['brand'], p['brand']) if L == 'en' else p['brand']
        T['picks'][p['id']] = q
    return T


def src_link(S, sid, L):
    s = S.get(sid)
    if not s:
        return ''
    t = s['t']
    media = t.split(',')[0] if ',' in t else (L == 'en' and 'Source' or '출처')
    if 'danawa' in s['u'] and ',' not in t:
        media = 'Danawa' if L == 'en' else '다나와'
    return '<a class="src" href="%s" target="_blank" rel="noopener" title="%s">%s</a>' % (e(s['u']), e(t), e(media[:28]))


def md_select(issue):
    sel = [p for p in issue['picks'] if p.get('md')]
    return sorted(sel, key=lambda p: (-p['sc'][0], -p['sc'][1]))


# ---------------------------------------------------------------- FAQ (shared by index + issue pages + JSON-LD)
def faq(issue, L):
    sel = md_select(issue)
    d = issue['edition']['date']
    if L == 'en':
        en = (issue.get('en') or {}).get('picks', {})
        names = '; '.join('%s (%s, %s)' % (en.get(p['id'], [p['name']])[0], en.get(p['id'], [0, p['ch']])[1], en_price(p['price'])) for p in sel)
        return [
            ('What is Gajeon Radar?', 'Gajeon Radar (가전레이더) is a Korean appliance magazine published every morning at 8:00 KST. It covers AI appliances, AI devices such as AI glasses and AI voice recorders, small appliances and major appliances across Korea, the US, Japan, China and Europe, and every number carries its source and date.'),
            ('How are the picks chosen?', 'Each product is scored 1–5 on demand, proof (reviews), timing, access (sourcing) and margin. The average is rounded to 0.5: 4.0 or higher is a Top pick, 3.5 is Conditional, 3.0 or lower is Watch. Prices, review counts and ranks come from Danawa\'s popularity ranking with ads excluded.'),
            ('What is the AI appliance MD select?', 'AI appliances that meet all four rules: top 5 in their Danawa category, 100+ reviews, a rating of 4.7 or higher, and AI features stated by the manufacturer. Each comes with a one-line MD note.'),
            ('Which AI appliances stand out today?', 'As of %s, the AI appliance MD select is: %s.' % (d, names) if sel else 'There is no AI appliance MD select in this issue.'),
            ('Are the Coupang links ads?', 'Yes. The Coupang links are part of the Coupang Partners program, and the magazine may earn a commission. Products are scored with the same rules whether or not they have a link.'),
            ('How do I get the newsletter?', 'Subscribe on the Korean homepage. The newsletter (in Korean) arrives every morning at 8:00 KST with three picks matched to your interests, and every email has an unsubscribe link.'),
        ]
    names = ', '.join('%s(%s, %s)' % (p['name'], p['ch'].split(' · ')[0], p['price']) for p in sel)
    return [
        ('가전레이더는 어떤 매체인가요?', '가전레이더(GAJEON RADAR)는 매일 아침 8시(한국 시간)에 발행하는 가전 매거진입니다. AI가전, AI 안경·AI 녹음기 같은 AI디바이스, 소형가전, 대형가전을 한국·미국·일본·중국·유럽에 걸쳐 다루고, 모든 수치에 매체와 날짜를 붙입니다.'),
        ('추천템은 어떤 기준으로 고르나요?', '수요·검증(리뷰)·타이밍·접근성·마진 다섯 항목을 1~5점으로 매기고, 평균을 0.5 단위로 반올림합니다. 4.0 이상은 추천템, 3.5는 조건부, 3.0 이하는 관망입니다. 가격·리뷰 수·순위는 다나와 인기상품순(광고 제외) 기준입니다.'),
        ('AI가전 MD 셀렉트는 무엇인가요?', '다나와 카테고리 인기 5위 이내, 리뷰 100건 이상, 평점 4.7 이상, 제조사가 밝힌 AI 기능까지 네 조건을 모두 갖춘 AI가전에 MD 한 줄 코멘트를 붙인 목록입니다.'),
        ('오늘 주목할 AI가전은 무엇인가요?', ('%s 기준 AI가전 MD 셀렉트는 %s입니다.' % (d, names)) if sel else '이번 호에는 AI가전 MD 셀렉트가 없습니다.'),
        ('쿠팡 링크는 광고인가요?', '네. 쿠팡 링크는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다. 링크가 있든 없든 같은 점수 기준으로 고릅니다.'),
        ('뉴스레터는 어떻게 받나요?', '홈페이지 맨 아래 구독 폼에서 신청하면 매일 아침 8시에 관심 분야에 맞춘 추천템 3개와 주요 뉴스를 메일로 보내 드립니다. 모든 메일 하단에 구독 해지 링크가 있습니다.'),
    ]


def faq_html(items):
    return ''.join('<details><summary>%s</summary><p>%s</p></details>' % (e(q), e(a)) for q, a in items)


# ---------------------------------------------------------------- JSON-LD
def ld(obj):
    return '<script type="application/ld+json">%s</script>' % json.dumps(obj, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


ORG = {'@type': 'NewsMediaOrganization', '@id': SITE + '#org', 'name': '가전레이더', 'alternateName': ['GAJEON RADAR', 'Gajeon Radar', 'Atelier Électro'],
       'url': SITE, 'logo': {'@type': 'ImageObject', 'url': SITE + 'logo.png', 'width': 512, 'height': 512},
       'sameAs': ['https://github.com/newyangs007/atelier-electro'], 'email': 'newyangs007@gmail.com'}


def jsonld_index(issue, L='ko'):
    T = tr(issue, L)
    base = SITE if L == 'ko' else SITE + 'en/'
    web = {'@type': 'WebSite', '@id': SITE + '#site', 'name': '가전레이더', 'alternateName': ['GAJEON RADAR', 'Gajeon Radar'], 'url': SITE,
           'inLanguage': ['ko-KR', 'en'], 'publisher': {'@id': SITE + '#org'},
           'description': 'AI가전·AI디바이스·소형가전·대형가전 트렌드와 MD 추천템을 매일 아침 8시에 정리하는 가전 매거진'}
    items = [{'@type': 'ListItem', 'position': i + 1, 'url': SITE + p['page'], 'name': T['picks'][p['id']]['name']} for i, p in enumerate(issue['picks'])]
    lst = {'@type': 'ItemList', 'name': ('오늘의 가전 소싱 픽' if L == 'ko' else "Today's appliance picks") + ' ' + issue['edition']['date'], 'itemListElement': items}
    fq = {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq(issue, L)]}
    return ld({'@context': 'https://schema.org', '@graph': [ORG, web, lst, fq]})


def jsonld_issue(issue, L, url):
    T = tr(issue, L)
    d = issue['edition']['date']
    art = {'@type': 'NewsArticle', 'headline': strip(T['cover_title'])[:110], 'description': T['cover_deck'].replace('\n', ' ')[:300],
           'datePublished': d + 'T08:00:00+09:00', 'dateModified': d + 'T08:00:00+09:00', 'inLanguage': 'ko-KR' if L == 'ko' else 'en',
           'image': [SITE + 'og.png'], 'author': {'@id': SITE + '#org'}, 'publisher': {'@id': SITE + '#org'},
           'mainEntityOfPage': url, 'isAccessibleForFree': True,
           'about': ['AI가전', 'AI디바이스', '소형가전', '대형가전'] if L == 'ko' else ['AI appliances', 'AI devices', 'small appliances', 'major appliances']}
    bc = {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': BRAND[L], 'item': SITE if L == 'ko' else SITE + 'en/'},
        {'@type': 'ListItem', 'position': 2, 'name': d, 'item': url}]}
    return ld({'@context': 'https://schema.org', '@graph': [ORG, art, bc]})


def jsonld_product(p, issue):
    o = {'@context': 'https://schema.org', '@type': 'Product', 'name': p['name'], 'brand': {'@type': 'Brand', 'name': p['brand']},
         'description': p['why'], 'category': p['cat'], 'url': SITE + p['page']}
    if p.get('img'):
        o['image'] = SITE + p['img']
    m = re.fullmatch(r'\s*([\d,]+)\s*원\s*', p.get('price') or '')
    if m:
        o['offers'] = {'@type': 'Offer', 'price': m.group(1).replace(',', ''), 'priceCurrency': 'KRW', 'url': SITE + p['page'],
                       'priceValidUntil': issue['edition']['date']}
    bc = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': '가전레이더', 'item': SITE},
        {'@type': 'ListItem', 'position': 2, 'name': '오늘의 소싱 픽', 'item': SITE + '#picks'},
        {'@type': 'ListItem', 'position': 3, 'name': p['name'], 'item': SITE + p['page']}]}
    return ld(o) + ld(bc)


# ---------------------------------------------------------------- SSR fragments injected into index.html containers
def ssr_index(issue):
    S = issue['sources']
    out = {}
    out['cover-title'] = issue['cover']['title']
    out['cover-deck'] = e(issue['cover']['deck'])
    out['trend-list'] = ''.join('<article class="trend"><div class="rn">%s</div><div class="stat num">%s</div><div class="sl">%s</div><h3>%s</h3><p>%s</p></article>'
                                % (e(t['rn']), e(t['stat']), e(t['sl']), e(t['t']), e(t['line'])) for t in issue['trends'])
    news = sorted(issue['news'], key=lambda n: not n.get('pt'))
    out['wire-list'] = ''.join('<article class="story%s"><div class="meta"><span>%s</span><span class="cat c-%s">%s</span></div><h3>%s</h3><p>%s</p>%s</article>'
                               % (' pt' if n.get('pt') else '', e(REG['ko'].get(n['r'], n['r'])), e(n['c']), e(NEWSCAT['ko'].get(n['c'], n['c'])),
                                  e(n['h']), e(n['p']), src_link(S, n['s'], 'ko')) for n in news)
    out['pick-list'] = ''.join('<a class="pick" href="%s"><span class="vis">%s</span><span class="who">%s · %s</span><h3>%s</h3><span class="row"><span class="price num">%s</span><span class="verdict">%s</span></span></a>'
                               % (e(p['page']), ('<img src="%s" alt="%s" loading="lazy">' % (e(p['img']), e(p['name']))) if p.get('img') else '',
                                  e(p['brand']), e(p['cat']), e(p['name']), e(p['price']), verdict(score(p['sc']), 'ko')) for p in issue['picks'])
    out['ai-select'] = ''.join('<div class="ais"><a class="im" href="%s">%s</a><p class="meta">%s</p><p class="nm">%s</p><p class="mdl">%s</p><p class="pr num">%s</p></div>'
                               % (e(p['page']), ('<img src="%s" alt="%s" loading="lazy">' % (e(p['img']), e(p['name']))) if p.get('img') else '',
                                  e(p['ch']), e(p['name']), e(p['md']), e(p['price'])) for p in md_select(issue))
    return out


def inject(t, frag):
    for k, v in frag.items():
        t, n = re.subn(r'(<(\w+)[^>]*\bid="%s"[^>]*>)(</\2>)' % re.escape(k), lambda m: m.group(1) + v + m.group(3), t, count=1)
        assert n == 1, k
    return t


# ---------------------------------------------------------------- full static issue page (KO / EN)
CSS = '''
:root{--bg:#fff;--ink:#000;--ink2:#555;--rule:#ddd;--acc:#e0301e}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"IBM Plex Sans KR","Apple SD Gothic Neo","Malgun Gothic",system-ui,sans-serif;line-height:1.6;word-break:keep-all}
a{color:inherit}.w{max-width:1180px;margin:0 auto;padding:0 24px}
.top{position:sticky;top:0;z-index:5;background:#000;color:#fff}.top .w{display:flex;gap:18px;align-items:center;height:52px;overflow-x:auto;white-space:nowrap}
.top .logo{font-family:"Archivo","Noto Sans KR",sans-serif;font-weight:900;letter-spacing:-.01em;text-decoration:none;font-size:17px;margin-right:auto}
.top nav a{color:#bbb;text-decoration:none;font-size:13px;margin-left:16px}.top nav a:hover{color:#fff}
.lang{display:flex;border:1px solid #444;font-size:12px}.lang a{color:#aaa;text-decoration:none;padding:4px 10px}.lang a[aria-current]{background:#fff;color:#000}
.band{background:#000;color:#fff;padding:44px 0 56px}
.mast{font-family:"Archivo","Noto Sans KR",sans-serif;font-weight:900;font-stretch:75%;font-size:clamp(52px,11vw,150px);line-height:.86;letter-spacing:-.02em;margin:0;text-transform:uppercase}
.tag{border-top:1px solid #333;margin-top:20px;padding-top:14px;color:#aaa;font-size:13px;display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px 24px}
.tag b{color:#fff;font-weight:500}.intro{color:#bbb;font-size:14px;max-width:760px;margin:18px 0 0}
h1.cover{font-size:clamp(30px,5vw,56px);line-height:1.15;letter-spacing:-.03em;margin:46px 0 12px}h1.cover em{font-style:normal;color:var(--acc)}
.deck{white-space:pre-line;color:#ddd;font-size:17px;max-width:760px}
.figs{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:#333;border:1px solid #333;margin-top:30px}
.fig{background:#000;padding:16px}.fig .v{font-family:"Archivo",sans-serif;font-weight:800;font-size:34px}.fig .l{color:#aaa;font-size:13px}
.fig .src,.story .src,.tr .src{font-size:11.5px;color:inherit;opacity:.65}
section{padding:64px 0 8px}h2{font-size:28px;letter-spacing:-.02em;margin:0 0 6px}.sub{color:var(--ink2);font-size:14px;margin:0 0 26px}
.eyebrow{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.14em;color:var(--acc);text-transform:uppercase}
.trs{display:grid;grid-template-columns:repeat(3,1fr);gap:28px}.tr{border-top:2px solid #000;padding-top:12px}
.tr .st{font-family:"Archivo",sans-serif;font-weight:800;font-size:32px}.tr .sl{font-size:12.5px;color:var(--ink2)}.tr h3{margin:10px 0 4px;font-size:18px}.tr p{margin:0;font-size:14px;color:#333}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:40px 32px}
.card .im{display:block;aspect-ratio:1/1;border:1px solid var(--rule);background:#fff;display:grid;place-items:center}.card .im img{width:84%;height:84%;object-fit:contain}
.card .who{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.08em;color:var(--ink2);margin-top:14px}
.card h3{font-size:18px;line-height:1.4;margin:4px 0 8px}.card p{font-size:13.5px;margin:4px 0;color:#333}
.card .row{display:flex;justify-content:space-between;align-items:center;border-top:1px solid #000;padding-top:10px;margin-top:10px}
.price{font-family:"Archivo",sans-serif;font-weight:700;font-size:20px}.vd{font-size:12px;padding:3px 9px;border:1px solid #000}.vd.go{background:#000;color:#fff}
.btns{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}.btns a{font-size:12.5px;padding:7px 11px;border:1px solid #000;text-decoration:none}.btns a.cp{background:#000;color:#fff}
.md{background:#f4f4f4;padding:8px 10px;font-size:13px!important}
.ais{border:1px solid #000;padding:22px;margin-bottom:40px}.ais .grid{grid-template-columns:repeat(4,minmax(0,1fr));gap:22px}
.story{border-top:1px solid #000;padding:14px 0}.story.pt{border-top-width:4px}.story .meta{font-size:12px;color:var(--ink2);display:flex;gap:10px}.story h3{margin:6px 0 4px;font-size:17px}.story p{margin:0;font-size:14px;color:#333}
.news{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 40px}
table{width:100%;border-collapse:collapse;font-size:13.5px}th,td{text-align:left;padding:9px 8px;border-bottom:1px solid var(--rule);vertical-align:top}th{border-bottom:2px solid #000;font-size:12px}
.tbl{overflow-x:auto}.small{font-size:12px;color:var(--ink2)}
details{border-top:1px solid #000;padding:14px 0}summary{font-weight:600;cursor:pointer}details p{color:#333;font-size:14px}
.cta{background:#000;color:#fff;padding:48px 0;margin-top:64px}.cta a.b{display:inline-block;background:#fff;color:#000;padding:12px 22px;text-decoration:none;font-weight:600;margin-top:10px}
footer{padding:28px 0 60px;font-size:12.5px;color:var(--ink2)}footer a{margin-right:14px}
@media(max-width:860px){.grid,.trs,.figs{grid-template-columns:1fr 1fr}.ais .grid{grid-template-columns:1fr 1fr}.news{grid-template-columns:1fr}.top nav{display:none}}
'''

UI = {
    'ko': dict(nav=[('#trends', '트렌드'), ('#ai', 'AI가전 MD'), ('#picks', '소싱 픽'), ('#news', '뉴스'), ('#launches', '신제품'), ('#sources', '출처')],
               tag='GAJEON RADAR · AI가전 · AI디바이스 · 소형가전 · 대형가전 트렌드 & MD 추천', every='매일 08:00 KST 발행',
               intro='가전레이더는 국내외 가전 뉴스와 신제품, 다나와 인기순위·리뷰로 고른 AI가전·소형가전 MD 추천템을 매일 아침 8시에 정리합니다. 모든 수치에 매체와 날짜를 붙입니다.',
               trends='이번 주의 여섯 단어', ai='AI가전 MD 셀렉트', aisub='선정 기준: 다나와 카테고리 인기 5위 이내 · 리뷰 100건 이상 · 평점 4.7 이상 · 제조사가 밝힌 AI 기능',
               picks='오늘의 소싱 픽', pickssub='[광고] ‘쿠팡에서 구매’ 링크는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.',
               news='AI가전 · AI디바이스 · 소형 · 대형 뉴스', launches='주요 브랜드 신제품', sources='출처', faq='자주 묻는 질문',
               th_l=['시점', '시장', '브랜드', '카테고리', '제품', '가격'], th_s=['No.', '국가', '출처', '원문'],
               buy='쿠팡에서 구매 ↗', detail='상세·점수 근거', danawa='다나와 ↗', target='추천 대상', usp='차별점', score='소싱 점수', rev='리뷰', rate='평점',
               cta='매일 아침 8시, 메일로 받아보기', ctasub='관심 분야에 맞춘 추천템 3개와 주요 뉴스를 한 통으로 보내 드립니다.', ctab='구독하기',
               ctaurl='../#subscribe', home='../', open='열기 ↗', other='English', otherurl='../en/issue/%s.html', edition='호',
               foot='가격·리뷰·순위는 수집 시점 기준이며 판매처마다 다를 수 있습니다.', privacy='개인정보처리방침'),
    'en': dict(nav=[('#trends', 'Trends'), ('#ai', 'AI picks'), ('#picks', 'Picks'), ('#news', 'News'), ('#launches', 'Launches'), ('#sources', 'Sources')],
               tag="GAJEON RADAR · Korea's daily briefing on AI appliances, AI devices, small and major appliances", every='Every day 08:00 KST',
               intro='Gajeon Radar (가전레이더) tracks appliance news and launches across Korea, the US, Japan, China and Europe, and picks AI and small appliances from Danawa popularity ranks and reviews — every morning at 8 AM KST, with a source and date on every number.',
               trends='Six words this week', ai='AI appliance MD select', aisub='Rules: top 5 in the Danawa category · 100+ reviews · rating 4.7+ · AI features stated by the maker',
               picks="Today's sourcing picks", pickssub='[Ad] "Buy on Coupang" links are part of the Coupang Partners program; we may earn a commission. Coupang ships within Korea.',
               news='AI appliances · AI devices · small · major', launches='New launches from major brands', sources='Sources', faq='FAQ',
               th_l=['Date', 'Market', 'Brand', 'Category', 'Product', 'Price'], th_s=['No.', 'Country', 'Source', 'Link'],
               buy='Buy on Coupang ↗', detail='Details (Korean)', danawa='Danawa ↗', target='For', usp='Edge', score='Sourcing score', rev='reviews', rate='rating',
               cta='Get it by email every morning', ctasub='The newsletter is in Korean: three picks matched to your interests plus the key news.', ctab='Subscribe (Korean form)',
               ctaurl='../../#subscribe', home='../', open='Open ↗', other='한국어', otherurl='../../issue/%s.html', edition='Issue',
               foot='Prices, reviews and ranks are as collected and can differ by seller.', privacy='Privacy (Korean)'),
}


def page(issue, L, depth, url, alt_url, canonical=None):
    """depth: path prefix back to site root ('../' or '../../')."""
    T = tr(issue, L)
    U = UI[L]
    S = issue['sources']
    E = issue['edition']
    R = depth
    d = E['date']
    head = ('<!DOCTYPE html><html lang="%s"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            % ('ko' if L == 'ko' else 'en'))
    title = ('%s %s | AI가전·소형가전 트렌드와 MD 추천템 — 가전레이더' % (d, strip(T['cover_title']))) if L == 'ko' else \
        ('%s — %s | Gajeon Radar: Korean AI & small appliance trends' % (strip(T['cover_title']), d))
    desc = T['cover_deck'].replace('\n', ' ')[:150]
    alt_ko = url if L == 'ko' else alt_url
    alt_en = alt_url if L == 'ko' else url
    head += '<title>%s</title><meta name="description" content="%s">' % (e(title), e(desc))
    head += '<link rel="canonical" href="%s"><link rel="alternate" hreflang="ko" href="%s"><link rel="alternate" hreflang="en" href="%s"><link rel="alternate" hreflang="x-default" href="%s">' % (
        e(canonical or url), e(alt_ko), e(alt_en), e(alt_ko))
    head += ('<meta property="og:type" content="article"><meta property="og:title" content="%s"><meta property="og:description" content="%s"><meta property="og:url" content="%s">'
             '<meta property="og:image" content="%sog.png"><meta property="og:site_name" content="가전레이더"><meta property="og:locale" content="%s"><meta name="twitter:card" content="summary_large_image">'
             '<meta property="article:published_time" content="%sT08:00:00+09:00">' % (e(title), e(desc), e(canonical or url), SITE, 'ko_KR' if L == 'ko' else 'en_US', d))
    head += '<link rel="icon" href="%sfavicon.svg" type="image/svg+xml"><link rel="alternate" type="application/rss+xml" title="가전레이더" href="%srss.xml">' % (R, SITE)
    head += '<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&family=IBM+Plex+Sans+KR:wght@400;500;600&family=IBM+Plex+Mono&family=Noto+Sans+KR:wght@900&display=swap" rel="stylesheet">'
    head += ADS_HEAD + '<style>%s</style>%s</head>' % (CSS, jsonld_issue(issue, L, canonical or url))
    nav = ''.join('<a href="%s">%s</a>' % (a, b) for a, b in U['nav'])
    lang = ('<nav class="lang"><a href="%s" %s>한국어</a><a href="%s" %s>EN</a></nav>'
            % ((e(alt_ko), 'aria-current="true"' if L == 'ko' else 'hreflang="ko"', e(alt_en), 'aria-current="true"' if L == 'en' else 'hreflang="en"')))
    body = '<body><header class="top"><div class="w"><a class="logo" href="%s">%s</a><nav>%s</nav>%s</div></header>' % (
        (R if L == 'ko' else R + 'en/'), '가전레이더' if L == 'ko' else 'GAJEON RADAR', nav, lang)
    body += '<div class="band"><div class="w"><p class="mast">%s</p><div class="tag"><span>%s</span><span><b>%s No.%03d · %s</b> · %s</span></div><p class="intro">%s</p>' % (
        '가전레이더' if L == 'ko' else 'Gajeon Radar', e(U['tag']), U['edition'], E['no'], d, e(U['every']), e(U['intro']))
    body += '<h1 class="cover">%s</h1><p class="deck">%s</p><div class="figs">' % (T['cover_title'], e(T['cover_deck']))
    body += ''.join('<div class="fig"><div class="v">%s<small>%s</small></div><div class="l">%s</div>%s</div>' % (
        e(f['v']), e(f['u']), e(T['figs'][i]), ''.join(src_link(S, s, L) for s in f.get('s', []))) for i, f in enumerate(issue['cover']['figs']))
    body += '</div></div></div><main class="w">'
    body += '<section id="trends"><span class="eyebrow">01 · Trends</span><h2>%s</h2><div class="trs">' % U['trends']
    body += ''.join('<article class="tr"><div class="st">%s</div><div class="sl">%s</div><h3>%s</h3><p>%s</p>%s</article>' % (
        e(t['stat']), e(t['sl']), e(t['t']), e(t['line']), ''.join(src_link(S, s, L) for s in t.get('s', []))) for t in T['trends'])
    body += '</div></section>'

    def card(p, md=False):
        q = T['picks'][p['id']]
        v = score(p['sc'])
        img = ('<img src="%s%s" alt="%s" loading="lazy">' % (R, e(p['img']), e(q['name']))) if p.get('img') else ''
        btn = []
        if p.get('cp'):
            btn.append('<a class="cp" href="%s" target="_blank" rel="noopener sponsored">%s</a>' % (e(p['cp']), U['buy']))
        btn.append('<a href="%s%s">%s</a>' % (R, e(p['page']), U['detail']))
        if p.get('pc'):
            btn.append('<a href="https://prod.danawa.com/info/?pcode=%s" target="_blank" rel="noopener">%s</a>' % (e(p['pc']), U['danawa']))
        x = '<article class="card"><a class="im" href="%s%s">%s</a><div class="who">%s · %s · %s</div><h3>%s</h3>' % (
            R, e(p['page']), img, e(q['brand_l']), e(REG[L].get(p['mk'], p['mk'])), e(q['cat']), e(q['name']))
        if md and q.get('md'):
            x += '<p class="md">MD · %s</p>' % e(q['md'])
        x += '<p>%s</p><p class="small">%s · %s %s · %s %s</p>' % (e(q['why']), e(q['ch']), U['rev'], e(str(p.get('rev', '—'))), U['rate'], e(str(p.get('rate', '—'))))
        if not md:
            x += '<p class="small"><b>%s</b> %s<br><b>%s</b> %s</p>' % (U['target'], e(q['target']), U['usp'], e(q['usp']))
        x += '<div class="row"><span class="price">%s</span><span class="vd%s">%s %.1f</span></div><div class="btns">%s</div></article>' % (
            e(q['price']), ' go' if v >= 4 else '', verdict(v, L), v, ''.join(btn))
        return x
    sel = md_select(issue)
    if sel:
        body += '<section id="ai"><div class="ais"><span class="eyebrow">AI · MD select</span><h2>%s</h2><p class="sub">%s</p><div class="grid">%s</div></div></section>' % (
            U['ai'], U['aisub'], ''.join(card(p, True) for p in sel))
    body += '<section id="picks"><span class="eyebrow">02 · Picks</span><h2>%s</h2><p class="sub">%s</p><div class="grid">%s</div></section>' % (
        U['picks'], U['pickssub'], ''.join(card(p) for p in sorted(issue['picks'], key=lambda p: -score(p['sc']))))
    body += '<section id="news"><span class="eyebrow">03 · The Wire</span><h2>%s</h2><div class="news">' % U['news']
    for c in ['AI', '디바이스', '소형', '대형']:
        for n in [n for n in T['news'] if n['c'] == c]:
            body += '<article class="story%s"><div class="meta"><span>%s</span><span>%s</span></div><h3>%s</h3><p>%s</p>%s</article>' % (
                ' pt' if n.get('pt') else '', e(NEWSCAT[L][c]), e(REG[L].get(n['r'], n['r'])), e(n['h']), e(n['p']), src_link(S, n['s'], L))
    body += '</div></section>'
    body += '<section id="launches"><span class="eyebrow">04 · Launches</span><h2>%s</h2><div class="tbl"><table><thead><tr>%s</tr></thead><tbody>' % (
        U['launches'], ''.join('<th>%s</th>' % h for h in U['th_l']))
    body += ''.join('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s %s</td><td>%s</td></tr>' % (
        e(l['d']), e(REG[L].get(l['m'], l['m'])), e(T['brands'].get(l['b'], l['b']) if L == 'en' else l['b']), e(l['cat']), e(l['p']),
        src_link(S, l['s'], L), e(l['pr'])) for l in T['launches'])
    body += '</tbody></table></div></section>'
    body += '<section id="faq"><span class="eyebrow">FAQ</span><h2>%s</h2>%s</section>' % (U['faq'], faq_html(faq(issue, L)))
    body += '<section id="sources"><span class="eyebrow">Sources</span><h2>%s</h2><div class="tbl"><table><thead><tr>%s</tr></thead><tbody>' % (
        U['sources'], ''.join('<th>%s</th>' % h for h in U['th_s']))
    C = CTRY_EN if L == 'en' else CTRY_KO
    body += ''.join('<tr><td>%d</td><td>%s</td><td>%s</td><td><a href="%s" target="_blank" rel="noopener">%s</a></td></tr>' % (
        i + 1, e(C.get(s.get('r', ''), s.get('r', '') or '—')), e(s['t']), e(s['u']), U['open']) for i, (k, s) in enumerate(S.items()))
    body += '</tbody></table></div></section></main>'
    body += '<div class="cta"><div class="w"><h2>%s</h2><p>%s</p><a class="b" href="%s#subscribe">%s</a></div></div>' % (U['cta'], U['ctasub'], R, U['ctab'])
    body += '<footer class="w"><p>%s</p><p><a href="%s">%s</a><a href="%sprivacy.html">%s</a><a href="%srss.xml">RSS</a><a href="%sllms.txt">llms.txt</a></p><p>© 가전레이더 GAJEON RADAR</p></footer></body></html>' % (
        U['foot'], e(alt_en if L == 'ko' else alt_ko), U['other'], R, U['privacy'], R, R)
    return head + body


# ---------------------------------------------------------------- markdown (for llms.txt consumers)
def markdown(issue, L):
    T = tr(issue, L)
    S = issue['sources']
    d = issue['edition']['date']
    o = ['# %s — %s No.%03d (%s)' % ('가전레이더' if L == 'ko' else 'Gajeon Radar', d, issue['edition']['no'], strip(T['cover_title'])), '',
         '> ' + T['cover_deck'].replace('\n', ' '), '']
    o.append('## ' + ('AI가전 MD 셀렉트' if L == 'ko' else 'AI appliance MD select'))
    for p in md_select(issue):
        q = T['picks'][p['id']]
        o.append('- [%s](%s%s) — %s · %s · %s %s/%s · MD: %s' % (q['name'], SITE, p['page'], q['ch'], q['price'], 'reviews' if L == 'en' else '리뷰', p.get('rev'), p.get('rate'), q.get('md') or ''))
    o += ['', '## ' + ('소싱 픽 (점수순)' if L == 'ko' else 'Sourcing picks (by score)')]
    for p in sorted(issue['picks'], key=lambda p: -score(p['sc'])):
        q = T['picks'][p['id']]
        v = score(p['sc'])
        o.append('- [%s](%s%s) — %s %.1f · %s · %s · %s' % (q['name'], SITE, p['page'], verdict(v, L), v, q['price'], q['ch'], q['why']))
    o += ['', '## ' + ('뉴스' if L == 'ko' else 'News')]
    for n in T['news']:
        s = S.get(n['s'], {})
        o.append('- **%s** (%s, %s) %s — [%s](%s)' % (n['h'], NEWSCAT[L].get(n['c'], n['c']), REG[L].get(n['r'], n['r']), n['p'], s.get('t', '')[:60], s.get('u', '')))
    o += ['', '## ' + ('트렌드' if L == 'ko' else 'Trends')]
    for t in T['trends']:
        o.append('- %s: %s (%s) — %s' % (t['t'], t['stat'], t['sl'], t['line']))
    o += ['', '## ' + ('점수 기준' if L == 'ko' else 'Scoring'), faq(issue, L)[1][1], '']
    return '\n'.join(o) + '\n'


def llms_txt(issue, issues):
    d = issue['edition']['date']
    o = ['# 가전레이더 (GAJEON RADAR)', '',
         '> 가전레이더는 AI가전·AI디바이스(AI 안경·AI 녹음기)·소형가전·대형가전 트렌드와 다나와 인기순위·리뷰로 고른 MD 추천템을 매일 아침 8시(KST)에 정리하는 한국어 가전 매거진입니다. '
         'Gajeon Radar is a daily Korean appliance magazine (English edition available) covering AI appliances, AI devices, small and major appliances in Korea, the US, Japan, China and Europe. Every number carries its source and date.',
         '', '- 발행: 매일 08:00 KST · 언어: 한국어(원문), 영어(번역판)',
         '- 점수: 수요·검증·타이밍·접근성·마진 1~5점 평균(0.5 단위), 4.0 이상 추천템 · 3.5 조건부 · 3.0 이하 관망',
         '- 가격·리뷰·순위 출처: 다나와 인기상품순(광고 제외), 해외는 제조사 발표가',
         '- 쿠팡 링크는 쿠팡 파트너스 제휴 링크입니다', '',
         '## 최신 호 / Latest issue',
         '- [%s 한국어판 (Markdown)](%sissue/%s.md): %s' % (d, SITE, d, strip(issue['cover']['title'])),
         '- [%s 한국어판 (HTML)](%sissue/%s.html)' % (d, SITE, d),
         '- [%s English edition (Markdown)](%sen/issue/%s.md)' % (d, SITE, d),
         '- [English homepage](%sen/)' % SITE, '',
         '## AI가전 MD 셀렉트 (%s)' % d]
    for p in md_select(issue):
        o.append('- [%s](%s%s): %s, %s, 리뷰 %s·평점 %s. %s' % (p['name'], SITE, p['page'], p['ch'], p['price'], p.get('rev'), p.get('rate'), p.get('md', '')))
    o += ['', '## 오늘의 추천템 (%s)' % d]
    for p in sorted(issue['picks'], key=lambda p: -score(p['sc'])):
        v = score(p['sc'])
        o.append('- [%s](%s%s): %s %.1f, %s, %s' % (p['name'], SITE, p['page'], verdict(v, 'ko'), v, p['price'], p['ch']))
    o += ['', '## 지난 호 / Archive'] + ['- [%s No.%03d %s](%sissue/%s.html)' % (a['date'], a['no'], a['title'], SITE, a['date']) for a in issues[:30]]
    o += ['', '## Optional', '- [RSS](%srss.xml)' % SITE, '- [Sitemap](%ssitemap.xml)' % SITE, '- [개인정보처리방침](%sprivacy.html)' % SITE, '']
    return '\n'.join(o)


def rss(issues_full, L='ko'):
    base = SITE if L == 'ko' else SITE + 'en/'
    items = []
    for j in issues_full[:30]:
        T = tr(j, L)
        d = j['edition']['date']
        link = (SITE + 'issue/%s.html' if L == 'ko' else SITE + 'en/issue/%s.html') % d
        top = ', '.join(T['picks'][p['id']]['name'] for p in sorted(j['picks'], key=lambda p: -score(p['sc']))[:5])
        desc = T['cover_deck'].replace('\n', ' ') + (' 오늘의 추천템: ' if L == 'ko' else " Today's picks: ") + top
        items.append('<item><title>%s</title><link>%s</link><guid isPermaLink="true">%s</guid><pubDate>%s</pubDate><description>%s</description></item>' % (
            e('%s No.%03d %s' % (d, j['edition']['no'], strip(T['cover_title']))), link, link, rfc822(d), e(desc)))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
            '<title>%s</title><link>%s</link><atom:link href="%srss.xml" rel="self" type="application/rss+xml"/>'
            '<description>%s</description><language>%s</language>%s</channel></rss>\n') % (
        e('가전레이더 — AI가전·소형가전 트렌드와 MD 추천템' if L == 'ko' else 'Gajeon Radar — Korean AI & small appliance trends'), base, base,
        e('AI가전·AI디바이스·소형가전·대형가전 뉴스와 MD 추천템, 매일 아침 8시' if L == 'ko' else 'Daily at 8 AM KST: appliance news, launches and MD picks from Korea'),
        'ko' if L == 'ko' else 'en', ''.join(items))


def rfc822(d):
    import datetime
    t = datetime.datetime.strptime(d, '%Y-%m-%d')
    return t.strftime('%a, %d %b %Y') + ' 08:00:00 +0900'
