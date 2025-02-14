from fastapi import HTTPException
from pymongo import MongoClient
import datetime


# MongoDB connection setup
client = MongoClient("mongodb://localhost:27017/")
db = client["seo_platform"]
scraped_data_collection = db["scraped_data"]


# Store scraped HTML data
def store_scraped_html(url: str, html_content: str):
    document = {
        "url": url,
        "html_content": html_content,
        "timestamp": datetime.datetime.utcnow()
    }

    # Insert the document into MongoDB
    scraped_data_collection.insert_one(document)

    return {"message": "HTML content stored successfully", "url": url}


# Get scraped HTML by URL
def get_scraped_data_by_url(url: str):
    data = scraped_data_collection.find_one({"url": url})
    if not data:
        raise HTTPException(status_code=404, detail="Scraped data not found")
    return data
