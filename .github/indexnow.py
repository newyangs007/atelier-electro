# -*- coding: utf-8 -*-
"""push로 바뀐 페이지를 IndexNow로 검색엔진(Bing·네이버·Yandex·Seznam 등)에 바로 알림.
키 파일은 루트 사이트 https://newyangs007.github.io/<KEY>.txt 에 있어 같은 주소 아래 모든 사이트에 쓸 수 있습니다.
사용: python .github/indexnow.py <이전 커밋> <새 커밋>
"""
import json, os, subprocess, sys, urllib.parse, urllib.request

KEY = 'e147e9fae7f2d64b5415b1c3e58a86ca'
HOST = 'newyangs007.github.io'
SITE = f'https://{HOST}/{os.environ.get("SITE_PATH", "").strip("/")}/'
SKIP = ('mail/', 'tools/', '.github/', 'google', 'unsubscribe')
a, b = (sys.argv[1:3] + ['HEAD~1', 'HEAD'])[:2] if len(sys.argv) > 2 else ('HEAD~1', 'HEAD')
try:
    out = subprocess.run(['git', 'diff', '--name-only', '--diff-filter=AM', a, b], capture_output=True, text=True, check=True).stdout
except Exception as e:
    print('변경 목록을 읽지 못함:', e); sys.exit(0)
urls = []
for f in out.split('\n'):
    f = f.strip()
    if not f or f.startswith(SKIP) or not (f.endswith('.html') or f in ('llms.txt', 'llms-full.txt', 'rss.xml')):
        continue
    if f == 'index.html':
        urls.append(SITE)
    elif f.endswith('/index.html'):
        urls.append(SITE + urllib.parse.quote(f[:-len('index.html')]))
    else:
        urls.append(SITE + urllib.parse.quote(f))
urls = list(dict.fromkeys(urls))[:10000]
if not urls:
    print('알릴 페이지 없음'); sys.exit(0)
body = json.dumps({'host': HOST, 'key': KEY, 'keyLocation': f'https://{HOST}/{KEY}.txt', 'urlList': urls}).encode()
for ep in ['https://api.indexnow.org/indexnow', 'https://searchadvisor.naver.com/indexnow']:
    try:
        req = urllib.request.Request(ep, data=body, headers={'Content-Type': 'application/json; charset=utf-8'})
        with urllib.request.urlopen(req, timeout=20) as r:
            print(ep, r.status, f'{len(urls)}개')
    except Exception as e:
        print(ep, '실패:', e)
