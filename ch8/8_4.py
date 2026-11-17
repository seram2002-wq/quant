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
# 테스트 모드:  python 8_4.py --test
#   매수 조건과 상관없이 대상 ETF를 1주씩(최대 5종목) 바로 사고, 3분 뒤 전부 판다.
#   자동 매수 → 슬랙 알림 → 자동 매도 → 종료의 전체 흐름을 확인하는 용도이며,
#   모의투자에서만 동작한다.
#
# 책과 다른 점
#   - 대신증권 크레온 대신 한국투자증권 API(kis.py) 사용
#   - 매수는 최유리 지정가 후 미체결 잔량 취소, 매도는 시장가
#     (책은 매수 최유리 FOK, 매도 최유리 IOC)
#   - 목표가와 이동평균은 하루에 한 번만 계산 (모의투자 호출 제한 때문)
#   - 다시 실행했을 때 이미 보유한 종목은 매수한 것으로 처리 (중복 매수 방지)
#   - 매도는 대상 ETF(SYMBOLS)만 (책은 계좌의 모든 종목을 매도)
import os
import sys
import time
import socket
from datetime import datetime
from pathlib import Path

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
TEST_HOLD_SECONDS = 180     # 테스트 모드에서 매수 후 매도까지 기다리는 시간(초)
ORDER_WAIT_TRIES = 3        # 매수 주문 후 체결 확인 횟수 (2초 간격)

# ---------------------------------------------------------------- 슬랙
try:
    from slack_sdk import WebClient
    _slack = WebClient(token=os.getenv('SLACK_BOT_TOKEN')) \
        if os.getenv('SLACK_BOT_TOKEN') else None
except ImportError:
    _slack = None
_slack_channel = os.getenv('SLACK_CHANNEL', '#general')


LOG_DIR = Path(__file__).parent / 'logs'    # 날짜별 로그 파일 (logs\YYYYMMDD.log)


def printlog(message):
    """화면에 출력하고 로그 파일에도 남긴다 (슬랙으로는 보내지 않는다)."""
    line = datetime.now().strftime('[%m/%d %H:%M:%S] ') + str(message)
    print(line, flush=True)
    try:                                    # 작업 스케줄러로 실행하면 화면을 못 보므로 파일에도 기록
        LOG_DIR.mkdir(exist_ok=True)
        log_file = LOG_DIR / (datetime.now().strftime('%Y%m%d') + '.log')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except OSError:
        pass


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

    def buy_etf(self, code, test=False):
        """매수 조건을 만족하면 최유리 지정가로 매수한다. 매수했으면 True.

        test=True면 조건을 보지 않고 1주만 산다 (테스트 모드 전용).
        """
        if code in self.bought_list:
            return False
        name = SYMBOLS[code]
        if test:
            price = self.kis.get_price(code)['price']
            printlog(f'{name}({code}) : [테스트] 현재가 {price:,} → 1주 최유리 지정가 매수 주문')
            return self._order_buy(code, name, 1)
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
                 f'→ {qty}주 최유리 지정가 매수 주문')
        return self._order_buy(code, name, qty)

    def _held_qty(self, code):
        """잔고에서 해당 종목의 (보유 수량, 매입 평균가)를 돌려준다."""
        _, stocks = self.kis.get_balance()
        held = next((s for s in stocks if s['code'] == code), None)
        return (held['qty'], held['avg_price']) if held else (0, 0)

    def _order_buy(self, code, name, qty):
        """최유리 지정가로 매수하고, 체결되지 않은 잔량은 취소한다.

        최유리 지정가는 매도 1호가에 나온 물량만큼만 체결되므로 일부가 미체결로
        남을 수 있다. 미체결 주문이 남아 있으면 나중에 엉뚱한 때 체결될 수 있어서,
        잠시 기다린 뒤 잔량을 취소하고 체결된 수량만 보유한다.
        """
        self.bought_list.append(code)                   # 성공이든 실패든 오늘은 다시 주문하지 않음
        try:
            order = self.kis.buy(code, qty, best=True)  # 최유리 지정가
        except KISError as ex:
            dbgout(f'매수 주문 실패 : {name}({code}) {qty}주 → {ex}')
            return False

        held, avg = 0, 0
        for _ in range(ORDER_WAIT_TRIES):               # 체결을 기다린다
            time.sleep(2)
            held, avg = self._held_qty(code)
            if held >= qty:
                break
        canceled = False
        if held < qty:                                  # 미체결 잔량 취소
            try:
                self.kis.cancel(order)
                canceled = True
                printlog(f'{name}({code}) : 미체결 잔량 취소 요청')
            except KISError as ex:                      # 이미 다 체결됐으면 취소할 것이 없다
                printlog(f'{name}({code}) : 취소할 잔량 없음 ({ex})')
            time.sleep(2)
            held, avg = self._held_qty(code)

        if held >= qty:
            dbgout(f'매수 : {name}({code}) {held:,}주, 매입가 {avg:,}원')
        elif held > 0:
            dbgout(f'매수(일부 체결) : {name}({code}) {held:,}주 / 주문 {qty:,}주, '
                   f'매입가 {avg:,}원, 나머지는 취소')
        elif canceled:
            dbgout(f'매수 미체결 : {name}({code}) {qty:,}주 주문을 취소했습니다.')
        else:                                           # 취소할 잔량은 없는데 잔고에 아직 안 보임
            dbgout(f'매수 주문 : {name}({code}) {qty:,}주 (체결됐으나 잔고 반영 전일 수 있음)')
        return held > 0 or not canceled

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


