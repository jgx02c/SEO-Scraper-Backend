from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["seo_platform"]
scraped_data_collection = db["scraped_data"]

# Example to insert scraped data
scraped_data_collection.insert_one({
    "url": "http://example.com",
    "html_content": "<html>...</html>",
    "timestamp": datetime.datetime.utcnow()
})
