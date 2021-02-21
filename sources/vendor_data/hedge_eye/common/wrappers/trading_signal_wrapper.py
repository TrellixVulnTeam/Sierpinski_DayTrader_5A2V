from sources.framework.common.wrappers.wrapper import Wrapper
from sources.framework.common.enums.Actions import *
from sources.framework.common.enums.fields.trading_signal_field import *


class TradingSignalWrapper(Wrapper):
    def __init__(self, pTradingSignal):
        self.TradingSignal = pTradingSignal

    def GetAction(self):
        return Actions.TRADING_SIGNAL

    def GetField(self, field):
        if field is None:
            return None

        if field == TradingSignalField.Symbol:
            return self.TradingSignal.Symbol
        elif field == TradingSignalField.Date:
            return self.TradingSignal.Date
        elif field == TradingSignalField.Side:
            return self.TradingSignal.Side
        elif field == TradingSignalField.Price:
            return self.TradingSignal.Price
        else:
            return None

