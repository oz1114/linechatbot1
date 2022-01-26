# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.


import datetime
import errno
import json
import os
from stat import FILE_ATTRIBUTE_TEMPORARY
import sys
import tempfile
import threading
from argparse import ArgumentParser
from random import *

from flask import Flask, request, abort, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageAction,
    ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URIAction,
    PostbackAction, DatetimePickerAction,
    CameraAction, CameraRollAction, LocationAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage, FileMessage,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent,
    MemberJoinedEvent, MemberLeftEvent,
    FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent,
    TextComponent, IconComponent, ButtonComponent,
    SeparatorComponent, QuickReply, QuickReplyButton,
    ImageSendMessage)

from time import sleep

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)

# get channel_secret and channel_access_token from your environment variable
specialCAT = os.environ['specialCAT']
specialCS = os.environ['specialCS']
if specialCAT is None or specialCS is None:
    print('Specify LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN as environment variables.')
    sys.exit(1)

line_bot_api = LineBotApi(specialCAT)
handler = WebhookHandler(specialCS)

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
groupsList = {}
f = open('Capital.txt', 'rt', encoding='UTF8')
capitals = f.readlines()
f.close()
f = open('4WS.txt','r',encoding='euc-kr')
ws4arr = f.readlines()
f.close()
f = open('thingsQuiz.txt','rt',encoding='UTF8')
thingsq = f.readlines()
f.close()
f = open('LiarGame.txt','rt',encoding='UTF8')
liarGameList = f.readlines()
f.close()
class groupGame:
    def __init__(self,group_id):
        self.state= 0#게임 진행 상태
        self.groupId = group_id#방 식별 id
        self.memberList = []#게임 참가자 리스트
        self.file = None#게임 진행용파일
        self.nowMem = 0#현재 순서 멤버
        self.nowAnswer = []#현재 정답 리스트
        self.fileTemp = []#파일 저장용 readlines
        self.timerA = Timer1(group_id,'',0)#문제 타이머
        self.roundCounter = 1#endless 랜덤게임 라운드 저장용
        self.voted = set()#투표여부 확인용
        self.votedCount = []#득표수
        self.liarMan = ''
    def resetGame(self):#게임 진행 상태 리셋
        self.state = 0
        self.memberList = []
        self.file = None
        self.nowMem = 0
        self.nowAnswer = []
        self.fileTemp = []
        self.timerA = Timer1(self.groupId,'',0)
        self.voted = set()
        self.votedCount = []
        self.liarMan = ''
    def missionSuccess(self):
        line_bot_api.push_message(
            self.groupId, TextSendMessage(text='정답!!\n미션 성공!!\n게임시작을 입력해주세요'))
        self.state = 1
    def wordSentance4(self):#사자성어 정하기
        self.nowAnswer = []
        global ws4arr
        q = ''
        t = randint(0,len(ws4arr)-1)
        sentance = ws4arr[t]
        si = (int)(len(sentance)/2)
        for i in range(si):
            if i==0:
                q = sentance[:2]
            else:
                self.nowAnswer.append(sentance[i*2:(i+1)*2])
        targetMember = self.memberList[self.nowMem].display_name
        ans = ''
        for a in self.nowAnswer:
            ans += a +' '
        line_bot_api.push_message(
            self.groupId, 
                TextSendMessage(text='사자성어 이어말하기\n 제한시간 6초\n\n'
                +targetMember +' 님 문제입니다'))
        sleep(1)
        line_bot_api.push_message(self.groupId, TextSendMessage(text=q))
        self.timerA = Timer1(self.groupId,ans,6)
        self.timerA.start()
    def capitalQuiz(self):#수도퀴즈
        global capitals
        self.nowAnswer = []
        t = randint(0,len(capitals)-1)
        temp = capitals[t].split()
        q = temp[0]
        self.nowAnswer = temp[1:]
        ans = ''
        for a in temp[1:]:
            ans += a +' '
        targetMember = self.memberList[self.nowMem].display_name
        line_bot_api.push_message(
            self.groupId,
                TextSendMessage(text='수도 이름 맞히기\n 제한시간 7초\n\n'
                + targetMember +' 님 문제입니다'))
        sleep(1)
        line_bot_api.push_message(self.groupId, TextSendMessage(text=q))
        self.timerA = Timer1(self.groupId,ans,7)
        self.timerA.start()
    def thingsQuiz(self):#사물퀴즈
        global thingsq
        self.nowAnswer = []
        t = randint(0,len(thingsq)-1)
        temp = thingsq[t].split()
        qimage = temp[-1]
        self.nowAnswer = temp[:-1]
        ans = ''
        for a in self.nowAnswer:
            ans+=a+' '
        targetMember = self.memberList[self.nowMem].display_name
        line_bot_api.push_message(
            self.groupId,
                TextSendMessage(text='사물 이름 맞히기\n 제한시간 6초\n\n'
                +targetMember +' 님 문제입니다'))
        sleep(1)
        line_bot_api.push_message(self.groupId, ImageSendMessage(qimage,qimage))
        self.timerA = Timer1(self.groupId,ans,6)
        self.timerA.start()
    def LiarGame(self):#거짓말쟁이 게임
        global liarGameList
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
        
    def messageR(self,text,userId):
        if text == '게임준비' and self.state==0:
            self.state = 1
            line_bot_api.push_message(self.groupId, TextSendMessage(text= '게임에 참가하실 분들은 참가 를 입력해주세요'))
        elif text == '참가' and self.state==1:
            profile = line_bot_api.get_profile(userId)
            if profile not in self.memberList:
               self.memberList.append(profile)
        elif text == '게임시작' and self.state==1:
            self.nowMem = 0
            if len(self.memberList)<1:
                line_bot_api.push_message(self.groupId, TextSendMessage(text='참가 인원이 없습니다'))
            else:
                members = ''
                for mem in self.memberList:
                    members += mem.display_name + ' '
                line_bot_api.push_message(
                    self.groupId,
                        TextSendMessage(text='참가 멤버는\n'+ members + '\n입니다\n\n'
                        +'게임을 선택하여 주십시오\n1.사자성어 이어말하기\n2.수도 맞히기'
                        +'\n3.사물퀴즈\n4.endless랜덤게임\n5.거짓말쟁이게임'))
                self.state = 2
        elif text=='1' and self.state == 2:#사자성어 게임 시작
            self.state = 3
            shuffle(self.memberList)
            self.nowMem = 0
            self.wordSentance4()
        elif text in self.nowAnswer and self.state==3 and userId==self.memberList[self.nowMem].user_id:#사자성어 게임 정답
            self.timerA.flag.set()
            self.nowMem +=1
            if self.nowMem>=len(self.memberList):
                self.missionSuccess()
            else:
                #line_bot_api.push_message(self.groupId, TextSendMessage(text='정답!!'))
                self.wordSentance4()
        elif text=='2' and self.state ==2:#수도 맞히기 게임 시작
            self.state = 4
            shuffle(self.memberList)
            self.nowMem = 0
            self.capitalQuiz()
        elif text in self.nowAnswer and self.state==4 and userId==self.memberList[self.nowMem].user_id:#수도 맞히기 정답
            self.timerA.flag.set()
            self.nowMem+=1
            if self.nowMem>=len(self.memberList):
                self.missionSuccess()
            else:
                #line_bot_api.push_message(self.groupId, TextSendMessage(text='정답!!'))
                self.capitalQuiz()
        elif text=='3' and self.state==2:#사물 퀴즈
            self.state=5
            shuffle(self.memberList)
            self.nowMem = 0
            self.thingsQuiz()
        elif text in self.nowAnswer and self.state==5 and userId==self.memberList[self.nowMem].user_id:#사물퀴즈 정답
            self.timerA.flag.set()
            self.nowMem+=1
            if self.nowMem>=len(self.memberList):
                self.missionSuccess()
            else:
                #line_bot_api.push_message(self.groupId, TextSendMessage(text='정답!!'))
                self.thingsQuiz()
        elif text=='4' and self.state==2:#endless 랜덤게임
            self.state=99
            shuffle(self.memberList)
            self.nowMem = 0
            self.roundCounter = 1
            r = randint(1,3)
            if r==1:
                self.wordSentance4()
            elif r==2:
                self.capitalQuiz()
            elif r==3:
                self.thingsQuiz()
        elif text in self.nowAnswer and self.state==99 and userId==self.memberList[self.nowMem].user_id:#endless 랜덤게임 정답
            self.timerA.flag.set()
            self.nowMem+=1
            if self.nowMem>=len(self.memberList):
                self.nowMem = 0
            rc = str(self.roundCounter)
            line_bot_api.push_message(self.groupId, TextSendMessage(text='지금까지' + rc + '문제 연속 정답!!'))
            self.roundCounter+=1
            r = randint(1,3)
            if r==1:
                self.wordSentance4()
            elif r==2:
                self.capitalQuiz()
            elif r==3:
                self.thingsQuiz()
        elif text=='5' and self.state==2:#거짓말쟁이 게임
            self.state = 6
            shuffle(self.memberList)
            self.roundCounter = 0
            self.nowMem = 0
            self.LiarGame()
        elif self.state==6 and userId==self.memberList[self.nowMem].user_id:#거짓말쟁이 게임 대화,투표시작
            self.nowMem+=1
            if self.nowMem>=len(self.memberList):
                if self.roundCounter==0:
                    self.roundCounter = 1
                    self.nowMem = 0
                    line_bot_api.push_message(self.groupId, TextSendMessage(text='두번째 설명 시작해주세요'))
                    return
                self.state=98
                self.voted = set()
                self.votedCount = [0 for i in range(len(self.memberList))]
                line_bot_api.push_message(self.groupId, TextSendMessage(text='투표를 시작합니다\n득표수가 같은경우 앞사람으로 정해집니다.'))
        elif self.state==98:#거짓말쟁이게임 투표
            i = 0
            correct = False
            for i in range(len(self.memberList)):
                if self.memberList[i].display_name==text:
                    correct = True
                    break
            if correct and userId not in self.voted:
                self.voted.add(userId)
                self.votedCount[i] +=1
            if len(self.voted) == len(self.memberList):
                i = self.votedCount.index(max(self.votedCount))
                if self.memberList[i].user_id==self.liarMan:
                    self.state=97
                    line_bot_api.push_message(self.groupId, TextSendMessage(text='거짓말쟁이를 맞추셨습니다.\n거짓말쟁이는'
                    +self.memberList[i].display_name+'\n거짓말쟁이는 정답을 말해주세요'))
                else:
                    line_bot_api.push_message(self.groupId, TextSendMessage(text=self.memberList[i].display_name +'는 거짓말쟁이가 아니었습니다\n'
                    +'거짓말쟁이는 '+ line_bot_api.get_profile(self.liarMan).display_name
                    +'\n거짓말쟁이의 승리!!\n정답은 '+self.nowAnswer[0]))
                    self.state=1
        elif self.state==97 and userId==self.liarMan:
            if text==self.nowAnswer[0]:
                line_bot_api.push_message(self.groupId, TextSendMessage(text='거짓말쟁이가 정답을 맞추었습니다.\n거짓말쟁이의 승리!!'))
                self.state = 1
            else:
                line_bot_api.push_message(self.groupId, TextSendMessage(text='거짓말쟁이가 답을 맞추지 못했습니다.\n팀의 승리!!\n정답은'
                +self.nowAnswer[0]))
                self.state=1
        elif text=='reset':
            #line_bot_api.push_message(self.groupId, TextSendMessage(text='게임 설정을 Reset 합니다'))
            self.resetGame()
