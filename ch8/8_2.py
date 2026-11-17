# 8.2 변동성 돌파 전략의 매수 목표가 계산 (주문은 하지 않는다)
# ETF별로 오늘 시가, 어제 변동폭, 목표가, 이동평균, 현재가를 구해
# 지금 매수 조건을 만족하는지만 출력한다.
from kis import KIS, KISError
from strategy import analyze, is_buy_signal, K

# 매매 대상 ETF (종목코드: 이름). 원하는 종목으로 바꿔도 된다.
SYMBOLS = {
    '069500': 'KODEX 200',
    '102110': 'TIGER 200',
    '229200': 'KODEX 코스닥150',
    '133690': 'TIGER 미국나스닥100',
    '360750': 'TIGER 미국S&P500',
}

try:
    kis = KIS()
    print(f'접속 대상 : {kis.server["name"]}   (K = {K})')
    for code, name in SYMBOLS.items():
        info = analyze(kis, code)
        if info is None:
            print(f'{name}({code}) : 오늘 시세가 아직 없습니다 (장 시작 전이거나 휴장일).')
            continue
        price = kis.get_price(code)['price']
        signal = '매수 조건 충족' if is_buy_signal(info, price) else '대기'
        print(f'{name}({code})')
        print(f'   오늘 시가 {info["open"]:,} + (어제 고가 {info["last_high"]:,}'
              f' - 어제 저가 {info["last_low"]:,}) × {K} = 목표가 {info["target"]:,.0f}')
        print(f'   5일선 {info["ma5"]:,.0f}, 10일선 {info["ma10"]:,.0f}, '
              f'현재가 {price:,}  →  {signal}')
except KISError as e:
    print('실패:', e)
