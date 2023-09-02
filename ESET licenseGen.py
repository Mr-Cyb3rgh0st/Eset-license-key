# Version 1.0.6.1 (07.08.2023)
import re
import time

from selenium.webdriver import Chrome
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service

from string import ascii_letters
from random import choice

import datetime
import requests
import os

GET_EBCN = 'document.getElementsByClassName'
GET_EBID = 'document.getElementById'
DEFAULT_MAX_ITER = 30
DEFAULT_DELAY = 1

class EmailConnectError(Exception):
    pass

class Email:
    def __init__(self):
        self.__login = None
        self.__domain = None
        self.__api = 'https://www.1secmail.com/api/v1/'
        
    def register(self):
        url = f'{self.__api}?action=genRandomMailbox&count=1'
        try:
            r = requests.get(url)
        except:
            raise EmailConnectError
        if r.status_code != 200:
            raise EmailConnectError
        self.__login, self.__domain = str(r.content, 'utf-8')[2:-2].split('@')
    
    def login(self, login, domain):
        self.__login = login
        self.__domain = domain
    
    def get_full_login(self):
        return self.__login+'@'+self.__domain
        
    def read_email(self):
        url = f'{self.__api}?action=getMessages&login={self.__login}&domain={self.__domain}'
        try:
            r = requests.get(url)
        except:
            raise EmailConnectError
        if r.status_code != 200:
            raise EmailConnectError
        return r.json()
    
    def get_message(self, message_id):
        url = f'{self.__api}?action=readMessage&login={self.__login}&domain={self.__domain}&id={message_id}'
        try:
            r = requests.get(url)
        except:
            raise EmailConnectError
        if r.status_code != 200:
            raise EmailConnectError
        return r.json()

class SharedTools:
    def untilConditionExecute(driver: Chrome, js: str, delay=DEFAULT_DELAY, max_iter=DEFAULT_MAX_ITER, positive_result=True):
        i = 0
        while True:
            try:
                if i > max_iter:
                    return False
                result = driver.execute_script(js)
                if result == positive_result:
                    return True
            except Exception as E:
                pass
            i += 1
            time.sleep(delay)

    def createPassword(length):
        return ''.join(['Xx0$']+[choice(ascii_letters) for _ in range(length)])

class EsetRegister:
    def __init__(self, registered_email_obj: Email, eset_password: str):
        self.email_obj = registered_email_obj
        self.eset_password = eset_password
        self.driver = None

    def initDriver(self):
        driver_options = ChromeOptions()
        if os.name == 'posix': # For Linux
            print('[*] Initializing driver for Linux')
            driver_options.add_argument('--no-sandbox')
            driver_options.add_argument('--disable-dev-shm-usage')
            driver_options.add_argument('--headless')
        if os.name == 'nt':
            print('[*] Initializing driver for Windows')
        driver_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.driver = Chrome(options=driver_options)
        self.driver.set_window_size(600, 600)

    def getToken(self, delay=DEFAULT_DELAY, max_iter=DEFAULT_MAX_ITER) -> str:
        i = 0
        while True:
            json = self.email_obj.read_email()
            if json != []:
                message = json[-1]
                if message['from'].find('product.eset.com') != -1:
                    message_body = self.email_obj.get_message(message['id'])
                    match = re.search(r'token=[a-zA-Z\d:/-]*', message_body['body'])
                    if match is not None:
                        token = match.group()[6:]
                        return token
            i += 1
            if i == max_iter:
                print('[-] Token retrieval error!!!')
                self.driver.quit()
                return ''
            time.sleep(delay)

    def createAccount(self):
        print('\n[*] [EMAIL] Register page loading...')
        self.driver.get(f'https://login.eset.com/Register')
        print('[+] [EMAIL] Register page is loaded!')
        self.driver.execute_script(f"{GET_EBID}('Email').value='{self.email_obj.get_full_login()}'\ndocument.forms[0].submit()")

        print('\n[*] [PASSWD] Register page loading...')
        SharedTools.untilConditionExecute(self.driver, f"return typeof {GET_EBID}('Password') === 'object'")
        self.driver.execute_script(f"{GET_EBID}('Password').value='{self.eset_password}'\ndocument.forms[0].submit()")
        print('[+] [PASSWD] Register page is loaded!')
        
        while True:
            time.sleep(0.5)
            title = self.driver.execute_script('return document.title')
            if title == 'Service not available':
                print('\n[-] ESET temporarily blocked your IP, try again later!!!')
                self.driver.quit()
                break
            url = self.driver.execute_script('return document.URL')
            if url == 'https://home.eset.com/':
                return True
        return False

    def confirmAccount(self):
        token = self.getToken()
        if token == '':
            return False
        print(f'\n[+] ESET Token: {token}')
        print('\n[*] Account confirmation is in progress...')
        self.driver.get(f'https://login.eset.com/link/confirmregistration?token={token}')
        SharedTools.untilConditionExecute(self.driver, 'return document.title === "ESET HOME"')
        SharedTools.untilConditionExecute(self.driver, f'return typeof {GET_EBCN}("verification-email_p")[1] === "object"', positive_result=False)
        print('[+] Account successfully confirmed!')
        return True

    def returnDriver(self) -> Chrome:
        return self.driver

