class CSVConstants:

    #region Column Consts

    @staticmethod
    def _SIMPLE_SYMBOL():
        return 0

    @staticmethod
    def _SIMPLE_QTY():
        return 1

    @staticmethod
    def _EXTENDED_SYMBOL():
        return 0

    @staticmethod
    def _EXTENDED_EXCHANGE():
        return 1

    @staticmethod
    def _EXTENDED_SIDE():
        return 2

    @staticmethod
    def _EXTENDED_QTY():
        return 3

    @staticmethod
    def _EXTENDED_ACCOUNT():
        return 4

    @staticmethod
    def _EXTENDED_ORDER_TYPE():
        return 5

    @staticmethod
    def _EXTENDED_LIMIT_PRICE():
        return 6

    @staticmethod
    def _EXTENDED_BROKER():
        return 7

    @staticmethod
    def _EXTENDED_STRATEGY():
        return 8

    #endregion

    #region CSV Side Values
    @staticmethod
    def _SIDE_BUY():
        return "B"

    @staticmethod
    def _SIDE_SELL_CLOSE():
        return "S"

    @staticmethod
    def _SIDE_SELL_SHORT():
        return "SS"

    @staticmethod
    def _SIDE_BUY_TO_CLOSE():
        return "BS"

    #endregion

    # region CSV Order Type Values
    @staticmethod
    def _ORD_TYPE_MARKET():
        return "MKT"

    @staticmethod
    def _ORD_TYPE_LIMIT():
        return "LMT"

    # endregion

    # region CSV Time In Force Values
    @staticmethod
    def _TIF_DAY():
        return "DAY"

    # endregion

    # region CSV Ord Status Values
    @staticmethod
    def _ORD_STATUS_NEW():
        return "NEW"

    @staticmethod
    def _ORD_STATUS_PARTIALLY_FILLED():
        return "PARTIALLY_FILLED"

    @staticmethod
    def _ORD_STATUS_FILLED():
        return "FILLED"

    @staticmethod
    def _ORD_STATUS_DONE_FOR_DAY():
        return "DONE_FOR_DAY"

    @staticmethod
    def _ORD_STATUS_CANCELED():
        return "CANCELED"

    @staticmethod
    def _ORD_STATUS_PENDING_CANCEL():
        return "PENDING_CANCEL"

    @staticmethod
    def _ORD_STATUS_STOPPED():
        return "STOPPED"

    @staticmethod
    def _ORD_STATUS_REJECTED():
        return "REJECTED"

    @staticmethod
    def _ORD_STATUS_SUSPENDED():
        return "SUSPENDED"
    @staticmethod
    def _ORD_STATUS_PENDING_NEW():
        return "PENDING_NEW"
    @staticmethod
    def _ORD_STATUS_CALCULATED():
        return "CALCULATED"
    @staticmethod
    def _ORD_STATUS_EXPIRED():
        return "EXPIRED"
    @staticmethod
    def _ORD_STATUS_ACCEPTED_FOR_BIDDING():
        return "ACCEPTED_FOR_BIDDING"
    @staticmethod
    def _ORD_STATUS_PENDING_REPLACE():
        return "PENDING_REPLACE"
    @staticmethod
    def _ORD_STATUS_REPLACED():
        return "REPLACED"
    @staticmethod
    def _ORD_STATUS_UNDEFINED():
        return "UNDEFINED"

    # endregion