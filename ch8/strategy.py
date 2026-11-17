"""변동성 돌파 전략 계산 (책 8장의 get_target_price, get_movingaverage에 해당)

변동성 돌파 전략: 오늘 주가가 "오늘 시가 + 어제 변동폭(고가-저가) × K"를
넘어서면 상승 추세로 보고 매수하고, 장 마감 전에 전부 판다.
책과 같이 K=0.5를 쓰고, 현재가가 5일·10일 이동평균보다 위일 때만 매수한다.
"""
from datetime import datetime

K = 0.5                                                # 변동폭에 곱하는 비율


def analyze(kis, code, today=None):
    """종목의 목표가와 이동평균을 계산해 딕셔너리로 돌려준다.

    오늘 시세가 아직 없으면(장 시작 전, 휴장일) None을 돌려준다.
    """
    today = today or datetime.now().strftime('%Y%m%d')
    rows = kis.get_ohlc(code)                          # 최신 날짜가 맨 앞
    if len(rows) < 11 or rows[0]['date'] != today:
        return None
    today_row, prev = rows[0], rows[1:]                # 오늘 / 어제 이전
    lastday = prev[0]
    target = today_row['open'] + (lastday['high'] - lastday['low']) * K
    ma5 = sum(r['close'] for r in prev[:5]) / 5        # 어제까지의 5일 이동평균
    ma10 = sum(r['close'] for r in prev[:10]) / 10     # 어제까지의 10일 이동평균
    return {
        'code': code,
        'open': today_row['open'],                     # 오늘 시가
        'last_high': lastday['high'],                  # 어제 고가
        'last_low': lastday['low'],                    # 어제 저가
        'target': target,                              # 매수 목표가
        'ma5': ma5, 'ma10': ma10,
    }


def is_buy_signal(info, price):
    """현재가가 목표가와 5일·10일 이동평균을 모두 넘으면 True"""
    return price > info['target'] and price > info['ma5'] and price > info['ma10']
