"""Build the daily newsletter email from an issue JSON.
Usage: python3 tools/email.py issues/YYYY-MM-DD.json  -> writes out/email.html, out/email.txt,
and prints a JSON list of inline images (in cid order) to attach.
"""
import json, re, sys, html

ARTIFACT_URL = "https://newyangs007.github.io/atelier-electro/"
f = sys.argv[1]
j = json.load(open(f, encoding="utf-8"))
ed = j["edition"]
strip = lambda s: re.sub("<[^>]+>", "", s)
e = html.escape


def score(p):
    m = sum(p["sc"]) / 5
    return round(m * 2) / 2


picks = j["picks"]
rec = [p for p in picks if score(p) >= 4.0][:4]
ai = [p for p in picks if p.get("ai")][:3]
imgs = []


def card(p):
    cid = ""
    if p.get("img"):
        cid = "att%d" % len(imgs)
        imgs.append(p["img"])
    buy = ('<a href="%s" target="_blank" style="display:inline-block;margin-top:10px;padding:9px 16px;background:#121214;color:#f4f2ee;'
           'text-decoration:none;font-size:13px;letter-spacing:.03em">쿠팡에서 보기 &rarr;</a>' % e(p["cp"])) if p.get("cp") else ""
    href = p.get("cp") or ARTIFACT_URL
    a0 = '<a href="%s" target="_blank" style="color:#121214;text-decoration:none">' % e(href)
    img = ('<td width="120" valign="top" style="padding-right:18px">%s<img src="cid:%s" width="120" height="120" alt="%s" '
           'style="display:block;width:120px;height:120px;object-fit:contain;background:#ffffff;border:1px solid #d6d2c9"></a></td>' % (a0, cid, e(p["name"]))) if cid else ""
    return ('<tr><td style="padding:18px 0;border-top:1px solid #d6d2c9"><table role="presentation" cellpadding="0" cellspacing="0" width="100%%"><tr>%s'
            '<td valign="top"><div style="font-size:11px;letter-spacing:.12em;color:#9c7a43">%s &middot; ★ %.1f</div>'
            '<div style="font-size:17px;font-weight:600;color:#121214;margin:6px 0 4px;line-height:1.35">%s%s</a></div>'
            '<div style="font-size:15px;color:#121214">%s <span style="color:#5b5b61;font-size:12px">· 리뷰 %s · 평점 %s</span></div>'
            '<div style="font-size:13px;color:#5b5b61;line-height:1.6;margin-top:6px">%s</div>%s</td></tr></table></td></tr>'
            % (img, e(p["brand"]), score(p), a0, e(p["name"]), e(p["price"]), e(str(p.get("rev", "—"))), e(str(p.get("rate", "—"))), e(p["why"]), buy))


def sec(title, eyebrow, rows):
    return ('<tr><td style="padding:34px 32px 6px"><div style="font-size:11px;letter-spacing:.16em;color:#9c7a43">%s</div>'
            '<div style="font-family:Georgia,\'Noto Serif KR\',serif;font-size:22px;color:#121214;margin:8px 0 6px">%s</div>'
            '<table role="presentation" cellpadding="0" cellspacing="0" width="100%%">%s</table></td></tr>' % (eyebrow, title, rows))


trend_rows = "".join(
    '<tr><td style="padding:12px 0;border-top:1px solid #d6d2c9"><span style="font-size:20px;font-weight:700;color:#121214">%s</span>'
    ' <span style="font-size:12px;color:#5b5b61">%s</span><div style="font-size:15px;font-weight:600;color:#121214;margin-top:4px">%s</div>'
    '<div style="font-size:13px;color:#5b5b61;line-height:1.6">%s</div></td></tr>' % (e(t["stat"]), e(t.get("sl", "")), e(t["t"]), e(t["line"]))
    for t in j["trends"][:3])
