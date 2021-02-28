class PositionDto:

    def __init__(self,pSymbol=None,pExchange=None,pSide=None,pQty=None,
                 pOrderType=None,pLimitPrice=None,pBroker=None,pStrategy=None):
        self.Symbol=pSymbol
        self.Exchange=pExchange
        self.Side = pSide
        self.Qty = pQty
        self.OrderType = pOrderType
        self.LimitPrice = pLimitPrice
        self.Broker = pBroker
        self.Strategy = pStrategy
