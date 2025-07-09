# main.py
from Selenium_Scraper.scraper import YelpScrapper
from yelp_cassandra import CassandraDataBase
import json

def main():
    scraper = None
    db = None
    try:
        scraper = YelpScrapper(auto_close=True)
        scraper.print_proxy_info()

        scraper.get_yelp_page()
        scraper.select_and_apply_filters()

        all_scraped_data = scraper.scraping_data()

        db = CassandraDataBase()
        db.connect()
        db.create_tables()

        db.insert_restaurant_data(all_scraped_data)

    except Exception as e:
        print(f"An error occurred in main: {e}")
    finally:
        if scraper:
            scraper.quit()
        if db:
            db.close()

if __name__ == "__main__":
    main()