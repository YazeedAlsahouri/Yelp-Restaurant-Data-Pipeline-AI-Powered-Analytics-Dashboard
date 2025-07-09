from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
import time
import random
from .scrape_proxies import ProxyScrape
# from . import scrape_proxies.ProxyScrape
from . import restaurant_scraper
from . import consts
import os
from selenium.common.exceptions import NoSuchElementException, TimeoutException

class YelpScrapper(webdriver.Chrome):

    def __init__(self ,driver_path = "C:/SeleniumDrivers" ,auto_close = False):

        self.driver_path = driver_path
        self.auto_close = auto_close

        with ProxyScrape(driver_path) as proxy_scraper:
            proxy_scraper.get_proxy_page()
            self.proxy = proxy_scraper.get_proxy()

        options = webdriver.ChromeOptions()
        if self.proxy:
            print(f"Using proxy: {self.proxy}")
            options.add_argument(f'--proxy-server={self.proxy}')
        options.add_argument("--lang=en-US")
        options.add_experimental_option(
            'prefs', {
                'intl.accept_languages': 'en-US,en'
            }
        )
        os.environ["PATH"] += driver_path
        super(YelpScrapper, self).__init__(options=options)

        self.implicitly_wait(20)
        self.maximize_window()

    def __exit__(self ,exc_type ,exc_val ,exc_tb):
        if self.auto_close:
            self.quit()

    def get_yelp_page(self):
        url = consts.YELP_URL

        try:
            self.get(url)
            WebDriverWait(self ,10).until(
                EC.presence_of_element_located((By.XPATH ,'//span[@class=" y-css-14kekzi" and text() = "Restaurants"]'))
            )
        except Exception as e:
            print(f"Error caught in get_yelp_page: {e}")

    def print_proxy_info(self):
        print("\n=== PROXY VERIFICATION ===")
        print(f"Configured proxy (if any): {self.proxy}")

        try:
            self.get("https://httpbin.org/ip")
            WebDriverWait(self, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'pre'))
            )
            actual_ip_info = self.find_element(By.TAG_NAME, 'pre').text
            print(f"Actual connection IP info: {actual_ip_info}")
        except Exception as e:
            print(f"Could not retrieve actual connection IP: {e}")
            print("This might happen if there's no internet connection or the proxy is not working.")

    def select_and_apply_filters(self):
        try:
            restaurants_btn = WebDriverWait(self, 10).until(
                EC.presence_of_element_located((By.XPATH, '//span[@class=" y-css-14kekzi" and text() = "Restaurants"]'))
            )
            restaurants_btn.click()
        except Exception as e:
            print(f"Error clicking Restaurants button: {e}")
            return

        time.sleep(random.uniform(1, 3))

        try:
            location_search_box = WebDriverWait(self, 20).until(
                EC.presence_of_element_located((By.XPATH, '//input[@class="input__09f24__yaqh1 y-css-trukho e140vcx51" and contains(@id ,"ocation")]'))
            )
            location_search_box.clear()
            location_search_box.send_keys(consts.LOCATION)
        except Exception as e:
            print(f"Error interacting with location search box: {e}")
            return

        time.sleep(random.uniform(1, 3))

        try:
            search_btn = WebDriverWait(self, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@class='ewsdu8x6 y-css-14trpyl']"))
            )
            self.execute_script("arguments[0].click();", search_btn)
        except Exception as e:
            print(f"Error clicking search button: {e}")
            return

    def scraping_data(self):

        scraper = restaurant_scraper.RestaurantScraper(driver = self)

        return scraper.scrape_pages()