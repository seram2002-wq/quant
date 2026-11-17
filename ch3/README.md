# ch3 — 팬더스를 활용한 데이터 분석

3장 실습 기록입니다. 야후 파이낸스(`yfinance`)에서 주가와 지수를 받아
수익률, 최대 손실 낙폭(MDD), 지수 간 관계를 계산하고 그래프로 그립니다.

## 파일 목록

| 파일 | 내용 |
|---|---|
| `3_4_cumulative_return_comparison.py` | 삼성전자와 마이크로소프트의 일간 변동률, 누적 변동률 비교 |
| `3_5_kospi_mdd.py` | KOSPI의 최대 손실 낙폭(MDD) 계산 |
| `3_6_dow_kospi_comparison.py` | 다우존스 지수와 KOSPI 비교, 선형 회귀 분석 |
| `3_7_dow_kospi_regression_plot.py` | 다우존스와 KOSPI의 산점도와 회귀선 |

## 실행 방법

```
C:\workspaces\quant\quant.venv\Scripts\activate
cd C:\workspaces\quant\quant_실습\ch3
python 3_4_cumulative_return_comparison.py
```

인터넷 연결이 필요합니다 (야후 파이낸스에서 시세를 받아 옴).

## 3_4_cumulative_return_comparison.py — 일간 변동률과 누적 변동률

삼성전자(`005930.KS`)와 마이크로소프트(`MSFT`)의 2026-05-04 이후 종가로
두 가지를 계산하고, 누적 변동률을 한 그래프에 그립니다.

- 일간 변동률(%) = (오늘 종가 - 어제 종가) ÷ 어제 종가 × 100
- 누적 변동률(%) = 일간 변동률을 차례로 곱해 나간 값 (`cumprod`)

주가 수준이 다른 두 종목을 "같은 날 100에서 시작했다면"으로 맞춰서
비교하는 방법입니다. 주석 처리된 `plt.hist(...)`를 풀면 일간 변동률의
분포(히스토그램)를 볼 수 있습니다.

## 3_5_kospi_mdd.py — 최대 손실 낙폭(MDD)

MDD(Maximum Drawdown)는 일정 기간의 최고점에서 최저점까지 떨어진 비율로,
"가장 나쁜 시점에 샀을 때 얼마나 잃을 수 있었나"를 나타냅니다.

- 2004-01-04 이후 KOSPI(`^KS11`) 종가 사용
- `peak`: 최근 252거래일(약 1년)의 최고 종가
- `drawdown`: 그 최고가 대비 현재 종가의 하락률
- `max_dd`: 최근 252거래일 중 가장 큰 하락률

위쪽에 KOSPI 지수, 아래쪽에 낙폭(파랑)과 MDD(빨강)를 그리고, 전체 기간의
MDD 최솟값을 출력합니다.

## 3_6_dow_kospi_comparison.py — 다우존스와 KOSPI 비교

책의 3.6절을 한 파일에 순서대로 담았고, 앞 단계는 주석으로 남겨 뒀습니다.

| 부분 | 내용 | 상태 |
|---|---|---|
| 3.6.1 | 두 지수를 한 그래프에 그리기 | 주석 처리 |
| 3.6.2 | 시작일을 100으로 맞춘 지수화 비교 | 주석 처리 |
| 3.6.3 | 두 지수를 하나의 데이터프레임으로 합치고 산점도 그리기 | 데이터 합치기만 실행 |
| 3.6.4 | `scipy.stats.linregress`로 선형 회귀 분석 | 실행 |

두 나라의 휴장일이 달라 빈 값이 생기므로 `bfill()`과 `ffill()`로 채웁니다.
실행하면 회귀 분석 결과(기울기, 절편, 상관계수 등)가 출력됩니다. 앞
단계의 그래프를 보려면 해당 부분의 주석을 풀면 됩니다.

## 3_7_dow_kospi_regression_plot.py — 산점도와 회귀선

2000-01-04 이후 다우존스(X)와 KOSPI(Y)의 산점도를 그리고, 그 위에
회귀선 `Y = 기울기 × X + 절편`을 빨간 선으로 겹쳐 그립니다. 제목에
상관계수 R이 표시됩니다. R이 1에 가까울수록 두 지수가 같은 방향으로
움직였다는 뜻입니다.

## 책 원본 대비 수정 사항

- `pdr.get_data_yahoo()` 대신 `yf.download()`와 `yf.Ticker().history()` 사용
  (기존 방식은 더 이상 동작하지 않음)
- `yfinance`의 `auto_adjust` 기본값이 바뀌어 `Close`가 이미 수정 종가이므로
  `Adj Close` 대신 `Close` 사용
- `fillna(method='bfill')` 대신 `.bfill()`, `.ffill()` 사용 (최신 pandas 문법)
