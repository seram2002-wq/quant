# quant_실습 — 파이썬 증권 데이터 분석 실습

『파이썬 증권 데이터 분석』(Investar) 책을 3장부터 9장까지 따라가며 진행한 실습
프로젝트입니다. 책이 나온 뒤 네이버 금융 시세 페이지 폐기, 야후 파이낸스 API
변경, 증권사 API 변경 등으로 원본 코드가 그대로 동작하지 않는 부분이 많아,
최신 파이썬과 라이브러리 버전에 맞게 고쳐 가며 진행했습니다.

각 장의 자세한 내용과 실행 결과는 장별 `README.md`에 있습니다.

## 장별 요약

| 장 | 주제 | 주요 내용 | 데이터 출처 |
|---|---|---|---|
| [ch3](ch3/README.md) | 팬더스 데이터 분석 | 누적 수익률 비교, KOSPI MDD, 다우존스·KOSPI 회귀 분석 | 야후 파이낸스 |
| [ch4](ch4/README.md) | 웹 스크레이핑 | KRX 상장법인 목록, 셀트리온 종가·캔들 차트 | KRX, FinanceDataReader |
| [ch5](ch5/README.md) | 시세 DB 구축 | MySQL 테이블 생성, 접속 테스트, DB 시세 조회 | MySQL (`INVESTAR`) |
| [ch6](ch6/README.md) | 트레이딩 전략 | 효율적 투자선, 샤프 지수, 볼린저 밴드, 삼중창, 듀얼 모멘텀 | MySQL |
| [ch7](ch7/README.md) | 장고와 자동화 | 장고 웹(관리자, 인덱스, 계좌 잔고), 슬랙 알림, 백트레이더 백테스트 | FinanceDataReader |
| [ch8](ch8/README.md) | 변동성 돌파 자동매매 | 한국투자증권 API 모의투자 ETF 자동매매, 작업 스케줄러 | 한국투자증권 Open API |
| [ch9](ch9/README.md) | 딥러닝 주가 예측 | 활성화 함수, 다층 퍼셉트론, 선형 회귀, LSTM 주가 예측 | MySQL |

## 개발 환경

- Python 3.11.9, 가상환경 `C:\workspaces\quant\quant.venv` (venv)
- IDE: VS Code, Git 관리 도구: Sourcetree
- 원격 저장소: GitHub (`seram2002-wq/quant`)
- DB: MySQL 8.0 (로컬 설치). 책은 MariaDB 기준이지만 `pymysql`로 같은 방식으로
  사용 가능해서 MySQL 사용
- 장고 프로젝트: `C:\mySite\Investar` (이 저장소 밖, 7장)
- 증권사 API: 한국투자증권 KIS Developers 모의투자 (8장, 책은 대신증권 크레온)
- 알림: 슬랙 봇 (`slack_sdk`)
- 딥러닝: TensorFlow 2.21.0 (케라스 포함)

## 폴더 구조

```
quant_실습/
├── ch3/ ~ ch9/              # 장별 실습 코드와 README
├── Investar/                # 시세 DB 공용 모듈 (5, 6, 9장에서 사용)
│   ├── Analyzer.py          # MarketDB 클래스 (DB 조회)
│   ├── MarketDB.py          # Analyzer.py와 같은 내용으로 맞춘 조회 모듈
│   ├── DBUpdater.py         # KRX 종목 목록 + 일별 시세 수집, DB 저장
│   ├── DBUpdaterEx.py       # DBUpdater + 매일 17시 자동 재실행
│   └── config.json          # 시세 수집 기간 설정 (git 추적 제외)
├── run_dbupdater.bat        # 로그인 시 DBUpdaterEx.py 실행 (시세 DB 업데이트)
├── run_trader.bat           # 작업 스케줄러가 평일 08:50에 8장 자동매매 실행
├── requirements.txt         # 필요한 라이브러리 목록 (장별 주석)
├── requirements-lock.txt    # 설치된 전체 라이브러리와 정확한 버전 (pip freeze)
├── .env.example             # 환경 변수 이름 예시 (값 없음)
├── .env                     # 비밀번호, API 키, 토큰 (git 추적 제외)
├── .gitignore
└── 상장법인목록.xls         # 4장 실습용 KRX 상장법인 목록
```

