# 9.4 RNN(LSTM)을 이용한 주가 예측 (책 예제 ch09_09_RNN_StockPrediction.py)
# 삼성전자의 최근 10일 시세(시가, 고가, 저가, 거래량, 종가)를 보고
# 다음 날 종가를 예측하는 모델을 만든다.
#
# 실행 전 준비: MySQL이 켜져 있고 INVESTAR DB에 시세가 들어 있어야 한다.
#
# 책과 다른 점
#   - 조회 기간: 책은 2018-05-04 ~ 2020-01-22, 여기서는 DB에 있는 최근 기간
#   - LSTM의 input_shape 대신 Input 층 사용 (케라스 3 권장 방식)
#   - raw_df.close[-1] 대신 .iloc[-1] 사용 (최신 pandas는 위치 인덱싱에 iloc 필요)
#   - 내일 종가 환산을 정규화의 역변환으로 계산 (아래 주석 참고)
#   - 실행할 때마다 결과가 달라지지 않도록 난수 시드 고정
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'    # 텐서플로 안내 메시지 줄이기 (import보다 먼저)
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras import Sequential, Input
from tensorflow.keras.layers import Dense, LSTM, Dropout
from Investar import Analyzer

tf.keras.utils.set_random_seed(42)          # 난수 시드 고정

START_DATE = '2025-01-02'                   # 이 날짜부터 DB에 있는 최신 날짜까지 사용
mk = Analyzer.MarketDB()
raw_df = mk.get_daily_price('삼성전자', START_DATE)
print(f'데이터 : {raw_df.index[0]} ~ {raw_df.index[-1]}, {len(raw_df)}거래일')

window_size = 10    # 과거 며칠을 보고 예측할지
data_size = 5       # 하루치 데이터 개수 (시가, 고가, 저가, 거래량, 종가)


def MinMaxScaler(data):
    """최솟값과 최댓값을 이용하여 0 ~ 1 값으로 변환 (정규화)"""
    numerator = data - np.min(data, 0)
    denominator = np.max(data, 0) - np.min(data, 0)
    # 0으로 나누기 에러가 발생하지 않도록 매우 작은 값(1e-7)을 더해서 나눔
    return numerator / (denominator + 1e-7)


# 가격(수만 원)과 거래량(수천만 주)은 크기가 너무 달라서 모두 0~1로 맞춘다
dfx = raw_df[['open', 'high', 'low', 'volume', 'close']].astype(float)
dfx = MinMaxScaler(dfx)
dfy = dfx[['close']]

x = dfx.values.tolist()
y = dfy.values.tolist()

# 10일치 데이터(x) → 그다음 날 종가(y) 묶음을 하루씩 밀어 가며 만든다
data_x = []
data_y = []
for i in range(len(y) - window_size):
    _x = x[i : i + window_size]     # 다음 날 종가(i+window_size)는 포함되지 않음
    _y = y[i + window_size]         # 다음 날 종가
    data_x.append(_x)
    data_y.append(_y)
print(f'학습 묶음 : {len(data_y)}개 (입력 {window_size}일 × {data_size}개 값 → 다음 날 종가 1개)')

# 앞쪽 70%로 학습하고, 뒤쪽 30%로 얼마나 맞는지 확인한다
train_size = int(len(data_y) * 0.7)
train_x = np.array(data_x[0 : train_size])
train_y = np.array(data_y[0 : train_size])

test_size = len(data_y) - train_size
test_x = np.array(data_x[train_size : len(data_x)])
test_y = np.array(data_y[train_size : len(data_y)])

# 모델 생성: LSTM 2층 + 출력층
model = Sequential()
model.add(Input(shape=(window_size, data_size)))
model.add(LSTM(units=10, activation='relu', return_sequences=True))
model.add(Dropout(0.1))             # 일부 연결을 무작위로 꺼서 과적합을 줄임
model.add(LSTM(units=10, activation='relu'))
model.add(Dropout(0.1))
model.add(Dense(units=1))           # 출력: 다음 날 종가(정규화된 값) 1개
model.summary()

model.compile(optimizer='adam', loss='mean_squared_error')
model.fit(train_x, train_y, epochs=60, batch_size=30)
pred_y = model.predict(test_x)

# 실제 종가와 예측 종가 비교 그래프 (테스트 구간, 정규화된 값)
plt.figure(figsize=(9, 6))
plt.plot(test_y, color='red', label='real SEC stock price')
plt.plot(pred_y, color='blue', label='predicted SEC stock price')
plt.title('SEC stock price prediction')
plt.xlabel('time')
plt.ylabel('stock price (normalized)')
plt.legend()
image_dir = Path(__file__).parent / 'images'
image_dir.mkdir(exist_ok=True)
plt.savefig(image_dir / '9_4.png', dpi=100)     # ch9\images\9_4.png로 저장

# 가장 최근 10일로 "다음 거래일" 종가를 예측하고, 0~1 값을 원래 가격으로 되돌린다.
# 책은 raw_df.close[-1] * pred_y[-1] / dfy.close[-1] (비례식)로 계산하는데,
# 정규화가 "최솟값을 빼고 범위로 나눈 것"이므로 여기서는 그 역변환을 쓴다.
last_x = np.array([x[-window_size:]])
next_norm = float(model.predict(last_x, verbose=0)[0][0])
close_min, close_max = raw_df['close'].min(), raw_df['close'].max()
next_price = next_norm * (close_max - close_min + 1e-7) + close_min
print(f'마지막 종가 ({raw_df.index[-1]}) : {float(raw_df["close"].iloc[-1]):,.0f} KRW')
print(f"다음 거래일 예측 종가 (Tomorrow's SEC price) : {next_price:,.0f} KRW")

plt.show()
