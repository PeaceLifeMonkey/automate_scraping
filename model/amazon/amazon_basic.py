import timeit

from bs4 import BeautifulSoup
from common.utils.amazon.amazon import Amazon


class ScrapAmazon(Amazon):
    def __init__(self, config_path, profile_path) -> None:
        super().__init__(config_path, profile_path)
        self.title = str()
        self.image = str()
        self.rating = int()
        self.rating_count = float()
        self.new_price = float()
        self.list_price = float()
        self.brand = str()
        self.color = str()
        self.material = str()
        self.frame_material = str()
        self.top_material = str()

    def timeit_decorator(func):
        def wrapper(*args, **kwargs):
            start_time = timeit.default_timer()
            result = func(*args, **kwargs)
            end_time = timeit.default_timer()
            print(f"Execution time: {end_time - start_time} seconds")
            return result
        return wrapper

    def init_variable(self) -> None:
        self.title = str()
        self.image = str()
        self.rating = int()
        self.rating_count = float()
        self.new_price = float()
        self.list_price = float()
        self.brand = str()
        self.color = str()
        self.material = str()
        self.frame_material = str()
        self.top_material = str()

    @timeit_decorator
    def scrap_amazon(self, asin:str) -> None:
        self.init_variable()

        self.get_page(asin)
        self.get_basic_info(asin)        

    def get_basic_info(self, asin:str) -> None:
        if self.check_exist():
            self.driver.implicitly_wait(0.5)
            soup = BeautifulSoup(self.driver.page_source,'html.parser')
            self.get_title(soup)
            self.get_rating(soup)
            self.get_brand(soup)

    def check_exist(self) -> None:
        dogs = self.driver_find_elements('//img[@id="d"]')
        if len(dogs) == 0:
            return True
        else:
            img_alt = dogs[0].get_attribute("alt")
            if img_alt == "Dogs of Amazon":
                return False

    def get_title(self, soup:BeautifulSoup) -> None:
        title = soup.find_all("span",{"id":"productTitle"})
        if len(title) != 0:
            self.title = title[0].text.strip()
        else:
            self.title = None

    def get_rating(self, soup:BeautifulSoup) -> None:
        eles_1 = soup.find_all("div",{"id":"averageCustomerReviews_feature_div"})
        if len(eles_1) != 0:
            rating = self.driver_find_elements('//*[@id="acrPopover"]')
            if len(rating) != 0:
                rating = rating[0].get_attribute('title')
                self.rating = float(rating.replace(' out of 5 stars',''))
                rating_count = eles_1[0].find("span",{"id":"acrCustomerReviewText"}).text.strip()
                self.rating_count = int(
                    rating_count.replace(
                    ' ratings','').strip().replace(',','')
                )
            else:
                self.rating = None
                self.rating_count = None


    def get_brand(self, soup:BeautifulSoup) -> None:
        brand = soup.find_all("div",{"id":"bylineInfo_feature_div"})
        if len(brand) != 0:
            self.brand = brand[0].text.replace('\n','').replace(
                'Visit the ','').replace(
                ' Store','').strip()
        else:
            self.brand = None

if __name__ == "__main__":
    profile_path = '/media/quang/Quang/Automate/profiles'
    cfg_path = '/media/quang/Quang/Automate/configs/amazon/amazon_web_config.yaml'
    amz = ScrapAmazon(cfg_path,profile_path)
    asin = 'B08B6F1NNR'
    amz.set_amazon_location_v2('90001')
    amz.scrap_amazon(asin)
    pass
