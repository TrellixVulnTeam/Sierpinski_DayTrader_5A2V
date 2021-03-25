import threading
from datetime import date

from selenium.webdriver.common.by import By

from sources.framework.util.singleton.common.util.singleton import *
from sources.framework.common.abstract.base_communication_module import BaseCommunicationModule
from sources.framework.common.interfaces.icommunication_module import ICommunicationModule
from sources.order_routers.bloomberg.common.wrappers.historical_prices_wrapper import *
from sources.framework.common.wrappers.market_data_wrapper import *
from sources.vendor_data.hedge_eye.common.configuration.configuration import *
from sources.vendor_data.hedge_eye.common.dto.trading_signal_dto import *
from sources.vendor_data.hedge_eye.common.wrappers.trading_signal_wrapper import *
from sources.vendor_data.hedge_eye.data_access_layer.two_captcha_manager import *
from sources.framework.common.dto.cm_state import *
from selenium import webdriver
import time
import winsound

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

_BUY_SIGNAL_PREFIX="BUY SIGNAL"
_SELL_SIGNAL_PREFIX="SELL SIGNAL"


class SignalTracker( BaseCommunicationModule, ICommunicationModule):

    # region Constructors

    def __init__(self):
        # region Attributes
        self.Name = "Hedge Eye Signal Tracker"
        self.Configuration=None
        self.TwoCaptchaManager = None
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

    def GetCaptchaToken(self):

        while True:

            requestId = None

            try:
                requestId=self.TwoCaptchaManager.GetCapthaRequestId()
            except Exception as e:
                self.DoLog("Could not recover 2Captcha Request Id:{}".format(str(e)),MessageType.ERROR)

            i=1
            token=None
            found=False
            while True:
                # now we have to wait for the captcha to be solved
                time.sleep(1)
                try:
                    token=self.TwoCaptchaManager.GetHCaptchaToken(requestId)
                    found=True
                    return token
                except Exception as e:
                    self.DoLog("Could not recover the captcha token in the attempt #{}:{}".format(i,str(e)),MessageType.ERROR)
                finally:
                    i+=1
                    if(i>10 and not found):
                        self.DoLog("More than 10 unsuccessful attempts. Restarting Login process.",MessageType.ERROR)
                        break

    def DoLoadToken(self,driver,cntrl,token):
        driver.execute_script(
            'var element=document.getElementsByName("'+cntrl+'")[0]; element.style.display="";')
        driver.execute_script('document.getElementsByName("'+cntrl+'")[0].innerHTML = "'+token+'" ')

    def DoLogin(self,driver):
        token = self.GetCaptchaToken()
        driver.get(self.Configuration.LoginURL)

        self.DoLoadToken(driver, "g-recaptcha-response", token)
        self.DoLoadToken(driver, "h-captcha-response", token)

        xpaths = {'email': "//input[@name='user[email]']", 'pw': "//input[@name='user[password]']"}
        driver.find_element_by_xpath(xpaths['email']).send_keys(self.Configuration.HedgeEyeLogin)
        driver.find_element_by_xpath(xpaths['pw']).send_keys(self.Configuration.HedgeEyePwd)
        touch_button = driver.find_element_by_xpath("//input[@name='commit']")
        touch_button.click()

    def TrackForSignals(self):

        signalsFound=[]
        articles=[]
        self.DoLog("Starting Trading Signal Scrapping".format(datetime.datetime.now()), MessageType.INFO)
        self.DoLog("Opening Chrome window".format(datetime.datetime.now()), MessageType.INFO)
        driver = webdriver.Chrome(executable_path=self.Configuration.ChromeDriverPath)
        signalsURL = self.Configuration.HedgeEyeURL

        self.DoLogin(driver)

        while   True:

            try:

                driver.get(signalsURL)
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
                    date = datetime.datetime.strptime(dateStr[i].text, self.Configuration.DateTimeFormat)

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

            self.TwoCaptchaManager=TwoCaptchaManager(self.Configuration.LoginURL,
                                                     self.Configuration.CaptchaSvcURL,
                                                     self.Configuration.TwoCaptchaCustomerKey,
                                                     self.Configuration.SiteKey)

            threading.Thread(target=self.TrackForSignals, args=()).start()
            self.DoLog("SignalTracker Successfully initialized", MessageType.INFO)

            return CMState.BuildSuccess(self)
        else:
            msg = "Error initializing SignalTracker"
            self.DoLog(msg, MessageType.ERROR)
            return CMState.BuildFailure(self,errorMsg=msg)


    #endregion