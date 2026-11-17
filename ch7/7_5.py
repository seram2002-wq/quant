# 7.5 슬랙으로 알림 메시지 보내기
# 책 원본(ch07_07_Slack_SendMessage.py)은 slacker 라이브러리를 쓰지만,
# slacker는 개발이 중단되어 새로 만든 슬랙 앱에서는 동작하지 않으므로
# 슬랙 공식 라이브러리인 slack_sdk로 바꿈.
# 토큰은 코드에 직접 쓰지 않고 .env의 SLACK_BOT_TOKEN에서 읽음.
import os
from dotenv import load_dotenv, find_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv(find_dotenv())
token = os.getenv('SLACK_BOT_TOKEN')
channel = os.getenv('SLACK_CHANNEL', '#general')   # 메시지를 보낼 채널

if not token:
    raise SystemExit('.env 파일에 SLACK_BOT_TOKEN이 없습니다.')

client = WebClient(token=token)

markdown_text = '''
This message is plain.
*This message is bold.*
`This message is code.`
_This message is italic._
~This message is strike.~
'''

attach_dict = {
    'color'      : '#ff0000',
    'author_name': 'INVESTAR',
    'author_link': 'https://github.com/investar',
    'title'      : '오늘의 증시 KOSPI',
    'title_link' : 'https://finance.naver.com/sise/sise_index.naver?code=KOSPI',
    'text'       : '2,326.13 △11.89 (+0.51%)',     # 책의 예시 문구 (실제 지수 아님)
    'image_url'  : 'https://ssl.pstatic.net/imgstock/chart3/day/KOSPI.png'
}

attach_list = [attach_dict]

try:
    client.chat_postMessage(channel=channel, text=markdown_text,
                            attachments=attach_list)
    print(f'{channel} 채널로 메시지를 보냈습니다.')
except SlackApiError as e:
    print('전송 실패:', e.response['error'])
