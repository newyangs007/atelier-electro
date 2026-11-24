"""Build the daily newsletter email (3-minute read).
Usage: python3 <tools|build>/email.py issues/YYYY-MM-DD.json [--to EMAIL] [--interests "AI디바이스,주방"]
Writes out/email.html and out/email.txt and prints JSON {subject, preheader, images:[thumb paths in cid order]}.
- Product photo, name and button link to the Coupang Partners link (cp); without cp they link to the product page.
- Unsubscribe link carries the recipient address when --to is given.
"""
import json, re, sys, html, os, argparse
from urllib.parse import quote

SITE = "https://newyangs007.github.io/atelier-electro/"
_T = "tools" if os.path.exists("tools/config.json") else "build"
SND = (json.load(open(_T + "/config.json", encoding="utf-8")) if os.path.exists(_T + "/config.json") else {}).get("sender", {})
ap = argparse.ArgumentParser()
ap.add_argument('issue')
ap.add_argument('--to', default='')
ap.add_argument('--interests', default='')
a = ap.parse_args()

j = json.load(open(a.issue, encoding="utf-8"))
ed = j["edition"]
strip = lambda s: re.sub("<[^>]+>", "", s)
e = html.escape
os.makedirs("out/thumbs", exist_ok=True)


def score(p):
    return round(sum(p["sc"]) / 5 * 2) / 2


def slug(p):
    if p.get('pc'):
        return 'p/%s.html' % p['pc']
    base = re.sub(r'[^a-z0-9]+', '-', (p.get('q') or '').lower()).strip('-')
    if len(base) < 4:
        base = re.sub(r'[^a-z0-9]+', '-', p['name'].lower()).strip('-')
    return 'p/%s.html' % (base or p['id'])


CATMAP = {"AI가전": lambda p: p.get("ai") and p["cat"] != "AI디바이스", "AI디바이스": lambda p: p["cat"] == "AI디바이스",
          "주방": lambda p: p["cat"] == "주방", "청소": lambda p: p["cat"] in ("청소", "생활"),
          "난방·가습": lambda p: p["cat"] in ("난방", "가습", "계절"), "뷰티": lambda p: p["cat"] == "뷰티",
          "대형가전": lambda p: p["cat"] == "대형가전",
          "TV·오디오": lambda p: p["cat"] in ("TV", "오디오", "이어폰"),
          "모바일·워치": lambda p: p["cat"] in ("스마트폰", "태블릿", "워치", "노트북"),
          "특가": lambda p: (p.get("dc") or 0) >= 30}
ints = [x.strip() for x in a.interests.split(",") if x.strip() in CATMAP]
picks = sorted(j["picks"], key=lambda p: -score(p))
if any(p.get("cp") for p in picks):  # 메일에는 쿠팡 링크가 연결된 제품만
    picks = [p for p in picks if p.get("cp")]
# 추천템은 매일 바뀌게: 어제 추천템 3은 뒤로, 오늘 추천템 3(build.py 가 계산)은 앞으로
_prev = set(j.get("prev_top3") or [])
_t3 = j.get("top3") or []
picks = sorted(picks, key=lambda p: (p["id"] in _prev, _t3.index(p["id"]) if p["id"] in _t3 else 9))
chosen = []
if ints:  # round-robin over interests (조건부 이상) until 3, then general picks
    pools = [[p for p in picks if CATMAP[it](p) and score(p) >= 3.5 and p["id"] not in _prev] for it in ints]
    while len(chosen) < 3 and any(pools):
        for pool in pools:
            while pool and pool[0] in chosen:
                pool.pop(0)
            if pool and len(chosen) < 3:
                chosen.append(pool.pop(0))
for p in picks:
    if len(chosen) >= 3: break
    if p not in chosen: chosen.append(p)
chosen = chosen[:3]
matched = {id(p) for p in chosen if ints and any(CATMAP[i](p) for i in ints)}

imgs = []


def thumb(path):
    from PIL import Image
    name = "out/thumbs/" + os.path.basename(path)
    if not os.path.exists(name):
        im = Image.open(path).convert("RGB")
        im.thumbnail((240, 240))
        im.save(name, "JPEG", quality=82, optimize=True)
    return os.path.abspath(name)


