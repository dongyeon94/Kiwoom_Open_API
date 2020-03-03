"""
화면 번호
10011 : 주식 매수
10021 : 주식 매도


SetInputValue()      데이터 입력
CommRqData()         데이터 요청
GetCommData()        요청된 데이터 수신
SendOrder()          주식 매수 매도 요청


GetCommRealData()    실시간 데이터 요청
OnReceiveTrData()    TR데이터가 수신 되면 작동함

"""

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QAxContainer import *
import datetime
import time

# COM_CODE = "005930"  # 삼성전자
#COM_DATE = "20200219"  # 기준일자 600 거래일 전일 부터 현제까지 받아옴
COM_DATE = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

# 테스트용 종목 : 엘컴텍 (3000원정도)
COM_CODE = '037950'

# 모듈 메인 정의
class MyWindow(QMainWindow):

    # 초기 setup (화면크기, 화면 이름, API모듈 로딩 )
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyStock")
        self.setGeometry(300, 300, 400, 600)
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

        # 기능 정리

        # 로그인 버튼 ( 키움 증권 로그인 모듈 불러옴)
        login_btn = QPushButton("Login", self)              # Login 이라는 이름의 버튼을 생성
        login_btn.move(20, 20)                              # 20,20 위치에 버튼 위치
        login_btn.clicked.connect(self.login_clicked)       # 버튼을 눌렀을때 실행되는 기능은 login_clicked

        # 로그인 상태  ( 현재 로그인 되어있는 상태 )
        state_btn = QPushButton("Check state", self)
        state_btn.move(20, 70)
        state_btn.clicked.connect(self.staate_clicked)

        # 로그인 유저 정보 ( 사용자 이름, 아이디, 계좌 정보)
        info_btn = QPushButton('login info', self)
        info_btn.move(20, 120)
        info_btn.clicked.connect(self.login_info)

        # 주식 매수 버튼   (주식을 매수할 수 있는 버튼 , 주식 개수, 시가, 현재가 등등 세부 설정 가능)
        buy_order_btm = QPushButton('주식 매수', self)
        buy_order_btm.move(20, 170)
        buy_order_btm.clicked.connect(self.stock_buy_order)

        # 주식 매도 버튼  (주식을 매도할 수 있는 버튼 , 주식 개수, 시가, 현재가 등등 세부 설정 가능)
        sale_order_btn = QPushButton('주식 매도', self)
        sale_order_btn.move(20, 220)
        sale_order_btn.clicked.connect(self.stock_sale_order)

        # 주식 종목 정보 조회 ( 한번 호출에 최대 600개 데이터 불러옴)
        search_btn = QPushButton('주식 조회', self)
        search_btn.move(20, 270)
        search_btn.clicked.connect(self.suject_serach)

        # 주식 종목 분봉 조회 ( 한번 호출에 최대 900개 데이터 불러옴)
        minute_btn2 = QPushButton('분봉 조회', self)
        minute_btn2.move(20, 320)
        minute_btn2.clicked.connect(self.minute_data)

        # 주식 현재가 버튼 ( 실시간 체결 정보 출력 //체결 정보 없으면 데이터 없음)
        real_time_btn = QPushButton('주식 현재가', self)
        real_time_btn.move(20, 370)
        real_time_btn.clicked.connect(self.real_data)



        # # 테스트
        # test_btn2 = QPushButton('기능 테스트', self)
        # test_btn2.move(20, 500)
        # test_btn2.clicked.connect(self.test)





        # 수신 이벤트 ( 데이터가 수신 될때 작동하게됨)
        self.kiwoom.OnReceiveTrData.connect(self.receive_trdata)
        # self.kiwoom.OnReceiveRealData.connect(self.realData)