def run_test(trader):
    """테스트 모드: 조건 없이 1주씩 사고, 잠시 뒤 전부 판다."""
    if trader.kis.mode != 'mock':
        printlog('테스트 모드는 모의투자(KIS_MODE=mock)에서만 실행합니다.')
        return
    t_now = datetime.now()
    hhmm = t_now.hour * 100 + t_now.minute
    if t_now.weekday() >= 5 or not 905 <= hhmm < 1510:
        printlog('테스트 모드는 평일 09:05~15:10 사이에만 실행합니다 (장 운영 시간).')
        return
    dbgout(f'[테스트 모드] 조건 없이 1주씩 매수하고 {TEST_HOLD_SECONDS // 60}분 뒤 전부 매도합니다.')
    for code in SYMBOLS:
        if len(trader.bought_list) >= TARGET_BUY_COUNT:
            break
        try:
            trader.buy_etf(code, test=True)
        except (KISError, OSError) as ex:
            dbgout(f'오류 : {SYMBOLS[code]}({code}) {ex}')
    trader.report()
    printlog(f'{TEST_HOLD_SECONDS}초 동안 보유한 뒤 매도합니다...')
    time.sleep(TEST_HOLD_SECONDS)
    if trader.sell_all(max_tries=4):
        trader.report()
        dbgout('[테스트 모드] 모든 종목을 매도했습니다. 종료합니다.')
    else:
        dbgout('[테스트 모드] 주의: 아직 팔리지 않은 종목이 있습니다. 잔고를 확인하세요.')


def main():
    # 프로그램이 두 개 동시에 돌면 같은 종목을 두 번 살 수 있으므로 하나만 실행되게 한다.
    # (같은 포트는 한 프로그램만 쓸 수 있다는 점을 이용. 프로그램이 끝나면 자동으로 풀림)
    global _single_instance_lock
    _single_instance_lock = socket.socket()
    try:
        _single_instance_lock.bind(('127.0.0.1', 47284))
    except OSError:
        printlog('자동매매가 이미 실행 중입니다. 이 창은 종료합니다.')
        return

    kis = KIS()
    trader = Trader(kis)
    trader.prepare()
    if '--test' in sys.argv:
        run_test(trader)
        return
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
                _, stocks = kis.get_balance()
                had_stocks = any(s['code'] in SYMBOLS for s in stocks)
                if trader.sell_all():
                    trader.report()
                    if had_stocks:
                        dbgout('모든 종목을 매도했습니다. 자동매매를 종료합니다.')
                    else:
                        dbgout('오늘은 매수한 종목이 없습니다. 자동매매를 종료합니다.')
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