def card(p):
    href = p.get("cp") or SITE + slug(p)
    a0 = '<a href="%s" target="_blank" style="color:#111111;text-decoration:none">' % e(href)
    img = ""
    if p.get("img") and os.path.exists(p["img"]):
        cid = "att%d" % len(imgs)
        imgs.append(thumb(p["img"]))
        img = ('<td width="104" valign="top" style="padding-right:14px">%s<img src="cid:%s" width="104" height="104" alt="%s" '
               'style="display:block;width:104px;height:104px;background-color:#ffffff;border:1px solid #dddddd;border-radius:8px"></a></td>' % (a0, cid, e(p["name"])))
    # bulletproof button: Gmail removes the CSS 'background' shorthand, so the colour sits on the table cell (bgcolor) as well
    btn = ('<table role="presentation" cellpadding="0" cellspacing="0" style="margin-top:12px"><tr><td bgcolor="#e0301e" style="background-color:#e0301e;border-radius:8px">'
           '<a href="%s" target="_blank" style="display:inline-block;padding:11px 18px;border:2px solid #e0301e;border-radius:8px;background-color:#e0301e;'
           'color:#ffffff;text-decoration:none;font-size:14px;font-weight:700">%s &rarr;</a></td></tr></table>') % (e(href), "쿠팡에서 가격 보기" if p.get("cp") else "자세히 보기")
    tag = ' · 관심 분야 맞춤' if id(p) in matched else ''
    v = score(p)
    vd = "추천템" if v >= 4 else ("조건부" if v >= 3.5 else "관망")
    return ('<tr><td style="padding:18px 0;border-top:1px solid #e5e5e5"><table role="presentation" cellpadding="0" cellspacing="0" width="100%%"><tr>%s'
            '<td valign="top"><div style="font-size:12px;font-weight:700;color:#b42318">%s · ★ %.1f %s%s</div>'
            '<div style="font-size:17px;font-weight:700;color:#111111;margin:5px 0 4px;line-height:1.4">%s%s</a></div>'
            '<div style="font-size:18px;font-weight:800;color:#111111">%s</div>'
            '<div style="font-size:14px;color:#333333;line-height:1.6;margin-top:6px">%s</div>%s</td></tr></table></td></tr>'
            % (img, e(p["brand"]), v, vd, tag, a0, e(p["name"]), e(p["price"]), e(p["why"]), btn))


def sec(title, eyebrow, rows):
    return ('<tr><td style="padding:26px 24px 4px"><div style="font-size:12px;font-weight:800;letter-spacing:.08em;color:#e0301e">%s</div>'
            '<div style="font-size:22px;font-weight:800;color:#111111;margin:4px 0 6px;letter-spacing:-.02em">%s</div>'
            '<table role="presentation" cellpadding="0" cellspacing="0" width="100%%">%s</table></td></tr>' % (eyebrow, title, rows))


order = {"AI": 0, "TV": 1, "IT": 2, "로봇": 3, "디바이스": 4, "소형": 5, "대형": 6}
pts = sorted([n for n in j["news"] if n.get("pt")], key=lambda n: (-(n.get("imp") or 0), order.get(n["c"], 9)))
news3 = pts[:5]  # 중요도(imp) 순 상위 5
REGK = {"KR": "한국", "US": "미국", "JP": "일본", "CN": "중국", "EU": "유럽"}
CAT = {"AI": "AI가전", "TV": "TV", "IT": "IT·모바일", "로봇": "로봇", "디바이스": "AI디바이스", "소형": "소형가전", "대형": "대형가전"}
SRC = j["sources"]
def nlink(n):
    S = SRC.get(n["s"])
    return S["u"] if S else SITE
def nmedia(n):
    S = SRC.get(n["s"])
    return (S["t"].split(",")[0][:30]) if S else "출처"
