# 8.1 한국투자증권 API 접속 테스트 (책의 "크레온 플러스 연결 확인"에 해당)
# 토큰 발급 → 현재가 조회 → 계좌 잔고 조회 → 주문 가능 금액 조회 순서로 확인한다.
# 주문은 하지 않는다.
from kis import KIS, KISError

try:
    kis = KIS()
    print(f'접속 대상 : {kis.server["name"]} ({kis.base_url})')
    print(f'계좌번호  : {kis.cano[:2]}******-{kis.acnt_prdt_cd}')

    kis.get_token()
    print('1. 토큰 발급 : 성공')

    p = kis.get_price('005930')
    print(f'2. 현재가 조회 : 삼성전자 {p["price"]:,}원 ({p["rate"]:+.2f}%), '
          f'시가 {p["open"]:,} 고가 {p["high"]:,} 저가 {p["low"]:,}')

    summary, stocks = kis.get_balance()
    print(f'3. 잔고 조회 : 예수금 {summary["cash"]:,}원, '
          f'총 평가금액 {summary["total"]:,}원, 보유 종목 {len(stocks)}개')
    for s in stocks:
        print(f'   - {s["name"]}({s["code"]}) {s["qty"]:,}주, '
              f'평가손익 {s["profit"]:+,}원')
    print(f'4. 주문 가능 금액 조회 : {kis.get_buyable_cash():,}원')
    print('접속 테스트를 모두 통과했습니다.')
except KISError as e:
    print('실패:', e)
