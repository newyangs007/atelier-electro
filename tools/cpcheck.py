"""쿠팡 파트너스 링크 검증 결과(tools/cpcheck.json)를 읽어, 노출해도 되는 링크인지 판단한다.

규칙(운영자 지시, 2026-11-27):
- 링크는 쿠팡 파트너스 단축 링크(https://link.coupang.com/a/...)만 허용.
- 크롬으로 열어 봤을 때 ① 쿠팡 상품 페이지(/vp/products/<id>)로 가지 않거나 ② 파트너스 추적값(lptag=AF…)이 없거나
  ③ 엉뚱한 제품(같은 모델이 아님)이거나 ④ 페이지가 열리지 않거나(오류·없는 상품·판매 종료·품절) 하면 ok=false 로 기록하고,
  그 제품은 홈페이지·메일·제품 페이지 어디에도 내보내지 않는다.
"""
import json, os, re

_P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cpcheck.json')
CP_RE = re.compile(r'^https://link\.coupang\.com/a/[A-Za-z0-9]+$')


def load():
    try:
        return json.load(open(_P, encoding='utf-8')).get('links', {})
    except Exception:
        return {}


def bad_links():
    return sorted(k for k, v in load().items() if not v.get('ok'))


def usable(cp, _bad=None):
    if not cp or not CP_RE.match(cp.strip()):
        return False
    bad = set(_bad) if _bad is not None else set(bad_links())
    return cp.strip() not in bad
