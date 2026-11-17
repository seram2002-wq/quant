"""한국투자증권(KIS) Open API 공용 모듈

책 8장은 대신증권 크레온 플러스(win32com, 32비트 파이썬)를 쓰지만,
여기서는 한국투자증권 REST API로 바꿔서 64비트 파이썬 그대로 사용한다.

.env (quant_실습\\.env)에 아래 값이 있어야 한다.
    KIS_MODE=mock                    mock(모의투자, 기본값) 또는 real(실전투자)

    KIS_APP_KEY=...                  모의투자 앱키
    KIS_APP_SECRET=...               모의투자 앱시크릿
    KIS_ACCOUNT_NO=12345678-01       모의투자 계좌번호(8자리-2자리)

    KIS_REAL_APP_KEY=...             실전투자 앱키
    KIS_REAL_APP_SECRET=...          실전투자 앱시크릿
    KIS_REAL_ACCOUNT_NO=12345678-01  실전투자 계좌번호

모의투자 값은 KIS_MOCK_APP_KEY처럼 MOCK을 붙인 이름으로 적어도 된다.
실전투자는 반드시 KIS_REAL_로 시작하는 값만 사용하므로, KIS_MODE를 real로
바꾸지 않는 한 실전 계좌로 주문이 나가지 않는다.

키, 시크릿, 토큰은 화면에 출력하지 않는다.
"""
import os
import re
import json
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# 모의투자와 실전투자는 접속 주소와 TR ID(거래 종류 코드)의 첫 글자만 다르다.
SERVERS = {
    'mock': {'url': 'https://openapivts.koreainvestment.com:29443',
             'tr_prefix': 'V', 'interval': 1.0, 'name': '모의투자'},
    'real': {'url': 'https://openapi.koreainvestment.com:9443',
             'tr_prefix': 'T', 'interval': 0.1, 'name': '실전투자'},
}


class KISError(Exception):
    """API가 실패 응답을 돌려줬을 때 발생시키는 예외"""


