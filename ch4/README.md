# ch4 — 웹 스크레이핑을 사용한 데이터 분석

4장 실습 기록입니다. KRX 상장법인 목록을 읽어 오고, 셀트리온의 시세로
종가 차트와 캔들 차트를 그립니다.

## 파일 목록

| 파일 | 내용 |
|---|---|
| `4_1_krx_listed_companies.py` | KRX 상장법인 목록 읽기 |
| `4_4_3_celltrion_candlestick.py` | 셀트리온 캔들 차트 |
| `4_4_3_2_celltrion_mplfinance_styles.py` | 셀트리온 캔들, OHLC, 이동평균·거래량 포함 차트 |
| `4_5_celltrion_close_chart.py` | 셀트리온 종가 차트 |

## 실행 방법

```
C:\workspaces\quant\quant.venv\Scripts\activate
cd C:\workspaces\quant\quant_실습\ch4
python 4_1_krx_listed_companies.py
```

인터넷 연결이 필요합니다.

## 4_1_krx_listed_companies.py — KRX 상장법인 목록

KRX 기업공시 사이트(`kind.krx.co.kr`)의 상장법인 목록 다운로드 주소를
`pd.read_html()`로 바로 읽습니다.

- `encoding='euc-kr'`: 한글이 깨지지 않도록 인코딩 지정
- 종목코드를 문자열로 바꾸고 `zfill(6)`으로 6자리를 맞춤
  (숫자로 읽으면 `005930`이 `5930`이 되기 때문)
- 종목코드 순으로 정렬해 출력

위쪽 주석은 내려받은 엑셀 파일(`상장법인목록.xls`)을 읽는 방법입니다.
이 목록 읽기는 이후 `Investar\DBUpdater.py`와 8장의 종목명 조회에도
같은 방식으로 쓰입니다.

## 4_5_celltrion_close_chart.py — 종가 차트

셀트리온(068270)의 최근 30거래일 종가를 꺾은선 그래프로 그립니다.
`fdr.DataReader('068270')`으로 전체 시세를 받아 마지막 30행만 사용합니다.

## 4_4_3_celltrion_candlestick.py — 캔들 차트

같은 데이터를 `mplfinance`로 캔들 차트로 그립니다. 캔들 하나가 하루의
시가, 고가, 저가, 종가를 나타냅니다. `style='charles'`를 사용했습니다.

## 4_4_3_2_celltrion_mplfinance_styles.py — 차트 종류와 꾸미기

`mplfinance`로 차트 세 개를 차례로 그립니다. 창을 닫으면 다음 차트가
나옵니다.

1. 기본 캔들 차트 (`type='candle'`)
2. OHLC 차트 (`type='ohlc'`)
3. 꾸민 캔들 차트: 이동평균선 3개(`mav=(2, 4, 6)`), 거래량(`volume=True`),
   상승 빨강·하락 파랑(`make_marketcolors(up='r', down='b')`)

국내에서는 상승을 빨강, 하락을 파랑으로 표시하므로 색을 직접 지정했습니다.

## 책 원본 대비 수정 사항

- **네이버 금융 스크레이핑 → FinanceDataReader**: 책은 네이버 금융의 일별
  시세 페이지를 BeautifulSoup으로 한 페이지씩 긁어 오지만, 해당 페이지가
  폐기되어 동작하지 않음. `fdr.DataReader()`로 교체
- FinanceDataReader는 날짜 인덱스와 `Open`, `High`, `Low`, `Close`, `Volume`
  컬럼을 바로 주기 때문에, 책의 컬럼 이름 변경과 자료형 변환이 필요 없음
- `mpl_finance`(지원 종료) 대신 `mplfinance` 사용
- `read_html()`에 `encoding='euc-kr'` 명시, 종목코드는
  `.astype(str).str.zfill(6)`으로 처리
