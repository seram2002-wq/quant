# quant_실습 — 파이썬 증권 데이터 분석 실습

『파이썬 증권 데이터 분석』(Investar) 책을 따라가며 진행한 실습 프로젝트입니다.
책이 출간된 시점 이후 네이버 금융 시세 페이지가 폐기되는 등 원본 코드가 그대로
동작하지 않는 부분이 많아, 최신 파이썬/라이브러리 버전에 맞게 여러 곳을 수정했습니다.

## 개발 환경

- Python 가상환경: `quant.venv` (venv)
- IDE: VS Code
- DB: MySQL 8.0.17 (로컬 설치, MariaDB 아님 — 책은 MariaDB 기준이지만 `pymysql`은
  기본적인 SQL 작업에서는 둘 다 동일하게 동작하여 그대로 MySQL 사용)
- Git 관리 도구: Sourcetree
- 원격 저장소: GitHub (`seram2002-wq/quant`)

## 폴더 구조

```
quant_실습/
├── ch3/            # 3장: pandas/matplotlib 기초, 지수 비교
├── ch4/            # 4장: KRX 종목 목록 수집
├── ch5/            # 5장: MySQL 연동, DB 저장/조회
├── ch6/            # 6장: 포트폴리오 분석 (Efficient Frontier 등)
├── ch7/            # 7장: 장고 웹 서버 실습 기록 (프로젝트는 C:\mySite\Investar)
├── ch8/            # 8장: 변동성 돌파 전략 (한국투자증권 모의투자)
├── Investar/       # 공용 모듈 패키지
│   ├── Analyzer.py       # MarketDB 클래스 (DB 조회 전용)
│   ├── MarketDB.py       # Analyzer.py와 동일 내용으로 동기화한 조회 모듈
│   ├── DBUpdater.py      # KRX 종목 + 일별 시세 수집/DB 적재
│   ├── DBUpdaterEx.py    # DBUpdater와 동일, 자동 실행용
│   └── config.json       # { "pages_to_fetch": 100 } 등 수집 설정
├── run_dbupdater.bat     # DBUpdaterEx.py를 Investar 폴더 기준으로 실행하는 배치파일
├── .env                  # DB_PASSWORD 등 민감 정보 (git 추적 제외)
├── .gitignore
└── requirements.txt
```

## 초기 설정

1. 가상환경 활성화 후 의존성 설치

   ```
   pip install -r requirements.txt
   ```

2. 프로젝트 루트에 `.env` 파일 생성 (git에 올리지 않음)

   ```
   DB_PASSWORD=본인의_MySQL_비밀번호
   ```

3. `.gitignore`에 `.env`, `config.json`이 반드시 포함되어 있는지 확인
   (파일명 오타 — `.gitnore`처럼 잘못 저장되면 비밀번호가 그대로 GitHub에
   올라갈 수 있으므로 특히 주의)

## 데이터 파이프라인 사용법

`Investar/DBUpdaterEx.py`를 실행하면:

1. KRX 상장 종목 목록을 받아와 `company_info` 테이블에 저장
2. 각 종목의 일별 시세를 FinanceDataReader로 받아와 `daily_price` 테이블에 저장
3. 실행 즉시 1회 업데이트 후, 다음날 오후 5시에 자동으로 재실행되도록 예약

```
cd Investar
python DBUpdaterEx.py
```

수집 기간은 `Investar/config.json`의 `pages_to_fetch` 값으로 조절합니다
(1페이지 = 10거래일). 현재 100(약 4년치)으로 설정되어 있으며, 이 값을 바꾸면
다음 실행부터 반영됩니다.

### Windows 로그인 시 자동 실행

`run_dbupdater.bat`을 Windows 레지스트리
(`HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`)에 등록해
두어, 로그인할 때마다 자동으로 `DBUpdaterEx.py`가 실행됩니다. 더 이상
필요 없어지면 작업 관리자 → 시작프로그램 탭에서 `DBUpdater` 항목을
비활성화하거나, 레지스트리에서 해당 값을 삭제하면 됩니다.

### DB에서 시세 조회

`Investar/Analyzer.py`의 `MarketDB` 클래스로 저장된 시세를 조회합니다.

```python
from Investar import Analyzer
mk = Analyzer.MarketDB()
df = mk.get_daily_price('삼성전자', '2022-08-19', '2026-09-22')
```

`Investar` 폴더 밖(`ch3`~`ch6`)에서 이 모듈을 import하려면, 스크립트 맨 위에
아래 코드를 추가해야 합니다.

```python
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

## 책 원본 대비 주요 수정 사항

- **네이버 시세 스크래핑 → FinanceDataReader**: `finance.naver.com/item/sise_day.nhn`
  페이지가 네이버에서 폐기(HTTP 410/403)되어 더 이상 동작하지 않아,
  `fdr.DataReader()`로 전면 교체
- **비밀번호 하드코딩 제거**: `password='...'`를 코드에 직접 쓰지 않고
  `.env` + `os.getenv('DB_PASSWORD')`로 분리 (GitHub 업로드 대비)
- **`.env` 탐색 안정화**: `load_dotenv()` 대신 `load_dotenv(find_dotenv())`
  사용 — 실행 위치(cwd)가 달라도 상위 폴더까지 자동으로 `.env`를 찾음
- **pandas 최신 문법 대응**: `fillna(method=...)` → `.bfill()`/`.ffill()`,
  `df.append()` 제거, `read_html(encoding='euc-kr')` 명시, 종목코드는
  `.astype(str).str.zfill(6)`으로 처리
- **yfinance 대응**: `auto_adjust` 기본값 변경으로 `Adj Close` 대신 `Close` 사용
- **`config.json` 기록 버그 수정**: 파일이 없을 때 실제 사용 값(100)과 저장
  값(기존엔 1)이 서로 달라, 다음 실행부터 조용히 10일치만 받아오던 버그를
  두 값을 일치시켜 수정
- **`Investar/MarketDB.py`와 `Analyzer.py` 동기화**: 두 파일에 서로 다른
  버전의 `MarketDB` 클래스가 있던 것을 최신 버전(날짜 검증, 존재하지 않는
  종목 코드 처리, snake_case 메서드명)으로 통일
- **`BIGINT(20)` → `BIGINT`**: MySQL 8.0.19+에서 표시 폭 지정이
  지원 종료(deprecated)되어 경고가 뜨는 부분 정리

## 알아두면 좋은 점

- DB에는 `daily_price` 기준 **2022-08-19 ~ 현재**까지의 데이터만 있습니다
  (책 예제의 2016~2018년 데이터는 DB에 없으므로, 해당 구간을 조회하면
  빈 결과가 나옵니다). 필요하면 `config.json`의 `pages_to_fetch`를 늘려
  더 과거 데이터를 받아오면 됩니다.
- `config.json`은 스크립트 실행 시점의 현재 작업 디렉터리(cwd) 기준
  상대경로로 열리므로, 반드시 `Investar` 폴더를 기준으로 실행해야
  의도한 설정 파일을 읽습니다.
- MySQL Workbench에서 쿼리 결과가 10개로 제한되어 보인다면, 툴바의
  "Limit to N rows" 드롭다운을 "Don't Limit"으로 바꾸면 됩니다.
