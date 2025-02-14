from b2sdk.v2 import B2Api, InMemoryAccountInfo

# Authenticate with Backblaze
info = InMemoryAccountInfo()
b2_api = B2Api(info)
b2_api.authorize_account("production", "your_app_id", "your_app_key")

# Get the bucket
bucket = b2_api.get_bucket_by_name("seo-scraper-files")

# Upload file
with open("path/to/your/file.html", "rb") as file:
    bucket.upload_local_file(file, "file.html")

print("File uploaded successfully!")
