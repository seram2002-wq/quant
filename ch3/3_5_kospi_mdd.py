import matplotlib.pyplot as plt
import yfinance as yf
 
# 1. Ticker 객체를 이용해 단일 인덱스 형태로 데이터 가져오기
ticker = yf.Ticker("^KS11")
kospi = ticker.history(start="2004-01-04")
window = 252
 
# 2. MDD 계산 (auto_adjust=True 기본값이라 'Close'가 이미 조정된 값입니다)
peak = kospi["Close"].rolling(window, min_periods=1).max()
drawdown = kospi["Close"] / peak - 1.0
max_dd = drawdown.rolling(window, min_periods=1).min()
 
# 3. 시각화
plt.figure(figsize=(9, 7))
plt.subplot(211)
kospi["Close"].plot(label="KOSPI", title="KOSPI MDD", grid=True, legend=True)
plt.subplot(212)
drawdown.plot(c="blue", label="KOSPI DD", grid=True, legend=True)
max_dd.plot(c="red", label="KOSPI MDD", grid=True, legend=True)
plt.show()

print(max_dd.min())