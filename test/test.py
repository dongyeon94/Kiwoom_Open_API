import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import datetime
import time


class MainGUI(QMainWindow):
    sig1 = pyqtSignal
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyStock")
        self.setGeometry(300, 150, 400, 800)


        # 로그인
        login_btn = QPushButton("로그인", self)
        login_btn.move(20, 20)
        login_btn.clicked.connect(self.test3)

        info_btn = QPushButton('로그인 확인', self)
        info_btn.move(20, 70)
        info_btn.clicked.connect(self.test)

        self.kiwoom = QAxWidget("KFOpenAPI.KFOpenAPICtrl.1")
        self.login = QThread()
        self.login.start()

    def test(self):

        self.login_fun = Worker()

        self.login_fun.moveToThread(self.login)
        self.login_fun.login_info()

    def test3(self):

        print('0')
        self.login_fun = Worker()
        print('1')
        self.login_fun.moveToThread(self.login)
        self.login_fun.login_clicked()




class Worker(MainGUI):


    def __init__(self):
        super().__init__()
        self.kiwoom2 = self.kiwoom
        print('inits',self.kiwoom)
    def login_clicked(self):
        ret = self.kiwoom2.dynamicCall("CommConnect(0)")
        print(ret)
        print('login_clkied',self.kiwoom)


    def login_info(self):
        print('login info',self.kiwoom)
        print('login info', self.kiwoom2)
        info_user_id = self.kiwoom2.dynamicCall('GetLoginInfo("USER_ID")')
        info_user_name = self.kiwoom2.dynamicCall('GetLoginInfo("USER_NAME")')
        info_account_cnt = self.kiwoom2.dynamicCall('GetLoginInfo("ACCOUNT_CNT")')
        info_accno = self.kiwoom2.dynamicCall('GetLoginInfo("ACCNO")')
        info_key_bsecgb = self.kiwoom2.dynamicCall('GetLoginInfo("KEY_BSECGB")')
        info_firew_secgb = self.kiwoom2.dynamicCall('GetLoginInfo("FIREW_SECGB")')
        # self.account.setText(info_accno.split(';')[0])

        print('---------------------------------')
        print('user_id         : ', info_user_id)
        print('user_name       : ', info_user_name)
        print('전체계좌 갯수    : ', info_account_cnt)
        print('계좌 정보        :', info_accno)
        print('키보드 보안 여부 : ', info_key_bsecgb, '  [0:정상 / 1:해지]')

        print('방화벽 설정여부  :', info_firew_secgb, '  [0:미설정 / 1:설정 / 2:해지]')
        print('---------------------------------')

app = QApplication(sys.argv)
form = MainGUI()
form.show()
app.exec_()