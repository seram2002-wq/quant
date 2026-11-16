# ch7 — 장고(Django) 웹 서버 실습

7장 실습 기록입니다. 장고 프로젝트 자체는 이 저장소 밖인 `C:\mySite\Investar`에
있고, 가상환경은 다른 장과 같은 `C:\workspaces\quant\quant.venv`를 사용합니다.

## 환경

- Django 5.2.17 (`quant.venv`에 설치)
- 프로젝트 위치: `C:\mySite\Investar`
- 앱: `hello` (`settings.py`의 `INSTALLED_APPS`에 등록)

```
C:\mySite\Investar\
├── manage.py
├── db.sqlite3
├── Investar\        # 프로젝트 설정 (settings.py, urls.py 등)
└── hello\           # Hello 앱 (views.py의 sayHello)
```

## 서버 실행 방법

```
C:\workspaces\quant\quant.venv\Scripts\activate
cd C:\mySite\Investar
python manage.py runserver
```

프롬프트 앞에 `(quant.venv)`가 붙어 있는지 확인한 뒤 실행합니다.
정상적으로 뜨면 아래처럼 나옵니다.

```
System check identified no issues (0 silenced).
Django version 5.2.17, using settings 'Investar.settings'
Starting development server at http://127.0.0.1:8000/
```

서버를 끄려면 터미널에서 `Ctrl+C`를 누릅니다. 마지막의
`WARNING: This is a development server...`는 개발용 서버라는 안내라서 무시해도 됩니다.

## 접속 주소

`Investar/urls.py`가 대문자로 시작하는 영문 이름만 받도록 되어 있습니다.

```python
re_path(r'^(?P<name>[A-Z][a-z]*)$', views.sayHello),
```

- `http://127.0.0.1:8000/Seram` → "Hello, Seram!" 출력
- `http://127.0.0.1:8000/` → 404 (루트 주소를 연결하지 않았으므로 정상)
- `http://127.0.0.1:8000/admin/` → 장고 관리자 페이지

## 겪은 문제와 해결 (2026-11-16)

### 1. 서버가 안 열림 — 가상환경에 Django가 없었음

`quant.venv`에 Django가 설치되어 있지 않아 `runserver`가 실행되지 않았습니다.
가상환경을 켠 상태에서 프로젝트를 만들 때 쓴 버전과 같은 버전을 설치해서 해결했습니다.

```
pip install django==5.2.17
```

### 2. Investar 폴더가 두 개 — 철자가 다른 오타 프로젝트

`C:\mySite` 안에 `Investar`(a)와 `Invester`(e)가 같이 있었습니다.
`Invester`는 `django-admin startproject` 때 이름을 잘못 입력해서 생긴 빈
프로젝트(`hello` 앱 없음)라서 삭제했고, 지금은 `Investar`만 남아 있습니다.
오타 폴더에서 서버를 띄우면 `/Seram` 같은 주소도 404가 나므로, 반드시
`C:\mySite\Investar`에서 실행합니다.

### 3. 가상환경이 실습 폴더 밖에 있어도 되는가

됩니다. 가상환경은 위치가 아니라 활성화 여부만 중요해서, 한 번 활성화하면
그 터미널에서는 어느 폴더로 이동해도 같은 파이썬과 패키지를 씁니다.

- 새 터미널을 열 때마다 `activate`를 다시 실행해야 합니다.
- VS Code에서 `quant_실습` 폴더만 열면 가상환경을 못 찾을 수 있으니,
  `Ctrl+Shift+P` → "Python: Select Interpreter"에서
  `C:\workspaces\quant\quant.venv\Scripts\python.exe`를 지정합니다.
- 가상환경 폴더는 옮기거나 이름을 바꾸면 깨지므로 그대로 둡니다.

### 4. `startapp hello`가 CommandError — 이미 만든 앱

```
CommandError: 'hello' conflicts with the name of an existing Python module
and cannot be used as an app name.
```

