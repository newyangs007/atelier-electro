#!/usr/bin/env python3
"""Apps Script 발송용 메일 템플릿을 홈페이지에 올린다.

mail/today.json   : 오늘 호 뉴스레터 (수신자 주소 자리 {{EMAIL}}, URL 인코딩 자리 {{EMAIL_ENC}})
mail/welcome.json : 구독 완료 메일 (광고 동의/미동의 두 가지, {{EMAIL}}·{{INTERESTS}}·{{DATE}} 자리)
mail/img/         : 메일에 넣는 제품 사진(240px)

구글 Apps Script(사용자 계정)가 이 파일을 읽어 사용자 Gmail 에서 직접 보낸다.
구독자 개인 정보는 여기에 들어가지 않는다.
"""
import json, os, shutil, subprocess, sys, datetime
from urllib.parse import quote

SITE = "https://newyangs007.github.io/atelier-electro/"
issue = sys.argv[1]
os.makedirs("mail/img", exist_ok=True)
os.makedirs("out/thumbs", exist_ok=True)


def run(cmd):
    return json.loads(subprocess.check_output([sys.executable] + cmd, text=True))


j = json.load(open(issue, encoding="utf-8"))
r = run(["tools/email.py", issue, "--to", "{{EMAIL}}", "--interests", ""])
html = open("out/email.html", encoding="utf-8").read()
text = open("out/email.txt", encoding="utf-8").read()
enc = quote("{{EMAIL}}")
html, text = html.replace(enc, "{{EMAIL_ENC}}"), text.replace(enc, "{{EMAIL_ENC}}")
imgs = []
for i, pth in enumerate(r.get("images", [])):
    base = os.path.basename(pth)
    shutil.copy(pth, "mail/img/" + base)
    imgs.append({"cid": "att%d" % i, "url": SITE + "mail/img/" + base})
no = j["edition"]["label"].split(" · ")[1] if " · " in j["edition"]["label"] else j["edition"]["date"]
json.dump({"date": j["edition"]["date"], "no": no, "subject": r["subject"], "preheader": r.get("preheader", ""),
           "html": html, "text": text, "images": imgs}, open("mail/today.json", "w", encoding="utf-8"), ensure_ascii=False)

# 구독 완료 메일: 날짜는 표시 형식이 그대로 바뀌도록 표식 날짜로 만든 뒤 자리 표시로 바꾼다
W = {}
for key, mkt in (("agree", "동의"), ("disagree", "미동의")):
    w = run(["tools/welcome.py", "--to", "{{EMAIL}}", "--interests", "{{INTERESTS}}", "--mkt", mkt,
             "--date", "2000-01-01", "--today", no])
    h = open("out/welcome.html", encoding="utf-8").read()
    t = open("out/welcome.txt", encoding="utf-8").read()
    for a, b in ((enc, "{{EMAIL_ENC}}"), ("2000년 1월 1일", "{{DATE}}"), ("2000.01.01", "{{DATE}}"), ("2000-01-01", "{{DATE}}")):
        h, t = h.replace(a, b), t.replace(a, b)
    W[key] = {"subject": w["subject"], "html": h, "text": t}
W["date"] = j["edition"]["date"]
json.dump(W, open("mail/welcome.json", "w", encoding="utf-8"), ensure_ascii=False)
# 지난 사진 정리: 오늘 메일에 쓰는 사진만 남김
keep = {os.path.basename(x["url"]) for x in imgs}
for f in os.listdir("mail/img"):
    if f not in keep:
        os.remove("mail/img/" + f)
print("mail/today.json", len(imgs), "images;", "mail/welcome.json")
