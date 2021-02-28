import threading
from datetime import date

from sources.framework.util.singleton.common.util.singleton import *
from sources.framework.common.abstract.base_communication_module import BaseCommunicationModule
from sources.framework.common.interfaces.icommunication_module import ICommunicationModule
from sources.order_routers.bloomberg.common.wrappers.historical_prices_wrapper import *
from sources.framework.common.wrappers.market_data_wrapper import *
from sources.vendor_data.hedge_eye.common.configuration.configuration import *
from sources.vendor_data.hedge_eye.common.dto.trading_signal_dto import *
from sources.vendor_data.hedge_eye.common.wrappers.trading_signal_wrapper import *
from sources.framework.common.dto.cm_state import *
from selenium import webdriver
import time
import winsound

_BUY_SIGNAL_PREFIX="BUY SIGNAL"
_SELL_SIGNAL_PREFIX="SELL SIGNAL"
_DATETIME_FORMAT="%m/%d/%y %H:%M %p EST"

class SignalTracker( BaseCommunicationModule, ICommunicationModule):

    # region Constructors

    def __init__(self):
        # region Attributes
        self.Name = "Hedge Eye Signal Tracker"
        self.Configuration=None
        # endregion

    # endregion

    #region Private Methods

    def CreateTradingSignal(self,date,side,signal):
        try:
            flds=signal.split(" ")

            symbol = flds[2]
            price = float(flds[3].replace("$",""))

            tradingSignal = TradingSignalDto(symbol,date,side,price)

            wrapper = TradingSignalWrapper(tradingSignal)

            self.InvokingModule.ProcessIncoming(wrapper)

        except Exception as e:
            self.DoLog("Critical error Parsing Signal {}: {}".format(signal,str(e)), MessageType.ERROR)
            #winsound.Beep(1000, self.Configuration.SleepLengthSeconds * 1000)


    def LoadConfig(self):
        self.Configuration = Configuration(self.ModuleConfigFile)
        return True

    def FindLoginError(self,driver):

        errors = driver.find_elements_by_xpath("//span[contains(@class,'error')]")

        foundLoginError = False
        for error in errors:
            if error.text.startswith("You need to sign in"):
                foundLoginError = True

        return foundLoginError

    def TrackForSignals(self):

        signalsFound=[]
        articles=[]
        self.DoLog("Starting Trading Signal Scrapping".format(datetime.datetime.now()), MessageType.INFO)
        self.DoLog("Opening Chrome window".format(datetime.datetime.now()), MessageType.INFO)
        driver = webdriver.Chrome(executable_path=self.Configuration.ChromeDriverPath)
        url = self.Configuration.HedgeEyeURL

        while   True:

            try:
                driver.get(url)
                while True:
                    foundLoginError = self.FindLoginError(driver)
                    if foundLoginError:
                        winsound.Beep(2500,self.Configuration.SleepLengthSeconds*1000)
                        time.sleep(self.Configuration.SleepBetweenBeeps)
                    else:
                        break
                self.DoLog("Searching for trading signals".format(datetime.datetime.now()), MessageType.INFO)
                rows = driver.find_elements_by_xpath("//div[contains(@class,'col-sm-12 ext-list-article')]")

                dateStr = driver.find_elements_by_xpath("//p[contains(@class,'article__meta__date')]")
                titleStr = driver.find_elements_by_xpath("//h2[contains(@class,'article__title')]")

                for i,title in enumerate(titleStr):

                    title=str(titleStr[i].text)
                    date = datetime.datetime.strptime(dateStr[i].text, _DATETIME_FORMAT)

                    if title in signalsFound:
                        break
                    elif title.startswith(_BUY_SIGNAL_PREFIX):
                        self.DoLog("Creating Buy Signal: {} at {}".format(title,date),MessageType.INFO)
                        signalsFound.append(title)
                        threading.Thread(target=self.CreateTradingSignal, args=(date,Side.Buy,title)).start()

                    elif title.startswith(_SELL_SIGNAL_PREFIX):
                        self.DoLog("Creating Sell Signal: {} at {}".format(title,date),MessageType.INFO)
                        signalsFound.append(title)
                        threading.Thread(target=self.CreateTradingSignal, args=(date,Side.Sell,title)).start()
                    elif title not in articles:
                        self.DoLog("Discarding regular article: {}".format(title.encode("utf-8")),MessageType.INFO)
                        articles.append(title.encode("utf-8"))

                self.DoLog("All signals processed".format(datetime.datetime.now()),MessageType.INFO)
            except Exception as e:
                self.DoLog("Critical error Downloading Signals: {}".format(str(e)), MessageType.ERROR)
                #TODO: Publish Error
                winsound.Beep(1000,self.Configuration.SleepLengthSeconds*1000)

            time.sleep(self.Configuration.SignalUpdFreqSeconds)

    #endregion

    #region Public Methods


    def ProcessMessage(self, wrapper):
        try:
            if wrapper.GetAction() == Actions.START_SIGNAL_TRACKING:
                return self.ProcessStartSignalTracking(wrapper)

            else:
                raise Exception("SignalTracker.ProcessMessage: Not prepared for routing message {}".format(wrapper.GetAction()))
        except Exception as e:
            self.DoLog("Critical error @SignalTracker.ProcessMessage: " + str(e), MessageType.ERROR)
            return CMState.BuildFailure(self, Exception=e)

    def ProcessIncoming(self, wrapper):
        try:
            raise Exception("ProcessIncoming: Not prepared for routing message {}".format(wrapper.GetAction()))
        except Exception as e:
            self.DoLog("Critical error @SignalTracker.ProcessIncoming: " + str(e), MessageType.ERROR)
            return CMState.BuildFailure(self, Exception=e)

    def ProcessOutgoing(self, wrapper):
        try:
            raise Exception("ProcessOutgoing: Not prepared for routing message {}".format(wrapper.GetAction()))
        except Exception as e:
            self.DoLog("Critical error @SignalTracker.ProcessOutgoing: " + str(e), MessageType.ERROR)
            return CMState.BuildFailure(self, Exception=e)

    def Initialize(self, pInvokingModule, pConfigFile):
        self.ModuleConfigFile = pConfigFile
        self.InvokingModule = pInvokingModule
        self.DoLog("SignalTracker  Initializing", MessageType.INFO)

        if self.LoadConfig():

            threading.Thread(target=self.TrackForSignals, args=()).start()
            self.DoLog("SignalTracker Successfully initialized", MessageType.INFO)

            return CMState.BuildSuccess(self)
        else:
            msg = "Error initializing SignalTracker"
            self.DoLog(msg, MessageType.ERROR)
            return CMState.BuildFailure(self,errorMsg=msg)


    #endregion