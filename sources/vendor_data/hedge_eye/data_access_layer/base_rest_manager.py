class BaseRESTManager:

    def __init__(self):
        pass


    #region Private Methods

    def GetHeaders(self):

        return {
            "Content-Type": "application/x-www-form-urlencoded"
        }

    #endregion