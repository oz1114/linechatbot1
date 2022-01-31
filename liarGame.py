from key import (
    line_bot_api, liarGameList
    )
from random import *
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
from linebot.models import TextSendMessage

def LiarGame(self):
    self.nowAnswer = []
    t = randint(0,len(liarGameList)-1)
    temp = liarGameList[t].split()
    liarGameCategory = temp[0]
    t = randint(1,len(temp)-1)
    self.nowAnswer = temp[t:t+1]
    liar = randint(0,len(self.memberList)-1)
    talkOrder = ''
    for i in range(len(self.memberList)):
        talkOrder += self.memberList[i].display_name + ' '
        if i==liar:
            line_bot_api.push_message(self.memberList[i].user_id,TextSendMessage(text = '당신은 거짓말쟁이 입니다.'))
            self.liarMan = self.memberList[i].user_id
        else:
            line_bot_api.push_message(self.memberList[i].user_id,TextSendMessage(text = self.nowAnswer[0]))
    line_bot_api.push_message(self.groupId, TextSendMessage(text= '카테고리는 '+liarGameCategory
    +'\n순서대로 정답에 관해 설명해주시면 됩니다.\n순서는 '+talkOrder+'\n첫번째 설명 시작!'))

def liarVote(self,text,userId):
    i = 0
    correct = False
    #채팅 내용이 투표인가?
    for i in range(len(self.memberList)):
        if self.memberList[i].display_name==text:
            correct = True
            break
    #채팅 내용이 투표이고 채팅을 친 사람이 투표를 아직 하지 않은경우
    if correct and userId not in self.voted and userId in self.memberList:
        self.voted.add(userId)
        self.votedCount[i] +=1
    #투표가 완료된 경우
    if len(self.voted) == len(self.memberList):
        self.state='wait'
        i = self.votedCount.index(max(self.votedCount))
        if self.memberList[i].user_id==self.liarMan:
            self.state='liarspeak'
            line_bot_api.push_message(self.groupId, TextSendMessage(text='거짓말쟁이를 맞추셨습니다.\n거짓말쟁이는'
            +self.memberList[i].display_name+'\n거짓말쟁이는 정답을 말해주세요'))
        else:
            line_bot_api.push_message(self.groupId, TextSendMessage(text=self.memberList[i].display_name +'는 거짓말쟁이가 아니었습니다\n'
            +'거짓말쟁이는 '+ line_bot_api.get_profile(self.liarMan).display_name
            +'\n거짓말쟁이의 승리!!\n정답은 '+self.nowAnswer[0]))
            self.state=1