import sys
import math
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import pyqtSlot, QTimer
import datetime
import time
import pandas as pd

global current_data
current_data = 0
COM_CODE = "CLJ20"  # crude oil
# COM_DATE = "20200219"  # 기준일자 600 거래일 전일 부터 현제까지 받아옴
COM_DATE = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

minu = []
tick = []
sale_time = None
real_bong = None

debugFlag = True
log_file_t = None
log_file_b = None
log_file_tran = None

# Head for Doubly LinkedList(매수한 선물 리스트)
head = None

# 진입 타입
type_sell = 1  # 매수 진입
type_buy = 2  # 매도 진입

# 진입 판단 파라미터
bongP = 0
# 마지막 가격. 첫 가격으로 자동으로 바뀜.
lastBongPrice = 0
lastTickPrice = 0

# Hardcoded
numBought = 10


class MyWindow(QMainWindow):
    global debugFlag
    def __init__(self):
        # 초기 setup 모듈 로딩 등
        super().__init__()
        self.setWindowTitle("PyStock")
        self.setGeometry(300, 150, 400, 800)
        self.kiwoom = QAxWidget("KFOpenAPI.KFOpenAPICtrl.1")

        # 기능 정리

        # 시작작
        module_start = QPushButton('시뮬레이션 시작', self)
        module_start.move(200, 300)
        module_start.clicked.connect(self.data_loading)

        # 로그인
        login_btn = QPushButton("Login", self)
        login_btn.move(20, 20)
        login_btn.clicked.connect(self.login_clicked)

        state_btn = QPushButton("Check state", self)
        state_btn.move(20, 70)
        state_btn.clicked.connect(self.staate_clicked)

        info_btn = QPushButton('login info', self)
        info_btn.move(20, 120)
        info_btn.clicked.connect(self.login_info)

        search_btm = QPushButton('주식 조회', self)
        search_btm.move(20, 170)
        search_btm.clicked.connect(self.subject_search)

        min_btn = QPushButton('분봉 조회', self)
        min_btn.move(20, 220)
        min_btn.clicked.connect(self.minute_data)

        buy_btn = QPushButton('매수버튼', self)
        buy_btn.move(20, 270)
        buy_btn.clicked.connect(self.stock_buy_order)

        sale_btn = QPushButton('매도 버튼', self)
        sale_btn.move(20, 320)
        sale_btn.clicked.connect(self.stock_sale_order)

        # 기능 테스트(테스트 용도로 사용)
        test_btn3 = QPushButton('기능 테스트 정지', self)
        test_btn3.move(20, 470)
        test_btn3.clicked.connect(self.real_data_disconnect)

        test_ = QPushButton('정정 테스트', self)
        test_.move(20, 570)
        test_.clicked.connect(self.test)

        # 데이터 수신 이벤트
        self.kiwoom.OnReceiveTrData.connect(self.receive_trdata)

    def test(self):
        self.stock_buy_order()
        time.sleep(1)
        self.stock_sale_order(price=40.00)
        # self.stock_buy_order()

    def run(self, tickPrice, bongPrice, tickFlag, bongFlag, sale_time, debug_flag):
        global head, type_sell, type_buy, bongP, lastBongPrice, lastTickPrice, log_file_b, log_file_t, log_file_tran
        print('run test', tickPrice, bongPrice, ', 시간 : ', sale_time)
        if tickPrice is None:
            return
        if lastTickPrice == 0:
            lastTickPrice = tickPrice
            log_file_t.write('시간: ' + str(sale_time) + ' TickPrice: ' + str(tickPrice) + '\n')
            log_file_t.flush()
            return
        if bongFlag and lastBongPrice == 0:
            log_file_b.write('시간: ' + str(sale_time) + ' BongPrice: ' + ' ' + str(bongPrice) + ' BongP: ' + str(bongP) + '\n')
            log_file_b.flush()
            lastBongPrice = bongPrice

        curr = head
        while curr is not None:
            tickSold = False
            if tickFlag:
                if tickPrice > lastTickPrice:
                    curr.tickP += 1
                elif tickPrice < lastTickPrice:
                    curr.tickP -= 1
                if curr.type == type_buy:
                    # Option2: 매수거래가 3틱이상 올랐을때 매도
                    if curr.tickP == 3:
                        print('3틱 매수거래 상승 Option2')
                        print('(Tick)매수 +익절 $' + str(curr.price) + '에 ' + str(curr.count) + '개 $' + str(tickPrice))
                        log_file_tran.write(str(sale_time) + ' opt2_(Tick)매수 +익절 $' + str(curr.price) + '에 ' + str(curr.count) + '개를 $' + str(tickPrice) + '에\n')
                        # MyWindow().stock_sale_order()
                        # self.stock_buy_order()
                        # 익절은 예약에서 알아서 팔림
                        remove_elem(curr)
                        tickSold = True
                    # Option4: 매수거래가 6틱이상 하락했을때 매도
                    elif curr.tickP == -6:
                        print('a매수 6틱 하락 Option4')
                        print('(Tick)매수 -손절 $' + str(curr.price) + '에 ' + str(curr.count) + '개 $' + str(tickPrice))
                        log_file_tran.write(str(sale_time) + ' opt4_(Tick)매수 -손절 $' + str(curr.price) + '에 ' + str(curr.count) + '개를 $' + str(tickPrice) + '에\n')
                        # MyWindow().stock_sale_order()
                        # self.stock_sale_wati()
                        # time.sleep(1)
                        # self.stock_sale_order()
                        remove_elem(curr)
                        tickSold = True
                        self.stock_sale_wati()
                        # time.sleep(1)
                        # self.stock_sale_order()

                else:
                    # Option2_reverse: 매도거래가 3틱이상 내렸을 때 매도
                    if curr.tickP == -3:
                        print('매도 3틱 하락 Option2_reverse')
                        print('(Tick)매도 +익절 $' + str(curr.price) + '에 ' + str(curr.count) + '개 $' + str(tickPrice))
                        log_file_tran.write(str(sale_time) + ' opt2_r(Tick)매도 +익절 $' + str(curr.price) + '에 ' + str(curr.count) + '개를 $' + str(tickPrice) + '에\n')
                        # MyWindow().stock_sale_order()
                        # self.stock_sale_order()
                        remove_elem(curr)
                        tickSold = True

                    # Option4_reverse: 매도거래가 6틱이상 상승했을때 매도
                    elif curr.tickP == 6:
                        print('매도 6틱 상승 Option4_reverse')
                        print('(Tick)매도 -손절 $' + str(curr.price) + '에 ' + str(curr.count) + '개 $' + str(tickPrice))
                        log_file_tran.write(str(sale_time) + ' opt4_r(Tick)매도 -손절 $' + str(curr.price) + '에 ' + str(curr.count) + '개를 $' + str(tickPrice) + '에\n')
                        # MyWindow().stock_sale_order()
                        # self.stock_buy_wait()
                        # time.sleep(1)
                        # self.stock_buy_order()
                        remove_elem(curr)
                        self.stock_buy_wait()
                        # time.sleep(1)
                        # print('---')
                        # self.stock_buy_order()
                        # print('===')
                        tickSold = True
            if bongFlag and bongPrice is not None and not tickSold:
                if bongPrice > lastBongPrice:
                    curr.bongP += 1
                elif bongPrice < lastBongPrice:
                    curr.bongP -= 1
                if curr.type == type_buy:
                    if curr.bongP == -1 and curr.bongCount == 1:
                        # Option3: 매수진입 직후 마이너스 봉일때 바로 팜
                        print('매수진입후 마이너스 Option3')
                        print('(Bong)매도 -손절 $' + str(curr.price) + '에 ' + str(curr.count) + '개 $' + str(bongPrice))
                        log_file_tran.write(str(sale_time) + ' opt3_(Bong)매도 -손절 $' + str(curr.price) + '에 ' + str(curr.count) + '개를 $' + str(bongPrice) + '에\n')
                        # MyWindow().stock_sale_order()
                        self.stock_sale_wati()
                        # time.sleep(1)
                        # self.stock_sale_order()
                        remove_elem(curr)
                else:
                    if curr.bongP == 1 and curr.bongCount == 1:
                        # Option3_reverse: 매도진입 직후 플러스 봉일때 바로 팜
                        print('option3 매도진입 플로스 Option3_reverse')
                        print('(Bong)매도 -손절 $' + str(curr.price) + '에 ' + str(curr.count) + '개 $' + str(bongPrice))
                        log_file_tran.write(str(sale_time) + ' opt3_r(Bong)매도 -손절 $' + str(curr.price) + '에 ' + str(curr.count) + '개를 $' + str(bongPrice) + '에\n')
                        # MyWindow().stock_sale_order()
                        self.stock_sale_wati()
                        # time.sleep(1)
                        # self.stock_sale_order()
                        remove_elem(curr)
                curr.bongCount += 1

            curr = curr.next

        if bongFlag and bongPrice is not None:
            if bongP <= -3:
                if bongPrice > lastBongPrice:
                    # 매수진입: bong 3번 내려갔다가 한번 오르면 삼
                    print(type(bongPrice), str(bongPrice), '봉진입 사는거')
                    pri = round(bongPrice + 0.03, 2)
                    # print('(Bong)매수 진입: $' + str(bongPrice) + '에 ' + str(numBought) + '개'+float(str(bongPrice))+0.03,'에 예약')
                    print('(Bong)매수 진입: $' + str(bongPrice) + '에 ' + str(numBought) + '개  : ', pri, '에 예약')
                    log_file_tran.write(str(sale_time) + ' (Bong)매수 진입: $' + str(bongPrice) + '에 ' + str(numBought) + '개  : '+ str(pri) + '에 예약\n')
                    # MyWindow().stock_buy_order()
                    self.stock_buy_order(bongPrice)

                    time.sleep(1)
                    print('예약중')
                    self.stock_sale_order(pri)
                    print('=====')
                    ll_append(Transaction(type_buy, bongPrice, numBought))
            elif bongP >= 3:
                if bongPrice < lastBongPrice:
                    # 매도진입: bong 3번 올랐다가 한번 내리면 삼
                    print(type(bongPrice), str(bongPrice), ' 봉진입 파는거')
                    pri = round(bongPrice - 0.03, 2)
                    print('(Bong)매도 진입: $' + str(bongPrice) + '에 ' + str(numBought) + '개  : ', pri, '에 예약')
                    log_file_tran.write(str(sale_time) + ' (Bong)매도 진입: $' + str(bongPrice) + '에 ' + str(numBought) + '개  : ' + str(pri) + '에 예약\n')
                    # MyWindow().stock_buy_order()
                    self.stock_sale_order(bongPrice)
                    time.sleep(1)
                    print('예약중')
                    self.stock_buy_order(pri)
                    print('=====')
                    ll_append(Transaction(type_sell, bongPrice, numBought))

            if bongPrice > lastBongPrice:
                if bongP > 0:
                    bongP += 1
                else:
                    bongP = 1

            elif bongPrice < lastBongPrice:
                if bongP < 0:
                    bongP -= 1
                else:
                    bongP = -1
            lastBongPrice = bongPrice
        if bongFlag:
            log_file_b.write('시간: ' + str(sale_time) + ' BongPrice: ' + ' ' + str(bongPrice) + ' BongP: ' + str(bongP) + '\n')
        lastTickPrice = tickPrice
        log_file_t.write('시간: ' + str(sale_time) + ' TickPrice: ' + str(tickPrice) + '\n')
        log_file_b.flush()
        log_file_t.flush()
        log_file_tran.flush()

    # ------ 주식 주문  start  -------

    # 주식 매수
    def stock_buy_order(self, price=0):
        print('매수중', price)
        #                             구분 , 화면번호 , 계좌 , 주문유형 ,종목코드, 개수,가격, stop가격, 거래구분, 주문번호
        if price == 0:
            data = self.kiwoom.SendOrder('주식매수', "1211", '7009039772', 2, COM_CODE, 1, str(price), "", "1", "")
        else:
            data = self.kiwoom.SendOrder('주식매수', "1211", '7009039772', 2, COM_CODE, 1, str(price), "", "2", "")
        print(data, '...')
        # self.kiwoom.SetInputValue('계좌번호', "7009039772")
        # self.kiwoom.SetInputValue("비밀번호", "0000")
        # self.kiwoom.SetInputValue('비밀번호입력매체', "00")  # 무조건 00
        # self.kiwoom.SetInputValue('종목코드', COM_CODE)
        # self.kiwoom.SetInputValue("매도수구분", "2")  # 1:매도, 2:매수
        # self.kiwoom.SetInputValue("해외주문유형", "1")  # 1:시장가, 2:지정가, 3:STOP, 4:StopLimit, 5:OCO, 6:IF DONE
        # self.kiwoom.SetInputValue("주문수량", "1")
        # self.kiwoom.SetInputValue("주문표시가격", "0")
        # self.kiwoom.SetInputValue("STOP구분", "0")  # 0:선택안함, 1:선택
        # self.kiwoom.SetInputValue("STOP표시가격", "")
        # self.kiwoom.SetInputValue("LIMIT구분", "0")  # 0:선택안함, 1:선택
        # self.kiwoom.SetInputValue("LIMIT표시가격", "")
        # self.kiwoom.SetInputValue("해외주문조건구분", "0")  # 0:당일, 6:GTD
        # self.kiwoom.SetInputValue("주문조건종료일자", "0")  # 0:당일, 6:GTD
        # self.kiwoom.SetInputValue("통신주문구분", "AP")  # 무조건 "AP" 입력
        #
        # data = self.kiwoom.CommRqData('주식주문', "opw10008", "", '0101')

    # 주식 매도
    def stock_sale_order(self, price=0):
        print('매도중', price)
        #                             구분 , 화면번호 , 계좌 , 주문유형 ,종목코드, 개수,가격, stop가격, 거래구분, 주문번호
        if price == 0:
            data = self.kiwoom.SendOrder('주식매도', "1212", '7009039772', 1, COM_CODE, 1, str(price), "", "1", "")
        else:
            data = self.kiwoom.SendOrder('주식매도', "1212", '7009039772', 1, COM_CODE, 1, str(price), "", "2", "")
        print(data, '...')

        #
        # # self.stock_buy_order()
        # self.kiwoom.SetInputValue('계좌번호', "7009039772")
        # self.kiwoom.SetInputValue("비밀번호", "0000")
        # self.kiwoom.SetInputValue('비밀번호입력매체', "00")  # 무조건 00
        # self.kiwoom.SetInputValue('종목코드', COM_CODE)
        # self.kiwoom.SetInputValue("매도수구분", "1")  # 1:매도, 2:매수
        # self.kiwoom.SetInputValue("해외주문유형", "1")  # 1:시장가, 2:지정가, 3:STOP, 4:StopLimit, 5:OCO, 6:IF DONE
        # self.kiwoom.SetInputValue("주문수량", "1")
        # self.kiwoom.SetInputValue("주문표시가격", "0")
        # self.kiwoom.SetInputValue("STOP구분", "0")  # 0:선택안함, 1:선택
        # self.kiwoom.SetInputValue("STOP표시가격", "")
        # self.kiwoom.SetInputValue("LIMIT구분", "0")  # 0:선택안함, 1:선택
        # self.kiwoom.SetInputValue("LIMIT표시가격", "")
        # self.kiwoom.SetInputValue("해외주문조건구분", "0")  # 0:당일, 6:GTD
        # self.kiwoom.SetInputValue("주문조건종료일자", "0")  # 0:당일, 6:GTD
        # self.kiwoom.SetInputValue("통신주문구분", "AP")  # 무조건 "AP" 입력
        #
        # data = self.kiwoom.CommRqData('주식주문', "opw10008", "", '0101')
        # print(data)

    # 주식 매도 정정 취소
    def stock_sale_modify(self, code):
        #                             구분 , 화면번호 , 계좌 , 주문유형 ,종목코드, 개수,가격, stop가격, 거래구분, 주문번호
        data = self.kiwoom.SendOrder('주식정정', "1213", '7009039772', 3, COM_CODE, 1, "0", "0", "2", str(code[6:]))
        print(data)
        time.sleep(1)
        self.stock_sale_order()

    # 주식 매수 정정 취소
    def stock_buy_modify(self, code):
        #                             구분 , 화면번호 , 계좌 , 주문유형 ,종목코드, 개수,가격, stop가격, 거래구분, 주문번호
        data = self.kiwoom.SendOrder('주식정정', "1213", '7009039772', 4, COM_CODE, 1, "0", "0", "2", str(code[6:]))
        print(data)
        time.sleep(1)
        self.stock_buy_order()

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
        global sale_time, real_bong
        # print(sRealType)
        if sRealType == "해외선물시세":
            # print('주식 체결 데이터')
            current_data = self.kiwoom.GetCommRealData(sRealType, 10)
            bong_price = None
            bongFlag = False
            # market_data = self.kiwoom.GetCommRealData(sJongmokCode, 16)
            tmp_time = int(self.kiwoom.GetCommRealData(sRealType, 20))
            if sale_time is None:
                sale_time = tmp_time
            if tmp_time // 100 > sale_time // 100:
                bong_price = real_bong
                real_bong = abs(float(str(current_data)))
                bongFlag = True
            else:
                real_bong = abs(float(str(current_data)))
            sale_time = tmp_time

            tick.append(current_data)
            # print(current_data,type(current_data))
            self.run(abs(float(str(current_data))), bong_price, True, bongFlag, str(sale_time), debugFlag)
            # print('현재가 : ', current_data)
            # # print('시가 : ' , market_data)
            # print('체결 시간 : ', sale_time)
            # print('등락 : ')
            # print('-' * 20)

    # 실시간 데이터  ( 종목에 대해 실시간 정보 요청을 실행함)
    def real_data(self):
        self.kiwoom.SetInputValue('종목코드', COM_CODE)
        self.kiwoom.SetInputValue('시간단위', "1")
        res = self.kiwoom.CommRqData('해외선물시세', 'opt10011', "0", 'opt10011')
        # print(res)
        #         # if res == 0:
        #         #     print('요청성공')
        #         # else:
        #         #     print('요청 실패')
        #         # time.sleep(1)
        self.kiwoom.OnReceiveRealData.connect(self.realData)

    # 실시간 데이터 디스커넥
    def real_data_disconnect(self):
        self.kiwoom.DisconnectRealData('opt10011')

    # 매도 미체결 취소 조회
    def stock_buy_wait(self):
        print('미체결 조회중')
        time.sleep(1)
        self.kiwoom.SetInputValue('계좌번호', "7009039772")
        self.kiwoom.SetInputValue("비밀번호", "0000")
        self.kiwoom.SetInputValue('비밀번호입력매체', "00")  # 무조건 00
        self.kiwoom.SetInputValue('종목코드', COM_CODE)
        self.kiwoom.SetInputValue('통화코드', "USD")
        self.kiwoom.SetInputValue('매도수구분', "1")
        res = self.kiwoom.CommRqData("매도미체결", "opw30001", "", "opw30001")

    # 매수 미체결 조회
    def stock_sale_wati(self):
        print('미체결 조회중')
        time.sleep(1)
        self.kiwoom.SetInputValue('계좌번호', "7009039772")
        self.kiwoom.SetInputValue("비밀번호", "0000")
        self.kiwoom.SetInputValue('비밀번호입력매체', "00")  # 무조건 00
        self.kiwoom.SetInputValue('종목코드', COM_CODE)
        self.kiwoom.SetInputValue('통화코드', "USD")
        self.kiwoom.SetInputValue('매도수구분', "2")
        res = self.kiwoom.CommRqData("매수미체결", "opw30001", "", "opw30001")

    # 데이터 수신중
    def receive_trdata(self, sScrNo, sRQName, sTrCode, sRecordName, sPreNext):
        # print(sRQName)
        if sRQName == "매도미체결":
            # dataCount = self.kiwoom.GetRepeatCnt(sTrCode, sRQName)
            # dataCount2 = self.kiwoom.GetChejanData(9203)
            num = self.kiwoom.GetCommData(sTrCode, sRQName, 0, "주문번호")
            # typ = self.kiwoom.GetCommData(sTrCode, sRQName, 0, "구븐")
            print(num)
            if int(num) > 0:
                self.stock_buy_modify(num)

        if sRQName == "매수미체결":
            # dataCount = self.kiwoom.GetRepeatCnt(sTrCode, sRQName)
            # dataCount2 = self.kiwoom.GetChejanData(9203)
            num = self.kiwoom.GetCommData(sTrCode, sRQName, 0, "주문번호")
            # typ = self.kiwoom.GetCommData(sTrCode, sRQName, 0, "구븐")
            print(num)
            if int(num) > 0:
                self.stock_sale_modify(num)

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
                minu.append(outputVal)
                # print(outputVal[1])
                #self.run(abs(float(str(outputVal[1]))), abs(float(str(outputVal[1]))), True, True, outputVal[0], debugFlag)
                # self.run(current_data,outputVal[1],True,True)
                # for idx, output in enumerate(outputVal):
                #     print(inputVal[idx] + ' : ' + output)
                # print('----------------')

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
        self.kiwoom.SetInputValue("종목코드", COM_CODE)
        res = self.kiwoom.CommRqData("주가조회", "opt10001", "0", "opt10001")
        print(res)

    def minute_data(self):
        self.kiwoom.SetInputValue("종목코드", COM_CODE)
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
    def __init__(self, typeIn, priceIn, count):
        self.type = typeIn
        self.price = priceIn
        self.count = count
        # 초기 세팅
        self.bongP = 0
        self.tickP = 0
        self.bongCount = 0
        # Doubly Linked List라서 prev & next 존재
        self.prev = None
        self.next = None


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
    if debugFlag:
        fileName_b = 'log' + COM_DATE + '_bong.txt'
        fileName_t = 'log' + COM_DATE + '_tick.txt'
        fileName_trans = 'log' + COM_DATE + '_거래.txt'
        log_file_b = open(fileName_b, 'w')
        log_file_t = open(fileName_t, 'w')
        log_file_tran = open(fileName_trans, 'w')
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
    # minu
    # tick
    data1 = pd.DataFrame(minu, index=None)
    data2 = pd.DataFrame(tick, index=None)
    data1.to_csv('분봉.csv', index=None)
    data2.to_csv('틱.csv', index=None)
