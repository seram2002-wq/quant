# ch5 — 시세 DB 구축 및 시세 조회 API 개발

5장 실습 기록입니다. MySQL에 시세 DB를 만들고, 저장된 시세를 조회해서
그래프로 그립니다. DB에 데이터를 채우고 조회하는 코드는 `Investar` 폴더에
있습니다 (루트 `README.md`의 "데이터 파이프라인 사용법" 참고).

## 파일 목록

| 파일 | 내용 |
|---|---|
| `5_1_1_samsung_yahoo.py` | 야후 파이낸스의 삼성전자 종가, 수정 종가, 거래량 |
| `5_1_2_samsung_investar_db.py` | 직접 만든 DB에서 읽은 삼성전자 종가와 거래량 |
| `5_2_mysql_connection_test.py` | MySQL 접속 테스트 |
| `5_3_create_tables.sql` | 테이블 생성과 조회 SQL |

## 준비

- MySQL이 로컬에 설치되어 실행 중이어야 함 (책은 MariaDB 기준이지만 MySQL 사용)
- `INVESTAR` 데이터베이스가 있어야 함
- `quant_실습\.env`에 `DB_PASSWORD`가 있어야 함 (git 추적 제외)

## 실행 방법

```
C:\workspaces\quant\quant.venv\Scripts\activate
cd C:\workspaces\quant\quant_실습\ch5
python 5_2_mysql_connection_test.py
```

## 5_1_1_samsung_yahoo.py — 야후 파이낸스 데이터의 한계 확인

삼성전자(`005930.KS`)의 2017년 이후 종가(`Close`)와 수정 종가
(`Adj Close`)를 위쪽에, 거래량을 아래쪽에 그립니다. 책은 이 그래프로
야후 파이낸스의 국내 주식 데이터에 오류가 있을 수 있다는 점을 보이고,
그래서 시세 DB를 직접 만드는 것으로 이어집니다.

`auto_adjust=False`를 지정한 이유는, 최신 `yfinance`의 기본값으로는
`Adj Close` 컬럼이 나오지 않기 때문입니다.

## 5_2_mysql_connection_test.py — MySQL 접속 테스트

`pymysql`로 로컬 MySQL의 `INVESTAR` DB에 접속해 버전을 출력합니다.
`MySQL version : ...`이 나오면 접속에 성공한 것입니다.

비밀번호는 코드에 쓰지 않고 `.env`의 `DB_PASSWORD`에서 읽습니다.
`load_dotenv(find_dotenv())`는 실행 위치와 상관없이 상위 폴더까지 올라가며
`.env`를 찾습니다.

## 5_3_create_tables.sql — 테이블 구조

MySQL Workbench 등에서 실행하는 SQL입니다.

| 테이블 | 내용 | 기본 키 |
|---|---|---|
| `company_info` | 종목코드, 회사명, 마지막 업데이트 날짜 | `code` |
| `daily_price` | 종목코드, 날짜, 시가, 고가, 저가, 종가, 전일비, 거래량 | `code`, `date` |

아래쪽에는 데이터 확인용 조회문이 있습니다 (전체 조회, 저장된 날짜 범위,
회사명 검색 등).

이 파일의 `BIGINT(20)`은 MySQL 8.0.19 이후 표시 폭 지정이 지원 종료되어
경고가 뜰 수 있습니다. `Investar\DBUpdater.py`가 테이블을 만들 때는
`BIGINT`로 정리되어 있습니다.

## 5_1_2_samsung_investar_db.py — 직접 만든 DB에서 조회

`Investar\Analyzer.py`의 `MarketDB` 클래스로 DB에 저장된 삼성전자 시세를
읽어 종가와 거래량을 그립니다. `5_1_1`과 같은 모양의 그래프를 직접 만든
DB의 데이터로 그리는 것입니다.

```python
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Investar import Analyzer
```

맨 위 두 줄은 `ch5` 폴더에서 한 단계 위(`quant_실습`)를 모듈 검색 경로에
추가해서 `Investar` 폴더를 불러올 수 있게 합니다. 6장의 파일들도 같은
방식을 씁니다.

DB에는 2022-08-19 이후 데이터만 있으므로 조회 기간을 그 안으로 잡아야
합니다. 먼저 `Investar\DBUpdaterEx.py`로 DB에 시세가 채워져 있어야 합니다.

## 책 원본 대비 수정 사항

- 책의 DB 업데이트 코드는 네이버 금융을 스크레이핑하지만, 해당 페이지가
  폐기되어 FinanceDataReader로 교체 (`Investar\DBUpdater.py`)
- 비밀번호 하드코딩 제거: `.env`와 `os.getenv('DB_PASSWORD')` 사용
- `yfinance`의 `auto_adjust` 기본값 변경에 대응
- 조회 기간을 실제 DB에 있는 날짜 범위로 변경
