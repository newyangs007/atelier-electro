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
chosen = []
if ints:  # round-robin over interests (조건부 이상) until 3, then general picks
    pools = [[p for p in picks if CATMAP[it](p) and score(p) >= 3.5] for it in ints]
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
               'style="display:block;width:104px;height:104px;object-fit:contain;background:#ffffff;border:1px solid #dddddd;border-radius:8px"></a></td>' % (a0, cid, e(p["name"])))
    btn = ('<a href="%s" target="_blank" style="display:inline-block;margin-top:12px;padding:10px 16px;border:2px solid #e0301e;border-radius:8px;'
           'background:#ffffff;color:#e0301e;text-decoration:none;font-size:14px;font-weight:700">%s &rarr;</a>') % (e(href), "쿠팡에서 보기" if p.get("cp") else "자세히 보기")
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


order = {"AI": 0, "IT": 1, "디바이스": 2, "소형": 3, "대형": 4}
pts = sorted([n for n in j["news"] if n.get("pt")], key=lambda n: order.get(n["c"], 4))
seen, news3 = set(), []
for n in pts:  # spread across fields: one per field first
    if n["c"] not in seen:
        news3.append(n); seen.add(n["c"])
    if len(news3) == 5: break
for n in pts:
    if len(news3) == 5: break
    if n not in news3: news3.append(n)
REGK = {"KR": "한국", "US": "미국", "JP": "일본", "CN": "중국", "EU": "유럽"}
CAT = {"AI": "AI가전", "IT": "IT·모바일", "디바이스": "AI디바이스", "소형": "소형가전", "대형": "대형가전"}
news_rows = "".join(
    '<tr><td style="padding:14px 0;border-top:1px solid #e5e5e5"><div style="font-size:12px;font-weight:700;color:#b42318">%s · %s</div>'
    '<div style="font-size:16px;font-weight:700;color:#111111;margin-top:4px;line-height:1.45">%s</div><div style="font-size:14px;color:#333333;line-height:1.6;margin-top:4px">%s</div></td></tr>'
    % (e(CAT.get(n["c"], n["c"])), e(REGK.get(n["r"], n["r"])), e(n["h"]), e(n["p"])) for n in news3)

mail = j.get("mail", {})
tr = next((t for t in j["trends"] if t.get("stat")), None)
hook = mail.get("hook") or (news3[0]["h"] if news3 else strip(j["cover"]["title"]))
pre = mail.get("pre") or ("가전 전문 매거진 가전레이더 · 오늘의 추천: " + " · ".join(p["name"] for p in chosen))[:120]
num = mail.get("num") or tr
title = strip(j["cover"]["title"])
unsub = SITE + "unsubscribe.html" + ("?e=" + quote(a.to) if a.to else "")
no = ed["label"].split(" · ")[1] if " · " in ed["label"] else ed["date"]

