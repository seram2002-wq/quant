import pandas as pd
#4.1.2 엑셀 파일
# krx_list =pd.read_html("C:\workspaces\quant\상장법인목록.xls")
# print(krx_list[0])

#URL 사용
df = pd.read_html(
    'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13',
    header=0,
    encoding='euc-kr'
)[0]
df['종목코드'] = df['종목코드'].astype(str).str.zfill(6)
df = df.sort_values(by='종목코드')
print(df)