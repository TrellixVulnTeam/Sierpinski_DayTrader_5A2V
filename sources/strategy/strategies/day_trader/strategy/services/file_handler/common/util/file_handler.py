from sources.strategy.strategies.day_trader.strategy.services.file_handler.common.util.input_file_converter import *
from sources.strategy.strategies.day_trader.strategy.services.file_handler.common.util.output_file_converter import *
from sources.framework.common.logger.message_type import *
import shutil
import os
import threading
import csv
import traceback

class FileHandler:

    def __init__(self):
        pass

    @staticmethod
    def MoveFile( input, output):
        """ Move csv file, from input to output.

        Args:
            input (String): Current csv file path.
            output (String): Destination csv file path.

        """
        shutil.move(input, output)


    @staticmethod
    def FetchInputFile(logger, configuration):

        while True:

            for r, d, f in os.walk(configuration.InputPath):
                for file in f:
                    if '.csv' in file:

                        try:
                            logger.DoLog("Found CSV file {}. Extracting positions to route".format(file), MessageType.INFO)
                            posToRouteArr = InputFileConverter.ExtractNewPositions(logger,configuration.InputPath+file,configuration.Mode)

                            FileHandler.MoveFile(configuration.InputPath + file,configuration.ProcessedPath + file)
                            logger.DoLog("File Handler Module : Moving file {} to {}".format(configuration.InputPath  + file, configuration.ProcessedPath  + file),MessageType.INFO)

                            threading.Thread(target=logger.OnPositionsToProcess, args=(posToRouteArr,)).start()
                        except Exception as e:
                            traceback.print_exc()
                            logger.DoLog("Critical error fetching for input files @FileHandlerModule.FetchInputFileThread: " + str(e), MessageType.ERROR)
                            FileHandler.MoveFile(configuration.InputPath + file, configuration.ProcessedPath.FailedPath + file)

            time.sleep(3)

