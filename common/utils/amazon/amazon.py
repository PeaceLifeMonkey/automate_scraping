import json
import yaml
import time
import datetime

from amazoncaptcha import AmazonCaptcha
from yaml.loader import SafeLoader
from selenium.webdriver.common.by import By
from selenium.webdriver.remote import webelement
from webdriver_manager.chrome import ChromeDriverManager

from common.utils.amazon.amazon_request import send_change_location_request
from common.utils.chrome.chrome import Chrome

class Amazon:
    _AMAZON_WEB_ADDRESS = 'https://www.amazon.com'

    def __init__(
        self, config_path, profile_path
    ) -> None:
        self.load_config(config_path)
        self.init_driver(profile_path)
        self.withdraw_time = datetime.datetime.now()
        self.set_amazon_location_v2('90001')

    def load_config(self, config_path) -> None:
        with open(config_path) as file:
            self.cfg = yaml.load(file, Loader=SafeLoader)

    def init_driver(self, profile_path) -> None:
        self.chrome = Chrome()
        self.chrome.create_new_profile(profile_path = profile_path, 
                                        no_load_image=True)
        self.driver = self.chrome.driver

    def driver_find_elements(self, xpath) -> list:
        return self.driver.find_elements(By.XPATH, xpath)

    def driver_find_elements_by_id(self,xpath) -> list:
        return self.driver.find_elements(By.ID,xpath)

    def driver_find_element(self, xpath) -> webelement:
        return self.driver.find_element(By.XPATH, xpath)
    
    def get_page(self, asin:str) -> None:
        link = self.cfg["AMAZON_LINK"] + asin + "?th=1&psc=1"
        self.driver.get(link)

    def get_page_amz_captcha(self, asin:str) -> bool:
        try:
            link = self.cfg["AMAZON_LINK"] + asin + "?th=1&psc=1"
            self.driver.get(link)
            image = self.find_elements(By.XPATH,'//*[@class="a-row a-text-center"]/img')
            if len(image) != 0:
                link_image = image[0].get_attribute("src")
                captcha = AmazonCaptcha.fromlink(link_image)
                solution = captcha.solve()
                self.driver_find_elements('//*[@id="captchacharacters"]')[0].send_keys(solution)
                self.driver_find_elements('//*[@type="submit"]')[0].click()
        except Exception as ex:
            print(f"Get link Failed!!! Exception has been thrown. {ex}")
            return False
        return True

    def check_exist(self) -> None:
        dogs = self.driver_find_elements('//img[@id="d"]')
        if len(dogs) == 0:
            return True
        else:
            img_alt = dogs[0].get_attribute("alt")
            if img_alt == "Dogs of Amazon":
                return False

    def check_amazon_location(self, loc):
        elements = self.driver.find_elements("id", "glow-ingress-line2")

        location = None
        if len(elements) != 0:
            location = elements[0].text

        if location != None:
            if loc in location:
                return True

        return False

    def set_amazon_location_v1(self, zipcode: str) -> bool:
        # Select to change deliver button
        elements = self.driver.find_elements('id', 'nav-global-location-slot')
        if len(elements) != 0:
            elements[0].click()
            time.sleep(3)
        else:
            return False

        try:
            elements = self.driver.find_elements('id', 'GLUXChangePostalCodeLink')
            if len(elements) != 0:
                elements[0].click()
                time.sleep(1)
        except Exception as ex:
            pass

        elements = self.driver.find_elements('id', 'GLUXZipUpdateInput')
        if len(elements) != 0:
            elements[0].clear()
            elements[0].send_keys(zipcode)
        else:
            return False
        
        elements = self.driver.find_elements('id', 'GLUXZipUpdate')
        if len(elements) != 0:
            elements[0].click()
            time.sleep(1)
        else:
            return False
        
        self.driver.refresh()
        return True

    def set_amazon_location_v2(self, zipcode: str) -> bool:
        try:
            self.driver.get(self._AMAZON_WEB_ADDRESS)
            image = self.driver_find_elements('//*[@class="a-row a-text-center"]/img')
            if len(image) != 0:
                link_image = image[0].get_attribute("src")
                captcha = AmazonCaptcha.fromlink(link_image)
                solution = captcha.solve()
                self.driver.find_elements(By.XPATH,'//*[@id="captchacharacters"]')[0].send_keys(solution)
                self.driver.find_elements(By.XPATH,'//*[@type="submit"]')[0].click()
                # self.driver.get(self._AMAZON_WEB_ADDRESS)
                self.chrome.waiting_for_process()

                if self.check_amazon_location(zipcode):
                    # print("Location is changed!!!")
                    # self.logger.info("Location is changed!!!")
                    return True
                # else:
                #     print("Location is changed!!!")
                    # self.logger.info("Try to change amazon location!!!")

                xpath = r'//span[@id="nav-global-location-data-modal-action"]'
                location_elements = self.driver_find_elements(xpath)
                if len(location_elements) == 1:
                    data = location_elements[0].get_attribute("data-a-modal")
                    json_data = json.loads(data)

                    cookies = self.chrome.get_cookies_dict()
                    ajax_token = json_data["ajaxHeaders"]["anti-csrftoken-a2z"]
                    check, mess = send_change_location_request(
                        ajax_token, cookies, zipcode
                    )

                    if check == False:
                        check = self.set_amazon_location_v1(zipcode)
                        return False
                else:
                    check = self.set_amazon_location_v1(zipcode)
                    return False
        except Exception as ex:
            print(f"Get link Failed!!! Exception has been thrown. {ex}")
            return False
        return True


if __name__ == "__main__":
    profile_path = r'I:\profiles\test'
    cfg_path = r'F:\Code\freelance\automate_scraping\configs\amazon\amazon_web_config.yaml'
    amazon = Amazon(cfg_path, profile_path)
    pass