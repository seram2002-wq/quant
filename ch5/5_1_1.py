import yfinance as yf
import matplotlib.pyplot as plt

df = yf.download('005930.KS', start='2017-01-01', auto_adjust=False)

plt.figure(figsize=(9, 6))
plt.subplot(2, 1, 1)
plt.title('Samsung Electronics (Yahoo Finance)')
plt.plot(df.index, df['Close'], 'c', label='Close')
plt.plot(df.index, df['Adj Close'], 'b--', label='Adj Close')
plt.legend(loc='best')
plt.subplot(2, 1, 2)
plt.bar(df.index, df['Volume'].values.flatten(), color='g', label='Volume')
plt.legend(loc='best')
plt.show()