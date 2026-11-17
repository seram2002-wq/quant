# 7.6 백트레이더를 이용한 백테스트 (2) RSI_SMA 전략 + 수수료 + 매매 로그
# 책 원본(ch07_09_Backtrader_RSI_SMA.py)에서 시세 조회만
# YahooFinanceData → FinanceDataReader + PandasData로 바꿈.
import backtrader as bt
import FinanceDataReader as fdr


class MyStrategy(bt.Strategy):
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.rsi = bt.indicators.RSI_SMA(self.data.close, period=21)

    def notify_order(self, order):                      # 주문 상태가 바뀔 때마다 호출됨
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:           # 주문 체결
            if order.isbuy():
                self.log(f'BUY  : 주가 {order.executed.price:,.0f}, '
                    f'수량 {order.executed.size:,.0f}, '
                    f'수수료 {order.executed.comm:,.0f}, '
                    f'자산 {cerebro.broker.getvalue():,.0f}')
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(f'SELL : 주가 {order.executed.price:,.0f}, '
                    f'수량 {order.executed.size:,.0f}, '
                    f'수수료 {order.executed.comm:,.0f}, '
                    f'자산 {cerebro.broker.getvalue():,.0f}')
            self.bar_executed = len(self)
        elif order.status in [order.Canceled]:
            self.log('ORDER CANCELD')
        elif order.status in [order.Margin]:
            self.log('ORDER MARGIN')
        elif order.status in [order.Rejected]:
            self.log('ORDER REJECTED')
        self.order = None

    def next(self):
        if not self.position:
            if self.rsi < 30:
                self.order = self.buy()
        else:
            if self.rsi > 70:
                self.order = self.sell()

    def log(self, txt, dt=None):
        dt = self.datas[0].datetime.date(0)
        print(f'[{dt.isoformat()}] {txt}')


cerebro = bt.Cerebro()
cerebro.addstrategy(MyStrategy)

# 엔씨소프트(036570) 2017-01-01 ~ 2019-12-01
df = fdr.DataReader('036570', '2017-01-01', '2019-12-01')
data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)

cerebro.broker.setcash(10000000)
cerebro.broker.setcommission(commission=0.0014)         # 수수료 0.14% (매수/매도 각각)
cerebro.addsizer(bt.sizers.PercentSizer, percents=90)   # 자산의 90%로 매매

print(f'Initial Portfolio Value : {cerebro.broker.getvalue():,.0f} KRW')
cerebro.run()
print(f'Final Portfolio Value   : {cerebro.broker.getvalue():,.0f} KRW')
cerebro.plot(style='candlestick')
