from numpy.distutils.conv_template import replace_re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from selenium.webdriver.remote.webdriver import WebDriver
import time
import random
from .scrape_proxies import ProxyScrape
# from . import scrape_proxies.ProxyScrape
from . import consts
import os
from selenium.common.exceptions import NoSuchElementException, TimeoutException


class RestaurantScraper:

    def __init__(self ,driver : WebDriver):
        self.driver = driver

    def scrape_pages(self):
        all_restaurants_data = []

        for page in range(1,11):
            try:
                all_restaurants_data.append(self.scrape_restaurants())
            except Exception as e:
                print(f"Error scraping restaurants on page {page}: {e}")
                continue

            try:
                div1 = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR ,'div[class="pagination-links__09f24__Y1Vj7 y-css-1n5biw7"]'))
                )
                div2 = WebDriverWait(div1, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR ,f'div[aria-label="Page: {page +1}"]'))
                )
                link = WebDriverWait(div2, 5).until(
                    EC.element_to_be_clickable((By.XPATH ,'..'))
                )
                link.click()
            except Exception as e:
                print(f"Error navigating to next restaurant list page {page + 1}: {e}")
                break

        return all_restaurants_data

    def scrape_restaurants(self):
        try:
            restaurants_ul = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="main-content"]/ul'))
            )
        except Exception as e:
            print(f"Error finding restaurants UL: {e}")
            return []

        try:
            restaurants = restaurants_ul.find_elements(By.CSS_SELECTOR, 'div[class="businessName__09f24__HG_pC y-css-mhg9c5"]')
        except Exception as e:
            print(f"Error finding restaurant elements: {e}")
            return []

        time.sleep(3)

        restaurants_data = []

        for rest in restaurants:
            try:
                restaurants_data.append(self.scrape_inside_restaurants(rest))
            except Exception as e:
                print(f"Error scraping inside restaurant: {e}")
                continue

        return restaurants_data

    def scrape_inside_restaurants(self ,restaurant):
        try:
            h3 = WebDriverWait(restaurant, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, 'h3'))
            )
            a = WebDriverWait(h3, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, 'a'))
            )
            href = a.get_attribute("href")
        except Exception as e:
            print(f"Error getting restaurant href: {e}")
            return {}

        try:
            self.driver.get(href)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH,'/html/body/yelp-react-root/div[1]/div[5]/div[1]/div[1]/div/div/div[1]/h1'))
            )
        except Exception as e:
            print(f"Error navigating to restaurant page {href}: {e}")
            return {}

        restaurant_data = {}

        try:
            r_name = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH,'/html/body/yelp-react-root/div[1]/div[5]/div[1]/div[1]/div/div/div[1]/h1'))
            )
            r_rating = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH,'/html/body/yelp-react-root/div[1]/div[5]/div[1]/div[1]/div/div/div[2]/div[2]/span[1]'))
            )
            r_view = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH,'/html/body/yelp-react-root/div[1]/div[5]/div[1]/div[1]/div/div/div[2]/div[2]/span[2]/a'))
            )

            restaurant_data["Restaurant Name"] = r_name.text

            try:
                restaurant_data["Restaurant Average Rating"] = float(r_rating.text)
            except ValueError:
                print(f"Could not convert rating '{r_rating.text}' to float.")
                restaurant_data["Restaurant Average Rating"] = None

            try:
                r_view_text = r_view.text
                if "k" in r_view_text.lower() :
                    r_value = float(r_view_text.lower().replace("k" ,'')) * 1000
                else:
                    r_value = int(r_view_text)
                restaurant_data["Restaurant Total Reviews"] = r_value
            except ValueError:
                print(f"Could not convert review count '{r_view.text}' to int.")
                restaurant_data["Restaurant Total Reviews"] = None

        except Exception as e:
            print(f"Error extracting restaurant main details: {e}")


        users_reviews = []

        for page in range(1,11):
            try:
                users_reviews_ul = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="reviews"]/section/div[2]/ul'))
                )
                users_lists = users_reviews_ul.find_elements(By.TAG_NAME, 'li')[:-1]

                users_reviews.append(self.scrape_reviews(users_lists))

                div = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR ,f'div[aria-label="Page: {page +1}"]'))
                )
                link = WebDriverWait(div, 5).until(
                    EC.element_to_be_clickable((By.XPATH ,'..'))
                )
                link.click()
            except Exception as e:
                print(f"Error navigating to next review page {page + 1} or scraping reviews: {e}")
                break

        restaurant_data["Reviews Info"] = users_reviews

        return restaurant_data


    def scrape_reviews(self ,users_lists):
        results = []

        for review_li in users_lists:
            try:
                user_info = WebDriverWait(review_li, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class="user-passport-info y-css-mhg9c5"]'))
                )

                span = WebDriverWait(user_info, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'span'))
                )
                a = WebDriverWait(span, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'a'))
                )
                user_name = a.text

                user_country = WebDriverWait(user_info, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="UserPassportInfoTextContainer"]'))
                )
                user_country_text = WebDriverWait(user_country, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'span'))
                ).text

                review_paragraph = WebDriverWait(review_li, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'p[class="comment__09f24__D0cxf y-css-1541nhh"]'))
                )
                review_span = WebDriverWait(review_paragraph, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'span'))
                )
                review_text = review_span.text

                results.append({
                    "User Name": user_name
                    , "Country": user_country_text
                    , "Review Text": review_text
                })
            except Exception as e:
                print(f"Error scraping individual review: {e}")
                continue

        return results