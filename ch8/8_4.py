# 8.4 변동성 돌파 전략 ETF 자동매매 (책의 EtfAlgoTrader.py에 해당)
#
# 하루 동안 켜 두면 아래 순서로 동작한다.
#   09:00~09:05  전날 팔지 못한 대상 ETF가 있으면 전부 매도
#   09:05~15:15  ETF별 목표가를 넘고 5일·10일 이동평균보다 위면 매수
#                (최대 5종목, 종목당 주문 가능 금액의 19%)
#   15:15~15:20  보유한 대상 ETF를 전부 매도하고 종료
#   15:20 이후   종료
# 매매와 오류는 슬랙으로도 알린다.
#
# 책과 다른 점
#   - 대신증권 크레온 대신 한국투자증권 API(kis.py) 사용
#   - 주문은 시장가 (책은 최유리 FOK/IOC)
#   - 목표가와 이동평균은 하루에 한 번만 계산 (모의투자 호출 제한 때문)
#   - 다시 실행했을 때 이미 보유한 종목은 매수한 것으로 처리 (중복 매수 방지)
#   - 매도는 대상 ETF(SYMBOLS)만 (책은 계좌의 모든 종목을 매도)
import os
import sys
import time
from datetime import datetime

from kis import KIS, KISError
from strategy import analyze, is_buy_signal

# 매매 대상 ETF (종목코드: 이름)
SYMBOLS = {
    '069500': 'KODEX 200',
    '102110': 'TIGER 200',
    '229200': 'KODEX 코스닥150',
    '133690': 'TIGER 미국나스닥100',
    '360750': 'TIGER 미국S&P500',
    # 인버스 ETF: 지수가 내리면 오르는 상품 (하락장에서 매수 조건을 만족)
    '114800': 'KODEX 인버스',
    '251340': 'KODEX 코스닥150선물인버스',
}
TARGET_BUY_COUNT = 5        # 하루에 매수할 최대 종목 수
BUY_PERCENT = 0.19          # 종목당 주문 비율 (5종목 × 19% = 95%, 나머지는 여유분)

# ---------------------------------------------------------------- 슬랙
try:
    from slack_sdk import WebClient
    _slack = WebClient(token=os.getenv('SLACK_BOT_TOKEN')) \
        if os.getenv('SLACK_BOT_TOKEN') else None
except ImportError:
    _slack = None
_slack_channel = os.getenv('SLACK_CHANNEL', '#general')


def printlog(message):
    """화면에만 출력한다."""
    print(datetime.now().strftime('[%m/%d %H:%M:%S]'), message, flush=True)


def dbgout(message):
    """화면과 슬랙에 동시에 출력한다. 슬랙 전송이 실패해도 프로그램은 계속된다."""
    printlog(message)
    if _slack is None:
        return
    try:
        _slack.chat_postMessage(
            channel=_slack_channel,
            text=datetime.now().strftime('[%m/%d %H:%M:%S] ') + message)
    except Exception as ex:
        printlog(f'(슬랙 전송 실패: {ex})')