class EsetKeygen:
    def __init__(self, registered_email_obj: Email, driver: Chrome):
        self.email_obj = registered_email_obj
        self.driver = driver

    def sendRequestForKey(self):
        print('\n[*] License page loading...')
        self.driver.get("https://home.eset.com/licenses")
        SharedTools.untilConditionExecute(self.driver, f"return {GET_EBCN}('ion-cui-button ios button button-solid ion-activatable ion-focusable hydrated').length > 1")
        print('[+] License page is loaded!')
        
        print('\n[*] Request sending...')
        self.driver.execute_script(f"{GET_EBCN}('ion-cui-button ios button button-solid ion-activatable ion-focusable hydrated')[1].click()")

        print('[*] Waiting for permission to request...')
        SharedTools.untilConditionExecute(self.driver, f"return {GET_EBCN}('ion-cui-button ios button button-clear ion-activatable ion-focusable hydrated').length > 10")
        self.driver.execute_script(f"{GET_EBCN}('ion-cui-button ios button button-clear ion-activatable ion-focusable hydrated')[10].click()")
        print('[+] Access to the request was open!')

        print('\n[*] Platforms loading...')
        SharedTools.untilConditionExecute(self.driver, f"return {GET_EBCN}('ion-cui-card device-protect-os-card ios hydrated').length > 1")
        self.driver.execute_script(f"{GET_EBCN}('ion-cui-card device-protect-os-card ios hydrated')[1].click()")
        print('[+] Windows platform is selected!')
        SharedTools.untilConditionExecute(self.driver, f"return typeof {GET_EBCN}('ion-cui-button ios button button-block button-clear ion-activatable ion-focusable hydrated')[0] === 'object'")
        self.driver.execute_script(f"{GET_EBCN}('ion-cui-button protect-page--continue-button ion-color ion-color-secondary ios button button-block button-solid ion-activatable ion-focusable hydrated')[0].click()")
        
        print('\n[*] Request license page loading...')
        SharedTools.untilConditionExecute(self.driver, f"return typeof {GET_EBCN}('sc-ion-input-ios-h sc-ion-input-ios-s ios hydrated')[0] === 'object'")
        print('[*] Sending a request for a license...')
        self.driver.execute_script(f"{GET_EBCN}('sc-ion-input-ios-h sc-ion-input-ios-s ios hydrated')[0].value = '{self.email_obj.get_full_login()}'")
        self.driver.execute_script(f"{GET_EBCN}('ion-cui-button ios button button-solid ion-activatable ion-focusable hydrated')[1].click()")
        print('[*] Waiting for confirmation of request...')

        SharedTools.untilConditionExecute(self.driver, f"return typeof {GET_EBCN}('ProtectionSuccess')[0] === 'object'")
        print('[+] Request was approved!')

    def getLicenseData(self):
        self.driver.get("https://home.eset.com/licenses")
        print('\n[*] License uploads...')
        SharedTools.untilConditionExecute(self.driver, f"return {GET_EBCN}('ion-cui-button license-preview_link-btn ios button button-block button-solid ion-activatable ion-focusable hydrated').length > 0", max_iter=20)

        license_tag = self.driver.execute_script(f"return {GET_EBCN}('ion-cui-button license-preview_link-btn ios button button-block button-solid ion-activatable ion-focusable hydrated')[0].href")
        print('[+] License is uploaded!')
        self.driver.get(f"https://home.eset.com{license_tag}")

        print('\n[*] Getting information from the license...')
        SharedTools.untilConditionExecute(self.driver, f"return {GET_EBCN}('DetailInfoSectionItem__value').length > 15")

        license_name = self.driver.execute_script(f"return {GET_EBCN}('DetailInfoSectionItem__value')[0].textContent")
        license_out_date = self.driver.execute_script(f"return {GET_EBCN}('DetailInfoSectionItem__value')[2].textContent")
        license_key = self.driver.execute_script(f"return {GET_EBCN}('DetailInfoSectionItem__value')[4].textContent")
        print('[+] Information successfully received!')
        return license_name, license_out_date, license_key
        
if __name__ == '__main__':
    try:
        email_obj = Email()
        email_obj.register()
        eset_password = SharedTools.createPassword(6)
        EsetReg = EsetRegister(email_obj, eset_password)
        EsetReg.initDriver()
        if not EsetReg.createAccount():
            input('Press Enter...')
            exit()
        if not EsetReg.confirmAccount():
            input('Press Enter...')
            exit()
        driver = EsetReg.returnDriver()
        EsetKeyG = EsetKeygen(email_obj, driver)
        EsetKeyG.sendRequestForKey()
        license_name, license_out_date, license_key = EsetKeyG.getLicenseData()
        output_line = f"\nLicense Name: {license_name}\nLicense Out Date: {license_out_date}\nLicense Key: {license_key}\n"
        print(output_line)
        date = datetime.datetime.now()
        f = open(f"{str(date.day)}.{str(date.month)}.{str(date.year)} - ESET KEYS.txt", 'a')
        f.write(output_line)
        f.close()
        driver.quit()
    except Exception as E:
        print(E)
    input('Press Enter...')
