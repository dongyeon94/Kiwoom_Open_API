import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import pyqtSlot,QTimer
import datetime
import time
import pandas as pd

COM_CODE = "CLJ20"  # crude oil
#COM_DATE = "20200219"  # 기준일자 600 거래일 전일 부터 현제까지 받아옴
COM_DATE = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

minu = []
tick = []


class MyWindow(QMainWindow):
    def __init__(self):
        # 초기 setup 모듈 로딩 등
        super().__init__()
        self.setWindowTitle("PyStock")
        self.setGeometry(300, 150, 400, 800)
        self.kiwoom = QAxWidget("KFOpenAPI.KFOpenAPICtrl.1")

        # 기능 정리
        login_btn = QPushButton("Login", self)
        login_btn.move(20, 20)
        login_btn.clicked.connect(self.login_clicked)

        state_btn = QPushButton("Check state", self)
        state_btn.move(20, 70)
        state_btn.clicked.connect(self.staate_clicked)

        info_btn = QPushButton('login info',self)
        info_btn.move(20,120)
        info_btn.clicked.connect(self.login_info)

        search_btm = QPushButton('주식 조회',self)
        search_btm.move(20,170)
        search_btm.clicked.connect(self.suject_serach)

        min_btn = QPushButton('분봉 조회', self)
        min_btn.move(20, 220)
        min_btn.clicked.connect(self.minute_data)

        buy_btn = QPushButton('매수버튼',self)
        buy_btn.move(20,270)
        buy_btn.clicked.connect(self.stock_buy_order)

        sale_btn = QPushButton('매도 버튼',self)
        sale_btn.move(20,320)
        sale_btn.clicked.connect(self.stock_sale_order)


        # 기능 테스트(테스트 용도로 사용)
        test_btn2 = QPushButton('데이터 로딩', self)
        test_btn2.move(20, 420)
        test_btn2.clicked.connect(self.data_loading)

        test_btn3 = QPushButton('기능 테스트 정지', self)
        test_btn3.move(20, 470)
        test_btn3.clicked.connect(self.real_data_disconnect)

        test_ = QPushButton('매수 테스트', self)
        test_.move(20, 570)
        test_.clicked.connect(self.stock_buy_order)

        # 데이터 수신 이벤트
        self.kiwoom.OnReceiveTrData.connect(self.receive_trdata)



    def test(self):
        pass

