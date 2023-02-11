from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import DesiredCapabilities
import os
import time
from decouple import config
from selenium.webdriver.chrome.service import Service
from fuzzywuzzy import fuzz
from pydantic import BaseModel
from typing import List

class Review(BaseModel):
    #logo: str
    title: str
    link: str
    rating: float

class SiteReview(BaseModel):
    reviews: List[Review]
    rating: float

def build_top_amazon_review(scraper, XPATH) -> Review:
    review = scraper.browser.find_element(By.XPATH, XPATH)
    
    rating_element = review.find_element(By.XPATH, ".//div[1]/div[4]/i/span")
    rating_text = rating_element.get_attribute('textContent')
    rating_float = float(rating_text[:3])

    title_element = review.find_element(By.XPATH, ".//div[1]/div[4]/span[2]")
    title_text = title_element.get_attribute('textContent')

    read_more_element = review.find_element(By.XPATH, ".//div[2]/a")
    review_hyperlink = read_more_element.get_attribute('href')
    return Review(title=title_text, link=review_hyperlink, rating=rating_float)

def build_amazon_review(scraper, XPATH) -> Review:
    review = scraper.browser.find_element(By.XPATH, XPATH)
    rating_element = review.find_element(By.XPATH, ".//a[1]/i/span")
    rating_text = rating_element.get_attribute('textContent')
    rating_float = float(rating_text[:3])

    title_element = review.find_element(By.XPATH, ".//a[2]/span")
    title_text = title_element.get_attribute('textContent')

    
    read_more_element = review.find_element(By.XPATH, ".//a[1]")
    review_hyperlink = read_more_element.get_attribute('href')
    return Review(title=title_text, link=review_hyperlink, rating=rating_float)

def scrape_amazon(scraper, product_name) -> SiteReview:
    browser = scraper.browser

    # Search for the product
    browser.get('https://www.amazon.com/s?k=' + product_name)
    parent_xpath = "//*[@id=\"search\"]/div[1]/div[1]/div/span[1]/div[1]"
    WebDriverWait(browser, 3)
    scraper.wait(parent_xpath)
    
    # Get all the products from the search and click on the one that matches the most with the product name
    parent = browser.find_element(By.XPATH, parent_xpath)
    elements = parent.find_elements(By.CLASS_NAME, "a-size-medium")
    closest_element = elements[0]
    highest_ratio = fuzz.ratio(product_name, closest_element.text)
    for element in elements:    
        ratio = fuzz.ratio(product_name, element.text)
        if ratio > highest_ratio:
            closest_element = element
            highest_ratio = ratio
    closest_element.click()
    
    rating_xpath = "//*[@id=\"reviewsMedley\"]/div/div[1]/span[1]/span/div[2]/div/div[2]/div/span/span"
    scraper.wait(rating_xpath)

    # Find the rating for the product
    rating = browser.find_element(By.XPATH, rating_xpath)
    rating_text = rating.text
    rating_float = float(rating_text[:3])

    # Go the the customer review page
    all_reviews_xpath = "//*[@id=\"cr-pagination-footer-0\"]/a"
    all_reviews_css_selector = "a[data-hook='see-all-reviews-link-foot']"
    
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, all_reviews_css_selector))
    )
    see_all_reviews = browser.find_element(By.CSS_SELECTOR, all_reviews_css_selector)
    see_all_reviews.click()

    # Select the best positive and critical reviews
    pos_review_xpath = "/html/body/div[1]/div[3]/div/div[1]/div/div[1]/div[1]/div/div/div[1]/div[1]"
    general_review_xpath = "/html/body/div[1]/div[3]/div/div[1]/div/div[1]/div[5]/div[3]/div/div[1]/div/div/div[2]"
    WebDriverWait(browser, 10).until(lambda driver: driver.find_elements(By.XPATH, pos_review_xpath) or
                                               driver.find_elements(By.XPATH, general_review_xpath))[0]

    if len(browser.find_elements(By.XPATH, pos_review_xpath)) > 0:
        positive_review: Review = build_top_amazon_review(scraper, pos_review_xpath)
        critical_review: Review = build_top_amazon_review(scraper, "/html/body/div[1]/div[3]/div/div[1]/div/div[1]/div[1]/div/div/div[2]/div[1]")
        return SiteReview(reviews=[positive_review, critical_review], rating=rating_float)
    else:
        review_1: Review = build_amazon_review(scraper, general_review_xpath)
        review_2: Review = build_amazon_review(scraper, "/html/body/div[1]/div[3]/div/div[1]/div/div[1]/div[5]/div[3]/div/div[2]/div/div/div[2]")
        return SiteReview(reviews=[review_1, review_2], rating=rating_float)
    

    

class Scraper:
    def __init__(self):
        service = Service(config("CHROMEDRIVER_PATH"))
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = config("GOOGLE_CHROME_BIN", "")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        #chrome_options.add_argument("start-maximized")

        caps = DesiredCapabilities().CHROME
        caps["pageLoadStrategy"] = "none"
        self.browser = webdriver.Chrome(service=service, options=chrome_options)

    def __del__(self):
        self.browser.quit() # clean up driver when we are cleaned up

    def wait(self, XPATH):
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.XPATH, XPATH))
        )



