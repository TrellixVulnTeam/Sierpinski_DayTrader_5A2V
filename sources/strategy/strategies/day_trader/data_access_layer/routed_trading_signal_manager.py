import pyodbc
import datetime
from sources.strategy.strategies.day_trader.business_entities.trading_signal import *
from sources.strategy.strategies.day_trader.business_entities.model_parameter import *

_id = 0
_symbol =1
_side = 2
_date =3
_trade_id =4
_creation_time =5
_last_update_timestamp =6


class RoutedTradingSignalManager():

    # region Constructors
    def __init__(self, connString):
        self.ConnParams = {}
        self.i = 0
        self.connection = pyodbc.connect(connString, autocommit=False)

    #endregion


    #region Private Methods

    def BuildRoutedTradingSignal(self, row):
        routedTradingSingal = TradingSignal(symbol=row[_symbol], side=row[_side],
                                            date=row[_date],
                                            tradeId=row[_trade_id], creationTime=row[_creation_time],
                                            lastUpdateTimestamp=[_last_update_timestamp])

        return routedTradingSingal

    #endregion


    #region Public Methods


    def GetTradingSignals(self,fromDate):
        routedTradingSignals=[]
        with self.connection.cursor() as cursor:
            params = (fromDate)
            cursor.execute("{CALL GetRoutedTradingSignals (?)}", params)

            for row in cursor:
                routedTradingSignals.append( self.BuildRoutedTradingSignal(row))

        return routedTradingSignals

    def PersistTradingSignal(self, tradingSignal):
        with self.connection.cursor() as cursor:
            params = (tradingSignal.Symbol,tradingSignal.Side,tradingSignal.Date,
                      tradingSignal.TradeId)
            cursor.execute("{CALL PersistRoutedTradingSignal (?,?,?,?)}", params)
            self.connection.commit()



    #endregion