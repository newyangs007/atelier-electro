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
          "모바일·워치": lambda p: p["cat"] in ("스마트폰", "태블릿", "워치")}
ints = [x.strip() for x in a.interests.split(",") if x.strip() in CATMAP]
picks = sorted(j["picks"], key=lambda p: -score(p))
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
    a0 = '<a href="%s" target="_blank" style="color:#121214;text-decoration:none">' % e(href)
    img = ""
    if p.get("img") and os.path.exists(p["img"]):
        cid = "att%d" % len(imgs)
        imgs.append(thumb(p["img"]))
        img = ('<td width="96" valign="top" style="padding-right:12px">%s<img src="cid:%s" width="96" height="96" alt="%s" '
               'style="display:block;width:96px;height:96px;object-fit:contain;background:#fff;border:1px solid #d6d2c9"></a></td>' % (a0, cid, e(p["name"])))
    btn = '<a href="%s" target="_blank" style="display:inline-block;margin-top:10px;padding:8px 14px;background:#121214;color:#f4f2ee;text-decoration:none;font-size:13px">%s &rarr;</a>' % (
        e(href), "쿠팡에서 보기" if p.get("cp") else "자세히 보기")
    tag = ' · <span style="color:#6a3f8f">관심 분야 맞춤</span>' if id(p) in matched else ''
    v = score(p)
    vd = "추천템" if v >= 4 else ("조건부" if v >= 3.5 else "관망")
    return ('<tr><td style="padding:16px 0;border-top:1px solid #d6d2c9"><table role="presentation" cellpadding="0" cellspacing="0" width="100%%"><tr>%s'
            '<td valign="top"><div style="font-size:11px;letter-spacing:.1em;color:#9c7a43">%s · ★ %.1f %s%s</div>'
            '<div style="font-size:16px;font-weight:600;margin:5px 0 3px;line-height:1.35">%s%s</a></div>'
            '<div style="font-size:15px;color:#121214">%s</div>'
            '<div style="font-size:13px;color:#5b5b61;line-height:1.55;margin-top:5px">%s</div>%s</td></tr></table></td></tr>'
            % (img, e(p["brand"]), v, vd, tag, a0, e(p["name"]), e(p["price"]), e(p["why"]), btn))


def sec(title, eyebrow, rows):
    return ('<tr><td style="padding:28px 28px 4px"><div style="font-size:11px;letter-spacing:.16em;color:#9c7a43">%s</div>'
            '<div style="font-family:Georgia,\'Noto Serif KR\',serif;font-size:21px;color:#121214;margin:6px 0 4px">%s</div>'
            '<table role="presentation" cellpadding="0" cellspacing="0" width="100%%">%s</table></td></tr>' % (eyebrow, title, rows))


order = {"AI": 0, "디바이스": 1, "소형": 2, "대형": 3}
pts = sorted([n for n in j["news"] if n.get("pt")], key=lambda n: order.get(n["c"], 4))
seen, news3 = set(), []
for n in pts:  # spread across fields: one per field first
    if n["c"] not in seen:
        news3.append(n); seen.add(n["c"])
    if len(news3) == 3: break
for n in pts:
    if len(news3) == 3: break
    if n not in news3: news3.append(n)
CAT = {"AI": "AI가전", "디바이스": "AI디바이스", "소형": "소형가전", "대형": "대형가전"}
news_rows = "".join(
    '<tr><td style="padding:12px 0;border-top:1px solid #d6d2c9"><span style="font-size:11px;letter-spacing:.08em;color:#9c7a43">%s · %s</span>'
    '<div style="font-size:15px;font-weight:600;color:#121214;margin-top:3px">%s</div><div style="font-size:13px;color:#5b5b61;line-height:1.55">%s</div></td></tr>'
    % (e(CAT.get(n["c"], n["c"])), e(n["r"]), e(n["h"]), e(n["p"])) for n in news3)

mail = j.get("mail", {})
tr = next((t for t in j["trends"] if t.get("stat")), None)
hook = mail.get("hook") or (news3[0]["h"] if news3 else strip(j["cover"]["title"]))
pre = mail.get("pre") or ("오늘의 추천: " + " · ".join(p["name"] for p in chosen))[:110]
num = mail.get("num") or tr
title = strip(j["cover"]["title"])
unsub = SITE + "unsubscribe.html" + ("?e=" + quote(a.to) if a.to else "")
no = ed["label"].split(" · ")[1] if " · " in ed["label"] else ed["date"]

