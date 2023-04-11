import json

import requests
from requests import exceptions

from parsel import Selector

AMAZON_US_URL = "https://www.amazon.com/"

DEFAULT_USER_AGENT = "Mozilla/5.0 ..."
DEFAULT_REQUEST_HEADERS = {"Accept-Language": "en", "User-Agent": DEFAULT_USER_AGENT}


AMAZON_CSRF_TOKEN_URL = (
    'https://www.amazon.com/portal-migration/hz/glow/'
    'get-rendered-address-selections'
)

def get_ajax_token(page_source: dict) -> str:
    content = Selector(text=page_source)
    data = content.xpath(
        "//span[@id='nav-global-location-data-modal-action']/@data-a-modal"
    ).get()

    if not data:
        return None

    json_data = json.loads(data)
    return json_data["ajaxHeaders"]["anti-csrftoken-a2z"]

def get_token(cookies:dict, ajax_token:dict) -> str:
    headers = {
        'authority': 'www.amazon.com',
        'accept': 'text/html,*/*',
        'accept-language': 'en-US,en;q=0.9',
        'anti-csrftoken-a2z': ajax_token,
        'device-memory': '8',
        'downlink': '1.1',
        'dpr': '1',
        'ect': '4g',
        'referer': 'https://www.amazon.com/',
        'rtt': '200',
        'sec-ch-device-memory': '8',
        'sec-ch-dpr': '1',
        'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-ch-ua-platform-version': '"5.15.90"',
        'sec-ch-viewport-width': '1037',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'viewport-width': '1037',
        'x-requested-with': 'XMLHttpRequest',
    }

    params = {
        'deviceType': 'desktop',
        'pageType': 'Gateway',
        'storeContext': 'NoStoreName',
        'actionSource': 'desktop-modal',
    }

    response = requests.get(
        url=AMAZON_CSRF_TOKEN_URL, headers=headers, params=params, cookies=cookies
    )
    
    content = Selector(text=response.text)
    csrf_token = content.re_first(r'CSRF_TOKEN : "(.+?)"')
    return csrf_token

def send_change_location_request(ajax_token:str, cookies:dict, zip_code:str) -> bool:
    error_message = str()
    try:
        anti_csrftoken = get_token(cookies, ajax_token)
        if anti_csrftoken is None:
            error_message += "anti_csrftoken is None\n"
            return (False, error_message)

        headers = {
            'authority': 'www.amazon.com',
            'accept': 'text/html,*/*',
            'accept-language': 'en-US,en;q=0.9',
            'anti-csrftoken-a2z': anti_csrftoken,
            'device-memory': '8',
            'downlink': '1.35',
            'dpr': '1',
            'ect': '4g',
            'origin': 'https://www.amazon.com',
            'referer': 'https://www.amazon.com/',
            'rtt': '550',
            'sec-ch-device-memory': '8',
            'sec-ch-dpr': '1',
            'sec-ch-ua': '"-Not.A/Brand";v="8", "Chromium";v="102"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-viewport-width': '830',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
            'viewport-width': '830',
            'x-requested-with': 'XMLHttpRequest',
        }

        data = {
            'actionSource': 'glow',
            'almBrandId': 'undefined',
            'deviceType': 'web',
            'locationType': 'LOCATION_INPUT',
            'pageType': 'Gateway',
            'storeContext': 'generic',
            'zipCode': zip_code,
        }

        response = requests.post(
            'https://www.amazon.com/gp/delivery/ajax/address-change.html', 
            cookies=cookies, headers=headers, 
            data=data
        )
        
        if zip_code not in response.text:
            error_message += "Change location failed!!!\n"
            return (False, error_message)
            
        return (True, error_message)
    except exceptions.ConnectTimeout as e:
        error_message += f"Request change location Timeout!!!\n{e}"
    except exceptions.ConnectionError as e:
        error_message += f"Request change location Error!!!\n{e}"
    except Exception as e:
        error_message += f"Request change location falded!!!\n{e}"

    return (False, error_message)