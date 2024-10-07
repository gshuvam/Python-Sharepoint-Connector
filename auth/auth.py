import re
import os
import sys
import msal
import time
import subprocess
import customtkinter as ctk

import undetected_chromedriver as uc
from gui.dialogs import PasswordDialog
from logger.custom_logger import get_logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located, element_to_be_clickable, text_to_be_present_in_element

from auth.cache import CacheHandler
from auth.credentials import Credentials


class BaseAuth:
    def __init__(self, ENABLE_CACHE=True, IS_TEST=False):
        """
        Initialize common settings for authentication classes.
        :param ENABLE_CACHE: Whether to enable caching
        :param IS_TEST: Whether the environment is a test environment
        """
        self.ENABLE_CACHE = ENABLE_CACHE
        self.IS_TEST = IS_TEST
        self.logger = get_logger('Auth')


class DeviceFlowAuth(BaseAuth):
    def __init__(
            self,
            cache_handler: CacheHandler = None, 
            client_id='1b730954-1685-4b74-9bfd-dac224a7b894',
            tenant_id='common',
            scope='https://graph.microsoft.com/.default',
            **kwargs
        ):
        """
        Initialize the DeviceFlowAuth with authentication details.
        
        :param client_id: Application (client) ID from Azure AD
        :param authority: Azure AD authority URL
        :param scope: Permissions you request
        """
        super.__init__(**kwargs)
        self.client_id = client_id
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.scope = scope
        self.app = msal.PublicClientApplication(client_id=self.client_id, authority=self.authority)
        self.cache_handler = cache_handler

    def authenticate(self):
        """
        Perform authentication using the device code flow.
        """

        if self.ENABLE_CACHE and self.cache_handler:
            cache_data = self.cache_handler.load_cache()
            if cache_data and self.username == cache_data['username']:
                if cache_data['data_type'] == 'auth_token':
                    auth_token = self.cache_handler.validate_token(cache_data=cache_data)
                    if auth_token:
                        return auth_token
            self.logger.warning('Cache expired! Initiating login process!')

        flow = self.app.initiate_device_flow(scopes=[self.scope])

        if "message" in flow:
            token_response = self.app.acquire_token_by_device_flow(flow)
            if "access_token" in token_response:
                self.token_response = token_response
                auth_data = {
                    "Access Token:": token_response["access_token"],
                    "Refresh Token:": token_response.get("refresh_token")
                }
                self.cache_handler.save_cache(self.username, auth_data)
                return auth_data
            else:
                return None
        else:
            return None
        
    
    def refresh_token(self):
        """
        Refresh the access token using the refresh token without user interaction.
        """
        
        if self.token_response and "refresh_token" in self.token_response:
            token_response = self.app.acquire_token_by_refresh_token(self.token_response["refresh_token"], scopes=[self.scope])

            if "access_token" in token_response:
                self.token_response = token_response
                return token_response["access_token"]
            else:
                return None
        else:
            return None
        


