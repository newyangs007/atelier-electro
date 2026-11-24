"""Make the English homepage from the same template as the Korean one.

Only display text is translated: HTML text nodes and aria-label/placeholder/title/alt attributes, and
single-quoted JS string literals. Literals that are data keys (category names used for matching, form values)
are left alone; their display names are switched at runtime (window.AE_LANG === 'en' block in the template).
"""
import re

D = {
    '가전레이더 홈': 'Gajeon Radar home', '사이트 전체 검색': 'Search the whole site', '검색': 'Search', '언어': 'Language',
    '구독': 'Subscribe', '호수·목차': 'Issue & contents', '호수 선택·과월호': 'Pick an issue · past issues', '숫자': 'Numbers',
    '뉴스': 'News', '신제품': 'Launches', 'MD픽': 'MD picks', '특가': 'Deals', '제품': 'Products',
    '매일 아침 7시 발행': 'Published daily at 7 a.m. KST', '과월호 보기 →': 'Past issues →',
    '카카오톡 등으로 오늘 호 공유하기': "Share today's issue", '카카오톡으로 공유': 'Share',
    '숫자로 보는 오늘': 'Today in numbers', ' · 좌우로 넘겨 보기': ' · swipe or use the arrows', '이전 수치': 'Previous figure', '다음 수치': 'Next figure', '이전 특가': 'Previous deal', '다음 특가': 'Next deal', '자동 넘김 멈춤': 'Pause auto-scroll', '자동 넘김 시작': 'Start auto-scroll', '오늘 호의 핵심 수치와 이번 주 흐름 · 수치마다 출처': "Key figures from today's issue and this week's trends · every figure sourced",
    '오늘의 가전뉴스': "Today's appliance news",
    '중요도 순 · 한국·미국·일본·중국·유럽 · 제목을 누르면 원문으로 가고, 해외 기사는 한국어 번역으로 열립니다 · 핵심 수치는 형광펜 표시': 'By importance · Korea, US, Japan, China, Europe · click a headline to open the original article · key figures highlighted',
    '중요도 순 · 한국·미국·일본·중국·유럽 · 제목을 누르면 기사 원문': 'By importance · Korea, US, Japan, China, Europe · click a headline to open the original article',
    '으로 바로 갑니다': '', '뉴스 범위': 'News range', '오늘 호 · 중요도순': "Today's issue · by importance",
    '지난 뉴스까지 · 날짜순': 'Including past news · by date', '뉴스 전체 페이지 →': 'All news page →', '뉴스 분야': 'News topics',
    '뉴스 페이지': 'News pages', '최근 3개월 주요 브랜드 출시·발표 · 월별로 보기 · 제목을 누르면 출처로 이동': 'Major brand launches of the last 3 months · by month · click a title for the source',
    '출시 월': 'Launch month', '신제품 페이지': 'Launch pages', '오늘의 MD 픽': "Today's MD picks",
    '매일 다른 제품 · 카테고리마다 1개씩 · 쿠팡 파트너스 제휴': 'Different products every day · one per category · Coupang Partners',
    '이전 제품': 'Previous product', '자동 넘김 멈춤': 'Pause auto-advance', '다음 제품': 'Next product',
    '[광고] 쿠팡 버튼은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.': '[Ad] Coupang buttons are Coupang Partners affiliate links; we earn a commission on purchases.',
    'MD 픽 넘기기': 'MD pick slides', '매일 아침 7시, 가전 뉴스·MD 픽을 무료로': 'Appliance news and MD picks, free, every morning at 7',
    '3분이면 읽는 가전 전문 뉴스레터': 'A 3-minute appliance newsletter', '무료 구독하기': 'Subscribe free', '동료에게 보내기': 'Send to a colleague',
    '오늘의 특가': "Today's deals", '30% 이상': '30%+ off',
    '인기 브랜드 제품 중 할인 폭이 큰 6개 · 쿠팡 표시 정가': 'Six popular-brand products with the biggest discounts · vs. Coupang list price',
    '또는 다나와 출시가': 'or Danawa launch price', '대비 30% 이상 · 쿠팡 반품 최상 등급 포함': '30%+ off · includes Coupang returns graded "Best"',
    '카테고리별 제품': 'Products by category', '쿠팡 파트너스 제휴 제품만 · 카테고리가 자동으로 바뀌며 4개씩 보여 드려요': 'Coupang Partners products only · categories rotate automatically, 4 at a time',
    '제품 검색': 'Product search', '제품·브랜드·종류 검색 — 관련 뉴스도 함께': 'Search products, brands, types — related news too',
    '예: TV, 로봇청소기': 'e.g. TV, robot vacuum', '검색어 지우기': 'Clear search', '상위 카테고리': 'Categories',
    '카테고리 자동 넘김 멈춤': 'Pause category rotation', '하위 카테고리': 'Sub-categories', '더 보기': 'More',
    '매일 아침 7시,': 'Every morning at 7,', '가전 뉴스와 MD 픽을 메일로': 'appliance news and MD picks by email',
    '관심 분야에 맞춘 추천템과 핵심 뉴스를 3분 분량으로 보내 드려요. 공동구매·특가 소식은 원하는 분께만.': 'Picks matched to your interests and the key news in a 3-minute read. Group-buy and deal offers only if you opt in.',
    '가전 일 하는 동료에게도 알려 주세요': 'Tell a colleague in the appliance business', '카톡 공유': 'Share',
    '이메일': 'Email', '이메일 주소': 'Email address', '구독하기': 'Subscribe', '선택 항목': 'Optional',
    '성별·나이대·독자 유형·관심 분야': 'gender, age, reader type, interests', '— 맞춤 추천에 쓰여요': '— used for tailored picks',
    '성별': 'Gender', '남성': 'Male', '여성': 'Female', '나이대': 'Age', '선택': 'Select', '10대': 'Teens', '만 14세 이상': '14+',
    '20대': '20s', '30대': '30s', '40대': '40s', '50대': '50s', '60대 이상': '60+', '독자 유형': 'Reader type', '선택 안 함': 'Prefer not to say',
    '가전 관심 소비자': 'Consumer', '유통·MD·바이어': 'Retail / MD / buyer', '제조·브랜드': 'Manufacturer / brand',
    '온라인 셀러·리셀러': 'Online seller', '미디어·크리에이터': 'Media / creator', '기타': 'Other', '관심 분야': 'Interests',
    'AI가전': 'AI appliances', '청소·생활': 'Cleaning & living', '난방·가습': 'Heating & humidifying', '계절가전': 'Seasonal',
    'TV·오디오': 'TV & audio', '모바일·워치': 'Mobile & watch', '모바일·노트북·워치': 'Mobile, laptop & watch', '특가 30%↑': 'Deals 30%+',
    '[필수] 만 14세 이상이며, 개인정보 수집·이용과 뉴스레터 수신에 동의합니다': '[Required] I am 14 or older and agree to the collection and use of my information and to receive the newsletter',
    '수집 항목: 이메일·성별·나이대·독자 유형·관심 분야 · 목적: 매일 아침 뉴스레터 발송': 'Collected: email, gender, age, reader type, interests · Purpose: daily morning newsletter',
    '쿠팡 파트너스 등 제휴 링크 포함': 'includes affiliate links such as Coupang Partners', '맞춤 추천, 독자 통계 · 보유: 구독 해지 시까지': 'tailored picks, reader statistics · Kept until you unsubscribe',
    '해지 즉시 파기': 'deleted immediately on unsubscribe', '. 만 14세 미만은 구독할 수 없습니다.': '. Under-14s cannot subscribe.',
    '[선택] 공동구매·특가·유튜브 쇼핑 영상 등 광고성 정보 수신에 동의합니다': '[Optional] I agree to receive promotional info such as group buys, deals and YouTube shopping videos',
    '동의하지 않아도 뉴스레터는 받을 수 있고, 메일 하단 링크로 언제든 철회할 수 있습니다.': 'You get the newsletter either way and can withdraw anytime via the link in each email.',
    '개인정보처리방침': 'Privacy policy', '자주 묻는 질문': 'FAQ', '출처 전체 보기': 'All sources', '점수 기준': 'How we score',
    '수요·검증': 'Demand, proof', '리뷰': 'reviews', '·타이밍·접근성': ', timing, access', '소싱': 'sourcing',
    '·마진을 1~5점으로 매기고 평균을 0.5 단위로 반올림합니다. 4.0 이상 추천템, 3.5 조건부, 3.0 이하 관망. 가격·리뷰·순위는 다나와 인기상품순': ' and margin are scored 1–5 and averaged to the nearest 0.5: 4.0+ top pick, 3.5 conditional, 3.0 or below watch. Prices, reviews and ranks follow Danawa popularity',
    '광고 제외': 'ads excluded', '수집 시점 기준이며 판매처마다 다를 수 있습니다.': 'as collected and may differ by seller.',
    '브랜드 정보': 'Brands', '· 매일 아침 7시 가전 트렌드와 추천템': '· Appliance trends and picks every morning at 7',
    '뉴스 전체': 'All news', '신제품 전체': 'All launches', '과월호': 'Past issues', '브랜드': 'Brands', '구독 해지': 'Unsubscribe',
    '비즈니스 협업 환영 :': 'Business inquiries:', '카카오톡으로 오늘 호 공유': "Share today's issue", '공유': 'Share', '맨 위로': 'Back to top',
    '호수 선택 · 과월호': 'Pick an issue · past issues', '닫기': 'Close', '← 이전 호': '← Previous', '최신 호': 'Latest', '다음 호 →': 'Next →',
    '보기 방식': 'View', '일별': 'Daily', '주차별': 'Weekly', '월별': 'Monthly', '연도별': 'Yearly', '날짜로 찾기': 'Find by date',
    '과월호 전체 페이지 열기 ↗': 'Open the full archive ↗', '뉴스·제품·브랜드·신제품·지난 호 전체 검색': 'Search news, products, brands, launches and past issues',
    '검색어': 'Search term', '제품 상세': 'Product details', '추천템': 'Top pick', '조건부': 'Conditional', '관망': 'Watch',
    '쿠팡에서 가격 보기 ↗': 'See price on Coupang ↗', '상세 보기': 'Details', 'MD 추천': 'MD pick', '쿠팡': 'Coupang',
    '수요': 'Demand', '검증': 'Proof', '타이밍': 'Timing', '접근성': 'Access', '마진': 'Margin',
    '한국': 'Korea', '미국': 'US', '일본': 'Japan', '중국': 'China', '유럽': 'Europe', '독일': 'Germany', '이탈리아': 'Italy', '영국': 'UK',
    '스위스': 'Switzerland', '호주': 'Australia', '인도': 'India', '싱가포르': 'Singapore', '프랑스': 'France', '전체': 'All',
    'IT·모바일': 'IT & mobile', '디바이스': 'Devices', '소형': 'Small', '소형가전': 'Small appliances', '대형': 'Large',
    '스마트폰·태블릿': 'Phones & tablets', '워치·웨어러블': 'Watches & wearables', '주방가전': 'Kitchen', '뷰티·미용기기': 'Beauty devices',
    '청소·로봇': 'Cleaning & robots', '이어폰·헤드폰': 'Earbuds & headphones', '계절·생활': 'Seasonal & living',
    '관련 뉴스': 'Related news', '원문 ↗': 'Article ↗', '상세': 'Details', '상세 정보': 'Details', '번째:': ':',
    '카테고리 자동 넘김 시작': 'Resume category rotation', '바로가기 ↗': '↗', '관련 기사 ·': 'Related ·', '종류': 'Type',
    '’ 전체 카테고리 검색 결과': '’ — results in all categories', '개 · 점수 높은 순': ' · by score',
    '’에 맞는 쿠팡 제휴 제품은 아직 없어요.': '’ — no Coupang Partners products yet.', '관련 뉴스를 먼저 보여 드려요.': 'Here is related news instead.',
    '전체 보기': 'See all', '이전 페이지': 'Previous page', '다음 페이지': 'Next page', '주요': 'Key', '특가 −': 'Deal −',
    '추천 이유': 'Why', '추천 대상': 'For', '차별점': 'Standout', '신호': 'Signal', '· 평점': '· rating', '쿠팡에서 보기': 'View on Coupang',
    '제품 페이지': 'Product page', '다나와 ↗': 'Danawa ↗', '소싱 점수': 'Sourcing score', '[가전레이더 MD 픽]': '[Gajeon Radar MD pick]',
    '지난 호 뉴스를 불러오는 중…': 'Loading past news…', '호 남음': ' more issues', '주차 ·': ' week ·', '지난 호': 'Past issue',
    '를 보고 있어요. 가격·순위는 그날 기준입니다.': ' — prices and ranks are as of that day.', '최신 호로': 'Go to latest', '다른 호 보기': 'Other issues',
    '호를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.': "Couldn't load the issue. Please try again shortly.",
    '에는 발행된 호가 없어 가장 가까운 지난 호': ' has no issue; opening the closest earlier issue', '를 엽니다.': '.',
    '그 날짜 이전에는 발행된 호가 없어요. 첫 호는': 'No issue before that date. The first issue is', '입니다.': '.',
    '집계 준비 중': 'Coming soon', '구독자': 'subscribers', '누적 방문자': 'visitors', '기준': 'as of', '광고': 'Ad',
    '메일 앱이 열리면 그대로 보내 주세요. 접수되면 구독 완료 메일을 보내 드리고, 다음 날 아침 7시부터 발송합니다.': 'Send the email that opens. Once received, we will confirm and start the next morning at 7.',
    '이메일 주소를 확인해 주세요.': 'Please check your email address.', '[필수] 항목에 동의해 주세요.': 'Please agree to the required item.',
    '구독 신청이 완료됐어요. 몇 분 안에 구독 완료 메일과 오늘 호를 보내 드리고, 내일부터 매일 아침 7시에 도착합니다.': "You're subscribed. A confirmation and today's issue arrive within minutes, then every morning at 7 a.m. KST.",
    '제품명·브랜드·뉴스 키워드로 찾아보세요. 지난 호 뉴스까지 함께 찾습니다.': 'Search by product, brand or news keyword — past issues included.',
    '쿠팡 제휴': 'Coupang Partners', '· 오늘 제휴 제품': "· today's products", '제품 보기': 'View products', '열기': 'Open',
    '’에 맞는 내용이 없어요. 다른 낱말로 찾아보세요.': '’ — nothing found. Try another word.', '자동 넘김 시작': 'Resume auto-advance',
    '링크 복사됨 — 카톡 대화창에 붙여 넣기': 'Link copied — paste it in a chat', '링크를 복사해 카카오톡에 붙여 넣으세요': 'Copy the link and paste it in a chat',
    '가전 업계 소식을 매일 아침 3분으로 — 가전레이더 무료 구독': 'Appliance industry news in 3 minutes every morning — subscribe to Gajeon Radar free',
    '(출처)': '', '(선택)': '(optional)', '(리뷰)': ' (reviews)', '(소싱)': ' (sourcing)',
    '제품명': 'Product', '구독 신청': 'Subscription', '호': '', '개': '', '건': '', '명': '', '년 ': '.', '월': '', '일월화수목금토': 'SMTWTFS',
}
# 데이터 값(카테고리 이름, 폼 값)이라 그대로 둠 — 화면 이름은 런타임에서 바꿈
PROTECT = {'주방', '청소', '로봇', '뷰티', '워치', '이어폰', '오디오', '스마트폰', '태블릿', '노트북', '대형가전', 'AI디바이스', 'TV',
           '난방', '가습', '계절', '생활', '동의', '미동의', '스마트링', '에어프라이어', '음식물처리기', '밥솥', '블렌더·두유제조기', '스팀오븐·찜기',
           '로봇청소기', '무선청소기', '히터', '가습기', '헤어드라이어', '뷰티디바이스', '세탁·건조기', 'AI 녹음기', 'AI 안경', '무선 이어폰',
           '헤드폰', '스피커', '스마트워치', '김치냉장고', '냉장고', 'QLED·미니LED TV', '폴더블폰', 'LG전자', '삼성전자', '가전레이더',
           '디바이스', '소형', '대형', 'AI', 'IT', '갤럭시', '아이폰', '정가', '출시가'}
