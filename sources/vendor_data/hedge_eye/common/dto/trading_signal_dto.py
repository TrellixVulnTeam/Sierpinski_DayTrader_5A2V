from sources.framework.common.enums.Side import Side

_BUY="BUY"
_SELL="SELL"
_UNK="UNKNOWN"
class TradingSignalDto:
    def __init__(self, symbol,date,side,price):

        self.Symbol=symbol
        self.Date=date
        self.Side=side
        self.Price = price


    def GetSignalId(self):

        return "{}_{}_{}".format(self.Symbol,self.Date.date(),self.GetStrSide(self.Side))


    def GetStrSide(self,side):

       if (side==Side.Buy):
           return _BUY
       elif (side == Side.Sell):
           return _SELL
       elif (side == Side.SellShort):
           return _SELL
       elif (side == Side.BuyToClose):
           return _BUY
       else:
           return _UNK



