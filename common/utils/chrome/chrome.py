import os
import time

import json
import yaml
import shutil

from amazoncaptcha import AmazonCaptcha

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType

from webdriver_manager.chrome import ChromeDriverManager

import requests
from io import BytesIO
import urllib.parse as urlparse


class Chrome:
    def __init__(self) -> None:
        self.driver = None
        self.driver_path = ''
        self.profile_path = ''
        self.num_of_request = 0

    # get chrome profile 
    def get_chrome_options(
        self, extension_path: str = None, 
        fresh_profile: bool = False,
        no_image: bool = False,
        proxy:str=None,
    ) -> Options:
        """
        Modifi chrome options with profile headless and windownsize
        Parameters
        ----------
        extension_path: string
            Path to extension file. if the extension path is None, 
            there is nothing extension is added.
        fresh_profile: bool or None, default None
            Remove the old profile exsised if the flag is True, default 
            options is False that mean don't remove old profile.
        """
        if fresh_profile:
            self.removeProfileExisted(self.profile_path)

        chrome_options = Options()
        prefs = dict()

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_argument("disable-infobars")
        
        if no_image == True:
            chrome_options.add_argument('--blink-settings=imagesEnabled=false')
            prefs["profile.managed_default_content_settings.images"] = 2
        
        if prefs:
            chrome_options.add_experimental_option("prefs", prefs)

        # chrome_options.headless = False
        # # chrome_options.add_argument("start-maximized")
        chrome_options.add_argument('--user-data-dir=' + self.profile_path)
        chrome_options.add_argument('--profile-directory=Profile 1')

        if proxy is not None:
            chrome_options.add_argument('--proxy-server=%s' % proxy)
    
        if extension_path is not None:
            chrome_options.add_extension(extension_path)

        # # Fix bug chrome show log
        # chrome_options.add_experimental_option(
        #     "excludeSwitches", ["enable-logging"]
        # )

        return chrome_options
    
    def create_new_profile(
        self, 
        driver_path:str=None, 
        profile_path:str=None, 
        extension: str = None,
        fresh_profile: bool = False,
        no_load_image: bool = False,
        proxy:str=None,
    ) -> bool:
        """
        Create the new profile with driver and profile path
        
        Parameters
        ----------
        driver_path: string
            The string path to chrome driver corresponding with the current
            chrome version.
        profile_path: string
            The string path to dir that will be storage the chrom user 
            profile.
        extension: string or None
            the string path to extension cxr file you have downloaded. 
            default don't add extension with None value
        
        Examples
        ----------
        Create new profile without extension and don't fresh profile
        >>> create_new_profile("home/driver", "home/profile/sample")
        """
        if self.driver != None:
            self.driver.quit()
        self.driver_path = driver_path
        self.profile_path = profile_path
        self.driver = webdriver.Chrome(
            executable_path=ChromeDriverManager().install(), 
            chrome_options=self.get_chrome_options(
                extension,
                fresh_profile,
                no_load_image,
                proxy=proxy
            )
        )

        # Create new proto for navigator
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source":
                "const newProto = navigator.__proto__;"
                "delete newProto.webdriver;"
                "navigator.__proto__ = newProto;"
        })

        # Remove all tab without main
        windows = self.driver.window_handles
        if len(windows) > 1:
            for i in range(1, len(windows)):
                window_name = windows[i]
                self.driver.switch_to.window(window_name)
                self.driver.close()
            self.driver.switch_to.window(windows[0])

        return True

    def find_elements_by_xpath(self, xpath: str) -> list:
        return self.driver.find_elements(By.XPATH, xpath)

    def expand_shadow_element(self, element: WebElement) -> WebElement:
        script = 'return arguments[0].shadowRoot'
        shadow_root = self.driver.execute_script(script, element)
        return shadow_root

    def clean_cached_cookies(self) -> None:
        self.get_page(r'chrome://settings/clearBrowserData')
        self.waiting_for_process()

        root1 = self.driver.find_element(By.TAG_NAME,'settings-ui')
        shadow_root1 = self.expand_shadow_element(root1)

        root2 = shadow_root1.find_element(By.CSS_SELECTOR, 'settings-main')
        shadow_root2 = self.expand_shadow_element(root2)

        root3 = shadow_root2.find_element(By.CSS_SELECTOR, 'settings-basic-page')
        shadow_root3 = self.expand_shadow_element(root3)

        root4 = shadow_root3.find_element(By.CSS_SELECTOR, 'settings-privacy-page')
        shadow_root4 = self.expand_shadow_element(root4)

        root5 = shadow_root4.find_element(By.CSS_SELECTOR, 'settings-clear-browsing-data-dialog')
        shadow_root5 = self.expand_shadow_element(root5)

        root6 = shadow_root5.find_element(By.CSS_SELECTOR, 'settings-dropdown-menu')
        shadow_root6 = self.expand_shadow_element(root6)

        select = Select(shadow_root6.find_element(By.CLASS_NAME, 'md-select'))
        select.select_by_visible_text('All time')

        button = shadow_root5.find_element(By.CSS_SELECTOR, r'#clearBrowsingDataConfirm')
        button.click()

    def get_image_through_site(self, url: str) -> BytesIO:
        try: 
            self.getPage(url)
            self.waiting_for_process()
            img_element = self.driver_find_elements('//img')
            if len(img_element) == 0:
                return None
            image = img_element[0].screenshot_as_png

            if self.num_of_request % 50 == 0:
                self.clean_cached_cookies()

            return BytesIO(image)
        except Exception as ex:
            print(f"Exception has been thrown. {ex}")
            return False

    def get_page_via_gg_translate(self, url: str) -> bool:
        try:
            if 'translate.goog' in url:
                self.get_page(url)
            else:
                query = urlparse.urlparse(url).query
                url = url.replace(query, requests.utils.quote(query))

                url_converted = (
                    'https://translate.google.com/translate'
                    f'?sl=vi&tl=en&hl=en&u={url}&client=webapp'
                    '&_x_tr_pto=op'
                )
                self.get_page(url_converted)
        except Exception as ex:
            print(f"Exception has been thrown. {ex}")
            return False
        return True

    def getPageWithProxySite(self, link: str) -> bool:
        try: 
            url_proxySite = r'https://www.proxysite.com/'
            self.getPage(url_proxySite)
            self.waiting_for_process()
            input_url = self.driver.find_element(By.XPATH, r'//input[@placeholder="Enter Url"]')
            input_url.send_keys(link)
            go_button = input_url.find_element(By.XPATH, r'.//following-sibling::button')
            go_button.click()
        except Exception as ex:
            print(f"Exception has been thrown. {ex}")
            return False
        return True

    def get_page(self, link: str) -> bool:
        try:
            self.driver.get(link)
            self.num_of_request += 1
        except Exception as ex:
            print(f"Get page Failed!!! Exception has been thrown. {ex}")
            return False
        return True

    def removeProfileExisted(self, path: str) -> None:
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)

    def waiting_for_process(self, wait:int = 1, sleep:int = 1) -> None:
        self.driver.implicitly_wait(wait) # seconds
        time.sleep(sleep)
    
    def close(self, remove_profile:bool=False) -> None:
        if self.driver != None:
            self.driver.quit()
        if remove_profile:
            self.removeProfileExisted(self.profile_path)
    
    def post(self, action: str, params: dict) -> None:
        return self.driver.execute_script("""
        function post(path, params, method='post') {
            const form = document.createElement('form');
            form.method = method;
            form.action = path;
        
            for (const key in params) {
                if (params.hasOwnProperty(key)) {
                const hiddenField = document.createElement('input');
                hiddenField.type = 'hidden';
                hiddenField.name = key;
                hiddenField.value = params[key];
        
                form.appendChild(hiddenField);
            }
            }
        
            document.body.appendChild(form);
            form.submit();
        }
        params = """ + str(params) + """
        
        return post(arguments[1], arguments[0]);
        """, params, action)

    def post3(self, action: str, params: dict) -> None:
        self.driver.execute_script("""
        param = JSON.stringify(arguments[0])
        $.ajax({
            url: arguments[1],
            type: 'POST',
            data: param,
            success: function (data) {
                alert(data);
            }
        });
        """, params, action)

    def post2(self, action: str, params: dict) -> str:
        params = str(params)
        params = params.replace("'", '"')
        params = params.replace('True', 'true')
        params = params.replace('False', 'false')

        return self.driver.execute_script("""
        var path = arguments[0]
        var params = """ + params + """
        const response = await fetch(path, {
            method: 'POST',
            headers: {
                'accept': 'application/json',
                'content-type': 'application/json',
                'user-agent': 'Mozilla/5.0 ...'
            },
            body: JSON.stringify(params)
        })
        return response.text();
        """, action)

    def get_page_via_proxysite(self, url: str) -> None:
        act = ('https://eu2.proxysite.com'
            '/includes/process.php?action=update')
        self.post(action=act, params={'d':url})

    def load_localstorage(self, data:dict) -> None:
        for key, value in data.items():
            script = "window.localStorage.setItem(arguments[0], arguments[1]);"
            self.driver.execute_script(script, key, value)

    def get_cookies_dict(self) -> dict:
        cookies = dict()
        all_cookies = self.driver.get_cookies()
        for cookie in all_cookies:
            cookies[cookie['name']] = cookie['value']
        return cookies

    def get_page_via_hidemyass(self, url:str) -> None:
        act = ('https://proxy-sea.hidemyass-freeproxy.com/process/en-ww')
        self.post(
            action=act, 
            params={
                'form[url]':url, 
                'form[dataCenter]': 'us', 
                'terms-agreed': '1'
            }
        )

        self.waiting_for_process()
        xpath = '//div[@class="terms-agree-wrapper"]//a[@class="button primary"]'
        terms_agree_wrapper = self.find_elements(By.XPATH,xpath)
        if len(terms_agree_wrapper) != 0:
            agree_href = terms_agree_wrapper[0].get_attribute('href')
            self.getPage(agree_href)
            self.waiting_for_process()

    
    def scroll_until_the_end(self) -> None:
        SCROLL_PAUSE_TIME = 0.1
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        for i in  range(int(last_height/1000)):
            # Scroll down to bottom
            self.driver.execute_script(f"window.scrollTo(0, {int(i*1000)});")
            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)


if __name__ == "__main__":
    profile_path = r'I:\profiles'
    profile_name = 'test'

    link = 'https://www.amazon.com/'
    chrome = Chrome()
    chrome.create_new_profile(
        profile_path=os.path.join(profile_path,profile_name),
        no_load_image=True)
    chrome.get_page_amz_captcha(link)
    pass