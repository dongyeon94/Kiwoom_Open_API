
import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import pyqtSlot, QTimer, QObject, QThread, QTime
import datetime
import time
import threading

global current_data
current_data = 0
CODE = "CLJ20"  # crude oil
COM_DATE = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

sale_time = None
bong_start = None
bong_end = None

# Head for Doubly LinkedList(매수한 선물 리스트)
head = None

# 진입 타입
type_buy = 2  # 매수 진입
type_sell = 1  # 매도 진입

#진입 플래그
transaction_flag = False

# 진입 판단 파라미터
bongP = 0
bongPlus = None
# 마지막 가격. 첫 가격으로 자동으로 바뀜.
lastTickPrice = None

debug_file_started = False

# Hardcoded
numBought = 1

total = 0

class MyWindow(QMainWindow):
    def __init__(self):
        # 초기 setup 모듈 로딩 등
        super().__init__()

        self.setWindowTitle("PyStock")
        self.setGeometry(50, 50, 400, 800)
        self.kiwoom = QAxWidget("KFOpenAPI.KFOpenAPICtrl.1")

        # 입력 기능 정리
        self.account = QLineEdit(self)
        self.account.move(200, 20)
        self.account.resize(100, 30)
        self.account.setPlaceholderText('계좌번호를 입력하세요')

        self.password = QLineEdit(self)
        self.password.move(200, 70)
        self.password.resize(100, 30)
        self.password.setPlaceholderText('비밀번호를 입력하세요')

        self.stoct_code = QLineEdit(self)
        self.stoct_code.move(200, 120)
        self.stoct_code.resize(100, 30)
        self.stoct_code.setPlaceholderText('종목 코드를 입력하세요')

        self.stoct_num = QLineEdit(self)
        self.stoct_num.move(200, 170)
        self.stoct_num.resize(100, 30)
        self.stoct_num.setPlaceholderText('주문량')

        # option - version -
        self.ChekGroup1 = QCheckBox('option1', self)
        self.ChekGroup1.move(200, 220)
        self.ChekGroup1.clicked.connect(self.checkbox)

        self.ChekGroup2 = QCheckBox('option2', self)
        self.ChekGroup2.move(200, 245)
        self.ChekGroup2.clicked.connect(self.checkbox)

        self.starttime = QTimeEdit(self)
        self.starttime.setDisplayFormat("hh:mm:ss")
        self.starttime.move(200, 280)

        self.endtime = QTimeEdit(self)
        self.endtime.setDisplayFormat("hh:mm:ss")
        self.endtime.move(200, 320)
        self.endtime.setTime(QTime(23, 59,59))

        self.gain_text = QLabel(self)
        self.gain_text.move(200,400)
        self.gain_text.setText('익절')
        self.gain_text.resize(30,20)

        self.get_gain = QComboBox(self)
        self.get_gain.move(230, 400)
        self.get_gain.resize(100, 20)
        self.get_gain.addItems([str(i) for i in range(1, 101)])

        self.loss_text =QLabel(self)
        self.loss_text.move(200,425)
        self.loss_text.setText('손절')
        self.loss_text.resize(30,20)

        self.get_loss = QComboBox(self)
        self.get_loss.move(230, 425)
        self.get_loss.resize(100, 20)
        self.get_loss.addItems([str(i) for i in range(1, 101)])




        # 디버깅 모드
        self.debug_check = QCheckBox('디버깅모드', self)
        self.debug_check.move(200, 600)
        self.debug_check.clicked.connect(self.debug_check_fun)

        self.debug_file = QPushButton('디버깅 파일', self)
        self.debug_file.move(200, 650)
        self.debug_file.clicked.connect(self.debug_file_fun)
        self.debug_file_obj = None

        self.option_warning  = QMessageBox(self)
        self.option_warning.resize(300,500)


        # 시작
        module_start = QPushButton('거래 시작', self)
        module_start.move(200, 500)
        module_start.clicked.connect(self.data_loading)

        # 로그인
        login_btn = QPushButton("로그인", self)
        login_btn.move(20, 20)
        login_btn.clicked.connect(self.login_clicked)

        info_btn = QPushButton('로그인 확인', self)
        info_btn.move(20, 70)
        info_btn.clicked.connect(self.login_info)

        search_btm = QPushButton('주식 조회', self)
        search_btm.move(20, 170)
        search_btm.clicked.connect(self.subject_search)

        buy_btn = QPushButton('매수버튼', self)
        buy_btn.move(20, 270)
        buy_btn.clicked.connect(self.stock_buy_order)

        sale_btn = QPushButton('매도 버튼', self)
        sale_btn.move(20, 320)
        sale_btn.clicked.connect(self.stock_sale_order)

        # 데이터 수신 이벤트
        self.kiwoom.OnReceiveTrData.connect(self.receive_trdata)
        self.kiwoom.OnReceiveChejanData.connect(self.get_transaction_data)



        # 로그파일
        self.log_file = None

        test_ = QPushButton(' 테스트', self)
        test_.move(20, 600)
        test_.clicked.connect(self.test1)


        self.stoct_code.setText('CLK20')
        self.stoct_num.setText('1')



    def test1(self):
        print('test22')
        print(self.combobo.currentText())
        # data = self.test()
        # data = self.kiwoom.OnReceiveChejanData.connect(self.test)
        # print(data)

    def get_transaction_data(self, sGubun, nItemCnt):
        global transaction_flag, type_buy, type_sell

        # 매수 2 매도 1
        if sGubun == '1' and transaction_flag:
            print('예약중')
            price = float(self.kiwoom.GetChejanData(910))
            type_tran = int(self.kiwoom.GetChejanData(907))
            sale_time = int(self.kiwoom.GetChejanData(908))
            print(price,':',type_tran,';',sale_time)
            print(type(price), ':', type(type_tran), ';', type(sale_time))
            ll_append(Transaction(type_tran, price, numBought, sale_time))
            if type_tran == type_buy:
                pri = round(price + 0.01*int(self.get_gain.currentText()) , 2)
                self.log_file.write(str(sale_time) + ',' + str(True) + ',_,' + str(0) + "," + str(price) + ',에 매수 진입,' + str(pri) + '에 매도 예약\n')
                self.stock_sale_order(pri)
            else:
                pri = round(price - 0.01*int(self.get_gain.currentText()) , 2)
                self.log_file.write(str(sale_time) + ',' + str(True) + ',_,' + str(0) + "," + str(price) + ',에 매도 진입,' + str(pri) + '에 매수 예약\n')
                self.stock_buy_order(pri)
            transaction_flag = False


    def get_transaction_data_debug(self, price, typeIn, sale_time, bongP):
        global transaction_flag, type_buy
        print('test중')
        ll_append(Transaction(typeIn, price, numBought, sale_time))
        transaction_flag = False
        if typeIn == type_buy:
            pri = round(price + 0.03, 2)
            print(str(sale_time) + ',' + str(True) + ',' + str(price) + ',' + str(bongP) + "," + str(price) + ',에 매수 진입,' + str(pri) + '에 매도 예약')
        else:
            pri = round(price - 0.03, 2)
            print(str(sale_time) + ',' + str(True) + ',' + str(price) + ',' + str(bongP) + "," + str(price) + ',에 매도 진입,' + str(pri) + '에 매수 예약')


    def debug_check_fun(self):
        if self.debug_check.isChecked():
            return True
        else:
            return False

    def debug_file_fun(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', "",
                                            "All Files(*);; Python Files(*.py)", '/home')
        if not fname[0]:
            QMessageBox.about(self, "Warning", "파일을 선택하지 않았습니다.")
        else:
            self.debug_file_name = fname[0]

    def run(self, price, bongPlus, tickFlag, bongFlag, sale_time, option):
        global head, type_sell, type_buy, bongP, lastTickPrice, total, transaction_flag

        if self.debug_check_fun() is False and self.log_file is None:
            self.log_file = open('log' + COM_DATE + '_거래.csv', mode='wt', encoding='utf-8')
            self.log_file.write('체결시간,BongFlag,가격,봉카운트,거래내역\n')
            self.log_file.flush()

        if price is None:
            return

        if lastTickPrice is None:
            lastTickPrice = price
            if self.debug_check_fun() is False:
                self.log_file.write(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + "," + str(bongP) + '\n')
                self.log_file.flush()
            else:
                print(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + "," + str(bongP))
            return

        curr = head
        while curr is not None:
            tickSold = False
            if tickFlag:
                # if price > lastTickPrice:
                #     curr.tickP += 1
                # elif price < lastTickPrice:
                #     curr.tickP -= 1
                if curr.type == type_buy:
                    # Option2: 매수거래가 3틱이상 올랐을때 매도
                    if price - curr.price >= 0.01*int(self.get_gain.currentText()):
                        if self.debug_check_fun() is False:
                            self.log_file.write(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(
                                bongP) + ',' + 'opt2_익절 ' + str(curr.tran_time) + '에 $' + str(curr.price) + '에 매수 후 $' + str(price) + '에 매도\n')
                        else:
                            print(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(
                                bongP) + ',' + 'opt2_익절 ' + str(curr.tran_time) + '에 $' + str(curr.price) + '에 매수 후 $' + str(price) + '에 매도')
                        # 익절은 예약에서 알아서 팔림
                        remove_elem(curr)
                        tickSold = True
                        total += (price - curr.price) * numBought
                    # Option4: 매수거래가 6틱이상 하락했을때 매도
                    elif price - curr.price <= -0.01*int(self.get_loss.currentText()):
                        if self.debug_check_fun() is False:
                            self.stock_buy_wait()
                            self.log_file.write(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(
                                bongP) + ',' + 'opt4_손절 ' + str(curr.tran_time) + '에 $' + str(curr.price) + '에 매수 후 $' + str(price) + '에 매도\n')
                        else:
                            print(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(
                                bongP) + ',' + 'opt4_손절 ' + str(curr.tran_time) + '에 $' + str(curr.price) + '에 매수 후 $' + str(price) + '에 매도')
                        remove_elem(curr)
                        tickSold = True
                        total += (price - curr.price) * numBought
                else:
                    # Option2_reverse: 매도거래가 3틱이상 내렸을 때 매도
                    if price - curr.price <= -0.01*int(self.get_gain.currentText()):
                        if self.debug_check_fun() is False:
                            self.log_file.write(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(
                                bongP) + ',' + 'opt2r_익절 ' + str(curr.tran_time) + '에 $' + str(curr.price) + '$에 매도 후 $' + str(price) + '에 매수\n')
                        else:
                            print(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(
                                bongP) + ',' + 'opt2r_익절 ' + str(curr.tran_time) + '에 $' + str(curr.price) + '$에 매도 후 $' + str(price) + '에 매수')
                        remove_elem(curr)
                        tickSold = True
                        total += (price - curr.price) * numBought
                    # Option4_reverse: 매도거래가 6틱이상 상승했을때 매도
                    elif price - curr.price >= 0.01*int(self.get_loss.currentText()):
                        if self.debug_check_fun() is False:
                            self.stock_sale_wait()
                            self.log_file.write(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(
                                bongP) + ',' + 'opt4r_손절 ' + str(curr.tran_time) + '에 $' + str(curr.price) + '에 매도 후 $' + str(price) + '에 매수\n')
                        else:
                            print(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(
                                bongP) + ',' + 'opt4r_손절 ' + str(curr.tran_time) + '에 $' + str(curr.price) + '에 매도 후 $' + str(price) + '에 매수')
                        remove_elem(curr)
                        tickSold = True
                        total += (price - curr.price) * numBought
            if bongFlag and not tickSold:
                curr.bongCount += 1
                if bongPlus > 0:
                    curr.bongP += 1
                elif bongPlus < 0:
                    curr.bongP -= 1
                if curr.type == type_buy:
                    if curr.bongP == -1 and curr.bongCount == 2:
                        # Option3: 매수진입 직후 마이너스 봉일때 바로 팜 (진입한 봉은 무시)
                        if self.debug_check_fun() is False:
                            self.stock_buy_wait()
                            self.log_file.write(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(
                                bongP) + ',' + 'opt3_손절 ' + str(curr.tran_time) + '에 $' + str(curr.price) + '에 매수 후 $' + str(price) + '에 매도\n')
                        else:
                            print(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(
                                bongP) + ',' + 'opt3_손절 ' + str(curr.tran_time) + '에 $' + str(curr.price) + '에 매수 후 $' + str(price) + '에 매도')
                        remove_elem(curr)
                        total += (price - curr.price) * numBought
                else:
                    if curr.bongP == 1 and curr.bongCount == 2:
                        # Option3_reverse: 매도진입 직후 플러스 봉일때 바로 팜 (진입한 봉은 무시)
                        if self.debug_check_fun() is False:
                            self.stock_sale_wait()
                            self.log_file.write(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(
                            bongP) + ',' + 'opt3r_손절 ' + str(curr.tran_time) + '에 $' + str(curr.price) + '에 매도 후 $' + str(price) + '에 매수\n')
                        else:
                            print(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(
                            bongP) + ',' + 'opt3r_손절 ' + str(curr.tran_time) + '에 $' + str(curr.price) + '에 매도 후 $' + str(price) + '에 매수')
                        remove_elem(curr)
                        total += (price - curr.price) * numBought
            curr = curr.next

        if bongFlag:
            if bongP is None:
                if bongPlus > 0:
                    bongP = 1
                elif bongPlus < 0:
                    bongP = -1
                else:
                    bongP = 0
            else:
                if option[0] == '1' and bongP <= -3:
                    if bongPlus > 0:
                        # 매수진입: bong 3번 내려갔다가 한번 오르면 '삼'
                        transaction_flag = True
                        # pri = round(price + 0.03, 2)

                        if self.debug_check_fun() is False:
                            print('매수 진입', price)
                            self.stock_buy_order()
                            # time.sleep(1)
                            # self.stock_sale_order(pri)
                            # self.log_file.write(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(
                            #     bongP + '\n'))
                        else:
                            # print(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(bongP))
                            self.get_transaction_data_debug(price, type_buy, sale_time, bongP)
                        # ll_append(Transaction(type_buy, price, numBought, sale_time))
                elif option[1] == '1' and bongP >= 3:
                    if bongPlus < 0:
                        transaction_flag = True
                        # 매도진입: bong 3번 올랐다가 한번 내리면 삼
                        # pri = round(price - 0.03, 2)
                        if self.debug_check_fun() is False:
                            print('매도 진입', price)
                            self.stock_sale_order()
                            # time.sleep(1)
                            # self.stock_buy_order(pri)
                            # self.log_file.write(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(
                            #     bongP + '\n'))
                        else:
                            # print(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(bongP))
                            self.get_transaction_data_debug(price, type_sell, sale_time, bongP)
                        # ll_append(Transaction(type_sell, price, numBought, sale_time))
                if bongPlus > 0:
                    if bongP > 0:
                        bongP += 1
                    else:
                        bongP = 1

                elif bongPlus < 0:
                    if bongP < 0:
                        bongP -= 1
                    else:
                        bongP = -1
        lastTickPrice = price
        if self.debug_check_fun() is False:
            self.log_file.write(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(bongP) + '\n')
            self.log_file.flush()
        else:
            print(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(bongP))

    # ------ 주식 주문  start  -------

    # 주식 매수
    def stock_buy_order(self, price=0):
        print('매수중', price)
        getPrice = 0
        #                             구분 , 화면번호 , 계좌 , 주문유형 ,종목코드, 개수,가격, stop가격, 거래구분, 주문번호
        if price == 0:
            data = self.kiwoom.SendOrder('주식매수', "1211", self.account.text(), 2, self.stoct_code.text(),
                                         int(self.stoct_num.text()), str(price), "", "1", "")
        else:
            data = self.kiwoom.SendOrder('주식매수', "1211", self.account.text(), 2, self.stoct_code.text(),
                                         int(self.stoct_num.text()), str(price), "", "2", "")

        return getPrice

    # 주식 매도
    def stock_sale_order(self, price=0):
        print('매도중', price)
        #                             구분 , 화면번호 , 계좌 , 주문유형 ,종목코드, 개수,가격, stop가격, 거래구분, 주문번호
        if price == 0:
            data = self.kiwoom.SendOrder('주식매도', "1212", self.account.text(), 1, self.stoct_code.text(),
                                         int(self.stoct_num.text()), str(price), "", "1", "")
        else:
            data = self.kiwoom.SendOrder('주식매도', "1212", self.account.text(), 1, self.stoct_code.text(),
                                         int(self.stoct_num.text()), str(price), "", "2", "")


    # 주식 매도 정정 취소
    def stock_sale_modify(self, code):
        #                             구분 , 화면번호 , 계좌 , 주문유형 ,종목코드, 개수,가격, stop가격, 거래구분, 주문번호
        data = self.kiwoom.SendOrder('주식정정', "1213", self.account.text(), 3, self.stoct_code.text(),
                                     int(self.stoct_num.text()), "0", "0", "2", str(code[6:]))
        time.sleep(1)
        print(data)
        self.stock_sale_order()

    # 주식 매수 정정 취소
    def stock_buy_modify(self, code):
        #                             구분 , 화면번호 , 계좌 , 주문유형 ,종목코드, 개수,가격, stop가격, 거래구분, 주문번호
        data = self.kiwoom.SendOrder('주식정정', "1213", self.account.text(), 4, self.stoct_code.text(),
                                     int(self.stoct_num.text()), "0", "0", "2", str(code[6:]))
        time.sleep(1)
        print(data)
        self.stock_buy_order()

    # ------ 주식 주문  end  -------

    # ------ 데이터 수신 기능  start  -------

    def data_loading(self):
        global debug_file_started, total
        print('데이터 로딩')


        if self.checkbox()=='':
            # self.option_warning.showMessage('옵션을 선택해주세요')
            self.option_warning.about(self,'프로그램 경고','시작 전 옵셥을 선택해주세요')
                # show('옵션을 선택해주세요')
            return

        # 실시간 체결 데이터 로딩
        if self.debug_check_fun() is False:
            self.kiwoom.SetInputValue('종목코드', self.stoct_code.text())
            self.kiwoom.SetInputValue('시간단위', "1")
            res = self.kiwoom.CommRqData('해외선물시세', 'opt10011', "0", 'opt10011')
            print(res)
            if res == 0:
                print('요청성공')
            else:
                print('요청 실패')
            self.kiwoom.OnReceiveRealData.connect(self.realData)
        else:
            debugFile = open(self.debug_file_name, mode='rt',encoding="utf-8")
            while True:
                try:
                    if debug_file_started is False:
                        # 첫줄 날려버리기
                        debugFile.readline()
                        time.sleep(0.2)
                        debug_file_started = True
                    dataline = debugFile.readline()
                    time.sleep(0.2)
                    if dataline == '':
                        print("디버그 파일 읽기 끝")
                        print("Total", total)
                        debugFile.close()
                        break
                    self.realData('', "해외선물시세", dataline.strip().split(","))
                except EOFError:
                    print("디버그 파일 읽기 끝")
                    print("Total", total)
                    debugFile.close()

    # 실시간 체결 정보 수신 데이터
    def realData(self, sJongmokCode, sRealType, sRealData):
        global sale_time, bong_start, bong_end, bongPlus
        if sRealType == "해외선물시세":
            bongFlag = False
            if self.debug_check_fun():
                tmp_time = int(sRealData[0])
                if sRealData[2] == '_':
                    return
                current_data = float(sRealData[2])
            else:
                current_data = self.kiwoom.GetCommRealData(sRealType, 10)
                # market_data = self.kiwoom.GetCommRealData(sJongmokCode, 16)
                tmp_time = int(self.kiwoom.GetCommRealData(sRealType, 20))
            if sale_time is None:
                if tmp_time / 100 == tmp_time // 100:
                    bong_start = abs(float(str(current_data)))
                    print("프로그램 시작 시간: ", tmp_time // 100)
                else:
                    startTime = str(tmp_time // 100 + 1)
                    print("프로그램 시작 시간: ", startTime)
                sale_time = tmp_time
            if tmp_time // 100 > sale_time // 100 or tmp_time // 100 == 0:
                if bong_start is None:
                    bong_start = abs(float(str(current_data)))
                    bongPlus = 0
                else:
                    bongPlus = bong_end - bong_start
                    if round(abs(bongPlus), 2) <= 0.01:
                        bongPlus = 0
                        #0.01인경우 무시
                        bong_start = abs(float(str(current_data)))
                    else:
                        bong_start = abs(float(str(current_data)))
                bongFlag = True
            else:
                bong_end = abs(float(str(current_data)))
            if bongPlus is not None:
                sale_time = tmp_time
                if self.debug_check_fun() is False:
                    if int(self.start_time()) <= sale_time <= int(self.end_time()):
                        self.run(abs(float(str(current_data))), bongPlus, True, bongFlag, str(sale_time), self.checkbox())
                    else:
                        self.disconnect()
                else:
                    self.run(abs(float(str(current_data))), bongPlus, True, bongFlag, str(sale_time), self.checkbox())

    # 실시간 데이터  ( 종목에 대해 실시간 정보 요청을 실행함)
    def real_data(self):
        if self.debug_check_fun() is False:
            self.kiwoom.SetInputValue('종목코드', self.stoct_code.text())
            self.kiwoom.SetInputValue('시간단위', "1")
            res = self.kiwoom.CommRqData('해외선물시세', 'opt10011', "0", 'opt10011')
            self.kiwoom.OnReceiveRealData.connect(self.realData)

    # 실시간 데이터 디스커넥
    def real_data_disconnect(self):
        if self.debug_check_fun() is False:
            self.kiwoom.DisconnectRealData('opt10011')

    # 매도 미체결 취소 조회
    def stock_buy_wait(self):
        print('미체결 조회중')
        self.kiwoom.SetInputValue('계좌번호', self.account.text())
        self.kiwoom.SetInputValue("비밀번호", self.password.text())
        self.kiwoom.SetInputValue('비밀번호입력매체', "00")  # 무조건 00
        self.kiwoom.SetInputValue('종목코드', self.stoct_code.text())
        self.kiwoom.SetInputValue('통화코드', "USD")
        self.kiwoom.SetInputValue('매도수구분', "1")
        res = self.kiwoom.CommRqData("매도미체결", "opw30001", "", "opw30001")
        time.sleep(1)

    # 매수 미체결 조회
    def stock_sale_wait(self):
        print('미체결 조회중')
        self.kiwoom.SetInputValue('계좌번호', self.account.text())
        self.kiwoom.SetInputValue("비밀번호", self.password.text())
        self.kiwoom.SetInputValue('비밀번호입력매체', "00")  # 무조건 00
        self.kiwoom.SetInputValue('종목코드', self.stoct_code.text())
        self.kiwoom.SetInputValue('통화코드', "USD")
        self.kiwoom.SetInputValue('매도수구분', "2")
        res = self.kiwoom.CommRqData("매수미체결", "opw30001", "", "opw30001")
        time.sleep(1)

    # 데이터 수신중
    def receive_trdata(self, sScrNo, sRQName, sTrCode, sRecordName, sPreNext):
        # print(sRQName)
        if sRQName == "매도미체결":
            # dataCount = self.kiwoom.GetRepeatCnt(sTrCode, sRQName)
            # dataCount2 = self.kiwoom.GetChejanData(9203)
            try:
                num = self.kiwoom.GetCommData(sTrCode, sRQName, 0, "주문번호")
                # typ = self.kiwoom.GetCommData(sTrCode, sRQName, 0, "구븐")
                print(num)
                if int(num) > 0:
                    self.stock_sale_modify(num)
            except:
                print('매도 미체결 내역 없음')

        if sRQName == "매수미체결":
            # dataCount = self.kiwoom.GetRepeatCnt(sTrCode, sRQName)
            # dataCount2 = self.kiwoom.GetChejanData(9203)
            try:
                num = self.kiwoom.GetCommData(sTrCode, sRQName, 0, "주문번호")
                # typ = self.kiwoom.GetCommData(sTrCode, sRQName, 0, "구븐")
                print(num)
                if int(num) > 0:
                    self.stock_buy_modify(num)
            except:
                print('매수 미체결 내역 없음')

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
            # print('분봉 데이터')
            dataCount = self.kiwoom.GetRepeatCnt(sTrCode, sRQName)
            # print('총 데이터 수 : ', dataCount)
            code = self.kiwoom.GetCommData(sTrCode, sRQName, 0, "종목코드")
            # print("종목코드: " + code)
            # print("------------------------------")
            # 가장최근에서 10 거래일 전까지 데이터 조회
            for dataIdx in range(1):
                inputVal = ["체결시간n", "현재가n", "등락율n", "시가n", "고가n", "저가n"]
                outputVal = ['', '', '', '', '', '']
                for idx, j in enumerate(inputVal):
                    outputVal[idx] = self.kiwoom.GetCommData(sTrCode, sRQName, dataIdx, j)
                # print(outputVal[1])
                # self.run(abs(float(str(outputVal[1]))), abs(float(str(outputVal[1]))), True, True, outputVal[0], debugFlag)
                # self.run(current_data,outputVal[1],True,True)
                # for idx, output in enumerate(outputVal):
                #     print(inputVal[idx] + ' : ' + output)
                # print('----------------')

    def start_time(self):
        return self.starttime.time().toString().replace(':', '')

    def end_time(self):
        return self.endtime.time().toString().replace(':', '')

    def checkbox(self):
        te = ''
        if self.ChekGroup1.isChecked():
            te = '10'
        if self.ChekGroup2.isChecked():
            te = '01'
        if self.ChekGroup1.isChecked() and self.ChekGroup2.isChecked():
            te = '11'
        return te

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

    def login_info(self):
        info_user_id = self.kiwoom.dynamicCall('GetLoginInfo("USER_ID")')
        info_user_name = self.kiwoom.dynamicCall('GetLoginInfo("USER_NAME")')
        info_account_cnt = self.kiwoom.dynamicCall('GetLoginInfo("ACCOUNT_CNT")')
        info_accno = self.kiwoom.dynamicCall('GetLoginInfo("ACCNO")')
        info_key_bsecgb = self.kiwoom.dynamicCall('GetLoginInfo("KEY_BSECGB")')
        info_firew_secgb = self.kiwoom.dynamicCall('GetLoginInfo("FIREW_SECGB")')
        self.account.setText(info_accno.split(';')[0])

        print('---------------------------------')
        print('user_id         : ', info_user_id)
        print('user_name       : ', info_user_name)
        print('전체계좌 갯수    : ', info_account_cnt)
        print('계좌 정보        :', info_accno)
        print('키보드 보안 여부 : ', info_key_bsecgb, '  [0:정상 / 1:해지]')

        print('방화벽 설정여부  :', info_firew_secgb, '  [0:미설정 / 1:설정 / 2:해지]')
        print('---------------------------------')

    # ------ 유저 정보  end  -------

    # ------ 종목 정보  start  -------
    def subject_search(self):
        self.kiwoom.SetInputValue("종목코드", self.stoct_code.text())
        res = self.kiwoom.CommRqData("주가조회", "opt10001", "0", "opt10001")
        print(res)

    def minute_data(self):
        self.kiwoom.SetInputValue("종목코드", self.stoct_code.text())
        self.kiwoom.SetInputValue("시간단위", "1")
        # self.kiwoom.SetInputValue("기준일자", datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        # self.kiwoom.SetInputValue("수정주가구분","1")
        # res = self.kiwoom.CommRqData("분봉정보","opt10012","0",datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        res = self.kiwoom.CommRqData("분봉정보", "opt10012", "0", "opt10012")
        print(res)
        if res == 0:
            print('조회 성공')
        else:
            print('조회 실패')


# ------ 유저 정보  end  -------


# Transaction: Node
class Transaction:
    def __init__(self, typeIn, priceIn, count, tran_timeIn):
        self.type = typeIn
        self.price = priceIn
        self.count = count
        self.tran_time = tran_timeIn
        # 초기 세팅
        self.bongP = 0
        self.tickP = 0
        self.bongCount = 0
        # Doubly Linked List라서 prev & next 존재
        self.prev = None
        self.next = None

    def __str__(self):
        return '체결 노드. 가격: ' + str(self.price)

# LinkedList 영역
def ll_append(newNode):
    global head
    """
    Insert a new element at the end of the list.
    Takes O(n) time.
    """
    if not head:
        head = newNode
        return
    curr = head
    while curr.next:
        curr = curr.next
    curr.next = newNode


def remove_elem(node):
    global head
    """
    Unlink an element from the list.
    Takes O(1) time.
    """
    prev = node.prev
    if node.prev:
        node.prev.next = node.next
    if node.next:
        node.next.prev = node.prev
    if node is head:
        head = node.next
    node.prev = None
    node.next = None
    return prev


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # log_file = open('log' + COM_DATE + '_거래.csv', 'w')
    # log_file.write('체결시간,BongFlag,가격,봉카운트,거래내역\n')
    # log_file.flush()
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