news_rows = "".join(
    '<tr><td style="padding:14px 0;border-top:1px solid #e5e5e5"><div style="font-size:12px;font-weight:700;color:#b42318">%s · %s</div>'
    '<div style="font-size:16px;font-weight:700;color:#111111;margin-top:4px;line-height:1.45"><a href="%s" target="_blank" style="color:#111111;text-decoration:none">%s</a></div><div style="font-size:14px;color:#333333;line-height:1.6;margin-top:4px">%s</div>'
    '<a href="%s" target="_blank" style="display:inline-block;margin-top:6px;font-size:13px;font-weight:700;color:#e0301e;text-decoration:none">%s 원문 바로가기 &rarr;</a></td></tr>'
    % (e(CAT.get(n["c"], n["c"])), e(REGK.get(n["r"], n["r"])), e(nlink(n)), e(n["h"]), e(n["p"]), e(nlink(n)), e(nmedia(n))) for n in news3)

# 더 많은 쿠팡 제휴 제품: 추천템과 겹치지 않게 카테고리마다 1개씩, 사진 있는 것만 최대 4개 (LG전자·삼성전자 먼저)
def upper(p):
    c = p["cat"]
    if c == "TV": return "TV"
    if c == "대형가전": return "대형"
    if c == "주방": return "주방"
    if c in ("청소", "로봇") or p.get("icon") == "robot": return "청소"
    if c in ("난방", "가습", "계절", "생활"): return "계절"
    if c == "뷰티": return "뷰티"
    if c in ("스마트폰", "태블릿", "노트북", "워치"): return "모바일"
    if c in ("이어폰", "오디오"): return "오디오"
    return c
more, seen_up = [], {upper(p) for p in chosen}
for p in sorted(picks, key=lambda p: (p["brand"] not in ("LG전자", "삼성전자"), -score(p))):
    if len(more) >= 4: break
    if p in chosen or not p.get("img") or not os.path.exists(p["img"]) or upper(p) in seen_up: continue
    seen_up.add(upper(p)); more.append(p)


def mini(p):
    href = p.get("cp") or SITE + slug(p)
    cid = "att%d" % len(imgs)
    imgs.append(thumb(p["img"]))
    return ('<td width="50%%" valign="top" style="padding:12px 6px;border-top:1px solid #e5e5e5">'
            '<a href="%s" target="_blank" style="text-decoration:none;color:#111111"><img src="cid:%s" width="120" height="120" alt="%s" '
            'style="display:block;width:120px;height:120px;background-color:#ffffff;border:1px solid #dddddd;border-radius:8px"></a>'
            '<div style="font-size:12px;color:#666666;margin-top:8px">%s</div>'
            '<div style="font-size:14px;font-weight:700;line-height:1.4;margin-top:2px"><a href="%s" target="_blank" style="color:#111111;text-decoration:none">%s</a></div>'
            '<div style="font-size:15px;font-weight:800;margin-top:4px">%s</div>'
            '<a href="%s" target="_blank" style="display:inline-block;margin-top:6px;font-size:13px;font-weight:700;color:#e0301e;text-decoration:none">%s &rarr;</a></td>'
            % (e(href), cid, e(p["name"]), e(p["brand"]), e(href), e(p["name"]), e(p["price"]), e(href), "쿠팡에서 보기" if p.get("cp") else "자세히 보기"))

mail = j.get("mail", {})
tr = next((t for t in j["trends"] if t.get("stat")), None)
hook = mail.get("hook") or (news3[0]["h"] if news3 else strip(j["cover"]["title"]))
pre = mail.get("pre") or ("가전 전문 매거진 가전레이더 · 오늘의 추천: " + " · ".join(p["name"] for p in chosen))[:120]
num = mail.get("num") or tr
title = strip(j["cover"]["title"])
_hs = [k for k in (j["cover"].get("s") or []) if k in SRC] or ([news3[0]["s"]] if news3 and news3[0]["s"] in SRC else [])
hero_u = SRC[_hs[0]]["u"] if _hs else SITE
chosen_html = "".join(card(p) for p in chosen)  # 사진 번호(att0~) 순서를 본문 순서와 맞춤
_rows = "".join("<tr>" + "".join(mini(p) for p in more[i:i + 2]) + ('<td width="50%"></td>' if len(more[i:i + 2]) == 1 else "") + "</tr>" for i in range(0, len(more), 2))
more_html = sec("카테고리별 쿠팡 제휴 제품", "MORE PICKS", _rows) if more else ""
unsub = SITE + "unsubscribe.html" + ("?e=" + quote(a.to) if a.to else "")
no = ed["label"].split(" · ")[1] if " · " in ed["label"] else ed["date"]

