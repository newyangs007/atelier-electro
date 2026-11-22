import json,re,glob,os
issues=[]
for f in sorted(glob.glob('issues/*.json')):
    j=json.load(open(f,encoding='utf-8'))
    issues.append({"date":j['edition']['date'],"no":j['edition']['no'],"title":re.sub('<[^>]+>','',j['cover']['title'])})
issues.sort(key=lambda a:a['date'],reverse=True)
latest=json.load(open('issues/%s.json'%issues[0]['date'],encoding='utf-8'))
t=open('tools/template.html',encoding='utf-8').read()
dump=lambda o:json.dumps(o,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
t=t.replace('/*__BRANDS__*/',open('tools/brands.json',encoding='utf-8').read())
t=t.replace('/*__ICONS__*/',open('tools/icons.txt',encoding='utf-8').read())
t=t.replace('/*__ARCHIVE__*/',dump(issues)).replace('/*__ISSUE__*/',dump(latest))
open('index.html','w',encoding='utf-8').write(t)
print(issues)
