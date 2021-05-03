from sources.vendor_data.hedge_eye.data_access_layer.base_rest_manager import *
import requests

class TwoCaptchaManager(BaseRESTManager):

    #region Constructors
    def __init__(self,pLoginURL,pCaptchaSvcURL,pTwoCaptchaCustomerKey,pSiteKey):
        self.LoginURL=pLoginURL
        self.CaptchaSvcURL=pCaptchaSvcURL
        self.TwoCaptchaCustomerKey=pTwoCaptchaCustomerKey
        self.SiteKey=pSiteKey


    #endregion

    #region Private Static Attributes

    @staticmethod
    def _REQUEST_ID_SITE():
        return "/in.php"

    @staticmethod
    def _TOKEN_REQ_SITE():
        return "/res.php"

    #endregion


    #region Public Methods

    def GetCapthaRequestId(self):

        queryString = "?key={}&method={}&googlekey={}&pageurl={}" \
            .format(self.TwoCaptchaCustomerKey, "userrecaptcha", self.SiteKey, self.LoginURL)

        url = self.CaptchaSvcURL + self._REQUEST_ID_SITE() + queryString

        r = requests.get(url=url, headers=self.GetHeaders())

        if r.status_code == 200:
            if r.text.startswith("OK"):
                return r.text.split("|")[1]
            else:
                raise Exception("Error recovering 2Captcha request id:{}".format(r.text))
        else:
            raise Exception(r.text)


    def GetHCaptchaToken(self,requestId):

        queryString = "?key={}&action={}&id={}".format(self.TwoCaptchaCustomerKey, "get", requestId)

        url = self.CaptchaSvcURL + self._TOKEN_REQ_SITE() + queryString

        r = requests.get(url=url, headers=self.GetHeaders())

        if r.status_code == 200:
            if r.text.startswith("OK"):
                return r.text.split("|")[1]
            else:
                raise Exception("Error recovering capcha token:{}".format(r.text))
        else:
            raise Exception(r.text)

    #endregion