파일 이름은 `장_절_내용.py` 형식입니다 (예: `6_3_1_bollinger_band.py`,
`8_4_auto_trader.py`). 숫자로 시작하는 파일은 `import`로 불러올 수 없으므로,
다른 파일이 불러 쓰는 모듈은 `kis.py`, `strategy.py`처럼 이름을 따로 지었습니다.

## 처음 설정

1. 가상환경을 만들고 라이브러리 설치

   ```
   python -m venv C:\workspaces\quant\quant.venv
   C:\workspaces\quant\quant.venv\Scripts\activate
   cd C:\workspaces\quant\quant_실습
   pip install -r requirements.txt
   ```

   지금과 완전히 같은 버전으로 설치하려면 `requirements-lock.txt`를 사용합니다.
   최신 버전으로 설치하면 코드를 다시 고쳐야 할 수 있습니다.

2. `.env.example`을 복사해 `.env`를 만들고 값을 채움 (git에 올리지 않음)

   | 항목 | 용도 |
   |---|---|
   | `DB_PASSWORD` | MySQL root 비밀번호 (5, 6, 9장, `Investar`) |
   | `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD` | 장고 관리자 계정 기록 (7장) |
   | `SLACK_BOT_TOKEN`, `SLACK_CHANNEL` | 슬랙 알림 (7, 8장) |
   | `KIS_MODE` | `mock`(모의투자, 기본값) 또는 `real`(실전투자) |
   | `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO` | 한국투자증권 모의투자 |
   | `KIS_REAL_APP_KEY`, `KIS_REAL_APP_SECRET`, `KIS_REAL_ACCOUNT_NO` | 한국투자증권 실전투자 |

3. MySQL 설치 후 `INVESTAR` 데이터베이스를 만들고, `Investar\DBUpdaterEx.py`로
   시세를 채움 (아래 "시세 DB")

4. `.gitignore`에 `.env`, `config.json`, `.kis_token_*.json`, `logs/`가
   포함되어 있는지 확인. 파일명 오타(`.gitnore` 등)가 있으면 비밀번호와 키가
   GitHub에 올라갈 수 있으므로 특히 주의

## 시세 DB

5, 6, 9장은 직접 만든 MySQL 시세 DB를 사용합니다. 3, 4, 7, 8장은 인터넷에서
바로 받으므로 DB가 없어도 됩니다.

### 업데이트

```
cd C:\workspaces\quant\quant_실습\Investar
python DBUpdaterEx.py
```

1. KRX 상장 종목 목록을 받아 `company_info` 테이블에 저장
2. 종목마다 일별 시세를 FinanceDataReader로 받아 `daily_price` 테이블에 저장
3. 끝나면 `Waiting for next update ...`을 출력하고 다음 날 17시에 다시 실행

- 반드시 `Investar` 폴더에서 실행 (`config.json`을 실행 위치 기준으로 읽음)
- 수집 기간은 `config.json`의 `pages_to_fetch`로 조절 (1 = 10거래일).
  현재 25(약 250거래일)
- 종목이 2,700개 이상이라 30분~1시간 이상 걸림
- MySQL 서비스가 꺼져 있으면 `Can't connect to MySQL server` 오류가 남.
  윈도우 "서비스"에서 MySQL 서비스를 시작하고, 시작 유형을 "자동"으로 두면
  컴퓨터를 켤 때 같이 켜짐

업데이트 확인 (MySQL Workbench):

```sql
SELECT MAX(date) FROM daily_price;
```

### 조회

```python
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Investar import Analyzer

mk = Analyzer.MarketDB()
df = mk.get_daily_price('삼성전자', '2025-01-02')
```

맨 위 두 줄은 `ch5`, `ch6`, `ch9` 같은 하위 폴더에서 한 단계 위의 `Investar`
폴더를 불러오기 위한 것입니다.

## 자동 실행

| 대상 | 방식 | 시점 | 내용 |
|---|---|---|---|
| `run_dbupdater.bat` | 윈도우 로그인 시 실행 (레지스트리 Run 키) | 로그인할 때 | 시세 DB 업데이트 후 매일 17시 재실행 |
| `run_trader.bat` | 작업 스케줄러 `ETF_AutoTrade` | 평일 08:50 | 8장 자동매매 (09:05~15:15 감시, 15:15 매도 후 종료) |

