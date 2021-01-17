from sources.framework.common.wrappers.wrapper import Wrapper
from sources.framework.common.enums.Actions import *
from sources.framework.common.enums.fields.position_list_field import *

class NewPositionBulkRequestWrapper(Wrapper):
    def __init__(self, pPositionWrapperArr):
        self.PositionWrapperArr = pPositionWrapperArr

    def GetAction(self):
        """ See Wrapper class.

        Returns:
            Return an Action object.
        """
        return Actions.NEW_POSITION_BULK

    def GetField(self, field):
        """ See Wrapper class.

        Args:
            field ():

        Returns:
            Return an specific position field.
        """
        if field is None:
            return None

        if field == PositionListField.Positions:
            return self.PositionWrapperArr
        else:
            return None