order = {"AI": 0, "소형": 1, "대형": 2}
pts = sorted([n for n in j["news"] if n.get("pt")], key=lambda n: order.get(n["c"], 3))[:5]
news_rows = "".join(
    '<tr><td style="padding:12px 0;border-top:1px solid #d6d2c9"><span style="font-size:11px;letter-spacing:.1em;color:#9c7a43">%s · %s</span>'
    '<div style="font-size:15px;font-weight:600;color:#121214;margin-top:4px">%s</div><div style="font-size:13px;color:#5b5b61;line-height:1.6">%s</div></td></tr>'
    % (e(n["c"]), e(n["r"]), e(n["h"]), e(n["p"])) for n in pts)

title = strip(j["cover"]["title"])
deck = e(j["cover"].get("deck", "")).replace("\n", "<br>")
body = f'''<!doctype html><html><body style="margin:0;background:#e9e6df">
<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background:#e9e6df"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" cellpadding="0" cellspacing="0" width="640" style="max-width:640px;width:100%;background:#f4f2ee;font-family:-apple-system,'Apple SD Gothic Neo','Malgun Gothic',sans-serif">
<tr><td style="padding:14px 32px;font-size:11px;color:#5b5b61">[광고] 이 메일의 쿠팡 링크는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</td></tr>
<tr><td style="background:#0c0c0e;padding:40px 32px 36px">
<div style="font-family:Georgia,serif;font-style:italic;font-size:30px;color:#f4f2ee">Atelier Électro</div>
<div style="font-size:11px;letter-spacing:.16em;color:#c9a96e;margin-top:8px">{e(ed["label"])}</div>
<div style="font-family:Georgia,'Noto Serif KR',serif;font-size:28px;line-height:1.3;color:#f4f2ee;margin-top:26px">{e(title)}</div>
<div style="font-size:14px;line-height:1.7;color:#b9b6ae;margin-top:12px">{deck}</div>
<a href="{ARTIFACT_URL}" style="display:inline-block;margin-top:24px;padding:12px 22px;border:1px solid #c9a96e;color:#c9a96e;text-decoration:none;font-size:13px;letter-spacing:.04em">오늘 호 전체 보기 &rarr;</a>
</td></tr>
{sec("오늘의 추천템", "SOURCING PICKS", "".join(card(p) for p in rec))}
{sec("AI가전 픽", "AI APPLIANCES", "".join(card(p) for p in ai))}
{sec("숫자로 본 트렌드", "TRENDS", trend_rows)}
{sec("놓치면 안 될 뉴스", "POINT NEWS", news_rows)}
<tr><td style="padding:30px 32px 36px"><a href="{ARTIFACT_URL}" style="display:block;text-align:center;padding:14px;background:#121214;color:#f4f2ee;text-decoration:none;font-size:14px">신제품 · 채널 · 출처까지 매거진에서 보기 &rarr;</a></td></tr>
<tr><td style="padding:20px 32px 30px;border-top:1px solid #d6d2c9;font-size:11px;line-height:1.7;color:#5b5b61">
가격·리뷰는 수집 시점({e(ed.get("collected",""))}) 다나와 등 공개 자료 기준이며 판매처마다 다를 수 있습니다. 모든 수치의 출처는 매거진의 ‘출처’ 섹션에 있습니다.<br>
수신을 원하지 않으시면 이 메일에 ‘구독 해지’라고 답장해 주세요. · {e(ed.get("next",""))}</td></tr>
</table></td></tr></table></body></html>'''

txt = "%s\n%s\n\n오늘의 추천템\n%s\n\nAI가전 픽\n%s\n\n전체 보기: %s\n\n[광고] 쿠팡 링크는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.\n수신 거부: '구독 해지'로 답장" % (
    ed["label"], title,
    "\n".join("- %s %s (★%.1f) %s" % (p["name"], p["price"], score(p), p.get("cp", "")) for p in rec),
    "\n".join("- %s %s (★%.1f) %s" % (p["name"], p["price"], score(p), p.get("cp", "")) for p in ai),
    ARTIFACT_URL)
import os
os.makedirs("out", exist_ok=True)
open("out/email.html", "w", encoding="utf-8").write(body)
open("out/email.txt", "w", encoding="utf-8").write(txt)
print(json.dumps({"subject": "(광고) Atelier Électro %s · %s" % (ed["label"].split(" · ")[1] if " · " in ed["label"] else ed["date"], title), "images": imgs}, ensure_ascii=False))