# ---------------------------------------------------------------- 매매
class Trader:
    def __init__(self, kis):
        self.kis = kis
        self.bought_list = []       # 오늘 매수한 종목 코드
        self.infos = {}             # 종목별 목표가·이동평균 (하루 한 번 계산)
        self.no_data = set()        # 오늘 시세가 없다고 이미 알린 종목
        self.buy_amount = 0         # 종목당 주문 금액

    def prepare(self):
        """시작할 때 잔고와 주문 가능 금액을 확인하고 종목당 주문 금액을 정한다."""
        _, stocks = self.kis.get_balance()
        for s in stocks:
            # 이미 보유 중인 대상 종목은 매수한 것으로 본다 (재실행 시 중복 매수 방지)
            if s['code'] in SYMBOLS and s['code'] not in self.bought_list:
                self.bought_list.append(s['code'])
        total_cash = self.kis.get_buyable_cash()
        self.buy_amount = int(total_cash * BUY_PERCENT)
        dbgout(f'자동매매 시작 ({self.kis.server["name"]}) : 주문 가능 금액 {total_cash:,}원, '
               f'종목당 {BUY_PERCENT:.0%} = {self.buy_amount:,}원, '
               f'보유 종목 {len(stocks)}개')

    def buy_etf(self, code):
        """매수 조건을 만족하면 시장가로 매수한다. 매수했으면 True."""
        if code in self.bought_list:
            return False
        name = SYMBOLS[code]
        if code not in self.infos:
            info = analyze(self.kis, code)
            if info is None:                            # 오늘 시세 없음
                if code not in self.no_data:
                    self.no_data.add(code)
                    printlog(f'{name}({code}) : 오늘 시세가 아직 없습니다.')
                return False
            self.infos[code] = info
            printlog(f'{name}({code}) : 목표가 {info["target"]:,.0f}, '
                     f'5일선 {info["ma5"]:,.0f}, 10일선 {info["ma10"]:,.0f}')
        info = self.infos[code]
        price = self.kis.get_price(code)['price']
        if not is_buy_signal(info, price):
            return False

        qty = self.buy_amount // price
        if qty <= 0:
            printlog(f'{name}({code}) : 매수 조건 충족, 그러나 주문 금액이 1주 가격보다 작습니다.')
            self.bought_list.append(code)               # 다시 시도하지 않음
            return False
        printlog(f'{name}({code}) : 현재가 {price:,} > 목표가 {info["target"]:,.0f} '
                 f'→ {qty}주 시장가 매수 주문')
        self.bought_list.append(code)                   # 성공이든 실패든 오늘은 다시 주문하지 않음
        try:
            self.kis.buy(code, qty)
        except KISError as ex:
            dbgout(f'매수 주문 실패 : {name}({code}) {qty}주 → {ex}')
            return False
        time.sleep(2)
        _, stocks = self.kis.get_balance()
        held = next((s for s in stocks if s['code'] == code), None)
        if held:
            dbgout(f'매수 : {name}({code}) {held["qty"]:,}주, 매입가 {held["avg_price"]:,}원')
        else:
            dbgout(f'매수 주문 : {name}({code}) {qty}주 (체결 확인 전)')
        return True

    def sell_all(self, max_tries=10):
        """보유한 대상 ETF를 모두 시장가로 매도한다. 전부 팔리면 True.

        책은 계좌의 모든 종목을 팔지만, 여기서는 SYMBOLS에 있는 종목만 판다.
        (실전 계좌에 따로 보유한 주식이 있어도 건드리지 않도록)
        """
        for _ in range(max_tries):
            _, stocks = self.kis.get_balance()
            stocks = [s for s in stocks if s['code'] in SYMBOLS]
            if not stocks:
                return True
            for s in stocks:
                if s['sellable'] > 0:
                    self.kis.sell(s['code'], s['sellable'])
                    dbgout(f'매도 주문 : {s["name"]}({s["code"]}) {s["sellable"]:,}주, '
                           f'평가손익 {s["profit"]:+,}원')
            time.sleep(30)
        return False

    def report(self):
        """현재 잔고를 슬랙으로 알린다."""
        summary, stocks = self.kis.get_balance()
        lines = [f'잔고 : 총 평가금액 {summary["total"]:,}원, 보유 종목 {len(stocks)}개']
        for s in stocks:
            lines.append(f'  {s["name"]}({s["code"]}) {s["qty"]:,}주, '
                         f'평가손익 {s["profit"]:+,}원')
        dbgout('\n'.join(lines))


def main():
    kis = KIS()
    trader = Trader(kis)
    trader.prepare()
    soldout = False                 # 09:00~09:05 매도를 했는지
    reported_hour = None            # 잔고를 알린 시(hour)
    last_error = ''

    while True:
        t_now = datetime.now()
        t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
        t_start = t_now.replace(hour=9, minute=5, second=0, microsecond=0)
        t_sell = t_now.replace(hour=15, minute=15, second=0, microsecond=0)
        t_exit = t_now.replace(hour=15, minute=20, second=0, microsecond=0)

        if t_now.weekday() >= 5:                        # 토요일, 일요일
            printlog('주말에는 실행하지 않습니다.')
            return
        try:
            if t_9 < t_now < t_start and not soldout:   # 전날 남은 종목 정리
                soldout = True
                trader.sell_all()
                trader.bought_list.clear()
            if t_start < t_now < t_sell:                # 매수 구간
                for code in SYMBOLS:
                    if len(trader.bought_list) < TARGET_BUY_COUNT:
                        trader.buy_etf(code)
                if t_now.minute >= 30 and reported_hour != t_now.hour:
                    reported_hour = t_now.hour          # 매시 30분에 한 번 잔고 알림
                    trader.report()
            if t_sell < t_now < t_exit:                 # 일괄 매도 구간
                if trader.sell_all():
                    trader.report()
                    dbgout('모든 종목을 매도했습니다. 자동매매를 종료합니다.')
                    return
                dbgout('주의: 아직 팔리지 않은 종목이 있습니다.')
            if t_exit < t_now:                          # 장 마감 전 종료
                dbgout('자동매매를 종료합니다.')
                return
            last_error = ''
        except (KISError, OSError) as ex:               # API 오류, 네트워크 오류
            msg = str(ex)
            if msg != last_error:                       # 같은 오류는 한 번만 알림
                last_error = msg
                dbgout(f'오류 : {msg}')
            time.sleep(10)
        time.sleep(3)


if __name__ == '__main__':
    try:
        main()
    except KISError as e:
        dbgout(f'시작 실패 : {e}')
        sys.exit(1)
    except KeyboardInterrupt:
        printlog('사용자가 중단했습니다. 보유 종목이 있다면 직접 확인하세요.')
