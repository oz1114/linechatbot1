import json
from random import *
from key import (
    line_bot_api, gameList
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
from linebot.models import TextSendMessage

#state 1~7 게임 진행상태 96~99 기타 상태 100:대기상태

class groupGame:
    def __init__(self,group_id):
        self.state= 0#게임 진행 상태 정수형
        self.groupId = group_id#방 식별 id
        self.memberList = []#게임 참가자 리스트 프로필 형식
        self.nowMem = 0#현재 순서 멤버 정수형
        self.nowAnswer = []#현재 정답 리스트 텍스트형식
        self.timerA = None
        self.roundCounter = 1#endless 랜덤게임 라운드 저장용,거짓말쟁이게임 라운드 저장, 마피아게임 일수 저장 정수형
        self.voted = set()#투표여부 확인용 user_id 형식 집합
        self.votedCount = []#득표수 정수형 리스트
        self.liarMan = ''#마피아 혹은 거짓말쟁이 user_id 형식
        self.mafiaMember = []#마피아게임용 멤버리스트
    #게임 진행 상태 리셋
    def resetGame(self):
        self.state = 0
        self.memberList = []
        self.nowMem = 0
        self.nowAnswer = []
        self.timerA = None
        self.roundCounter = 0
        self.voted = set()
        self.votedCount = []
        self.liarMan = ''
        self.mafiaMember = []
    
    #외부 함수
    from quiz import quiz
    from liarGame import (
        LiarGame, liarVote
    )
    from mafiaGame import (
        mafiaButton, mafiaStart, mafiaVote
    )

    #모두 정답
    def missionSuccess(self):
        line_bot_api.push_message(
            self.groupId, TextSendMessage(text='정답!!\n미션 성공!!\n게임시작을 입력해주세요'))
        self.state = 1

    #메시지 처리함수##########################################################################################################
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
                self.state=2
                members = ''
                for mem in self.memberList:
                    members += mem.display_name + ' '
                line_bot_api.push_message(
                    self.groupId,
                        TextSendMessage(text='참가 멤버는\n'+ members + '\n입니다\n\n'
                        +'게임을 선택하여 주십시오\n1.사자성어 이어말하기\n2.수도 맞히기'
                        +'\n3.랜드마크 퀴즈\n4.endless랜덤게임\n5.거짓말쟁이게임\n6.마피아게임'))

        #사자성어 게임 시작
        elif text=='1' and self.state == 2:
            self.state = 3
            self.roundCounter = 0
            shuffle(self.memberList)
            self.nowMem = 0
            self.quiz(gameList[0])
        #사자성어 게임 정답
        elif text in self.nowAnswer and self.state==3 and userId==self.memberList[self.nowMem].user_id:
            self.timerA.flag.set()
            self.nowMem +=1
            if self.nowMem>=len(self.memberList):
                self.missionSuccess()
            else:
                self.quiz(gameList[0])


        #수도 맞히기 게임 시작
        elif text=='2' and self.state ==2:
            self.state = 4
            self.roundCounter = 0
            shuffle(self.memberList)
            self.nowMem = 0
            self.quiz(gameList[1])
        #수도 맞히기 정답
        elif text in self.nowAnswer and self.state==4 and userId==self.memberList[self.nowMem].user_id:
            self.timerA.flag.set()
            self.nowMem+=1
            if self.nowMem>=len(self.memberList):
                self.missionSuccess()
            else:
                self.quiz(gameList[1])


        #랜드마크 퀴즈
        elif text=='3' and self.state==2:
            self.state=5
            self.roundCounter = 0
            shuffle(self.memberList)
            self.nowMem = 0
            self.quiz(gameList[2])
        #랜드마크퀴즈 정답
        elif text in self.nowAnswer and self.state==5 and userId==self.memberList[self.nowMem].user_id:
            self.timerA.flag.set()
            self.nowMem+=1
            if self.nowMem>=len(self.memberList):
                self.missionSuccess()
            else:
                self.quiz(gameList[2])


        #endless 랜덤게임
        elif text=='4' and self.state==2:
            self.state=99
            shuffle(self.memberList)
            self.nowMem = 0
            self.roundCounter = 0
            r = randint(0,2)
            self.quiz(gameList[r])
        #endless 랜덤게임 정답
        elif text in self.nowAnswer and self.state==99 and userId==self.memberList[self.nowMem].user_id:
            self.timerA.flag.set()
            self.nowMem+=1
            if self.nowMem>=len(self.memberList):
                self.nowMem = 0
            self.roundCounter+=1
            r = randint(0,2)
            self.quiz(gameList[r])


        #거짓말쟁이 게임
        elif text=='5' and self.state==2:
            self.state = 6
            shuffle(self.memberList)
            self.roundCounter = 0
            self.nowMem = 0
            self.LiarGame()
        #거짓말쟁이 게임 대화,투표시작
        elif self.state==6 and userId==self.memberList[self.nowMem].user_id:
            self.nowMem+=1
            if self.nowMem>=len(self.memberList):
                if self.roundCounter==0:
                    self.roundCounter = 1
                    self.nowMem = 0
                    line_bot_api.push_message(self.groupId, TextSendMessage(text='두번째 설명 시작해주세요'))
                    return
                self.state='liarvote'
                self.voted = set()
                self.votedCount = [0 for i in range(len(self.memberList))]
                line_bot_api.push_message(self.groupId, TextSendMessage(text='투표를 시작합니다\n득표수가 같은 경우 앞사람으로 정해집니다'))
        #거짓말쟁이게임 투표
        elif self.state=='liarvote':
            self.liarVote(text,userId)
        #거짓말쟁이가 정답을 말할 때
        elif self.state=='liarspeak' and userId==self.liarMan:
            if text==self.nowAnswer[0]:
                line_bot_api.push_message(self.groupId, TextSendMessage(text='거짓말쟁이가 정답을 맞추었습니다.\n거짓말쟁이의 승리!!'))
                self.state = 1
            else:
                line_bot_api.push_message(self.groupId, TextSendMessage(text='거짓말쟁이가 답을 맞추지 못했습니다.\n팀의 승리!!\n정답은'
                +self.nowAnswer[0]))
                self.state=1


        #마피아게임 시작
        elif self.state==2 and text=='6':
            self.mafiaStart()
        #마피아게임 투표
        elif self.state==7 and text=='투표시작':
            self.voted = set()
            self.votedCount = [0 for i in range(len(self.mafiaMember))]
            self.state='mafiavote'
        #마피아게임 투표중
        elif self.state=='mafiavote':
            self.mafiaVote(text,userId)

        #마피아게임 테스트용
        elif text == '마피아테스트' and len(self.memberList)>1:
            self.liarMan = userId
            self.state='mafiakill'
            self.mafiaMember = self.memberList
            self.mafiaButton()

        #진행상황 리셋(게임준비부터)
        elif text=='reset':
            self.resetGame()