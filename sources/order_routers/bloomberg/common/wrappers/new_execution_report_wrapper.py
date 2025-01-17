from sources.framework.common.wrappers.wrapper import Wrapper
from sources.framework.common.enums.Actions import *
from sources.framework.common.enums.fields.execution_report_field import *
from sources.framework.common.enums.ExecType import *
from sources.framework.common.enums.OrdStatus import *


import datetime


class NewExecutionReportWrapper(Wrapper):
    def __init__(self, pOrder):
        self.Order = pOrder

    def GetExecType(self):
        return ExecType.New

    def GetOrdStatus(self):
        return OrdStatus.New

    # region Public Methods

    def GetAction(self):
        return Actions.EXECUTION_REPORT

    def GetField(self, field):
        if field == None:
            return None

        if field == ExecutionReportField.ExecType:
            return self.GetExecType()
        elif field == ExecutionReportField.ExecID:
            return None  # default
        elif field == ExecutionReportField.OrdStatus:
            return self.GetOrdStatus()
        elif field == ExecutionReportField.OrdRejReason:
            return None
        elif field == ExecutionReportField.LeavesQty:
            return self.Order.OrderQty
        elif field == ExecutionReportField.CumQty:
            return 0
        elif field == ExecutionReportField.AvgPx:
            return None
        elif field == ExecutionReportField.Commission:
            return None  # default
        elif field == ExecutionReportField.Text:
            return "Fake New Order"
        elif field == ExecutionReportField.TransactTime:
            return datetime.datetime.now()  # default
        elif field == ExecutionReportField.LastQty:
            return None
        elif field == ExecutionReportField.LastPx:
            return None
        elif field == ExecutionReportField.LastMkt:
            return None
        elif field == ExecutionReportField.OrderID:
            return self.Order.OrderId
        elif field == ExecutionReportField.ClOrdID:
            return self.Order.ClOrdId
        elif field == ExecutionReportField.OrigClOrdID:
            return self.Order.OrigClOrdId
        elif field == ExecutionReportField.Symbol:
            return self.Order.Security.Symbol
        elif field == ExecutionReportField.OrderQty:
            return self.Order.OrderQty
        elif field == ExecutionReportField.CashOrderQty:
            return None
        elif field == ExecutionReportField.OrdType:
            return self.Order.OrdType
        elif field == ExecutionReportField.Price:
            return self.Order.Price
        elif field == ExecutionReportField.StopPx:
            return self.Order.StopPx
        elif field == ExecutionReportField.Currency:
            return self.Order.Currency
        elif field == ExecutionReportField.ExpireDate:
            return None
        elif field == ExecutionReportField.MinQty:
            return None
        elif field == ExecutionReportField.Side:
            return self.Order.Side
        elif field == ExecutionReportField.QuantityType:
            return self.Order.QuantityType
        elif field == ExecutionReportField.PriceType:
            return self.Order.PriceType
        elif field == ExecutionReportField.Order:
            return self.Order
        else:
            return None

    # endregion
