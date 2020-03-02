"""
 tickList =[2045, 2040, 2045, 2040, 2045, 2040, 2040, 2045, 2045, 2045, 2050, 2045, 2050, 2045, 2045, 2045, 2045, 2050, 2045,
     2045, 2045, 2045, 2050, 2045, 2050, 2045, 2045, 2050, 2045, 2045, 2050, 2045, 2050, 2050, 2045, 2050, 2050, 2045,
     2050, 2045, 2045, 2045, 2045, 2040, 2045, 2045, 2045, 2045, 2040, 2040, 2045, 2045, 2045, 2040, 2045, 2040, 2040,
     2045, 2040, 2045, 2040, 2045, 2040, 2040, 2040, 2040, 2040, 2040, 2040, 2040, 2040, 2035, 2040, 2035, 2035, 2040,
     2040, 2035, 2035, 2035, 2035, 2035, 2035, 2040, 2040, 2035, 2040, 2035]

    bongList = [2035, 2045, 2050, 2050, 2055, 2060, 2055, 2055, 2050, 2050]

"""
head = None


def run():
    global head
    # bongList = [600, 500, 400, 300, 400, 300, 200, 100]
    # tickList = [600, 550, 500, 450, 400, 350, 300, 350, 400, 350, 300, 250, 200, 150, 100]

    #bong에 팔아야함 (tick으로 팔면 안됨)
    bongList = [600, 500, 400, 300, 400, 500, 300, 200, 100]
    tickList = [600, 550, 500, 450, 400, 350, 300, 350, 400, 450, 500, 350, 300, 250, 200, 150, 100]

    # bongList = [600, 500, 500, 400, 300, 400, 300, 600, 700]
    bongMinus = 0
    bongPlus = 0
    tickMinus = 0
    tickPlus = 0
    # HardCoded
    numBought = 10
    curr = None
    prev = None
    dest = len(tickList)
    tickPrice = 0
    tickCount = 0
    bongPrice = 0
    bongFlag = False
    #tick과 Bong비율 default: 60초
    #디버깅위해 2초로 설정
    divideBy = 2
    price = bongList[0]

    while tickCount < dest:
        tickPrice = tickList[tickCount]
        if bongPrice != bongList[tickCount // divideBy]:
            #Bong은 60번에 한번만 수행
            bongPrice = bongList[tickCount // divideBy]
            bongFlag = True

        curr = head
        while curr is not None:
            tickSold = False
            if tickPrice > curr.price:
                curr.tickPlus += 1
                curr.tickMinus = 0
            elif tickPrice < curr.price:
                curr.tickPlus = 0
                curr.tickMinus += 1
            #Option2: 3틱이상 올랐을때 매도
            if curr.tickPlus >= 3:
                print('(Tick)$' + str(curr.price) + '에 ' + str(curr.count) + '개 $' + str(tickPrice) + '에 익절')
                remove_elem(curr)
                tickSold = True
            #Option4: 6틱이상 하락했을때 매도
            elif curr.tickMinus == 6:
                print('(Tick)$' + str(curr.price) + '에 ' + str(curr.count) + '개 $' + str(bongPrice) + '에 손절')
                remove_elem(curr)
                tickSold = True

            if bongFlag and not tickSold:
                if bongPrice > curr.price:
                    curr.bongPlus += 1
                    curr.bongMinus = 0
                elif bongPrice < curr.price:
                    curr.bongMinus += 1
                    curr.bongPlus = 0
                if curr.bongMinus == 1 and curr.bongCount == 1:
                    # Option3: 진입 직후 마이너스 봉일때 바로 팜
                    print('(Bong)$' + str(curr.price) + '에 ' + str(curr.count) + '개 $' + str(bongPrice) + '에 손절')
                    remove_elem(curr)
                curr.bongCount += 1
            prev = curr
            curr = curr.next

        if bongFlag:
            if bongMinus >= 3:
                if bongPrice > price:
                    #진입: bong 3번 오르면 삼
                    print('(Bong)진입: ' + str(bongPrice))
                    ll_append(Tran_DListNode(bongPrice, 0, 0, 0, 0, numBought))

            if bongPrice > price:
                bongPlus += 1
                bongMinus = 0

            elif bongPrice < price:
                bongMinus += 1
                bongPlus = 0
            price = bongPrice

        tickCount += 1


# Node
class Tran_DListNode:

    def __init__(self, price, bongPlus, bongMinus, tickPlus, tickMinus, count):
        self.price = price
        self.bongPlus = bongPlus
        self.bongMinus = bongMinus
        self.tickPlus = tickPlus
        self.tickMinus = tickMinus
        self.count = count
        self.prev = None
        self.next = None
        self.bongCount = 0


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
    run()