# ------ 주식 주문  start  -------

    # 주식 매수
    def stock_buy_order(self):
        print('매수중')

        self.kiwoom.SetInputValue('계좌번호', "7009039772")
        self.kiwoom.SetInputValue("비밀번호", "0000")
        self.kiwoom.SetInputValue('비밀번호입력매체', "00")  # 무조건 00
        self.kiwoom.SetInputValue('종목코드', COM_CODE)
        self.kiwoom.SetInputValue("매도수구분", "2")  # 1:매도, 2:매수
        self.kiwoom.SetInputValue("해외주문유형", "1")  # 1:시장가, 2:지정가, 3:STOP, 4:StopLimit, 5:OCO, 6:IF DONE
        self.kiwoom.SetInputValue("주문수량", "1")
        self.kiwoom.SetInputValue("주문표시가격", "0")
        self.kiwoom.SetInputValue("STOP구분", "0")  # 0:선택안함, 1:선택
        self.kiwoom.SetInputValue("STOP표시가격", "")
        self.kiwoom.SetInputValue("LIMIT구분", "0")  # 0:선택안함, 1:선택
        self.kiwoom.SetInputValue("LIMIT표시가격", "")
        self.kiwoom.SetInputValue("해외주문조건구분", "0")  # 0:당일, 6:GTD
        self.kiwoom.SetInputValue("주문조건종료일자", "0")  # 0:당일, 6:GTD
        self.kiwoom.SetInputValue("통신주문구분", "AP")  # 무조건 "AP" 입력

        data = self.kiwoom.CommRqData('주식주문', "opw10008", "", '0101')

        print(data)

    # 주식 매도
    def stock_sale_order(self):
        print('매도중')

        self.kiwoom.SetInputValue('계좌번호', "7009039772")
        self.kiwoom.SetInputValue("비밀번호", "0000")
        self.kiwoom.SetInputValue('비밀번호입력매체', "00")  # 무조건 00
        self.kiwoom.SetInputValue('종목코드', COM_CODE)
        self.kiwoom.SetInputValue("매도수구분", "1")  # 1:매도, 2:매수
        self.kiwoom.SetInputValue("해외주문유형", "1")  # 1:시장가, 2:지정가, 3:STOP, 4:StopLimit, 5:OCO, 6:IF DONE
        self.kiwoom.SetInputValue("주문수량", "1")
        self.kiwoom.SetInputValue("주문표시가격", "0")
        self.kiwoom.SetInputValue("STOP구분", "0")  # 0:선택안함, 1:선택
        self.kiwoom.SetInputValue("STOP표시가격", "")
        self.kiwoom.SetInputValue("LIMIT구분", "0")  # 0:선택안함, 1:선택
        self.kiwoom.SetInputValue("LIMIT표시가격", "")
        self.kiwoom.SetInputValue("해외주문조건구분", "0")  # 0:당일, 6:GTD
        self.kiwoom.SetInputValue("주문조건종료일자", "0")  # 0:당일, 6:GTD
        self.kiwoom.SetInputValue("통신주문구분", "AP")  # 무조건 "AP" 입력

        data = self.kiwoom.CommRqData('주식주문', "opw10008", "", '0101')

        print(data)

# ------ 주식 주문  end  -------


# ------ 데이터 수신 기능  start  -------
    def data_loading(self):
        print('데이터 로딩')
        # 분봉 1분마다  start안에 숫자는 1/1000초  1분 = 60000
        self.minute_data()
        self.timer = QTimer(self)
        self.timer.start(60000)
        self.timer.timeout.connect(self.minute_data)

        # 실시간 체결 데이터 로딩
        self.kiwoom.SetInputValue('종목코드', COM_CODE)
        self.kiwoom.SetInputValue('시간단위', "1")
        res = self.kiwoom.CommRqData('해외선물시세', 'opt10011', "0", 'opt10011')
        print(res)
        if res == 0:
            print('요청성공')
        else:
            print('요청 실패')

        self.kiwoom.OnReceiveRealData.connect(self.realData)


    # 실시간 체결 정보 수신 데이터
    def realData(self, sJongmokCode, sRealType, sRealData):
        if sRealType == "해외선물시세":
            print('주식 체결 데이터')
            current_data = self.kiwoom.GetCommRealData(sRealType, 10)
            # market_data = self.kiwoom.GetCommRealData(sJongmokCode, 16)
            sale_time = self.kiwoom.GetCommRealData(sRealType, 20)

            tick.append(current_data)
            print('현재가 : ', current_data)
            # print('시가 : ' , market_data)
            print('체결 시간 : ', sale_time)
            print('등락 : ')
            print('-' * 20)

    # 실시간 데이터  ( 종목에 대해 실시간 정보 요청을 실행함)
    def real_data(self):
        self.kiwoom.SetInputValue('종목코드', COM_CODE)
        self.kiwoom.SetInputValue('시간단위', "1")
        res = self.kiwoom.CommRqData('해외선물시세', 'opt10011', "0", 'opt10011')
        print(res)
        if res == 0:
            print('요청성공')
        else:
            print('요청 실패')
        time.sleep(1)
        self.kiwoom.OnReceiveRealData.connect(self.realData)

    # 실시간 데이터 디스커넥
    def real_data_disconnect(self):
        self.kiwoom.DisconnectRealData('opt10011')

    # 데이터 수신중
    def receive_trdata(self, sScrNo, sRQName, sTrCode, sRecordName, sPreNext):
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
                inputVal = ["체결시간n", "현재가n", "시가", "고가", "저가", "거래량"]
                outputVal = ['', '', '', '', '', '']
                for idx, j in enumerate(inputVal):
                    outputVal[idx] = self.kiwoom.GetCommData(sTrCode, sRQName, dataIdx, j)
                for idx, output in enumerate(outputVal):
                    print(inputVal[idx] + ' : ' + output)
                print('----------------')

        if sRQName == "분봉정보":
            print('분봉 데이터')
            dataCount = self.kiwoom.GetRepeatCnt(sTrCode, sRQName)
            print('총 데이터 수 : ', dataCount)
            code = self.kiwoom.GetCommData(sTrCode, sRQName, 0, "종목코드")
            print("종목코드: " + code)
            print("------------------------------")
            # 가장최근에서 10 거래일 전까지 데이터 조회
            for dataIdx in range(1):
                inputVal = ["체결시간n", "현재가n", "등락율n", "시가n", "고가n", "저가n"]
                outputVal = ['', '', '', '', '', '']
                for idx, j in enumerate(inputVal):
                    outputVal[idx] = self.kiwoom.GetCommData(sTrCode, sRQName, dataIdx, j)
                minu.append(outputVal)
                for idx, output in enumerate(outputVal):
                    print(inputVal[idx] + ' : ' + output)
                print('----------------')

