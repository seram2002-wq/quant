import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from importlib import import_module
 
# 6_7.py가 있는 폴더를 모듈 검색 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from importlib import util as _util
 
spec = _util.spec_from_file_location(
    "dual_momentum",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "6_7.py"))
dual_momentum = _util.module_from_spec(spec)
spec.loader.exec_module(dual_momentum)
 
# 최근 6개월(형성기간) 동안 수익률 상위 10개 종목 = 상대 모멘텀
mom = dual_momentum.DualMomentum()
rltv = mom.get_rltv_momentum('2025-01-01', '2025-06-30', 10)
 
# 그 종목들을 형성기간 이후(2025-07-01 ~ 2025-12-31)에 들고 있었다면? = 절대 모멘텀
if rltv is not None:
    mom.get_abs_momentum(rltv, '2025-07-01', '2025-12-31')