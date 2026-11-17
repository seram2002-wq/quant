# 8.3 모의투자 주문 테스트
# KODEX 200을 시장가로 1주 사고, 잔고에 들어온 것을 확인한 뒤 다시 판다.
# 모의투자에서만 동작하도록 막아 두었다 (실전 계좌로는 실행되지 않음).
import time
from kis import KIS, KISError

CODE, NAME, QTY = '069500', 'KODEX 200', 1


def show_balance(kis, title):
    summary, stocks = kis.get_balance()
    print(f'[{title}] 예수금 {summary["cash"]:,}원, '
          f'총 평가금액 {summary["total"]:,}원, 보유 종목 {len(stocks)}개')
    for s in stocks:
        print(f'   - {s["name"]}({s["code"]}) {s["qty"]:,}주 '
              f'(매도 가능 {s["sellable"]:,}주), 매입가 {s["avg_price"]:,}원, '
              f'평가손익 {s["profit"]:+,}원')
    return stocks


def wait_holding(kis, code, want, tries=10):
    """보유 수량이 want(True: 있음, False: 없음) 상태가 될 때까지 기다린다."""
    for _ in range(tries):
        time.sleep(2)
        _, stocks = kis.get_balance()
        held = [s for s in stocks if s['code'] == code and s['sellable'] > 0]
        if bool(held) == want:
            return held[0]['sellable'] if held else 0
    return None


try:
    kis = KIS()
    if kis.mode != 'mock':
        raise SystemExit('이 테스트는 모의투자(KIS_MODE=mock)에서만 실행합니다.')
    print(f'접속 대상 : {kis.server["name"]}')
    show_balance(kis, '주문 전')

    r = kis.buy(CODE, QTY)                             # 시장가 매수
    print(f'매수 주문 : {NAME} {QTY}주 시장가, 주문번호 {r["order_no"]} ({r["message"]})')

    sellable = wait_holding(kis, CODE, True)
    if sellable is None:
        show_balance(kis, '매수 후')
        raise SystemExit('매수가 아직 체결되지 않았습니다. 장 운영 시간(09:00~15:30)인지 '
                         '확인하고, 잠시 뒤 잔고를 다시 조회해 보세요.')
    show_balance(kis, '매수 후')

    r = kis.sell(CODE, sellable)                       # 시장가 매도
    print(f'매도 주문 : {NAME} {sellable}주 시장가, 주문번호 {r["order_no"]} ({r["message"]})')

    if wait_holding(kis, CODE, False) is None:
        print('매도가 아직 체결되지 않았습니다. 잠시 뒤 잔고를 다시 조회해 보세요.')
    show_balance(kis, '매도 후')
    print('주문 테스트가 끝났습니다.')
except KISError as e:
    print('실패:', e)