# ------ 데이터 수신 기능  end  -------



# ------ 유저 정보  start  -------
    def login_clicked(self):
        ret = self.kiwoom.dynamicCall("CommConnect(0)")
        print(ret)

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


    def  login_info(self):
        info_user_id =self.kiwoom.dynamicCall('GetLoginInfo("USER_ID")')
        info_user_name = self.kiwoom.dynamicCall('GetLoginInfo("USER_NAME")')
        info_account_cnt = self.kiwoom.dynamicCall('GetLoginInfo("ACCOUNT_CNT")')
        info_accno = self.kiwoom.dynamicCall('GetLoginInfo("ACCNO")')
        info_key_bsecgb = self.kiwoom.dynamicCall('GetLoginInfo("KEY_BSECGB")')

        info_firew_secgb = self.kiwoom.dynamicCall('GetLoginInfo("FIREW_SECGB")')

        print('---------------------------------')
        print('user_id         : ',info_user_id)
        print('user_name       : ',info_user_name)
        print('전체계좌 갯수    : ',info_account_cnt)
        print('계좌 정보        :',info_accno)
        print('키보드 보안 여부 : ',info_key_bsecgb,'  [0:정상 / 1:해지]')

        print('방화벽 설정여부  :',info_firew_secgb,'  [0:미설정 / 1:설정 / 2:해지]')
        print('---------------------------------')

# ------ 유저 정보  end  -------



# ------ 종목 정보  start  -------
    def suject_serach(self):
        self.kiwoom.SetInputValue("종목코드",COM_CODE)
        res = self.kiwoom.CommRqData("주가조회", "opt10001", "0", "opt10001")
        print(res)

    def minute_data(self):
        self.kiwoom.SetInputValue("종목코드",COM_CODE)
        self.kiwoom.SetInputValue("시간단위","1")
        # self.kiwoom.SetInputValue("기준일자", datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        # self.kiwoom.SetInputValue("수정주가구분","1")
        # res = self.kiwoom.CommRqData("분봉정보","opt10012","0",datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        res = self.kiwoom.CommRqData("분봉정보", "opt10012", "0", "opt10012")
        print(res)
        if res==0:
            print('조회 성공')
        else:
            print('조회 실패')


# ------ 유저 정보  end  -------



if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
    # minu
    # tick
    data1 = pd.DataFrame(minu,index=None)
    data2 = pd.DataFrame(tick, index=None)
    data1.to_csv('분봉.csv',index=None)
    data2.to_csv('틱.csv',index=None)