body = f'''<!doctype html><html><head><meta charset="utf-8"><meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light"></head><body style="margin:0;background:#f2f2f2">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{e(pre)}&#8199;&#65279;&#847;&#8199;&#65279;&#847;</div>
<table role="presentation" cellpadding="0" cellspacing="0" width="100%" bgcolor="#f2f2f2" style="background:#f2f2f2"><tr><td align="center" style="padding:16px 8px">
<table role="presentation" cellpadding="0" cellspacing="0" width="600" bgcolor="#ffffff" style="max-width:600px;width:100%;table-layout:fixed;word-break:keep-all;overflow-wrap:anywhere;background:#ffffff;font-family:-apple-system,'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',sans-serif;color:#111111;border-top:6px solid #e0301e">
<tr><td style="padding:10px 24px;font-size:12px;line-height:1.5;color:#444444;border-bottom:1px solid #eeeeee">[광고] 이 메일의 쿠팡 링크는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</td></tr>
<tr><td align="center" style="padding:26px 24px 8px;text-align:center">
<div style="font-size:11px;font-weight:700;letter-spacing:.38em;color:#e0301e">THE APPLIANCE MAGAZINE</div>
<div style="font-size:44px;font-weight:900;color:#111111;letter-spacing:-.05em;line-height:1.1;margin-top:10px;white-space:nowrap">가전레이더</div>
<div style="font-size:13px;font-weight:800;letter-spacing:.42em;color:#111111;margin-top:8px;white-space:nowrap">GAJEON RADAR</div>
<div style="font-size:16px;font-weight:600;color:#222222;line-height:1.5;margin-top:14px;white-space:nowrap">가전의 내일을 가장 먼저 읽다</div>
<div style="font-size:12px;font-weight:800;color:#e0301e;margin-top:4px;white-space:nowrap">가전 전문 매거진 · 매일 아침 7시</div>
<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-top:16px;border-top:2px solid #111111;border-bottom:1px solid #111111"><tr>
<td align="left" style="padding:8px 0;font-size:12px;font-weight:800;color:#111111;letter-spacing:.04em">{e(no)}</td>
<td align="center" style="padding:8px 0;font-size:12px;font-weight:700;color:#111111">{e(ed['label'].split(' · ')[0])}</td>
<td align="right" style="padding:8px 0;font-size:12px;font-weight:700;color:#111111">3분 읽기</td></tr></table>
</td></tr>
<tr><td style="padding:14px 24px 4px">
<div style="font-size:26px;font-weight:800;line-height:1.35;color:#111111;letter-spacing:-.03em"><a href="{e(hero_u)}" target="_blank" style="color:#111111;text-decoration:none">{e(title)}</a></div>
<a href="{e(hero_u)}" target="_blank" style="display:inline-block;margin-top:8px;font-size:13px;font-weight:700;color:#e0301e;text-decoration:none">출처 바로가기 &rarr;</a>
{('<table role="presentation" cellpadding="0" cellspacing="0" width="100%%" style="margin-top:16px"><tr><td bgcolor="#fff1ef" style="background:#fff1ef;border-left:5px solid #e0301e;padding:14px 16px"><span style="font-size:32px;font-weight:900;color:#e0301e">%s</span><br><span style="font-size:14px;font-weight:600;color:#222222">%s</span></td></tr></table>' % (e(num["stat"]), e(num["sl"]))) if num else ''}
</td></tr>
{sec("오늘의 가전뉴스 5", "POINT NEWS", news_rows)}
{sec("오늘의 추천템 3", "가전레이더 MD PICK", chosen_html)}
{more_html}
<tr><td style="padding:22px 24px 28px"><a href="{SITE}" style="display:block;text-align:center;padding:15px;border:2px solid #111111;border-radius:10px;background-color:#ffffff;color:#111111;text-decoration:none;font-size:15px;font-weight:800">가전 전문 매거진 가전레이더에서 전체 보기 &rarr;</a>
<div style="font-size:13px;color:#555555;text-align:center;margin-top:8px">제품 리스트 · 오늘의 특가 30%↑ · 신제품 · 모든 출처</div></td></tr>
<tr><td style="padding:0 24px 24px"><table role="presentation" cellpadding="0" cellspacing="0" width="100%"><tr><td bgcolor="#fff7cc" style="background-color:#fff7cc;border-radius:12px;padding:16px 18px;text-align:center">
<div style="font-size:15px;font-weight:800;color:#111111">가전 일 하는 동료에게도 알려 주세요</div>
<div style="font-size:13px;color:#444444;margin:4px 0 10px">이 메일을 전달하거나, 아래 버튼을 눌러 카카오톡·메일·문자로 추천해 주세요.</div>
<a href="{SITE}recommend.html" style="display:inline-block;padding:10px 16px;border-radius:8px;background-color:#111111;color:#ffffff;text-decoration:none;font-size:14px;font-weight:700">동료에게 추천하기 &rarr;</a>
</td></tr></table></td></tr>
<tr><td style="padding:18px 24px 26px;border-top:1px solid #e5e5e5;font-size:12px;line-height:1.75;color:#555555">
가격은 수집 시점({e(ed.get("collected", ""))}) 공개 자료 기준이며 판매처마다 다를 수 있습니다. 모든 수치의 출처는 홈페이지 ‘출처’ 섹션에 있습니다.<br>
전송자: {e(SND.get("name") or "가전레이더")} · <a href="mailto:{e(SND.get("email") or "newyangs007@gmail.com")}" style="color:#555555">{e(SND.get("email") or "newyangs007@gmail.com")}</a>{(" · " + e(SND["phone"])) if SND.get("phone") else ""}{(" · " + e(SND["addr"])) if SND.get("addr") else ""}<br>
더 이상 받지 않으려면 <a href="{e(unsub)}" style="color:#555555">수신 거부(구독 해지)</a>를 누르세요. 수신 거부에 비용이 들지 않습니다.<br>
If you no longer wish to receive this email, click <a href="{e(unsub)}" style="color:#555555">Unsubscribe</a>. Unsubscribing is free of charge.<br>{e(ed.get("next", ""))}</td></tr>
</table></td></tr></table></body></html>'''