class PasswordFlowAuth(BaseAuth):
    def __init__(self, credentials:Credentials, site_url:str, cache_handler:CacheHandler=None, interactive=False, **kwargs):
        """
        Initialize the PasswordFlowAuth with user credentials.
        
        :param credentials: An instance of the Credentials class
        """
        super.__init__(**kwargs)
        self.credentials = credentials
        self.cache_handler = cache_handler
        self.interactive = interactive
        self.site_url = site_url

    def authenticate(self):
        """
        Perform authentication using the password flow.
        """
        if self.ENABLE_CACHE:
            cache_data = self.cache_handler.load_cache()
            if cache_data and self.username == cache_data['username']:
                cookie_dict = self.cache_handler.validate_cache(cache_data)
                self.logger.success('Logged in successfully using cache!')
                if cookie_dict:
                    return cookie_dict
            self.logger.warning('Cache expired! Initiating login process!')
        
        # cookie is not valid
        if not self.IS_TEST:
            app = ctk.CTk()
            password_dialog = PasswordDialog(app, "Password", "Enter Sharepoint Password")
            self.password = password_dialog.get_input()
            app.destroy()
        self.driver = self.__initialize_webdriver()
        self.__login()
        cookie_dict =  self.__get_cookies()
        self.cache_handler.save_cache(self.username, cookie_dict)
        self.__quit_driver()
        return cookie_dict
    
    def __initialize_webdriver(self):
        """
        Initializes the Selenium WebDriver instance.

        Returns:
            WebDriver: The initialized WebDriver object for browser automation.
        """
        chrome_options = uc.ChromeOptions()
        if not self.DEBUGGING:
            if not self.interactive:
                chrome_options.add_argument("--headless")
            else:
                chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument('disable-infobars')
            chrome_options.add_argument('--disable-popup-blocking')
        driver = uc.Chrome(
            options=chrome_options,
            version_main=self.__get_version_main()
        )
        return driver
    
    def __get_cookies(self):
        """
        Retrieves the browser session cookies.

        Returns:
            dict: A dictionary containing the cookies for the current browser session.
        """

        cookies = self.driver.get_cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        return cookie_dict
    
    def __quit_driver(self):
        """
        Closes the WebDriver session and cleans up resources.

        Actions:
            - Closes the browser window.
            - Quits the WebDriver process.
            - Sets the WebDriver instance to None.
        """

        self.driver.close()
        self.driver.quit()
        self.driver = None

    def __get_version_main():
        """
        Retrieves the installed version of Google Chrome by checking predefined paths.

        Helper Function:
            get_version_via_subprocess(filename): Retrieves Chrome version using system commands.

        Returns:
            int or None: The major version number (e.g., 86) of the installed Chrome browser,
                        or None if the version cannot be determined.
        """

        def get_version_via_subprocess(filename):
            try:
                if os.name == 'nt':
                    result = subprocess.run(['wmic', 'datafile', 'where', f'name="{filename}"', 'get', 'Version', '/value'],
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
                    version = re.search(r'Version=([\d.]+)', result.stdout)
                    return version.group(1) if version else None

                elif os.path.exists(filename):
                    result = subprocess.run(['strings', filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    version = re.search(r'[\d.]+', result.stdout)
                    return version.group(0) if version else None

            except Exception:
                return None

        paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/usr/bin/google-chrome",
            r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
        ]

        version = list(filter(None, [get_version_via_subprocess(p) for p in paths]))
        
        if version:
            return int(version[0].split('.')[0])
        return None
    
    def __login(self):
        """
        Handles the login process based on the interactive flag.

        Actions:
            - Calls __password_flow_interactive() if self.interactive is True.
            - Calls __password_flow_auto() if self.interactive is False.
        """

        if self.interactive:
            self.__password_flow_interactive()
        else:
            self.__password_flow_auto()

    
    def __choose_mfa_and_verify(self):
        """
        Handles Multi-Factor Authentication (MFA) by selecting the appropriate verification method.

        Returns:
            bool: The result of the MFA verification.
        """
        
        parent_element = self.driver.find_element(By.XPATH, '//*[@id="idDiv_SAOTCS_Proofs"]')
        child_elements = parent_element.find_elements(By.CSS_SELECTOR, 'div.table-row')

        methods = {}
        for i, child in enumerate(child_elements):
            methods[i+1] = child

        for key, value in methods.items():
            print(f'{key}. {value.text}')
        print('Choose preferred MFA verification Option: ',end='\t')
        option = int(input())

        methods[option].click()

        if 'text' or 'code' in methods[option].lower():
            return self.__otp_verify()
        elif 'authenticator app' in methods[option].lower():
            return self.__microsoft_authenticator()
        else:
            return self.__call_verify()


    def __microsoft_authenticator(self):
        """
        Handles MFA verification using the Microsoft Authenticator app.

        Returns:
            bool: True if the verification was successful, False otherwise.
        """

        try:
            WebDriverWait(driver=self.driver, timeout=90).until(
                presence_of_element_located((By.XPATH, '//*[@id="idDiv_SAOTCAS_Description"]'))
            )
            mfa_text = self.driver.find_element(
                By.XPATH, '//*[@id="idDiv_SAOTCAS_Description"]').text
            mfa_code = self.driver.find_element(
                By.XPATH, '//*[@id="idRichContext_DisplaySign"]').text
            self.logger.warning('%s: %s', mfa_text, mfa_code)

            return True
        except Exception as e:
            self.logger.critical(
                'FATAL - Authentication was not successful. Please try again later.%s', e)
            sys.exit()
            return False            

    def __otp_verify(self):
        """
        Handles MFA verification via One-Time Password (OTP).

        Returns:
            bool: True upon successful verification.
        """

        WebDriverWait(driver=self.driver, timeout=90).until(
            presence_of_element_located((By.XPATH, '//*[@id="idTxtBx_SAOTCC_OTC"]'))
        )
        auth_code = int(input("Enter the authcode: "))
        auth_input = self.driver.find_element(By.XPATH, '//*[@id="idTxtBx_SAOTCC_OTC"]')
        auth_input.send_keys(auth_code)

        self.driver.find_element(By.XPATH, '//*[@id="idSubmit_SAOTCC_Continue"]').click()

        return True


    def __call_verify(self):
        """
        Handles MFA verification via phone call.

        Actions:
            - Logs a message indicating that a verification call was sent.
            - Waits for the user to complete the call.

        Returns:
            bool: True after the verification call completes.
        """

        self.logger.warning('Verification call sent! Please follow the on-call instructions to authenticate.')
        time.sleep(10)
        return True

    def __password_flow_auto(self):
        """
        Handles automatic login via password flow, including MFA verification if applicable.

        Actions:
            - Completes the MFA verification step.
            - Simulates a click on the "Sign in" button using the element with ID 'idSIButton9'.
            - Logs a success message upon successful login.
        """

        self.driver.get(self.site_url)
        # waiting for email screen popup
        WebDriverWait(driver=self.driver, timeout=90).until(
            presence_of_element_located((By.ID, 'i0116'))
        )
        username_input = self.driver.find_element(By.ID, 'i0116')
        if username_input:
            username_input.send_keys(self.credentials.username)
        time.sleep(2)
        self.driver.find_element(By.ID, 'idSIButton9').click()
        time.sleep(1)

        # checking for wrong username
        usernameerr_el = self.driver.find_elements(By.XPATH, '//*[@id="usernameError"]')
        if len(usernameerr_el) > 0:
            self.logger.critical(
                'FATAL - No account was found with the provided username!')
            exit()

        # waiting for password screen popup
        WebDriverWait(driver=self.driver, timeout=90).until(
            presence_of_element_located((By.ID, 'i0118'))
        )
        time.sleep(3)
        password_input = self.driver.find_element(By.ID, 'i0118')
        if password_input:
            password_input.send_keys(self.credentials.password)
        time.sleep(2)
        WebDriverWait(driver=self.driver, timeout=90).until(
            element_to_be_clickable((By.ID, 'idSIButton9'))
        )
        self.driver.find_element(By.ID, 'idSIButton9').click()
        time.sleep(4)

        # checking for wrong password
        passwderr_el = self.driver.find_elements(By.XPATH, '//*[@id="passwordError"]')
        if len(passwderr_el) > 0:
            self.logger.critical(
                'FATAL - Incorrect Password! Enter the correct one or reset it.')
            sys.exit()

        time.sleep(5)
        mfa_verification = False
        try:
            self.driver.find_element(By.XPATH, '//*[@id="idDiv_SAOTCS_Proofs"]')
            mfa_verification = self.__choose_mfa_and_verify()
        except:  # noqa: E722
            mfa_verification = self.__microsoft_authenticator()
        
        WebDriverWait(driver=self.driver, timeout=90).until(
            text_to_be_present_in_element(
                (
                    By.XPATH,
                    '//*[@id="lightbox"]/div[3]/div/div[2]/div/div[1]'
                ), 'Stay signed in?'
            )
        )

        if mfa_verification:
            self.logger.success('MFA verification complete')

        time.sleep(2)
        self.driver.find_element(By.ID, 'idSIButton9').click()

        self.logger.info('Successfully logged in!')

    def __password_flow_interactive(self):
        """
        Handles interactive login via password flow.

        Actions:
            - Logs a success message upon successful login after manual interaction.
        """
        
        self.driver.get(self.site_url)
        WebDriverWait(driver=self.driver, timeout=180).until(
            text_to_be_present_in_element(
                (By.XPATH, '//*[@id="lightbox"]/div[3]/div/div[2]/div/div[1]'), 'Stay signed in?')
        )
        self.driver.find_element(By.ID, 'idSIButton9').click()
        self.logger.info('Successfully logged in!')
    