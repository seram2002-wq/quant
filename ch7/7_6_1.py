# 7.6 백트레이더를 이용한 백테스트 (1) RSI 전략
# 책 원본(ch07_08_Backtrader_RSI.py)은 bt.feeds.YahooFinanceData로 시세를 받지만,
# 야후 파이낸스 API가 바뀌어 더 이상 동작하지 않으므로
# FinanceDataReader로 받은 데이터프레임을 bt.feeds.PandasData로 넣도록 바꿈.
import backtrader as bt
import FinanceDataReader as fdr


class MyStrategy(bt.Strategy):
    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close)   # RSI 지표 (기본 14일)

    def next(self):                                     # 봉 하나마다 호출됨
        if not self.position:                           # 보유 주식이 없을 때
            if self.rsi < 30:                           # 과매도 → 매수
                self.order = self.buy()
        else:                                           # 보유 중일 때
            if self.rsi > 70:                           # 과매수 → 매도
                self.order = self.sell()


cerebro = bt.Cerebro()
cerebro.addstrategy(MyStrategy)

# 엔씨소프트(036570) 2017-01-01 ~ 2019-12-01
df = fdr.DataReader('036570', '2017-01-01', '2019-12-01')
data = bt.feeds.PandasData(dataname=df)
cerebro.adddata(data)

cerebro.broker.setcash(10000000)                        # 초기 투자금 1천만 원
cerebro.addsizer(bt.sizers.SizerFix, stake=30)          # 매매 단위 30주

print(f'Initial Portfolio Value : {cerebro.broker.getvalue():,.0f} KRW')
cerebro.run()
print(f'Final Portfolio Value   : {cerebro.broker.getvalue():,.0f} KRW')
cerebro.plot()