- 로그인 시 실행 해제: 작업 관리자 → 시작프로그램 탭에서 `DBUpdater` 비활성화
- 작업 스케줄러 확인과 삭제: `schtasks /query /tn "ETF_AutoTrade"`,
  `schtasks /delete /tn "ETF_AutoTrade" /f`
- 컴퓨터는 "시스템 종료"가 아니라 "절전"으로 두고, 윈도우 절전 시간은 "안 함"
  (자세한 내용은 [ch8 README](ch8/README.md)의 "매일 자동 실행")
- 자동매매는 `.env`의 `KIS_MODE`를 따름. 실전으로 바꾸면 매일 실제 주문이
  나가므로, 실전 전환 전에 스케줄러를 먼저 끄고 판단

## 책 원본 대비 주요 수정 사항

### 데이터 출처

- 네이버 금융 시세 스크레이핑 → FinanceDataReader: `sise_day.nhn`,
  `sise.nhn` 페이지가 폐기되거나 구조가 바뀌어 동작하지 않음
  (`Investar\DBUpdater.py`, 4장, 7장 계좌 잔고)
- 야후 파이낸스: `pdr.get_data_yahoo()` 대신 `yf.download()`, `yf.Ticker()`
  사용. `auto_adjust` 기본값 변경으로 `Adj Close` 대신 `Close` 사용 (3, 5장).
  백트레이더의 `YahooFinanceData`도 동작하지 않아 FinanceDataReader +
  `PandasData`로 교체 (7장)
- 9장의 2018~2020년 데이터는 DB에 없어서 최근 기간으로 변경

### 라이브러리

- `slacker`(개발 중단) → `slack_sdk` (7, 8장)
- `mpl_finance`(지원 종료) → `mplfinance` 병행 (4, 6장)
- pandas 최신 문법: `fillna(method=...)` → `.bfill()`/`.ffill()`,
  `df.append()` 제거, 위치 인덱싱은 `.iloc`
- 케라스 3: `input_shape` 대신 `Input` 층 (9장)

### 증권사 API (8장)

- 대신증권 크레온 플러스(32비트 파이썬, 증권사 프로그램 로그인 필요) →
  한국투자증권 Open API (REST, 64비트 그대로, 모의투자 가능)
- 매수는 최유리 지정가 후 미체결 잔량 취소, 매도는 시장가
- 실전 계좌 주문은 `KIS_MODE=real`과 `KIS_REAL_ORDER=yes`가 모두 있어야 가능

### 보안

- 비밀번호, API 키, 토큰을 코드에 쓰지 않고 `.env`로 분리.
  `load_dotenv(find_dotenv())`로 실행 위치와 상관없이 `.env`를 찾음
- 한국투자증권 접근 토큰 파일(`.kis_token_*.json`)과 실행 로그(`logs/`)는
  git 추적 제외

### 버그 수정

- `config.json`이 없을 때 실제 사용 값과 저장 값이 달라, 다음 실행부터
  10일치만 받아오던 버그 수정
- `Investar\MarketDB.py`와 `Analyzer.py`에 서로 다른 버전의 `MarketDB`
  클래스가 있던 것을 최신 버전으로 통일
- `BIGINT(20)` → `BIGINT` (MySQL 8.0.19 이후 표시 폭 지정 지원 종료)

## 알아두면 좋은 점

- DB에는 2022-08-19 이후 시세만 있습니다. 더 과거가 필요하면
  `config.json`의 `pages_to_fetch`를 늘려 다시 받습니다.
- 장중에는 라이브러리를 새로 설치하거나 업그레이드하지 않습니다. 자동매매가
  같은 가상환경을 쓰기 때문입니다.
- 편집기에 파일을 열어 둔 상태에서 바깥(다른 프로그램)에서 그 파일이
  수정되면, 편집기에서 저장할 때 예전 내용으로 덮어써질 수 있습니다.
- MySQL Workbench에서 쿼리 결과가 일부만 보이면 툴바의 "Limit to N rows"를
  "Don't Limit"으로 바꿉니다.
- 이 저장소의 전략과 예측 코드는 책의 학습용 예제를 옮긴 것입니다. 지금
  시장에서 수익이 난다고 검증한 것이 아니므로 그대로 실전에 쓰지 않습니다.
