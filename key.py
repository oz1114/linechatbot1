import os
import sys
from linebot import (
    LineBotApi, WebhookHandler
)
specialCAT = os.environ['specialCAT']
specialCS = os.environ['specialCS']

if specialCAT is None or specialCS is None:
    print('Specify LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN as environment variables.')
    sys.exit(1)

line_bot_api = LineBotApi(specialCAT)
handler = WebhookHandler(specialCS)

f1 = open('4WS.txt','r',encoding='euc-kr')
f2 = open('Capital.txt', 'rt', encoding='UTF8')
f3 = open('landMarkQuiz.txt','rt',encoding='UTF8')
f4 = open('LiarGame.txt','rt',encoding='UTF8')
ws4arr = f1.readlines()
capitals = f2.readlines()
lmq = f3.readlines()
liarGameList = f4.readlines()
f1.close()
f2.close()
f3.close()
f4.close()
ansList = [ws4arr,capitals,lmq]
gameList = ['사자성어 이어말하기','수도 맞히기','랜드마크 퀴즈']