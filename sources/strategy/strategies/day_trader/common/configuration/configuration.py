import configparser

class Configuration:
    def __init__(self, configFile):
        config = configparser.ConfigParser()
        config.read(configFile)

        self.IncomingModule = config['DEFAULT']['INCOMING_MODULE']
        self.IncomingConfigFile = config['DEFAULT']['INCOMING_CONFIG_FILE']

        self.OutgoingModule = config['DEFAULT']['OUTGOING_MODULE']
        self.OutgoingConfigFile = config['DEFAULT']['OUTGOING_CONFIG_FILE']

        self.VendorModule = config['DEFAULT']['VENDOR_MODULE']
        self.VendorFile = config['DEFAULT']['VENDOR_FILE']

        self.Currency = config['DEFAULT']['CURRENCY']
        self.PauseBeforeExecutionInSeconds = int( config['DEFAULT']['PAUSE_BEFORE_EXECUTION_IN_SECONDS'])
        self.DefaultExchange= config['DEFAULT']['DEFAULT_EXCHANGE']
        self.MarketDataSubscriptionResetTime = config['DEFAULT']['MARKET_DATA_SUBSCRIPTION_RESET_TIME']
        self.DefaultAccount = config['DEFAULT']['DEFAULT_ACCOUNT']
        self.TestMode =config['DEFAULT']['TEST_MODE']=="True"
        self.PastDaysForTradingSignals = int(config['DEFAULT']['PAST_DAYS_FOR_TRADING_SIGNALS'])

        self.DBConectionString = config['DB']['CONNECTION_STRING']

        self.FileHandlerModule = config['DEFAULT']['FILE_HANDLER_MODULE']
        self.FileHandlerConfigFile = config['DEFAULT']['FILE_HANDLER_CONFIG_FILE']

        self.DBConnectionString =config['DB']['CONNECTION_STRING']