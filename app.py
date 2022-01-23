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
ws4file = open('4WS.txt','r',encoding='euc-kr')
ws4arr = ws4file.readlines
class groupGame:
    def __init__(self,group_id):
        self.state= 0#게임 진행 상태
        self.groupId = group_id#방 식별 id
        self.memberList = []#게임 참가자 리스트
        self.file = None#게임 진행용파일
        self.nowMem = 0#현재 순서 멤버
        self.nowAnswer = []#현재 정답 리스트
        self.fileTemp = []#파일 저장용 readlines
        self.timerA = Timer1(self.groupId)#문제 타이머
    def resetGame(self):#게임 진행 상태 리셋
        self.state = 0
        self.memberList = []
        self.file = None
        self.nowMem = 0
        self.nowAnswer = []
        self.fileTemp = []
        self.timerA = Timer1(self.groupId)
    def wordSentance4(self):#사자성어 정하기
        global ws4arr
        self.nowAnswer = []
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
        line_bot_api.push_message(self.groupId, TextSendMessage(text='사자성어 이어말하기'))
        line_bot_api.push_message(self.groupId, TextSendMessage(text= targetMember +' 님 문제입니다'))
        sleep(1)
        line_bot_api.push_message(self.groupId, TextSendMessage(text=q))
        self.timerA = Timer1(self.groupId)
        self.timerA.start()
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
                line_bot_api.push_message(self.groupId, TextSendMessage(text='참가 멤버는 '+ members + ' 입니다'))
                line_bot_api.push_message(self.groupId, TextSendMessage(text='게임을 선택하여 주십시오\n 1.사자성어 이어말하기'))
                self.state = 2
        elif text=='1' and self.state == 2:#사자성어 게임 시작
            shuffle(self.memberList)
            self.wordSentance4()
        elif text in self.nowAnswer and self.state==3 and userId==self.memberList[self.nowMem].user_id:#사자성어 게임 정답
            self.timerA.flag.set()
            line_bot_api.push_message(self.groupId, TextSendMessage(text='정답!!'))
            self.nowMem +=1
            if self.nowMem>=len(self.memberList):
                line_bot_api.push_message(self.groupId, TextSendMessage(text='미션 성공!!'))
                state = 1
            else:
                self.wordSentance4()
        elif text=='reset':
            line_bot_api.push_message(self.groupId, TextSendMessage(text='게임 설정을 Reset 합니다'))
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
    def __init__(self,groupId):
        threading.Thread.__init__(self)
        self.flag = threading.Event()
        global groupsList
        self.groupId = groupId
        self.nowAnswer = groupsList[groupId].nowAnswer
    def run(self):
        i = 5
        while not self.flag.is_set() and i>0:
            line_bot_api.push_message(self.groupId, TextSendMessage(text=i))
            i-=1
            sleep(1)
        if i==0:
            line_bot_api.push_message(self.groupId, TextSendMessage(text='땡!!'))
            ans = ''
            for a in self.nowAnswer:
                ans += a +' '
            line_bot_api.push_message(self.groupId, TextSendMessage(text='정답은 ' + ans + ' 입니다'))
            groupsList[self.groupId].state = 1
            line_bot_api.push_message(self.groupId, TextSendMessage(text='게임시작 을 말해주세요'))

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
        if groupId not in groupsList:
            groupsList[groupId] = groupGame(groupId)
        groupsList[groupId].messageR(text,event.source.user_id)
    else:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text="그룹을 만들어 주세요"))
    #elif text == '정답':
        #timerA.flag.set()
        #line_bot_api.reply_message(
            #event.reply_token, TextSendMessage(text="pass"))
    #elif text == 'time':
        #line_bot_api.reply_message(
            #event.reply_token, TextSendMessage(text="timer Start"))
        #timerA = Timer1()
        #timerA.start()

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        LocationSendMessage(
            title='Location', address=event.message.address,
            latitude=event.message.latitude, longitude=event.message.longitude
        )
    )


@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        StickerSendMessage(
            package_id=event.message.package_id,
            sticker_id=event.message.sticker_id)
    )


# Other Message Type
@handler.add(MessageEvent, message=(ImageMessage, VideoMessage, AudioMessage))
def handle_content_message(event):
    if isinstance(event.message, ImageMessage):
        ext = 'jpg'
    elif isinstance(event.message, VideoMessage):
        ext = 'mp4'
    elif isinstance(event.message, AudioMessage):
        ext = 'm4a'
    else:
        return

    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    dist_path = tempfile_path + '.' + ext
    dist_name = os.path.basename(dist_path)
    os.rename(tempfile_path, dist_path)

    line_bot_api.reply_message(
        event.reply_token, [
            TextSendMessage(text='Save content.'),
            TextSendMessage(text=request.host_url + os.path.join('static', 'tmp', dist_name))
        ])


@handler.add(MessageEvent, message=FileMessage)
def handle_file_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix='file-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    dist_path = tempfile_path + '-' + event.message.file_name
    dist_name = os.path.basename(dist_path)
    os.rename(tempfile_path, dist_path)

    line_bot_api.reply_message(
        event.reply_token, [
            TextSendMessage(text='Save file.'),
            TextSendMessage(text=request.host_url + os.path.join('static', 'tmp', dist_name))
        ])


@handler.add(FollowEvent)
def handle_follow(event):
    app.logger.info("Got Follow event:" + event.source.user_id)
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text='Got follow event'))


@handler.add(UnfollowEvent)
def handle_unfollow(event):
    app.logger.info("Got Unfollow event:" + event.source.user_id)


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


@handler.add(MemberJoinedEvent)
def handle_member_joined(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text='Got memberJoined event. event={}'.format(
                event)))


@handler.add(MemberLeftEvent)
def handle_member_left(event):
    app.logger.info("Got memberLeft event")


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
