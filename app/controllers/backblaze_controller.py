from b2sdk.v2 import B2Api, InMemoryAccountInfo

# Authenticate with Backblaze B2
info = InMemoryAccountInfo()
b2_api = B2Api(info)
b2_api.authorize_account("production", "your_app_id", "your_app_key")

# Get the bucket
bucket = b2_api.get_bucket_by_name("seo-scraper-files")


# Upload a file to Backblaze B2
def upload_file_to_backblaze(file_path: str, file_name: str):
    with open(file_path, 'rb') as file:
        bucket.upload_local_file(file, file_name)
    return f"s3://{bucket.name}/{file_name}"


# Delete a file from Backblaze B2 (if needed)
def delete_file_from_backblaze(file_url: str):
    # Extract file name from the URL and delete it from the Backblaze bucket
    file_name = file_url.split('/')[-1]
    file_info = bucket.get_file_info_by_name(file_name)
    bucket.delete_file_version(file_info.file_id, file_info.file_name)
    return {"message": "File deleted from Backblaze successfully"}
