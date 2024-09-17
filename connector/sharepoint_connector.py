import requests
from logger.custom_logger import get_logger

class SharePointConnector:
    def __init__(self, site_url, cookie_dict=None, auth_token=None):
        self.logger = get_logger(self.__class__.__name__)
        self.site_url = site_url
        self.cookie_dict = cookie_dict
        self.auth_token = auth_token
        self.session = self.__create_session()
        self.digest_value = self.__get_form_digest_value(site_url)

    def __create_session(self):
        session = requests.Session()

        if self.cookie_dict:
            for name, value in self.cookie_dict.items():
                session.cookies.set(name, value)
        
        if self.auth_token:
            session.headers.update({
                'Authorization': f'Bearer {self.auth_token}'
            })

        return session
    
    def __get_form_digest_value(self, site_url):
        if not site_url:
            return None
        headers = {
            "Accept": "application/json; odata=verbose",
            "Content-Type": "application/json; odata=verbose"
        }
        response = self.session.post(f"{site_url}/_api/contextinfo", headers=headers)

        if response.status_code == 200:
            return response.json()['d']['GetContextWebInformation']['FormDigestValue']