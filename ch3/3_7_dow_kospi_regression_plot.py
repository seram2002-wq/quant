import pandas as pd
import yfinance as yf
from scipy import stats
import matplotlib.pylab as plt

dow = yf.Ticker('^DJI').history(start='2000-01-04')
kospi = yf.Ticker('^KS11').history(start='2000-01-04')

df = pd.DataFrame({'X': dow['Close'], 'Y': kospi['Close']})
df = df.bfill()
df = df.ffill()

regr =stats.linregress(df.X,df.Y)
regr_line=f'Y={regr.slope:.2f}*X+{regr.intercept:.2f}'

plt.figure(figsize=(7,7))
plt.plot(df.X,df.Y,'.')
plt.plot(df.X,regr.slope*df.X+regr.intercept,'r')
plt.legend(['DOW X KOSPI', regr_line])
plt.title(f'DOW X KOSPI (R={regr.rvalue:.2f})')
plt.xlabel('Dow Jones Industrial Average')
plt.ylabel('KOSPI')
plt.show()