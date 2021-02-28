from sources.framework.common.logger.message_type import *
from sources.framework.business_entities.securities.security import *
from sources.strategy.strategies.day_trader.strategy.services.file_handler.common.util.csv_constants import *
from sources.strategy.strategies.day_trader.strategy.services.file_handler.common.dto.position_dto import *
from sources.strategy.strategies.day_trader.strategy.services.file_handler.common.wrapper.position_wrapper import *

import csv
import time
import datetime
import uuid

class InputFileConverter:

    def __init__(self):
        pass

    #region Static Consts

    @staticmethod
    def DATE_FIELD():
        return "Date"

    @staticmethod
    def SYMBOL_FIELD():
        return "Symbol"

    @staticmethod
    def TIME_FORMAT():
        return "%H:%M:%S"

    @staticmethod
    def DATE_FORMAT():
        return "%m/%d/%y"

    @staticmethod
    def LONG_DATE_FORMAT():
        return "%m/%d/%Y"

    @staticmethod
    def DAILY_BIAS_FIELD():
        return "DAILY_BIAS"

    #endregion

    @staticmethod
    # we only have symbol and qty
    def LaunchPositionInSimpleCsv(logger, reader):
        for row in reader:
            if len(row) == 2:
                logger.DoLog("Processing CSV position for symbol {} -> qty ={}".format(row[0], row[1]), MessageType.INFO)

                raise Exception("Simple CSV not implemented")
            else:
                logger.DoLog("Row {} not properly formatted!!!. Mode:{}".format(row, self.Configuration.Mode),
                           MessageType.WARNING)

    @staticmethod
    # we have ticker, side, quantity, account, order type, limit, broker, strategy
    def LaunchPositionInExtendedCsv( logger, reader):

        i = 0
        posWrapperArr = []
        for row in reader:

            # we ignore first row
            if i == 0:
                i += 1
                continue

            try:
                if row[0] == "CANCEL_ALL":
                    #TODO dev Cancel All Wrapper
                    break
                elif len(row) >= 8:
                    logger.DoLog(
                        "Creating potential position for symbol {} qty ={} side={} order type={} limit={} broker={} "
                        "strategy={} "
                            .format(row[CSVConstants._EXTENDED_SYMBOL()],
                                    row[CSVConstants._EXTENDED_QTY()],
                                    row[CSVConstants._EXTENDED_SIDE()],
                                    row[CSVConstants._EXTENDED_ORDER_TYPE()],
                                    row[CSVConstants._EXTENDED_LIMIT_PRICE()],
                                    row[CSVConstants._EXTENDED_BROKER()],
                                    row[CSVConstants._EXTENDED_STRATEGY()]), MessageType.INFO)

                    pos = PositionDto(pSymbol=row[CSVConstants._EXTENDED_SYMBOL()],
                                      pExchange=row[CSVConstants._EXTENDED_QTY()],
                                      pSide=row[CSVConstants._EXTENDED_SIDE()],
                                      pQty=float(row[CSVConstants._EXTENDED_QTY()]),
                                      pOrderType=row[CSVConstants._EXTENDED_ORDER_TYPE()],
                                      pLimitPrice=float(row[CSVConstants._EXTENDED_LIMIT_PRICE()]) if row[CSVConstants._EXTENDED_LIMIT_PRICE()]!="" else None,
                                      pBroker=row[CSVConstants._EXTENDED_BROKER()],
                                      pStrategy=row[CSVConstants._EXTENDED_STRATEGY()])

                    posWrapper = PositionWrapper(pos)
                    posWrapperArr.append(posWrapper)
                else:
                    logger.DoLog("Row {} not properly formatted!!!. Mode:{}".format(row, "Extended"),
                               MessageType.WARNING)

            except Exception as e:
                logger.DoLog("An error occurred while processing CSV row: {} ".format(str(e)), MessageType.ERROR)

        return posWrapperArr

    @staticmethod
    def ExtractNewPositions(logger,file,mode):

        try:
            with open(file, newline='') as f:
                reader = csv.reader(f)

                if mode == "SIMPLE":
                    return InputFileConverter.LaunchPositionInSimpleCsv(logger,reader)
                elif mode == "EXTENDED":
                    return InputFileConverter.LaunchPositionInExtendedCsv(logger,reader)
                else:
                    raise Exception("Unknown format for CSV file: {}".format(mode))

        except Exception as e:
            logger.DoLog("An error occurred while reading the file {}:{} ".format(file, str(e)) , MessageType.ERROR)
            raise e