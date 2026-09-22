import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
import pandas as pd
import pymysql, calendar, time, json
import FinanceDataReader as fdr
from datetime import datetime, timedelta
from threading import Timer

class DBUpdater:
    def __init__(self):
        """생성자: MySQL 연결 및 종목코드 딕셔너리 생성"""
        self.conn = pymysql.connect(host='localhost', user='root',
            password=os.getenv('DB_PASSWORD'), db='INVESTAR', charset='utf8')

        with self.conn.cursor() as curs:
            sql = """
            CREATE TABLE IF NOT EXISTS company_info (
                code VARCHAR(20),
                company VARCHAR(40),
                last_update DATE,
                PRIMARY KEY (code))
            """
            curs.execute(sql)
            sql = """
            CREATE TABLE IF NOT EXISTS daily_price (
                code VARCHAR(20),
                date DATE,
                open BIGINT,
                high BIGINT,
                low BIGINT,
                close BIGINT,
                diff BIGINT,
                volume BIGINT,
                PRIMARY KEY (code, date))
            """
            curs.execute(sql)
        self.conn.commit()
        self.codes = dict()

    def __del__(self):
        """소멸자: MySQL 연결 해제"""
        self.conn.close()

    def read_krx_code(self):
        """KRX로부터 상장기업 목록 파일을 읽어와서 데이터프레임으로 반환"""
        url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method='\
            'download&searchType=13'
        krx = pd.read_html(url, header=0, encoding='euc-kr')[0]
        krx = krx[['종목코드', '회사명']]
        krx = krx.rename(columns={'종목코드': 'code', '회사명': 'company'})
        krx.code = krx.code.astype(str).str.zfill(6)
        return krx

    def update_comp_info(self):
        """종목코드를 company_info 테이블에 업데이트 한 후 딕셔너리에 저장"""
        sql = "SELECT * FROM company_info"
        df = pd.read_sql(sql, self.conn)
        for idx in range(len(df)):
            self.codes[df['code'].values[idx]] = df['company'].values[idx]

        with self.conn.cursor() as curs:
            sql = "SELECT max(last_update) FROM company_info"
            curs.execute(sql)
            rs = curs.fetchone()
            today = datetime.today().strftime('%Y-%m-%d')
            if rs[0] == None or rs[0].strftime('%Y-%m-%d') < today:
                krx = self.read_krx_code()
                for idx in range(len(krx)):
                    code = krx.code.values[idx]
                    company = krx.company.values[idx]
                    sql = f"REPLACE INTO company_info (code, company, last"\
                        f"_update) VALUES ('{code}', '{company}', '{today}')"
                    curs.execute(sql)
                    self.codes[code] = company
                    tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
                    print(f"[{tmnow}] #{idx+1:04d} REPLACE INTO company_info "\
                        f"VALUES ({code}, {company}, {today})")
                self.conn.commit()
                print('')

    def read_naver(self, code, company, pages_to_fetch):
        """FinanceDataReader로 시세를 읽어서 데이터프레임으로 반환
           (예전 네이버 스크래핑 대상이던 finance.naver.com/item/sise_day.nhn
            페이지는 네이버에서 폐기(HTTP 410/403)되어 더 이상 동작하지 않아 대체함)

           속도 최적화: 필요한 기간(start)만 요청해서 받아온다.
        """
        try:
            days_needed = pages_to_fetch * 10
            start_date = (datetime.today() -
                timedelta(days=int(days_needed * 1.6))).strftime('%Y-%m-%d')

            df = fdr.DataReader(code, start=start_date)
            if df is None or df.empty:
                return None
            df = df.tail(days_needed)
            df = df.reset_index()
            df = df.rename(columns={'Date': 'date', 'Open': 'open',
                'High': 'high', 'Low': 'low', 'Close': 'close',
                'Volume': 'volume'})
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            df['diff'] = df['close'].diff().abs().fillna(0)
            df = df.dropna()
            df[['close', 'diff', 'open', 'high', 'low', 'volume']] = df[[
                'close', 'diff', 'open', 'high', 'low', 'volume']].astype(int)
            df = df[['date', 'open', 'high', 'low', 'close', 'diff', 'volume']]
            tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
            print('[{}] {} ({}) : {}rows > read complete'.format(
                tmnow, company, code, len(df)))
        except Exception as e:
            print('Exception occured :', str(e))
            return None
        return df

    def replace_into_db(self, df, num, code, company):
        """읽어온 주식 시세를 DB에 REPLACE"""
        with self.conn.cursor() as curs:
            for r in df.itertuples():
                sql = f"REPLACE INTO daily_price VALUES ('{code}', "\
                    f"'{r.date}', {r.open}, {r.high}, {r.low}, {r.close}, "\
                    f"{r.diff}, {r.volume})"
                curs.execute(sql)
            self.conn.commit()
            print('[{}] #{:04d} {} ({}) : {} rows > REPLACE INTO daily_'\
                'price [OK]'.format(datetime.now().strftime('%Y-%m-%d'\
                ' %H:%M'), num+1, company, code, len(df)))

    def update_daily_price(self, pages_to_fetch):
        """KRX 상장법인의 주식 시세를 읽어서 DB에 업데이트"""
        for idx, code in enumerate(self.codes):
            df = self.read_naver(code, self.codes[code], pages_to_fetch)
            if df is None:
                continue
            self.replace_into_db(df, idx, code, self.codes[code])

    def execute_daily(self):
        """실행 즉시 및 매일 오후 다섯시에 daily_price 테이블 업데이트"""
        self.update_comp_info()

        try:
            with open('config.json', 'r') as in_file:
                config = json.load(in_file)
                pages_to_fetch = config['pages_to_fetch']
        except FileNotFoundError:
            # config.json이 없으면 기본값 100(약 4년치)으로 새로 만든다.
            # (예전 버전은 실제 사용하는 값(100)과 파일에 저장하는 값(1)이
            #  서로 달라서, 다음 실행 때 1페이지(10일치)만 받아오는
            #  버그가 있었음 - 두 값을 일치시켜 수정함)
            pages_to_fetch = 100
            config = {'pages_to_fetch': pages_to_fetch}
            with open('config.json', 'w') as out_file:
                json.dump(config, out_file)
        self.update_daily_price(pages_to_fetch)

        tmnow = datetime.now()
        lastday = calendar.monthrange(tmnow.year, tmnow.month)[1]
        if tmnow.month == 12 and tmnow.day == lastday:
            tmnext = tmnow.replace(year=tmnow.year+1, month=1, day=1,
                hour=17, minute=0, second=0)
        elif tmnow.day == lastday:
            tmnext = tmnow.replace(month=tmnow.month+1, day=1, hour=17,
                minute=0, second=0)
        else:
            tmnext = tmnow.replace(day=tmnow.day+1, hour=17, minute=0,
                second=0)
        tmdiff = tmnext - tmnow
        secs = tmdiff.seconds
        t = Timer(secs, self.execute_daily)
        print("Waiting for next update ({}) ... ".format(tmnext.strftime
            ('%Y-%m-%d %H:%M')))
        t.start()

if __name__ == '__main__':
    dbu = DBUpdater()
    dbu.execute_daily()