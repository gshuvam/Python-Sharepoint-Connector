import sys
import time
import re
import os
import subprocess
import customtkinter as ctk

from auth.cache import CacheHandler
import undetected_chromedriver as uc
from gui.dialogs import PasswordDialog
from logger.custom_logger import get_logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located, element_to_be_clickable, text_to_be_present_in_element


class LoginHandler:
    def __init__(self, site_url, username, password, DEBUGGING, cache_file, key_file, domain):
        self.logger = get_logger(self.__class__.__name__)
        self.site_url = site_url
        self.username = username
        self.password = password
        self.DEBUGGING = DEBUGGING
        self.cache_file = cache_file
        self.key_file = key_file
        self.domain = domain
        self.cache_handler = CacheHandler(cache_file=self.cache_file, key_file=self.key_file, domain=self.domain)
        self.driver = None

    def initialize_webdriver(self):
        chrome_options = uc.ChromeOptions()
        if not self.DEBUGGING:
            chrome_options.add_argument("--headless")
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
    
    def login(self):
        self.driver.get(self.site_url)
        # waiting for email screen popup
        WebDriverWait(driver=self.driver, timeout=90).until(
            presence_of_element_located((By.ID, 'i0116'))
        )
        username_input = self.driver.find_element(By.ID, 'i0116')
        if username_input:
            username_input.send_keys(self.username)
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
            password_input.send_keys(self.password)
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

        # MFA verification
        mfa_verification = False
        try:
            WebDriverWait(driver=self.driver, timeout=90).until(
                presence_of_element_located((By.XPATH, '//*[@id="idDiv_SAOTCAS_Description"]'))
            )
            mfa_text = self.driver.find_element(
                By.XPATH, '//*[@id="idDiv_SAOTCAS_Description"]').text
            mfa_code = self.driver.find_element(
                By.XPATH, '//*[@id="idRichContext_DisplaySign"]').text
            self.logger.warning('%s: %s', mfa_text, mfa_code)
            mfa_verification = True
        except Exception as e:
            self.logger.critical(
                'FATAL - Authentication was not successful. Please try again later.%s', e)
            sys.exit()

        WebDriverWait(driver=self.driver, timeout=90).until(
            text_to_be_present_in_element(
                (By.XPATH, '//*[@id="lightbox"]/div[3]/div/div[2]/div/div[1]'), 'Stay signed in?')
        )

        if mfa_verification:
            self.logger.success('MFA verification complete')

        time.sleep(3)
        self.driver.find_element(By.ID, 'idSIButton9').click()

        self.logger.info('Successfully logged in!')
    
    def get_cookies(self):
        cookies = self.driver.get_cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        return cookie_dict
    
    def quit_driver(self):
        self.driver.close()
        self.driver.quit()
        self.driver = None

    def authenticate(self, ENABLE_CACHE, IS_TEST=False):
        if ENABLE_CACHE:
            cache_data = self.cache_handler.load_cache()
            if cache_data and self.username == cache_data['username']:
                cookie_dict = self.cache_handler.validate_cache(cache_data)
                self.logger.success('Logged in successfully using cache!')
                if cookie_dict:
                    return cookie_dict
            self.logger.warning('Cache expired! Initiating login process!')
        
        # cookie is not valid
        if not IS_TEST:
            app = ctk.CTk()
            password_dialog = PasswordDialog(app, "Password", "Enter Sharepoint Password")
            self.password = password_dialog.get_input()
            app.destroy()
        self.driver = self.initialize_webdriver()
        self.login()
        cookie_dict =  self.get_cookies()
        self.cache_handler.save_cache(self.username, cookie_dict)
        self.quit_driver()
        return cookie_dict
    
    def __get_version_main():
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