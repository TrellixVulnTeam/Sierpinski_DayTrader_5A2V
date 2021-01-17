from sources.framework.common.interfaces.icommunication_module import ICommunicationModule
from sources.framework.common.abstract.base_communication_module import *
from sources.strategy.strategies.day_trader.strategy.services.file_handler.common.configuration.configuration import *
from sources.strategy.strategies.day_trader.strategy.services.file_handler.common.util.file_handler import *
from sources.strategy.strategies.day_trader.strategy.services.file_handler.common.wrapper.new_position_bulk_request_wrapper import *
from sources.framework.common.enums.Actions import *
from sources.framework.common.logger.message_type import *
from sources.framework.common.dto.cm_state import *
from sources.framework.common.enums.fields.strategy_backtest_result_field import *
import threading
import os
import time
import csv
import shutil

class FileHandlerModule(BaseCommunicationModule, ICommunicationModule):

    def __init__(self):
        self.Configuration = None
        self.ModuleConfigFile = None
        self.InvokingModule = None


    #region Private Methods

    def DoLog(self, msg, type):
        self.InvokingModule.DoLog(msg, type)


    def LoadConfig(self):
        self.Configuration = Configuration(self.ModuleConfigFile)
        return True

    def OnPositionsToProcess(self,posWrapperArr):

        try:
            newPosBulkWrapper = NewPositionBulkRequestWrapper(posWrapperArr)
            self.InvokingModule.ProcessMessage(newPosBulkWrapper)

        except Exception as e:
            self.DoLog("Critical error @FileHandlerModule.OnPositionsToProcess: " + str(e), MessageType.ERROR)

    def FetchInputFileThread(self):

        try:
            FileHandler.FetchInputFile(self,self.Configuration)

        except Exception as e:
            self.DoLog("Critical error @FileHandlerModule.FetchInputFileThread: " + str(e), MessageType.ERROR)


    #endregion

    # region ICommunicationModule methods

    def ProcessMessage(self, wrapper):
        try:
            raise Exception("ProcessMessage: Not prepared to process message {}".format(wrapper.GetAction()))
        except Exception as e:
            self.DoLog("Critical error @FileHandlerModule.ProcessMessage: " + str(e), MessageType.ERROR)
            return CMState.BuildFailure(self, Exception=e)

    def ProcessOutgoing(self, wrapper):
        pass

    def ProcessIncoming(self, wrapper):
        try:
            if wrapper.GetAction() == Actions.SIMULATE_TRADES:
                return self.InvokingModule.ProcessMessage(wrapper)
            else:
                raise Exception("FileHandlerModule.ProcessIncoming: Not prepared to process message {}".format(wrapper.GetAction()))
        except Exception as e:
            self.DoLog("Critical error @FileHandlerModule.ProcessIncoming: " + str(e), MessageType.ERROR)
            return CMState.BuildFailure(self, Exception=e)


    def Initialize(self, pInvokingModule, pConfigFile):
        self.ModuleConfigFile = pConfigFile
        self.InvokingModule = pInvokingModule
        self.DoLog("FileHandlerModule  Initializing", MessageType.INFO)

        if self.LoadConfig():

            threading.Thread(target=self.FetchInputFileThread, args=()).start()

            self.DoLog("FileHandlerModule Successfully initialized", MessageType.INFO)
            return CMState.BuildSuccess(self)

        else:
            msg = "Error initializing config file for FileHandlerModule"
            self.DoLog(msg, MessageType.ERROR)
            return CMState.BuildFailure(self,errorMsg=msg)


    #endregion
