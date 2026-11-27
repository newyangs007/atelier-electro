# 쿠팡 파트너스 링크 검증 (매일, 게시 전 필수)

운영자 규칙: 쿠팡 바로가기는 **쿠팡 파트너스로 연결되는지 확인**하고, 연결이 안 되거나 **엉뚱한 페이지**가 열리거나 **페이지 정보를 열 수 없으면 추천 제품에서 무조건 뺀다**.

## 방법 (Claude in Chrome, 사용자의 실제 크롬)
1. 오늘 호 picks 의 cp 를 하나씩 새 탭에서 연다(navigate). 4~5초 기다린다.
2. 같은 탭에서 아래 스크립트를 실행한다.

```js
(() => {
  const u = location.href;
  const el = document.querySelector('.prod-buy-header__title, h1.prod-buy-header__title, h2.prod-buy-header__title, .product-title, h1');
  const title = ((el && el.innerText) || document.title || '').trim().slice(0, 160);
  const body = (document.body && document.body.innerText || '').slice(0, 6000);
  const err = /페이지를 찾을 수 없|존재하지 않는 상품|판매 ?중지|판매 ?종료|품절|접근이 거부|Access Denied|일시적인 오류/.test(body);
  return { u, product: /coupang\.com\/vp\/products\/\d+/.test(u), partner: /[?&]lptag=AF/i.test(u), title, err };
})()
```

3. 판정 — 아래 중 하나라도 해당하면 **ok=false**:
   - product=false (상품 페이지가 아님) 또는 partner=false (lptag=AF… 없음)
   - err=true (없는 상품·판매 종료·품절·오류 페이지)
   - title 이 picks 의 제품명·모델명과 같은 모델이 아님(용량·크기·세대·색상 코드까지 비교)
   - 15초 안에 열리지 않음
4. 결과를 tools/cpcheck.json 의 links 에 기록한다:
   `"<cp>": {"ok": true|false, "date": "YYYY-MM-DD", "id": "<pick id>", "title": "<쿠팡 상품명>", "why": "<실패 이유>"}`
5. ok=false 인 제품은 오늘 호 picks 에서도 지운다(build.py·메일·클라이언트도 cpcheck.json 을 보고 한 번 더 걸러 냄).
   카테고리 최소 개수(TV 4종·로봇 6종 등)가 모자라면 쿠팡 파트너스에서 같은 모델이 확인되는 다른 인기 모델로 채운다.

크롬을 쓸 수 없는 날(클라우드판)은 새 링크를 만들거나 검증할 수 없으므로, cpcheck.json 에서 ok=false 인 제품을 빼고 지난 검증이 통과한 제품만 유지한다.
