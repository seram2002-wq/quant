import FinanceDataReader as fdr
import mplfinance as mpf

# 셀트리온 시세 가져오기
df = fdr.DataReader('068270')
df = df.dropna()
df = df.iloc[-30:]          # 최근 30개 거래일
df = df.sort_index()        # 날짜순 정렬 (인덱스가 이미 날짜)

# FinanceDataReader는 이미 Open/High/Low/Close/Volume 컬럼과
# DatetimeIndex를 주기 때문에 rename/astype 작업이 필요 없습니다.

mpf.plot(df, title='Celltrion candle chart', type='candle')

mpf.plot(df, title='Celltrion ohlc chart', type='ohlc')

kwargs = dict(title='Celltrion customized chart', type='candle',
    mav=(2, 4, 6), volume=True, ylabel='ohlc candles')
mc = mpf.make_marketcolors(up='r', down='b', inherit=True)
s = mpf.make_mpf_style(marketcolors=mc)
mpf.plot(df, **kwargs, style=s)