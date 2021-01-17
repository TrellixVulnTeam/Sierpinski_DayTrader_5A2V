from sources.strategy.strategies.day_trader.business_entities.model_parameter import *

_KEY_CHAR="$$"

class ModelParametersHandler:
    def __init__(self,pModelParameters):

        self.ModelParametersDict ={}
        for modelParam in pModelParameters:
            if modelParam.Symbol is not None:
                self.ModelParametersDict[modelParam.Symbol+_KEY_CHAR+modelParam.Key]=modelParam
            else:
                self.ModelParametersDict[modelParam.Key] = modelParam


    #region Static Attributes

    @staticmethod
    def BACKWARD_DAYS_SUMMARIES_IN_MEMORY():
        return "BACKWARD_DAYS_SUMMARIES_IN_MEMORY"

    @staticmethod
    def BAR_FREQUENCY():
        return "BAR_FREQUENCY"

    @staticmethod
    def PROCESS_EXTERNAL_TRADING():
        return "PROCESS_EXTERNAL_TRADING"
    #endregion

    #region Public Methods

    def GetAll(self,  symbol):

        modelParamArr=[]

        for key in self.ModelParametersDict:
            if symbol is None:
                if not _KEY_CHAR in key:
                    modelParamArr.append(self.ModelParametersDict[key])
            else:
                if key.startswith(symbol):
                    modelParamArr.append(self.ModelParametersDict[key])

        return modelParamArr



    def Get(self, key, symbol=None):

        finalKey=key
        if symbol is not None:
            finalKey=symbol+_KEY_CHAR+key

        if finalKey in self.ModelParametersDict:
            return self.ModelParametersDict[finalKey]
        elif key in self.ModelParametersDict:
            return self.ModelParametersDict[key]
        else:
            raise Exception("Critical error! Could not find model parameter {} {} in memory"
                            .format(key," for symbol {} ".format(symbol) if symbol is not None else ""))

    def GetLight(self, key,symbol):
        finalKey = key
        if symbol is not None:
            finalKey = symbol + _KEY_CHAR + key

        if finalKey in self.ModelParametersDict:
            return self.ModelParametersDict[finalKey]
        else:
            return None

    def Set(self, key, symbol,modelParam):
        if(symbol is not None and symbol!="*"):
            self.ModelParametersDict[symbol + _KEY_CHAR +key] = modelParam
        else:
            self.ModelParametersDict[key] = modelParam

    #endregion