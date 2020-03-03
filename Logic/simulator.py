
#Head for Doubly LinkedList(매수한 선물 리스트)
head = None

#진입 타입
type_sell = 1 #매수 진입
type_buy = 2 #매도 진입

#진입 판단 파라미터
bongMinus = 0
bongPlus = 0
tickMinus = 0
tickPlus = 0
#마지막 가격. 첫 가격으로 자동으로 바뀜.
lastPrice = 0

# Hardcoded
numBought = 10


def run(tickPrice, bongPrice, tickFlag, bongFlag):
    global head, type_sell, type_buy, bongMinus, bongPlus, tickMinus, tickPlus, lastPrice
    if tickPrice is None:
        return
    if lastPrice == 0:
        lastPrice = tickPrice
        return

    curr = head
    while curr is not None:
        tickSold = False
        if tickFlag:
            if tickPrice > curr.price:
                curr.tickPlus += 1
                curr.tickMinus = 0
            elif tickPrice < curr.price:
                curr.tickPlus = 0
                curr.tickMinus += 1
            if curr.type == type_buy:
                # Option2: 매수거래가 3틱이상 올랐을때 매도
                if curr.tickPlus >= 3:
                    print('(Tick)매수 +익절 $' + str(curr.price) + '에 ' + str(curr.count) + '개 $' + str(tickPrice))
                    remove_elem(curr)
                    tickSold = True
                # Option4: 매수거래가 6틱이상 하락했을때 매도
                elif curr.tickMinus == 6:
                    print('(Tick)매수 -손절 $' + str(curr.price) + '에 ' + str(curr.count) + '개 $' + str(bongPrice))
                    remove_elem(curr)
                    tickSold = True
            else:
                # Option2_reverse: 매도거래가 3틱이상 내렸을 때 매도
                if curr.tickMinus >= 3:
                    print('(Tick)매도 +익절 $' + str(curr.price) + '에 ' + str(curr.count) + '개 $' + str(tickPrice))
                    remove_elem(curr)
                    tickSold = True
                # Option4_reverse: 매도거래가 6틱이상 상승했을때 매도
                elif curr.tickPlus == 6:
                    print('(Tick)매도 -손절 $' + str(curr.price) + '에 ' + str(curr.count) + '개 $' + str(bongPrice))
                    remove_elem(curr)
                    tickSold = True
        if bongFlag and bongPrice is not None and not tickSold:
            if bongPrice > curr.price:
                curr.bongPlus += 1
                curr.bongMinus = 0
            elif bongPrice < curr.price:
                curr.bongMinus += 1
                curr.bongPlus = 0
            if curr.type == type_buy:
                if curr.bongMinus == 1 and curr.bongCount == 1:
                # Option3: 매수진입 직후 마이너스 봉일때 바로 팜
                    print('(Bong)매도 -손절 $' + str(curr.price) + '에 ' + str(curr.count) + '개 $' + str(bongPrice))
                    remove_elem(curr)
            else:
                if curr.bongPlus == 1 and curr.bongCount == 1:
                # Option3_reverse: 매도진입 직후 플러스 봉일때 바로 팜
                    print('(Bong)매도 -손절 $' + str(curr.price) + '에 ' + str(curr.count) + '개 $' + str(bongPrice))
                    remove_elem(curr)
            curr.bongCount += 1

        curr = curr.next

    if bongFlag and bongPrice is not None:
        if bongMinus >= 3:
            if bongPrice > lastPrice:
                # 매수진입: bong 3번 내려갔다가 한번 오르면 삼
                print('(Bong)매수 진입: $' + str(bongPrice) + '에 ' + str(numBought) + '개')
                ll_append(Transaction(type_buy, bongPrice, numBought))
        elif bongPlus >= 3:
            if bongPrice < lastPrice:
                # 매도진입: bong 3번 올랐다가 한번 내리면 삼
                print('(Bong)매도 진입: $' + str(bongPrice) + '에 ' + str(numBought) + '개')
                ll_append(Transaction(type_sell, bongPrice, numBought))

        if bongPrice > lastPrice:
            bongPlus += 1
            bongMinus = 0

        elif bongPrice < lastPrice:
            bongMinus += 1
            bongPlus = 0
        lastPrice = bongPrice


# Transaction: Node
class Transaction:
    def __init__(self, typeIn, priceIn, count):
        self.type = typeIn
        self.price = priceIn
        self.count = count
        #초기 세팅
        self.bongPlus = 0
        self.bongMinus = 0
        self.tickPlus = 0
        self.tickMinus = 0
        self.bongCount = 0
        #Doubly Linked List라서 prev & next 존재
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
    # bong에 팔아야함 (tick으로 팔면 안됨)
    # bongList = [600, 500, 400, 300, 400, 500, 300, 200, 100]
    # tickList = [600, 550, 500, 450, 400, 350, 300, 350, 400, 450, 500, 350, 300, 250, 200, 150, 100]
    bongList = [600, 500, 400, 300, 400, 500, 300, 200, 100, 400, 500, 600, 700, 400, 500, 300, 200, 100]
    tickList = [600, 550, 500, 450, 400, 350, 300, 350, 400, 450, 500, 350, 300, 250, 200, 150, 100, 400, 450, 500, 550, 600, 650, 700, 500, 400, 450, 500, 350, 300, 250, 200, 150, 100]
    tickCount = 0
    while tickCount < len(tickList):
        tp = tickList[tickCount]
        bp = None
        if tickCount % 2 == 0:
            bp = bongList[tickCount // 2]
        run(tp, bp, True, True)
        tickCount += 1
