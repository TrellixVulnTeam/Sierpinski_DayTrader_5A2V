from sources.framework.common.enums.fields.trading_signal_field import TradingSignalField
from sources.framework.common.interfaces.icommunication_module import ICommunicationModule
from sources.framework.common.enums.fields.order_cancel_reject_field import *
from sources.framework.common.wrappers.error_wrapper import *
from sources.strategy.strategies.day_trader.common.configuration.configuration import Configuration
from sources.framework.common.converters.execution_report_converter import *
from sources.framework.common.enums.fields.execution_report_field import *
from sources.framework.common.abstract.base_communication_module import *
from sources.framework.common.wrappers.cancel_all_wrapper import *
from sources.strategy.strategies.day_trader.common.wrappers.cancel_position_wrapper import *
from sources.strategy.strategies.day_trader.common.converters.market_data_converter import *
from sources.framework.common.dto.cm_state import *
from sources.strategy.common.wrappers.position_list_request_wrapper import *
from sources.strategy.common.wrappers.position_wrapper import *
from sources.strategy.strategies.day_trader.common.wrappers.model_param_wrapper import *
from sources.strategy.data_access_layer.model_parameters_manager import *
from sources.strategy.data_access_layer.execution_summary_manager import *
from sources.strategy.strategies.day_trader.data_access_layer.routed_trading_signal_manager import *
from sources.strategy.data_access_layer.trading_signal_manager import *
from sources.strategy.strategies.day_trader.common.wrappers.portfolio_position_wrapper import *
from sources.strategy.strategies.day_trader.common.util.trading_signal_helper import *
from sources.framework.common.enums.fields.position_list_field import *
from sources.framework.util.log_helper import *
import threading
import time
import datetime
import uuid
import queue
import traceback