body = f'''<!doctype html><html><body style="margin:0;background:#e9e6df">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">{e(pre)}&#8199;&#65279;&#847;&#8199;&#65279;&#847;</div>
<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background:#e9e6df"><tr><td align="center" style="padding:20px 10px">
<table role="presentation" cellpadding="0" cellspacing="0" width="600" style="max-width:600px;width:100%;table-layout:fixed;word-break:keep-all;overflow-wrap:anywhere;background:#f4f2ee;font-family:-apple-system,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;color:#121214">
<tr><td style="padding:12px 28px;font-size:11px;color:#5b5b61">[광고] 이 메일의 쿠팡 링크는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</td></tr>
<tr><td style="background:#0c0c0e;padding:32px 28px 30px">
<div style="font-size:26px;font-weight:900;letter-spacing:-.02em;color:#f4f2ee">가전레이더 <span style="font-size:12px;font-weight:600;letter-spacing:.14em;color:#e0301e">GAJEON RADAR</span></div>
<div style="font-size:11px;letter-spacing:.16em;color:#c9a96e;margin-top:6px">{e(ed["label"])} · 3분 읽기</div>
<div style="font-family:Georgia,'Noto Serif KR',serif;font-size:25px;line-height:1.3;color:#f4f2ee;margin-top:20px">{e(title)}</div>
{('<div style="margin-top:18px;padding-top:16px;border-top:1px solid #2a2a2e"><span style="font-size:30px;font-weight:700;color:#c9a96e">%s</span> <span style="font-size:13px;color:#b9b6ae">%s</span></div>' % (e(num["stat"]), e(num["sl"]))) if num else ''}
</td></tr>
{sec("오늘의 추천템 3", "TOP PICKS", "".join(card(p) for p in chosen))}
{sec("놓치면 안 될 뉴스 3", "POINT NEWS", news_rows)}
<tr><td style="padding:24px 28px 30px"><a href="{SITE}" style="display:block;text-align:center;padding:14px;background:#121214;color:#f4f2ee;text-decoration:none;font-size:14px">소싱 픽 전체 · 신제품 · 출처는 홈페이지에서 &rarr;</a></td></tr>
<tr><td style="padding:18px 28px 26px;border-top:1px solid #d6d2c9;font-size:11px;line-height:1.7;color:#5b5b61">
가격·리뷰는 수집 시점({e(ed.get("collected", ""))}) 공개 자료 기준이며 판매처마다 다를 수 있습니다. 모든 수치의 출처는 홈페이지 ‘출처’ 섹션에 있습니다.<br>
전송자: {e(SND.get("name") or "가전레이더")} · <a href="mailto:{e(SND.get("email") or "newyangs007@gmail.com")}" style="color:#5b5b61">{e(SND.get("email") or "newyangs007@gmail.com")}</a>{(" · " + e(SND["phone"])) if SND.get("phone") else ""}{(" · " + e(SND["addr"])) if SND.get("addr") else ""}<br>
더 이상 받지 않으려면 <a href="{e(unsub)}" style="color:#5b5b61">수신 거부(구독 해지)</a>를 누르세요. 수신 거부에 비용이 들지 않습니다.<br>
If you no longer wish to receive this email, click <a href="{e(unsub)}" style="color:#5b5b61">Unsubscribe</a>. Unsubscribing is free of charge.<br>{e(ed.get("next", ""))}</td></tr>
</table></td></tr></table></body></html>'''

txt = "%s · 3분 읽기\n%s\n\n오늘의 추천템 3\n%s\n\n뉴스 3\n%s\n\n홈페이지: %s\n\n[광고] 쿠팡 링크는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.\n수신 거부(구독 해지) / Unsubscribe: %s\n전송자: %s" % (
    ed["label"], title,
    "\n".join("- %s %s (★%.1f) %s" % (p["name"], p["price"], score(p), p.get("cp") or SITE + slug(p)) for p in chosen),
    "\n".join("- %s" % n["h"] for n in news3), SITE, unsub, " · ".join(x for x in [SND.get("name") or "가전레이더", SND.get("email") or "newyangs007@gmail.com", SND.get("phone", ""), SND.get("addr", "")] if x))
open("out/email.html", "w", encoding="utf-8").write(body)
open("out/email.txt", "w", encoding="utf-8").write(txt)
miss = [k for k in ("phone", "addr") if not SND.get(k)]
print(json.dumps({"subject": "(광고) %s · 가전레이더 %s" % (hook, no), "preheader": pre, "images": imgs,
                  "warn": ("config.sender에 %s가 비어 있습니다(정보통신망법 시행령 별표 6: 전송자 명칭·이메일·전화번호·주소 표시)" % ", ".join(miss)) if miss else ""}, ensure_ascii=False))
