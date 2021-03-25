import configparser

class Configuration:
    def __init__(self, configFile):
        config = configparser.ConfigParser()
        config.read(configFile)

        self.HedgeEyeURL = config['DEFAULT']['HEDGE_EYE_URL']
        self.ChromeDriverPath=config['DEFAULT']['CHROME_DRIVER_PATH']
        self.DateTimeFormat = config['DEFAULT']['DATETIME_FORMAT']

        self.SleepBetweenBeeps = int( config['DEFAULT']['SLEEP_BTW_BEEPS'])
        self.SleepLengthSeconds = int( config['DEFAULT']['SLEEP_LENGTH_SECONDS'])
        self.SignalUpdFreqSeconds = int( config['DEFAULT']['SIGNAL_UPD_FREQ-SECONDS'])

        self.LoginURL = config['DEFAULT']['LOGIN_URL']
        self.CaptchaSvcURL = config['DEFAULT']['CAPTCHA_SVC_URL']
        self.SiteKey = config['DEFAULT']['SITE_KEY']
        self.TwoCaptchaCustomerKey = config['DEFAULT']['2CAPTCHA_CUSTOMER_KEY']

        self.HedgeEyeLogin = config['DEFAULT']['HEDGE_EYE_LOGIN']
        self.HedgeEyePwd = config['DEFAULT']['HEDGE_EYE_PWD']

        #2CAPTCHA_CUSTOMER_KEY



