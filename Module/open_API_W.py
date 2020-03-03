import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QAxContainer import *
import datetime
import time

COM_CODE = "CLJ20"  # 삼성전자
#COM_DATE = "20200219"  # 기준일자 600 거래일 전일 부터 현제까지 받아옴
COM_DATE = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

class MyWindow(QMainWindow):
    def __init__(self):
        # 초기 setup 모듈 로딩 등
        super().__init__()
        self.setWindowTitle("PyStock")
        self.setGeometry(300, 300, 400, 600)
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

        test_btn = QPushButton('주식 조회',self)
        test_btn.move(20,170)
        test_btn.clicked.connect(self.suject_serach)

        test_btn2 = QPushButton('분봉 조회', self)
        test_btn2.move(20, 220)
        test_btn2.clicked.connect(self.minute_data)



        # 기능 테스트(테스트 용도로 사용)
        test_btn2 = QPushButton('기능 테스트', self)
        test_btn2.move(20, 400)
        test_btn2.clicked.connect(self.real_data)


        # 데이터 수신 이벤트
        self.kiwoom.OnReceiveTrData.connect(self.receive_trdata)


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
        res = self.kiwoom.CommRqData('종목정보요청', 'opt10001', "0", '5010')
        if res == 0:
            print('요청성공')
        else:
            print('요청 실패')
        time.sleep(1)
        self.kiwoom.OnReceiveRealData.connect(self.realData)



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

    def receive_trdata(self, sScrNo, sRQName, sTrCode, sRecordName, sPreNext, nDataLength, sErrorCode, sMessage, sSplmMsg):
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
            for dataIdx in range(10):
                inputVal = ["일자", "체결시간", "시가", "고가", "저가", "현재가"]
                outputVal = ['', '', '', '', '', '']
                for idx, j in enumerate(inputVal):
                    outputVal[idx] = self.kiwoom.GetCommData(sTrCode ,sRQName, dataIdx, j)
                for idx, output in enumerate(outputVal):
                    print(inputVal[idx] + output)
                print('----------------')

    def test(self):
        test_data =self.kiwoom.dynamicCall('GetGlobalFutureItemlist()')
        print(test_data)


    def suject_serach(self):

        self.kiwoom.SetInputValue("종목코드",COM_CODE)
        # self.kiwoom.SetInputValue("기준일자", COM_DATE)
        #self.kiwoom.SetInputValue("수정주가구분", "0")
        res = self.kiwoom.CommRqData("주가조회", "opt10001", "0", "opt10001")
        print(res)


    def minute_data(self):

        self.kiwoom.SetInputValue("종목코드",COM_CODE)
        self.kiwoom.SetInputValue("틱범위","1:1분")
        self.kiwoom.SetInputValue("기준일자", datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        self.kiwoom.SetInputValue("수정주가구분","1")

        res = self.kiwoom.CommRqData("분봉정보","opt10080",0,datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        print(res)
        if res==0:
            print('조회 성공')
        else:
            print('조회 실패')




if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
