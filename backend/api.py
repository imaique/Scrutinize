from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from scraper import Scraper, Review, SiteReview


app = FastAPI()
scraper = Scraper()

class Item(BaseModel):
    customer_avg: float
    customer_reviews: List[Review] = []
    #article_avg: float

@app.get('/')
def get():
    
    return scraper.scrape_amazon('Apple iPhone 13 Pro 128GB - Blue - Unlocked')