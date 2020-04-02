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

# 진입 타입
type_buy = 2  # 매수 진입
type_sell = 1  # 매도 진입

# 진입 플래그
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
        self.setGeometry(300, 150, 400, 800)
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
        self.endtime.setTime(QTime(23, 59, 59))

        self.gain_text = QLabel(self)
        self.gain_text.move(200, 400)
        self.gain_text.setText('익절')
        self.gain_text.resize(30, 20)

        self.get_gain = QComboBox(self)
        self.get_gain.move(230, 400)
        self.get_gain.resize(100, 20)
        self.get_gain.addItems([str(i) for i in range(1, 101)])

        self.loss_text = QLabel(self)
        self.loss_text.move(200, 425)
        self.loss_text.setText('손절')
        self.loss_text.resize(30, 20)

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

        self.option_warning = QMessageBox(self)
        self.option_warning.resize(300, 500)

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

        self.buy_btn = QPushButton('매수버튼', self)
        self.buy_btn.move(20, 270)
        self.buy_btn.clicked.connect(self.stock_buy_order)

        self.sale_btn = QPushButton('매도 버튼', self)
        self.sale_btn.move(20, 320)
        self.sale_btn.clicked.connect(self.stock_sale_order)

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

        self.list = DLinkedList()

    def test1(self):
        print('test')


    def get_transaction_data(self, sGubun, nItemCnt):
        global transaction_flag, type_buy, type_sell, numBought
        # 예약 받아옴
        if sGubun == '0':
            tran = int(self.kiwoom.GetChejanData(905))
            stop_price = float(self.kiwoom.GetChejanData(13333))
            type_tran = int(self.kiwoom.GetChejanData(907))
            if stop_price != 0:
                if tran != 3:
                    # 예약과 시가를 구분
                    if type_tran == type_buy:
                        # 매도 후 낮아진 가격에 매수
                        type_tran = type_sell
                        price = round(stop_price - 0.01 * (int(self.get_loss.currentText())), 2)
                    else:
                        # 매수 후 높아진 가격에 매도
                        type_tran = type_buy
                        price = round(stop_price + 0.01 * (int(self.get_loss.currentText())), 2)
                    transaction_id = self.kiwoom.GetChejanData(9203)[6:]
                    sale_time = int(self.kiwoom.GetChejanData(908)[3:-2])
                    self.list.ll_append(Transaction(type_tran, price, sale_time, transaction_id))
                else:
                    #봉손절(예약취소, 취소거래 아이디 다름)
                    if type_tran == type_sell:
                        self.stock_sale_order()
                    else:
                        self.stock_buy_order()
        # 매수 2 매도 1
        # 거래 체결된 경우
        if sGubun == '1':
            # 경우1: 새로 산 후 예약 거는 경우
            if transaction_flag:
                type_tran = int(self.kiwoom.GetChejanData(907))
                price = float(self.kiwoom.GetChejanData(910))
                sale_time = int(self.kiwoom.GetChejanData(908))
                transaction_id = self.kiwoom.GetChejanData(9203)[6:]
                if type_tran == type_buy:
                    self.log_file.write(
                        str(sale_time) + ',' + str(True) + ',_,' + str(0) + "," + str(price) + ',' + str(
                            transaction_id) + ',(id) 매수 진입\n')
                    self.stock_sale_order(price,5)
                else:
                    self.log_file.write(
                        str(sale_time) + ',' + str(True) + ',_,' + str(0) + "," + str(price) + ',' + str(
                            transaction_id) + ',(id) 매도 진입\n')
                    self.stock_buy_order(price,5)
                transaction_flag = False
            # #경우2: 익절(예약) or 손절(시가) 거래 체결
            else:
                transaction_id = self.kiwoom.GetChejanData(9203)[6:]
                tran = int(self.kiwoom.GetChejanData(905))
                price = float(self.kiwoom.GetChejanData(910))
                sale_time = int(self.kiwoom.GetChejanData(908))
                if tran == 21:
                    curr = self.list.head
                    while curr is not None:
                        if curr.id == transaction_id:
                            # OCO손절 or익절 (예약 체결됨)
                            # Opt2, 2r: 매도/수거래가 3틱이상 올랐을때 매도
                            self.list.remove_elem(curr)
                            if curr.type == type_buy:
                                self.log_file.write(str(sale_time) + ',' + str(False) + ',' + str(price) + ',' +
                                                     str(bongP) + ',' + '판매완료 id:' + str(curr.id) + ' $'
                                                     + str(curr.price) + '$에 매수 후 $' + str(price) + '에 매도\n')
                            else:
                                self.log_file.write(str(sale_time) + ',' + str(False) + ',' + str(price) + ',' + str(
                                    bongP) + ',' + '판매완료 id:' + str(curr.id) + ' $' + str(
                                    curr.price) + '$에 매도 후 $' + str(price) + '에 매수\n')
                            break
                        curr = curr.next

                # if tran == 23:
                #     # 봉손절 case: 예약 취소 완료, 시가로 팔기
                #     type_tran = int(self.kiwoom.GetChejanData(907))
                #     if type_tran == type_sell:
                #         self.stock_sale_order()
                #     else:
                #         self.stock_buy_order()

    def get_transaction_data_debug(self, price, typeIn, sale_time, bongP):
        global transaction_flag, type_buy
        self.list.ll_append(Transaction(typeIn, price, sale_time, '디버깅'))
        transaction_flag = False
        if typeIn == type_buy:
            pri = round(price + 0.01 * int(self.get_gain.currentText()), 2)
            print(str(sale_time) + ',' + str(True) + ',' + str(price) + ',' + str(bongP) + "," + str(
                price) + ',에 매수 진입,' + str(pri) + '에 매도 예약')
        else:
            pri = round(price - 0.01 * int(self.get_gain.currentText()), 2)
            print(str(sale_time) + ',' + str(True) + ',' + str(price) + ',' + str(bongP) + "," + str(
                price) + ',에 매도 진입,' + str(pri) + '에 매수 예약')

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
        global type_sell, type_buy, bongP, lastTickPrice, total, transaction_flag

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

        if self.list.tail and self.list.tail.bongCount < 2:
            # 봉손절: 마지막 거래만 확인
            if bongFlag:
                self.list.tail.bongCount += 1
                if bongPlus > 0:
                    self.list.tail.bongP += 1
                elif bongPlus < 0:
                    self.list.tail.bongP -= 1
                if self.list.tail.type == type_buy:
                    if self.list.tail.bongP == -1 and self.list.tail.bongCount == 2:
                        # Option3: 매수진입 직후 마이너스 봉일때 바로 팜 (진입한 봉은 무시)
                        try:
                            if self.debug_check_fun() is False:
                                self.stock_sale_modify(self.list.tail.id)
                                self.log_file.write(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(
                                    bongP) + ',봉손절 ' + str(self.list.tail.tran_time) + '에 $' + str(
                                    self.list.tail.price) + '에 매수 후 $' + str(price) + '에 매도\n')
                            else:
                                print(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(
                                    bongP) + ',봉손절 ' + str(self.list.tail.tran_time) + '에 $' + str(
                                    self.list.tail.price) + '에 매수 후 $' + str(price) + '에 매도')
                        except:
                            pass
                        self.list.remove_elem(self.list.tail)
                else:
                    if self.list.tail.bongP == 1 and self.list.tail.bongCount == 2:
                        # Option3_reverse: 매도진입 직후 플러스 봉일때 바로 팜 (진입한 봉은 무시)
                        try:
                            if self.debug_check_fun() is False:
                                self.stock_buy_modify(self.list.tail.id)
                                self.log_file.write(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(
                                    bongP) + ',봉손절 ' + str(self.list.tail.tran_time) + '에 $' + str(
                                    self.list.tail.price) + '에 매도 후 $' + str(price) + '에 매수\n')
                            else:
                                print(str(sale_time) + ',' + str(bongFlag) + ',' + str(price) + ',' + str(
                                    bongP) + ',봉손절 ' + str(self.list.tail.tran_time) + '에 $' + str(
                                    self.list.tail.price) + '에 매도 후 $' + str(price) + '에 매수')
                        except:
                            pass
                        self.list.remove_elem(self.list.tail)
        if bongFlag:
            if bongP is None:
                if bongPlus > 0:
                    bongP = 1
                elif bongPlus < 0:
                    bongP = -1
                else:
                    bongP = 0
            else:
                if bongP <= -1 and bongPlus > 0:
                    if option[0] == '1' and (self.list.size == 0 or self.list.head.type == type_buy):
                        transaction_flag = True
                        if self.debug_check_fun() is False:
                            print('매수 진입', price)
                            self.stock_buy_order()
                        else:
                            self.get_transaction_data_debug(price, type_buy, sale_time, bongP)
                elif bongP >= 1 and bongPlus < 0:
                    if option[1] == '1' and (self.list.size == 0 or self.list.head.type == type_sell):
                        transaction_flag = True
                        if self.debug_check_fun() is False:
                            print('매도 진입', price)
                            self.stock_sale_order()
                        else:
                            self.get_transaction_data_debug(price, type_sell, sale_time, bongP)
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
    def stock_buy_order(self, price=0, flag=1):
        print('매수중')
        # limit 익절 stop 손절
        self.kiwoom.SetInputValue('계좌번호', self.account.text())
        self.kiwoom.SetInputValue("비밀번호", "0000")
        self.kiwoom.SetInputValue('비밀번호입력매체', "00")  # 무조건 00
        self.kiwoom.SetInputValue('종목코드', self.stoct_code.text())
        self.kiwoom.SetInputValue("매도수구분", "2")  # 1:매도, 2:매수
        self.kiwoom.SetInputValue("해외주문유형", str(flag))  # 1:시장가, 2:지정가, 3:STOP, 4:StopLimit, 5:OCO, 6:IF DONE
        self.kiwoom.SetInputValue("주문수량", "1")
        if flag == 1:
            self.kiwoom.SetInputValue("주문표시가격", "0")
            self.kiwoom.SetInputValue("STOP구분", "0")  # 0:선택안함, 1:선택
            self.kiwoom.SetInputValue("STOP표시가격", "")
            self.kiwoom.SetInputValue("LIMIT구분", "0")  # 0:선택안함, 1:선택
            self.kiwoom.SetInputValue("LIMIT표시가격", "")
            self.kiwoom.SetInputValue("해외주문조건구분", "0")  # 0:당일, 6:GTD
            self.kiwoom.SetInputValue("주문조건종료일자", "0")  # 0:당일, 6:GTD
            self.kiwoom.SetInputValue("통신주문구분", "AP")  # 무조건 "AP" 입력
        else:
            self.kiwoom.SetInputValue("주문표시가격", "0")
            self.kiwoom.SetInputValue("STOP구분", "1")  # 0:선택안함, 1:선택
            self.kiwoom.SetInputValue("STOP표시가격", str(round(price + 0.01 * int(self.get_loss.currentText()), 2)))
            self.kiwoom.SetInputValue("LIMIT구분", "1")  # 0:선택안함, 1:선택
            self.kiwoom.SetInputValue("LIMIT표시가격", str(round(price - 0.01 * int(self.get_gain.currentText()), 2)))
            self.kiwoom.SetInputValue("해외주문조건구분", "0")  # 0:당일, 6:GTD
            self.kiwoom.SetInputValue("주문조건종료일자", "0")  # 0:당일, 6:GTD
            self.kiwoom.SetInputValue("통신주문구분", "AP")  # 무조건 "AP" 입력

        data = self.kiwoom.CommRqData('주식주문', "opw10008", "", '0101')

        print(data)

    # 주식 매도
    def stock_sale_order(self, price=0, flag=1):
        print('매도중')

        self.kiwoom.SetInputValue('계좌번호', self.account.text())
        self.kiwoom.SetInputValue("비밀번호", "0000")
        self.kiwoom.SetInputValue('비밀번호입력매체', "00")  # 무조건 00
        self.kiwoom.SetInputValue('종목코드', self.stoct_code.text())
        self.kiwoom.SetInputValue("매도수구분", "1")  # 1:매도, 2:매수
        self.kiwoom.SetInputValue("해외주문유형", str(flag))  # 1:시장가, 2:지정가, 3:STOP, 4:StopLimit, 5:OCO, 6:IF DONE
        self.kiwoom.SetInputValue("주문수량", "1")
        if flag == 1:
            self.kiwoom.SetInputValue("주문표시가격", "0")
            self.kiwoom.SetInputValue("STOP구분", "0")  # 0:선택안함, 1:선택
            self.kiwoom.SetInputValue("STOP표시가격", "")
            self.kiwoom.SetInputValue("LIMIT구분", "0")  # 0:선택안함, 1:선택
            self.kiwoom.SetInputValue("LIMIT표시가격", "")
            self.kiwoom.SetInputValue("해외주문조건구분", "0")  # 0:당일, 6:GTD
            self.kiwoom.SetInputValue("주문조건종료일자", "0")  # 0:당일, 6:GTD
            self.kiwoom.SetInputValue("통신주문구분", "AP")  # 무조건 "AP" 입력
        else:
            self.kiwoom.SetInputValue("주문표시가격", "0")
            self.kiwoom.SetInputValue("STOP구분", "1")  # 0:선택안함, 1:선택
            self.kiwoom.SetInputValue("STOP표시가격", str(round(price - 0.01 * int(self.get_loss.currentText()), 2)))
            self.kiwoom.SetInputValue("LIMIT구분", "1")  # 0:선택안함, 1:선택
            self.kiwoom.SetInputValue("LIMIT표시가격", str(round(price + 0.01 * int(self.get_gain.currentText()), 2)))
            self.kiwoom.SetInputValue("해외주문조건구분", "0")  # 0:당일, 6:GTD
            self.kiwoom.SetInputValue("주문조건종료일자", "0")  # 0:당일, 6:GTD
            self.kiwoom.SetInputValue("통신주문구분", "AP")  # 무조건 "AP" 입력

        data = self.kiwoom.CommRqData('주식주문', "opw10008", "", '0101')

        print(data)

    # 주식 매도 정정 취소
    def stock_sale_modify(self, code):
        #                             구분 , 화면번호 , 계좌 , 주문유형 ,종목코드, 개수,가격, stop가격, 거래구분, 주문번호
        data = self.kiwoom.SendOrder('주식정정', "1213", self.account.text(), 3, self.stoct_code.text(),
                                     int(self.stoct_num.text()), "0", "0", "2", str(code))

    # 주식 매수 정정 취소
    def stock_buy_modify(self, code):
        #                             구분 , 화면번호 , 계좌 , 주문유형 ,종목코드, 개수,가격, stop가격, 거래구분, 주문번호
        data = self.kiwoom.SendOrder('주식정정', "1213", self.account.text(), 4, self.stoct_code.text(),
                                     int(self.stoct_num.text()), "0", "0", "2", str(code))

    # ------ 주식 주문  end  -------

    # ------ 데이터 수신 기능  start  -------

    def data_loading(self):
        global debug_file_started, total
        print('데이터 로딩')

        if self.checkbox() == '':
            # self.option_warning.showMessage('옵션을 선택해주세요')
            self.option_warning.about(self, '프로그램 경고', '시작 전 옵션을 선택해주세요')
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
            debugFile = open(self.debug_file_name, mode='rt', encoding="utf-8")
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
                # id = float(sRealData[])
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
                    # if round(abs(bongPlus), 2) <= 0.01:
                    #     bongPlus = 0
                    #     # 0.01인경우 무시
                    #     bong_start = abs(float(str(current_data)))
                    # else:
                    bong_start = abs(float(str(current_data)))
                bongFlag = True
            else:
                bong_end = abs(float(str(current_data)))
            if bongPlus is not None:
                sale_time = tmp_time
                if self.debug_check_fun() is False:
                    self.run(abs(float(str(current_data))), bongPlus, True, bongFlag, str(sale_time), self.checkbox())
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

    # # 매도 미체결 취소 조회
    # def stock_buy_wait(self):
    #     print('미체결 조회중')
    #     self.kiwoom.SetInputValue('계좌번호', self.account.text())
    #     self.kiwoom.SetInputValue("비밀번호", self.password.text())
    #     self.kiwoom.SetInputValue('비밀번호입력매체', "00")  # 무조건 00
    #     self.kiwoom.SetInputValue('종목코드', self.stoct_code.text())
    #     self.kiwoom.SetInputValue('통화코드', "USD")
    #     self.kiwoom.SetInputValue('매도수구분', "1")
    #     res = self.kiwoom.CommRqData("매도미체결", "opw30001", "", "opw30001")
    #     time.sleep(1)
    #
    # # 매수 미체결 조회
    # def stock_sale_wait(self):
    #     print('미체결 조회중')
    #     self.kiwoom.SetInputValue('계좌번호', self.account.text())
    #     self.kiwoom.SetInputValue("비밀번호", self.password.text())
    #     self.kiwoom.SetInputValue('비밀번호입력매체', "00")  # 무조건 00
    #     self.kiwoom.SetInputValue('종목코드', self.stoct_code.text())
    #     self.kiwoom.SetInputValue('통화코드', "USD")
    #     self.kiwoom.SetInputValue('매도수구분', "2")
    #     res = self.kiwoom.CommRqData("매수미체결", "opw30001", "", "opw30001")
    #     time.sleep(1)

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
    def __init__(self, typeIn, priceIn, tran_timeIn, idIn):
        self.type = typeIn
        self.price = priceIn
        self.tran_time = tran_timeIn
        self.id = idIn
        # 초기 세팅
        self.bongP = 0
        self.bongCount = 0
        # Doubly Linked List라서 prev & next 존재
        self.prev = None
        self.next = None

    def __str__(self):
        return '체결 노드. 가격: ' + str(self.price)


class DLinkedList:
    def __init__(self):
        self.size = 0
        self.head = None
        self.tail = None

    def remove_elem(self, node):
        self.size -= 1
        if self.head == self.tail:
            self.head = None
            self.tail = None
        else:
            if node is self.tail:
                self.tail.next = None
                self.tail = self.tail.prev
            else:
                node.prev.next = node.next
                node.next.prev = node.prev
                node = None

    def ll_append(self, newNode):
        self.size += 1
        if not self.head:
            self.head = newNode
            self.tail = newNode
            return
        curr = self.head
        while curr.next:
            curr = curr.next
        curr.next = newNode
        self.tail = curr.next


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
