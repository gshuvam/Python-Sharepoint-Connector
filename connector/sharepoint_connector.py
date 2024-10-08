import requests
from logger.custom_logger import get_logger

class SharePointConnector:
    """
    A class to manage SharePoint connections using either cookies or authentication tokens.

    Attributes:
        site_url (str): The URL of the SharePoint site.
        cookie_dict (dict, optional): A dictionary of cookies for session authentication.
        auth_token (str, optional): The authentication token for session authentication.
        session (requests.Session): The HTTP session used for making requests to SharePoint.
        digest_value (str): The form digest value required for making POST requests to SharePoint.
        logger (Logger): A logger instance for logging information.

    Methods:
        __create_session(): Creates and configures an HTTP session with authentication.
        __get_form_digest_value(site_url): Retrieves the form digest value from the SharePoint site.
    """


    def __init__(self, site_url, cookie_dict=None, auth_token=None):
        """
        Initializes the SharePointConnector instance.

        Args:
            site_url (str): The URL of the SharePoint site.
            cookie_dict (dict, optional): A dictionary of cookies for session authentication.
            auth_token (str, optional): The authentication token for session authentication.
        """

        self.logger = get_logger(self.__class__.__name__)
        self.site_url = site_url
        self.cookie_dict = cookie_dict
        self.auth_token = auth_token
        self.session = self.__create_session()
        self.digest_value = self.__get_form_digest_value(site_url)


    def __create_session(self) -> requests.Session:
        """
        Creates and configures a `requests.Session` object for making HTTP requests to SharePoint.

        If `cookie_dict` is provided, it sets cookies in the session for authentication.
        If `auth_token` is provided, it adds the token to the session headers for authentication.

        Returns:
            requests.Session: The configured HTTP session for SharePoint requests.
        """

        session = requests.Session()

        if self.cookie_dict:
            for name, value in self.cookie_dict.items():
                session.cookies.set(name, value)
        
        if self.auth_token:
            session.headers.update({
                'Authorization': f'Bearer {self.auth_token}'
            })

        return session
    
    def __get_form_digest_value(self, site_url) -> str:
        """
        Retrieves the form digest value from the SharePoint site.

        The form digest value is required for making POST requests to SharePoint.

        Args:
            site_url (str): The URL of the SharePoint site.

        Returns:
            str: The form digest value retrieved from the SharePoint site.
        """
        
        if not site_url:
            return None
        headers = {
            "Accept": "application/json; odata=verbose",
            "Content-Type": "application/json; odata=verbose"
        }
        response = self.session.post(f"{site_url}/_api/contextinfo", headers=headers)

        if response.status_code == 200:
            return response.json()['d']['GetContextWebInformation']['FormDigestValue']