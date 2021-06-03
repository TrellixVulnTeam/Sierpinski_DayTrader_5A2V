from sources.framework.common.wrappers.wrapper import Wrapper
from sources.framework.common.enums.Actions import *
from sources.framework.common.enums.fields.position_field import *
from sources.framework.common.enums.QuantityType import *
from sources.framework.common.enums.PriceType import *
from sources.framework.common.enums.Side import *
from sources.framework.common.enums.PositionsStatus import *

_ROUTING_BUY="B"
_ROUTING_SELL="S"
_ROUTING_BUY_COVER="BC"
_ROUTING_SELL_SHORT="SS"

class PositionWrapper(Wrapper):
    def __init__(self, pPosition):
        self.Position = pPosition

    #region Private Methods

    def GetSide(self):

        if(self.Position.Side==_ROUTING_BUY):
            return Side.Buy
        elif (self.Position.Side ==_ROUTING_SELL):
            return Side.Sell
        elif (self.Position.Side == _ROUTING_BUY_COVER):
            return Side.BuyToClose
        elif (self.Position.Side == _ROUTING_SELL_SHORT):
            return Side.SellShort
        else:
            raise Exception("Unknown side in input file {}".format(self.Position.Side))
    #endregion

    #region Public Methods

    def GetAction(self):
        """ See Wrapper class.

        Returns:
            Return an Action object.
        """
        return Actions.NEW_POSITION

    def GetField(self, field):
        """ See Wrapper class.

        Args:
            field ():

        Returns:
            Return an specific position field.
        """
        if field is None:
            return None

        if field == PositionField.Symbol:
            return self.Position.Symbol
        elif field == PositionField.PosId:
            return None
        elif field == PositionField.Exchange:
            return self.Position.SExchange
        elif field == PositionField.QuantityType:
            return QuantityType.SHARES
        elif field == PositionField.PriceType:
            return PriceType.FixedAmount
        elif field == PositionField.Qty:
            return self.Position.Qty
        elif field == PositionField.CashQty:
            return None
        elif field == PositionField.Percent:
            return None
        elif field == PositionField.ExecutionReports:
            return None
        elif field == PositionField.Orders:
            return None
        elif field == PositionField.Side:
            return self.GetSide()
        elif field == PositionField.PosStatus:
            return PositionStatus.Offline
        # elif field == PositionField.Security: #TODO Impl SecurityWrapper
        # return self.Position.Security
        elif field == PositionField.Currency:
            return None
        elif field == PositionField.SecurityType:
            return None
        elif field == PositionField.Account:
            return self.Position.Account
        elif field == PositionField.Broker:
            return self.Position.Broker
        elif field == PositionField.Strategy:
            return self.Position.Strategy
        elif field == PositionField.OrderType:
            return self.Position.OrderType
        elif field == PositionField.OrderPrice:
            return self.Position.LimitPrice
        else:
            return None

    #endregion

