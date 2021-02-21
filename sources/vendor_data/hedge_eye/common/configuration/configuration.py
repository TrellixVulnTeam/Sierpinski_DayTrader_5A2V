import configparser

class Configuration:
    def __init__(self, configFile):
        config = configparser.ConfigParser()
        config.read(configFile)

        self.HedgeEyeURL = config['DEFAULT']['HEDGE_EYE_URL']
        self.ChromeDriverPath=config['DEFAULT']['CHROME_DRIVER_PATH']

        self.SleepBetweenBeeps = int( config['DEFAULT']['SLEEP_BTW_BEEPS'])
        self.SleepLengthSeconds = int( config['DEFAULT']['SLEEP_LENGTH_SECONDS'])
        self.SignalUpdFreqSeconds = int( config['DEFAULT']['SIGNAL_UPD_FREQ-SECONDS'])


