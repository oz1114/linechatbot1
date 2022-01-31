from key import (
    line_bot_api, gameList,ansList
)
import json
import threading
from random import *
from time import sleep
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
from linebot.models import (TextSendMessage, FlexSendMessage, ImageSendMessage)

def quiz(self,title):
    self.nowAnswer = []
    #문제 선정 gameList[0] : 사자성어 이어말하기, 1:수도 맞히기, 2: 랜드마크 퀴즈
    q=''
    qimage = ''
    qlist = ansList[gameList.index(title)]
    t = randint(0,len(qlist)-1)
    targetMember = self.memberList[self.nowMem].display_name
    sec = 0
    if title==gameList[0] or title==gameList[1]:
        sentance = qlist[t].split()
        q = sentance[0]
        self.nowAnswer = sentance[1:]
        if title==gameList[0]:
            sec = 6
        else:
            sec = 7
    elif title==gameList[2]:
        temp = qlist[t].split()
        qimage = temp[-1]
        self.nowAnswer = temp[:-1]
        sec = 7
    #정답 출력용
    ans = ''
    for a in self.nowAnswer:
        ans += a +' '
        
    msg = flexMSGQ(title,targetMember,sec)
    message = FlexSendMessage(alt_text="Quiz", contents=json.loads(msg))
    line_bot_api.push_message(self.groupId, message)
    sleep(1)
    if title==gameList[2]:
        line_bot_api.push_message(self.groupId, ImageSendMessage(qimage,qimage))
        self.timerA = Timer1(self,ans,sec)
        self.timerA.start()
    msg = flexMSGS(q)
    message = FlexSendMessage(alt_text="Quiz", contents=json.loads(msg))
    line_bot_api.push_message(self.groupId, message)
    self.timerA = Timer1(self,ans,sec)
    self.timerA.start()

#큰 글씨체, 문제 제시용
def flexMSGS(sentance):
    msg="""
    {
  "type": "bubble",
  "body": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "text",
        "text": 
    """
    msg += "\""+sentance+"\","
    msg += """
            "weight": "bold",
        "size": "xxl"
      }
    ]
  }
}
    """
    return msg

#문제 종류 및 문제 풀 사람 확인용, 큰글씨
def flexMSGQ(title,user_name,t):
    msg = """
    {
  "type": "bubble",
  "body": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "text",
        "text": 
    """
    msg += "\""+title+"\","
    msg += """
        "weight": "bold",
        "size": "xl"
      },
      {
        "type": "text",
        "text": 
    """
    msg += "\""+user_name+"님 문제\","
    msg += """
        "weight": "bold",
        "size": "xl"
      },
      {
        "type": "text",
        "text": 
    """
    msg += "\"제한시간 "+str(t)+"초\","
    msg += """
        "size": "md",
        "color": "#999999",
        "margin": "md",
        "flex": 0
      }
    ]
  }
}
    """
    return msg

#문제 푸는 시간 재는 함수
class Timer1(threading.Thread):
    def __init__(self,gfunc,ans,t):
        threading.Thread.__init__(self)
        self.flag = threading.Event()
        self.gfunc = gfunc
        self.ans = ans
        self.t = t
    def run(self):
        while not self.flag.is_set() and self.t>0:
            sleep(1)
            self.t-=1
        if not self.flag.is_set() and self.t==0:
            self.gfunc.state = 1
            if self.gfunc.roundCounter>0:
                rc = str(self.gfunc.roundCounter)
                line_bot_api.push_message(self.groupId, TextSendMessage(text= '땡!!\n'
                +'정답은 ' +self.ans+' 입니다\n'
                +'총 ' + rc + ' 문제 연속 정답\n'
                +'게임시작 을 입력해주세요'))
                return
            line_bot_api.push_message(
                self.groupId,
                    TextSendMessage(text='땡!!\n'
                    +'정답은 ' + self.ans + ' 입니다\n'
                    +'게임시작 을 입력해주세요'))