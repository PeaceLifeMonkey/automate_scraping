import timeit
import re
import polars as pl
import json

from bs4 import BeautifulSoup
from common.utils.amazon.amazon import Amazon


class ScrapAmazon(Amazon):
    def __init__(self, config_path, profile_path) -> None:
        super().__init__(config_path, profile_path)
        self.parent_asin = str()
        self.title = str()
        self.main_image = str()
        self.rating = int()
        self.rating_count = float()
        self.new_price = float()
        self.list_price = float()
        self.brand = str()
        self.color = str()
        self.material = str()
        self.frame_material = str()
        self.top_material = str()
        self.remarks = list()

    def timeit_decorator(func):
        def wrapper(*args, **kwargs):
            start_time = timeit.default_timer()
            result = func(*args, **kwargs)
            end_time = timeit.default_timer()
            print(f"Execution time: {end_time - start_time} seconds")

            return result

        return wrapper

    def init_variable(self) -> None:
        self.parent_asin = str()
        self.title = str()
        self.main_image = str()
        self.rating = int()
        self.rating_count = float()
        self.new_price = float()
        self.list_price = float()
        self.brand = str()
        self.color = str()
        self.material = str()
        self.frame_material = str()
        self.top_material = str()
        self.remarks = list()

    @timeit_decorator
    def scrap_amazon(self, asin:str, zipcode:str) -> None:
        self.init_variable()

        self.set_amazon_location_v2(asin,zipcode)
        self.get_basic_info(asin)        

    def get_basic_info(self, asin:str) -> None:
        if self.check_exist():
            self.driver.implicitly_wait(0.5)
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source,'html.parser')
            self.get_image(soup)
            self.get_category(soup)
            self.get_price(asin)
            self.get_title(soup)
            self.get_weight(soup)
            self.get_rating(soup)
            self.get_brand(soup)
            self.get_material(soup)
            self.get_color(soup)
            self.get_parent_variations(page_source)

    def get_others_info(self, soup:BeautifulSoup) -> None:
        eles_rating = self.driver_find_elements(
            '//*[@id="averageCustomerReviews_feature_div"]/div[@id="averageCustomerReviews"]'
        )
        eles_feature = self.driver_find_elements(
            '//*[@id="detailBullets_feature_div"]/ul/li/span/span[1]'
        )
        eles_section_1 = self.driver_find_elements(
            '//*[@id="productDetails_detailBullets_sections1"]/tbody/tr'
        )
        eles_techspec = self.driver_find_elements(
            '//*[@id="productDetails_techSpec_section_1"]/tbody/tr'
        )

        if (
            len(eles_rating) == 0
            and len(eles_feature) == 0
            and len(eles_section_1) == 0
            and len(eles_techspec) == 0
        ):
            self.remarks = self.remarks + ["[3. Not Found other info]"]
        else:
            if len(eles_rating)> 0:
                self.get_rating(eles_rating)
            if len(eles_feature) > 0:
                self.get_info_from_feature(eles_feature)
            if len(eles_section_1) > 0:
                self.get_info_from_detail_sections1(eles_section_1)
            if len(eles_techspec) > 0:
                self.get_info_from_techspec(eles_techspec)
        if self.rank_root != "":
            numbers = re.findall('[0-9,]+', self.rank_root)
            if len(numbers) != 0:
                self.rank_root_no = int(numbers[0].replace(',', ''))

    def get_asin_status(self, soup:BeautifulSoup) -> None:
        status_element = soup.find('div',{"id":"availability"})
        if status_element is not None:
            status = status_element.find('span')
            self.asin_status = status.text.strip()
        else:
            status_element = self.driver_find_element(
                '//*[@id="outOfStock"]/div/div[1]/span[1]'
            )
            self.asin_status = status.text.strip()

        if status_element is None:
            status_element = None

    def get_category(self, soup:BeautifulSoup) -> None:
        cat_info_1 = soup.find('div',{'id':"nav-subnav"})
        if cat_info_1 is not None:
            cat_1 = cat_info_1.find_all("a")
            level = 0
            cat_ids = []
            cat_names = []
            cat_urls = []
            cat_levels = []

            if len(cat_1) > 0:
                for cat1 in cat_1:
                    level = level + 1
                    cat_id = None
                    cat_url = None
                    cat_url = cat1["href"]
                    if cat_url.find("node=") > 0:
                        cat_url_2 = cat_url[cat_url.find("node=") + len("node=") :]
                        cat_id = cat_url_2[: cat_url_2.find("&")]
                    cat_ids = cat_ids + [cat_id]
                    cat_names = cat_names + [cat1.text.strip()]
                    cat_urls = cat_urls + [cat_url.strip()]
                    cat_levels = cat_levels + [level]
                self.cats1_text = str(
                    {
                        "NAME": cat_names,
                        "ID": cat_ids,
                        "LEVEL": cat_levels,
                        "URL": cat_urls,
                    }
                )

        cat_info_2 = soup.find(
            'div',{"id":"wayfinding-breadcrumbs_feature_div"}
        )
        if cat_info_2 is not None:
            cat_2 = cat_info_2.find_all("a")
            level = 0
            cat_ids = []
            cat_names = []
            cat_urls = []
            cat_levels = []
            if len(cat_2) > 0:
                for cat2 in cat_2:
                    level = level + 1
                    cat_id = None
                    cat_url = None
                    cat_url = cat2["href"]
                    if cat_url.find("node=") > 0:
                        cat_id = cat_url[cat_url.find("node=") + len("node=") :]
                    cat_ids = cat_ids + [cat_id]
                    cat_names = cat_names + [cat2.text.strip()]
                    cat_urls = cat_urls + [cat_url.strip()]
                    cat_levels = cat_levels + [level]
                self.cats2_text = str(
                    {
                        "NAME": cat_names,
                        "ID": cat_ids,
                        "LEVEL": cat_levels,
                        "URL": cat_urls,
                    }
                )
                self.cate_id_root = cat_ids[0]

    def get_weight(self, soup:BeautifulSoup) -> None:
        weight_element_1 = soup.find(
            'tr',{'class':"a-spacing-small po-item_weight"}
        )
        weight_element_2 = soup.find(
            'div',{'id':"variation_item_display_weight"}
        )
        weight_element_3 = soup.find(
            'div',{'class':"a-spacing-none "\
            "a-spacing-top-small po-item_weight"}
        )
        if weight_element_1 is not None:
            weight_str = weight_element_1.find(
                "td",{"class":"a-span9"}
            )
            if weight_str is not None:
                self.weight = weight_str.text.strip()
        elif weight_element_2 is not None:
            weight_str = weight_element_2.find("div").find("span")
            if weight_str is not None:
                self.weight = weight_str.text.strip()
        elif weight_element_3 is not None:
            weight_str = weight_element_3.find("span",{"class":"a-span9"})
            if weight_str is not None:
                self.weight = weight_str.text.strip()
        else:
            self.weight = 'fail get'

    def get_image(self, soup:BeautifulSoup) -> None:
        main_image = soup.find(
            'div',{'id':"imgTagWrapperId"}
        )
        if main_image is None:
            main_image = soup.find(
                'div',{'id':"img-canvas"}
            )

        if main_image is not None:
            main_image = main_image.find("img")
            self.main_image = main_image['src']
        else:
            self.remarks = self.remarks + ["[7. Not Found pic]"]

    def get_price(self, asin:str) -> None:
        list_price = self.driver_find_elements(
            '//div[@id="corePriceDisplay_desktop_feature_div"]'
            '/div[@class="a-section a-spacing-small '\
            'aok-align-center"]/span/'
            'span[@class="a-size-small a-color-secondary '\
            'aok-align-center basisPrice"]/'
            'span[@class="a-price a-text-price"]'
        )
        
        if len(list_price) != 0:
            price_data = list_price[0].text
            list_match = re.findall(r"[$][0-9.,]*", price_data)
            if len(list_match) != 0:
                self.list_price = float(list_match[0].replace('$', '').replace(',', '').strip())
        else:
            elements = self.driver_find_elements('//div[@id="corePrice_desktop"]//tr')
            list_price = None
            if len(elements) == 2:
                # Fix for exception have "Save money"
                if 'You Save' in elements[1].text:
                    list_price = elements[0].text
                    list_match = re.findall(r"[$][0-9.,]*", list_price)
                    if len(list_match) != 0:
                        self.list_price = float(list_match[0].replace('$', '').replace(',', '').strip())

        whole_price_element = self.driver_find_elements(
            '//*[@class="a-price aok-align-center '\
            'reinventPricePriceToPayMargin priceToPay"]/'
            'span[@aria-hidden="true"]/span[@class="a-price-whole"]'
        )
        if len(whole_price_element) != 0:
            whole_price_text = whole_price_element[0].text
            frac_price_element = self.driver_find_elements(
                '//*[@class="a-price aok-align-center '\
                'reinventPricePriceToPayMargin priceToPay"]/'
                'span[@aria-hidden="true"]/'\
                'span[@class="a-price-fraction"]'
            )
            if len(frac_price_element) != 0:
                frac_price_text = frac_price_element[0].text
            else:
                frac_price_text = 0
            
            whole_price_text = whole_price_text.replace(',', '').replace('.', '')
            if whole_price_text == '':
                whole_price_text = '0'
            if frac_price_text == '':
                frac_price_text = '0'

            self.amz_price = float(whole_price_text + "." + frac_price_text)
        else:
            self.amz_price = 0

        if self.amz_price == 0:
            elements = self.driver_find_elements(f'//*[@data-asin="{asin}"]//*[@id="_price"]')
            if len(elements) != 0:
                price_data = elements[0].text
                list_match = re.findall(r"[$][0-9.,]*", price_data)
                if len(list_match) != 0:
                    self.amz_price = float(list_match[0].replace('$', '').replace(',', '').strip())

        check_free_txt = self.driver_find_elements_by_id(
            'actualPriceValue'
        )
        if len(check_free_txt) != 0:
            check_free_txt = check_free_txt[0].text
            if check_free_txt == 'Free Download':
                self.list_price = 0
            self.remarks = self.remarks + [check_free_txt]
        else:
            self.remarks = self.remarks + ["[6. Not Found List price]"]

    def check_exist(self) -> None:
        dogs = self.driver_find_elements('//img[@id="d"]')
        if len(dogs) == 0:
            return True
        else:
            img_alt = dogs[0].get_attribute("alt")
            if img_alt == "Dogs of Amazon":
                return False

    def get_parent_variations(self, page_source:str) -> None:
        parent_str = None
        dimension = None

        parent_str = re.findall(r'"parentAsin"\s?:\s?"(\w*)"', page_source)
        if len(parent_str) != 0:
            self.parent_asin = parent_str[0]
        else:
            self.parent_asin = None
        
        result_df = pl.DataFrame()
        dimension_str = re.findall(r'"dimensionValuesDisplayData" : ({.*})', page_source)
        if len(dimension_str) != 0:
            dimension_str:str = dimension_str[0]
            if dimension_str.startswith('{') and dimension_str.endswith('}'):
                dimension = json.loads(dimension_str)
                for sib_asin,dimensions in dimension.items():
                    rec = {}
                    rec["ASIN"] = sib_asin
                    rec["DIMENSIONS"] = dimensions
                    df = pl.DataFrame([rec])
                    result_df = pl.concat([result_df,df])
        else:
            dimension_str:str = None

        if not result_df.is_empty():
            self.variation = result_df.to_dict()
        else:
            self.variation = None

    def get_material(self,soup:BeautifulSoup) -> None:
        material = soup.find(
            "tr",{"class":"a-spacing-small po-material"}
        )
        if material is None:
            table_detail = soup.find(
                "table",{"id":"productDetails_techSpec_section_1"}
            )
            if table_detail is not None:
                table_detail = table_detail.find_all("tr")
                for value in table_detail:
                    title = value.find("th")
                    if title.text.strip() == "Material":
                        material_str = value.find("td")
                        if material_str is not None:
                            self.material = material_str.text.strip(
                            ).replace("\u200e","")
        else:
            material_str = material.find("td",{"class":"a-span9"})
            if material_str is not None:
                self.material = material_str.text.strip()

    def get_color(self,soup:BeautifulSoup) -> None:
        color = soup.find(
            "tr",{"class":"a-spacing-small po-color"}
        )
        if color is not None:
            color_str = color.find("td",{"class":"a-span9"})
            if color_str is not None:
                self.color = color_str.text.strip()
        else:
            table_detail = soup.find(
                "table",{"id":"productDetails_techSpec_section_1"}
            )
            if table_detail is not None:
                table_detail = table_detail.find_all("tr")
                for value in table_detail:
                    title = value.find("th")
                    if title.text.strip() == "Color":
                        color_str = value.find("td")
                        if color_str is not None:
                            self.material = color_str.text.strip(
                            ).replace("\u200e","")

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
    asin = 'B07F1ZB48H'
    # amz.set_amazon_location_v2(asin,'90001')
    amz.scrap_amazon(asin,'90001')
    pass
