# ch04_01_Celltrion_PlotChart.py
import FinanceDataReader as fdr
from matplotlib import pyplot as plt

# 셀트리온 전체 시세 가져오기
df = fdr.DataReader('068270')

# 차트 출력을 위해 데이터프레임 가공하기
df = df.dropna()
df = df.iloc[-30:]          # 최근 30개 거래일
df = df.sort_index()        # 날짜(인덱스) 순 정렬

# 날짜, 종가 컬럼으로 차트 그리기
plt.title('Celltrion (close)')
plt.xticks(rotation=45)
plt.plot(df.index, df['Close'], 'co-')
plt.grid(color='gray', linestyle='--')
plt.tight_layout()
plt.show()