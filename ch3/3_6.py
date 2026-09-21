from pandas_datareader import data as pdr
import yfinance as yf
 
ticker2 = yf.Ticker("^DJI")
dow = ticker2.history(start="2004-01-04")
ticker1 = yf.Ticker("^KS11")
kospi = ticker1.history(start="2004-01-04")

#3.6.1
# import matplotlib.pyplot as plt
# plt.figure(figsize=(9,5))
# plt.plot(dow.index,dow['Close'],'r--',label='Dow Joens Industrial')
# plt.plot(kospi.index,kospi['Close'],'b',label='kospi')
# plt.legend(loc='best')
# plt.show()

#3.6.2
# d=(dow.Close/dow.Close.loc['2000-01-04'])*100
# k=(kospi.Close/kospi.Close.loc['2000-01-04'])*100
# import matplotlib.pyplot as plt
# plt.figure(figsize=(9,5))
# plt.plot(d.index,d,'r--',label='Dow Joens Industrial')
# plt.plot(k.index,k,'b',label='kospi')
# plt.grid(True)
# plt.legend(loc='best')
# plt.show()

# 3.6.3
import pandas as pd
df=pd.DataFrame({'DOW': dow['Close'],'KOSPI': kospi['Close']})
df=df.bfill()
df=df.ffill()
# import matplotlib.pyplot as plt
# plt.figure(figsize=(7,7))
# plt.scatter(df['DOW'],df['KOSPI'],marker='.')
# plt.xlabel('Dow Joens Industrial Average')
# plt.ylabel('KOSPI')
# plt.show()

#3.6.4
from scipy import stats
regr = stats.linregress(df['DOW'], df['KOSPI'])
print(regr)
