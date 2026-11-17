import os
from dotenv import load_dotenv
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
import pymysql

connection = pymysql.connect(host='localhost', port=3306, db='INVESTAR',
    user='root', passwd=os.getenv('DB_PASSWORD'), autocommit=True)

cursor = connection.cursor()
cursor.execute("SELECT VERSION();")
result = cursor.fetchone()

print("MySQL version : {}".format(result))

connection.close()