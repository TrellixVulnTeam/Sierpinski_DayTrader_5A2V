class TradingSignal():

    def __init__(self, symbol=None, side=None,date=None,tradeId = None,creationTime=None,
                 lastUpdateTimestamp=None):
        self.Symbol=symbol
        self.Side = side
        self.Date=date
        self.TradeId = tradeId
        self.CreationTime=creationTime
        self.LastUpdateTimestamp=lastUpdateTimestamp


