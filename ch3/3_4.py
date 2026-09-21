from pandas_datareader import data as pdr
import yfinance as yf

# 삼성전자 데이터 처리
sec = yf.download('005930.KS', start='2026-05-04')
sec_dpc = (sec['Close'] - sec['Close'].shift(1)) / sec['Close'].shift(1) * 100
sec_dpc_cp = ((100 + sec_dpc) / 100).cumprod() * 100 - 100
sec_dpc.iloc[0] = 0

# 마이크로소프트 데이터 처리 (msft로 올바르게 변경)
msft = yf.download('MSFT', start='2026-05-04')
msft_dpc = (msft['Close'] - msft['Close'].shift(1)) / msft['Close'].shift(1) * 100
msft_dpc_cp = ((100 + msft_dpc) / 100).cumprod() * 100 - 100
msft_dpc.iloc[0] = 0

# print(sec.head())
# print(msft.head())

# tms_msft=msft.drop(columns='Volume')
# print(tms_msft.tail())

import matplotlib.pyplot as plt

plt.plot(sec.index,sec_dpc_cp, 'b', label='Samsung Electronics')
plt.plot(msft.index,msft_dpc_cp, 'r--', label='Mincrosoft')
# plt.show()

plt.ylabel('change%')
plt.legend(loc='best')
# plt.hist(sec_dpc,bins=18)
plt.grid(True)
plt.show()

# print(sec_dpc_cp)
# print(sec_dpc.describe())