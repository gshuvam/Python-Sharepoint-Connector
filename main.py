import os
import time
import random
from dotenv import find_dotenv, load_dotenv
import requests
import multiprocessing
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_element_located, element_to_be_clickable, text_to_be_present_in_element
from selenium.webdriver.support.ui import WebDriverWait

import undetected_chromedriver as uc

def wait(min_seconds=3, max_seconds=5):
    wait_time = random.uniform(min_seconds, max_seconds)
    time.sleep(wait_time)


def initiate_logger():
    SUCCESS_LEVEL_NUM = 25
    logging.addLevelName(SUCCESS_LEVEL_NUM, 'SUCCESS')

    class CustomLogger(logging.Logger):
        def success(self, message, *args, **kwargs):
            if self.isEnabledFor(SUCCESS_LEVEL_NUM):
                self._log(SUCCESS_LEVEL_NUM, message, args, **kwargs)

    logging.setLoggerClass(CustomLogger)

    class CustomFormatter(logging.Formatter):
        grey = "\x1b[38;20m"
        green = "\x1B[32;20m"
        yellow = "\x1b[33;20m"
        red = "\x1b[31;20m"
        bold_red = "\x1b[31;1m"
        reset = "\x1b[0m"
        format = "%(asctime)s - %(message)s"

        FORMATS = {
            logging.DEBUG: green + format + reset,
            logging.INFO: grey + format + reset,
            SUCCESS_LEVEL_NUM: green + format + reset,
            logging.WARNING: yellow + format + reset,
            logging.ERROR: red + format + reset,
            logging.CRITICAL: bold_red + format + reset
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    ch.setFormatter(CustomFormatter())

    logger.addHandler(ch)
    return logger

def login(driver, url, username, password, logger):
    driver.get(url)

    #username screen
    WebDriverWait(driver=driver, timeout=90).until(
        presence_of_element_located((By.ID, 'i0116'))
    )
    username_input = driver.find_element(By.ID, 'i0116')
    if username_input:
        username_input.send_keys(username)
    wait()
    driver.find_element(By.ID, 'idSIButton9').click()
    wait()

    #handling wrong username situation
    username_el = driver.find_elements(By.XPATH, '//*[@id="usernameError"]')
    if len(username_el)>0:
        logger.critical('FATAL - No account was found with provided username/email')
        exit()
    
    #password screen
    WebDriverWait(driver=driver, timeout=98).until(
        presence_of_element_located((By.ID, 'i0118'))
    )
    wait()
    password_input = driver.find_element(By.ID, 'i0118')
    if password_input:
        password_input.send_keys(password)
    wait()
    WebDriverWait(driver=driver, timeout=90).until(
        element_to_be_clickable((By.ID, 'idSIButton9'))
    )
    driver.find_element(By.ID, 'idSIButton9').click()
    wait()

    #handling wrong username situation
    passwderr_el = driver.find_elements(By.XPATH, '//*[@id="passwordError"]')
    if len(passwderr_el) > 0:
        logger.critical('FATAL - Incorrect Password! Enter the correct one or reset it.')
        exit()

    #MFA
    mfa_verification = False
    try:
        mfa_text = driver.find_element(
            By.XPATH, '//*[@id="idDiv_SAOTCAS_Description"]').text
        mfa_code = driver.find_element(
            By.XPATH, '//*[@id="idRichContext_DisplaySign"]').text
        logger.warning(f"{mfa_text}: {mfa_code}")
        mfa_verification = True
    except Exception as e:
        logger.critical(
            f'FATAL - Authentication was not successful. Please try again later.{e}')
        exit()

    WebDriverWait(driver=driver, timeout=98).until(
        text_to_be_present_in_element((By.XPATH, '//*[@id="lightbox"]/div[3]/div/div[2]/div/div[1]'), 'Stay signed in?')
    )

    if mfa_verification:
        logger.success('MFA verification complete')
    
    wait()
    driver.find_element(By.ID, 'idSIButton9').click()

    logger.info('Successfully logged in!')

def get_cookies(driver):
    cookies = driver.get_cookies()
    cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
    return cookie_dict

def create_session(cookie_dict):
    session = requests.Session()
    for name, value in cookie_dict.items():
        session.cookies.set(name, value)
    return session

def fetch_list_items(list_name, url, session, logger):
    headers = {
        'Accept': 'application/json; odata=verbose'
    }

    endpoint = f"{url}/_api/web/lists/getbytitle('{list_name}')/items"
    response = session.get(endpoint, headers=headers)

    if response.status_code == 200:
        return response.json()['d']['results']
    else:
        logger.critical('Something went wrong!.')
        return []


def main():
    logger = initiate_logger()
    load_dotenv(find_dotenv(), override=True)

    #initializing env vars
    username = os.environ.get('USERNAME')
    password = os.environ.get('PASSWORD')
    url = os.environ.get('SITE_URL')
    list_name = os.environ.get('LIST')

    DEBUGGING = True

    try:
        # creating service and setting up options
        # service = Service(driver_path)
        # chrome_options = Options()
        # if DEBUGGING:
        #     chrome_options.add_experimental_option('detach', True)
        # else:
        #     chrome_options.add_argument("--headless") 
        #     chrome_options.add_argument("--window-size=1920,1080")
        #     chrome_options.add_argument('--start-maximized')
        #     chrome_options.add_argument('--disable-gpu')
        #     chrome_options.add_argument('--no-sandbox')
        #     chrome_options.add_argument("--disable-extensions")
        #     chrome_options.add_argument('disable-infobars')
        # chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # initilizing webdriver
        # driver = webdriver.Chrome(service=service, options=chrome_options)

        chrome_options = webdriver.ChromeOptions()
        if not DEBUGGING:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--window-size=1920, 1080')
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('disable-infobars')
        driver = uc.Chrome(options=chrome_options)

        #logging in
        logger.info('Initializing sharepoint connection...')
        logger.success('Sharepoint site found - %s', url)
        login(driver=driver, url=url, username=username, password=password, logger=logger)

        #creating session
        cookie_dict = get_cookies(driver)
        session = create_session(cookie_dict)

        #testing session
        print(fetch_list_items(list_name, url, session, logger))

        driver.close()
        driver.quit()
        driver = None

    except Exception as e:
        logger.critical('Something went wrong!. %s', e)


if __name__=='__main__':
    process = multiprocessing.Process(target=main)
    process.start()
    process.join()#
    # main()