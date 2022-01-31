from key import line_bot_api
from random import *
import json
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
from linebot.models import (
    TextSendMessage,FlexSendMessage
)

def mafiaButton(self):
    t_count = 0
    mafiaMessage = """
        {
  "type": "bubble",
  "header": {
    "type": "box",
    "layout": "vertical",
    "spacing": "sm",
    "contents": [
        """
    for prof in self.mafiaMember:
        if prof.user_id == self.liarMan:
            continue
        t_count+=1
        sampleContent = """{
        "type": "button",
        "style": "secondary",
        "height": "sm",
        "action": {
          "type": "postback",
          "label": 
        """
        sampleContent+="\""+prof.display_name+"\",\n\"data\":\""+"mafiakill "+self.groupId+' '+prof.user_id+"\"}},"
        mafiaMessage+=sampleContent
    mafiaMessage = mafiaMessage[:-1]
    mafiaMessage+="""
        ],
    "flex": 0
  }
}
        """
    if t_count<1:
        return
    message = FlexSendMessage(alt_text="선택하시오", contents=json.loads(mafiaMessage))
    line_bot_api.push_message(self.liarMan, message)

def mafiaStart(self):
    if len(self.memberList)<3:
        self.state=1
        return
    self.mafiaMember = self.memberList[:]
    shuffle(self.mafiaMember)
    self.nowMem = 0
    self.roundCounter = 1
    t = randint(0,len(self.mafiaMember)-1)
    self.liarMan = self.mafiaMember[t].user_id
    line_bot_api.push_message(self.mafiaMember[t].user_id,TextSendMessage(text = '당신은 마피아 입니다.'))
    line_bot_api.push_message(self.groupId,TextSendMessage(text = str(self.roundCounter)+'일차 낮입니다.'
    +'\n토론을 진행한 후 투표시작 을 입력해주세요'))
    self.roundCounter+=1

def mafiaVote(self,text,userId):
    i=0
    correct = False
    #채팅이 투표인가?
    for i in range(len(self.mafiaMember)):
        if self.mafiaMember[i].display_name==text:
            correct = True
            break
    #채팅이 투표이고 채팅을 친 사람이 투표를 하지 않았나?
    if correct and userId not in self.voted and userId in self.mafiaMember:
        self.voted.add(userId)
        self.votedCount[i] +=1
    #모든 사람이 투표하면
    if len(self.voted)==len(self.mafiaMember):
        self.state='mafiakill'
        i = self.votedCount.index(max(self.votedCount))
        if self.mafiaMember[i].user_id==self.liarMan:
            line_bot_api.push_message(self.groupId, TextSendMessage(text=self.mafiaMember[i].display_name
            +' 님은 마피아였습니다.\n시민의 승리!!'))
            self.state=1
        else:
            self.mafiaMember.remove(self.mafiaMember[i])
            if len(self.mafiaMember)<4:
                line_bot_api.push_message(self.groupId, TextSendMessage(text='마피아는 '
                +line_bot_api.get_profile(self.liarMan).display_name+' 님이었습니다.\n마피아의 승리!!'
                ))
                self.state=1
            else:
                line_bot_api.push_message(self.groupId, TextSendMessage(text=self.mafiaMember[i].display_name
                +' 님은 선량한 시민이었습니다...\n이제 마피아의 밤입니다.\n마피아는 처리할 대상을 선택해주세요.'))
                self.mafiaButton()