body = f'''<!doctype html><html><head><meta charset="utf-8"><meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light"></head><body style="margin:0;background:#f2f2f2">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{e(pre)}&#8199;&#65279;&#847;&#8199;&#65279;&#847;</div>
<table role="presentation" cellpadding="0" cellspacing="0" width="100%" bgcolor="#f2f2f2" style="background:#f2f2f2"><tr><td align="center" style="padding:16px 8px">
<table role="presentation" cellpadding="0" cellspacing="0" width="600" bgcolor="#ffffff" style="max-width:600px;width:100%;table-layout:fixed;word-break:keep-all;overflow-wrap:anywhere;background:#ffffff;font-family:-apple-system,'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',sans-serif;color:#111111;border-top:6px solid #e0301e">
<tr><td style="padding:10px 24px;font-size:12px;line-height:1.5;color:#444444;border-bottom:1px solid #eeeeee">[광고] 이 메일의 쿠팡 링크는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</td></tr>
<tr><td style="padding:22px 24px 6px">
<div style="font-size:14px;font-weight:800;color:#e0301e;letter-spacing:.02em">가전 전문 매거진</div>
<div style="font-size:34px;font-weight:900;color:#111111;letter-spacing:-.04em;line-height:1.2;margin-top:2px">가전레이더 <span style="font-size:13px;font-weight:800;letter-spacing:.12em;color:#e0301e">GAJEON RADAR</span></div>
<div style="font-size:14px;color:#333333;line-height:1.55;margin-top:6px">AI가전·생활가전·대형가전·TV·IT 트렌드와 MD 추천템을 매일 아침 7시에</div>
<div style="font-size:13px;font-weight:700;color:#555555;margin-top:12px;padding-top:10px;border-top:1px solid #e5e5e5">{e(ed["label"])} · 3분 읽기</div>
</td></tr>
<tr><td style="padding:14px 24px 4px">
<div style="font-size:26px;font-weight:800;line-height:1.35;color:#111111;letter-spacing:-.03em">{e(title)}</div>
{('<table role="presentation" cellpadding="0" cellspacing="0" width="100%%" style="margin-top:16px"><tr><td bgcolor="#fff1ef" style="background:#fff1ef;border-left:5px solid #e0301e;padding:14px 16px"><span style="font-size:32px;font-weight:900;color:#e0301e">%s</span><br><span style="font-size:14px;font-weight:600;color:#222222">%s</span></td></tr></table>' % (e(num["stat"]), e(num["sl"]))) if num else ''}
</td></tr>
{sec("오늘의 추천템 3", "가전레이더 MD PICK", "".join(card(p) for p in chosen))}
{sec("놓치면 안 될 주요 뉴스 5", "POINT NEWS", news_rows)}
<tr><td style="padding:22px 24px 28px"><a href="{SITE}" style="display:block;text-align:center;padding:15px;border:2px solid #111111;border-radius:10px;background:#ffffff;color:#111111;text-decoration:none;font-size:15px;font-weight:800">가전 전문 매거진 가전레이더에서 전체 보기 &rarr;</a>
<div style="font-size:13px;color:#555555;text-align:center;margin-top:8px">제품 리스트 · 오늘의 특가 30%↑ · 신제품 · 모든 출처</div></td></tr>
<tr><td style="padding:18px 24px 26px;border-top:1px solid #e5e5e5;font-size:12px;line-height:1.75;color:#555555">
가격은 수집 시점({e(ed.get("collected", ""))}) 공개 자료 기준이며 판매처마다 다를 수 있습니다. 모든 수치의 출처는 홈페이지 ‘출처’ 섹션에 있습니다.<br>
전송자: {e(SND.get("name") or "가전레이더")} · <a href="mailto:{e(SND.get("email") or "newyangs007@gmail.com")}" style="color:#555555">{e(SND.get("email") or "newyangs007@gmail.com")}</a>{(" · " + e(SND["phone"])) if SND.get("phone") else ""}{(" · " + e(SND["addr"])) if SND.get("addr") else ""}<br>
더 이상 받지 않으려면 <a href="{e(unsub)}" style="color:#555555">수신 거부(구독 해지)</a>를 누르세요. 수신 거부에 비용이 들지 않습니다.<br>
If you no longer wish to receive this email, click <a href="{e(unsub)}" style="color:#555555">Unsubscribe</a>. Unsubscribing is free of charge.<br>{e(ed.get("next", ""))}</td></tr>
</table></td></tr></table></body></html>'''

txt = "가전 전문 매거진 가전레이더\n%s · 3분 읽기\n%s\n\n오늘의 추천템 3\n%s\n\n주요 뉴스 5\n%s\n\n홈페이지: %s\n\n[광고] 쿠팡 링크는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.\n수신 거부(구독 해지) / Unsubscribe: %s\n전송자: %s" % (
    ed["label"], title,
    "\n".join("- %s %s (★%.1f) %s" % (p["name"], p["price"], score(p), p.get("cp") or SITE + slug(p)) for p in chosen),
    "\n".join("- %s" % n["h"] for n in news3), SITE, unsub, " · ".join(x for x in [SND.get("name") or "가전레이더", SND.get("email") or "newyangs007@gmail.com", SND.get("phone", ""), SND.get("addr", "")] if x))
open("out/email.html", "w", encoding="utf-8").write(body)
open("out/email.txt", "w", encoding="utf-8").write(txt)
miss = [k for k in ("phone", "addr") if not SND.get(k)]
print(json.dumps({"subject": "(광고) [가전레이더 %s] %s" % (no, hook), "preheader": pre, "images": imgs,
                  "warn": ("config.sender에 %s가 비어 있습니다(정보통신망법 시행령 별표 6: 전송자 명칭·이메일·전화번호·주소 표시)" % ", ".join(miss)) if miss else ""}, ensure_ascii=False))