class DayTrader(BaseCommunicationModule, ICommunicationModule):

    def __init__(self):#test-develop

        self.LockCandlebar = threading.Lock()
        self.LockMarketData = threading.Lock()
        self.RoutingLock = threading.Lock()
        self.Configuration = None
        self.NextPostId = uuid.uuid4()

        self.PositionSecurities = {}

        self.PotentialPositions = {}
        self.PendingCancels = {}

        self.ModelParametersManager = None
        self.ExecutionSummaryManager = None
        self.RoutedTradingSignalManager = None

        self.ModelParametersHandler = None
        self.MarketData={}
        self.Candlebars={}
        self.HistoricalPrices={}

        self.InvokingModule = None
        self.OutgoingModule = None
        self.VendorModule=None

        self.FailureException = None
        self.ServiceFailure = False
        self.PositionsSynchronization = True

        self.OrdersQueue = queue.Queue(maxsize=1000000)
        self.SummariesQueue = queue.Queue(maxsize=1000000)
        self.PotentialPositionsQueue = queue.Queue(maxsize=1000000)

        self.LastSubscriptionDateTime = None

        self.WaitForFilledToArrive = False

    #region Util

    def ProcessCriticalError(self, exception,msg):
        self.FailureException=exception
        self.ServiceFailure=True
        self.DoLog(msg, MessageType.ERROR)

    def ProcessErrorInMethod(self,method,e, symbol=None):
        try:
            msg = "Error @{} for security {}:{} ".format(method, symbol if symbol is not None else "-",str(e))
            error = ErrorWrapper(Exception(msg))
            self.ProcessError(error)
            self.DoLog(msg, MessageType.ERROR)
        except Exception as e:
            self.DoLog("Critical error @DayTrader.ProcessError2: " + str(e), MessageType.ERROR)

    def TranslateSide(self, potPos,side):
        if self.Configuration.ImplementDetailedSides:

            if potPos is not None:
                if potPos.GetNetOpenShares()>0:
                    return side
                elif potPos.GetNetOpenShares() == 0 and side==Side.Sell:
                    return Side.SellShort
                elif potPos.GetNetOpenShares() == 0 and side==Side.Buy:
                    return Side.Buy
                else:
                    return Side.SellShort if side==Side.Sell else Side.BuyToClose
            else:
                return side
        else:
            return side

    def LoadConfig(self):
        self.Configuration = Configuration(self.ModuleConfigFile)
        return True

    def LoadRoutedTradingSignals(self):

        fromDate = datetime.datetime.now() - datetime.timedelta(days=self.Configuration.PastDaysForTradingSignals)

        routedTradingSignals = self.RoutedTradingSignalManager.GetTradingSignals(fromDate)

        for signal in routedTradingSignals:
            potPotIdPrefix = PotentialPosition.GetPosIdPrefix(signal.Symbol, signal.Side)
            routedSignalId = PotentialPosition.GetRoutedTradingSignalId(signal.Symbol, signal.Side, signal.CreationTime)
            self.DoLog("{}-Looking for potential positions to load routed trading signals".format(potPotIdPrefix), MessageType.INFO)

            potPositionsArr = list(filter(lambda x: x.Id.startswith(potPotIdPrefix), self.PotentialPositions.values()))

            for potPos in potPositionsArr:
                potPos.RoutedTradingSignals[routedSignalId]=signal
                self.DoLog("Asigning trading signal {} to potential position {}".format(routedSignalId,potPotIdPrefix),
                           MessageType.INFO)

    def LoadManagers(self):


        self.ExecutionSummaryManager = ExecutionSummaryManager(self.Configuration.DBConectionString)

        self.ModelParametersManager = ModelParametersManager(self.Configuration.DBConectionString)

        self.RoutedTradingSignalManager = RoutedTradingSignalManager(self.Configuration.DBConectionString)

        modelParams = self.ModelParametersManager.GetModelParametersManager()
        self.ModelParametersHandler = ModelParametersHandler(modelParams)

        self.LoadExecutionSummaryForPositions(self.ModelParametersHandler.Get(ModelParametersHandler.BACKWARD_DAYS_SUMMARIES_IN_MEMORY()))

    #endregion

    #region Threads

    def PublishSummaryThread(self,summary,potPos):
        try:
           pass
           #Nothing to publish as there is not a UI yet
        except Exception as e:
            self.DoLog("Critical error publishing summary: {}".format(str(e)), MessageType.ERROR)

    def PublishPortfolioPositionThread(self,potPos):
        try:
            pass
            #Nothing to publish as there is not a UI yet.
        except Exception as e:
            self.DoLog("Critical error publishing position: {}".format(str(e)), MessageType.ERROR)

    def PotentialPositionsPersistanceThread(self):

        while True:

            while not self.PotentialPositionsQueue.empty():

                try:
                    potPos = self.PotentialPositionsQueue.get()
                    #self.DayTradingPositionManager.PersistDayTradingPosition(potPos)
                    #Potential Positions not persisted yet
                except Exception as e:
                    self.DoLog("Error Saving Day Trading Position to DB: {}".format(e), MessageType.ERROR)
            time.sleep(int(1))

    def TradesPersistanceThread(self):

        while True:

            while not self.SummariesQueue.empty():

                try:
                    summary = self.SummariesQueue.get()
                    if summary.Position.PosId in self.PositionSecurities:
                        potPos = self.PositionSecurities[summary.Position.PosId]
                        self.ExecutionSummaryManager.PersistExecutionSummary(summary,
                                                                             potPos.Id if potPos is not None else None)
                    else:
                        self.ExecutionSummaryManager.PersistExecutionSummary(summary, None)

                except Exception as e:
                    self.DoLog("Error Saving Trades to DB: {}".format(e), MessageType.ERROR)
            time.sleep(int(1))

    def MarketSubscriptionsThread(self):
        while True:
            try:

                #TODO: implement market data subscr. if necessary
                pass
            except Exception as e:
                #traceback.print_exc()
                msg = "Critical error @DayTrader.MarketSubscriptionsThread:{}".format(str(e))
                self.ProcessCriticalError(e, msg)
                self.SendToInvokingModule(ErrorWrapper(Exception(msg)))
            finally:
                if self.RoutingLock.locked():
                    self.RoutingLock.release()

    def SendToInvokingModule(self, wrapper):
        try:
            pass
            # Not needed as there is not a UI
        except Exception as e:
            self.DoLog("Critical error @DayTrader.SendToInvokingModule.:{}".format(str(e)), MessageType.ERROR)

    def ProcessError(self, wrapper):
        try:
            pass

        except Exception as e:
            self.DoLog("Critical error @DayTrader.ProcessError: " + str(e), MessageType.ERROR)

    #endregion

    #region Private Methods

    def ProcessOrder(self,summary, isRecovery):
        order = summary.Position.GetLastOrder()

        if order is not None and summary.Position.IsFinishedPosition():
            self.OrdersQueue.put(order)
        else:
            self.DoLog("Order not found for position {}".format(summary.Position.PosId), MessageType.DEBUG)

    #If we are in testing mode, we use the Market Data as the real execution price for testing
    def ProcessExecutionPrices(self,potPos,execReport):

        if(self.Configuration.TestMode and execReport is not None and execReport.AvgPx is not None):
            if potPos.Security.Symbol in self.MarketData:
                md = self.MarketData[potPos.Security.Symbol]
                if md.Trade is not None:
                    execReport.AvgPx=md.Trade

    def UpdateManagedPosExecutionSummary(self,potPos, summary, execReport):

        self.ProcessExecutionPrices(potPos,execReport)
        summary.UpdateStatus(execReport, marketDataToUse= None)
        potPos.UpdateRouting() #order is important!
        if summary.Position.IsFinishedPosition():
            self.WaitForFilledToArrive = False

            LogHelper.LogPositionUpdate(self, "Managed Position Finished", summary, execReport)

            if summary.Position.PosId in self.PendingCancels:
                del self.PendingCancels[summary.Position.PosId]

        else:
            LogHelper.LogPositionUpdate(self, "Managed Position Updated", summary, execReport)

        self.SummariesQueue.put(summary)


    def ProcessOrderCancelReject(self,wrapper):

        try:
            orderId = wrapper.GetField(OrderCancelRejectField.OrderID)
            msg = wrapper.GetField(OrderCancelRejectField.Text)
            self.DoLog("Publishing cancel reject for orderId {} reason:{}".format(orderId,msg),MessageType.INFO)
            errWrapper = ErrorWrapper (Exception(msg))
            threading.Thread(target=self.ProcessError, args=(errWrapper,)).start()

        except Exception as e:
            self.DoLog("Critical error @DayTrader.ProcessOrderCancelReject: " + str(e), MessageType.ERROR)

    def CreateExecutionSummaryFromExecutionReport(self,posId,exec_report):
        extPos = Position(PosId=posId, Security=exec_report.Security, Side=exec_report.Side,
                          PriceType=exec_report.Order.PriceType, Qty=exec_report.OrderQty,
                          QuantityType=exec_report.Order.QuantityType, Account=exec_report.Order.Account,
                          Broker=exec_report.Order.Broker, Strategy=exec_report.Order.Strategy,
                          OrderType=exec_report.Order.OrdType, OrderPrice=exec_report.Order.Price)

        summary = ExecutionSummary(exec_report.TransactTime, extPos)
        summary.UpdateStatus(exec_report)

        LogHelper.LogPositionUpdate(self, "External Position Finished", summary, exec_report)

        return summary

    def ProcessExternalTrading(self,posId,exec_report, evalRouting = True):

        try:

            proceExtTradParam = self.ModelParametersHandler.Get(ModelParametersHandler.PROCESS_EXTERNAL_TRADING(),exec_report.Security.Symbol)

            pos_prefix = PotentialPosition.GetPosIdPrefix(exec_report.Order.Security.Symbol,exec_report.Order.Side)
            potPosKey = next(iter(list(filter(lambda x: x.startswith(pos_prefix) , self.PotentialPositions))), None)

            if potPosKey is not None and (proceExtTradParam is not None and proceExtTradParam.IntValue>0):
                potPos=self.PotentialPositions[potPosKey]
                if potPos.Routing and evalRouting:
                    raise Exception("External trading detected for security {}. It will be ignored as the security has other orders in progress!".format(exec_report.Security.Symbol))

                summary = self.CreateExecutionSummaryFromExecutionReport(posId,exec_report)

                self.PositionSecurities[posId] = potPos
                potPos.ExecutionSummaries[posId] = summary
                potPos.UpdateRouting()

                threading.Thread(target=self.PublishPortfolioPositionThread, args=(potPos,)).start()
                threading.Thread(target=self.PublishSummaryThread, args=(summary, potPos.Id)).start()

                self.SummariesQueue.put(summary)
            else:
                summary = self.CreateExecutionSummaryFromExecutionReport(posId, exec_report)
                self.SummariesQueue.put(summary)
                #self.DoLog("Ignoring external trading for security: {}".format(exec_report.Security.Symbol) , MessageType.INFO)
        except Exception as e:
            self.SendToInvokingModule(ErrorWrapper(e))

    def ProcessExecutionReport(self, wrapper):
        try:

            try:
                exec_report = ExecutionReportConverter.ConvertExecutionReport(wrapper)
            except Exception as e:
                self.DoLog("Discarding execution report with bad data: " + str(e), MessageType.INFO)
                #exec_report = ExecutionReportConverter.ConvertExecutionReport(wrapper)
                return

            pos_id = wrapper.GetField(ExecutionReportField.PosId)

            if pos_id is not None:

                self.RoutingLock.acquire(blocking=True)

                if pos_id in self.PositionSecurities:
                    potPos = self.PositionSecurities[pos_id]

                    if pos_id in potPos.ExecutionSummaries:

                        summary = potPos.ExecutionSummaries[pos_id]
                        self.UpdateManagedPosExecutionSummary(potPos,summary,exec_report)
                        self.ProcessOrder(summary, False)
                        threading.Thread(target=self.PublishPortfolioPositionThread, args=(potPos,)).start()
                        threading.Thread(target=self.PublishSummaryThread, args=(summary, potPos.Id)).start()
                        return CMState.BuildSuccess(self)
                    else:
                        self.DoLog("Received execution report for a managed position {} but we cannot find its execution summary".format(pos_id),MessageType.ERROR)
                else:
                    self.ProcessExternalTrading(pos_id,exec_report)
                    #self.DoLog("Received execution report for unknown PosId {}".format(pos_id), MessageType.INFO)
            else:
                raise Exception("Received execution report without PosId")
        except Exception as e:
            traceback.print_exc()
            self.DoLog("Critical error @DayTrader.ProcessExecutionReport: " + str(e), MessageType.ERROR)
            return CMState.BuildFailure(self, Exception=e)
        finally:
            if self.RoutingLock.locked():
                self.RoutingLock.release()

    def LoadExecutionSummaryForPositions(self, backDaysFromParam):

        if(backDaysFromParam is None or backDaysFromParam.IntValue is None):
            raise Exception("Config parameter BACKWARD_DAYS_SUMMARIES_IN_MEMORY was not specified!")

        now = datetime.datetime.utcnow()
        fromDate = now - datetime.timedelta(days=backDaysFromParam.IntValue)

        for potPos in self.PotentialPositions:
            summaries = self.ExecutionSummaryManager.GetExecutionSummaries(potPos,fromDate)
            self.DoLog("Loading {} summaries for security {}".format(len(summaries),potPos.Security.Symbol),MessageType.INFO)
            for summary in summaries:
                potPos.ExecutionSummaries[summary.Position.PosId]=summary
                self.PositionSecurities[summary.Position.PosId]=potPos

    def CancelAllPositions(self):

        for posId in self.PositionSecurities:
            potPos = self.PositionSecurities[posId]
            for sPosId in potPos.ExecutionSummaries:
                pos = potPos.ExecutionSummaries[sPosId]
                pos.PosStatus = PositionStatus.PendingCancel

        cancelWrapper = CancelAllWrapper()
        self.OutgoingModule.ProcessMessage(cancelWrapper)

    def UpdateManagedPositionOnInitialLoad(self,routePos):

        pot_pos_prefix = PotentialPosition.GetPosIdPrefix(routePos.Security.Symbol,routePos.Side)

        potPosKey = next(iter(list(filter(lambda x: x.startswith(pot_pos_prefix), self.PotentialPositions))), None)

        if potPosKey is None:
            return False

        potPos=self.PotentialPositions[potPosKey]

        try:
            summary = next(iter(list(filter(lambda x:    x.Position.GetLastOrder() is not None
                                                     and routePos.GetLastOrder() is not None
                                                     and x.Position.GetLastOrder().OrderId == routePos.GetLastOrder().OrderId,
                                 potPos.ExecutionSummaries.values()))), None)

            #if summary is not None and routePos.IsOpenPosition():
            if summary is not None:

                del potPos.ExecutionSummaries[summary.Position.PosId]
                del self.PositionSecurities[summary.Position.PosId]

                summary.Position.PosId = routePos.PosId
                potPos.ExecutionSummaries[summary.Position.PosId]=summary
                self.PositionSecurities[summary.Position.PosId]=potPos
                execReport=routePos.GetLastExecutionReport()

                self.DoLog("Final AvgPx on initial load for order id {}:Prev={} ".format(execReport.Order.OrderId,summary.AvgPx),MessageType.INFO)
                if self.Configuration.TestMode :
                    execReport.AvgPx=summary.AvgPx

                summary.UpdateStatus(execReport)
                self.DoLog("Final AvgPx on initial load for order id {}:Prev={} ".format(execReport.Order.OrderId,summary.AvgPx), MessageType.INFO)
                potPos.UpdateRouting()

                self.SummariesQueue.put(summary)
                self.PotentialPositionsQueue.put(potPos)
                #self.ExecutionSummaryManager.PersistExecutionSummary(summary, dayTradingPos.Id)
                threading.Thread(target=self.PublishSummaryThread, args=(summary, potPos.Id)).start()
                threading.Thread(target=self.PublishPortfolioPositionThread, args=(potPos,)).start()
                return True
            else:
                self.DoLog("External trading detected for Symbol:{}".format(potPos.Security.Symbol),MessageType.INFO)
                return False

        except Exception as e:
            msg = "Critical error @DayTrader.UpdateManagedPositionOnInitialLoad for symbol {} :{}".format(potPos.Security.Symbol,e)
            self.ProcessCriticalError(e,msg )
            self.SendToInvokingModule(ErrorWrapper(Exception(msg)))
            return True

    def ClosedUnknownStatusSummaries(self,positions):

        for potPos in self.PotentialPositions.values():

            for summary in potPos.ExecutionSummaries.values():

                if summary.Position.IsOpenPosition():

                    exchPos =   next(iter(list(filter(lambda x: x.GetLastOrder() is not None and summary.Position.GetLastOrder() is not None
                                                                and summary.Position.GetLastOrder().OrderId == x.GetLastOrder().OrderId,positions))), None)
                    if exchPos is None:
                        summary.Position.PosStatus=PositionStatus.Unknown
                        summary.LeavesQty = 0
                        summary.Position.LeavesQty=0
                        self.SummariesQueue.put(summary)
                        threading.Thread(target=self.PublishSummaryThread, args=(summary, potPos.Id)).start()

    def ProcessPositionList(self, wrapper):
        try:
            success = wrapper.GetField(PositionListField.Status)

            if success:
                positions = wrapper.GetField(PositionListField.Positions)

                self.DoLog("Received list of Open Positions: {} positions".format(Position.CountOpenPositions(self, positions)),
                    MessageType.INFO)
                i=0

                self.RoutingLock.acquire(blocking=True)
                for pos in positions:

                    summary = ExecutionSummary(datetime.datetime.now(), pos)
                    if pos.GetLastExecutionReport() is not None:

                        if not self.UpdateManagedPositionOnInitialLoad(pos):
                            processExtTradParam = self.ModelParametersHandler.Get(ModelParametersHandler.PROCESS_EXTERNAL_TRADING(), pos.Security.Symbol)
                            if processExtTradParam.IntValue == 1:
                                self.ProcessExternalTrading(pos.PosId,pos.GetLastExecutionReport(),evalRouting=False)
                            else:
                                self.DoLog("Discarding execution report for unknown PosId{}".format(pos.PosId),MessageType.ERROR)
                    else:
                        self.DoLog("Could not find execution report for position id {}".format(pos.PosId),MessageType.ERROR)
                self.ClosedUnknownStatusSummaries(positions)

                self.DoLog("Process ready to receive commands and trade", MessageType.INFO)
            else:
                exception= wrapper.GetField(PositionListField.Error)
                raise exception

        except Exception as e:
            self.ProcessCriticalError(e,"Critical error @DayTrader.ProcessPositionList:{}".format(e))
        finally:
            self.PositionsSynchronization = False
            if self.RoutingLock.locked():
                self.RoutingLock.release()

    def DoPersistRoutedTradingSignal(self,routedTradingSingal):
        self.RoutedTradingSignalManager.PersistTradingSignal(routedTradingSingal)

    def ProcessTradingSignal(self,wrapper):

        date = wrapper.GetField(TradingSignalField.Date)
        side = wrapper.GetField(TradingSignalField.Side)
        symbol = wrapper.GetField(TradingSignalField.Symbol)
        price = wrapper.GetField(TradingSignalField.Price)

        self.DoLog("Received trading signal for Symbol {} date {} side {} and price {}"
                   .format(symbol,date,side,price),MessageType.INFO)

        if(date.date()!=datetime.datetime.now().date()):
            self.DoLog("Discarding old trading signal for Symbol {} date {} side {} and price {}"
                       .format(symbol, date, side, price), MessageType.INFO)
            return

        try:
            potPotIdPrefix = PotentialPosition.GetPosIdPrefix(symbol, side)
            self.DoLog("{}-Looking for potential positions (from input file)".format(potPotIdPrefix),MessageType.INFO)

            self.RoutingLock.acquire(blocking=True)

            potPositionsArr = list(filter(lambda x: x.startswith(potPotIdPrefix), self.PotentialPositions))
            self.DoLog("{}-Found {} potential positions".format(potPotIdPrefix,len(potPositionsArr)),MessageType.INFO)

            if self.RoutingLock.locked():
                self.RoutingLock.release()

            for potPosKey in potPositionsArr:

                potPos=self.PotentialPositions[potPosKey]
                routedTradingSignalId = PotentialPosition.GetRoutedTradingSignalId(symbol, side, date)
                if routedTradingSignalId in potPos.RoutedTradingSignals:
                    self.DoLog("Discarding Trading Signal because it has already been routed: symbol={} Side={} Date={}"
                               .format(symbol,side,date),MessageType.ERROR)
                    self.DoPersistRoutedTradingSignal(potPos.RoutedTradingSignals[routedTradingSignalId])
                    return

                routePos = Position(PosId=self.NextPostId,
                                  Security=Security(Symbol=symbol, Exchange=self.Configuration.DefaultExchange,
                                                    SecType=potPos.Security.SecurityType),
                                  Side=potPos.GetRoutingSide(), PriceType=PriceType.FixedAmount, Qty=potPos.Size,
                                  QuantityType=QuantityType.SHARES,
                                  Account=self.Configuration.DefaultAccount,
                                  Broker=potPos.Broker, Strategy=potPos.Strategy,
                                  OrderType=potPos.GetOrdType(),
                                  OrderPrice=potPos.GetPrice(price))

                routePos.ValidateNewPosition()
                potPos.ExecutionSummaries[routePos.PosId]=ExecutionSummary(datetime.datetime.now(), routePos)

                self.NextPostId = uuid.uuid4()
                self.PositionSecurities[routePos.PosId] = potPos

                self.DoLog("Routing position for Symbol {} date {} side {} and price {}".format(symbol,date,side,price),MessageType.INFO)
                posWrapper = PositionWrapper(routePos)
                self.OrderRoutingModule.ProcessMessage(posWrapper)

                self.DoLog("Persisting position for Symbol {} date {} side {} and price {}" .format(symbol, date, side, price), MessageType.INFO)

                routedTradingSignal = TradingSignal(symbol=symbol,side=PotentialPosition.GetStrSide(side),date=date, tradeId=None)
                potPos.RoutedTradingSignals[routedTradingSignalId]=routedTradingSignal
                self.DoPersistRoutedTradingSignal(routedTradingSignal)

                self.DoLog("{}-Trading signal successfully routed for symbol {} and side {} at {} ".format(potPotIdPrefix,symbol,side,price), MessageType.INFO)
        except Exception as e:
            traceback.print_exc()
            self.ProcessErrorInMethod("@DayTrader.ProcessTradingSignal", e,symbol)

    def ProcessHistoricalPrices(self,wrapper):

        security = MarketDataConverter.ConvertHistoricalPrices(wrapper)
        try:
            #TODO: Update daily historical data
            pass
        except Exception as e:
            self.ProcessErrorInMethod("@DayTrader.ProcessHistoricalPrices",e,security.Symbol if security is not None else None)

    def RunClose(self,potPos,side,statisticalParam,candlebar, text=None, generic = False, closingCond = None):

        if potPos.Routing:
            for summary in potPos.GetOpenSummaries():

                # we just cancel summaries whose side is different than the closing side. We don't want to cancel the close
                if  (
                    summary.Position.PosId not in self.PendingCancels  and
                    (potPos.GetNetOpenShares() == 0 or summary.Position.Side != side)):
                    self.DoLog("Cancelling order previously to closing position for symbol {}".format(potPos.Security.Symbol), MessageType.INFO)
                    self.PendingCancels[summary.Position.PosId] = summary
                    cxlWrapper = CancelPositionWrapper(summary.Position.PosId)
                    state= self.OrderRoutingModule.ProcessMessage(cxlWrapper)
                    if not state.Success:
                        self.ProcessError(state.Exception)

        else:
            netShares = potPos.GetNetOpenShares()
            if netShares!=0: #if there is something to close
                # print("Now we do close positions for security {} for net open shares {}".format(dayTradingPos.Security.Symbol, netShares))

                self.ProcessNewPositionReqManagedPos(potPos, side, netShares if netShares > 0 else netShares * (-1),
                                                     self.Configuration.DefaultAccount, text=text)

                if generic:
                    self.TradingSignalHelper.PersistTradingSignal(potPos, TradingSignalHelper._ACTION_CLOSE(),
                                                                  self.TranslateSide(potPos, side), statisticalParam,
                                                                  candlebar, self, closingCond)
                else:
                    self.TradingSignalHelper.PersistMACDRSITradingSignal(potPos, TradingSignalHelper._ACTION_CLOSE(),
                                                                         self.TranslateSide(potPos, side), candlebar,
                                                                         self, closingCond)


    def ProcessPortfolioPositionsRequestThread(self,wrapper):
        try:

            pass
            #not implemented as there is not a UI
        except Exception as e:
            msg="Critical error @DayTrader.ProcessPortfolioPositionsRequestThread.:{}".format(str(e))
            self.ProcessCriticalError(e,msg)
            self.ProcessError(ErrorWrapper(Exception(msg)))

    def AssignRoutedTradingSignalToPotentialPos(self,potPos,routedTradingSignals):

        if routedTradingSignals is not None:
            for signal in list(filter(lambda x:     x.Symbol == potPos.Security.Symbol
                                                and x.Side == PotentialPosition.GetStrSide(potPos.Side)
                            , routedTradingSignals)):
                routedSignalId = PotentialPosition.GetRoutedTradingSignalId(signal.Symbol,
                                                                            PotentialPosition.GetEnumSide(signal.Side),
                                                                            signal.Date)
                self.DoLog("Assigning already routed trading signal {} to position {}"
                           .format(routedSignalId, potPos.Id), MessageType.INFO)

                potPos.RoutedTradingSignals[routedSignalId]=signal



    #we just route a position and ignore the answers
    def ProcessNewPositionReqSinglePos(self,wrapper,routedTradingSignals):
        try:

            symbol = wrapper.GetField(PositionField.Symbol)
            secType = wrapper.GetField(PositionField.SecurityType)
            side = wrapper.GetField(PositionField.Side)
            qty = int( wrapper.GetField(PositionField.Qty))
            ordType = wrapper.GetField(PositionField.OrderType)
            price = wrapper.GetField(PositionField.OrderPrice)
            broker = wrapper.GetField(PositionField.Broker)
            strategy = wrapper.GetField(PositionField.Strategy)

            self.RoutingLock.acquire(blocking=True)

            pot_pos_id=PotentialPosition.GetPosId(symbol,side,qty)
            potPos = PotentialPosition(pot_pos_id,
                                       security=Security(Symbol=symbol,SecType=secType),
                                       size=qty,side=side,broker=broker,strategy=strategy,
                                       ordType=ordType, price=price)

            self.PotentialPositions[pot_pos_id]=potPos

            self.AssignRoutedTradingSignalToPotentialPos(potPos,routedTradingSignals)

            self.DoLog("Created potential position from input file for symbol {} side {} qty {}"
                       .format(symbol,side,qty),MessageType.INFO)

        except Exception as e:
            traceback.print_exc()
            msg = "Exception @DayTrader.ProcessNewPositionReqSinglePos: {}!".format(str(e))
            self.ProcessCriticalError(e, msg)
            self.ProcessError(ErrorWrapper(Exception(msg)))
        finally:
            if self.RoutingLock.locked():
                self.RoutingLock.release()

    def ProcessNewPositionReqManagedPos(self, potPos, side,qty,account, price = None,stopLoss=None,
                                        takeProfit=None,closeEndOfDay=None, text=None):
        try:

            if potPos.Routing:
                return

            self.RoutingLock.acquire(blocking=True)

            side = self.TranslateSide(potPos, side)

            newPos = Position(PosId=self.NextPostId,
                              Security=potPos.Security,
                              Side=side, PriceType=PriceType.FixedAmount, Qty=qty, QuantityType=QuantityType.SHARES,
                              Account=account if account is not None else self.Configuration.DefaultAccount,
                              Broker=None, Strategy=None,
                              OrderType=OrdType.Market if price is None else OrdType.Limit,
                              OrderPrice=price)

            newPos.StopLoss=stopLoss
            newPos.TakeProfit=takeProfit
            newPos.CloseEndOfDay=closeEndOfDay

            newPos.ValidateNewPosition()

            summary = ExecutionSummary(datetime.datetime.now(), newPos)
            summary.Text=text
            potPos.ExecutionSummaries[self.NextPostId] = summary
            potPos.Routing=True
            self.PositionSecurities[self.NextPostId] = potPos
            self.NextPostId = uuid.uuid4()
            if self.RoutingLock.locked():
                self.RoutingLock.release()

            posWrapper = PositionWrapper(newPos)
            state = self.OrderRoutingModule.ProcessMessage(posWrapper)

            if state.Success:
                threading.Thread(target=self.PublishPortfolioPositionThread, args=(potPos,)).start()
                threading.Thread(target=self.PublishSummaryThread, args=(summary, potPos.Id)).start()
            else:
                del potPos.ExecutionSummaries[summary.Position.PosId]
                del self.PositionSecurities[summary.Position.PosId]
                potPos.Routing=False
                raise state.Exception

        finally:
            if self.RoutingLock.locked():
                self.RoutingLock.release()

    def ProcessNewPositionReqThread(self,wrapper,routedTradingSignals=None):
        try:

            self.ProcessNewPositionReqSinglePos(wrapper,routedTradingSignals)

        except Exception as e:
            msg = "Exception @DayTrader.ProcessNewPositionReqThread: {}!".format(str(e))
            #self.ProcessCriticalError(e, msg)
            self.ProcessError(ErrorWrapper(Exception(msg)))

    def ProcessCancelAllPositionReqThread(self,wrapper):
        try:
            state = self.OrderRoutingModule.ProcessMessage(wrapper)

            if not state.Success:
                self.ProcessError(ErrorWrapper(state.Exception))

        except Exception as e:
            msg = "Exception @DayTrader.ProcessCancelAllPositionReqThread: {}!".format(str(e))
            #self.ProcessCriticalError(e, msg)
            self.ProcessError(ErrorWrapper(Exception(msg)))

    def ProcessCancePositionReqThread(self,wrapper):
        try:

            posId = wrapper.GetField(PositionField.PosId)

            if posId is not None:

                self.RoutingLock.acquire(blocking=True)
                potPosKey = next(iter(list(filter(lambda x: x == posId, self.PotentialPositions))), None)
                self.RoutingLock.release()
                if potPosKey is not None:
                    potPos = self.PotentialPositions[potPosKey]
                    for routPosId in potPos.ExecutionSummaries:
                        summary = potPos.ExecutionSummaries[routPosId]
                        if summary.Position.IsOpenPosition():

                            if self.RoutingLock.locked():
                                self.RoutingLock.release()

                            cxlWrapper = CancelPositionWrapper(summary.Position.PosId)
                            state = self.OrderRoutingModule.ProcessMessage(cxlWrapper)

                            if not state.Success:
                                self.ProcessError(ErrorWrapper(state.Exception))
                else:
                    raise Exception("Could not find a daytrading position for Id {}".format(posId))
            else:
                raise Exception("You have to specify a position id to cancel a position")
        except Exception as e:
            msg = "Exception @DayTrader.ProcessCancePositionReqThread: {}!".format(str(e))
            # self.ProcessCriticalError(e, msg)
            self.ProcessError(ErrorWrapper(Exception(msg)))
        finally:
            if self.RoutingLock.locked():
                self.RoutingLock.release()

    def SendBulkModelParameters(self,parameters):
        try:
            for paramInMem in parameters:
                modelParmWrapper = ModelParameterWrapper(paramInMem)
                self.SendToInvokingModule(modelParmWrapper)
        except Exception as e:
            msg = "Critical Error @SendBulkModelParameters: {}!".format(str(e))
            self.ProcessError(ErrorWrapper(Exception(msg)))
            self.DoLog(msg, MessageType.ERROR)

    def ProcessCancePositionReq(self,wrapper):
        try:

            if self.PositionsSynchronization:
                raise Exception("The engine is in the synchronization process. Please try again later!")

            if self.ServiceFailure:
                return CMState.BuildFailure(self,Exception=self.FailureException)

            threading.Thread(target=self.ProcessCancePositionReqThread, args=(wrapper,)).start()

            return CMState.BuildSuccess(self)

        except Exception as e:
            msg = "Critical Error cancelling position to the exchange: {}!".format(str(e))
            self.ProcessCriticalError(e, msg)
            self.ProcessError(ErrorWrapper(Exception(msg)))
            return CMState.BuildFailure(self, Exception=e)

    def ProcessCancelAllPositionReq(self,wrapper):
        try:

            if self.PositionsSynchronization:
                raise Exception("The engine is in the synchronization process. Please try again later!")

            if self.ServiceFailure:
                return CMState.BuildFailure(self,Exception=self.FailureException)

            threading.Thread(target=self.ProcessCancelAllPositionReqThread, args=(wrapper,)).start()

            return CMState.BuildSuccess(self)

        except Exception as e:
            msg = "Critical Error sending new position to the exchange: {}!".format(str(e))
            self.ProcessCriticalError(e, msg)
            self.ProcessError(ErrorWrapper(Exception(msg)))
            return CMState.BuildFailure(self, Exception=e)

    def ProcessNewPositionReq(self,wrapper):

        try:

            if self.PositionsSynchronization:
                raise Exception("The engine is in the synchronization process. Please try again later!")

            if self.ServiceFailure:
                return CMState.BuildFailure(self,Exception=self.FailureException)

            threading.Thread(target=self.ProcessNewPositionReqThread, args=(wrapper,)).start()

            return CMState.BuildSuccess(self)

        except Exception as e:
            msg = "Critical Error sending new position to the exchange: {}!".format(str(e))
            self.ProcessCriticalError(e, msg)
            self.ProcessError(ErrorWrapper(Exception(msg)))
            return CMState.BuildFailure(self, Exception=e)

    def DeletePotentialPositions(self,newPosArr):
        try:
            self.RoutingLock.acquire(blocking=True)

            toDel = []
            for potPos in self.PotentialPositions.values():
                # we look for this position in the fulk positions
                newPotPos = next(iter(list(
                            filter(lambda x: PotentialPosition.GetPosId(x.GetField(PositionField.Symbol),
                                                                        x.GetField(PositionField.Side),
                                                                        int(x.GetField(PositionField.Qty))) == potPos.Id,
                                   newPosArr))),None)
                if newPotPos is None:
                    toDel.append(potPos)

            for potPos in toDel:
                self.DoLog("Deleting old Potential Position {} for PosId {}".format(potPos.Security.Symbol,potPos.Id),MessageType.INFO)
                del self.PotentialPositions[potPos.Id]

        except Exception as e:
            msg = "Error deleting old positions exchange: {}!".format(str(e))
            raise Exception(msg)
        finally:
            if self.RoutingLock.locked():
                self.RoutingLock.release()

    def ProcessNewPositionBulkReq(self, wrapper):
        try:

            if self.PositionsSynchronization:
                raise Exception("The engine is in the synchronization process. Please try again later!")

            if self.ServiceFailure:
                return CMState.BuildFailure(self, Exception=self.FailureException)

            fromDate = datetime.datetime.now() - datetime.timedelta(days=self.Configuration.PastDaysForTradingSignals)
            routedTradingSignals = self.RoutedTradingSignalManager.GetTradingSignals(fromDate)

            newPosArr = wrapper.GetField(PositionListField.Positions)

            self.DeletePotentialPositions(newPosArr)

            for newPosWrapper in newPosArr:
                threading.Thread(target=self.ProcessNewPositionReqThread, args=(newPosWrapper,routedTradingSignals,)).start()

            return CMState.BuildSuccess(self)

        except Exception as e:
            msg = "Critical Error sending bulk positions to the exchange: {}!".format(str(e))
            self.ProcessCriticalError(e, msg)
            self.ProcessError(ErrorWrapper(Exception(msg)))
            return CMState.BuildFailure(self, Exception=e)

    def ProcessPortfolioPositionsRequest(self,wrapper):
        
        if self.ServiceFailure:
            return CMState.BuildFailure(self,Exception=self.FailureException)

        threading.Thread(target=self.ProcessPortfolioPositionsRequestThread, args=(wrapper,)).start()

        return CMState.BuildSuccess(self)

    def RequestPositionList(self):
        time.sleep(int(self.Configuration.PauseBeforeExecutionInSeconds))
        self.DoLog("Requesting for open orders...", MessageType.INFO)
        wrapper = PositionListRequestWrapper()
        self.OrderRoutingModule.ProcessMessage(wrapper)

    #endregion

    #region Public Methods

    def ProcessMessage(self, wrapper):
        try:
            if wrapper.GetAction() == Actions.PORTFOLIO_POSITIONS_REQUEST:
                return self.ProcessPortfolioPositionsRequest(wrapper)
            elif wrapper.GetAction() == Actions.NEW_POSITION:
                return self.ProcessNewPositionReq(wrapper)
            elif wrapper.GetAction() == Actions.CANCEL_ALL_POSITIONS:
                return self.ProcessCancelAllPositionReq(wrapper)
            elif wrapper.GetAction() == Actions.CANCEL_POSITION:
                return self.ProcessCancePositionReq(wrapper)
            elif wrapper.GetAction() == Actions.NEW_POSITION_BULK:
                return self.ProcessNewPositionBulkReq(wrapper)
            else:
                raise Exception("DayTrader.ProcessMessage: Not prepared for routing message {}".format(wrapper.GetAction()))
        except Exception as e:
            self.DoLog("Critical error @DayTrader.ProcessMessage: " + str(e), MessageType.ERROR)
            return CMState.BuildFailure(self, Exception=e)

    def ProcessIncoming(self, wrapper):
        try:

            if wrapper.GetAction() == Actions.TRADING_SIGNAL:
                threading.Thread(target=self.ProcessTradingSignal, args=(wrapper,)).start()
                return CMState.BuildSuccess(self)
            elif wrapper.GetAction() == Actions.ERROR:
                threading.Thread(target=self.ProcessError, args=(wrapper,)).start()
            else:
                raise Exception("ProcessIncoming: Not prepared for routing message {}".format(wrapper.GetAction()))
        except Exception as e:
            self.DoLog("Critical error @DayTrader.ProcessIncoming: " + str(e), MessageType.ERROR)
            return CMState.BuildFailure(self, Exception=e)

    def ProcessOutgoing(self, wrapper):
        try:
            if wrapper.GetAction() == Actions.EXECUTION_REPORT:

                threading.Thread(target=self.ProcessExecutionReport, args=(wrapper,)).start()
                return CMState.BuildSuccess(self)
            elif wrapper.GetAction() == Actions.POSITION_LIST:
                threading.Thread(target=self.ProcessPositionList, args=(wrapper,)).start()
                return CMState.BuildSuccess(self)
            elif wrapper.GetAction() == Actions.ORDER_CANCEL_REJECT:
                threading.Thread(target=self.ProcessOrderCancelReject, args=(wrapper,)).start()
                return CMState.BuildSuccess(self)
            elif wrapper.GetAction() == Actions.ERROR:
                threading.Thread(target=self.ProcessError, args=(wrapper,)).start()
                return CMState.BuildSuccess(self)
            else:
                raise Exception("ProcessOutgoing: Not prepared for routing message {}".format(wrapper.GetAction()))
        except Exception as e:
            self.DoLog("Critical error @DayTrader.ProcessOutgoing: " + str(e), MessageType.ERROR)
            return CMState.BuildFailure(self, Exception=e)

    def Initialize(self, pInvokingModule, pConfigFile):
        self.ModuleConfigFile = pConfigFile
        self.InvokingModule = pInvokingModule
        self.DoLog("DayTrader  Initializing", MessageType.INFO)

        if self.LoadConfig():

            if self.Configuration.TestMode:
                self.PositionsSynchronization=False

            threading.Thread(target=self.TradesPersistanceThread, args=()).start()

            threading.Thread(target=self.PotentialPositionsPersistanceThread, args=()).start()

            self.LoadManagers()

            self.FileHandlerModule = self.InitializeModule(self.Configuration.FileHandlerModule,self.Configuration.FileHandlerConfigFile)

            self.MarketDataModule =  self.InitializeModule(self.Configuration.IncomingModule,self.Configuration.IncomingConfigFile)

            self.OrderRoutingModule = self.InitializeModule(self.Configuration.OutgoingModule,self.Configuration.OutgoingConfigFile)

            self.VendorModule = self.InitializeModule(self.Configuration.VendorModule,self.Configuration.VendorFile)

            time.sleep(self.Configuration.PauseBeforeExecutionInSeconds)

            self.LoadRoutedTradingSignals()

            threading.Thread(target=self.MarketSubscriptionsThread, args=()).start()

            self.DoLog("DayTrader Successfully initialized", MessageType.INFO)

            return CMState.BuildSuccess(self)

        else:
            msg = "Error initializing Day Trader"
            self.DoLog(msg, MessageType.ERROR)
            return CMState.BuildFailure(self,errorMsg=msg)

    #endregion