class KIS:
    def __init__(self):
        self.mode = (os.getenv('KIS_MODE') or 'mock').strip().lower()
        if self.mode not in SERVERS:
            raise KISError("KIS_MODE는 mock 또는 real이어야 합니다.")
        self.server = SERVERS[self.mode]
        self.base_url = self.server['url']
        self.app_key = self._env('APP_KEY')
        self.app_secret = self._env('APP_SECRET')

        account = self._env('ACCOUNT_NO')
        m = re.fullmatch(r'(\d{8})-?(\d{2})', account)
        if not m:
            raise KISError('계좌번호(ACCOUNT_NO)는 12345678-01처럼 '
                           '숫자 8자리-2자리 형식이어야 합니다.')
        self.cano, self.acnt_prdt_cd = m.group(1), m.group(2)

        # 토큰은 하루 동안 유효하고 자주 발급받으면 제한되므로 파일에 저장해 재사용한다.
        self.token_file = Path(__file__).parent / f'.kis_token_{self.mode}.json'
        self._token = None
        self._token_expires = 0.0
        self._last_call = 0.0

    def _env(self, name):
        """모드에 맞는 .env 값을 읽는다.

        real 모드: KIS_REAL_이름 만 사용 (모의투자 값으로 대신하지 않음)
        mock 모드: KIS_MOCK_이름, 없으면 KIS_이름
        """
        if self.mode == 'real':
            names = [f'KIS_REAL_{name}']
        else:
            names = [f'KIS_MOCK_{name}', f'KIS_{name}']
        for n in names:
            value = (os.getenv(n) or '').strip().strip('"').strip("'")
            if value:
                return value
        raise KISError(f'.env 파일에 {names[0]} 값이 없습니다.')

    # ------------------------------------------------------------ 인증
    def get_token(self):
        """접근 토큰을 돌려준다. 저장된 토큰이 유효하면 그것을 쓴다."""
        # 만료 10분 전까지만 기존 토큰을 쓰고, 그 뒤에는 새로 발급받는다.
        if self._token and self._token_expires > time.time() + 600:
            return self._token
        if self.token_file.exists():
            try:
                saved = json.loads(self.token_file.read_text(encoding='utf-8'))
                if saved.get('expires_at', 0) > time.time() + 600:
                    self._token = saved['access_token']
                    self._token_expires = saved['expires_at']
                    return self._token
            except (ValueError, KeyError):
                pass                                   # 파일이 깨졌으면 새로 발급

        res = requests.post(
            self.base_url + '/oauth2/tokenP',
            json={'grant_type': 'client_credentials',
                  'appkey': self.app_key, 'appsecret': self.app_secret},
            timeout=10)
        data = self._json(res)
        if 'access_token' not in data:
            raise KISError('토큰 발급 실패: '
                           f"{data.get('error_code', res.status_code)} "
                           f"{data.get('error_description', '')}")
        self._token = data['access_token']
        self._token_expires = time.time() + int(data.get('expires_in', 86400))
        self.token_file.write_text(json.dumps({
            'access_token': self._token,
            'expires_at': self._token_expires,
        }), encoding='utf-8')
        return self._token

    # ------------------------------------------------------------ 공통 호출
    @staticmethod
    def _json(res):
        try:
            return res.json()
        except ValueError:
            raise KISError(f'응답을 해석할 수 없습니다 (HTTP {res.status_code})')

    def _headers(self, tr_id):
        return {
            'content-type': 'application/json; charset=utf-8',
            'authorization': 'Bearer ' + self.get_token(),
            'appkey': self.app_key,
            'appsecret': self.app_secret,
            'tr_id': tr_id,
            'custtype': 'P',                           # 개인
        }

    def _wait(self):
        """호출 제한에 걸리지 않도록, 직전 응답을 받은 뒤 일정 시간 기다린다."""
        gap = self.server['interval'] - (time.time() - self._last_call)
        if gap > 0:
            time.sleep(gap)

    def _call(self, send):
        """요청을 보내고 결과를 돌려준다.

        호출 제한(EGW00201 초당 거래건수 초과)에 걸리면 잠시 쉬고 다시 시도한다.
        이 오류는 서버가 요청을 처리하지 않고 돌려보낸 것이라 다시 보내도 안전하다.
        """
        for attempt in range(4):
            self._wait()
            try:
                res = send()
            finally:
                self._last_call = time.time()
            data = self._json(res)
            if data.get('rt_cd') == '0':               # '0'이 정상
                return data
            if data.get('msg_cd') == 'EGW00201' and attempt < 3:
                time.sleep(1.5 * (attempt + 1))        # 1.5초, 3초, 4.5초
                continue
            raise KISError(f"{data.get('msg_cd', res.status_code)} "
                           f"{data.get('msg1', '').strip()}")

    def _get(self, path, tr_id, params):
        headers = self._headers(tr_id)
        return self._call(lambda: requests.get(
            self.base_url + path, headers=headers, params=params, timeout=10))

    def _post(self, path, tr_id, body):
        headers = self._headers(tr_id)
        return self._call(lambda: requests.post(
            self.base_url + path, headers=headers,
            data=json.dumps(body), timeout=10))

    # ------------------------------------------------------------ 조회
    def get_price(self, code):
        """종목의 현재가 정보를 딕셔너리로 돌려준다."""
        data = self._get(
            '/uapi/domestic-stock/v1/quotations/inquire-price',
            'FHKST01010100',                           # 시세 조회는 모의/실전 TR ID가 같다
            {'FID_COND_MRKT_DIV_CODE': 'J', 'FID_INPUT_ISCD': code})
        out = data['output']
        return {
            'code': code,
            'price': int(out['stck_prpr']),            # 현재가
            'open': int(out['stck_oprc']),             # 시가
            'high': int(out['stck_hgpr']),             # 고가
            'low': int(out['stck_lwpr']),              # 저가
            'rate': float(out['prdy_ctrt']),           # 전일 대비 등락률(%)
        }

    def get_ohlc(self, code):
        """최근 약 30거래일의 일별 시세를 최신 날짜부터 리스트로 돌려준다."""
        data = self._get(
            '/uapi/domestic-stock/v1/quotations/inquire-daily-price',
            'FHKST01010400',
            {'FID_COND_MRKT_DIV_CODE': 'J', 'FID_INPUT_ISCD': code,
             'FID_PERIOD_DIV_CODE': 'D', 'FID_ORG_ADJ_PRC': '0'})
        rows = []
        for r in data.get('output', []):
            if not r.get('stck_bsop_date'):
                continue
            rows.append({
                'date': r['stck_bsop_date'],           # 'YYYYMMDD'
                'open': int(r['stck_oprc']), 'high': int(r['stck_hgpr']),
                'low': int(r['stck_lwpr']), 'close': int(r['stck_clpr']),
            })
        rows.sort(key=lambda x: x['date'], reverse=True)
        return rows

    def get_balance(self):
        """계좌 잔고를 돌려준다: (요약 딕셔너리, 보유 종목 리스트)"""
        data = self._get(
            '/uapi/domestic-stock/v1/trading/inquire-balance',
            self.server['tr_prefix'] + 'TTC8434R',     # 모의 VTTC8434R / 실전 TTTC8434R
            {'CANO': self.cano, 'ACNT_PRDT_CD': self.acnt_prdt_cd,
             'AFHR_FLPR_YN': 'N', 'OFL_YN': '', 'INQR_DVSN': '02',
             'UNPR_DVSN': '01', 'FUND_STTL_ICLD_YN': 'N',
             'FNCG_AMT_AUTO_RDPT_YN': 'N', 'PRCS_DVSN': '01',
             'CTX_AREA_FK100': '', 'CTX_AREA_NK100': ''})

        def num(d, key):
            try:
                return int(float(d.get(key) or 0))
            except ValueError:
                return 0

        stocks = []
        for row in data.get('output1', []):
            qty = num(row, 'hldg_qty')
            if qty == 0:
                continue
            stocks.append({
                'code': row.get('pdno'), 'name': row.get('prdt_name'),
                'qty': qty,                            # 보유 수량
                'sellable': num(row, 'ord_psbl_qty'),  # 매도 가능 수량
                'avg_price': num(row, 'pchs_avg_pric'),  # 매입 평균가
                'price': num(row, 'prpr'),             # 현재가
                'profit': num(row, 'evlu_pfls_amt'),   # 평가손익
            })
        out2 = data.get('output2') or [{}]
        out2 = out2[0] if isinstance(out2, list) else out2
        summary = {
            'cash': num(out2, 'dnca_tot_amt'),         # 예수금
            'cash_d2': num(out2, 'prvs_rcdl_excc_amt'),  # D+2 예수금
            'total': num(out2, 'tot_evlu_amt'),        # 총 평가금액
        }
        return summary, stocks

    def get_buyable_cash(self, code='069500'):
        """지금 주문에 쓸 수 있는 현금(미수 없이 살 수 있는 금액)을 돌려준다.

        잔고의 예수금은 결제(D+2) 기준이라 오늘 사고판 금액이 반영되지 않는다.
        이 값은 오늘 매수한 금액이 빠지고 매도한 금액이 더해진 실제 사용 가능 금액이다.
        """
        data = self._get(
            '/uapi/domestic-stock/v1/trading/inquire-psbl-order',
            self.server['tr_prefix'] + 'TTC8908R',     # 모의 VTTC8908R / 실전 TTTC8908R
            {'CANO': self.cano, 'ACNT_PRDT_CD': self.acnt_prdt_cd,
             'PDNO': code, 'ORD_UNPR': '', 'ORD_DVSN': '01',
             'CMA_EVLU_AMT_ICLD_YN': 'N', 'OVRS_ICLD_YN': 'N'})
        out = data.get('output') or {}
        for key in ('nrcvb_buy_amt', 'ord_psbl_cash'):  # 미수없는매수금액, 주문가능현금
            try:
                return int(float(out[key]))
            except (KeyError, TypeError, ValueError):
                continue
        raise KISError('주문 가능 금액을 응답에서 찾지 못했습니다.')

    # ------------------------------------------------------------ 주문
    def _order(self, side, code, qty, price):
        """현금 주문을 넣고 주문번호를 돌려준다. price가 0이면 시장가 주문."""
        qty, price = int(qty), int(price)
        if qty <= 0:
            raise KISError('주문 수량은 1 이상이어야 합니다.')
        # 실전 계좌는 .env에 KIS_REAL_ORDER=yes가 있을 때만 주문을 허용한다.
        if self.mode == 'real' and \
                (os.getenv('KIS_REAL_ORDER') or '').strip().lower() != 'yes':
            raise KISError('실전 계좌 주문이 잠겨 있습니다. '
                           '(.env에 KIS_REAL_ORDER=yes가 있어야 주문 가능)')
        # 모의 VTTC0012U(매수) / VTTC0011U(매도), 실전은 첫 글자가 T
        tr_id = self.server['tr_prefix'] + \
            ('TTC0012U' if side == 'buy' else 'TTC0011U')
        body = {
            'CANO': self.cano, 'ACNT_PRDT_CD': self.acnt_prdt_cd,
            'PDNO': code,
            'ORD_DVSN': '01' if price == 0 else '00',  # 01 시장가, 00 지정가
            'ORD_QTY': str(qty),
            'ORD_UNPR': str(price),                    # 시장가는 0
            'EXCG_ID_DVSN_CD': 'KRX',                  # 한국거래소
        }
        if side == 'sell':
            body['SLL_TYPE'] = '01'                    # 일반 매도
        data = self._post('/uapi/domestic-stock/v1/trading/order-cash',
                          tr_id, body)
        out = data.get('output') or {}
        return {'order_no': out.get('ODNO'), 'time': out.get('ORD_TMD'),
                'message': data.get('msg1', '').strip()}

    def buy(self, code, qty, price=0):
        """매수 주문. price를 생략하면 시장가."""
        return self._order('buy', code, qty, price)

    def sell(self, code, qty, price=0):
        """매도 주문. price를 생략하면 시장가."""
        return self._order('sell', code, qty, price)


def now():
    return datetime.now().strftime('[%m/%d %H:%M:%S]')
