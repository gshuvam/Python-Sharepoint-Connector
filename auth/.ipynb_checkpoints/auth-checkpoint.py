import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_element_located, element_to_be_clickable, text_to_be_present_in_element
from selenium.webdriver.support.ui import WebDriverWait
import undetected_chromedriver as uc

from logger.custom_logger import CustomLoggerSetup


class LoginHandler:
    def __init__(self, site_url, username, password, DEBUGGING):
        self.logger = CustomLoggerSetup.create_custom_logger(self.__class__.__name__)
        self.site_url = site_url
        self.username = username
        self.password = password
        self.DEBUGGING = DEBUGGING
        self.driver = self.initialize_webdriver()

    def initialize_webdriver(self):
        chrome_options = webdriver.ChromeOptions()
        if not self.DEBUGGING:
            chrome_options.add_argument("--headless") 
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument('disable-infobars')
        driver = uc.Chrome(options=chrome_options)
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
            exit()

        # MFA verification
        mfa_verification = False
        try:
            mfa_text = self.driver.find_element(
                By.XPATH, '//*[@id="idDiv_SAOTCAS_Description"]').text
            mfa_code = self.driver.find_element(
                By.XPATH, '//*[@id="idRichContext_DisplaySign"]').text
            self.logger.warning('%s: %s', mfa_text, mfa_code)
            mfa_verification = True
        except Exception as e:
            self.logger.critical(
                'FATAL - Authentication was not successful. Please try again later.%s', e)
            exit()

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
