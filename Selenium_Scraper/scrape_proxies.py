from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
from . import consts
import os
from selenium.common.exceptions import NoSuchElementException, TimeoutException


class ProxyScrape(webdriver.Chrome):

    def __init__(self, driver_path="C:/SeleniumDrivers"):

        self.driver_path = driver_path

        os.environ["PATH"] += driver_path

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")

        super(ProxyScrape, self).__init__(options=options)

        self.implicitly_wait(15)

    def get_proxy_page(self):
        url = consts.PROXY_URL

        try:
            self.get(url)
            WebDriverWait(self, 20).until(
                EC.presence_of_element_located((By.XPATH, "//table[@class='table table-striped table-bordered']"))
            )
        except Exception as e:
            print(f"Error caught in get_proxy_page: {e}")

    def test_proxy(self, proxy_address, timeout=5):
        print(f"Testing proxy: {proxy_address}...")
        proxies = {
            'http': f'http://{proxy_address}',
            'https': f'https://{proxy_address}'
        }
        try:
            response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=timeout)
            response.raise_for_status()
            print(f"Proxy {proxy_address} is working! IP: {response.json().get('origin')}")
            return True
        except ValueError as e:
            print(f"Proxy {proxy_address} failed: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred while testing proxy {proxy_address}: {e}")
            return False

    def get_proxy(self):
        self.proxy = None
        temp_proxy = None

        try:
            table = WebDriverWait(self ,10).until(
                EC.presence_of_element_located((By.XPATH, "//table[@class='table table-striped table-bordered']"))
            )
            try:
                tbody = table.find_element(By.TAG_NAME, "tbody")
            except Exception as e:
                print(f"Error finding tbody: {e}")
                return None

            try:
                trs = tbody.find_elements(By.TAG_NAME, "tr")[1:51]
            except Exception as e:
                print(f"Error finding trs: {e}")
                return None

            for tr in trs:
                try:
                    tds = tr.find_elements(By.TAG_NAME, "td")
                    IP = tds[0].text.strip()
                    Port = tds[1].text.strip()
                    Anonymity = tds[4].text.strip().lower()
                    Https = tds[6].text.strip().lower()

                    if not IP and not Port:
                        continue
                    current_proxy_address = f"{IP}:{Port}"

                    if Anonymity == "elite proxy" and Https == "yes":
                        if self.test_proxy(current_proxy_address):
                            self.proxy = current_proxy_address
                            return self.proxy

                    if Https == "yes":
                        if self.test_proxy(current_proxy_address):
                            temp_proxy = current_proxy_address
                except ValueError as E :
                    print(f"Error caught inside proxy loop: {E}")
                except Exception as E :
                    print(f"Error caught inside proxy loop for element finding: {E}")

            if self.proxy is None:
                self.proxy = temp_proxy

        except Exception as E:
            print(f"Error caught in get_proxy: {E}")

        return self.proxy