# --데이터 수신에 관련된 기능 start --

    # 분봉, 현재가 수신 데이터
    def receive_trdata(self, sScrNo, sRQName, sTrCode, sRecordName, sPreNext, nDataLength, sErrorCode, sMessage,
                       sSplmMsg):
        print(sRQName)
        if sRQName == "주가조회":
            print('주가조회')
            dataCount = self.kiwoom.GetRepeatCnt(sTrCode, sRQName)
            print('총 데이터 수 : ', dataCount)
            code = self.kiwoom.GetCommData(sTrCode, sRQName, 0, "종목코드")
            print("종목코드: " + code)
            print("------------------------------")
            # 가장최근에서 10 거래일 전까지 데이터 조회
            for dataIdx in range(10):
                inputVal = ["일자", "거래량", "시가", "고가", "저가", "현재가"]
                outputVal = ['', '', '', '', '', '']
                for idx, j in enumerate(inputVal):
                    outputVal[idx] = self.kiwoom.GetCommData(sTrCode, sRQName, dataIdx, j)
                for idx, output in enumerate(outputVal):
                    print(inputVal[idx] + output)
                print('----------------')

        if sRQName == "분봉정보":
            print('분봉 데이터')
            dataCount = self.kiwoom.GetRepeatCnt(sTrCode, sRQName)
            print('총 데이터 수 : ', dataCount)
            code = self.kiwoom.GetCommData(sTrCode, sRQName, 0, "종목코드")
            print("종목코드: " + code)
            print("------------------------------")
            # 가장최근에서 10 거래일 전까지 데이터 조회
            for dataIdx in range(3):
                inputVal = ["일자", "체결시간", "시가", "고가", "저가", "현재가"]
                outputVal = ['', '', '', '', '', '']
                for idx, j in enumerate(inputVal):
                    outputVal[idx] = self.kiwoom.GetCommData(sTrCode, sRQName, dataIdx, j)
                for idx, output in enumerate(outputVal):
                    print(inputVal[idx] + output)
                print('----------------')



    # 실시간 체결 정보 수신 데이터
    def realData(self, sJongmokCode, sRealType, sRealData):
        if sRealType == "주식체결":
            print('주식 체결 데이터')
            current_data = self.kiwoom.GetCommRealData(sJongmokCode, 10)
            # market_data = self.kiwoom.GetCommRealData(sJongmokCode, 16)
            sale_time = self.kiwoom.GetCommRealData(sJongmokCode, 20)
            print('현재가 : ', current_data)
            # print('시가 : ' , market_data)
            print('체결 시간 : ', sale_time)
            print('등락 : ')
            print('-' * 20)




    # 실시간 데이터  ( 종목에 대해 실시간 정보 요청을 실행함)
    def real_data(self):
        self.kiwoom.SetInputValue('종목코드', COM_CODE)
        res = self.kiwoom.CommRqData('종목정보요청', 'opt10001', 0, '5010')
        if res == 0:
            print('요청성공')
        else:
            print('요청 실패')
        time.sleep(1)
        self.kiwoom.OnReceiveRealData.connect(self.realData)

    # 주식 검색 입력/ 요청
    def suject_serach(self):
        self.kiwoom.SetInputValue("종목코드", COM_CODE)    # 종목코드 입력
        self.kiwoom.SetInputValue("기준일자", COM_DATE)    # 기준 일자 ( 현재 시간설정)
        self.kiwoom.SetInputValue("수정주가구분", "0")
        res = self.kiwoom.CommRqData("주가조회", "opt10081", 0, "opt10081")  # 입력한 데이터 기반 데이터 요청,
        print(res)


    # 분봉 데이터 입력/ 요쳥
    def minute_data(self):
        self.kiwoom.SetInputValue("종목코드", COM_CODE)     # 종목코드 입력
        self.kiwoom.SetInputValue("틱범위", "1")            # 틱범위 입력 1분 기준
        self.kiwoom.SetInputValue("기준일자", datetime.datetime.now().strftime('%Y%m%d%H%M%S')) # 기준일자 현재날짜
        self.kiwoom.SetInputValue("수정주가구분", "1")

        res = self.kiwoom.CommRqData("분봉정보", "opt10080", 0, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))  # 입력한 데이터 기반 데이터 요청
        print(res)
        if res == 0:
            print('조회 성공')
        else:
            print('조회 실패')


# --데이터 수신에 관련된 기능 end --




# -- 주식 매도 매수등 요청 기능 start --

    # 주식 매수
    def stock_buy_order(self):
        # SendOrder(구분요청명 , 화면번호 , 계좌 번호, 주문 유형, 주식 코드, 주문 수량, 주문단가, 거래 구분, 주문번호)
        # 주문유형  : [ 1 신규 매수 / 2 신규 매도 / 3 매수 취소  / 4 매도 취소 / 5 매수정정 / 6 매도 정정 ]
        data = self.kiwoom.SendOrder('주식매수', "10011", '8130515111', 1, COM_CODE, 1, 0, '03', "")
        print(data)

    # 주식 매도
    def stock_sale_order(self):
        # SendOrder(구분요청명 , 화면번호 , 계좌 번호, 주문 유형, 주식 코드, 주문 수량, 주문단가, 거래 구분, 주문번호)
        # 주문유형  : [ 1 신규 매수 / 2 신규 매도 / 3 매수 취소  / 4 매도 취소 / 5 매수정정 / 6 매도 정정 ]
        data = self.kiwoom.SendOrder('주식매도', "10021", '8130515111', 2, COM_CODE, 5, 0, '03', "")
        print(data)

# -- 주식 매도 매수등 요청 기능 end --





# ---- 유저 관련 기능 start----
    # 로그인 버튼 기능
    def login_clicked(self):
        ret = self.kiwoom.dynamicCall("CommConnect()")
        print(ret)

    # 로그인 상태 정보
    def staate_clicked(self):
        if self.kiwoom.dynamicCall("GetConnectState()") == 0:
            self.statusBar().showMessage("Not connected")
            print('---------------------------------')
            print('로그인 실패')
            print('---------------------------------')
        else:
            self.statusBar().showMessage("Connected")
            print('---------------------------------')
            print('로그인 성공')
            print('---------------------------------')

    # 로그인 유저 정보
    def login_info(self):
        info_user_id = self.kiwoom.dynamicCall('GetLoginInfo("USER_ID")')
        info_user_name = self.kiwoom.dynamicCall('GetLoginInfo("USER_NAME")')
        info_account_cnt = self.kiwoom.dynamicCall('GetLoginInfo("ACCOUNT_CNT")')
        info_accno = self.kiwoom.dynamicCall('GetLoginInfo("ACCNO")')
        info_key_bsecgb = self.kiwoom.dynamicCall('GetLoginInfo("KEY_BSECGB")')

        info_firew_secgb = self.kiwoom.dynamicCall('GetLoginInfo("FIREW_SECGB")')

        print('---------------------------------')
        print('user_id         : ', info_user_id)
        print('user_name       : ', info_user_name)
        print('전체계좌 갯수    : ', info_account_cnt)
        print('계좌 정보        :', info_accno)
        print('키보드 보안 여부 : ', info_key_bsecgb, '  [0:정상 / 1:해지]')

        print('방화벽 설정여부  :', info_firew_secgb, '  [0:미설정 / 1:설정 / 2:해지]')
        print('---------------------------------')

# ---- 유저 관련 기능 end----



# 메인 실행 함수 ( 이 함수가 없으면 프로그램이 실행되지 않음)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()