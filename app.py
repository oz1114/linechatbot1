import errno
import os
from stat import FILE_ATTRIBUTE_TEMPORARY
from argparse import ArgumentParser
from key import (
    line_bot_api, handler
)
from flask import Flask, request, abort, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

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
    ImageSendMessage,AudioSendMessage)
from groupGame import groupGame
from time import sleep

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)

# get channel_secret and channel_access_token from your environment variable

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

groupsList = {}

# function for create tmp dir for download content
def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise

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
        if text == 'bye':
            line_bot_api.push_message(groupId, TextSendMessage(text='Leave Room'))
            del groupsList[groupId]
            line_bot_api.leave_group(groupId)
            return
        if groupId not in groupsList:
            temp_group = groupGame(groupId)
            groupsList[groupId] = temp_group
        groupsList[groupId].messageR(text,event.source.user_id)

    else:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text="그룹을 만들어 주세요"))

@handler.add(PostbackEvent)
def handle_postback(event):
    global groupsList
    gId = ''
    uId = ''
    temp = event.postback.data.split()
    if len(temp)==3:
        if temp[0]=='mafiakill':
            gId = temp[1]
            uId = temp[2]
        func = groupsList[gId]
        if func.state!=100:
            return
        prof = line_bot_api.get_profile(uId)
        if prof in func.mafiaMember:
            func.state=7
            func.mafiaMember.remove(prof)
            line_bot_api.push_message(gId, TextSendMessage(text=prof.display_name+'님이 마피아에게 죽었습니다.'
            +'\n낮이 되었습니다.\n토론 후 투표시작 을 입력해주세요'))


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