txt = "가전레이더 GAJEON RADAR\n가전의 내일을 가장 먼저 읽다 · 가전 전문 매거진\n%s · 3분 읽기\n%s\n\n오늘의 가전뉴스 5\n%s\n\n오늘의 추천템 3\n%s\n\n홈페이지: %s\n\n[광고] 쿠팡 링크는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.\n수신 거부(구독 해지) / Unsubscribe: %s\n전송자: %s" % (
    ed["label"], title,
    "\n".join("- %s %s" % (n["h"], nlink(n)) for n in news3),
    "\n".join("- %s %s (★%.1f) %s" % (p["name"], p["price"], score(p), p.get("cp") or SITE + slug(p)) for p in chosen + more), SITE, unsub, " · ".join(x for x in [SND.get("name") or "가전레이더", SND.get("email") or "newyangs007@gmail.com", SND.get("phone", ""), SND.get("addr", "")] if x))
open("out/email.html", "w", encoding="utf-8").write(body)
open("out/email.txt", "w", encoding="utf-8").write(txt)
miss = [k for k in ("phone", "addr") if not SND.get(k)]
print(json.dumps({"subject": "(광고) [가전레이더 %s] %s" % (no, hook), "preheader": pre, "images": imgs,
                  "warn": ("config.sender에 %s가 비어 있습니다(정보통신망법 시행령 별표 6: 전송자 명칭·이메일·전화번호·주소 표시)" % ", ".join(miss)) if miss else ""}, ensure_ascii=False))
