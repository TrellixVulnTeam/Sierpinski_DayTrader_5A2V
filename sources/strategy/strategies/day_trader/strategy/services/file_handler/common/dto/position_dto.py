class PositionDto:

    def __init__(self,pSymbol=None,pExchange=None,pSide=None,pQty=None,pAccount=None,
                 pOrderType=None,pLimitPrice=None,pBroker=None,pStrategy=None):
        self.Symbol=pSymbol
        self.Exchange=pExchange
        self.Side = pSide
        self.Qty = pQty
        self.Account = pAccount
        self.OrderType = pOrderType
        self.LimitPrice = pLimitPrice
        self.Broker = pBroker
        self.Strategy = pStrategy
