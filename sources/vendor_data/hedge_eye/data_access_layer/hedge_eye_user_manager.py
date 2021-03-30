import pyodbc
from sources.vendor_data.hedge_eye.business_entities.hedge_eye_user import *

_login=0
_pwd=1
_last_login_time=2

class HedgeEyeUserManager():

    # region Constructors
    def __init__(self, connString):
        self.ConnParams = {}
        self.i = 0
        self.connection = pyodbc.connect(connString, autocommit=False)

    #endregion

    #region Private Methods

    def BuildHedgeEyeUser(self, row):
        user = HedgeEyeUser(pLogin= row[_login],pPwd=row[_pwd],pLastLoginTime=row[_last_login_time])
        return user

    #endregion

    # region Public Methods

    def GetHedgeEyeUsers(self):
        users=[]
        with self.connection.cursor() as cursor:
            params = ()
            cursor.execute("{CALL GetHedgeEyeUsers ()}", params)

            for row in cursor:
                users.append( self.BuildHedgeEyeUser(row))

        return users

    def PersistHedgeEyeUser(self,user):
        with self.connection.cursor() as cursor:
            params = (user.Login,user.LastLoginTime)
            cursor.execute("{CALL PersistHedgeEyeUser (?,?)}", params)
            #self.connection.commit()

    #endregion
