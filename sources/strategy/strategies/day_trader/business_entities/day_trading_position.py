from sources.framework.business_entities.securities.security import *
from sources.framework.business_entities.market_data.candle_bar import *
from sources.framework.common.enums.Side import *
from sources.framework.common.enums.PositionsStatus import PositionStatus

from scipy import stats
import json
import statistics
import time
from datetime import datetime, timedelta
from json import JSONEncoder

#region Consts


#endregion

class DayTradingPosition():

    #region Constructor

    def __init__(self,id ,security,shares,active,routing,open):
        self.Id=id
        self.Security = security

        self.MarketData = None
        self.OpenMarketData=None

        self.SharesQuantity=shares
        self.Active=active

        self.ExecutionSummaries={}
        self.Routing =routing
        self.Open=open

    def ResetExecutionSummaries(self):
        self.ExecutionSummaries = {}

    def ResetProfitCounters(self,now):
        self.OpenMarketData=None
        self.MarketData = None

    #endregion

    #region Static Methods

    #endregion

    #region Private Methods

    #endregion

    #region Private Util/Aux

    #endregion

    #region Manual Trading Rules

    #endregion

    #region Strong and simple Terminal


    #endregion