`hello` 앱을 9월 29일에 이미 만들어 두었기 때문에 나오는 메시지입니다.
같은 이름으로 다시 만들 수 없을 뿐 문제는 아니므로, 이 단계는 건너뜁니다.

## 진행 상황 (2026-11-16 기준)

| 단계 | 상태 | 비고 |
|---|---|---|
| 장고 설치, `Investar` 프로젝트 생성 | 완료 | `C:\mySite\Investar` |
| `migrate`, 서버 실행 | 완료 | 마이그레이션 18건 적용, `runserver` 성공 |
| `hello` 앱 생성 및 등록 | 완료 | `INSTALLED_APPS`에 `'hello'` |
| `urls.py` 연결, `sayHello` 뷰 | 완료 | `/Seram` → "Hello, Seram!" |
| 관리자 페이지 (`createsuperuser`) | 완료 | `/admin/` 로그인 확인 |
| 인덱스 페이지 (`index` 앱, 템플릿, CSS) | 완료 | `/index/` 접속 확인 |
| 계좌 잔고 확인 (`balance` 앱) | 아직 | |
| 슬랙 알림 메시지 | 아직 | |
| 백트레이더 백테스트 | 아직 | |

## 관리자 페이지

관리자 계정을 만든 뒤 `/admin/`으로 로그인합니다. `migrate`는 이미 되어
있으므로 다시 할 필요가 없습니다.

```
cd C:\mySite\Investar
python manage.py createsuperuser
python manage.py runserver
```

- `createsuperuser`는 Username, Email(비워도 됨), Password를 차례로 묻습니다.
  비밀번호는 입력해도 화면에 표시되지 않는 것이 정상입니다.
- 접속 주소: `http://127.0.0.1:8000/admin/`
- 계정 정보는 `db.sqlite3`에 저장되며, 비밀번호는 README나 코드에 적지 않습니다.

## 인덱스 페이지

`index` 앱을 만들어 템플릿(HTML)과 정적 파일(CSS, 이미지)을 연결했습니다.

```
index\
├── views.py                  # main_view: render(request, 'index.html')
├── templates\index.html      # 책 예제 ch07_02_index.html
└── static\index\
    ├── style.css             # 책 예제 ch07_03_style.css
    └── Django_Logo.jpg
```

- `settings.py`의 `INSTALLED_APPS`에 `'index'` 추가
- `urls.py`에 `from index import views as index_views`와
  `path('index/', index_views.main_view)` 추가
- 접속 주소: `http://127.0.0.1:8000/index/`

### 겪은 문제: `TemplateDoesNotExist at /index/`

파일과 설정이 모두 맞는데도 에러가 났습니다. 예전에 띄운 서버 프로세스가
남아서 8000번 포트 요청을 받고 있었던 것으로 보이며(그 서버는 `templates`
폴더가 생기기 전에 시작되어 폴더를 모름), 남은 프로세스를 정리하고 서버를
다시 띄워 해결했습니다.

```
netstat -ano | findstr :8000
taskkill /F /PID 숫자
python manage.py runserver
```

`templates`나 `static` 폴더를 새로 만든 뒤에는 서버를 완전히 껐다가 다시 켭니다.

## 서버 끄기와 다시 시작하기

- 끄기: 서버를 띄운 터미널에서 `Ctrl+C` 후 터미널 창을 닫습니다.
  파일과 `db.sqlite3`는 그대로 남으므로 따로 저장할 것은 없습니다.
- 다시 시작: 위 "서버 실행 방법"의 세 줄(`activate` → `cd` → `runserver`)을
  그대로 실행합니다.

## 다음에 할 일

- 계좌 잔고 확인 (`balance` 앱): 책 예제 `ch07_04_balance_views.py`,
  `ch07_05_balance.html`, `ch07_06_b_style.css`
- 슬랙 알림 메시지: `ch07_07_Slack_SendMessage.py`
- 백트레이더 백테스트: `ch07_08_Backtrader_RSI.py`, `ch07_09_Backtrader_RSI_SMA.py`