# HTML 글자(관심 분야 칩 등)에만 쓰는 번역
HD = dict(D, **{'주방': 'Kitchen', '청소': 'Cleaning', '뷰티': 'Beauty', 'AI디바이스': 'AI devices', '대형가전': 'Large appliances',
                '가전레이더': 'GAJEON RADAR', '로봇': 'Robots', '스마트폰': 'Smartphones'})
SHORT = 2  # 2자 이하 항목은 리터럴 전체가 같을 때만 바꿈
_keys = sorted(D, key=len, reverse=True)
_hkeys = None


def _sub(text, dic=None):
    dic = dic or D
    if text in dic:
        return dic[text]
    out = text
    for k in (_hkeys if dic is HD else _keys):
        if len(k) <= SHORT:
            continue
        if k in out:
            out = out.replace(k, dic[k])
    return out


def _html_part(h):
    global _hkeys
    if _hkeys is None:
        _hkeys = sorted(HD, key=len, reverse=True)
    h = re.sub(r'>([^<>]*[가-힣][^<>]*)<', lambda m: '>' + _ws(m.group(1)) + '<', h)
    h = re.sub(r'\b(aria-label|placeholder|title|alt)="([^"]*[가-힣][^"]*)"', lambda m: '%s="%s"' % (m.group(1), _sub(m.group(2).strip(), HD)), h)
    return h


def _ws(s):
    a = len(s) - len(s.lstrip()); b = len(s.rstrip())
    return s[:a] + _sub(s.strip(), HD) + s[b:]


def _js_part(js):
    def lit(m):
        c = m.group(1)
        if not re.search('[가-힣]', c) or c in PROTECT:
            return m.group(0)
        return "'" + _sub(c).replace("'", "\\'") + "'"
    return re.sub(r"'((?:[^'\\\n]|\\.)*)'", lit, js)


def translate(t):
    head_end = t.index('</head>')
    head, body = t[:head_end], t[head_end:]
    parts = re.split(r'(<script\b[^>]*>.*?</script>)', body, flags=re.S)
    out = []
    for p in parts:
        if p.startswith('<script'):
            if 'application/json' in p[:80] or 'ld+json' in p[:80]:
                out.append(p)
            else:
                out.append(_js_part(p))
        else:
            out.append(_html_part(p))
    return head + ''.join(out)