# function for create tmp dir for download content
def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise

#문제 푸는 시간 재는 함수
class Timer1(threading.Thread):
    def __init__(self,groupId,ans,t):
        threading.Thread.__init__(self)
        self.flag = threading.Event()
        global groupsList
        self.groupId = groupId
        self.ans = ans
        self.t = t
    def run(self):
        while not self.flag.is_set() and self.t>0:
            #line_bot_api.push_message(self.groupId, TextSendMessage(text=i))
            sleep(1)
            self.t-=1
        if not self.flag.is_set() and self.t==0:
            groupsList[self.groupId].state = 1
            line_bot_api.push_message(
                self.groupId,
                    TextSendMessage(text='땡!!\n'
                    +'정답은 ' + self.ans + ' 입니다\n'
                    +'게임시작 을 입력해주세요'))

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    global groupsList
    text = event.message.text
    if isinstance(event.source, SourceGroup):
        groupId = event.source.group_id
        if text=='profile':
            profile = line_bot_api.get_profile(event.source.user_id)
            line_bot_api.reply_message(
                event.reply_token, 
                    TextSendMessage(text='Display name: ' + profile.display_name
                    +'\nuser_id: ' + event.source.user_id)
            )
            return
        elif text == 'bye':
            line_bot_api.push_message(groupId, TextSendMessage(text='Leave Room'))
            del groupsList[groupId]
            line_bot_api.leave_group(groupId)
            return
        elif groupId not in groupsList:
            temp_group = groupGame(groupId)
            groupsList[groupId] = temp_group
        groupsList[groupId].messageR(text,event.source.user_id)

    else:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text="그룹을 만들어 주세요"))

@handler.add(JoinEvent)
def handle_join(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='Joined this ' + event.source.type))


@handler.add(LeaveEvent)
def handle_leave():
    app.logger.info("Got leave event")


@handler.add(PostbackEvent)
def handle_postback(event):
    global groupsList
    if event.postback.data == 'ping':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text='pong'))
    elif event.postback.data == 'datetime_postback':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.postback.params['datetime']))
    elif event.postback.data == 'date_postback':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.postback.params['date']))


@handler.add(BeaconEvent)
def handle_beacon(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text='Got beacon event. hwid={}, device_message(hex string)={}'.format(
                event.beacon.hwid, event.beacon.dm)))

@app.route('/static/<path:path>')
def send_static_content(path):
    return send_from_directory('static', path)


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    # create tmp dir for download content
    make_static_tmp_dir()

    #app.run(debug=options.debug, port=options.port)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
