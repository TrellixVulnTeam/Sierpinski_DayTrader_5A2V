from sources.framework.business_entities.securities.security import *
from sources.framework.business_entities.market_data.candle_bar import *
from sources.framework.common.enums.OrdType import OrdType
from sources.framework.common.enums.Side import *
from sources.framework.common.enums.PositionsStatus import PositionStatus

from scipy import stats
import json
import statistics
import time
from datetime import datetime, timedelta
from json import JSONEncoder

#region Consts
_BUY="BUY"
_SELL="SELL"
_UNK="UNKNOWN"

_ROUTING_BUY="B"
_ROUTING_SELL="S"
_ROUTING_BUY_COVER="BC"
_ROUTING_SELL_SHORT="SS"

_ORD_TYPE_MKT="MKT"
_ORD_TYPE_LMT="LMT"
_ORD_TYPE_ALERT="ALERT"


#endregion


class PotentialPosition():

    #region Constructor

    def __init__(self,id,security,size,side,broker=None,strategy=None,ordType=None,price=None):

        self.Id = id
        self.Security = security

        self.MarketData = None
        self.OpenMarketData=None

        self.Size=size
        self.Side = side
        self.OrdType=ordType
        self.Price=price

        self.Broker=broker
        self.Strategy=strategy

        self.Active=True
        self.ExecutionSummaries={}
        self.RoutedTradingSignals={}
        self.Routing =False
        self.Open=open

        self.RunningBacktest = False


    def ResetExecutionSummaries(self):
        self.ExecutionSummaries = {}

    def ResetProfitCounters(self,now):
        self.OpenMarketData=None
        self.MarketData = None

    #endregion

    #region Static Methods

    @staticmethod
    def GetPosIdPrefix(symbol, side):

        strSide = _BUY if side==Side.Buy else _SELL
        return "{}_{}".format(symbol,strSide)

    @staticmethod
    def GetPosId(symbol,side,qty):
        return  "{}_{}_{}".format(symbol,PotentialPosition.GetStrSide(side),qty)

    @staticmethod
    def GetRoutedTradingSignalId(symbol, side,date):

        strSide=PotentialPosition.GetStrSide(side)

        return "{}_{}_{}".format(symbol, strSide, date.date().strftime("%m%d%Y"))

    @staticmethod
    def GetStrSide(side):

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

    @staticmethod
    def GetEnumSide(side):

       if (side==_BUY):
           return Side.Buy
       elif (side == _SELL):
           return Side.Sell
       else:
           return Side.Unknown


    #endregion

    #region Private Methods

    #endregion

    #region Private Trading Methods

    def GetOpenSummaries(self):
        return list(filter(lambda x: x.Position.IsOpenPosition(), self.ExecutionSummaries.values()))

    def GetNetOpenShares(self):
        todaySummaries = sorted(list(filter(lambda x: x.CumQty >= 0 ,
                                            self.ExecutionSummaries.values())),
                                key=lambda x: x.Timestamp, reverse=False)

        netShares = 0
        for summary in todaySummaries:
            # first we calculate the traded positions
            if summary.GetTradedSummary() > 0:
                if summary.SharesAcquired():
                    netShares += summary.GetNetShares()
                else:
                    netShares -= summary.GetNetShares()

        return netShares

    def UpdateRouting(self):
        nextOpenPos = next(iter(list(filter(lambda x: x.Position.IsOpenPosition(), self.ExecutionSummaries.values()))),
                           None)
        self.Routing = nextOpenPos is not None

    #endregion


    #region Public Methods

    def GetRoutingSide(self):
        return self.Side
        # if self.Side==_ROUTING_BUY:
        #     return Side.Buy
        # elif self.Side==_ROUTING_SELL:
        #     return Side.Sell
        # elif self.Side==_ROUTING_SELL_SHORT:
        #     return Side.SellShort
        # elif self.Side==_ROUTING_BUY_COVER:
        #     return Side.BuyToClose
        # else:
        #     raise Exception("Invalid Potential Position Side {}".format(self.Side))

    def GetOrdType(self):

        if self.OrdType==_ORD_TYPE_MKT:
            return OrdType.Market
        elif self.OrdType==_ORD_TYPE_LMT:
            return OrdType.Limit
        elif self.OrdType==_ORD_TYPE_ALERT:
            return OrdType.Limit
        else:
            raise Exception("Invalid Order Type for Potential Position: {}".format(self.OrdType))

    def GetPrice(self,tradingSignalPrice):
        if self.OrdType==_ORD_TYPE_MKT:
            return None
        elif self.OrdType==_ORD_TYPE_LMT:
            return self.Price
        elif self.OrdType==_ORD_TYPE_ALERT:
            return tradingSignalPrice
        else:
            raise Exception("Invalid Order Type for Potential Position: {}".format(self.OrdType))


    #endregion




