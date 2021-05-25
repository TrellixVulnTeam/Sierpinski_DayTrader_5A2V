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
from sources.vendor_data.hedge_eye.common.dto.trading_tag_dto import TradingTagDto
from sources.vendor_data.hedge_eye.common.wrappers.trading_signal_wrapper import *
from sources.vendor_data.hedge_eye.data_access_layer.two_captcha_manager import *
from sources.vendor_data.hedge_eye.data_access_layer.hedge_eye_user_manager import *
from sources.framework.common.dto.cm_state import *
from selenium import webdriver
import time
import winsound
import threading

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

_BUY_SIGNAL_PREFIX="BUY SIGNAL"
_BUY_SIGNAL_COVERING_PREFIX="BUY SIGNAL - COVERING SHORT"
_SELL_SIGNAL_PREFIX="SELL SIGNAL"
_SELL_SIGNAL_SHORTING_PREFIX="SELL SIGNAL - SHORTING"


class SignalTracker( BaseCommunicationModule, ICommunicationModule):

    # region Constructors

    def __init__(self):
        # region Attributes
        self.Name = "Hedge Eye Signal Tracker"
        self.Configuration=None
        self.TwoCaptchaManager = None
        self.HedgeEyeUserManager = None
        self.PublishLock = threading.Lock()
        self.TransmittedSignals = {}
        # endregion

    # endregion

    #region Private Methods

    def ReTransissionSignalThread(self):

        while True:
            try:
                self.DoLog("Re transmitting previously sent trading signals",MessageType.INFO)

                self.PublishLock.acquire(blocking=True)

                for tradingSignal in self.TransmittedSignals.values():

                    #we only retransmit Today's trading signals
                    if tradingSignal.Date.date()==datetime.datetime.now().date():
                        wrapper = TradingSignalWrapper(tradingSignal)
                        self.DoLog("Re transmitting trading signal for symbol {} (id={})".
                                   format(tradingSignal.Symbol,tradingSignal.GetSignalId()), MessageType.INFO)
                        self.InvokingModule.ProcessIncoming(wrapper)

            except Exception as e:
                self.DoLog("Critical error Re Transmitting Signals: {}".format(str(e)), MessageType.ERROR)
                winsound.Beep(1000, self.Configuration.SleepLengthSeconds * 1000)

            finally:
                if self.PublishLock.locked():
                    self.PublishLock.release()
                time.sleep(self.Configuration.SignalRetransmissionFreq)


    def CreateTradingSignal(self,date,side,signal):
        try:
            symbol=None
            price=None
            flds = signal.split(" ")

            if  signal.startswith(_SELL_SIGNAL_SHORTING_PREFIX):
                symbol = flds[4]
                price = float(flds[5].replace("$", ""))
            elif signal.startswith(_BUY_SIGNAL_COVERING_PREFIX) :
                symbol = flds[5]
                price = float(flds[6].replace("$", ""))
            else:
                symbol = flds[2]
                price = float(flds[3].replace("$",""))

            tradingSignal = TradingSignalDto(symbol,date,side,price)

            wrapper = TradingSignalWrapper(tradingSignal)

            self.InvokingModule.ProcessIncoming(wrapper)

            signal_id=tradingSignal.GetSignalId()

            self.TransmittedSignals[signal_id]=tradingSignal

        except Exception as e:
            self.DoLog("Critical error Parsing Signal {}: {}".format(signal,str(e)), MessageType.ERROR)
            #winsound.Beep(1000, self.Configuration.SleepLengthSeconds * 1000)

    def LoadManagers(self):

        self.HedgeEyeUserManager = HedgeEyeUserManager(self.Configuration.DBConnectionString)

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
                    elif not found:
                        time.sleep(self.Configuration.SleepBetweenLoginAttempts)

    def DoLoadToken(self,driver,cntrl,token):
        driver.execute_script(
            'var element=document.getElementsByName("'+cntrl+'")[0]; element.style.display="";')
        driver.execute_script('document.getElementsByName("'+cntrl+'")[0].innerHTML = "'+token+'" ')

    def GetNextUserToUse(self):
        users=self.HedgeEyeUserManager.GetHedgeEyeUsers()

        notUsedUser =next(iter(list(filter(lambda x: x.LastLoginTime is None, users))), None)


        if notUsedUser is None:

            usedArr = sorted(list(filter(lambda x: x.LastLoginTime is not None, users)), key=lambda x: x.LastLoginTime,
                             reverse=False)

            oldestUsedUser = usedArr[0] if len(usedArr)>0 else None

            if oldestUsedUser is None:
                raise Exception("Could not find user to login to Hedge Eye")

            return oldestUsedUser
        else:
            return notUsedUser

    def ValidateLoggedIn(self,driver,current_url):
        try:
            WebDriverWait(driver, 4).until(EC.url_changes(current_url))#4 seconds timeout
        except Exception as e:
            #First we look for error messages
            error_span = driver.find_element_by_xpath("//span[@class='error']")

            if error_span is not None:
                raise  Exception(error_span.text)
            else:
                raise Exception("Failed to log in")

        # We try to go to the signals URL
        current_url = driver.current_url
        driver.get(self.Configuration.HedgeEyeURL)
        WebDriverWait(driver, 4).until(EC.url_changes(current_url))#4 seconds timeout

        welcome_control = driver.find_element_by_xpath("//a[@id='se-inner-nav-open-signals']")

        if (welcome_control is not None and welcome_control.text == "OPEN SIGNALS"):
            return True
        else:
            raise Exception("No 'OPEN SIGNALS' link found after logging in")

    def DoLogin(self,driver):

        success= False

        while not success:

            user = self.GetNextUserToUse()

            try:

                token = self.GetCaptchaToken()
                driver.get(self.Configuration.LoginURL)

                self.DoLoadToken(driver, "g-recaptcha-response", token)
                #self.DoLoadToken(driver, "h-captcha-response", token)

                xpaths = {'email': "//input[@name='user[email]']", 'pw': "//input[@name='user[password]']"}
                current_url = driver.current_url

                driver.find_element_by_xpath(xpaths['email']).send_keys(user.Login)
                driver.find_element_by_xpath(xpaths['pw']).send_keys(user.Pwd)
                touch_button = driver.find_element_by_xpath("//input[@name='commit']")
                touch_button.click()

                success=self.ValidateLoggedIn(driver, current_url)

            except Exception as e:
                self.DoLog("Failed to log in for user {}:{} ".format(user.Login,str(e)),MessageType.ERROR)
            finally:
                user.LastLoginTime=datetime.datetime.now()
                self.HedgeEyeUserManager.PersistHedgeEyeUser(user)

    def GetTradingSignals(self,driver):
        #rows = driver.find_elements_by_xpath("//div[contains(@class,'col-sm-12 ext-list-article')]")

        #H2 Trading signals
        dateStrH2 = driver.find_elements_by_xpath("//p[contains(@class,'article__meta__date')]")
        titleStrH2 = driver.find_elements_by_xpath("//h2[contains(@class,'article__title')]")

        #H1 trading signals --> header!
        dateStrH1 = driver.find_elements_by_xpath("//time[contains(@class,'article__time')]//span[2]")
        titleStrH1 = driver.find_elements_by_xpath("//h1[contains(@class,'article__header')]")


        tradingTagDTOs=[]

        for i, title in enumerate(titleStrH2):
            title = str(titleStrH2[i].text)
            date = datetime.datetime.strptime(dateStrH2[i].text, self.Configuration.DateTimeFormat)

            dto=TradingTagDto(title,date)
            tradingTagDTOs.append(dto)

        for i, title in enumerate(titleStrH1):
            title = str(titleStrH1[i].text)
            date = datetime.datetime.strptime(dateStrH1[i].text, self.Configuration.DateTimeFormat)

            dto = TradingTagDto(title, date)
            tradingTagDTOs.append(dto)

        return tradingTagDTOs

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

                signalTags= self.GetTradingSignals(driver)

                #rows = driver.find_elements_by_xpath("//div[contains(@class,'col-sm-12 ext-list-article')]")
                #dateStr = driver.find_elements_by_xpath("//p[contains(@class,'article__meta__date')]")
                #titleStr = driver.find_elements_by_xpath("//h2[contains(@class,'article__title')]")

                self.PublishLock.acquire(blocking=True)

                for signalTag in signalTags:
                #for i,title in enumerate(titleStr):

                    #title=str(titleStr[i].text)
                    #date = datetime.datetime.strptime(dateStr[i].text, self.Configuration.DateTimeFormat)

                    if signalTag.title in signalsFound:
                        break
                    elif signalTag.title.startswith(_BUY_SIGNAL_PREFIX) or signalTag.title.startswith(_BUY_SIGNAL_COVERING_PREFIX):
                        self.DoLog("Creating Buy Signal: {} at {}".format(signalTag.title,date),MessageType.INFO)
                        signalsFound.append(signalTag.title)
                        threading.Thread(target=self.CreateTradingSignal, args=(signalTag.date,Side.Buy,signalTag.title)).start()

                    elif signalTag.title.startswith(_SELL_SIGNAL_PREFIX) or signalTag.title.startswith(_SELL_SIGNAL_SHORTING_PREFIX):
                        self.DoLog("Creating Sell Signal: {} at {}".format(signalTag.title,signalTag.date),MessageType.INFO)
                        signalsFound.append(signalTag.title)
                        threading.Thread(target=self.CreateTradingSignal, args=(signalTag.date,Side.Sell,signalTag.title)).start()
                    elif signalTag.title not in articles:
                        self.DoLog("Discarding regular article: {}".format(signalTag.title.encode("utf-8")),MessageType.INFO)
                        articles.append(signalTag.title.encode("utf-8"))

                self.DoLog("All signals processed".format(datetime.datetime.now()),MessageType.INFO)
            except Exception as e:
                self.DoLog("Critical error Downloading Signals: {}".format(str(e)), MessageType.ERROR)
                #TODO: Publish Error
                winsound.Beep(1000,self.Configuration.SleepLengthSeconds*1000)
            finally:
                if self.PublishLock.locked():
                    self.PublishLock.release()

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

            self.LoadManagers()

            self.TwoCaptchaManager=TwoCaptchaManager(self.Configuration.LoginURL,
                                                     self.Configuration.CaptchaSvcURL,
                                                     self.Configuration.TwoCaptchaCustomerKey,
                                                     self.Configuration.SiteKey)

            threading.Thread(target=self.TrackForSignals, args=()).start()
            threading.Thread(target=self.ReTransissionSignalThread, args=()).start()
            self.DoLog("SignalTracker Successfully initialized", MessageType.INFO)

            return CMState.BuildSuccess(self)
        else:
            msg = "Error initializing SignalTracker"
            self.DoLog(msg, MessageType.ERROR)
            return CMState.BuildFailure(self,errorMsg=msg)


    #endregion