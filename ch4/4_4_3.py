# ch04_04_Celltrion_Candlestick.py
import FinanceDataReader as fdr
import mplfinance as mpf

# 셀트리온 전체 시세 가져오기
df = fdr.DataReader('068270')

# 최근 30개 거래일만 사용 (날짜순 정렬은 FinanceDataReader가 이미 해줌)
df = df.dropna()
df = df.iloc[-30:]

# 캔들스틱 차트 그리기
mpf.plot(
    df,
    type='candle',
    style='charles',      # 상승=빨강, 하락=파랑 계열의 스타일
    title='Celltrion (candle stick)',
    ylabel='Price',
    figsize=(9, 6),
    datetime_format='%Y-%m-%d',
    xrotation=45,
    show_nontrading=False
)
